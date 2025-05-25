"""
Search Bot 客户端模块

此模块提供了与 Telegram Bot API 交互的客户端功能，包括：
1. 初始化和管理 Telethon 客户端（使用 Bot Token 认证）
2. 注册命令处理器和回调查询处理器
3. 启动客户端服务响应用户交互
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import Optional
import asyncio

from telethon import TelegramClient
from telethon.errors import ApiIdInvalidError, AuthKeyUnregisteredError
from telethon.tl.types import BotCommand
from telethon.tl.functions.bots import SetBotCommandsRequest
from telethon.tl.types import BotCommandScopeDefault

from core.config_manager import ConfigManager
from core.meilisearch_service import MeiliSearchService
from search_bot.command_handlers import CommandHandlers
from search_bot.callback_query_handlers import CallbackQueryHandlers

# 配置日志记录器
logger = logging.getLogger(__name__)

# 会话文件目录
SESSIONS_DIR = ".sessions"

# 默认命令列表，用于设置Telegram Bot的快捷命令
DEFAULT_COMMANDS = [
    BotCommand(command="start", description="欢迎使用并显示帮助信息"),
    BotCommand(command="help", description="显示帮助信息"),
    BotCommand(command="search", description="搜索消息，支持高级语法"),
    BotCommand(command="get_dialogs", description="获取用户所有对话列表 (管理员)"),
    BotCommand(command="add_whitelist", description="添加用户/群组到白名单 (管理员)"),
    BotCommand(command="remove_whitelist", description="从白名单移除用户/群组 (管理员)"),
    BotCommand(command="set_userbot_config", description="设置User Bot的API ID和HASH (管理员)"),
    BotCommand(command="view_userbot_config", description="查看User Bot的API ID和HASH (管理员)"),
    BotCommand(command="restart_userbot", description="重启User Bot (管理员)"),
    BotCommand(command="set_oldest_sync_time", description="设置最旧同步时间 (管理员)"),
    BotCommand(command="view_oldest_sync_time", description="查看最旧同步时间 (管理员)"),
    BotCommand(command="view_search_config", description="查看搜索缓存配置 (管理员)"),
    BotCommand(command="set_search_config", description="设置搜索缓存配置 (管理员)"),
    BotCommand(command="clear_search_cache", description="清空搜索缓存 (管理员)"),
    BotCommand(command="view_dialogs_cache", description="查看对话缓存状态 (管理员)"),
    BotCommand(command="clear_dialogs_cache", description="清空对话缓存 (管理员)"),
]


class SearchBot:
    """
    Search Bot 客户端类
    
    负责初始化 Telethon 客户端（使用 Bot Token 认证）、
    注册事件处理器并启动客户端服务。
    """
    
    def __init__(self, session_name: str = "search_bot", userbot_restart_event: Optional[asyncio.Event] = None) -> None:
        """
        初始化 Search Bot 客户端
        
        Args:
            session_name: 会话文件名，默认为 "search_bot"
            userbot_restart_event: User Bot 重启事件，用于重启 User Bot
        """
        # 存储User Bot重启事件
        self.userbot_restart_event = userbot_restart_event
        # 确保会话目录存在
        self._ensure_sessions_dir_exists()
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        self.session_name = session_name
        
        # 构建会话文件路径
        session_path = os.path.join(SESSIONS_DIR, session_name)
        
        # 从配置获取 API 凭据
        # 首先尝试从环境变量获取
        api_id = self.config_manager.get_env("TELEGRAM_API_ID")
        api_hash = self.config_manager.get_env("TELEGRAM_API_HASH")
        self.bot_token = self.config_manager.get_env("TELEGRAM_BOT_TOKEN")
        
        # 如果环境变量中没有，则从配置文件中获取
        if not api_id:
            api_id = self.config_manager.get_config("Telegram", "API_ID")
        if not api_hash:
            api_hash = self.config_manager.get_config("Telegram", "API_HASH")
        if not self.bot_token:
            self.bot_token = self.config_manager.get_config("Telegram", "BOT_TOKEN")
        
        # 验证 API 凭据
        if not api_id or not api_hash:
            error_msg = "未找到 Telegram API 凭据，请在环境变量或配置文件中设置 TELEGRAM_API_ID 和 TELEGRAM_API_HASH"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 验证 Bot Token
        if not self.bot_token:
            error_msg = "未找到 Telegram Bot Token，请在环境变量或配置文件中设置 TELEGRAM_BOT_TOKEN"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 转换 api_id 为整数（Telethon 要求）
        try:
            api_id = int(api_id)
        except ValueError:
            logger.error(f"API_ID 必须是整数，当前值: {api_id}")
            raise ValueError(f"API_ID 必须是整数，当前值: {api_id}")
        
        # 初始化 TelegramClient
        logger.info(f"初始化 Search Bot TelegramClient，会话文件: {session_path}")
        self.client = TelegramClient(session_path, api_id, api_hash)
        
        # 初始化 MeiliSearch 服务
        meili_host = self.config_manager.get_env("MEILISEARCH_HOST") or \
                     self.config_manager.get_config("MeiliSearch", "HOST", "http://localhost:7700")
        meili_api_key = self.config_manager.get_env("MEILISEARCH_API_KEY") or \
                        self.config_manager.get_config("MeiliSearch", "API_KEY")
        self.meilisearch_service = MeiliSearchService(meili_host, meili_api_key)
        
        # 获取管理员 ID 列表
        admin_ids_str = self.config_manager.get_env("ADMIN_IDS") or \
                        self.config_manager.get_config("Telegram", "ADMIN_IDS", "")
        self.admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(",") if id_str.strip()] if admin_ids_str else []
        
        # 初始化事件处理器（在注册前不实例化）
        self.command_handlers = None
        self.callback_query_handlers = None
    
    def _ensure_sessions_dir_exists(self) -> None:
        """
        确保会话文件目录存在
        
        创建 .sessions 目录（如果不存在）
        """
        Path(SESSIONS_DIR).mkdir(exist_ok=True)
        logger.debug(f"确保会话目录存在: {SESSIONS_DIR}")
    
    def register_event_handlers(self) -> None:
        """
        注册所有事件处理器
        
        初始化并注册命令处理器和回调查询处理器
        """
        # 初始化命令处理器和回调查询处理器
        self.command_handlers = CommandHandlers(
            client=self.client,
            meilisearch_service=self.meilisearch_service,
            config_manager=self.config_manager,
            admin_ids=self.admin_ids,
            userbot_restart_event=self.userbot_restart_event
        )
        
        self.callback_query_handlers = CallbackQueryHandlers(
            client=self.client,
            command_handler=self.command_handlers # Pass CommandHandlers instance
        )
        
        logger.info("已注册所有事件处理器")
    
    async def set_bot_commands(self) -> None:
        """
        设置Bot的快捷命令列表
        
        将预定义的命令列表发送给BotFather，使用户在与Bot对话时
        可以看到命令提示和自动完成。
        """
        try:
            # 使用正确的Telethon API设置Bot命令列表
            await self.client(SetBotCommandsRequest(
                scope=BotCommandScopeDefault(),
                lang_code='',
                commands=DEFAULT_COMMANDS
            ))
            logger.info(f"已成功设置Bot命令列表，共 {len(DEFAULT_COMMANDS)} 个命令")
            
        except Exception as e:
            logger.error(f"设置Bot命令列表时出错: {e}")
            # 不抛出异常，因为这不是关键功能，不应阻止Bot启动
    
    async def run(self) -> None:
        """
        启动 Search Bot
        
        注册事件处理器，使用 Bot Token 认证启动客户端，
        并保持运行直到断开连接。
        """
        try:
            # 注册事件处理器
            self.register_event_handlers()
            
            # 使用 Bot Token 启动客户端
            logger.info("正在启动 Search Bot...")
            await self.client.start(bot_token=self.bot_token)
            
            # 获取 Bot 信息并打印启动成功消息
            me = await self.client.get_me()
            logger.info(f"Search Bot 启动成功! Bot: @{me.username}")
            print(f"Search Bot (@{me.username}) 已成功启动并正在运行...")
            
            # 设置Bot命令列表
            await self.set_bot_commands()
            
            # 保持运行直到断开连接
            await self.client.run_until_disconnected()
            
        except ApiIdInvalidError:
            logger.error("API ID 或 API Hash 无效，请检查配置")
            raise
        except AuthKeyUnregisteredError:
            logger.error("Bot Token 无效或已过期，请检查配置")
            raise
        except Exception as e:
            logger.exception(f"Search Bot 运行时出错: {e}")
            raise
        finally:
            # 确保客户端断开连接
            await self.disconnect()
    
    async def disconnect(self) -> None:
        """
        断开与 Telegram 服务器的连接
        
        在应用程序结束时调用，确保优雅地关闭连接
        """
        if self.client and self.client.is_connected():
            logger.info("断开 Search Bot 连接...")
            await self.client.disconnect()


# 主程序入口
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建并运行 Search Bot
    bot = SearchBot()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("检测到键盘中断，正在关闭 Search Bot...")
    except Exception as e:
        logger.exception(f"运行 Search Bot 时发生错误: {e}")
    finally:
        logger.info("Search Bot 已关闭")