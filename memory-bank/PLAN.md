# 项目执行计划：Telegram 中文历史消息便捷搜索 (AI 执行版)

## 1. 项目目标与AI执行原则

本文档基于 `FOLLOWME.md` 的项目规划，旨在为 AI 提供一个清晰、可执行的开发路线图，以完成 Telegram 中文历史消息便捷搜索工具的开发。

**核心原则：**

*   **AI 主导开发：** AI 将负责整个项目的开发生命周期，包括代码编写、测试、环境配置、命令执行等。
*   **遵循计划：** AI 需严格按照本计划中定义的阶段和步骤执行。
*   **自主决策与执行：** 在遵循计划的前提下，AI 被授权在技术细节上做出合理决策，并自主执行必要的开发命令（如 `git commit`, `docker build`, `npm install`, `pip install` 等）。
*   **详细记录：** AI 在执行每个主要步骤或遇到问题时，应在 `memory-bank/activeContext.md` 中记录其思考过程、执行的命令、遇到的问题及解决方案。
*   **用户确认节点：** 在每个主要阶段（如后端 MVP 完成、前端 MVP 完成）完成后，AI 应通过 `ask_followup_question` 请求用户确认，然后再进入下一阶段。

## 2. 开发阶段与任务分解

项目将按照以下顺序进行，每个阶段都包含开发和测试：

### 阶段 0: 项目初始化与环境准备 (AI 执行)

1.  **任务：** 初始化项目结构。
    *   **AI 行动：**
        *   根据 `FOLLOWME.md` 中定义的后端和前端目录结构，创建项目骨架。
        *   初始化 Git 仓库。
        *   创建基础的 `README.md` (可从 `FOLLOWME.md` 提取项目愿景和目标)。
        *   创建 `.gitignore` 文件，包含 Python, Node.js, Meilisearch 和常见 IDE 的忽略规则。
        *   创建 `memory-bank/activeContext.md` 并记录初始化过程。
