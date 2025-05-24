"""
消息格式化模块

此模块负责将从 Meilisearch 返回的原始搜索结果数据格式化为用户友好的文本，
准备在 Telegram Bot 中展示。还负责生成分页按钮等交互元素。
"""

import logging
import re
import base64 # Added
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from telethon import Button

from user_bot.utils import generate_message_link

# 添加正则表达式模式，用于清理Markdown标记
MARKDOWN_PATTERNS = [
    (r'\*\*(.*?)\*\*', r'\1'),  # 移除加粗标记 **text** -> text
    (r'\[(.*?)\]\((.*?)\)', r'\1')  # 移除链接标记 [text](url) -> text
]

# 配置日志记录器
logger = logging.getLogger(__name__)


def format_search_results(
    results: Dict[str, Any],
    current_page: int,
    total_pages: int,
    query_original: Optional[str] = None  # Added: The original full query for callback data
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
        query_original: 原始的、未解析的搜索查询字符串 (包含过滤器等)
        
    Returns:
        Tuple[str, Optional[List[List[Button]]]]:
            - 格式化后的消息文本
            - 分页按钮列表（如果有分页）或 None（如果没有分页）
    """
    # 验证结果数据的完整性
    if not results:
        return "😕 未找到匹配的消息。搜索结果为空。", None
    
    # 确保 hits 字段存在且不为空
    hits = results.get('hits', [])
    if not hits:
        return "😕 未找到匹配的消息。请尝试其他关键词或检查搜索语法。", None
    
    # 提取基本搜索信息，使用安全的 get 方法并提供默认值
    # query_displayed will be the parsed query from Meili results,
    # query_original is the full user input used for consistent callbacks
    query_displayed = results.get('query', '未知查询')
    if query_original is None:
        logger.warning("format_search_results called without query_original. Pagination might lose filters.")
        query_for_callback_raw = query_displayed # Fallback, might be just keywords
    else:
        query_for_callback_raw = query_original

    total_hits = results.get('estimatedTotalHits', len(hits))
    processing_time = results.get('processingTimeMs', 0)
    
    # 构建消息头部 (Markdown 格式)
    # Display the original query if available and different from parsed, or just parsed
    display_query_in_header = query_original if query_original and query_original.strip() != query_displayed.strip() else query_displayed
    
    message_parts = [
        f"🔍 搜索结果: \"**{display_query_in_header}**\"\n",
        f"📊 找到约 **{total_hits}** 条匹配消息 (用时 **{processing_time}ms**)\n",
        f"📄 第 **{current_page}/{total_pages}** 页\n\n"
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
        
        # 获取消息文本，安全处理高亮片段
        original_text = hit.get('text', '')
        
        # 清理原始文本中的Markdown标记，避免解析冲突
        cleaned_text = original_text
        for pattern, replacement in MARKDOWN_PATTERNS:
            cleaned_text = re.sub(pattern, replacement, cleaned_text)
        
        # 截取文本预览并处理长度
        text_preview = cleaned_text[:150]
        if len(cleaned_text) > 150:
            text_preview += '...'
        
        # 格式化单条消息，确保所有变量都不为空，防止实体边界问题
        safe_sender = sender_name or "未知发送者"
        safe_chat = chat_title or "未知聊天"
        safe_link = message_link or "#"  # 使用安全的默认链接
        
        # 构建消息部分
        # 添加分割线 (如果不是第一条消息且有多条消息)
        if index > 1 and len(hits) > 1:
            message_parts.append("─・─・─・─\n")

        message_parts.append(
            f"{index}. **{safe_sender}** 在 **{safe_chat}** 中发表于 {date_str}\n"  # 发送者和聊天标题加粗
            f"{text_preview}\n"
            f"[👉 查看原消息]({safe_link})\n\n"  # Markdown 链接按钮
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
        
        # 每个按钮存储数据格式：search_page:{页码}:{base64_encoded_original_query}
        try:
            encoded_query_for_callback = base64.b64encode(query_for_callback_raw.encode('utf-8')).decode('utf-8')
        except Exception as e:
            logger.error(f"无法对查询进行Base64编码: '{query_for_callback_raw}', error: {e}")
            # Fallback: use a placeholder or truncated query if encoding fails, though this is bad.
            # This should ideally not happen.
            encoded_query_for_callback = base64.b64encode("error_encoding_query".encode('utf-8')).decode('utf-8')

        
        # 首页和上一页按钮 (如果当前不在第一页)
        if current_page > 1:
            buttons_row.append(Button.inline("⏮ 首页", f"search_page:1:{encoded_query_for_callback}"))
            buttons_row.append(Button.inline("◀️ 上一页", f"search_page:{current_page - 1}:{encoded_query_for_callback}"))
        
        # 当前页/总页数按钮 (不可点击)
        buttons_row.append(Button.inline(f"📄 {current_page}/{total_pages}", f"noop")) # noop is fine
        
        # 下一页和末页按钮 (如果当前不在最后一页)
        if current_page < total_pages:
            buttons_row.append(Button.inline("▶️ 下一页", f"search_page:{current_page + 1}:{encoded_query_for_callback}"))
            buttons_row.append(Button.inline("⏭ 末页", f"search_page:{total_pages}:{encoded_query_for_callback}"))
        
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
    return f"⚠️ 搜索出错\n\n{error_message}\n\n请检查您的搜索语法或稍后再试。"


def format_help_message() -> str:
    """
    生成帮助消息
    
    返回搜索功能的帮助说明
    
    Returns:
        str: 帮助说明文本
    """
    help_text = """
🔍 **Telegram 中文历史消息搜索机器人 - 帮助文档**

**基本搜索:**
- 直接发送关键词进行搜索: `/search <你的关键词>`
  例如: `/search 如何学习Python`

**高级搜索语法:**
- **精确短语**: 使用双引号包裹短语 `"<关键短语>"`
  例如: `/search "机器学习算法"`
- **类型筛选**: `type:<类型>` (user/group/channel)
  例如: `/search 学习 type:group`
- **时间筛选**: `date:<起始日期>_<结束日期>` (YYYY-MM-DD)
  例如: `/search 会议 date:2023-01-01_2023-12-31`
  (如果只提供起始日期，则默认为搜索到当前日期)
- **组合使用**: 可以组合上述所有高级语法
  例如: `/search "项目进度" type:group date:2023-01-01_2023-12-31`

**搜索结果:**
- 默认按相关性排序，并按时间倒序排列。
- 点击结果下方的链接可直接跳转到原始消息位置。
- 使用页面底部的按钮进行翻页。

**对话管理:**
- `/get_dialogs`: 获取当前账户下的所有对话列表，包括对话名称和ID。
  这些ID可用于白名单管理命令。

---

**管理员命令 (仅限管理员使用):**

**User Bot 配置管理:**
- `/set_userbot_config <配置项> <值>`: 设置 User Bot 的配置。
  例如: `/set_userbot_config USER_SESSION_NAME my_new_session`
  可配置项包括: `USER_API_ID`, `USER_API_HASH`, `USER_SESSION_NAME`, `USER_PROXY_URL`。
  *注意: 修改配置后，需要使用 `/restart_userbot` 命令使配置生效。*
- `/view_userbot_config`: 查看 User Bot 当前的主要配置项 (敏感信息会打码)。
- `/restart_userbot`: 重启 User Bot 以应用新的配置或解决一些问题。

**白名单管理:**
- `/add_whitelist <chat_id>`: 将指定的 chat_id 添加到 User Bot 的消息同步白名单。
- `/remove_whitelist <chat_id>`: 从白名单中移除指定的 chat_id。

**最旧同步时间管理:**
- `/set_oldest_sync_time [chat_id] <timestamp>`: 设置最旧同步时间戳，限制历史同步范围。
  例如:
  - 设置全局时间戳: `/set_oldest_sync_time 2023-01-01T00:00:00Z`
  - 设置特定聊天时间戳: `/set_oldest_sync_time -1001234567890 2023-01-01T00:00:00Z`
  - 移除设置: `/set_oldest_sync_time remove` 或 `/set_oldest_sync_time -1001234567890 remove`
- `/view_oldest_sync_time [chat_id]`: 查看当前的最旧同步时间设置。
  例如:
  - 查看所有设置: `/view_oldest_sync_time`
  - 查看特定聊天设置: `/view_oldest_sync_time -1001234567890`

*注意: 最旧同步时间设置可限制历史同步的范围，早于该时间戳的消息将不会被同步到搜索系统中，有助于减少存储开销。*

**缓存管理:**
- `/view_search_config`: 查看搜索缓存配置和状态。
- `/set_search_config <配置项> <值>`: 设置搜索缓存配置。
- `/clear_search_cache`: 清空搜索缓存。
- `/view_dialogs_cache`: 查看对话缓存状态。
- `/clear_dialogs_cache`: 清空对话缓存。

---

**配置文件说明:**

本系统使用多个配置文件来管理不同的设置：
1.  **`config.ini`**: 存放通用的、非敏感的应用程序配置。
2.  **`.env`**: 存放全局的、敏感的配置信息和环境变量，例如 Search Bot 的 Token、MeiliSearch API Key、管理员 ID 等。**此文件不应提交到版本控制。**
3.  **`.env.userbot`**: 专门存放 User Bot 的配置信息，特别是 API ID 和 API Hash。**此文件不应提交到版本控制。** `/set_userbot_config` 命令会修改此文件。

**配置加载优先级:**
- **User Bot 特定配置** (如 `USER_API_ID`):
  1. `.env.userbot` (最高)
  2. `.env` (作为环境变量)
  3. `config.ini` (最低)
- **其他配置**:
  1. `.env` (作为环境变量) (最高)
  2. `config.ini` (最低)

---

**如何设置管理员:**

管理员权限用于执行 `/add_whitelist`, `/remove_whitelist`, `/set_userbot_config`, `/view_userbot_config`, `/restart_userbot` 等命令。
可以通过以下任一方式设置管理员用户 ID (Telegram User ID):

1.  **通过 `.env` 文件:**
    在项目根目录的 `.env` 文件中添加或修改 `ADMIN_IDS` 变量，多个 ID 用逗号分隔:
    ```
    ADMIN_IDS=123456789,987654321
    ```
2.  **通过 `config.ini` 文件:**
    在项目根目录的 `config.ini` 文件的 `[Telegram]` 部分添加或修改 `ADMIN_IDS` 配置项:
    ```ini
    [Telegram]
    ADMIN_IDS=123456789,987654321
    ```
    *注意: `.env` 文件中的设置会覆盖 `config.ini` 中的设置。*

**如何获取您的 Telegram User ID:**
- 与 Telegram 上的 `@userinfobot` 机器人对话，它会告诉您您的 User ID。
- 当有用户尝试执行管理员命令但权限不足时，系统日志中也会记录该用户的 ID。

修改配置后，请重启应用程序使管理员设置生效。

---

如果您在使用过程中遇到任何问题或有任何建议，欢迎提出！
    """
    return help_text.strip()


def format_dialogs_list(
    dialogs_info: List[Tuple[str, int, str]],
    current_page: int,
    total_pages: int,
    items_per_page: int = 10  # Default items per page for dialogs
) -> Tuple[str, Optional[List[List[Button]]]]:
    """
    格式化对话列表为用户友好的文本，并支持分页。
    
    将从 UserBotClient 获取的对话信息格式化为用户友好的文本，
    包括对话名称、ID和类型，并生成分页按钮。
    
    Args:
        dialogs_info: 包含 (dialog_name, dialog_id, dialog_type) 元组的完整列表
        current_page: 当前页码，从 1 开始
        total_pages: 总页数
        items_per_page: 每页显示的对话数量
        
    Returns:
        Tuple[str, Optional[List[List[Button]]]]:
            - 格式化后的消息文本
            - 分页按钮列表（如果有分页）或 None（如果没有分页）
    """
    if not dialogs_info:
        return "📭 **对话列表为空**\n\n当前账户下没有找到任何对话。", None
    
    total_dialogs = len(dialogs_info)
    
    # 构建消息头部
    message_parts = [
        f"💬 **对话列表** (共 **{total_dialogs}** 个对话)\n",
        f"📄 第 **{current_page}/{total_pages}** 页\n\n"
    ]
    
    # 计算当前页的对话范围
    start_index = (current_page - 1) * items_per_page
    end_index = start_index + items_per_page
    current_page_dialogs = dialogs_info[start_index:end_index]
    
    # 遍历当前页的对话列表，格式化每个对话
    for local_index, (dialog_name, dialog_id, dialog_type) in enumerate(current_page_dialogs, 1):
        global_index = start_index + local_index # 全局索引
        # 安全处理对话名称，避免Markdown冲突
        safe_dialog_name = dialog_name or "未知对话"
        
        # 清理对话名称中的Markdown标记
        for pattern, replacement in MARKDOWN_PATTERNS:
            safe_dialog_name = re.sub(pattern, replacement, safe_dialog_name)
        
        # 截取过长的对话名称
        if len(safe_dialog_name) > 35: # Adjusted length to make space for type and index
            safe_dialog_name = safe_dialog_name[:32] + "..."
        
        # 格式化对话类型，使其更易读
        type_emoji_map = {
            "user": "👤",
            "group": "👥",
            "channel": "📢",
            "unknown": "❓"
        }
        type_display = f"{type_emoji_map.get(dialog_type, '❓')} {dialog_type.capitalize()}"

        # 格式化单个对话条目
        message_parts.append(
            f"{global_index}. **{safe_dialog_name}** ({type_display})\n"
            f"   ID: `{dialog_id}`\n\n"
        )
        
    # 构建分页按钮 (如果需要)
    buttons = None
    if total_pages > 1:
        buttons_row = []
        
        # 首页和上一页按钮
        if current_page > 1:
            buttons_row.append(Button.inline("⏮ 首页", f"dialog_page:1"))
            buttons_row.append(Button.inline("◀️ 上一页", f"dialog_page:{current_page - 1}"))
        
        # 当前页/总页数按钮 (不可点击)
        buttons_row.append(Button.inline(f"📄 {current_page}/{total_pages}", "noop_dialog_page")) # Use a specific noop
        
        # 下一页和末页按钮
        if current_page < total_pages:
            buttons_row.append(Button.inline("▶️ 下一页", f"dialog_page:{current_page + 1}"))
            buttons_row.append(Button.inline("⏭ 末页", f"dialog_page:{total_pages}"))
            
        buttons = [buttons_row]

        # 如果按钮超过5个，拆分为两行 (类似搜索结果)
        if len(buttons_row) > 5:
            nav_buttons = buttons_row[:2] + buttons_row[3:]  # 导航按钮
            page_button = [buttons_row[2]]  # 页码按钮
            buttons = [nav_buttons, page_button]
            
    # 添加说明信息 (如果是在最后一页或者总页数不多时显示，避免重复)
    if current_page == total_pages or total_pages <=1 :
        message_parts.append(
            "💡 **说明:**\n"
            "- 对话ID可用于白名单管理命令\n"
            "- 使用 `/add_whitelist <对话ID>` 添加到白名单\n"
            "- 使用 `/remove_whitelist <对话ID>` 从白名单移除"
        )
    
    # 合并所有消息部分
    formatted_message = ''.join(message_parts)
    
    logger.debug(f"已格式化对话列表第 {current_page}/{total_pages} 页，包含 {len(current_page_dialogs)} 个对话")
    return formatted_message, buttons