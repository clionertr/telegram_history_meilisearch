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
import time # Added for cache timestamping
from typing import List, Optional, Union, Dict, Any, Tuple
from datetime import datetime

from telethon import events, Button
from telethon.tl.types import User

from core.meilisearch_service import MeiliSearchService
from core.config_manager import ConfigManager
from .cache_service import SearchCacheService # Added
from .dialogs_cache_service import DialogsCacheService # Added for dialogs caching
from search_bot.message_formatters import format_search_results, format_error_message, format_help_message, format_dialogs_list
from user_bot.client import UserBotClient

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
        self.cache_service = SearchCacheService(config_manager)
        self.dialogs_cache_service = DialogsCacheService(config_manager) # Added for dialogs caching
        self.active_full_fetches: Dict[str, asyncio.Task] = {} # For managing async full-fetch tasks
        
        # 注册命令处理函数
        self.register_handlers()
        
        logger.info("命令处理器已初始化，搜索缓存和对话缓存服务已配置")
    
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
        
        # 对话列表命令
        self.client.add_event_handler(
            self.get_dialogs_command,
            events.NewMessage(pattern=r"^/get_dialogs$")
        )

        # 新增：处理普通文本消息作为搜索（应在所有特定命令之后注册）
        self.client.add_event_handler(
            self.handle_plain_text_message,
            events.NewMessage(func=self._is_plain_text_and_not_command)
        )

        # Search Cache Admin Commands
        self.client.add_event_handler(
            self.view_search_config_command,
            events.NewMessage(pattern=r"^/view_search_config$")
        )
        self.client.add_event_handler(
            self.set_search_config_command,
            events.NewMessage(pattern=r"^/set_search_config(?:\s+(\S+))?(?:\s+(.+))?$")
        )
        self.client.add_event_handler(
            self.clear_search_cache_command,
            events.NewMessage(pattern=r"^/clear_search_cache$")
        )
        
        # Dialogs Cache Admin Commands
        self.client.add_event_handler(
            self.view_dialogs_cache_command,
            events.NewMessage(pattern=r"^/view_dialogs_cache$")
        )
        self.client.add_event_handler(
            self.clear_dialogs_cache_command,
            events.NewMessage(pattern=r"^/clear_dialogs_cache$")
        )
        
        # 最旧同步时间设置命令
        self.client.add_event_handler(
            self.set_oldest_sync_time_command,
            events.NewMessage(pattern=r"^/set_oldest_sync_time(?:\s+(-?\d+))?(?:\s+(.+))?$")
        )
        self.client.add_event_handler(
            self.view_oldest_sync_time_command,
            events.NewMessage(pattern=r"^/view_oldest_sync_time(?:\s+(-?\d+))?$")
        )
        
        logger.info("已注册所有命令处理函数，包括普通文本搜索处理器、搜索缓存和对话缓存管理命令")
    
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
            r"^/restart_userbot$",
            r"^/get_dialogs$",
            # Add new search config commands to prevent them being treated as plain text
            r"^/view_search_config$",
            r"^/set_search_config(?:\s+(\S+))?(?:\s+(.+))?$",
            r"^/clear_search_cache$",
            r"^/view_dialogs_cache$",
            r"^/clear_dialogs_cache$"
        ]
        
        for pattern in known_commands_patterns:
            if re.match(pattern, text):
                return False # 匹配已知命令格式

        # 进一步排除任何以 / 开头的消息，以防有未明确列出的命令
        if text.startswith('/'):
            return False
            
        # 新增命令
        r"^/set_oldest_sync_time(?:\s+(-?\d+))?(?:\s+(.+))?$",
        r"^/view_oldest_sync_time(?:\s+(-?\d+))?$",
            
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

    async def _get_results_from_meili(self,
                                      parsed_query: str,
                                      filters: Optional[str],
                                      sort: List[str],
                                      page: int,
                                      hits_per_page: int,
                                      start_timestamp: Optional[int] = None,
                                      end_timestamp: Optional[int] = None,
                                      chat_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Helper function to call MeiliSearch and return results.
        
        Args:
            parsed_query: 解析后的查询字符串
            filters: Meilisearch 过滤条件字符串
            sort: 排序规则列表
            page: 页码
            hits_per_page: 每页结果数
            start_timestamp: 开始时间戳（可选）
            end_timestamp: 结束时间戳（可选）
            chat_types: 聊天类型列表（可选）
            
        Returns:
            Dict[str, Any]: Meilisearch 搜索结果
        """
        return self.meilisearch_service.search(
            query=parsed_query,
            filters=filters,
            sort=sort,
            page=page,
            hits_per_page=hits_per_page,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            chat_types=chat_types
        )

    async def _fetch_all_results_async(self, cache_key: str, parsed_query: str, filters_dict: Optional[Dict[str, Any]], meili_filters: Optional[str], sort_options: List[str], total_hits_estimate: int):
        """
        异步获取所有搜索结果并更新缓存。
        """
        try:
            logger.info(f"后台任务开始: 为 key='{cache_key}' 获取全部 {total_hits_estimate} 条结果。")
            # Fetch all results. MeiliSearch's limit parameter can be high.
            # We assume meilisearch_service.search handles pagination if we ask for all hits.
            # Let's fetch all in one go if total_hits_estimate is manageable, e.g., < 1000.
            # Otherwise, we might need a loop here, but for now, try to get all.
            # The MeiliSearch Python SDK's `search` method with `hits_per_page` set to total_hits
            # should ideally return all results if the server limit allows.
            # If total_hits_estimate is very large, this might be slow or hit server limits.
            # For now, we'll request all items.
            
            # A more robust approach for very large result sets would be to fetch in chunks
            # and append, but that complicates cache updates significantly.
            # Let's assume total_hits_estimate is within a reasonable limit for a single fetch.
            # The default limit for MeiliSearch is 1000 per query if not specified otherwise by `hitsPerPage`.
            
            all_results_data = []
            # If total_hits_estimate is 0, no need to fetch
            if total_hits_estimate == 0:
                logger.info(f"后台任务: key='{cache_key}', 总命中数为0，无需获取。")
                self.cache_service.update_cache_to_complete(parsed_query, filters_dict, [], 0)
                return

            # Fetch all results. The MeiliSearch client handles pagination internally if we set a high limit.
            # We'll fetch all results in one go.
            # The `search` method in MeiliSearchService already handles `page` and `hits_per_page`.
            # To get all, we can set hits_per_page to total_hits and page to 1.
            # However, MeiliSearch has a default limit (often 1000).
            # For simplicity, we'll fetch up to a practical limit (e.g. 1000) for the "full" cache.
            # If total_hits > 1000, the "full" cache will contain the first 1000.
            # This is a pragmatic choice to avoid excessive memory/network for huge result sets.
            # The user can still paginate through MeiliSearch directly via callbacks if needed beyond this.
            
            fetch_limit = min(total_hits_estimate, 1000) # Cap full fetch at 1000 for now

            if fetch_limit > 0:
                # 准备筛选参数
                start_timestamp = None
                end_timestamp = None
                chat_types = None
                
                if filters_dict:
                    # 提取日期范围
                    if 'date_range' in filters_dict:
                        date_range = filters_dict['date_range']
                        start_timestamp = date_range.get('start')
                        end_timestamp = date_range.get('end')
                    
                    # 提取聊天类型
                    if 'chat_type' in filters_dict:
                        chat_types = filters_dict['chat_type']
                
                # 获取所有结果
                full_search_results_obj = await self._get_results_from_meili(
                    parsed_query=parsed_query,
                    filters=meili_filters,
                    sort=sort_options,
                    page=1, # Get all from the first page
                    hits_per_page=fetch_limit, # Request all (up to the cap)
                    start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp,
                    chat_types=chat_types
                )
                all_results_data = full_search_results_obj.get('hits', [])
            
            self.cache_service.update_cache_to_complete(parsed_query, filters_dict, all_results_data, total_hits_estimate)
            logger.info(f"后台任务完成: key='{cache_key}' 的缓存已更新为 {len(all_results_data)} 条完整结果 (总预估 {total_hits_estimate})。")

        except Exception as e:
            logger.error(f"后台任务失败: key='{cache_key}' 获取全部结果时出错: {e}", exc_info=True)
            # Optionally, remove the partial cache entry or mark it as failed?
            # For now, the partial entry will remain until TTL.
        finally:
            if cache_key in self.active_full_fetches:
                del self.active_full_fetches[cache_key]

    async def _perform_search(self, event, query: str, page: int = 1, is_direct_search: bool = False) -> None:
        """
        执行搜索操作并回复结果。集成了缓存逻辑。
        
        Args:
            event: Telethon 事件对象。
            query: 搜索关键词。
            page: 请求的页码 (用于分页)。
            is_direct_search: 是否为直接无命令搜索。
        """
        try:
            sender_id = (await event.get_sender()).id
            logger.info(f"用户 {sender_id} 搜索: '{query}', 页码: {page}")

            parsed_query, filters_dict = self._parse_advanced_syntax(query)
            meili_filters = self._build_meilisearch_filters(filters_dict) if filters_dict else None
            
            hits_per_page = 5  # Standard items per page for display
            sort_options = ["date:desc"] # Default sort

            cached_data_entry = None
            if self.cache_service.is_cache_enabled():
                cached_data_entry = self.cache_service.get_from_cache(parsed_query, filters_dict)

            if cached_data_entry:
                cached_results, is_partial, total_hits_from_cache, fetch_ts = cached_data_entry
                logger.info(f"缓存命中 for query '{parsed_query}'. Partial: {is_partial}, Total Hits: {total_hits_from_cache}")

                if not is_partial: # Full data in cache
                    results_to_format = {
                        'hits': cached_results[ (page - 1) * hits_per_page : page * hits_per_page ],
                        'query': parsed_query,
                        'processingTimeMs': 0, # From cache
                        'estimatedTotalHits': total_hits_from_cache
                    }
                    total_pages = (total_hits_from_cache + hits_per_page - 1) // hits_per_page if total_hits_from_cache > 0 else 0
                    formatted_message, buttons = format_search_results(results_to_format, page, total_pages, query_original=query)
                    await event.respond(formatted_message, buttons=buttons, parse_mode='md')
                    logger.info(f"已从完整缓存向用户 {sender_id} 发送第 {page} 页结果")
                    return

                # Partial data in cache
                if total_hits_from_cache is not None:
                    # Check if requested page is within the initial fetch
                    if page * hits_per_page <= len(cached_results):
                        results_to_format = {
                            'hits': cached_results[ (page - 1) * hits_per_page : page * hits_per_page ],
                            'query': parsed_query,
                            'processingTimeMs': 0, # From cache
                            'estimatedTotalHits': total_hits_from_cache
                        }
                        total_pages = (total_hits_from_cache + hits_per_page - 1) // hits_per_page if total_hits_from_cache > 0 else 0
                        formatted_message, buttons = format_search_results(results_to_format, page, total_pages, query_original=query)
                        await event.respond(formatted_message, buttons=buttons, parse_mode='md')
                        logger.info(f"已从部分缓存 (初始获取部分) 向用户 {sender_id} 发送第 {page} 页结果")
                        return
                    else:
                        # Requested page is beyond initial fetch.
                        # Check if full fetch is ongoing or completed.
                        cache_key_for_async = self.cache_service._generate_cache_key(parsed_query, filters_dict) # pylint: disable=protected-access
                        if cache_key_for_async in self.active_full_fetches or (fetch_ts is not None and time.time() - fetch_ts < 60): # Task running or recently started (give it 60s)
                            # Chosen:方案A (提示用户等待) for pagination beyond initial while async fetch is running
                            await event.respond("⏳ 正在加载更多结果，请稍候片刻再尝试翻页...", parse_mode='md')
                            logger.info(f"用户 {sender_id} 请求的页面超出初始缓存，后台任务仍在进行中。")
                            # Record this choice in activeContext.md
                            # Decision: For pagination requests beyond the initial cached set, while a background
                            # full-fetch task is active (or was very recently initiated), we will inform the user
                            # that more results are loading and ask them to wait. This avoids hitting MeiliSearch
                            # again for a page that will soon be part of the complete cache entry, and provides
                            # a better UX than an immediate (potentially partial or inconsistent) result.
                            # The alternative of fetching this specific page directly from MeiliSearch might lead
                            # to this page not being part of the "all_results_data" when the background task completes,
                            # or requiring complex merging logic.
                            return
                        else:
                            # Full fetch might have completed and updated the cache, or failed/timed out.
                            # Re-check cache, it might be complete now.
                            fresh_cached_entry = self.cache_service.get_from_cache(parsed_query, filters_dict)
                            if fresh_cached_entry and not fresh_cached_entry[1]: # is_partial is False
                                cached_results_updated, _, total_hits_updated, _ = fresh_cached_entry
                                results_to_format = {
                                    'hits': cached_results_updated[ (page - 1) * hits_per_page : page * hits_per_page ],
                                    'query': parsed_query,
                                    'processingTimeMs': 0,
                                    'estimatedTotalHits': total_hits_updated
                                }
                                total_pages = (total_hits_updated + hits_per_page - 1) // hits_per_page if total_hits_updated > 0 else 0
                                formatted_message, buttons = format_search_results(results_to_format, page, total_pages, query_original=query)
                                await event.respond(formatted_message, buttons=buttons, parse_mode='md')
                                logger.info(f"已从更新后的完整缓存向用户 {sender_id} 发送第 {page} 页结果")
                                return
                            # If still partial or not found, proceed to fetch from Meili (should ideally not happen if logic is correct)
                            logger.warning(f"缓存状态异常 for {parsed_query} after async check, proceeding to MeiliSearch for page {page}")


            # Cache miss or only partial data that doesn't cover the page and async fetch not active/helpful
            # This part is primarily for the first time a search is made (page=1)
            if page == 1: # Only do initial + async fetch on the first page request
                status_message = await event.respond("🔍 正在搜索，请稍候...", parse_mode='md')
                
                initial_fetch_count = self.cache_service.get_initial_fetch_count()
                
                # 准备筛选参数
                start_timestamp = None
                end_timestamp = None
                chat_types = None
                
                if filters_dict:
                    # 提取日期范围
                    if 'date_range' in filters_dict:
                        date_range = filters_dict['date_range']
                        start_timestamp = date_range.get('start')
                        end_timestamp = date_range.get('end')
                    
                    # 提取聊天类型
                    if 'chat_type' in filters_dict:
                        chat_types = filters_dict['chat_type']
                
                # Stage 1: Initial Fetch
                initial_results_obj = await self._get_results_from_meili(
                    parsed_query, meili_filters, sort_options, 1, initial_fetch_count,
                    start_timestamp=start_timestamp, end_timestamp=end_timestamp, chat_types=chat_types
                )
                initial_hits_data = initial_results_obj.get('hits', [])
                estimated_total_hits = initial_results_obj.get('estimatedTotalHits', 0)

                # Store initial results in cache
                full_fetch_ts = None
                if self.cache_service.is_cache_enabled():
                    if estimated_total_hits > len(initial_hits_data):
                        full_fetch_ts = time.time() # Mark time if async fetch will be needed
                    self.cache_service.store_in_cache(
                        parsed_query, filters_dict, initial_hits_data, estimated_total_hits,
                        is_partial=(estimated_total_hits > len(initial_hits_data)),
                        full_fetch_initiated_timestamp=full_fetch_ts
                    )

                # Format and send initial results
                total_pages_for_initial = (estimated_total_hits + hits_per_page - 1) // hits_per_page if estimated_total_hits > 0 else 0
                formatted_message, buttons = format_search_results(initial_results_obj, 1, total_pages_for_initial, query_original=query)
                
                try:
                    await status_message.edit(formatted_message, buttons=buttons, parse_mode='md')
                except Exception: # If edit fails (e.g. message too old)
                    await event.respond(formatted_message, buttons=buttons, parse_mode='md')
                logger.info(f"已向用户 {sender_id} 发送初始 {len(initial_hits_data)} 条搜索结果 (总共 {estimated_total_hits} 条)")

                # Stage 2: Asynchronous Full Fetch (if needed)
                if self.cache_service.is_cache_enabled() and estimated_total_hits > len(initial_hits_data):
                    cache_key_for_async = self.cache_service._generate_cache_key(parsed_query, filters_dict) # pylint: disable=protected-access
                    if cache_key_for_async not in self.active_full_fetches:
                        logger.info(f"启动后台任务: 为 key='{cache_key_for_async}' 获取剩余结果。")
                        task = asyncio.create_task(
                            self._fetch_all_results_async(
                                cache_key_for_async, parsed_query, filters_dict, meili_filters, sort_options, estimated_total_hits
                            )
                        )
                        self.active_full_fetches[cache_key_for_async] = task
                    else:
                        logger.info(f"后台任务已在运行: key='{cache_key_for_async}'")
                return # Initial results sent, async fetch (if any) started.

            else: # page > 1 and data not sufficiently in cache
                # This case means user is asking for a subsequent page,
                # but the cache (even after checking for async completion) doesn't have it.
                # This might happen if TTL expired, or cache was cleared, or async failed silently.
                # For robustness, fetch this specific page directly from MeiliSearch.
                # This page won't be part of the "full_fetch" logic if it runs later for the same query.
                logger.warning(f"缓存未命中或数据不足 (页码 {page}) for '{parsed_query}'. 直接从 MeiliSearch 获取。")
                status_message = await event.respond(f"🔍 正在加载第 {page} 页，请稍候...", parse_mode='md')
                
                # 准备筛选参数
                start_timestamp = None
                end_timestamp = None
                chat_types = None
                
                if filters_dict:
                    # 提取日期范围
                    if 'date_range' in filters_dict:
                        date_range = filters_dict['date_range']
                        start_timestamp = date_range.get('start')
                        end_timestamp = date_range.get('end')
                    
                    # 提取聊天类型
                    if 'chat_type' in filters_dict:
                        chat_types = filters_dict['chat_type']
                
                # 获取特定页面的结果
                page_specific_results_obj = await self._get_results_from_meili(
                    parsed_query, meili_filters, sort_options, page, hits_per_page,
                    start_timestamp=start_timestamp, end_timestamp=end_timestamp, chat_types=chat_types
                )
                estimated_total_hits = page_specific_results_obj.get('estimatedTotalHits', 0) # Re-confirm total
                total_pages = (estimated_total_hits + hits_per_page - 1) // hits_per_page if estimated_total_hits > 0 else 0
                
                formatted_message, buttons = format_search_results(page_specific_results_obj, page, total_pages, query_original=query)
                try:
                    await status_message.edit(formatted_message, buttons=buttons, parse_mode='md')
                except Exception:
                    await event.respond(formatted_message, buttons=buttons, parse_mode='md')
                logger.info(f"已直接从 MeiliSearch 向用户 {sender_id} 发送第 {page} 页结果")
                return

        except Exception as e:
            logger.error(f"执行搜索时出错 (query: {query}, page: {page}): {e}", exc_info=True)
            error_message = format_error_message(str(e))
            # Try to edit if status_message exists, otherwise respond
            try:
                if 'status_message' in locals() and status_message:
                    await status_message.edit(error_message, parse_mode='md')
                else:
                    await event.respond(error_message, parse_mode='md')
            except Exception:
                 await event.respond(error_message, parse_mode='md')

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
        # For /search command, it's always the first page initially
        await self._perform_search(event, query, page=1)
    
    def _parse_advanced_syntax(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """
        解析高级搜索语法
        
        支持的语法:
        - 精确短语: "关键短语"
        - 类型筛选: type:类型 (user/group/channel)
          可以多次使用此语法来筛选多种类型，如: type:group type:channel
        - 时间筛选: date:起始_结束 (YYYY-MM-DD_YYYY-MM-DD)
        
        Args:
            query: 原始查询字符串
            
        Returns:
            Tuple[str, Dict[str, Any]]: 处理后的查询和过滤条件字典
        """
        # 初始化结果
        filters = {}
        
        # 处理类型筛选 (可能有多个)
        chat_types = []
        type_matches = re.finditer(r'type:(\w+)', query)
        valid_chat_types = ['user', 'group', 'channel']
        
        for match in type_matches:
            chat_type = match.group(1).lower()
            if chat_type in valid_chat_types and chat_type not in chat_types:
                chat_types.append(chat_type)
        
        if chat_types:
            filters['chat_type'] = chat_types
            # 从查询中移除所有 type: 部分
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
            chat_type_value = filters_dict['chat_type']
            
            # 如果是列表，构建 OR 条件
            if isinstance(chat_type_value, list) and chat_type_value:
                chat_type_conditions = [f"chat_type = '{chat_type}'" for chat_type in chat_type_value]
                filter_parts.append(f"({' OR '.join(chat_type_conditions)})")
            # 如果是单个值，直接添加条件
            elif isinstance(chat_type_value, str):
                filter_parts.append(f"chat_type = '{chat_type_value}'")
        
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

    async def get_dialogs_command(self, event) -> None:
        """
        处理 /get_dialogs 命令
        
        获取用户账户下的所有对话列表，包括对话名称和ID
        支持30分钟缓存以提高响应速度
        
        Args:
            event: Telethon 事件对象
        """
        try:
            sender = await event.get_sender()
            sender_id = sender.id
            logger.info(f"用户 {sender_id} 请求获取对话列表")
            
            # 首先检查缓存
            cached_dialogs = None
            if self.dialogs_cache_service.is_cache_enabled():
                cached_dialogs = self.dialogs_cache_service.get_from_cache(sender_id)
            
            if cached_dialogs:
                # 缓存命中，直接使用缓存数据
                logger.info(f"用户 {sender_id} 的对话列表缓存命中，共 {len(cached_dialogs)} 个对话")
                all_dialogs_info = cached_dialogs
                
                # 发送缓存提示消息（可选）
                status_message = await event.respond("📋 正在加载对话列表（来自缓存）...")
            else:
                # 缓存未命中，需要从API获取
                logger.info(f"用户 {sender_id} 的对话列表缓存未命中，从API获取")
                
                # 发送处理中的消息
                status_message = await event.respond("🔍 正在获取对话列表，请稍候...")
                
                # 获取 UserBotClient 实例
                try:
                    userbot_client = UserBotClient()
                    
                    # 调用获取对话信息的方法
                    all_dialogs_info = await userbot_client.get_dialogs_info()
                    
                    # 将结果存入缓存
                    if self.dialogs_cache_service.is_cache_enabled() and all_dialogs_info:
                        self.dialogs_cache_service.store_in_cache(sender_id, all_dialogs_info)
                        logger.info(f"用户 {sender_id} 的对话列表已存入缓存，30分钟内有效")
                    
                except RuntimeError as e:
                    # UserBot 客户端相关错误
                    error_msg = "⚠️ User Bot 未正确初始化或未连接，无法获取对话列表。\n\n请联系管理员检查 User Bot 状态。"
                    await status_message.edit(error_msg, parse_mode='md')
                    logger.error(f"UserBot 客户端错误: {e}")
                    return
                    
                except Exception as e:
                    # 其他错误
                    error_msg = f"⚠️ 获取对话列表时发生错误: {str(e)}\n\n请稍后再试或联系管理员。"
                    await status_message.edit(error_msg, parse_mode='md')
                    logger.error(f"获取对话列表时发生未知错误: {e}", exc_info=True)
                    return
            
            # 检查对话列表是否为空
            if not all_dialogs_info:
                await status_message.edit("📭 **对话列表为空**\n\n当前账户下没有找到任何对话。", parse_mode='md')
                logger.info(f"用户 {sender_id} 的对话列表为空")
                return

            # 分页设置
            dialogs_per_page = 15  # 每页显示的对话数量，可以根据需要调整
            current_page = 1 # 初始请求总是第一页
            total_dialogs = len(all_dialogs_info)
            total_pages = (total_dialogs + dialogs_per_page - 1) // dialogs_per_page
            if total_pages == 0: # Handle case with 0 dialogs, though caught by `if not all_dialogs_info`
                total_pages = 1

            # 格式化对话列表（第一页）
            formatted_message, buttons = format_dialogs_list(
                dialogs_info=all_dialogs_info,
                current_page=current_page,
                total_pages=total_pages,
                items_per_page=dialogs_per_page
            )
            
            # 更新消息
            await status_message.edit(formatted_message, buttons=buttons, parse_mode='md')
            
            # 记录日志
            cache_status = "（来自缓存）" if cached_dialogs else "（从API获取）"
            logger.info(f"已向用户 {sender_id} 发送对话列表第 {current_page}/{total_pages} 页，共 {total_dialogs} 个对话 {cache_status}")
                
        except Exception as e:
            logger.error(f"处理 /get_dialogs 命令时出错: {e}", exc_info=True)
            try:
                await event.respond("😕 处理获取对话列表请求时出现错误，请稍后再试。")
            except Exception:
                # 如果连回复都失败了，只能记录日志
                logger.error("无法发送错误回复消息")

    async def view_search_config_command(self, event) -> None:
        """处理 /view_search_config 命令 (管理员权限)"""
        if not await self.is_admin(event):
            await event.respond("⚠️ 此命令需要管理员权限。")
            return
        try:
            config_text = "🔍 **搜索缓存配置**\n\n"
            config_text += f"- 启用缓存: `{self.config_manager.get_search_cache_enabled()}`\n"
            config_text += f"- 缓存TTL (秒): `{self.config_manager.get_search_cache_ttl()}`\n"
            config_text += f"- 初始获取条目数: `{self.config_manager.get_search_cache_initial_fetch_count()}`\n\n"
            
            cache_stats = self.cache_service.get_cache_stats()
            if cache_stats.get("enabled"):
                config_text += "**缓存状态:**\n"
                config_text += f"- 当前条目数: `{cache_stats.get('currsize', 'N/A')}`\n"
                config_text += f"- 最大条目数: `{cache_stats.get('maxsize', 'N/A')}`\n"
            else:
                config_text += "**缓存状态:** `已禁用`\n"
            
            await event.respond(config_text, parse_mode='md')
            logger.info(f"管理员 {(await event.get_sender()).id} 查看搜索缓存配置")
        except Exception as e:
            logger.error(f"处理 /view_search_config 命令时出错: {e}")
            await event.respond(f"⚠️ 查看搜索缓存配置时出现错误: {str(e)}")

    async def set_search_config_command(self, event) -> None:
        """处理 /set_search_config 命令 (管理员权限)"""
        if not await self.is_admin(event):
            await event.respond("⚠️ 此命令需要管理员权限。")
            return

        message_text = event.message.text
        match = re.match(r"^/set_search_config(?:\s+(\S+))?(?:\s+(.+))?$", message_text)

        if not match or not match.group(1) or not match.group(2):
            help_text = """请提供配置项和值，例如：
`/set_search_config enable_search_cache true`

可设置的配置项:
- `enable_search_cache` (true/false)
- `search_cache_ttl_seconds` (整数, 例如 3600)
- `search_cache_initial_fetch_count` (整数, 例如 20)

更改配置后，缓存将重新初始化。"""
            await event.respond(help_text, parse_mode='md')
            return

        key = match.group(1).lower()
        value_str = match.group(2).strip()
        
        valid_keys = {
            "enable_search_cache": lambda v: v.lower() == 'true' or v.lower() == 'false',
            "search_cache_ttl_seconds": lambda v: v.isdigit(),
            "search_cache_initial_fetch_count": lambda v: v.isdigit()
        }

        if key not in valid_keys:
            await event.respond(f"⚠️ 无效的配置项: `{key}`。请从允许的列表中选择。")
            return

        try:
            processed_value: Union[bool, int, str]
            if key == "enable_search_cache":
                if value_str.lower() not in ['true', 'false']:
                    raise ValueError("enable_search_cache 必须是 true 或 false")
                processed_value = value_str.lower() == 'true'
            elif key in ["search_cache_ttl_seconds", "search_cache_initial_fetch_count"]:
                if not value_str.isdigit():
                    raise ValueError(f"{key} 必须是一个整数")
                processed_value = int(value_str)
                if processed_value <= 0 and key != "search_cache_ttl_seconds": # TTL can be 0 for no expiry with maxsize
                     if processed_value <=0 and key == "search_cache_ttl_seconds" and self.config_manager.config.getint("SearchBot", "search_cache_ttl_seconds", fallback=1) == 0 : # allow 0 if already 0 (no expiry)
                         pass # allow 0 for TTL if it means no expiry based on cachetools
                     elif key == "search_cache_initial_fetch_count" and processed_value <=0:
                         raise ValueError(f"{key} 必须大于 0")

            else: # Should not happen due to key check
                await event.respond(f"⚠️ 未知的配置键: {key}")
                return

            # Update ConfigParser in memory
            section = "SearchBot"
            if not self.config_manager.config.has_section(section):
                self.config_manager.config.add_section(section)
            
            self.config_manager.config.set(section, key, str(processed_value)) # Store as string in ini

            # Save to config.ini
            with open(self.config_manager.config_path, "w", encoding="utf-8") as f:
                self.config_manager.config.write(f)
            
            # Reload config in ConfigManager instance
            self.config_manager.load_config() # This re-reads the file into self.config
            self.config_manager._load_search_bot_config() # This updates the specific attributes

            # Re-initialize SearchCacheService with new config
            # Pass the existing maxsize if it was set, or default. For now, use default.
            current_maxsize = self.cache_service.get_cache_stats().get('maxsize', 200) if self.cache_service.is_cache_enabled() else 200

            self.cache_service = SearchCacheService(self.config_manager, maxsize=current_maxsize)
            self.active_full_fetches.clear() # Clear ongoing fetches

            await event.respond(f"✅ 配置项 `{key}` 已更新为 `{processed_value}`。\n搜索缓存已使用新配置重新初始化。进行中的异步获取任务已清除。", parse_mode='md')
            logger.info(f"管理员 {(await event.get_sender()).id} 更新搜索配置: {key} = {processed_value}")

        except ValueError as ve:
            await event.respond(f"⚠️ 值错误: {str(ve)}")
        except Exception as e:
            logger.error(f"处理 /set_search_config 命令时出错: {e}", exc_info=True)
            await event.respond(f"⚠️ 更新搜索配置时出现严重错误: {str(e)}")

    async def clear_search_cache_command(self, event) -> None:
        """处理 /clear_search_cache 命令 (管理员权限)"""
        if not await self.is_admin(event):
            await event.respond("⚠️ 此命令需要管理员权限。")
            return
        try:
            self.cache_service.clear_cache()
            self.active_full_fetches.clear() # Clear any ongoing background fetch tasks
            await event.respond("✅ 搜索缓存已清空，进行中的异步获取任务已清除。")
            logger.info(f"管理员 {(await event.get_sender()).id} 清空了搜索缓存")
        except Exception as e:
            logger.error(f"处理 /clear_search_cache 命令时出错: {e}")
            await event.respond(f"⚠️ 清空搜索缓存时出现错误: {str(e)}")

    async def view_dialogs_cache_command(self, event) -> None:
        """处理 /view_dialogs_cache 命令 (管理员权限)"""
        if not await self.is_admin(event):
            await event.respond("⚠️ 此命令需要管理员权限。")
            return
        try:
            config_text = "💬 **对话缓存状态**\n\n"
            
            cache_stats = self.dialogs_cache_service.get_cache_stats()
            if cache_stats.get("enabled"):
                config_text += f"- 启用状态: `已启用`\n"
                config_text += f"- 缓存TTL: `{cache_stats.get('ttl', 'N/A')}秒` (30分钟)\n"
                config_text += f"- 当前条目数: `{cache_stats.get('currsize', 'N/A')}`\n"
                config_text += f"- 最大条目数: `{cache_stats.get('maxsize', 'N/A')}`\n\n"
                config_text += "**说明:**\n"
                config_text += "- 每个用户的对话列表单独缓存\n"
                config_text += "- 缓存有效期为30分钟\n"
                config_text += "- 缓存可减少对Telegram API的调用频率"
            else:
                config_text += "**状态:** `已禁用`\n\n"
                config_text += "对话缓存当前已禁用，每次请求都会直接调用Telegram API。"
            
            await event.respond(config_text, parse_mode='md')
            logger.info(f"管理员 {(await event.get_sender()).id} 查看对话缓存状态")
        except Exception as e:
            logger.error(f"处理 /view_dialogs_cache 命令时出错: {e}")
            await event.respond(f"⚠️ 查看对话缓存状态时出现错误: {str(e)}")

    async def clear_dialogs_cache_command(self, event) -> None:
        """处理 /clear_dialogs_cache 命令 (管理员权限)"""
        if not await self.is_admin(event):
            await event.respond("⚠️ 此命令需要管理员权限。")
            return
        try:
            if not self.dialogs_cache_service.is_cache_enabled():
                await event.respond("ℹ️ 对话缓存当前已禁用，无需清空。")
                return
            
            # 获取清空前的统计信息
            stats_before = self.dialogs_cache_service.get_cache_stats()
            cleared_count = stats_before.get('currsize', 0)
            
            self.dialogs_cache_service.clear_cache()
            
            await event.respond(f"✅ 对话缓存已清空。\n\n已清除 `{cleared_count}` 个缓存条目。", parse_mode='md')
            logger.info(f"管理员 {(await event.get_sender()).id} 清空了对话缓存，清除了 {cleared_count} 个条目")
        except Exception as e:
            logger.error(f"处理 /clear_dialogs_cache 命令时出错: {e}")
            await event.respond(f"⚠️ 清空对话缓存时出现错误: {str(e)}")
            
    async def set_oldest_sync_time_command(self, event) -> None:
        """
        处理 /set_oldest_sync_time 命令 (管理员权限)
        
        设置全局或特定聊天的最旧同步时间戳
        格式: /set_oldest_sync_time [chat_id] <timestamp>
        如果不提供chat_id，则设置全局时间戳
        
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
            match = re.match(r"^/set_oldest_sync_time(?:\s+(-?\d+))?(?:\s+(.+))?$", message_text)
            
            # 帮助文本
            help_text = """**设置最旧同步时间戳**
            
用法:
1. 设置全局最旧同步时间：
   `/set_oldest_sync_time 2023-01-01T00:00:00Z`

2. 设置特定聊天的最旧同步时间：
   `/set_oldest_sync_time -1001234567890 2023-01-01T00:00:00Z`

3. 移除设置：
   `/set_oldest_sync_time remove` (移除全局设置)
   `/set_oldest_sync_time -1001234567890 remove` (移除特定聊天设置)

时间戳格式可以是：
- ISO 8601日期时间 (例如: `2023-01-01T00:00:00Z`)
- Unix时间戳 (例如: `1672531200`)

早于该时间戳的历史消息将不会被同步。"""
            
            if not match or (not match.group(1) and not match.group(2)):
                # 如果没有提供任何参数，显示帮助
                await event.respond(help_text, parse_mode='md')
                return
            
            chat_id_str = match.group(1)
            timestamp_str = match.group(2)
            
            # 处理场景: /set_oldest_sync_time <timestamp> (全局设置)
            if chat_id_str and not timestamp_str:
                # 第一个参数可能是时间戳，而不是chat_id
                if not chat_id_str.startswith('-') or not chat_id_str[1:].isdigit():
                    timestamp_str = chat_id_str
                    chat_id = None
                else:
                    # 是chat_id但没有提供时间戳
                    await event.respond("请提供时间戳，例如: `/set_oldest_sync_time -1001234567890 2023-01-01T00:00:00Z`", parse_mode='md')
                    return
            else:
                # 处理场景: /set_oldest_sync_time <chat_id> <timestamp>
                chat_id = int(chat_id_str) if chat_id_str else None
            
            # 处理时间戳
            timestamp = None
            if timestamp_str and timestamp_str.lower() != 'remove':
                # 尝试解析为ISO 8601格式
                try:
                    if timestamp_str.isdigit():
                        # 是Unix时间戳
                        timestamp = int(timestamp_str)
                    else:
                        # 是ISO 8601格式
                        timestamp = timestamp_str
                except ValueError:
                    await event.respond(f"⚠️ 无效的时间戳格式: `{timestamp_str}`\n\n{help_text}", parse_mode='md')
                    return
            
            # 执行设置
            success = self.config_manager.set_oldest_sync_timestamp(chat_id, timestamp)
            
            if success:
                if chat_id is None:
                    if timestamp is None:
                        message = "✅ 已成功移除全局最旧同步时间戳设置。"
                    else:
                        message = f"✅ 已设置全局最旧同步时间戳为: `{timestamp}`"
                else:
                    if timestamp is None:
                        message = f"✅ 已成功移除聊天 `{chat_id}` 的最旧同步时间戳设置。"
                    else:
                        message = f"✅ 已设置聊天 `{chat_id}` 的最旧同步时间戳为: `{timestamp}`"
                
                await event.respond(message, parse_mode='md')
                logger.info(f"管理员 {(await event.get_sender()).id} 设置最旧同步时间戳: chat_id={chat_id}, timestamp={timestamp}")
            else:
                await event.respond("⚠️ 设置最旧同步时间戳失败，请检查参数格式。", parse_mode='md')
                
        except Exception as e:
            logger.error(f"处理 /set_oldest_sync_time 命令时出错: {e}")
            await event.respond(f"⚠️ 设置最旧同步时间戳时出现错误: {str(e)}")
    
    async def view_oldest_sync_time_command(self, event) -> None:
        """
        处理 /view_oldest_sync_time 命令 (管理员权限)
        
        查看全局或特定聊天的最旧同步时间戳
        格式: /view_oldest_sync_time [chat_id]
        如果不提供chat_id，则显示所有设置
        
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
            match = re.match(r"^/view_oldest_sync_time(?:\s+(-?\d+))?$", message_text)
            
            chat_id_str = match.group(1) if match else None
            
            if chat_id_str:
                # 查看特定聊天的设置
                chat_id = int(chat_id_str)
                timestamp = self.config_manager.get_oldest_sync_timestamp(chat_id)
                
                response = f"🕒 **聊天 `{chat_id}` 的最旧同步时间设置**\n\n"
                if timestamp:
                    response += f"最旧同步时间戳: `{timestamp.isoformat()}`\n"
                    response += f"Unix时间戳: `{int(timestamp.timestamp())}`\n\n"
                    response += "早于此时间的消息将不会被同步。"
                else:
                    response += "此聊天没有特定的最旧同步时间设置，将使用全局设置（如果有）。"
            else:
                # 查看所有设置
                sync_settings = getattr(self.config_manager, 'sync_settings', {}) or {}
                
                response = "🕒 **最旧同步时间设置**\n\n"
                
                # 显示全局设置
                if "global_oldest_sync_timestamp" in sync_settings:
                    global_timestamp = sync_settings["global_oldest_sync_timestamp"]
                    response += f"**全局设置**: `{global_timestamp}`\n\n"
                else:
                    response += "**全局设置**: 未设置\n\n"
                
                # 显示特定聊天设置
                chat_settings = [k for k in sync_settings.keys() if k != "global_oldest_sync_timestamp"]
                if chat_settings:
                    response += "**聊天特定设置**:\n"
                    for chat_id_key in chat_settings:
                        try:
                            chat_id = int(chat_id_key)
                            if isinstance(sync_settings[chat_id_key], dict) and "oldest_sync_timestamp" in sync_settings[chat_id_key]:
                                chat_timestamp = sync_settings[chat_id_key]["oldest_sync_timestamp"]
                                response += f"- 聊天 `{chat_id}`: `{chat_timestamp}`\n"
                        except (ValueError, TypeError):
                            continue
                else:
                    response += "**聊天特定设置**: 无\n"
            
            await event.respond(response, parse_mode='md')
            logger.info(f"管理员 {(await event.get_sender()).id} 查看最旧同步时间设置")
            
        except Exception as e:
            logger.error(f"处理 /view_oldest_sync_time 命令时出错: {e}", exc_info=True)
            await event.respond(f"⚠️ 查看最旧同步时间设置时出现错误: {str(e)}")

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