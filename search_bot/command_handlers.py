"""
命令处理模块

此模块负责处理用户通过 Search Bot 发送的命令，包括：
1. 基本命令：/start, /help
2. 搜索命令：/search <关键词>
3. 管理员命令：/add_whitelist, /remove_whitelist
"""

import logging
import re
import asyncio
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
        admin_ids: List[int],
        userbot_restart_event: Optional[asyncio.Event] = None
    ) -> None:
        """
        初始化命令处理器
        
        Args:
            client: Telethon 客户端
            meilisearch_service: Meilisearch 服务实例
            config_manager: 配置管理器实例
            admin_ids: 管理员用户 ID 列表
            userbot_restart_event: User Bot 重启事件，用于触发重启
        """
        self.client = client
        self.meilisearch_service = meilisearch_service
        self.config_manager = config_manager
        self.admin_ids = admin_ids
        self.userbot_restart_event = userbot_restart_event
        
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
        
        # User Bot 配置相关命令
        self.client.add_event_handler(
            self.set_userbot_config_command,
            events.NewMessage(pattern=r"^/set_userbot_config(?:\s+(\S+))?(?:\s+(.+))?$")
        )
        
        self.client.add_event_handler(
            self.view_userbot_config_command,
            events.NewMessage(pattern=r"^/view_userbot_config$")
        )
        
        self.client.add_event_handler(
            self.restart_userbot_command,
            events.NewMessage(pattern=r"^/restart_userbot$")
        )

        # 新增：处理普通文本消息作为搜索（应在所有特定命令之后注册）
        self.client.add_event_handler(
            self.handle_plain_text_message,
            events.NewMessage(func=self._is_plain_text_and_not_command)
        )
        
        logger.info("已注册所有命令处理函数，包括普通文本搜索处理器")
    
    def _is_plain_text_and_not_command(self, event) -> bool:
        """
        检查消息是否为普通文本消息，并且不是一个已知的命令。
        只处理来自用户的消息，忽略频道广播等。
        """
        # 确保消息来自用户 (不是频道自动发布等)
        if not event.is_private and not event.is_group: # 简单判断，可根据需求调整
             if event.chat and hasattr(event.chat, 'broadcast') and event.chat.broadcast:
                 return False # 是频道广播

        if not event.message or not event.message.text:
            return False # 没有文本内容 (例如图片、贴纸)
        
        text = event.message.text.strip()
        if not text: # 消息为空或只有空格
            return False

        # 检查是否以已知命令前缀开头
        # 注意：这里的命令列表应该与 register_handlers 中注册的命令保持一致
        known_commands_patterns = [
            r"^/start$",
            r"^/help$",
            r"^/search(?:\s+(.+))?$",
            r"^/add_whitelist(?:\s+(-?\d+))?$",
            r"^/remove_whitelist(?:\s+(-?\d+))?$",
            r"^/set_userbot_config(?:\s+(\S+))?(?:\s+(.+))?$",
            r"^/view_userbot_config$",
            r"^/restart_userbot$"
        ]
        
        for pattern in known_commands_patterns:
            if re.match(pattern, text):
                return False # 匹配已知命令格式

        # 进一步排除任何以 / 开头的消息，以防有未明确列出的命令
        if text.startswith('/'):
            return False
            
        return True # 是普通文本消息，且不是已知命令

    async def handle_plain_text_message(self, event) -> None:
        """
        处理普通文本消息，将其作为搜索查询。
        """
        query = event.message.text.strip()
        # 确保查询不为空（虽然 _is_plain_text_and_not_command 已经检查过）
        if not query:
            return

        logger.info(f"接收到普通文本消息，将作为搜索查询: '{query}' from user {(await event.get_sender()).id}")
        await self._perform_search(event, query, is_direct_search=True)

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
            
            await event.respond(welcome_message, parse_mode='md') # 启用 Markdown
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
            await event.respond(help_message, parse_mode='md') # 启用 Markdown
            logger.info(f"已发送帮助消息给用户 {(await event.get_sender()).id}")
            
        except Exception as e:
            logger.error(f"处理 /help 命令时出错: {e}")
            await event.respond("😕 获取帮助信息时出现错误，请稍后再试。")
    
    async def _perform_search(self, event, query: str, is_direct_search: bool = False) -> None:
        """
        执行搜索操作并回复结果。
        
        Args:
            event: Telethon 事件对象。
            query: 搜索关键词。
            is_direct_search: 是否为直接无命令搜索 (用于未来可能的提示)。
        """
        try:
            logger.info(f"用户 {(await event.get_sender()).id} 搜索: {query}")
            
            # 解析高级搜索语法
            filters = None
            parsed_query, filters_dict = self._parse_advanced_syntax(query)
            if filters_dict:
                filters = self._build_meilisearch_filters(filters_dict)
                logger.debug(f"解析后的过滤条件: {filters}")
            
            # 执行搜索
            # 首先发送一个 "正在搜索" 的提示消息
            try:
                # 尝试编辑消息，如果用户快速连续发送，可能会失败
                # 但对于命令搜索，通常是新消息，所以直接 respond
                if event.is_reply or is_direct_search: # 假设直接搜索可能需要编辑之前的 "正在处理"
                     await event.edit("🔍 正在搜索，请稍候...")
                else:
                    await event.respond("🔍 正在搜索，请稍候...")
            except Exception: # pylint: disable=broad-except
                 # 如果编辑失败（例如消息太旧或权限问题），则发送新消息
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
            # 对于直接搜索，我们可能需要编辑之前的 "正在搜索" 消息
            # 对于命令搜索，通常是新消息，所以直接 respond
            # 为了简化，我们统一使用 respond，Telethon 会处理好
            await event.respond(formatted_message, buttons=buttons, parse_mode='md') # 启用 Markdown
            logger.info(f"已向用户 {(await event.get_sender()).id} 发送搜索结果，共 {total_hits} 条")

            # TODO: （可选）如果 is_direct_search 为 True 且结果为空，可以发送提示信息
            # if is_direct_search and total_hits == 0:
            #     await event.respond("💡 你可以直接发送关键词进行搜索哦！如果需要帮助，请发送 /help。")

        except Exception as e:
            logger.error(f"执行搜索时出错 (query: {query}): {e}")
            error_message = format_error_message(str(e))
            await event.respond(error_message, parse_mode='md') # 启用 Markdown

    async def search_command(self, event) -> None:
        """
        处理 /search 命令
        
        执行搜索并返回结果
        
        Args:
            event: Telethon 事件对象
        """
        message_text = event.message.text
        match = re.match(r"^/search(?:\s+(.+))?$", message_text)
        
        if not match or not match.group(1):
            await event.respond("请提供搜索关键词，例如：`/search Python 教程`\n发送 `/help` 获取更多使用说明。")
            return
        
        query = match.group(1).strip()
        await self._perform_search(event, query)
    
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
                await event.respond(f"✅ 已成功将 chat_id `{chat_id}` 添加到白名单。", parse_mode='md') # 启用 Markdown
                logger.info(f"管理员 {(await event.get_sender()).id} 添加 {chat_id} 到白名单")
            else:
                await event.respond(f"ℹ️ chat_id `{chat_id}` 已在白名单中，无需重复添加。", parse_mode='md') # 启用 Markdown
            
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
                await event.respond(f"✅ 已成功将 chat_id `{chat_id}` 从白名单移除。", parse_mode='md') # 启用 Markdown
                logger.info(f"管理员 {(await event.get_sender()).id} 从白名单移除 {chat_id}")
            else:
                await event.respond(f"ℹ️ chat_id `{chat_id}` 不在白名单中，无需移除。", parse_mode='md') # 启用 Markdown
            
        except Exception as e:
            logger.error(f"处理 /remove_whitelist 命令时出错: {e}")
            await event.respond(f"⚠️ 移除白名单时出现错误: {str(e)}")
            
    async def set_userbot_config_command(self, event) -> None:
        """
        处理 /set_userbot_config 命令 (管理员权限)
        
        设置 User Bot 配置项
        
        Args:
            event: Telethon 事件对象
        """
        try:
            # 检查权限
            if not await self.is_admin(event):
                await event.respond("⚠️ 此命令需要管理员权限。")
                return
            
            # 获取参数
            message_text = event.message.text
            match = re.match(r"^/set_userbot_config(?:\s+(\S+))?(?:\s+(.+))?$", message_text)
            
            if not match or not match.group(1):
                help_text = """请提供要设置的配置项和值，例如：
`/set_userbot_config USER_SESSION_NAME my_session`

可设置的配置项包括：
- `USER_API_ID` - Telegram API ID
- `USER_API_HASH` - Telegram API Hash
- `USER_SESSION_NAME` - 会话名称（如需修改，需要重启 User Bot）
- `USER_PROXY_URL` - 代理服务器 URL（如需使用）

⚠️ 注意：修改配置后，需要使用 `/restart_userbot` 命令使配置生效。"""
            await event.respond(help_text, parse_mode='md') # 启用 Markdown
            return
            
            key = match.group(1).upper()  # 转为大写
            if not match.group(2):
                await event.respond(f"请提供 `{key}` 的值，例如：`/set_userbot_config {key} value`")
                return
                
            value = match.group(2).strip()
            
            # 添加USER_前缀（如果没有）
            if not key.startswith("USER_"):
                key = f"USER_{key}"
                
            # 设置配置
            self.config_manager.set_userbot_env(key, value)
            
            # 发送成功消息
            await event.respond(f"✅ 已设置 User Bot 配置项 `{key}` = `{value if key != 'USER_API_HASH' else '******'}`\n\n使用 `/restart_userbot` 命令使配置生效。", parse_mode='md') # 启用 Markdown
            logger.info(f"管理员 {(await event.get_sender()).id} 设置 User Bot 配置项 {key}")
            
        except Exception as e:
            logger.error(f"处理 /set_userbot_config 命令时出错: {e}")
            await event.respond(f"⚠️ 设置 User Bot 配置时出现错误: {str(e)}")
            
    async def view_userbot_config_command(self, event) -> None:
        """
        处理 /view_userbot_config 命令 (管理员权限)
        
        查看 User Bot 当前配置
        
        Args:
            event: Telethon 事件对象
        """
        try:
            # 检查权限
            if not await self.is_admin(event):
                await event.respond("⚠️ 此命令需要管理员权限。")
                return
            
            # 获取配置
            config_dict = self.config_manager.get_userbot_config_dict(exclude_sensitive=True)
            
            if not config_dict:
                await event.respond("ℹ️ User Bot 尚未配置任何环境变量。使用 `/set_userbot_config` 命令进行配置。")
                return
                
            # 格式化配置信息
            config_text = "📝 **User Bot 当前配置**\n\n"
            for key, value in config_dict.items():
                config_text += f"- `{key}` = `{value}`\n"
                
            config_text += "\n使用 `/set_userbot_config <key> <value>` 修改配置，使用 `/restart_userbot` 使配置生效。"
            
            await event.respond(config_text, parse_mode='md') # 启用 Markdown
            logger.info(f"管理员 {(await event.get_sender()).id} 查看 User Bot 配置")
            
        except Exception as e:
            logger.error(f"处理 /view_userbot_config 命令时出错: {e}")
            await event.respond(f"⚠️ 查看 User Bot 配置时出现错误: {str(e)}")
            
    async def restart_userbot_command(self, event) -> None:
        """
        处理 /restart_userbot 命令 (管理员权限)
        
        重启 User Bot
        
        Args:
            event: Telethon 事件对象
        """
        try:
            # 检查权限
            if not await self.is_admin(event):
                await event.respond("⚠️ 此命令需要管理员权限。")
                return
            
            # 检查是否有重启事件
            if not self.userbot_restart_event:
                await event.respond("⚠️ 重启功能未初始化，无法重启 User Bot。")
                logger.error("尝试重启 User Bot，但 userbot_restart_event 未初始化")
                return
                
            # 发送重启消息
            await event.respond("🔄 正在重启 User Bot，请稍候...")
            logger.info(f"管理员 {(await event.get_sender()).id} 触发 User Bot 重启")
            
            # 设置重启事件
            self.userbot_restart_event.set()
            
            # 等待一段时间，让重启过程完成
            await asyncio.sleep(5)
            
            # 发送重启完成消息
            await event.respond("✅ User Bot 已重新启动，新配置已生效。")
            
        except Exception as e:
            logger.error(f"处理 /restart_userbot 命令时出错: {e}")
            await event.respond(f"⚠️ 重启 User Bot 时出现错误: {str(e)}")


# 辅助函数：创建命令处理器并注册到客户端
def setup_command_handlers(
    client,
    meilisearch_service: MeiliSearchService,
    config_manager: ConfigManager,
    admin_ids: List[int],
    userbot_restart_event: Optional[asyncio.Event] = None
) -> CommandHandlers:
    """
    创建命令处理器并将其注册到客户端
    
    Args:
        client: Telethon 客户端
        meilisearch_service: Meilisearch 服务实例
        config_manager: 配置管理器实例
        admin_ids: 管理员用户 ID 列表
        userbot_restart_event: User Bot 重启事件，用于触发重启
        
    Returns:
        CommandHandlers: 命令处理器实例
    """
    handler = CommandHandlers(
        client=client,
        meilisearch_service=meilisearch_service,
        config_manager=config_manager,
        admin_ids=admin_ids,
        userbot_restart_event=userbot_restart_event
    )
    
    return handler