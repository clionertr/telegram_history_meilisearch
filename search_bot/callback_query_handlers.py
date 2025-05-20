"""
回调查询处理模块

此模块负责处理用户点击 Telegram Bot 消息中的 InlineKeyboardMarkup 按钮时触发的回调查询。
主要处理搜索结果的分页逻辑，接收页码变更请求，重新执行搜索并更新消息。
"""

import logging
import re
from typing import Optional, Dict, Any, List

from telethon import events, Button
from telethon.events import CallbackQuery

from core.meilisearch_service import MeiliSearchService
from search_bot.message_formatters import format_search_results, format_error_message

# 配置日志记录器
logger = logging.getLogger(__name__)


class CallbackQueryHandlers:
    """
    回调查询处理器类
    
    负责处理用户点击 InlineKeyboardMarkup 按钮时触发的回调查询，
    特别是搜索结果的分页按钮。
    """
    
    def __init__(self, client, meilisearch_service: MeiliSearchService) -> None:
        """
        初始化回调查询处理器
        
        Args:
            client: Telethon 客户端
            meilisearch_service: Meilisearch 服务实例
        """
        self.client = client
        self.meilisearch_service = meilisearch_service
        
        # 注册回调处理函数
        self.register_handlers()
        
        logger.info("回调查询处理器已初始化")
    
    def register_handlers(self) -> None:
        """
        注册所有回调查询处理函数
        """
        # 分页按钮回调处理
        self.client.add_event_handler(
            self.pagination_callback,
            events.CallbackQuery(pattern=r"^page_(\d+)_(.*)$")
        )
        
        # "noop" 按钮回调处理（当前页码按钮，不执行任何操作）
        self.client.add_event_handler(
            self.noop_callback,
            events.CallbackQuery(pattern=r"^noop$")
        )
        
        logger.info("已注册所有回调查询处理函数")
    
    async def pagination_callback(self, event: CallbackQuery.Event) -> None:
        """
        处理分页按钮的回调查询
        
        解析回调数据，提取页码和查询参数，重新执行搜索并更新消息。
        
        回调数据格式: page_{页码}_{查询参数}
        
        Args:
            event: Telethon CallbackQuery 事件对象
        """
        try:
            # 获取用户信息（用于日志）
            sender = await event.get_sender()
            user_id = sender.id
            
            # 解析回调数据
            data = event.data.decode('utf-8')
            logger.debug(f"收到分页回调: {data}, 用户: {user_id}")
            
            # 使用正则表达式提取页码和查询参数
            match = re.match(r"^page_(\d+)_(.*)$", data)
            if not match:
                logger.warning(f"无效的回调数据格式: {data}")
                await event.answer("无效的请求格式", alert=True)
                return
            
            # 提取页码和查询参数
            page = int(match.group(1))
            query = match.group(2)
            
            # 检查查询参数是否可能被截断
            if len(query) >= 20:  # 在 message_formatters.py 中查询参数被限制为 20 个字符
                logger.warning(f"查询参数可能被截断: {query}")
                # 这里我们仍然使用截断的查询，但记录警告
                # 未来可以考虑实现用户会话存储或缓存完整查询
            
            logger.info(f"处理分页请求: 页码={page}, 查询='{query}', 用户={user_id}")
            
            # 通知用户正在处理
            await event.answer("正在加载新页面...")
            
            # 设置搜索参数
            hits_per_page = 5  # 与 command_handlers.py 中保持一致
            sort = ["date:desc"]  # 默认按时间倒序
            
            # 执行搜索
            results = self.meilisearch_service.search(
                query=query,
                filters=None,  # 注意：这里我们没有保留高级过滤条件，这是一个简化实现的局限
                sort=sort,
                page=page,
                hits_per_page=hits_per_page
            )
            
            # 计算总页数
            total_hits = results.get('estimatedTotalHits', 0)
            total_pages = (total_hits + hits_per_page - 1) // hits_per_page if total_hits > 0 else 0
            
            # 格式化搜索结果
            formatted_message, buttons = format_search_results(results, page, total_pages)
            
            # 更新消息，使用纯文本模式
            await event.edit(
                formatted_message,
                buttons=buttons,
                parse_mode=None  # 使用纯文本模式，避免Markdown解析冲突
            )
            
            logger.info(f"已更新分页消息: 页码={page}/{total_pages}, 用户={user_id}")
            
        except Exception as e:
            logger.error(f"处理分页回调时出错: {e}")
            try:
                await event.answer(f"加载页面出错: {str(e)[:200]}", alert=True)
            except:
                # 如果无法通过 answer 显示错误，尝试编辑消息
                try:
                    error_message = format_error_message(f"加载页面出错: {str(e)}")
                    await event.edit(error_message, parse_mode=None)  # 使用纯文本模式
                except:
                    logger.error("无法通知用户错误信息")
    
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
    meilisearch_service: MeiliSearchService
) -> CallbackQueryHandlers:
    """
    创建回调查询处理器并将其注册到客户端
    
    Args:
        client: Telethon 客户端
        meilisearch_service: Meilisearch 服务实例
        
    Returns:
        CallbackQueryHandlers: 回调查询处理器实例
    """
    handler = CallbackQueryHandlers(
        client=client,
        meilisearch_service=meilisearch_service
    )
    
    return handler