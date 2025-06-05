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
import base64
from typing import Optional, List
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

        # 初始化缓存
        self._dialogs_cache = []  # 缓存所有会话的基本信息
        self._avatars_cache = {}  # 缓存头像 {dialog_id: base64_string}
        self._cache_timestamp = None  # 缓存时间戳
        self._cache_ttl = 300  # 缓存5分钟（可配置）

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
        3. 初始化会话缓存

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
            
            # 初始化会话缓存
            logger.info("开始初始化会话缓存...")
            await self._init_dialogs_cache()
            logger.info(f"会话缓存初始化完成，缓存了 {len(self._dialogs_cache)} 个会话")
            
            # 预下载所有头像
            logger.info("开始预下载所有会话头像...")
            await self._preload_all_avatars()
            logger.info(f"头像预下载完成，成功缓存了 {len([v for v in self._avatars_cache.values() if v is not None])} 个头像")
            
            # 初始化会话索引
            logger.info("开始初始化会话索引...")
            await self._index_sessions_to_meilisearch()
            logger.info("会话索引初始化完成")
            
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

    async def _init_dialogs_cache(self) -> None:
        """
        初始化会话缓存
        获取所有会话的基本信息并缓存到内存中
        """
        try:
            all_dialogs = await self._client.get_dialogs()
            self._dialogs_cache = []
            
            for dialog in all_dialogs:
                dialog_name = dialog.name or "未知对话"
                dialog_id = dialog.id
                dialog_type_str = "unknown"

                if dialog.is_user:
                    dialog_type_str = "user"
                elif dialog.is_group:
                    dialog_type_str = "group"
                elif dialog.is_channel:
                    if hasattr(dialog.entity, 'megagroup') and dialog.entity.megagroup:
                         dialog_type_str = "group"
                    else:
                         dialog_type_str = "channel"
                
                dialog_info = {
                    "id": dialog_id,
                    "name": dialog_name,
                    "type": dialog_type_str,
                    "unread_count": dialog.unread_count if hasattr(dialog, 'unread_count') else 0,
                    "date": dialog.date.timestamp() if dialog.date else None,
                    "entity": dialog.entity,  # 保留entity用于后续头像下载
                }
                
                self._dialogs_cache.append(dialog_info)
            
            self._cache_timestamp = asyncio.get_event_loop().time()
            logger.debug(f"缓存了 {len(self._dialogs_cache)} 个会话的基本信息")
            
        except Exception as e:
            logger.error(f"初始化会话缓存失败: {e}")
            self._dialogs_cache = []

    def _is_cache_valid(self) -> bool:
        """
        检查缓存是否有效
        
        Returns:
            bool: 缓存是否在有效期内
        """
        if not self._dialogs_cache or self._cache_timestamp is None:
            return False
        
        current_time = asyncio.get_event_loop().time()
        return (current_time - self._cache_timestamp) < self._cache_ttl

    async def refresh_dialogs_cache(self) -> None:
        """
        手动刷新会话缓存
        """
        logger.info("手动刷新会话缓存...")
        await self._init_dialogs_cache()
        logger.info(f"会话缓存已刷新，当前缓存 {len(self._dialogs_cache)} 个会话")

    async def _download_and_cache_avatar(self, dialog_info: dict) -> str:
        """
        下载并缓存单个头像
        
        Args:
            dialog_info: 会话信息字典
            
        Returns:
            str: Base64编码的头像数据或None
        """
        dialog_id = dialog_info["id"]
        dialog_name = dialog_info.get("name", "Unknown")
        
        # 检查缓存中是否已有头像
        if dialog_id in self._avatars_cache:
            logger.debug(f"从缓存返回对话 {dialog_id} ({dialog_name}) 的头像")
            return self._avatars_cache[dialog_id]
        
        try:
            entity = dialog_info.get("entity")
            if not entity:
                logger.warning(f"对话 {dialog_id} ({dialog_name}) 没有entity信息，无法下载头像")
                self._avatars_cache[dialog_id] = None
                return None
            
            logger.debug(f"开始下载对话 {dialog_id} ({dialog_name}) 的头像...")
            
            # 设置超时时间为5秒
            photo_bytes = await asyncio.wait_for(
                self._client.download_profile_photo(entity, file=bytes),
                timeout=5.0
            )
            
            if photo_bytes:
                base64_string = base64.b64encode(photo_bytes).decode('utf-8')
                avatar_data = f"data:image/jpeg;base64,{base64_string}"
                
                # 缓存头像
                self._avatars_cache[dialog_id] = avatar_data
                logger.info(f"成功下载并缓存对话 {dialog_id} ({dialog_name}) 的头像，大小: {len(photo_bytes)} 字节")
                return avatar_data
            else:
                logger.warning(f"对话 {dialog_id} ({dialog_name}) 没有头像或下载为空")
                self._avatars_cache[dialog_id] = None
                return None
                
        except asyncio.TimeoutError:
            logger.warning(f"下载对话 {dialog_id} ({dialog_name}) 头像超时 (5秒)")
            self._avatars_cache[dialog_id] = None
            return None
        except Exception as e:
            logger.warning(f"下载对话 {dialog_id} ({dialog_name}) 头像失败: {e}")
            self._avatars_cache[dialog_id] = None
            return None

    def get_cached_dialogs_count(self) -> int:
        """
        获取缓存的会话总数
        
        Returns:
            int: 缓存的会话数量
        """
        return len(self._dialogs_cache)

    def clear_avatars_cache(self) -> None:
        """
        清除头像缓存
        """
        self._avatars_cache.clear()
        logger.info("头像缓存已清除")

    async def _preload_all_avatars(self) -> None:
        """
        预下载所有会话的头像
        
        在应用启动时并发下载所有会话的头像，提升用户体验。
        使用信号量控制并发数量，避免过多的并发请求。
        """
        if not self._dialogs_cache:
            logger.warning("会话缓存为空，无法预下载头像")
            return
        
        # 限制并发下载数量，避免过多请求
        max_concurrent = 10
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def download_with_semaphore(dialog_info):
            """带信号量控制的下载函数"""
            async with semaphore:
                return await self._download_and_cache_avatar(dialog_info)
        
        # 创建所有下载任务
        download_tasks = [
            download_with_semaphore(dialog_info) 
            for dialog_info in self._dialogs_cache
        ]
        
        logger.info(f"开始并发下载 {len(download_tasks)} 个会话的头像（最大并发数: {max_concurrent}）")
        
        # 并发执行所有下载任务
        try:
            results = await asyncio.gather(*download_tasks, return_exceptions=True)
            
            # 统计下载结果
            success_count = 0
            error_count = 0
            no_avatar_count = 0
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    error_count += 1
                    dialog_info = self._dialogs_cache[i]
                    logger.warning(f"下载对话 {dialog_info['id']} ({dialog_info['name']}) 头像时发生异常: {result}")
                elif result is None:
                    no_avatar_count += 1
                else:
                    success_count += 1
            
            logger.info(f"头像预下载完成 - 成功: {success_count}, 无头像: {no_avatar_count}, 失败: {error_count}")
            
        except Exception as e:
            logger.error(f"预下载头像时发生错误: {e}")

    async def _index_sessions_to_meilisearch(self) -> None:
        """
        将会话数据索引到MeiliSearch中，用于搜索功能
        """
        if not self._dialogs_cache:
            logger.warning("会话缓存为空，无法索引到MeiliSearch")
            return
        
        try:
            # 准备索引数据
            session_docs = []
            for dialog_info in self._dialogs_cache:
                # 为会话创建搜索文档
                session_doc = {
                    "id": str(dialog_info["id"]),  # 确保ID是字符串类型
                    "name": dialog_info["name"] or "未知对话",
                    "type": dialog_info["type"],
                    "unread_count": dialog_info.get("unread_count", 0),
                    "date": dialog_info.get("date"),
                    "avatar_key": str(dialog_info["id"])  # 使用dialog_id作为头像缓存key
                }
                session_docs.append(session_doc)
            
            # 批量索引到MeiliSearch
            result = self.meilisearch_service.index_sessions_bulk(session_docs)
            logger.info(f"已将 {len(session_docs)} 个会话索引到MeiliSearch")
            
        except Exception as e:
            logger.error(f"索引会话到MeiliSearch失败: {e}")
            # 不抛出异常，因为搜索功能失败不应该影响应用启动

    async def refresh_sessions_index(self) -> None:
        """
        刷新会话索引：清空现有索引并重新索引所有会话
        """
        try:
            logger.info("开始刷新会话索引...")
            
            # 清空现有索引
            self.meilisearch_service.clear_sessions_index()
            
            # 重新获取会话数据
            await self._init_dialogs_cache()
            
            # 重新索引会话
            await self._index_sessions_to_meilisearch()
            
            logger.info("会话索引刷新完成")
            
        except Exception as e:
            logger.error(f"刷新会话索引失败: {e}")
            raise

    def search_sessions(self, query: str, session_types: Optional[List[str]] = None, 
                       page: int = 1, hits_per_page: int = 20) -> dict:
        """
        搜索会话
        
        Args:
            query: 搜索关键词
            session_types: 会话类型过滤
            page: 页码
            hits_per_page: 每页结果数
            
        Returns:
            搜索结果字典
        """
        try:
            # 使用MeiliSearch搜索会话
            search_results = self.meilisearch_service.search_sessions(
                query=query,
                session_types=session_types,
                page=page,
                hits_per_page=hits_per_page,
                sort=["date:desc"]
            )
            
            # 增强搜索结果，添加头像信息
            enhanced_hits = []
            for hit in search_results.get('hits', []):
                session_id = int(hit['id'])
                
                # 从缓存获取头像
                avatar_base64 = self._avatars_cache.get(session_id)
                
                # 构建增强的会话信息
                enhanced_session = {
                    "id": session_id,
                    "name": hit['name'],
                    "type": hit['type'],
                    "unread_count": hit.get('unread_count', 0),
                    "date": hit.get('date'),
                    "avatar_base64": avatar_base64
                }
                enhanced_hits.append(enhanced_session)
            
            # 返回增强的搜索结果
            return {
                "items": enhanced_hits,
                "total": search_results.get('estimatedTotalHits', 0),
                "page": page,
                "limit": hits_per_page,
                "total_pages": (search_results.get('estimatedTotalHits', 0) + hits_per_page - 1) // hits_per_page,
                "has_avatars": True,
                "from_search": True,
                "processing_time_ms": search_results.get('processingTimeMs', 0)
            }
            
        except Exception as e:
            logger.error(f"搜索会话失败: {e}")
            # 返回空结果而不是抛出异常
            return {
                "items": [],
                "total": 0,
                "page": page,
                "limit": hits_per_page,
                "total_pages": 0,
                "has_avatars": True,
                "from_search": True,
                "error": str(e)
            }

    async def get_dialogs_info(self, page: int = 1, limit: int = 20, include_avatars: bool = True) -> dict:
        """
        获取用户账户下的所有对话信息，支持分页。
        
        优先使用缓存数据，大幅提升加载速度。缓存包括：
        1. 会话基本信息缓存（5分钟有效期）
        2. 头像缓存（永久有效，直到手动清除）
        
        Args:
            page (int): 页码，从1开始。
            limit (int): 每页显示的对话数量。
            include_avatars (bool): 是否包含头像，默认为True。设置为False可大幅提升加载速度。
            
        Returns:
            dict: 包含对话信息和分页信息的字典:
                - items (list[dict]): 对话信息列表，每个字典包含:
                    - id (int): 对话ID
                    - name (str): 对话名称/标题
                    - type (str): 对话类型 ('user', 'group', 'channel')
                    - unread_count (int): 未读消息数
                    - date (float, optional): 最后一条消息的Unix时间戳
                    - avatar_base64 (str, optional): 头像的Base64编码字符串 (data URI)，仅当include_avatars=True时存在
                - total (int): 总对话数
                - page (int): 当前页码
                - limit (int): 每页数量
                - total_pages (int): 总页数
                - has_avatars (bool): 是否包含头像数据
                - from_cache (bool): 数据是否来自缓存
            
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
            logger.info(f"获取对话列表 (分页: page={page}, limit={limit}, 包含头像: {include_avatars})")
            
            # 检查缓存是否有效
            if not self._is_cache_valid():
                logger.info("缓存已过期或不存在，重新获取会话数据...")
                await self._init_dialogs_cache()
            
            # 从缓存获取数据
            all_dialogs = self._dialogs_cache.copy()
            
            if not all_dialogs:
                logger.warning("缓存为空，可能是获取会话数据失败")
                return {
                    "items": [],
                    "total": 0,
                    "page": page,
                    "limit": limit,
                    "total_pages": 0,
                    "has_avatars": include_avatars,
                    "from_cache": False
                }
            
            # 计算分页
            total_dialogs = len(all_dialogs)
            total_pages = (total_dialogs + limit - 1) // limit
            start_index = (page - 1) * limit
            end_index = start_index + limit
            
            # 获取当前页的对话
            paginated_dialogs = all_dialogs[start_index:end_index]
            
            # 准备返回数据
            dialogs_info = []
            for dialog_info in paginated_dialogs:
                # 复制基本信息（移除entity字段）
                result_dialog = {
                    "id": dialog_info["id"],
                    "name": dialog_info["name"],
                    "type": dialog_info["type"],
                    "unread_count": dialog_info["unread_count"],
                    "date": dialog_info["date"],
                }
                
                # 处理头像
                if include_avatars:
                    # 直接从缓存获取头像，不再进行下载
                    dialog_id = dialog_info["id"]
                    avatar = self._avatars_cache.get(dialog_id, None)
                    result_dialog["avatar_base64"] = avatar
                else:
                    result_dialog["avatar_base64"] = None
                
                dialogs_info.append(result_dialog)
            
            # 如果需要头像且有头像需要下载，记录下载情况
            if include_avatars:
                cached_count = sum(1 for d in paginated_dialogs if d["id"] in self._avatars_cache and self._avatars_cache[d["id"]])
                total_count = len(paginated_dialogs)
                logger.info(f"页面头像状态: {cached_count}/{total_count} 来自缓存")
            
            logger.info(f"成功获取 {len(dialogs_info)} 个对话信息 (第 {page} 页, 每页 {limit} 条，总对话数 {total_dialogs}) - 来自缓存")
            
            return {
                "items": dialogs_info,
                "total": total_dialogs,
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
                "has_avatars": include_avatars,
                "from_cache": True
            }
            
        except ValueError as ve:
            logger.error(f"分页参数错误: {str(ve)}")
            raise
        except Exception as e:
            logger.error(f"获取对话信息时发生错误: {str(e)}")
            raise Exception(f"获取对话信息失败: {str(e)}")

    async def disconnect(self) -> None:
        """
        断开与Telegram服务器的连接

        在应用程序结束时调用，确保优雅地关闭连接
        """
        if self._client and self._client.is_connected():
            logger.info("断开TelegramClient连接...")
            try:
                # 给客户端时间来完成正在进行的操作
                await asyncio.sleep(0.1)
                # 使用优雅关闭，等待所有任务完成
                await self._client.disconnect()
                logger.info("TelegramClient连接已关闭")
            except Exception as e:
                logger.error(f"断开TelegramClient连接时出错: {str(e)}")
                # 如果优雅关闭失败，强制关闭
                try:
                    if hasattr(self._client, '_disconnect'):
                        await self._client._disconnect()
                except Exception as force_e:
                    logger.error(f"强制断开连接也失败: {str(force_e)}")
        elif self._client:
            logger.info("TelegramClient 已经断开连接")
            
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
            # 确保客户端断开连接
            if self._client and self._client.is_connected():
                try:
                    await self._client.disconnect()
                except Exception as e:
                    logger.error(f"在任务取消时断开客户端连接失败: {str(e)}")
            # 不重新抛出异常，让任务安静地结束
        except Exception as e:
            logger.error(f"UserBotClient 运行时出错: {str(e)}")
            # 确保客户端断开连接
            if self._client and self._client.is_connected():
                try:
                    await self._client.disconnect()
                except Exception as disconnect_e:
                    logger.error(f"在异常处理时断开客户端连接失败: {str(disconnect_e)}")
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