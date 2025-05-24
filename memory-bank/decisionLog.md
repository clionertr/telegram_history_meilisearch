# 项目决策日志

## 2025/5/19

*   **决策:** 项目初始化阶段，确定使用 `uv` 作为 Python 包管理和虚拟环境工具。
    *   **理由:** `uv` 提供了比传统 `pip` 和 `venv` 更快的性能和更一致的依赖解析。
    *   **影响:** 更新了 `PLAN.md` 和环境搭建步骤。

*   **决策:** Search Bot 将使用 Telethon 而不是 `python-telegram-bot`。
    *   **理由:** 用户明确指示，且与 User Bot 技术栈统一，便于代码复用和维护。
    *   **影响:** 大幅修改了 `PLAN.md` 中 Search Bot 相关模块的开发计划。

## 2025/5/20

*   **决策:** `ConfigManager` 将负责自动创建 `.example` 配置文件的副本（如 `config.ini`, `whitelist.json`）如果它们不存在。
    *   **理由:** 提升首次运行的便捷性，用户无需手动复制模板。
    *   **影响:** `core/config_manager.py` 实现中增加了文件创建逻辑。

*   **决策:** `MeiliSearchService` 中，索引的 `id` 字段将作为主键。
    *   **理由:** 解决 Meilisearch 在有多个 `id` 后缀字段时主键推断失败的问题。
    *   **影响:** `core/meilisearch_service.py` 的 `ensure_index_setup` 方法中显式设置了主键。

*   **决策:** 前端项目选用 Vite + React + Zustand + Tailwind CSS 技术栈。
    *   **理由:**
        *   Vite: 现代化的构建工具，提供极佳的开发体验。
        *   React: 成熟的 UI 库。
        *   Zustand: 轻量级、简洁的状态管理方案。
        *   Tailwind CSS: 原子化 CSS，便于快速构建界面。
        *   `@telegram-apps/sdk`: 官方推荐的 Telegram Mini App SDK。
    *   **影响:** `frontend/` 目录下的项目初始化和依赖安装。

*   **决策:** 后端 API (`/api/v1/search`) 将支持更丰富的查询参数，包括 `chat_id_filter`, `chat_type_filter`, `sender_id_filter`, `date_from`, `date_to`, `sort_by`, `offset`, `limit`。
    *   **理由:** 提供更灵活和强大的搜索能力给前端。
    *   **影响:** `api/routers/search.py` 和 `core/meilisearch_service.py` 的实现。

*   **决策:** 修复前端分页功能时，确定问题根源在后端 `MeiliSearchService` 未正确返回 `estimatedTotalHits`。
    *   **理由:** 通过在后端添加详细日志进行诊断。
    *   **影响:** 修改了 `core/meilisearch_service.py` 的 `search()` 方法。

*   **决策:** 前端与 TMA SDK 集成时，创建自定义 Hook `useTelegramSDK`。
    *   **理由:** 封装 SDK 逻辑，便于在多组件中使用，并处理非 TMA 环境下的优雅降级。
    *   **影响:** 创建了 `frontend/src/hooks/useTelegramSDK.js`。

*   **决策:** 历史消息同步功能增强，引入持久化同步点和增量更新。
    *   **理由:** 避免重复索引，提高同步效率，支持按时间范围同步。
    *   **影响:** 修改了 `core/config_manager.py` (添加 `SyncPointManager`) 和 `user_bot/history_syncer.py`。

## 2025/5/21

*   **决策:** User Bot 的配置（API ID/Hash）将存储在独立的 `.env.userbot` 文件中，并通过 Search Bot 的管理员命令进行管理。
    *   **理由:** 增强安全性，将用户凭据与 Bot 配置分离，方便动态更新。
    *   **影响:** 修改了 `core/config_manager.py`, `search_bot/command_handlers.py`, `main.py`。

*   **决策:** 实现 User Bot 的远程重启机制，通过 Search Bot 的 `/restart_userbot` 命令触发。
    *   **理由:** 方便在更新配置后应用更改，无需手动重启整个应用。
    *   **影响:** 修改了 `main.py` (使用 `asyncio.Event`), `user_bot/client.py`, `search_bot/command_handlers.py`。

*   **决策:** Search Bot 将支持无命令前缀的普通文本消息搜索。
    *   **理由:** 提升用户体验，使其更接近自然语言交互。
    *   **影响:** 修改了 `search_bot/command_handlers.py`，添加了新的事件处理器。

