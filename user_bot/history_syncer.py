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
from core.config_manager import ConfigManager, SyncPointManager
# 删除对 UserBotClient 的直接导入，避免循环导入
from user_bot.utils import generate_message_link, format_sender_name, determine_chat_type

# 配置日志记录器
logger = logging.getLogger(__name__)

# 常量定义
BATCH_SIZE = 100  # 每批处理的消息数量
RATE_LIMIT_WAIT = 0  # 消息间隔，避免触发Telegram的速率限制（秒）
MAX_ATTEMPTS = 3  # 最大重试次数


class HistorySyncer:
    """
    历史消息同步器类
    
    负责从Telegram获取历史消息并同步到Meilisearch
    """
    
    def __init__(
        self,
        client: Optional[Any] = None,  # 使用 Any 类型替代 UserBotClient
        config_manager: Optional[ConfigManager] = None,
        meili_service: Optional[MeiliSearchService] = None,
        sync_point_manager: Optional[SyncPointManager] = None
    ) -> None:
        """
        初始化历史消息同步器
        
        Args:
            client: UserBotClient实例，如果未提供则创建新实例
            config_manager: ConfigManager实例，如果未提供则创建新实例
            meili_service: MeiliSearchService实例，如果未提供则创建新实例
        """
        # 延迟导入 UserBotClient，避免循环依赖
        if client is None:
            from user_bot.client import UserBotClient
            self.client = UserBotClient()
        else:
            self.client = client
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
        
        # 初始化同步点管理器（如果未提供）
        self.sync_point_manager = sync_point_manager or SyncPointManager()
        
        # 保留内存中的最后同步点（向后兼容）
        self.last_sync_points: Dict[int, Dict[str, Any]] = {}
        
        logger.info("历史消息同步器初始化完成")

    async def sync_chat_history(
        self,
        chat_id: int,
        limit: Optional[int] = None,
        offset_date: Optional[datetime] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        incremental: bool = True
    ) -> Tuple[int, int]:
        """
        同步指定聊天的历史消息
        
        从指定的chat_id拉取历史消息，分批处理并索引到Meilisearch。
        支持增量同步（基于最后同步点）和时间范围筛选。
        
        Args:
            chat_id: 聊天ID
            limit: 最大消息数量，None表示不限制
            offset_date: 开始时间点，None表示从最新消息开始（被增量同步或date_from覆盖时忽略）
            date_from: 开始日期，仅同步该日期之后的消息
            date_to: 结束日期，仅同步该日期之前的消息
            incremental: 是否启用增量同步，为True时会查找上次同步点并从那开始同步
            
        Returns:
            Tuple[int, int]: (处理的消息数量, 成功索引的消息数量)
        """
        # 确定同步模式和范围
        sync_mode = "全量同步"
        min_id: Optional[int] = None  # 用于 Telethon iter_messages 的最小消息 ID（仅获取更新的消息）
        last_sync_point = None
        
        # 如果启用增量同步，尝试获取最后同步点
        if incremental:
            last_sync_point = self.sync_point_manager.get_sync_point(chat_id)
            if last_sync_point:
                sync_mode = "增量同步"
                # 使用最后同步点的消息ID和日期
                message_id = last_sync_point.get("message_id")
                last_date_timestamp = last_sync_point.get("date")
                last_date = datetime.fromtimestamp(last_date_timestamp) if last_date_timestamp else None
                
                logger.info(f"检索到聊天 {chat_id} 的最后同步点: message_id={message_id}, date={last_date}")
                
                # 如果提供了date_from，则使用date_from和last_date中较新的一个
                if date_from and last_date and date_from > last_date:
                    min_id = message_id
                    offset_date = date_from
                    logger.info(f"使用指定的date_from({date_from})作为开始时间点，因为它比最后同步日期({last_date})更新")
                elif last_date:
                    # 对于增量同步，只需要保证新的消息被拉取。Telethon 提供的 `min_id` 参数
                    # 可以让我们只获取 *比指定 ID 更新* 的消息，方向仍然是从新到旧。
                    # 这样可以避免使用 offset_date 导致只能获取更旧消息的问题。
                    min_id = message_id  # 只获取 ID 大于此值的消息
                    offset_date = None  # 避免与 min_id 冲突
                    logger.info(
                        f"使用 min_id={min_id} 进行增量同步，只拉取比 message_id 更新的消息")
            else:
                logger.info(f"未找到聊天 {chat_id} 的同步点，将执行全量同步")
        
        # 时间范围筛选
        if date_from and (not offset_date or date_from > offset_date):
            offset_date = date_from
            logger.info(f"使用date_from({date_from})作为开始时间点")
            
        if date_to:
            logger.info(f"将仅同步 {date_to} 之前的消息")
        
        logger.info(f"开始{sync_mode}聊天 {chat_id} 的历史消息")
        
        # 获取最旧同步时间戳
        oldest_sync_timestamp = self.config_manager.get_oldest_sync_timestamp(chat_id)
        if oldest_sync_timestamp:
            logger.info(f"聊天 {chat_id} 的最旧同步时间戳: {oldest_sync_timestamp}")
        
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
            
            # 构造 iter_messages 的参数字典，按需选择 min_id 或 offset_date
            iter_kwargs = {
                "limit": limit,
                "wait_time": RATE_LIMIT_WAIT
            }
            if min_id is not None:
                iter_kwargs["min_id"] = min_id
            elif offset_date is not None:
                iter_kwargs["offset_date"] = offset_date

            async for message in client.iter_messages(
                chat_id,
                **iter_kwargs
            ):
                # 跳过非文本消息
                if not message.text:
                    continue
                    
                # 时间范围过滤 - 如果设置了date_to且消息日期晚于date_to，跳过
                if date_to and message.date > date_to:
                    continue
                
                # 检查是否早于最旧同步时间戳，如果是则停止向前同步
                if oldest_sync_timestamp and message.date <= oldest_sync_timestamp:
                    logger.info(f"遇到早于最旧同步时间戳的消息 (消息日期: {message.date}, 最旧时间戳: {oldest_sync_timestamp})，停止同步")
                    break
                
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
                    
                    # 如果还有消息但是它们早于最旧同步时间戳，记录这个情况
                    if oldest_sync_timestamp:
                        logger.info(f"由于最旧同步时间戳限制 ({oldest_sync_timestamp})，可能有些较早消息未被同步")
            
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
                return await self.sync_chat_history(
                    chat_id=chat_id,
                    limit=limit,
                    offset_date=offset_date,
                    date_from=date_from,
                    date_to=date_to,
                    incremental=incremental
                )
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
    
    async def initial_sync_all_whitelisted_chats(
        self,
        limit_per_chat: Optional[int] = None,
        incremental: bool = True,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[int, Tuple[int, int]]:
        """
        同步所有白名单中聊天的历史消息
        
        遍历配置管理器中的白名单，对每个聊天执行历史同步
        
        Args:
            limit_per_chat: 每个聊天同步的最大消息数量，None表示不限制
            incremental: 是否启用增量同步，为True时会查找上次同步点并从那开始同步
            date_from: 开始日期，仅同步该日期之后的消息
            date_to: 结束日期，仅同步该日期之前的消息
            
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
                processed, indexed = await self.sync_chat_history(
                    chat_id=chat_id,
                    limit=limit_per_chat,
                    incremental=incremental,
                    date_from=date_from,
                    date_to=date_to
                )
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
            sender_name = "未知发送者"  # 默认值
            
            # 1. 尝试多种方式获取sender_id
            # 首先尝试message.sender_id
            if getattr(message, 'sender_id', None) is not None:
                sender_id = message.sender_id
            # 如果sender_id还是0，尝试从from_id获取
            elif hasattr(message, 'from_id') and message.from_id is not None:
                # from_id可能是PeerUser、PeerChat或PeerChannel对象
                if hasattr(message.from_id, 'user_id'):
                    sender_id = message.from_id.user_id
                elif hasattr(message.from_id, 'chat_id'):
                    sender_id = message.from_id.chat_id
                elif hasattr(message.from_id, 'channel_id'):
                    sender_id = message.from_id.channel_id
            # 如果sender_id还是0，尝试从sender对象获取
            elif hasattr(message, 'sender') and message.sender is not None:
                if hasattr(message.sender, 'id'):
                    sender_id = message.sender.id
            
            # 2. 尝试获取sender_name
            try:
                if hasattr(message, 'sender') and message.sender is not None:
                    sender = message.sender
                    # 根据不同类型的sender获取名称
                    if hasattr(sender, 'first_name') or hasattr(sender, 'last_name'):
                        # 用户类型
                        sender_name = format_sender_name(
                            getattr(sender, 'first_name', None),
                            getattr(sender, 'last_name', None)
                        )
                    elif hasattr(sender, 'title'):
                        # 群组或频道类型
                        sender_name = getattr(sender, 'title', "未知发送者")
                    
                    # 如果sender_name为空或None，使用username作为备选
                    if not sender_name or sender_name == "未知发送者":
                        if hasattr(sender, 'username') and sender.username:
                            sender_name = f"@{sender.username}"
                
                # 记录debug日志，帮助诊断信息获取情况
                if sender_id != 0 and sender_name != "未知发送者":
                    logger.debug(f"成功获取发送者信息: sender_id={sender_id}, sender_name={sender_name}")
                else:
                    # 记录详细的警告日志，帮助诊断问题
                    sender_info = {
                        "sender_id": getattr(message, 'sender_id', None),
                        "from_id": getattr(message, 'from_id', None),
                        "sender": getattr(message, 'sender', None)
                    }
                    logger.warning(f"无法完全获取发送者信息，使用部分信息。sender_id={sender_id}, "
                                  f"sender_name={sender_name}, message属性={sender_info}")
            except Exception as e:
                logger.warning(f"解析发送者信息时发生异常: {str(e)}")
            
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
            
            # 适配新版 Meilisearch API 返回值处理
            # TaskInfo 对象可能有 task_uid 或 uid 属性
            task_id = "unknown"
            if hasattr(result, 'task_uid'):
                task_id = result.task_uid
            elif hasattr(result, 'uid'):
                task_id = result.uid
            elif isinstance(result, dict) and 'taskUid' in result:
                # 兼容旧版 API
                task_id = result['taskUid']
                
            logger.debug(f"批量索引 {len(message_batch)} 条消息，任务ID: {task_id}")
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
        # 保存在内存中（向后兼容）
        current = self.last_sync_points.get(chat_id)
        if not current or message.id > current.get("message_id", 0):
            self.last_sync_points[chat_id] = {
                "message_id": message.id,
                "date": message.date,
                "timestamp": int(time.time())
            }

            logger.debug(
                f"更新聊天 {chat_id} 的最后同步点: message_id={message.id}, date={message.date}"
            )

            # 持久化存储同步点
            self.sync_point_manager.update_sync_point(
                chat_id=chat_id,
                message_id=message.id,
                date=message.date,
                additional_info={"timestamp": int(time.time())}
            )


async def sync_chat_history(
    chat_id: int,
    limit: Optional[int] = None,
    offset_date: Optional[datetime] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    incremental: bool = True
) -> Tuple[int, int]:
    """
    同步指定聊天的历史消息（便捷函数）
    
    Args:
        chat_id: 聊天ID
        limit: 最大消息数量，None表示不限制
        offset_date: 开始时间点，None表示从最新消息开始
        date_from: 开始日期，仅同步该日期之后的消息
        date_to: 结束日期，仅同步该日期之前的消息
        incremental: 是否启用增量同步，为True时会查找上次同步点并从那开始同步
        
    Returns:
        Tuple[int, int]: (处理的消息数量, 成功索引的消息数量)
    """
    syncer = HistorySyncer()
    return await syncer.sync_chat_history(
        chat_id=chat_id,
        limit=limit,
        offset_date=offset_date,
        date_from=date_from,
        date_to=date_to,
        incremental=incremental
    )


async def initial_sync_all_whitelisted_chats(
    client = None,  # 移除类型注解以避免循环导入
    config_manager: Optional[ConfigManager] = None,
    meilisearch_service: Optional[MeiliSearchService] = None,
    sync_point_manager: Optional[SyncPointManager] = None,
    limit_per_chat: Optional[int] = None,
    incremental: bool = True,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> Dict[int, Tuple[int, int]]:
    """
    同步所有白名单中聊天的历史消息（便捷函数）
    
    此函数允许在调用时直接传入所需依赖，而不必创建新的实例。
    
    Args:
        client: TelegramClient实例（优先使用）
        config_manager: ConfigManager实例（优先使用）
        meilisearch_service: MeiliSearchService实例（优先使用）
        limit_per_chat: 每个聊天同步的最大消息数量，None表示不限制
        
    Returns:
        Dict[int, Tuple[int, int]]: 映射聊天ID到处理结果的字典，
                                  值为元组(处理的消息数量, 成功索引的消息数量)
    """
    # 延迟导入 UserBotClient，避免循环导入
    from user_bot.client import UserBotClient
    
    # 如果提供了所有依赖项，使用UserBotClient的客户端而非创建新实例
    if client and config_manager and meilisearch_service:
        user_bot_client = UserBotClient()
        user_bot_client._client = client  # 直接使用传入的客户端
        
        syncer = HistorySyncer(
            client=user_bot_client,
            config_manager=config_manager,
            meili_service=meilisearch_service,
            sync_point_manager=sync_point_manager
        )
    else:
        # 向后兼容：未提供完整依赖时创建新实例
        syncer = HistorySyncer()
    
    # 使用修改后的函数签名调用同步方法
    results = await syncer.initial_sync_all_whitelisted_chats(
        limit_per_chat=limit_per_chat,
        incremental=incremental,
        date_from=date_from,
        date_to=date_to
    )
    return results


async def sync_chat_history_by_date_range(
    chat_id: int,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: Optional[int] = None
) -> Tuple[int, int]:
    """
    在指定的时间范围内同步聊天历史消息
    
    此函数是一个便捷包装器，用于按日期范围获取历史消息
    
    Args:
        chat_id: 聊天ID
        date_from: 开始日期
        date_to: 结束日期
        limit: 最大消息数量，None表示不限制
        
    Returns:
        Tuple[int, int]: (处理的消息数量, 成功索引的消息数量)
    """
    # 创建同步器实例
    syncer = HistorySyncer()
    
    # 调用基础函数，禁用增量同步，使用日期范围
    return await syncer.sync_chat_history(
        chat_id=chat_id,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        incremental=False  # 禁用增量同步，仅按日期同步
    )