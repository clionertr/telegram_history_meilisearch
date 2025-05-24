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
---

## 决策记录：实现 "最旧同步时间" 功能 (Oldest Sync Timestamp)

**日期:** 2025-05-24

**背景:**
用户请求添加一个功能，允许设置一个“最旧同步时间”，早于该时间的消息将不被缓存，以提供更灵活的数据管理并减少存储需求。

**决策者:** NexusCore (任务分解与委派), 💻 Code (具体实现)

**决策/设计要点:**

1.  **配置存储 (`whitelist.json`):**
    *   在 `whitelist.json` 文件中引入一个新的顶层键 `sync_settings`。
    *   `sync_settings` 内部支持:
        *   `global_oldest_sync_timestamp`: 一个可选的全局设置，适用于所有未单独配置的聊天。
        *   按 `chat_id` (字符串键) 进行的特定聊天配置，每个聊天可拥有自己的 `oldest_sync_timestamp`。
    *   时间戳格式支持 ISO 8601 字符串和 Unix 时间戳整数，以提供灵活性。

2.  **配置管理 (`core/config_manager.py`):**
    *   `ConfigManager` 负责加载和解析 `sync_settings`。
    *   引入 `python-dateutil` 库来辅助解析 ISO 8601 格式的日期时间字符串，确保时间戳能被正确转换为 Python `datetime` 对象 (时区感知，UTC)。
    *   提供方法 `get_oldest_sync_timestamp(chat_id)`，该方法会优先返回特定于聊天的设置，如果不存在，则返回全局设置，如果两者都不存在，则返回 `None`。
    *   提供方法 `set_oldest_sync_timestamp(chat_id, timestamp)` 以便通过代码（例如API或Bot命令）更新这些设置。

3.  **同步逻辑 (`user_bot/history_syncer.py`):**
    *   `HistorySyncer` 在同步每个聊天的历史消息前，会从 `ConfigManager` 获取适用的 `oldest_sync_timestamp`。
    *   如果在遍历历史消息时，某条消息的日期早于（或等于，根据实现细节）获取到的 `oldest_sync_timestamp`，则停止对该聊天更早消息的同步。

4.  **用户接口:**
    *   **API 接口 (`api/routers/whitelist.py`):** 为管理员提供 RESTful API 端点，用于查看和修改全局及特定聊天的 `oldest_sync_timestamp` 设置。
    *   **Bot 命令 (`search_bot/command_handlers.py`):** 为管理员提供 Telegram Bot 命令 (`/set_oldest_sync_time`, `/view_oldest_sync_time`)，以方便直接通过聊天界面管理这些设置。

5.  **依赖管理:**
    *   将 `python-dateutil` 添加到 `requirements.txt`。

**理由:**
*   这种设计提供了足够的灵活性，允许用户根据需要进行全局或细粒度的控制。
*   将配置管理集中在 `ConfigManager` 中，保持了代码的模块化和可维护性。
*   提供 API 和 Bot 命令两种接口，满足了不同场景下的管理需求。
*   使用 `python-dateutil` 简化了日期时间字符串的解析工作。

**状态:** 已实施。

**关联 `activeContext.md` 记录:**
详细的实现过程记录在 `memory-bank/activeContext.md` 中（由 💻 Code 模式在 2025-05-24 左右记录的部分）。
---

## 决策记录：优化 `history_syncer.py` 避免 API 速率限制

**日期:** 2025-05-24

**背景:**
用户报告在 `user_bot/history_syncer.py` 的 `_build_message_doc` 方法中，由于频繁调用 `client.get_entity(sender_id)` ([`user_bot/history_syncer.py:382`](user_bot/history_syncer.py:382)) 获取发送者信息，导致了 Telegram API 的速率限制警告 ("A wait of X seconds is required (caused by GetUsersRequest)")。

**决策者:** NexusCore (任务分配), 💻 Code (具体实现)

**决策/设计要点:**

1.  **移除 `client.get_entity(sender_id)` 调用:**
    *   这是导致问题的直接原因，必须移除。

2.  **利用 `message.sender`:**
    *   Telethon 的 `Message` 对象通常会通过 `message.sender` 属性预加载发送者实体（如 `User` 或 `Chat` 对象）。优先使用此属性来获取发送者信息（如 `first_name`, `last_name`, `title`）。
    *   这种方法避免了额外的 API 调用，从而解决了速率限制问题。

3.  **增强日志记录与调试:**
    *   如果 `message.sender` 不可用或未能提供足够的发送者名称信息，记录一条 WARNING 级别的日志。
    *   该日志应包含 `sender_id`，以及 `message.sender` 和 `message.from_id` (如果存在) 的当前值，甚至可以考虑记录 `message.to_dict()` 的部分内容（如果适用且不过于冗长），以便用户协助分析 `message` 对象中实际包含的信息。

4.  **默认值与健壮性:**
    *   即使无法从 `message.sender` 或其他途径获取到发送者名称，程序也应继续正常处理该消息。
    *   在这种情况下，`sender_name` 可以被设置为一个默认值，例如 "未知发送者" 或 `None`，确保 `MeiliMessageDoc` 对象的构建不会失败。

**理由:**
*   **性能与稳定性:** 直接使用 `message` 对象中已有的数据是最优选择，可以显著减少 API 调用次数，避免速率限制，提高同步的稳定性和效率。
*   **问题可追溯性:** 详细的日志记录有助于在 `message.sender` 未按预期提供信息时，诊断问题原因或了解消息结构。
*   **用户体验:** 减少了不必要的警告刷屏。