2.  **任务：** 搭建本地开发环境。
    *   **AI 行动：**
        *   **Meilisearch:**
            *   提供 `docker-compose.yml` 配置，用于启动 Meilisearch 服务。
            *   确保 Meilisearch 服务可以通过 `http://localhost:7700` 访问，并设置一个安全的 `MASTER_KEY` (AI 生成并记录在 `.env` 中)。
        *   **Python (后端):**
            *   创建并激活 Python 虚拟环境 (如 `venv`)。
            *   根据 `FOLLOWME.md` 技术选型，在 `requirements.txt` 中列出核心依赖 (Telethon (用于 Userbot 和 Search Bot), meilisearch-python, FastAPI, python-dotenv, Pydantic, uvicorn)。
            *   执行 `pip install -r requirements.txt`。
            *   Python 版本将通过项目根目录下的 pyproject.toml 文件中的 `requires-python` 字段（例如 `requires-python = ">=3.9"`）进行约束，并由 `uv` 在创建虚拟环境时遵循此设置。
        *   **Node.js (前端 - 预备):**
            *   (此阶段仅做环境检查，实际安装在前端阶段进行) 检查 Node.js 和 npm/yarn 是否已安装。
        *   创建 `.env.example` 文件，列出所有需要的环境变量（如 `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `BOT_TOKEN`, `MEILISEARCH_HOST`, `MEILISEARCH_API_KEY` 等）。
        *   创建 `.env` 文件，并由 AI 填充占位符值（对于敏感信息，AI 可以生成安全的随机值或提示用户后续手动填写）。
        *   记录所有环境搭建步骤和命令到 `memory-bank/activeContext.md`。

### 阶段 1: 后端核心功能开发与测试 (AI 执行)

此阶段目标是完成 MVP 的后端部分，即 Userbot 缓存消息和 Search Bot 通过 Meilisearch 搜索消息。

1.  **任务：** `core/config_manager.py` 开发。
    *   **AI 行动：**
        *   实现加载 `.env` 和 `config.ini` (如果选择使用) 的功能。
        *   提供获取配置项的方法。
        *   实现白名单的读取、添加、移除逻辑 (初期可基于 JSON 文件或 Python 列表存储在配置文件中)。
        *   实现最旧同步时间（`oldest_sync_timestamp`）的读取和管理逻辑。该配置可以全局生效，或针对特定 chat_id 生效，存储于 `whitelist.json`。
        *   编写单元测试。
        *   记录到 `memory-bank/activeContext.md`。
2.  **任务：** `core/models.py` 开发。
    *   **AI 行动：**
        *   定义 `MeiliMessageDoc` Pydantic 模型，参照 `FOLLOWME.md` 4.1.3 节。
        *   编写单元测试。
        *   记录到 `memory-bank/activeContext.md`。
3.  **任务：** `core/meilisearch_service.py` 开发。
    *   **AI 行动：**
        *   实现初始化 Meilisearch 客户端。
        *   实现 `ensure_index_setup()`，包括索引创建和配置 (参照 `FOLLOWME.md` 4.2 节)。
        *   实现 `index_message()` 和 `index_messages_bulk()`。
        *   实现 `search()` 方法。
        *   编写集成测试 (需要本地 Meilisearch 服务运行)。
        *   记录到 `memory-bank/activeContext.md`。
4.  **任务：** `user_bot/client.py` 开发。
    *   **AI 行动：**
        *   初始化 `TelegramClient`。
        *   处理登录和会话管理。
        *   记录到 `memory-bank/activeContext.md`。
5.  **任务：** `user_bot/event_handlers.py` 开发。
    *   **AI 行动：**
        *   实现 `on_new_message` 处理函数，检查白名单，提取消息，调用 `MeilisearchService.index_message()`。
        *   (可选) 实现 `on_message_edited`。
        *   记录到 `memory-bank/activeContext.md`。
6.  **任务：** `user_bot/history_syncer.py` 开发。
    *   **AI 行动：**
        *   实现 `sync_chat_history()`。在同步时，从 `ConfigManager` 获取对应聊天的最旧同步时间，如果消息的 `date` 早于此时间戳，则停止同步该聊天更早的消息。
        *   实现 `initial_sync_all_whitelisted_chats()`。同样应用最旧同步时间的检查逻辑。
        *   记录到 `memory-bank/activeContext.md`。
7.  **任务：** `user_bot/utils.py` 开发。
    *   **AI 行动：**
        *   实现 `generate_message_link()`。
        *   记录到 `memory-bank/activeContext.md`。
8.  **任务：** `search_bot/message_formatters.py` 开发。
    *   **AI 行动：**
        *   实现 `format_search_results()`，处理来自 Meilisearch 的结果，并准备发送给用户的消息格式。其输入可能需要根据 Telethon 的消息对象特性进行调整（例如，如何构建回复）。
        *   编写单元测试。
        *   记录到 `memory-bank/activeContext.md`。
9.  **任务：** `search_bot/command_handlers.py` 开发。
    *   **AI 行动：**
        *   使用 Telethon 的事件处理器 (如 `@client.on(events.NewMessage(pattern='/start'))` 或使用 `add_event_handler`) 来处理 `/start`, `/help`, `/search` 等命令。
        *   `/search` 命令的处理逻辑应调用 `MeilisearchService.search()` 并使用 `message_formatters.format_search_results()` 格式化结果。
        *   白名单管理命令也应通过 Telethon 事件处理。
        *   记录到 `memory-bank/activeContext.md`。
10. **任务：** `search_bot/callback_query_handlers.py` 开发。
    *   **AI 行动：**
        *   使用 Telethon 的 `events.CallbackQuery` 事件处理器来处理 Inline Button 的回调，例如用于搜索结果的分页。
        *   记录到 `memory-bank/activeContext.md`。
11. **任务：** `search_bot/bot.py` 开发。
    *   **AI 行动：**
        *   初始化 `TelegramClient` (Telethon) 并使用 Bot Token 进行认证 (与 Userbot 的 `TelegramClient` 实例分开，或者根据设计决策共用但需清晰区分)。
        *   注册通过 `command_handlers.py` 和 `callback_query_handlers.py` 中定义的事件处理器。
        *   启动客户端 (例如 `client.run_until_disconnected()`)。
        *   记录到 `memory-bank/activeContext.md`。
12. **任务：** `main.py` (后端主入口) 开发。
    *   **AI 行动：**
        *   实现启动 Userbot (Telethon, 使用用户凭据) 和 Search Bot (Telethon, 使用 Bot Token) 的逻辑。这可能涉及异步运行两个独立的 Telethon客户端。
        *   确保可以从命令行运行，并能正确管理两个客户端的生命周期。
        *   记录到 `memory-bank/activeContext.md`。
13. **任务：** 后端 MVP 集成测试与调试。
    *   **AI 行动：**
        *   手动或通过脚本模拟 Userbot 接收消息并索引到 Meilisearch。
        *   通过 Search Bot 发送搜索指令，验证搜索结果和格式化。
        *   测试白名单功能。
        *   测试历史消息同步功能。
        *   修复发现的 BUG。
        *   记录测试过程和结果到 `memory-bank/activeContext.md`。
14. **任务：** 请求用户确认后端 MVP。
    *   **AI 行动：**
        *   总结后端 MVP 完成情况。
        *   使用 `ask_followup_question` 工具，向用户提问：“后端核心功能（Userbot 缓存、Search Bot 搜索）已开发完成并初步测试。是否可以继续进行前端开发阶段？”
            *   建议1: "是的，后端MVP符合预期，请继续前端开发。"
            *   建议2: "后端功能需要调整，请描述需要修改的部分。"
        *   记录到 `memory-bank/activeContext.md`。

### 阶段 2: 前端核心功能开发与测试 (AI 执行, 针对 Mini App/Web 界面)

此阶段目标是完成 MVP 的前端部分，即一个简单的搜索界面。

1.  **任务：** 前端项目初始化。
    *   **AI 行动：**
        *   在 `frontend/` 目录下，使用 `create-react-app` (或 Vite) 初始化 React 项目。
        *   安装基础依赖：React, ReactDOM, `@tma.js/sdk` (或 `telegram-web-app.js`), Zustand (或 Redux Toolkit), Tailwind CSS (或选定的UI库)。
        *   配置 ESLint, Prettier。
        *   创建 `frontend/.env.example` 和 `frontend/.env` (例如 `REACT_APP_API_BASE_URL`)。
        *   记录到 `memory-bank/activeContext.md`。
2.  **任务：** API 服务 (`api/`) 开发 (FastAPI)。
    *   **AI 行动：**
        *   在后端项目中创建 `api/` 模块。
        *   实现 `main.py` 作为 FastAPI 入口。
        *   创建 `routers/search.py`，实现 `/api/v1/search` POST 端点 (参照 `FOLLOWME.md` 4.4 节)。此 API 应调用 `core.meilisearch_service.search()`。
        *   (可选) 实现简单的管理 API 用于白名单等。
        *   配置 CORS，允许前端访问。
        *   编写 API 测试 (使用 `httpx` 和 `pytest`)。
        *   更新后端 `main.py` 以包含 FastAPI 应用的启动 (例如使用 Uvicorn)。
        *   记录到 `memory-bank/activeContext.md`。
3.  **任务：** 前端核心组件开发。
    *   **AI 行动：**
        *   `src/services/api.js` (或 `.ts`): 封装调用后端 `/api/v1/search` 的函数。
        *   `src/components/SearchBar.jsx`: 搜索输入框和提交按钮。
        *   `src/components/ResultsList.jsx`: 展示搜索结果列表。
        *   `src/components/ResultItem.jsx`: 单条搜索结果的展示。
        *   `src/pages/SearchPage.jsx`: 组合搜索栏和结果列表的主页面。
        *   `src/App.jsx`: 设置基本路由和布局。
        *   使用 Zustand (或 Redux) 管理搜索状态 (查询词、结果、加载状态、错误信息)。
        *   记录到 `memory-bank/activeContext.md`。
16. **任务：(已完成) 前端界面重构与组件化 (截至 2025-05-25)**
    *   **AI 行动（回顾性记录）：**
        *   **`1c11f68`: feat: 实现底部导航栏和设置界面**
            *   添加 BottomNavBar 组件，用于在搜索、群组和设置页面之间导航。
            *   创建 GroupsPage 组件，作为未来群组功能的占位符。
            *   开发了 SettingsPage 组件，并采用卡片式布局，用于各种设置选项。
            *   引入了 Zustand 存储，用于管理导航和设置状态。
            *   实现 SettingsCard 和 SettingsItems 组件，用于结构化设置显示。
            *   增强了界面，支持 Telegram 主题，以实现一致的样式。
            *   添加了主题选择、同步频率和缓存管理功能。
        *   **`eeb0961`: feat: 重构应用界面，实施阶段3设计方案**
            *   更新 App.css，添加新的样式规则以支持卡片式设计和现代化布局。
            *   修改 App.jsx，重构应用结构，优化页面标题获取逻辑。
            *   更新 index.css，定义全局样式和色板，支持深色模式。
            *   改进 FilterControls 组件，增强用户交互体验，添加新的卡片式设计。
            *   重构 ResultItem 和 ResultsList 组件，优化搜索结果展示。
            *   更新 SearchBar 组件，实施新的视觉风格和交互反馈。
            *   改进 BottomNavBar 组件，采用现代化导航设计，提升用户体验。
        *   **`6b53e38`: feat: 更新样式和组件，增强搜索和结果展示功能**
            *   在 App.css 中添加响应式设计，优化不同屏幕尺寸下的布局。
            *   更新 SearchBar 组件，添加键盘事件处理以支持回车搜索。
            *   修改 ResultsList 组件，确保分页按钮文本的可读性。
            *   引入紧凑型搜索按钮样式，提升用户交互体验。
        *   **`dfadaa0`: feat: 更新用户信息显示和样式，优化界面布局**
            *   修改 App.css，重命名用户信息区域样式并调整样式规则，增强视觉效果。
            *   更新 App.jsx，移除头部导航栏，添加用户信息横幅，提升用户体验。
            *   调整响应式设计，确保在不同屏幕尺寸下的布局一致性。
        *   **`fdaad94`: 优化底部导航栏样式，添加悬浮动画效果**
            *   修改 App.css，调整底部导航栏的高度、边距和样式，提升视觉效果。
            *   添加悬浮动画效果，增强用户交互体验。
            *   更新导航项的样式，确保在不同状态下的视觉一致性。
        *   记录到 `memory-bank/activeContext.md` (回顾性条目)。
4.  **任务：** 前端与 TMA SDK 集成。
    *   **AI 行动：**
        *   初始化 TMA SDK。
        *   利用 SDK 获取用户信息、主题颜色等，并适配前端 UI。
        *   实现通过 TMA SDK 的 `MainButton` 触发搜索或特定操作。
        *   记录到 `memory-bank/activeContext.md`。
5.  **任务：** 前端 MVP 测试与调试。
    *   **AI 行动：**
        *   在浏览器中运行前端应用。
        *   测试搜索功能，确保能正确调用后端 API 并展示结果。
        *   测试分页、错误处理。
        *   在 Telegram Mini App 环境中测试 (如果可能，或模拟其行为)。
        *   修复 BUG。
        *   记录测试过程和结果到 `memory-bank/activeContext.md`。
6.  **任务：** 请求用户确认前端 MVP。
    *   **AI 行动：**
        *   总结前端 MVP 完成情况。
        *   使用 `ask_followup_question` 工具，向用户提问：“前端搜索界面（Mini App/Web）核心功能已开发完成并初步测试。是否可以继续进行前后端协同开发和部署准备阶段？”
            *   建议1: "是的，前端MVP符合预期，请继续。"
            *   建议2: "前端功能需要调整，请描述需要修改的部分。"
        *   记录到 `memory-bank/activeContext.md`。

### 阶段 3: 前后端协同开发、优化与部署准备 (AI 执行)

1.  **任务：** 完善后端功能 (基于 `FOLLOWME.md` 次要功能)。
    *   **AI 行动：**
        *   实现按消息来源类别筛选 (更新 `MeilisearchService` 和 Bot 命令/API)。
        *   实现按时间段搜索 (更新 `MeilisearchService` 和 Bot 命令/API)。
        *   更新 Bot 命令和交互以支持新筛选。
        *   更新 API 以支持前端的新筛选条件。
        *   编写相应测试。
        *   记录到 `memory-bank/activeContext.md`。
2.  **任务：** 完善前端功能 (基于 `FOLLOWME.md` 次要功能)。
    *   **AI 行动：**
        *   在前端界面添加按来源和时间筛选的 UI 控件。
        *   更新前端 API 调用以包含新的筛选参数。
        *   测试前端筛选功能。
        *   记录到 `memory-bank/activeContext.md`。
3.  **任务：** 性能优化。
    *   **AI 行动：**
        *   评估 Userbot 缓存效率和 Search Bot/API 搜索速度。
        *   根据需要优化 Meilisearch 索引配置或查询。
        *   优化代码逻辑。
        *   记录到 `memory-bank/activeContext.md`。
4.  **任务：** 编写 `Dockerfile` 和 `docker-compose.yml`。
    *   **AI 行动：**
        *   为后端 Python 应用创建 `Dockerfile`。
        *   更新 `docker-compose.yml` 以包含后端应用服务和 Meilisearch 服务，并配置好网络、卷和环境变量。
        *   (可选) 为前端应用创建 `Dockerfile` (用于 Nginx 托管静态文件) 或准备静态文件构建命令。
        *   测试 Docker 构建和运行。
        *   记录到 `memory-bank/activeContext.md`。
5.  **任务：** 编写基础使用文档 (`README.md` 完善)。
    *   **AI 行动：**
        *   更新 `README.md`，包括：
            *   项目描述。
            *   功能列表。
            *   本地开发环境搭建步骤 (包括 Docker)。
            *   如何运行项目。
            *   环境变量说明。
            *   Bot 命令列表。
        *   记录到 `memory-bank/activeContext.md`。
6.  **任务：** 请求用户确认部署准备。
    *   **AI 行动：**
        *   总结协同开发、优化和部署准备情况。
        *   使用 `ask_followup_question` 工具，向用户提问：“项目功能已根据计划完善，Docker 配置和基础文档已准备就绪。是否可以进行最终测试和模拟部署？”
            *   建议1: "是的，准备充分，请进行最终测试和模拟部署。"
            *   建议2: "在部署前还有些调整，请描述。"
        *   记录到 `memory-bank/activeContext.md`。

### 阶段 4: 最终测试、模拟部署与总结 (AI 执行)

1.  **任务：** 端到端测试。
    *   **AI 行动：**
        *   使用 `docker-compose up` 完整启动本地环境。
        *   Userbot: 确保能连接 Telegram，监听白名单群组，并将消息存入 Meilisearch。
        *   Search Bot: 测试所有命令，特别是搜索、筛选、分页。
        *   Mini App/Web: 测试搜索、筛选、分页，确保与后端 API 交互正常。
        *   记录详细的 E2E 测试场景和结果到 `memory-bank/activeContext.md`。
2.  **任务：** (模拟) 部署。
    *   **AI 行动：**
        *   描述一个典型的部署流程（例如，到一台云服务器）。
        *   提供 `systemd` 服务文件示例 (如果不用 Docker 纯跑 Python)。
        *   提供 Nginx 配置示例 (如果用 Nginx 反代 FastAPI 和托管前端)。
        *   强调生产环境所需的安全措施 (如 Meilisearch master key, HTTPS)。
        *   记录到 `memory-bank/activeContext.md`。
3.  **任务：** 项目总结与未来展望。
    *   **AI 行动：**
        *   总结整个开发过程，已实现的功能，遇到的主要挑战及解决方案。
        *   基于 `FOLLOWME.md` 的 V2, V3+ 功能，提出下一步的开发建议。
        *   清理 `memory-bank/activeContext.md` 或将其归档，并更新主要的 Memory Bank 文件（如 `progress.md`, `decisionLog.md`）。
        *   记录到 `memory-bank/activeContext.md` (最后一次)。

## 3. AI 建议与注意事项

*   **版本控制：** AI 应在每个小功能或修复完成后，执行 `git add .` 和 `git commit -m "Descriptive message"`。在大的阶段性提交前，可以考虑创建特性分支。
*   **错误处理与日志：** 所有模块都应有健壮的错误处理和详细的日志记录 (使用 Python `logging` 模块)。
*   **代码质量：** AI 应尽量遵循 PEP 8 (Python) 和前端社区的最佳实践。使用 Black, Flake8/Pylint, ESLint, Prettier 进行代码格式化和检查。
*   **安全：** 务必将 API Keys, Tokens 等敏感信息存储在 `.env` 文件中，并确保 `.env` 文件在 `.gitignore` 中。Meilisearch 的 Master Key 必须设置且保密。
*   **Telethon 登录：** Userbot 首次运行时需要交互式登录 Telegram。AI 需要能处理这种情况，或者指导用户如何预先生成 session 文件。对于全自动执行，AI 可能需要用户预先提供 `*.session` 文件或通过环境变量传入登录凭据（如果 Telethon 支持非交互式登录）。**这是一个关键点，AI 需要明确如何处理 Userbot 的授权。**
*   **Telegram Bot Token：** 需要用户通过 BotFather 创建 Bot 并提供 Token。
*   **Meilisearch 中文优化：** 确保在 `ensure_index_setup` 时，考虑到中文分词和搜索的特性，可能需要查阅 Meilisearch 关于中文支持的最新文档进行配置。
*   **异步处理：** Python 后端（Telethon, FastAPI）大量使用异步编程，AI 需熟练运用 `async/await`。

## 4. AI 执行流程的启动

NexusCore 将根据此 `PLAN.md`，逐步创建 `new_task` 给相应的 AI 模式（主要是 💻 Code 模式），并传递必要的上下文和当前阶段的任务指令。AI 在执行每个任务时，应参考本计划的相应部分，并在 `memory-bank/activeContext.md` 中记录其工作。

---

**AI 请从 “阶段 0: 项目初始化与环境准备” 的第一个任务开始执行。**
## [2025-06-02] 后续开发建议 (来自 activeContext.md 会话功能开发总结)

**源自 `activeContext.md` (行 254-258):**

1.  **生产环境配置**:
    *   在生产环境中配置UserBot自动登录。
2.  **会话功能增强**:
    *   考虑添加会话搜索和筛选功能。
    *   可以添加批量操作功能（例如批量添加到白名单、批量已读等）。
    *   考虑添加会话详情页面，展示更丰富的会话信息或相关操作。
3.  **性能与缓存优化**:
    *   可以进一步优化头像缓存策略（例如使用IndexedDB本地缓存，提供更持久的离线支持）。