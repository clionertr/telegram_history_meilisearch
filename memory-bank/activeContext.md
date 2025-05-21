# Search Bot 优化：实现无命令前缀搜索

## 任务目标

修改 Search Bot，使其能够直接处理用户发送的文本消息作为搜索关键词，而无需输入 `/search` 命令前缀。

## 步骤规划

1.  **分析现有代码结构**:
    *   ✅ 阅读 [`search_bot/bot.py`](search_bot/bot.py:0) (事件处理器注册)。
    *   ✅ 阅读 [`search_bot/command_handlers.py`](search_bot/command_handlers.py:0) (现有 `/search` 命令逻辑)。
    *   ✅ 阅读 [`search_bot/message_formatters.py`](search_bot/message_formatters.py:0) (结果格式化)。
2.  **提取核心搜索逻辑**:
    *   ✅ 在 `CommandHandlers` 中创建了新的私有方法 `_perform_search(self, event, query: str, is_direct_search: bool = False)` ([`search_bot/command_handlers.py:179`](search_bot/command_handlers.py:179))。
    *   ✅ 将核心搜索、格式化、回复逻辑移至 `_perform_search`。
    *   ✅ 修改了 `search_command` ([`search_bot/command_handlers.py:239`](search_bot/command_handlers.py:239)) 以调用 `_perform_search`。
3.  **实现新的事件处理器**:
    *   ✅ 在 `CommandHandlers.register_handlers` ([`search_bot/command_handlers.py:63`](search_bot/command_handlers.py:63)) 中添加了新的事件处理器 `handle_plain_text_message` ([`search_bot/command_handlers.py:277`](search_bot/command_handlers.py:277))。
    *   ✅ 使用了辅助函数 `_is_plain_text_and_not_command` ([`search_bot/command_handlers.py:248`](search_bot/command_handlers.py:248)) 来捕获不匹配其他命令的普通文本消息。
    *   ✅ 新处理器调用 `_perform_search` 方法。
    *   ✅ 注意了处理器的注册顺序和 `func` 参数的使用。
4.  **调用搜索并返回结果**: ✅ (由 `_perform_search` ([`search_bot/command_handlers.py:179`](search_bot/command_handlers.py:179)) 处理)。
5.  **避免处理非文本消息**: ✅ (通过 `_is_plain_text_and_not_command` ([`search_bot/command_handlers.py:248`](search_bot/command_handlers.py:248)) 中的检查 `event.message.text` 是否存在且不为空，并且不是空的或只有空格)。
6.  **（可选）用户提示**: ✅ (在 `_perform_search` ([`search_bot/command_handlers.py:179`](search_bot/command_handlers.py:179)) 中为 `is_direct_search` 预留了 TODO 注释)。
7.  **请求确认**: 即将进行。
8.  **提交结果**: 等待确认后。

## 详细步骤与思考

### 2025/5/21 下午2:44

#### 3. 实现新的事件处理器

成功在 `CommandHandlers.register_handlers` ([`search_bot/command_handlers.py:63`](search_bot/command_handlers.py:63)) 中添加了 `handle_plain_text_message` ([`search_bot/command_handlers.py:277`](search_bot/command_handlers.py:277)) 事件处理器和 `_is_plain_text_and_not_command` ([`search_bot/command_handlers.py:248`](search_bot/command_handlers.py:248)) 辅助函数。
该处理器应该能够正确处理普通文本消息作为搜索查询，同时不影响现有命令。

所有主要的编码任务已完成。

下一步：向用户请求确认任务完成情况。