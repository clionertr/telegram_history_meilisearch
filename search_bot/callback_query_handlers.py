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
        self.cache_service = command_handler.cache_service # Convenience access for search cache
        self.dialogs_cache_service = command_handler.dialogs_cache_service # Convenience access for dialogs cache
        
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
            events.CallbackQuery(pattern=r"^search_page:(\d+):(.+)$") # Updated pattern for search
        )

        # 对话列表分页按钮回调处理
        self.client.add_event_handler(
            self.dialog_pagination_callback,
            events.CallbackQuery(pattern=r"^dialog_page:(\d+)$")
        )
        
        # "noop" 按钮回调处理（当前页码按钮，不执行任何操作）
        # Generic noop for search
        self.client.add_event_handler(
            self.noop_callback, # Can be reused if message is generic
            events.CallbackQuery(pattern=r"^noop$")
        )
        # Specific noop for dialog page button, if different message is desired
        self.client.add_event_handler(
            self.noop_dialog_callback,
            events.CallbackQuery(pattern=r"^noop_dialog_page$")
        )
        
        logger.info("已注册所有回调查询处理函数, 包括对话列表分页")

    async def pagination_callback(self, event: CallbackQuery.Event) -> None:
        """
        处理搜索结果分页按钮的回调查询 (search_page:<page_num>:<original_query_b64>)
        """
        try:
            sender = await event.get_sender()
            user_id = sender.id
            data = event.data.decode('utf-8')
            logger.debug(f"收到搜索分页回调: {data}, 用户: {user_id}")

            match = re.match(r"^search_page:(\d+):(.+)$", data)
            if not match:
                logger.warning(f"无效的搜索分页回调数据格式: {data}")
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

            logger.info(f"处理搜索分页请求: 页码={page}, 原始查询='{original_query}', 用户={user_id}")
            
            # Use command_handler methods to parse and build filters
            parsed_query, filters_dict = self.command_handler._parse_advanced_syntax(original_query) # pylint: disable=protected-access
            meili_filters = self.command_handler._build_meilisearch_filters(filters_dict) if filters_dict else None # pylint: disable=protected-access

            hits_per_page = 5  # Standard items per page for search
            sort_options = ["date:desc"]

            # Check cache
            cached_entry = None
            if self.cache_service.is_cache_enabled():
                cached_entry = self.cache_service.get_from_cache(parsed_query, filters_dict)

            if cached_entry:
                cached_results, is_partial, total_hits_from_cache, fetch_ts = cached_entry
                logger.info(f"搜索分页缓存命中 for '{parsed_query}'. Partial: {is_partial}, Total Hits: {total_hits_from_cache}")

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
            logger.info(f"搜索分页缓存未命中/不足 for '{parsed_query}', page {page}. 直接从 MeiliSearch 获取。")
            await event.answer("正在加载新页面...") # Toast notification
            
            page_specific_results_obj = await self.command_handler._get_results_from_meili( # pylint: disable=protected-access
                parsed_query, meili_filters, sort_options, page, hits_per_page
            )
            estimated_total_hits = page_specific_results_obj.get('estimatedTotalHits', 0)
            total_pages = (estimated_total_hits + hits_per_page - 1) // hits_per_page if estimated_total_hits > 0 else 0
            
            formatted_msg, buttons = format_search_results(page_specific_results_obj, page, total_pages, query_original=original_query)
            await event.edit(formatted_msg, buttons=buttons, parse_mode='md')

        except Exception as e:
            logger.error(f"处理搜索分页回调时出错: {e}", exc_info=True)
            try:
                await event.answer(f"加载页面出错: {str(e)[:190]}", alert=True)
            except Exception:
                try:
                    error_text = format_error_message(f"加载页面时出错: {str(e)}")
                    await event.edit(error_text, parse_mode='md')
                except Exception:
                    logger.error("无法通过 answer 或 edit 通知用户搜索分页错误")

    async def dialog_pagination_callback(self, event: CallbackQuery.Event) -> None:
        """
        处理对话列表分页按钮的回调查询 (dialog_page:<page_num>)
        """
        try:
            sender = await event.get_sender()
            user_id = sender.id
            data = event.data.decode('utf-8')
            logger.debug(f"收到对话列表分页回调: {data}, 用户: {user_id}")

            match = re.match(r"^dialog_page:(\d+)$", data)
            if not match:
                logger.warning(f"无效的对话列表分页回调数据格式: {data}")
                await event.answer("无效的请求格式", alert=True)
                return

            page = int(match.group(1))
            logger.info(f"处理对话列表分页请求: 页码={page}, 用户={user_id}")
            
            await event.answer("正在加载对话列表页面...") # Toast notification

            # 导入必要的模块
            from user_bot.client import UserBotClient # Local import
            from search_bot.message_formatters import format_dialogs_list # Ensure it's available

            all_dialogs_info = None
            cache_hit = False

            # 尝试从缓存获取对话列表
            if self.dialogs_cache_service.is_cache_enabled():
                all_dialogs_info = self.dialogs_cache_service.get_from_cache(user_id)
                if all_dialogs_info:
                    cache_hit = True
                    logger.info(f"对话列表分页: 用户 {user_id} 缓存命中，共 {len(all_dialogs_info)} 个对话")

            if not all_dialogs_info:
                # 缓存未命中或缓存禁用，从API获取
                logger.info(f"对话列表分页: 用户 {user_id} 缓存未命中或禁用，从API获取")

                try:
                    userbot_client = UserBotClient() # Get singleton instance
                    all_dialogs_info = await userbot_client.get_dialogs_info()

                    # 如果获取成功且缓存启用，则存入缓存
                    if all_dialogs_info and self.dialogs_cache_service.is_cache_enabled():
                        self.dialogs_cache_service.store_in_cache(user_id, all_dialogs_info)
                        logger.info(f"对话列表分页: 用户 {user_id} 的对话列表已存入缓存")
                except RuntimeError as e:
                    error_msg = "⚠️ User Bot 未正确初始化或未连接，无法获取对话列表分页数据。"
                    await event.edit(error_msg, parse_mode='md')
                    logger.error(f"对话列表分页: UserBot 客户端错误: {e}")
                    return
                except Exception as e:
                    error_msg = f"⚠️ 获取对话列表分页数据时发生错误: {str(e)}"
                    await event.edit(error_msg, parse_mode='md')
                    logger.error(f"对话列表分页: 获取对话列表时发生未知错误: {e}", exc_info=True)
                    return
            
            if not all_dialogs_info: # 再次检查，以防API调用也返回空
                await event.edit("📭 **对话列表为空**\n\n当前账户下没有找到任何对话。", parse_mode='md')
                logger.info(f"用户 {user_id} 的对话列表在分页时变为空")
                return

            dialogs_per_page = 15 # Should be consistent with CommandHandlers
            total_dialogs = len(all_dialogs_info)
            total_pages = (total_dialogs + dialogs_per_page - 1) // dialogs_per_page
            if total_pages == 0: total_pages = 1


            if page < 1 or page > total_pages:
                logger.warning(f"请求的对话页码 {page} 超出范围 (1-{total_pages})")
                await event.answer("请求的页码无效", alert=True)
                # Optionally, edit message to show first/last page or an error
                # For now, just answer and don't change the message.
                return

            formatted_msg, buttons = format_dialogs_list(
                dialogs_info=all_dialogs_info,
                current_page=page,
                total_pages=total_pages,
                items_per_page=dialogs_per_page
            )
            await event.edit(formatted_msg, buttons=buttons, parse_mode='md')
            # No event.answer() here as edit is confirmation

        except Exception as e:
            logger.error(f"处理对话列表分页回调时出错: {e}", exc_info=True)
            try:
                await event.answer(f"加载对话页面出错: {str(e)[:190]}", alert=True)
            except Exception:
                try:
                    # Use a generic error formatter if available, or simple text
                    await event.edit(f"⚠️ 加载对话页面时发生错误: {str(e)}", parse_mode='md')
                except Exception:
                    logger.error("无法通过 answer 或 edit 通知用户对话列表分页错误")

    async def noop_callback(self, event: CallbackQuery.Event) -> None:
        """处理通用 noop 回调 (不执行任何操作)"""
        try:
            await event.answer("这是当前页面", alert=False) # Generic message
        except Exception as e:
            logger.error(f"处理通用 noop 回调时出错: {e}")

    async def noop_dialog_callback(self, event: CallbackQuery.Event) -> None:
        """处理对话列表 noop 回调 (不执行任何操作)"""
        try:
            # You could customize the message for dialogs if needed
            await event.answer("这是当前对话列表页面", alert=False)
        except Exception as e:
            logger.error(f"处理对话 noop 回调时出错: {e}")


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