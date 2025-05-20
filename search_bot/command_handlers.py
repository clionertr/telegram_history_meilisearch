"""
命令处理模块

此模块负责处理用户通过 Search Bot 发送的命令，包括：
1. 基本命令：/start, /help
2. 搜索命令：/search <关键词>
3. 管理员命令：/add_whitelist, /remove_whitelist
"""

import logging
import re
from typing import List, Optional, Union, Dict, Any, Tuple
from datetime import datetime

from telethon import events, Button
from telethon.tl.types import User

from core.meilisearch_service import MeiliSearchService
from core.config_manager import ConfigManager
from search_bot.message_formatters import format_search_results, format_error_message, format_help_message

# 配置日志记录器
logger = logging.getLogger(__name__)


class CommandHandlers:
    """
    命令处理器类
    
    负责处理用户通过 Search Bot 发送的各类命令
    """

    def __init__(
        self, 
        client, 
        meilisearch_service: MeiliSearchService, 
        config_manager: ConfigManager,
        admin_ids: List[int]
    ) -> None:
        """
        初始化命令处理器
        
        Args:
            client: Telethon 客户端
            meilisearch_service: Meilisearch 服务实例
            config_manager: 配置管理器实例
            admin_ids: 管理员用户 ID 列表
        """
        self.client = client
        self.meilisearch_service = meilisearch_service
        self.config_manager = config_manager
        self.admin_ids = admin_ids
        
        # 注册命令处理函数
        self.register_handlers()
        
        logger.info("命令处理器已初始化")
    
    def register_handlers(self) -> None:
        """
        注册所有命令处理函数
        """
        # 基本命令
        self.client.add_event_handler(
            self.start_command,
            events.NewMessage(pattern=r"^/start$")
        )
        
        self.client.add_event_handler(
            self.help_command,
            events.NewMessage(pattern=r"^/help$")
        )
        
        # 搜索命令
        self.client.add_event_handler(
            self.search_command,
            events.NewMessage(pattern=r"^/search(?:\s+(.+))?$")
        )
        
        # 管理员命令
        self.client.add_event_handler(
            self.add_whitelist_command,
            events.NewMessage(pattern=r"^/add_whitelist(?:\s+(-?\d+))?$")
        )
        
        self.client.add_event_handler(
            self.remove_whitelist_command,
            events.NewMessage(pattern=r"^/remove_whitelist(?:\s+(-?\d+))?$")
        )
        
        logger.info("已注册所有命令处理函数")
    
    async def is_admin(self, event) -> bool:
        """
        检查用户是否为管理员
        
        Args:
            event: Telethon 事件对象
            
        Returns:
            bool: 用户是否为管理员
        """
        sender = await event.get_sender()
        user_id = sender.id
        
        is_admin = user_id in self.admin_ids
        if not is_admin:
            logger.warning(f"用户 {user_id} 尝试执行管理员命令，但不在管理员列表中")
        
        return is_admin
    
    async def start_command(self, event) -> None:
        """
        处理 /start 命令
        
        发送欢迎消息和基本使用说明
        
        Args:
            event: Telethon 事件对象
        """
        try:
            sender = await event.get_sender()
            user_name = getattr(sender, 'first_name', 'User')
            
            # 构建欢迎消息
            welcome_message = (
                f"👋 **你好，{user_name}！**\n\n"
                f"欢迎使用 Telegram 中文历史消息搜索机器人。\n\n"
                f"你可以通过发送 `/search 关键词` 来搜索历史消息。\n"
                f"例如：`/search Python 教程`\n\n"
                f"发送 `/help` 获取更详细的使用说明和高级搜索语法。"
            )
            
            await event.respond(welcome_message, parse_mode=None)
            logger.info(f"已发送欢迎消息给用户 {sender.id}")
            
        except Exception as e:
            logger.error(f"处理 /start 命令时出错: {e}")
            await event.respond("😕 启动机器人时出现错误，请稍后再试。")
    
    async def help_command(self, event) -> None:
        """
        处理 /help 命令
        
        发送详细的帮助信息，包括搜索语法
        
        Args:
            event: Telethon 事件对象
        """
        try:
            help_message = format_help_message()
            await event.respond(help_message, parse_mode=None)
            logger.info(f"已发送帮助消息给用户 {(await event.get_sender()).id}")
            
        except Exception as e:
            logger.error(f"处理 /help 命令时出错: {e}")
            await event.respond("😕 获取帮助信息时出现错误，请稍后再试。")
    
    async def search_command(self, event) -> None:
        """
        处理 /search 命令
        
        执行搜索并返回结果
        
        Args:
            event: Telethon 事件对象
        """
        try:
            # 获取搜索关键词
            message_text = event.message.text
            match = re.match(r"^/search(?:\s+(.+))?$", message_text)
            
            if not match or not match.group(1):
                await event.respond("请提供搜索关键词，例如：`/search Python 教程`\n发送 `/help` 获取更多使用说明。")
                return
            
            query = match.group(1).strip()
            logger.info(f"用户 {(await event.get_sender()).id} 搜索: {query}")
            
            # 解析高级搜索语法
            filters = None
            parsed_query, filters_dict = self._parse_advanced_syntax(query)
            if filters_dict:
                filters = self._build_meilisearch_filters(filters_dict)
                logger.debug(f"解析后的过滤条件: {filters}")
            
            # 执行搜索
            await event.respond("🔍 正在搜索，请稍候...")
            
            # 默认参数
            page = 1
            hits_per_page = 5
            sort = ["date:desc"]  # 默认按时间倒序
            
            # 调用 Meilisearch 搜索服务
            results = self.meilisearch_service.search(
                query=parsed_query,
                filters=filters,
                sort=sort,
                page=page,
                hits_per_page=hits_per_page
            )
            
            # 计算总页数
            total_hits = results.get('estimatedTotalHits', 0)
            total_pages = (total_hits + hits_per_page - 1) // hits_per_page if total_hits > 0 else 0
            
            # 格式化搜索结果
            formatted_message, buttons = format_search_results(results, page, total_pages)
            
            # 发送结果
            await event.respond(formatted_message, buttons=buttons, parse_mode=None)
            logger.info(f"已向用户 {(await event.get_sender()).id} 发送搜索结果，共 {total_hits} 条")
            
        except Exception as e:
            logger.error(f"处理 /search 命令时出错: {e}")
            error_message = format_error_message(str(e))
            await event.respond(error_message, parse_mode=None)
    
    def _parse_advanced_syntax(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """
        解析高级搜索语法
        
        支持的语法:
        - 精确短语: "关键短语"
        - 类型筛选: type:类型 (user/group/channel)
        - 时间筛选: date:起始_结束 (YYYY-MM-DD_YYYY-MM-DD)
        
        Args:
            query: 原始查询字符串
            
        Returns:
            Tuple[str, Dict[str, Any]]: 处理后的查询和过滤条件字典
        """
        # 初始化结果
        filters = {}
        
        # 处理类型筛选
        type_match = re.search(r'type:(\w+)', query)
        if type_match:
            chat_type = type_match.group(1).lower()
            if chat_type in ['user', 'group', 'channel']:
                filters['chat_type'] = chat_type
                # 从查询中移除 type: 部分
                query = re.sub(r'type:\w+', '', query).strip()
        
        # 处理时间筛选
        date_match = re.search(r'date:(\d{4}-\d{2}-\d{2})(?:_(\d{4}-\d{2}-\d{2}))?', query)
        if date_match:
            start_date = date_match.group(1)
            end_date = date_match.group(2) if date_match.group(2) else datetime.now().strftime('%Y-%m-%d')
            
            # 转换为 Unix 时间戳
            try:
                start_timestamp = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
                # 对于结束日期，设置为当天的最后一秒
                end_timestamp = int(datetime.strptime(end_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S').timestamp())
                
                filters['date_range'] = {
                    'start': start_timestamp,
                    'end': end_timestamp
                }
                
                # 从查询中移除 date: 部分
                query = re.sub(r'date:\d{4}-\d{2}-\d{2}(?:_\d{4}-\d{2}-\d{2})?', '', query).strip()
            except ValueError as e:
                logger.warning(f"日期解析错误: {e}")
        
        # 清理查询字符串，移除多余空格
        clean_query = re.sub(r'\s+', ' ', query).strip()
        
        return clean_query, filters
    
    def _build_meilisearch_filters(self, filters_dict: Dict[str, Any]) -> str:
        """
        构建 Meilisearch 过滤条件字符串
        
        Args:
            filters_dict: 过滤条件字典
            
        Returns:
            str: Meilisearch 过滤条件字符串
        """
        filter_parts = []
        
        # 处理聊天类型过滤
        if 'chat_type' in filters_dict:
            filter_parts.append(f"chat_type = '{filters_dict['chat_type']}'")
        
        # 处理日期范围过滤
        if 'date_range' in filters_dict:
            date_range = filters_dict['date_range']
            filter_parts.append(f"date >= {date_range['start']} AND date <= {date_range['end']}")
        
        # 组合所有过滤条件
        return ' AND '.join(filter_parts) if filter_parts else None
    
    async def add_whitelist_command(self, event) -> None:
        """
        处理 /add_whitelist 命令 (管理员权限)
        
        添加聊天到白名单
        
        Args:
            event: Telethon 事件对象
        """
        try:
            # 检查权限
            if not await self.is_admin(event):
                await event.respond("⚠️ 此命令需要管理员权限。")
                return
            
            # 获取 chat_id
            message_text = event.message.text
            match = re.match(r"^/add_whitelist(?:\s+(-?\d+))?$", message_text)
            
            if not match or not match.group(1):
                await event.respond("请提供要添加的 chat_id，例如：`/add_whitelist -1001234567890`")
                return
            
            chat_id = int(match.group(1))
            
            # 添加到白名单
            success = self.config_manager.add_to_whitelist(chat_id)
            
            if success:
                await event.respond(f"✅ 已成功将 chat_id `{chat_id}` 添加到白名单。")
                logger.info(f"管理员 {(await event.get_sender()).id} 添加 {chat_id} 到白名单")
            else:
                await event.respond(f"ℹ️ chat_id `{chat_id}` 已在白名单中，无需重复添加。")
            
        except Exception as e:
            logger.error(f"处理 /add_whitelist 命令时出错: {e}")
            await event.respond(f"⚠️ 添加白名单时出现错误: {str(e)}")
    
    async def remove_whitelist_command(self, event) -> None:
        """
        处理 /remove_whitelist 命令 (管理员权限)
        
        从白名单移除聊天
        
        Args:
            event: Telethon 事件对象
        """
        try:
            # 检查权限
            if not await self.is_admin(event):
                await event.respond("⚠️ 此命令需要管理员权限。")
                return
            
            # 获取 chat_id
            message_text = event.message.text
            match = re.match(r"^/remove_whitelist(?:\s+(-?\d+))?$", message_text)
            
            if not match or not match.group(1):
                await event.respond("请提供要移除的 chat_id，例如：`/remove_whitelist -1001234567890`")
                return
            
            chat_id = int(match.group(1))
            
            # 从白名单移除
            success = self.config_manager.remove_from_whitelist(chat_id)
            
            if success:
                await event.respond(f"✅ 已成功将 chat_id `{chat_id}` 从白名单移除。")
                logger.info(f"管理员 {(await event.get_sender()).id} 从白名单移除 {chat_id}")
            else:
                await event.respond(f"ℹ️ chat_id `{chat_id}` 不在白名单中，无需移除。")
            
        except Exception as e:
            logger.error(f"处理 /remove_whitelist 命令时出错: {e}")
            await event.respond(f"⚠️ 移除白名单时出现错误: {str(e)}")


# 辅助函数：创建命令处理器并注册到客户端
def setup_command_handlers(
    client, 
    meilisearch_service: MeiliSearchService, 
    config_manager: ConfigManager,
    admin_ids: List[int]
) -> CommandHandlers:
    """
    创建命令处理器并将其注册到客户端
    
    Args:
        client: Telethon 客户端
        meilisearch_service: Meilisearch 服务实例
        config_manager: 配置管理器实例
        admin_ids: 管理员用户 ID 列表
        
    Returns:
        CommandHandlers: 命令处理器实例
    """
    handler = CommandHandlers(
        client=client,
        meilisearch_service=meilisearch_service,
        config_manager=config_manager,
        admin_ids=admin_ids
    )
    
    return handler