*   **决策:** 优化 Search Bot 搜索结果的 Markdown 展示。
    *   **理由:** 提升信息可读性和美观性。
    *   **影响:** 修改了 `search_bot/message_formatters.py`, `search_bot/command_handlers.py`, `search_bot/callback_query_handlers.py`。

## 2025/5/23

*   **决策:** 为实现 `/get_dialogs` 功能，Code Mode 主动将原计划的多个子任务合并执行。
    *   **理由:** Code Mode 判断这些子任务关联紧密，一次性完成效率更高，且能直接进行端到端验证。
    *   **影响:**
        *   在 `user_bot/client.py` 中添加了 `get_dialogs_info()` 方法及单元测试。
        *   在 `search_bot/command_handlers.py` 中添加了 `/get_dialogs` 命令处理器。
        *   在 `search_bot/message_formatters.py` 中添加了 `format_dialogs_list()` 格式化函数，并更新了 `/help` 信息。
    *   **结果:** 整个 `/get_dialogs` 功能（包括 User Bot 端能力、Search Bot 端命令、消息格式化和帮助文档更新）已由 Code Mode 一并完成。

## 2025/5/24

*   **决策:** 实现后端按消息来源类别和时间段筛选功能。
    *   **理由:** 遵循 `FOLLOWME.md` 和 `PLAN.md` 中定义的次要功能要求，提升搜索的灵活性和精确度。
    *   **影响与技术细节:**
        *   **[`search_bot/command_handlers.py`](search_bot/command_handlers.py:0):**
            *   `_parse_advanced_syntax()`: 修改为能解析多个 `type:类型` 参数，并将结果存为列表。
            *   `_build_meilisearch_filters()`: 修改为能处理 `chat_type` 为列表的情况，构建 `OR` 连接的 Meilisearch 筛选字符串。
            *   `_get_results_from_meili()` 和 `_perform_search()`: 确保正确提取和传递解析出的时间戳和聊天类型列表参数给 `MeiliSearchService`。
        *   **[`core/meilisearch_service.py`](core/meilisearch_service.py:0):** 确认其 `search()` 方法已具备接收 `chat_types` (列表), `start_timestamp`, `end_timestamp` 参数的能力。
        *   **[`api/routers/search.py`](api/routers/search.py:0):** 确认其 `/api/v1/search` 端点已支持通过请求体中的 `filters` 对象传递 `chat_type` (列表), `date_from`, `date_to`。
        *   **测试:** 为 `command_handlers.py` 中的筛选逻辑添加了新的单元测试 ([`tests/unit/test_command_handlers_filters.py`](tests/unit/test_command_handlers_filters.py:0))。

*   **决策:** 实现前端按消息来源类别和时间段筛选功能，并优化用户体验。
    *   **理由:** 遵循 `FOLLOWME.md` 和 `PLAN.md` 中定义的次要功能要求，使用户能够方便地使用后端新增的筛选能力。
    *   **影响与技术细节:**
        *   **新组件:** 创建了 [`frontend/src/components/FilterControls.jsx`](frontend/src/components/FilterControls.jsx:0) 用于封装筛选 UI 和逻辑。
        *   **UI 设计:** 采用可折叠面板，包含聊天类型复选框和日期选择器。
        *   **状态管理:** 利用现有的 Zustand store ([`frontend/src/store/searchStore.js`](frontend/src/store/searchStore.js:0)) 管理筛选条件。
        *   **数据处理:** 确保用户选择的日期被正确转换为 Unix 时间戳 (秒级) 后再传递给 API。
        *   **用户体验:**
            *   实现了筛选条件的自动应用，用户更改筛选选项即时触发搜索。
            *   为日期筛选设置了默认值 (例如，最近三个月到明天)。
        *   **关键词高亮修复:** 在 [`frontend/src/components/ResultItem.jsx`](frontend/src/components/ResultItem.jsx:0) 中使用 `dangerouslySetInnerHTML` 并添加自定义 CSS，以正确渲染和美化后端返回的 HTML 高亮标签。
        *   **集成:** 将 `FilterControls` 组件集成到主搜索页面 [`frontend/src/pages/SearchPage.jsx`](frontend/src/pages/SearchPage.jsx:0)。