**状态:** 已实施。

**关联 `activeContext.md` 记录:**
详细的分析、代码修改方案和验证过程记录在 [`memory-bank/activeContext.md`](memory-bank/activeContext.md) 中（由 💻 Code 模式在 2025-05-24 记录的部分，标题为 "2025-05-24: 修复 `history_syncer.py` 中的 `client.get_entity` 警告问题"）。
---
## 2025/5/24 (续)

*   **决策:** 修复 `/restart_userbot` 命令，确保其在重启 User Bot 后能重新加载所有配置文件。
    *   **理由:** 用户报告在通过 `/restart_userbot` 重启 User Bot 后，对 `whitelist.json`, `sync_points.json`, `config.ini` 等文件的修改未生效。原 `reload_config()` 方法仅重新加载了 `.env.userbot`。
    *   **影响与技术细节:**
        *   修改了 [`user_bot/client.py`](user_bot/client.py) 中的 `reload_config()` 方法。
        *   在该方法中，确保调用了 `self.config_manager.load_env()`, `self.config_manager.load_userbot_env()`, `self.config_manager.load_config()`, `self.config_manager.load_whitelist()` 和 `self.config_manager._load_search_bot_config()`。
        *   这样可以保证所有由 `ConfigManager` 管理的配置在 User Bot 重启时都能从文件系统中刷新。
    *   **状态:** 已实施。
---

## 决策记录：修复 `history_syncer.py` 中消息来源与发送者信息为空的问题

**日期:** 2025-05-24

**背景:**
用户报告在 `user_bot/history_syncer.py` 中，通过事件监听器获取到的新消息，其来源信息（如 `chat_id`, `chat_title`）和发送者信息（`sender_id`, `sender_name`）存在为空或不完整的情况。此问题影响了消息在 Meilisearch 中的正确索引和后续的搜索展示。

**决策者:** NexusCore (任务委派), 💻 Code (具体实现)

**决策/设计要点 (由 💻 Code 模式实施):**

1.  **改进 `sender_id` 获取逻辑:**
    *   在 [`user_bot/history_syncer.py`](user_bot/history_syncer.py) 的 `_build_message_doc` 方法中，实现了更健壮的 `sender_id` 获取策略。
    *   优先尝试 `message.sender_id`。
    *   如果 `message.sender_id` 不可用或为0，则尝试从 `message.from_id` 获取。`message.from_id` 是一个 `Peer` 对象，需要从中提取用户ID、频道ID或聊天ID。
        *   如果是 `PeerUser`, 使用 `message.from_id.user_id`。
        *   如果是 `PeerChat`, 使用 `message.from_id.chat_id`。
        *   如果是 `PeerChannel`, 使用 `message.from_id.channel_id`。
    *   作为最后的备选，如果 `message.sender` 对象存在且有 `id` 属性，则使用 `message.sender.id`。
    *   确保即使部分属性不可用，也能尽可能获取到有效的发送者ID，默认为0。

2.  **增强 `sender_name` 获取逻辑:**
    *   继续优先尝试从 `message.sender` 对象获取发送者名称。
    *   针对不同类型的 `message.sender` (User, Chat, Channel) 使用合适的属性：
        *   对于 `User` 类型: 优先使用 `format_sender_name(sender.first_name, sender.last_name)`，如果结果为空，则尝试 `sender.username`。
        *   对于 `Chat` 或 `Channel` 类型: 使用 `sender.title`。
    *   如果 `message.sender` 不可用或未能提供名称，则 `sender_name` 保持为 "未知发送者" 或根据实际情况记录更具体的默认值。

3.  **来源信息 (Chat Info) 的稳定性:**
    *   对于 `chat_id`, `chat_title`, `chat_type`，这些信息是在 `sync_chat_history` 方法开始时通过 `client.get_entity(chat_id)` 获取并传入 `_build_message_doc` 的，这部分逻辑的稳定性较高，本次修复主要集中在发送者信息。

4.  **错误处理与日志记录:**
    *   在获取发送者信息的过程中，增加了更详细的 `DEBUG` 和 `WARNING` 级别的日志记录，方便追踪 `message` 对象在不同情况下的具体结构和信息获取路径。
    *   使用了安全的属性访问方式 (如 `getattr`)，以避免因预期属性不存在而引发的 `AttributeError`。

5.  **维持性能与API调用效率:**
    *   所有修复均在不重新引入对 `client.get_entity(sender_id)` 或类似高频API调用的前提下进行，以继续避免 Telegram API 的速率限制问题。

**理由:**
*   **准确性:** 提升了从原始 `Message` 对象中提取发送者ID和名称的准确性和覆盖面。
*   **健壮性:** 新的逻辑能更好地处理 `Message` 对象中部分信息缺失或结构变异的情况。
*   **可维护性:** 详细的日志有助于未来问题的诊断。
*   **性能:** 保持了原有的优化，避免了不必要的API调用。

**状态:** 已实施。

**关联 `activeContext.md` 记录:**
此 bug 修复任务由 💻 Code 模式直接完成，未被指示使用 `memory-bank/activeContext.md` 进行详细过程记录。修复的概要由 Code 模式在其 `attempt_completion` 结果中提供。