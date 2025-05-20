"""
历史消息同步模块

此模块负责从Telegram获取历史消息并同步到Meilisearch，包括：
1. 同步指定聊天的历史消息
2. 同步所有白名单中的聊天
"""

import logging
import asyncio
import time
from datetime import datetime
from typing import Optional, List, Dict, Any, Union, Tuple
from telethon.tl.types import Message, User, Chat, Channel
from telethon.errors import FloodWaitError, ChatAdminRequiredError, ChannelPrivateError

from core.models import MeiliMessageDoc
from core.meilisearch_service import MeiliSearchService
from core.config_manager import ConfigManager
from user_bot.client import UserBotClient
from user_bot.utils import generate_message_link, format_sender_name, determine_chat_type

# 配置日志记录器
logger = logging.getLogger(__name__)

# 常量定义
BATCH_SIZE = 100  # 每批处理的消息数量
RATE_LIMIT_WAIT = 2  # 消息间隔，避免触发Telegram的速率限制（秒）
MAX_ATTEMPTS = 3  # 最大重试次数


class HistorySyncer:
    """
    历史消息同步器类
    
    负责从Telegram获取历史消息并同步到Meilisearch
    """
    
    def __init__(
        self, 
        client: Optional[UserBotClient] = None,
        config_manager: Optional[ConfigManager] = None,
        meili_service: Optional[MeiliSearchService] = None
    ) -> None:
        """
        初始化历史消息同步器
        
        Args:
            client: UserBotClient实例，如果未提供则创建新实例
            config_manager: ConfigManager实例，如果未提供则创建新实例
            meili_service: MeiliSearchService实例，如果未提供则创建新实例
        """
        self.client = client or UserBotClient()
        self.config_manager = config_manager or ConfigManager()
        
        # 初始化MeiliSearchService（如果未提供）
        if meili_service is None:
            # 从配置获取MeiliSearch配置
            host = self.config_manager.get_env("MEILISEARCH_HOST") or \
                  self.config_manager.get_config("MeiliSearch", "HOST", "http://localhost:7700")
            api_key = self.config_manager.get_env("MEILISEARCH_API_KEY") or \
                     self.config_manager.get_config("MeiliSearch", "API_KEY")
            
            self.meili_service = MeiliSearchService(host=host, api_key=api_key)
        else:
            self.meili_service = meili_service
        
        # 存储最后同步点
        self.last_sync_points: Dict[int, Dict[str, Any]] = {}
        
        logger.info("历史消息同步器初始化完成")

    async def sync_chat_history(
        self, 
        chat_id: int, 
        limit: Optional[int] = None, 
        offset_date: Optional[datetime] = None
    ) -> Tuple[int, int]:
        """
        同步指定聊天的历史消息
        
        从指定的chat_id拉取历史消息，分批处理并索引到Meilisearch
        
        Args:
            chat_id: 聊天ID
            limit: 最大消息数量，None表示不限制
            offset_date: 开始时间点，None表示从最新消息开始
            
        Returns:
            Tuple[int, int]: (处理的消息数量, 成功索引的消息数量)
        """
        logger.info(f"开始同步聊天 {chat_id} 的历史消息")
        
        # 获取客户端实例
        client = self.client.get_client()
        
        # 获取聊天信息
        try:
            chat_entity = await client.get_entity(chat_id)
            chat_title = getattr(chat_entity, 'title', None)
            if not chat_title and hasattr(chat_entity, 'first_name'):
                # 如果是用户，使用名字作为标题
                chat_title = format_sender_name(
                    getattr(chat_entity, 'first_name', None),
                    getattr(chat_entity, 'last_name', None)
                )
            
            # 确定聊天类型
            if isinstance(chat_entity, User):
                chat_type = "user"
            elif isinstance(chat_entity, Chat):
                chat_type = "group"
            elif isinstance(chat_entity, Channel):
                if getattr(chat_entity, 'megagroup', False):
                    chat_type = "group"  # 超级群组也算作群组
                else:
                    chat_type = "channel"
            else:
                chat_type = "unknown"
                
            logger.info(f"聊天信息: ID={chat_id}, 标题={chat_title}, 类型={chat_type}")
            
        except Exception as e:
            logger.error(f"获取聊天 {chat_id} 信息失败: {str(e)}")
            return 0, 0
        
        # 处理计数
        processed_count = 0
        indexed_count = 0
        attempts = 0
        
        # 开始遍历历史消息
        try:
            # 准备批量消息列表
            message_batch: List[MeiliMessageDoc] = []
            
            # 使用迭代器获取历史消息，避免一次性加载全部
            async for message in client.iter_messages(
                chat_id,
                limit=limit,
                offset_date=offset_date,
                wait_time=RATE_LIMIT_WAIT  # 防止触发速率限制
            ):
                # 跳过非文本消息
                if not message.text:
                    continue
                
                processed_count += 1
                
                # 构建消息文档
                message_doc = await self._build_message_doc(message, chat_id, chat_title, chat_type)
                
                if message_doc:
                    message_batch.append(message_doc)
                    
                    # 当达到批处理大小时，索引并清空批处理列表
                    if len(message_batch) >= BATCH_SIZE:
                        success = await self._index_message_batch(message_batch)
                        if success:
                            indexed_count += len(message_batch)
                        message_batch = []
                        
                        # 记录最后同步点
                        self._update_last_sync_point(chat_id, message)
                
                # 如果设置了limit且已达到，则停止
                if limit is not None and processed_count >= limit:
                    break
                    
            # 处理剩余的批处理消息
            if message_batch:
                success = await self._index_message_batch(message_batch)
                if success:
                    indexed_count += len(message_batch)
                
                # 记录最后同步点（使用最后一条消息）
                if message_batch:
                    # 获取最后一条消息的ID，由于我们在处理时，消息是从新到旧，
                    # 因此最后一条消息是最早的，下次应该从比它新的消息开始
                    # 由于索引是以字典形式转换，需要从原始message中获取
                    self._update_last_sync_point(chat_id, message)
            
            logger.info(f"聊天 {chat_id} 同步完成，共处理 {processed_count} 条消息，成功索引 {indexed_count} 条")
            return processed_count, indexed_count
            
        except FloodWaitError as e:
            # Telegram限制了请求频率，需要等待
            wait_time = e.seconds
            logger.warning(f"触发Telegram速率限制，需要等待 {wait_time} 秒")
            await asyncio.sleep(wait_time)
            
            # 递增重试次数
            attempts += 1
            if attempts < MAX_ATTEMPTS:
                logger.info(f"重试同步聊天 {chat_id} 历史消息 (尝试 {attempts+1}/{MAX_ATTEMPTS})")
                return await self.sync_chat_history(chat_id, limit, offset_date)
            else:
                logger.error(f"同步聊天 {chat_id} 历史消息失败: 超过最大重试次数")
                return processed_count, indexed_count
                
        except (ChatAdminRequiredError, ChannelPrivateError) as e:
            # 没有权限访问此聊天
            logger.error(f"无权访问聊天 {chat_id}: {str(e)}")
            return 0, 0
            
        except Exception as e:
            logger.error(f"同步聊天 {chat_id} 历史消息时发生错误: {str(e)}")
            return processed_count, indexed_count
    
    async def initial_sync_all_whitelisted_chats(self, limit_per_chat: Optional[int] = None) -> Dict[int, Tuple[int, int]]:
        """
        同步所有白名单中聊天的历史消息
        
        遍历配置管理器中的白名单，对每个聊天执行历史同步
        
        Args:
            limit_per_chat: 每个聊天同步的最大消息数量，None表示不限制
            
        Returns:
            Dict[int, Tuple[int, int]]: 映射聊天ID到处理结果的字典，
                                      值为元组(处理的消息数量, 成功索引的消息数量)
        """
        logger.info("开始同步所有白名单中的聊天历史消息")
        
        # 获取白名单
        whitelist = self.config_manager.get_whitelist()
        if not whitelist:
            logger.warning("白名单为空，无需同步")
            return {}
        
        logger.info(f"白名单中共有 {len(whitelist)} 个聊天")
        
        # 存储每个聊天的同步结果
        results: Dict[int, Tuple[int, int]] = {}
        
        # 依次同步每个聊天
        for chat_id in whitelist:
            logger.info(f"开始同步聊天 {chat_id}")
            
            try:
                processed, indexed = await self.sync_chat_history(chat_id, limit=limit_per_chat)
                results[chat_id] = (processed, indexed)
                
                # 简单防止频率限制
                await asyncio.sleep(RATE_LIMIT_WAIT)
                
            except Exception as e:
                logger.error(f"同步聊天 {chat_id} 时发生异常: {str(e)}")
                results[chat_id] = (0, 0)
        
        # 汇总统计
        total_processed = sum(result[0] for result in results.values())
        total_indexed = sum(result[1] for result in results.values())
        
        logger.info(f"所有白名单聊天同步完成，共处理 {total_processed} 条消息，成功索引 {total_indexed} 条")
        return results
    
    async def _build_message_doc(
        self, 
        message: Message, 
        chat_id: int, 
        chat_title: Optional[str],
        chat_type: str
    ) -> Optional[MeiliMessageDoc]:
        """
        从Telethon消息对象构建MeiliMessageDoc
        
        Args:
            message: Telethon消息对象
            chat_id: 聊天ID
            chat_title: 聊天标题
            chat_type: 聊天类型
            
        Returns:
            MeiliMessageDoc或None（如果构建失败）
        """
        try:
            # 跳过空消息
            if not message.text:
                return None
            
            # 获取发送者信息
            sender_id = 0
            sender_name = None
            
            if message.sender_id:
                sender_id = message.sender_id
                
                try:
                    # 尝试获取发送者详细信息
                    client = self.client.get_client()
                    sender = await client.get_entity(sender_id)
                    
                    if hasattr(sender, 'first_name'):
                        sender_name = format_sender_name(
                            getattr(sender, 'first_name', None),
                            getattr(sender, 'last_name', None)
                        )
                    elif hasattr(sender, 'title'):
                        sender_name = sender.title
                except Exception as e:
                    logger.warning(f"获取发送者 {sender_id} 信息失败: {str(e)}")
            
            # 生成唯一ID和消息链接
            message_id = message.id
            doc_id = f"{chat_id}_{message_id}"
            message_link = generate_message_link(chat_id, message_id)
            
            # 创建文档对象
            return MeiliMessageDoc(
                id=doc_id,
                message_id=message_id,
                chat_id=chat_id,
                chat_title=chat_title,
                chat_type=chat_type,
                sender_id=sender_id,
                sender_name=sender_name,
                text=message.text,
                date=int(message.date.timestamp()),
                message_link=message_link
            )
            
        except Exception as e:
            logger.error(f"构建消息文档时发生错误: {str(e)}")
            return None
    
    async def _index_message_batch(self, message_batch: List[MeiliMessageDoc]) -> bool:
        """
        索引一批消息到Meilisearch
        
        Args:
            message_batch: MeiliMessageDoc对象列表
            
        Returns:
            bool: 索引是否成功
        """
        if not message_batch:
            return True
            
        try:
            # 调用MeiliSearchService的index_messages_bulk方法
            result = self.meili_service.index_messages_bulk(message_batch)
            logger.debug(f"批量索引 {len(message_batch)} 条消息，任务ID: {result.get('taskUid', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"索引消息批次时发生错误: {str(e)}")
            return False
    
    def _update_last_sync_point(self, chat_id: int, message: Message) -> None:
        """
        更新聊天的最后同步点
        
        Args:
            chat_id: 聊天ID
            message: 最后处理的消息
        """
        self.last_sync_points[chat_id] = {
            "message_id": message.id,
            "date": message.date,
            "timestamp": int(time.time())
        }
        
        logger.debug(f"更新聊天 {chat_id} 的最后同步点: message_id={message.id}, date={message.date}")
        
        # TODO: 将最后同步点持久化存储，可以使用ConfigManager或数据库
        # 当前仅在内存中保存，后续可以实现持久化方案


async def sync_chat_history(chat_id: int, limit: Optional[int] = None, offset_date: Optional[datetime] = None) -> Tuple[int, int]:
    """
    同步指定聊天的历史消息（便捷函数）
    
    Args:
        chat_id: 聊天ID
        limit: 最大消息数量，None表示不限制
        offset_date: 开始时间点，None表示从最新消息开始
        
    Returns:
        Tuple[int, int]: (处理的消息数量, 成功索引的消息数量)
    """
    syncer = HistorySyncer()
    return await syncer.sync_chat_history(chat_id, limit, offset_date)


async def initial_sync_all_whitelisted_chats(limit_per_chat: Optional[int] = None) -> Dict[int, Tuple[int, int]]:
    """
    同步所有白名单中聊天的历史消息（便捷函数）
    
    Args:
        limit_per_chat: 每个聊天同步的最大消息数量，None表示不限制
        
    Returns:
        Dict[int, Tuple[int, int]]: 映射聊天ID到处理结果的字典
    """
    syncer = HistorySyncer()
    return await syncer.initial_sync_all_whitelisted_chats(limit_per_chat)