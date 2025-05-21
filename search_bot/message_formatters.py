"""
消息格式化模块

此模块负责将从 Meilisearch 返回的原始搜索结果数据格式化为用户友好的文本，
准备在 Telegram Bot 中展示。还负责生成分页按钮等交互元素。
"""

import logging
import re
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
    # 验证结果数据的完整性
    if not results:
        return "😕 未找到匹配的消息。搜索结果为空。", None
    
    # 确保 hits 字段存在且不为空
    hits = results.get('hits', [])
    if not hits:
        return "😕 未找到匹配的消息。请尝试其他关键词或检查搜索语法。", None
    
    # 提取基本搜索信息，使用安全的 get 方法并提供默认值
    query = results.get('query', '未知查询')
    total_hits = results.get('estimatedTotalHits', len(hits))
    processing_time = results.get('processingTimeMs', 0)
    
    # 构建消息头部 (Markdown 格式)
    message_parts = [
        f"🔍 搜索结果: \"**{query}**\"\n",
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
        
        # 每个按钮存储数据格式：page_{页码}_{搜索查询}
        # 进一步限制查询参数长度，防止回调数据过大导致边界问题
        query_param = query[:20]  # 更严格地限制长度
        
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