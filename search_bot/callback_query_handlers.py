"""
回调查询处理模块

此模块负责处理用户点击 Telegram Bot 消息中的 InlineKeyboardMarkup 按钮时触发的回调查询。
主要处理搜索结果的分页逻辑，接收页码变更请求，重新执行搜索并更新消息。
"""

import logging
import re
import base64 # Added
import time   # Added
from typing import Optional, Dict, Any, List

from telethon import events, Button
from telethon.events import CallbackQuery

from core.meilisearch_service import MeiliSearchService # Will be accessed via command_handler
from search_bot.message_formatters import format_search_results, format_error_message
# Import CommandHandlers for type hinting, assuming it won't create circular dependency
# If it does, we might need to use 'from typing import TYPE_CHECKING' and forward reference
from search_bot.command_handlers import CommandHandlers

# 配置日志记录器
logger = logging.getLogger(__name__)


class CallbackQueryHandlers:
    """
    回调查询处理器类
    
    负责处理用户点击 InlineKeyboardMarkup 按钮时触发的回调查询，
    特别是搜索结果的分页按钮。
    """
    
    def __init__(self, client, command_handler: CommandHandlers) -> None: # Changed meilisearch_service to command_handler
        """
        初始化回调查询处理器
        
        Args:
            client: Telethon 客户端
            command_handler: CommandHandlers 实例，用于访问缓存服务和搜索逻辑
        """
        self.client = client
        self.command_handler = command_handler # Store CommandHandlers instance
        self.cache_service = command_handler.cache_service # Convenience access
        
        # 注册回调处理函数
        self.register_handlers()
        
        logger.info("回调查询处理器已初始化")
    
    def register_handlers(self) -> None:
        """
        注册所有回调查询处理函数
        """
        # 分页按钮回调处理 - New pattern for base64 encoded full query
        self.client.add_event_handler(
            self.pagination_callback,
            events.CallbackQuery(pattern=r"^search_page:(\d+):(.+)$") # Updated pattern
        )
        
        # "noop" 按钮回调处理（当前页码按钮，不执行任何操作）
        self.client.add_event_handler(
            self.noop_callback,
            events.CallbackQuery(pattern=r"^noop$")
        )
        
        logger.info("已注册所有回调查询处理函数")

    async def pagination_callback(self, event: CallbackQuery.Event) -> None:
        """
        处理分页按钮的回调查询 (search_page:<page_num>:<original_query_b64>)
        """
        try:
            sender = await event.get_sender()
            user_id = sender.id
            data = event.data.decode('utf-8')
            logger.debug(f"收到分页回调: {data}, 用户: {user_id}")

            match = re.match(r"^search_page:(\d+):(.+)$", data)
            if not match:
                logger.warning(f"无效的回调数据格式: {data}")
                await event.answer("无效的请求格式", alert=True)
                return

            page = int(match.group(1))
            original_query_b64 = match.group(2)
            
            try:
                original_query = base64.b64decode(original_query_b64).decode('utf-8')
            except Exception as e:
                logger.error(f"Base64解码原始查询失败: {e} (data: {original_query_b64})")
                await event.answer("无法解析查询参数", alert=True)
                return

            logger.info(f"处理分页请求: 页码={page}, 原始查询='{original_query}', 用户={user_id}")
            
            # Use command_handler methods to parse and build filters
            parsed_query, filters_dict = self.command_handler._parse_advanced_syntax(original_query) # pylint: disable=protected-access
            meili_filters = self.command_handler._build_meilisearch_filters(filters_dict) if filters_dict else None # pylint: disable=protected-access

            hits_per_page = 5  # Standard items per page
            sort_options = ["date:desc"]

            # Check cache
            cached_entry = None
            if self.cache_service.is_cache_enabled():
                cached_entry = self.cache_service.get_from_cache(parsed_query, filters_dict)

            if cached_entry:
                cached_results, is_partial, total_hits_from_cache, fetch_ts = cached_entry
                logger.info(f"分页缓存命中 for '{parsed_query}'. Partial: {is_partial}, Total Hits: {total_hits_from_cache}")

                if not is_partial: # Full data in cache
                    results_to_format = {
                        'hits': cached_results[(page - 1) * hits_per_page : page * hits_per_page],
                        'query': parsed_query, 'processingTimeMs': 0, 'estimatedTotalHits': total_hits_from_cache
                    }
                    total_pages = (total_hits_from_cache + hits_per_page - 1) // hits_per_page if total_hits_from_cache > 0 else 0
                    formatted_msg, buttons = format_search_results(results_to_format, page, total_pages, query_original=original_query)
                    await event.edit(formatted_msg, buttons=buttons, parse_mode='md')
                    await event.answer() # Acknowledge callback
                    return

                # Partial data in cache
                if total_hits_from_cache is not None:
                    if page * hits_per_page <= len(cached_results): # Page is within the initial fetch
                        results_to_format = {
                            'hits': cached_results[(page - 1) * hits_per_page : page * hits_per_page],
                            'query': parsed_query, 'processingTimeMs': 0, 'estimatedTotalHits': total_hits_from_cache
                        }
                        total_pages = (total_hits_from_cache + hits_per_page - 1) // hits_per_page if total_hits_from_cache > 0 else 0
                        formatted_msg, buttons = format_search_results(results_to_format, page, total_pages, query_original=original_query)
                        await event.edit(formatted_msg, buttons=buttons, parse_mode='md')
                        await event.answer() # Acknowledge callback
                        return
                    else: # Requested page is beyond initial fetch
                        cache_key_for_async = self.cache_service._generate_cache_key(parsed_query, filters_dict) # pylint: disable=protected-access
                        if cache_key_for_async in self.command_handler.active_full_fetches or \
                           (fetch_ts is not None and time.time() - fetch_ts < 60): # Task running or recently started
                            await event.answer("⏳ 更多结果加载中，请稍候再试...", alert=False) # Toast notification
                            return
                        else: # Full fetch might have completed or failed. Re-check cache.
                            fresh_cached_entry = self.cache_service.get_from_cache(parsed_query, filters_dict)
                            if fresh_cached_entry and not fresh_cached_entry[1]: # is_partial is False
                                cached_results_upd, _, total_hits_upd, _ = fresh_cached_entry
                                results_to_format = {
                                    'hits': cached_results_upd[(page - 1) * hits_per_page : page * hits_per_page],
                                    'query': parsed_query, 'processingTimeMs': 0, 'estimatedTotalHits': total_hits_upd
                                }
                                total_pages = (total_hits_upd + hits_per_page - 1) // hits_per_page if total_hits_upd > 0 else 0
                                formatted_msg, buttons = format_search_results(results_to_format, page, total_pages, query_original=original_query)
                                await event.edit(formatted_msg, buttons=buttons, parse_mode='md')
                                await event.answer() # Acknowledge callback
                                return
            
            # Cache miss or partial data not sufficient, and async fetch not helpful. Fetch directly.
            logger.info(f"分页缓存未命中/不足 for '{parsed_query}', page {page}. 直接从 MeiliSearch 获取。")
            await event.answer("正在加载新页面...") # Toast notification
            
            page_specific_results_obj = await self.command_handler._get_results_from_meili( # pylint: disable=protected-access
                parsed_query, meili_filters, sort_options, page, hits_per_page
            )
            estimated_total_hits = page_specific_results_obj.get('estimatedTotalHits', 0)
            total_pages = (estimated_total_hits + hits_per_page - 1) // hits_per_page if estimated_total_hits > 0 else 0
            
            formatted_msg, buttons = format_search_results(page_specific_results_obj, page, total_pages, query_original=original_query)
            await event.edit(formatted_msg, buttons=buttons, parse_mode='md')
            # No event.answer() here as the edit itself is a confirmation if it doesn't error.
            # If an error occurs during edit, the except block will handle event.answer.

        except Exception as e:
            logger.error(f"处理分页回调时出错: {e}", exc_info=True)
            try:
                # Try to answer with an alert, this is more likely to be seen by the user.
                await event.answer(f"加载页面出错: {str(e)[:190]}", alert=True) # Max 200 chars for answer
            except Exception: # pylint: disable=broad-except
                # Fallback to editing message if answer fails (e.g., if callback already answered)
                try:
                    error_text = format_error_message(f"加载页面时出错: {str(e)}")
                    await event.edit(error_text, parse_mode='md')
                except Exception: # pylint: disable=broad-except
                    logger.error("无法通过 answer 或 edit 通知用户分页错误")

    async def noop_callback(self, event: CallbackQuery.Event) -> None:
        """
        处理 noop 回调 (不执行任何操作)
        
        用于当前页码按钮，仅显示提示但不执行任何操作
        
        Args:
            event: Telethon CallbackQuery 事件对象
        """
        try:
            await event.answer("这是当前页面", alert=False)
        except Exception as e:
            logger.error(f"处理 noop 回调时出错: {e}")


# 辅助函数：创建回调查询处理器并注册到客户端
def setup_callback_handlers(
    client,
    command_handler: CommandHandlers # Changed
) -> CallbackQueryHandlers:
    """
    创建回调查询处理器并将其注册到客户端
    
    Args:
        client: Telethon 客户端
        command_handler: CommandHandlers 实例
        
    Returns:
        CallbackQueryHandlers: 回调查询处理器实例
    """
    handler = CallbackQueryHandlers(
        client=client,
        command_handler=command_handler # Pass command_handler
    )
    
    return handler