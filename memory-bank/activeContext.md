# 后端核心功能开发 - 工作日志 (已重置)

*(此文件用于记录当前正在执行的子任务的详细过程。下一个任务的日志将从这里开始。)*

## 任务8: `search_bot/message_formatters.py` 开发

**日期**: 2025年5月20日

### 1. 需求分析

根据 `FOLLOWME.md` 和 `PLAN.md` 中的描述，`message_formatters.py` 需要实现以下功能：

- 实现 `format_search_results(results, current_page, total_pages)` 函数
- 将 Meilisearch 返回的原始搜索结果格式化为用户友好的文本
- 每条结果应包含：消息摘要、发送者、时间和原始消息链接
- 支持分页，生成分页按钮

### 2. 资料收集

我首先检查了以下相关文件，了解数据结构和已有功能：

1. **`core/models.py`**: 了解 `MeiliMessageDoc` 的结构，包含字段如 `id`、`message_id`、`chat_id`、`chat_title`、`chat_type`、`sender_id`、`sender_name`、`text`、`date` 和 `message_link`。

2. **`user_bot/utils.py`**: 了解 `generate_message_link` 函数，它用于生成指向 Telegram 原始消息的链接。

3. **`core/meilisearch_service.py`**: 了解 `search` 方法的参数和返回结果的结构。

4. **`FOLLOWME.md`**: 查看 API 示例中的 Response Body，了解 Meilisearch 返回结果的格式。

### 3. 设计思路

1. **格式化消息内容**：
   - 对于每条搜索结果，提取重要信息（发送者、聊天标题、时间、文本内容）
   - 优先使用 Meilisearch 返回的高亮片段（如果有），使用户更容易找到匹配的内容
   - 限制文本长度，避免消息过长
   - 添加指向原始消息的链接

2. **分页设计**：
   - 使用 Telethon 的 `Button.inline` 创建内联按钮
   - 提供导航按钮：首页、上一页、当前页/总页数、下一页、末页
   - 在按钮的回调数据中包含页码和查询参数，方便 `callback_query_handlers.py` 处理分页请求

3. **错误处理**：
   - 添加 `format_error_message` 函数处理搜索异常
   - 添加 `format_help_message` 函数生成帮助消息

### 4. 实现细节

1. **`format_search_results` 函数**:
   - 返回类型为 `Tuple[str, Optional[List[List[Button]]]]`，包含格式化的消息文本和分页按钮
   - 优先使用 Meilisearch 的 `_formatted` 中的高亮片段
   - 时间戳（Unix timestamp）转换为人类可读的日期时间格式
   - 构建简洁明了的消息格式，包含序号、发送者、聊天标题、时间、文本摘要和原始消息链接
   - 对于空结果，返回友好的提示消息

2. **分页按钮处理**:
   - 根据当前页码和总页数动态生成不同的按钮组合
   - 按钮回调数据格式：`page_{页码}_{查询参数}`，用于回调查询处理
   - 限制查询参数长度，防止回调数据过大
   - 如果按钮过多，考虑拆分为两行显示

3. **错误和帮助消息**:
   - 格式化错误消息，提供用户友好的提示
   - 提供详细的搜索帮助，包括基本搜索和高级搜索语法说明

### 5. 优化考虑

1. **可扩展性**:
   - 函数设计考虑了未来可能的扩展，如添加更多过滤条件
   - 代码结构清晰，便于维护和修改

2. **用户体验**:
   - 使用 emoji 增强可读性和视觉吸引力
   - 提供清晰的导航和提示信息
   - 链接直接可点击，方便用户查看原始消息

### 6. 测试计划

由于 Search Bot 的其他部分（如 `bot.py`、`command_handlers.py` 和 `callback_query_handlers.py`）尚未实现，暂时无法进行完整的功能测试。计划在这些文件实现后，进行以下测试：

1. **单元测试**:
   - 测试 `format_search_results` 函数对各种搜索结果的格式化
   - 测试边界情况（如空结果、单页结果、多页结果）
   - 测试各种错误情况的处理

2. **集成测试**:
   - 与 `MeiliSearchService.search()` 结合测试
   - 与 Telethon 消息发送和按钮回调处理结合测试

### 7. 遇到的挑战和解决方案

1. **高亮片段处理**：
   - 挑战：需要确定 Meilisearch 是否返回了高亮片段，以及如何处理
   - 解决方案：通过检查 `_formatted` 字段是否存在并包含 `text`，决定使用高亮片段还是原始文本

2. **按钮数据存储**：
   - 挑战：需要在按钮回调数据中包含足够信息，同时保持数据量合理
   - 解决方案：使用简洁的格式 `page_{页码}_{查询参数}`，并限制查询参数长度

### 8. 总结

`search_bot/message_formatters.py` 模块已实现，提供了将 Meilisearch 搜索结果格式化为用户友好的 Telegram 消息的功能。代码已添加详细的文档和类型提示，遵循 PEP 8 规范，同时考虑了可维护性和可扩展性。

下一步是实现 `callback_query_handlers.py` 以处理分页按钮的回调，以及 `command_handlers.py` 以处理用户命令并调用搜索功能。

### 9. 单元测试

为了验证 `message_formatters.py` 的功能，我编写了单元测试文件 `tests/unit/test_message_formatters.py`，测试内容包括：

1. **空结果测试**：验证在没有搜索结果时返回适当的消息和无分页按钮
2. **单条结果测试**：验证单条结果的格式化是否正确
3. **高亮片段测试**：验证正确处理 Meilisearch 返回的高亮片段
4. **分页按钮测试**：验证在不同页码情况下（首页、中间页、末页）生成的分页按钮是否正确
5. **错误消息测试**：验证错误消息的格式化
6. **帮助消息测试**：验证帮助消息包含所有必要的信息

测试使用了 Python 的 `unittest` 框架和 `unittest.mock` 来模拟 Telethon 的 `Button` 类，这样可以在不依赖 Telethon 库的情况下测试按钮生成逻辑。

### 代码实现

```python
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