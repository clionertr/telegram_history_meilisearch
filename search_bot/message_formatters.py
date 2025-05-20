"""
消息格式化模块

此模块负责将从 Meilisearch 返回的原始搜索结果数据格式化为用户友好的文本，
准备在 Telegram Bot 中展示。还负责生成分页按钮等交互元素。
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from telethon import Button

from user_bot.utils import generate_message_link

# 配置日志记录器
logger = logging.getLogger(__name__)


def format_search_results(
    results: Dict[str, Any], 
    current_page: int, 
    total_pages: int
) -> Tuple[str, Optional[List[List[Button]]]]:
    """
    格式化 Meilisearch 搜索结果为用户友好的文本
    
    将 Meilisearch 返回的原始搜索结果格式化为用户友好的文本，
    包括消息摘要、发送者、时间和原始消息链接。
    同时生成分页按钮。
    
    Args:
        results: Meilisearch 返回的搜索结果字典
        current_page: 当前页码，从 1 开始
        total_pages: 总页数
        
    Returns:
        Tuple[str, Optional[List[List[Button]]]]: 
            - 格式化后的消息文本
            - 分页按钮列表（如果有分页）或 None（如果没有分页）
    """
    if not results or 'hits' not in results or not results['hits']:
        return "😕 未找到匹配的消息。请尝试其他关键词或检查搜索语法。", None
    
    # 提取基本搜索信息
    query = results.get('query', '')
    total_hits = results.get('estimatedTotalHits', 0)
    processing_time = results.get('processingTimeMs', 0)
    
    # 构建消息头部
    message_parts = [
        f"🔍 **搜索结果: \"{query}\"**\n",
        f"📊 找到约 {total_hits} 条匹配消息 (用时 {processing_time}ms)\n",
        f"📄 第 {current_page}/{total_pages} 页\n\n"
    ]
    
    # 遍历结果，格式化每条消息
    for index, hit in enumerate(results['hits'], 1):
        # 获取消息基本信息
        chat_title = hit.get('chat_title', '未知聊天')
        sender_name = hit.get('sender_name', '未知发送者')
        
        # 处理日期时间 (Unix 时间戳转换为可读格式)
        timestamp = hit.get('date', 0)
        date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        
        # 获取消息链接
        message_link = hit.get('message_link', '')
        
        # 获取消息文本，优先使用 Meilisearch 的高亮片段（如果有）
        if '_formatted' in hit and 'text' in hit['_formatted']:
            # Meilisearch 返回的高亮片段，已包含高亮标记
            text_preview = hit['_formatted']['text']
        else:
            # 如果没有高亮片段，使用原始文本并截取合适长度
            original_text = hit.get('text', '')
            text_preview = (original_text[:150] + '...') if len(original_text) > 150 else original_text
        
        # 格式化单条消息
        message_parts.append(
            f"{index}. **{sender_name}** 在 **{chat_title}** 中发表于 {date_str}\n"
            f"{text_preview}\n"
            f"[👉 查看原消息]({message_link})\n\n"
        )
    
    # 构建分页按钮 (如果需要)
    buttons = None
    if total_pages > 1:
        # 创建一组按钮，我们限制为:
        # 1. 首页按钮 (如果不在第一页)
        # 2. 上一页按钮 (如果不在第一页)
        # 3. 当前页码/总页数
        # 4. 下一页按钮 (如果不在最后一页)
        # 5. 末页按钮 (如果不在最后一页)
        buttons_row = []
        
        # 每个按钮存储数据格式：page_{页码}_{搜索查询}
        query_param = query[:30]  # 限制查询参数长度，防止数据过大
        
        # 首页和上一页按钮 (如果当前不在第一页)
        if current_page > 1:
            buttons_row.append(Button.inline("⏮ 首页", f"page_1_{query_param}"))
            buttons_row.append(Button.inline("◀️ 上一页", f"page_{current_page - 1}_{query_param}"))
        
        # 当前页/总页数按钮 (不可点击)
        buttons_row.append(Button.inline(f"📄 {current_page}/{total_pages}", f"noop"))
        
        # 下一页和末页按钮 (如果当前不在最后一页)
        if current_page < total_pages:
            buttons_row.append(Button.inline("▶️ 下一页", f"page_{current_page + 1}_{query_param}"))
            buttons_row.append(Button.inline("⏭ 末页", f"page_{total_pages}_{query_param}"))
        
        buttons = [buttons_row]
        
        # 如果按钮超过5个，拆分为两行
        if len(buttons_row) > 5:
            nav_buttons = buttons_row[:2] + buttons_row[3:]  # 导航按钮
            page_button = [buttons_row[2]]  # 页码按钮
            buttons = [nav_buttons, page_button]
    
    # 合并所有消息部分
    formatted_message = ''.join(message_parts)
    
    logger.debug(f"已格式化搜索结果，包含 {len(results['hits'])} 条消息，共 {total_pages} 页")
    return formatted_message, buttons


def format_error_message(error_message: str) -> str:
    """
    格式化错误消息
    
    将错误消息格式化为用户友好的文本
    
    Args:
        error_message: 错误信息
        
    Returns:
        str: 格式化后的错误消息
    """
    return f"⚠️ **搜索出错**\n\n{error_message}\n\n请检查您的搜索语法或稍后再试。"


def format_help_message() -> str:
    """
    生成帮助消息
    
    返回搜索功能的帮助说明
    
    Returns:
        str: 帮助说明文本
    """
    return (
        "🔍 **Telegram 中文历史消息搜索**\n\n"
        "**基本搜索**:\n"
        "直接发送关键词，如: `/search 如何学习Python`\n\n"
        "**高级搜索**:\n"
        "1. 精确短语: `\"关键短语\"`，如: `/search \"机器学习算法\"`\n"
        "2. 类型筛选: `type:类型`，如: `/search 学习 type:group`\n"
        "   支持的类型: user(私聊), group(群组), channel(频道)\n"
        "3. 时间筛选: `date:起始_结束`，如: `/search 会议 date:2023-01-01_2023-12-31`\n"
        "   日期格式: YYYY-MM-DD\n"
        "4. 组合使用: `/search \"项目进度\" type:group date:2023-01-01_2023-12-31`\n\n"
        "**提示**:\n"
        "- 默认显示最相关的结果，按页面底部按钮翻页查看更多\n"
        "- 点击消息下方链接可跳转到原始消息\n"
    )