"""
Userbot客户端模块

此模块提供了与Telegram API交互的客户端功能，包括：
1. 初始化和管理Telethon客户端
2. 处理登录和会话管理
3. 提供获取客户端实例的方法
"""

import os
import logging
import functools
import asyncio
from typing import Optional
from pathlib import Path
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError

from core.config_manager import ConfigManager
from core.meilisearch_service import MeiliSearchService
from user_bot.event_handlers import handle_new_message, handle_message_edited
from user_bot.history_syncer import initial_sync_all_whitelisted_chats

# 配置日志记录器
logger = logging.getLogger(__name__)

# 会话文件目录
SESSIONS_DIR = ".sessions"


class UserBotClient:
    """
    UserBot客户端类

    提供Telethon客户端的创建、初始化和管理功能，使用单例模式确保全局只有一个实例。
    负责处理Telegram API的身份验证和会话管理。
    """

    _instance: Optional["UserBotClient"] = None
    _client: Optional[TelegramClient] = None

    def __new__(cls, *args, **kwargs):
        """
        实现单例模式，确保只创建一个实例

        Returns:
            UserBotClient: 单例实例
        """
        if cls._instance is None:
            cls._instance = super(UserBotClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_manager: Optional[ConfigManager] = None, session_name: str = "user_bot_session"):
        """
        初始化UserBotClient

        Args:
            config_manager: 配置管理器实例，如果未提供则创建新实例
            session_name: 会话文件名，默认为"user_bot_session"
        """
        # 如果已经初始化过，则跳过
        if getattr(self, "_initialized", False):
            return

        # 确保会话目录存在
        self._ensure_sessions_dir_exists()

        # 初始化配置管理器
        self.config_manager = config_manager or ConfigManager()
        self.session_name = session_name

        # 初始化MeiliSearchService
        # 从配置获取MeiliSearch配置
        host = self.config_manager.get_env("MEILISEARCH_HOST")
        api_key = self.config_manager.get_env("MEILISEARCH_API_KEY")
        
        # 如果环境变量中没有配置，从配置文件获取
        if not host:
            host = self.config_manager.get_config("MeiliSearch", "HOST", "http://localhost:7700")
        if not api_key:
            api_key = self.config_manager.get_config("MeiliSearch", "API_KEY")
            
        self.meilisearch_service = MeiliSearchService(host=host, api_key=api_key)
        logger.info("已初始化MeiliSearchService")

        # 从配置获取会话名称
        user_session_name = self.config_manager.get_userbot_env("USER_SESSION_NAME")
        if user_session_name:
            self.session_name = user_session_name
            logger.info(f"从User Bot配置加载会话名称: {self.session_name}")

        # 构建会话文件路径（存储在.sessions目录下）
        session_path = os.path.join(SESSIONS_DIR, self.session_name)

        # 从User Bot配置获取API凭据
        api_id = self.config_manager.get_userbot_env("USER_API_ID")
        api_hash = self.config_manager.get_userbot_env("USER_API_HASH")

        # 如果User Bot配置中没有，尝试从全局环境变量获取
        if not api_id:
            api_id = self.config_manager.get_env("TELEGRAM_API_ID")
        if not api_hash:
            api_hash = self.config_manager.get_env("TELEGRAM_API_HASH")

        # 如果环境变量中也没有，则从配置文件中获取
        if not api_id:
            api_id = self.config_manager.get_config("Telegram", "API_ID")
        if not api_hash:
            api_hash = self.config_manager.get_config("Telegram", "API_HASH")

        # 验证API凭据
        if not api_id or not api_hash:
            logger.error("未找到Telegram API凭据，请在环境变量或配置文件中设置TELEGRAM_API_ID和TELEGRAM_API_HASH")
            raise ValueError("未找到Telegram API凭据")

        # 转换api_id为整数（Telethon要求）
        try:
            api_id = int(api_id)
        except ValueError:
            logger.error(f"API_ID必须是整数，当前值: {api_id}")
            raise ValueError(f"API_ID必须是整数，当前值: {api_id}")

        # 初始化TelegramClient
        logger.info(f"初始化TelegramClient，会话文件: {session_path}")
        self._client = TelegramClient(session_path, api_id, api_hash)
        self._initialized = True

    def _ensure_sessions_dir_exists(self) -> None:
        """
        确保会话文件目录存在

        创建.sessions目录（如果不存在）
        """
        Path(SESSIONS_DIR).mkdir(exist_ok=True)
        logger.debug(f"确保会话目录存在: {SESSIONS_DIR}")

    async def start(self) -> TelegramClient:
        """
        启动客户端并处理登录流程

        如果是首次运行，用户需要通过控制台输入手机号和验证码进行交互式登录
        后续运行将使用保存的会话文件自动登录

        登录成功后会：
        1. 注册消息事件处理器（新消息和编辑消息）
        2. 执行初始的历史消息同步（所有白名单聊天）

        Returns:
            TelegramClient: 已启动的Telethon客户端实例
        """
        if not self._client:
            logger.error("客户端未初始化，请先初始化UserBotClient")
            raise RuntimeError("客户端未初始化")

        logger.info("启动TelegramClient...")
        
        # 打印首次登录指南
        if not os.path.exists(os.path.join(SESSIONS_DIR, f"{self.session_name}.session")):
            logger.info("首次登录指南:")
            logger.info("1. 您将需要输入您的Telegram账号手机号（包含国家/地区代码，如+86）")
            logger.info("2. Telegram将发送验证码到您的手机或其他登录设备")
            logger.info("3. 输入验证码以完成登录")
            logger.info("4. 如果您的账号启用了两步验证，还需要输入密码")
            logger.info("注意: 登录过程中输入的信息不会被存储或传输到其他地方，仅用于直接验证并创建本地会话文件")

        try:
            # 启动客户端（如果未登录，将进入交互式登录流程）
            await self._client.start()
            
            # 获取当前用户信息，验证登录成功
            me = await self._client.get_me()
            logger.info(f"登录成功! 用户: {me.first_name} (@{me.username})")
            
            # 注册事件处理器
            # 使用functools.partial为事件处理器绑定额外参数（ConfigManager和MeiliSearchService实例）
            new_message_handler = functools.partial(
                handle_new_message,
                config_manager=self.config_manager,
                meili_service=self.meilisearch_service
            )
            
            edited_message_handler = functools.partial(
                handle_message_edited,
                config_manager=self.config_manager,
                meili_service=self.meilisearch_service
            )
            
            # 注册事件处理器
            self._client.add_event_handler(
                new_message_handler,
                events.NewMessage()
            )
            logger.info("已注册新消息事件处理器")
            
            self._client.add_event_handler(
                edited_message_handler,
                events.MessageEdited()
            )
            logger.info("已注册消息编辑事件处理器")
            
            # 执行初始历史同步
            logger.info("开始执行初始历史消息同步...")
            sync_results = await initial_sync_all_whitelisted_chats(
                client=self._client,
                config_manager=self.config_manager,
                meilisearch_service=self.meilisearch_service
            )
            
            # 记录同步结果
            total_processed = sum(result[0] for result in sync_results.values())
            total_indexed = sum(result[1] for result in sync_results.values())
            logger.info(f"初始历史同步完成，共处理 {total_processed} 条消息，成功索引 {total_indexed} 条")
            
            return self._client
            
        except SessionPasswordNeededError:
            logger.info("检测到两步验证，需要输入密码")
            raise
        except Exception as e:
            logger.error(f"登录过程中发生错误: {str(e)}")
            raise

    def get_client(self) -> TelegramClient:
        """
        获取TelegramClient实例

        需要先调用start()方法启动客户端

        Returns:
            TelegramClient: Telethon客户端实例

        Raises:
            RuntimeError: 如果客户端未初始化
        """
        if not self._client:
            logger.error("客户端未初始化，请先初始化UserBotClient")
            raise RuntimeError("客户端未初始化")
            
        return self._client

    async def get_dialogs_info(self, page: int = 1, limit: int = 20) -> list[dict]:
        """
        获取用户账户下的所有对话信息，支持分页。
        
        使用Telethon客户端的get_dialogs()功能获取所有对话，
        然后根据分页参数提取指定范围的对话，并返回包含对话详细信息的字典列表。
        
        Args:
            page (int): 页码，从1开始。
            limit (int): 每页显示的对话数量。
            
        Returns:
            list[dict]: 包含对话信息的字典列表，每个字典包含:
                        - id (int): 对话ID
                        - name (str): 对话名称/标题
                        - type (str): 对话类型 ('user', 'group', 'channel')
                        - unread_count (int): 未读消息数
                        - date (float, optional): 最后一条消息的Unix时间戳
            
        Raises:
            RuntimeError: 如果客户端未初始化或未连接。
            ValueError: 如果page或limit参数无效。
            Exception: 如果获取对话信息时发生API错误。
        """
        if not self._client:
            logger.error("客户端未初始化，无法获取对话信息")
            raise RuntimeError("客户端未初始化")
            
        if not self._client.is_connected():
            logger.error("客户端未连接，无法获取对话信息")
            raise RuntimeError("客户端未连接，请先调用start()方法")

        if page < 1:
            raise ValueError("页码 (page) 必须大于等于 1")
        if limit < 1:
            raise ValueError("每页数量 (limit) 必须大于等于 1")
            
        try:
            logger.info(f"开始获取对话列表 (分页: page={page}, limit={limit})...")
            
            # Telethon 的 get_dialogs() 不直接支持 offset 来跳过一定数量的对话。
            # 它有一个 `offset_id` 和 `offset_date` 参数，但这些用于从特定点开始获取。
            # 为了实现简单的页码分页，我们可以获取所有对话，然后在Python中进行切片。
            # 注意：如果对话数量非常大 (例如几千个)，这可能不是最高效的方法，
            # 因为它会先加载所有对话到内存中。
            # 对于非常大的列表，更高级的分页可能需要使用 offset_id/offset_date，
            # 但这会使页码逻辑复杂化。目前采用内存分页。
            
            all_dialogs = await self._client.get_dialogs() # 获取所有对话
            
            # 计算分页的起始和结束索引
            start_index = (page - 1) * limit
            end_index = start_index + limit
            
            # 获取当前页的对话
            paginated_dialogs = all_dialogs[start_index:end_index]
            
            dialogs_info = []
            for dialog in paginated_dialogs:
                dialog_name = dialog.name or "未知对话"
                dialog_id = dialog.id
                dialog_type_str = "unknown"

                if dialog.is_user:
                    dialog_type_str = "user"
                elif dialog.is_group: # 包括普通群组和超级群组
                    dialog_type_str = "group"
                elif dialog.is_channel:
                    # Telethon 的 is_group 已经能区分普通群组和超级群组（都算group）
                    # is_channel 通常指广播频道
                    # 进一步确认，如果 entity 是 Channel 且 megagroup 为 True，它实际上是超级群组
                    if hasattr(dialog.entity, 'megagroup') and dialog.entity.megagroup:
                         dialog_type_str = "group" # 超级群组也视为 group
                    else:
                         dialog_type_str = "channel" # 广播频道
                
                dialogs_info.append({
                    "id": dialog_id,
                    "name": dialog_name,
                    "type": dialog_type_str,
                    "unread_count": dialog.unread_count if hasattr(dialog, 'unread_count') else 0,
                    "date": dialog.date.timestamp() if dialog.date else None,
                })
                
            logger.info(f"成功获取 {len(dialogs_info)} 个对话信息 (第 {page} 页, 每页 {limit} 条，总对话数 {len(all_dialogs)})")
            # logger.debug(f"当前页对话列表: {dialogs_info}") # 避免日志过长
            
            return dialogs_info
            
        except ValueError as ve:
            logger.error(f"分页参数错误: {str(ve)}")
            raise
        except Exception as e:
            logger.error(f"获取对话信息时发生错误: {str(e)}")
            # 可以在这里添加更具体的错误处理，例如网络错误、API限制等
            raise Exception(f"获取对话信息失败: {str(e)}")

    async def disconnect(self) -> None:
        """
        断开与Telegram服务器的连接

        在应用程序结束时调用，确保优雅地关闭连接
        """
        if self._client:
            logger.info("断开TelegramClient连接...")
            await self._client.disconnect()
            
    async def run(self) -> None:
        """
        运行客户端直到断开连接
        
        此方法在客户端启动后调用，会保持客户端运行直到断开连接
        常用于确保事件处理器能够持续监听消息
        """
        if not self._client:
            logger.error("客户端未初始化，请先初始化UserBotClient")
            raise RuntimeError("客户端未初始化")
            
        # 如果客户端未启动，则先启动
        if not self._client.is_connected():
            await self.start()
            
        logger.info("UserBotClient 正在运行，等待事件...")
        
        try:
            # 运行直到断开连接
            await self._client.run_until_disconnected()
        except asyncio.CancelledError:
            # 优雅地处理任务取消
            logger.info("UserBotClient 任务被取消，正在关闭...")
            # 不重新抛出异常，让任务安静地结束
        except Exception as e:
            logger.error(f"UserBotClient 运行时出错: {str(e)}")
            raise
        
    def reload_config(self) -> None:
        """
        重新加载配置
        
        在配置更改后调用，重新加载User Bot的配置和所有相关配置文件
        注意：此方法不会重新创建客户端实例，需要先断开连接再重新启动
        """
        logger.info("正在重新加载User Bot配置和所有相关配置文件...")
        
        # 重新加载所有配置文件
        self.config_manager.load_env()  # 重新加载主环境变量
        self.config_manager.load_userbot_env()  # 重新加载User Bot环境变量
        self.config_manager.load_config()  # 重新加载config.ini
        self.config_manager.load_whitelist()  # 重新加载whitelist.json和同步设置
        self.config_manager._load_search_bot_config()  # 重新加载SearchBot特定配置
        
        # 更新会话名称（如果已更改）
        user_session_name = self.config_manager.get_userbot_env("USER_SESSION_NAME")
        if user_session_name and user_session_name != self.session_name:
            logger.info(f"会话名称已更改: {self.session_name} -> {user_session_name}")
            self.session_name = user_session_name
            
        logger.info("User Bot配置和所有相关配置文件已重新加载")