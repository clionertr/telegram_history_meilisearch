## 项目计划：Telegram 中文历史消息便捷搜索

**项目愿景：** 打造一款高效、易用的 Telegram 中文历史消息搜索工具，解决原生搜索在中文语境下的不足，提升用户获取信息的效率。

## 1. 项目准备阶段

### 1.1 用户需求

用户希望能够让电报搜索中文历史消息更方便。

**功能分类：**

*   **核心功能 (MVP)**
    *   [已明确] 使用 Telethon 的 Userbot 缓存 Telegram 历史文本消息到 Meilisearch 数据库中。
    *   [已明确] 使用白名单（配置文件或数据库）控制需要缓存的群组/用户/频道。
    *   [已明确] 通过调用 Meilisearch API 进行高效、精准的中文消息搜索。
    *   [已明确] 用户通过 Telegram 机器人（BotFather 创建的 Bot）进行交互，发送搜索指令并接收结果。
*   **次要功能 (V2)**
    *   [已明确] 支持按消息来源类别（私聊、群组、频道）进行筛选搜索。
    *   [已明确] 支持按时间段（如：过去一天、一周、自定义起止日期）进行搜索。
    *   [已明确] 添加 Telegram Mini App (TMA) / 简单网页端作为备用或增强搜索界面。
    *   支持增量更新
    *   [已明确] 支持设置"最旧同步时间"，限制历史消息同步范围，避免缓存过于久远的消息
*   **未来功能 (V3+)**
    *   [已明确] MCP（模型上下文协议）集成，可能用于更智能的语义搜索或问答。
    *   支持图片、文件元数据（文件名）搜索（如果 Telethon 和 Meilisearch 支持良好）。
    *   用户自定义黑名单词汇，过滤搜索结果。
    *   定时任务：定期同步新增消息，而非仅实时。
    *   多账户 Userbot 支持。

### 1.2 目标定义

*   **MVP：** 完成核心功能，用户可以通过 Telegram Bot 搜索已缓存的白名单聊天中的文本消息。
    *   **核心指标：** 能够成功缓存至少一个群组的近期1000条消息，并通过机器人成功搜索到至少10条相关消息。首次搜索响应时间 < 5秒。

*   **里程碑规划**
    1.  **M1: 环境搭建与基础验证 (预计1周)**
        *   本地开发环境配置 (Python, Node.js, Meilisearch Docker)。
        *   Telethon Userbot 成功登录并能读取指定群组消息。
        *   Meilisearch 服务启动，能够通过 API 手动索引和搜索简单数据。
        *   Telegram Bot 创建，能响应简单命令（如 `/start`, `/help`）。
    2.  **M2: 核心缓存功能实现 (预计2周)**
        *   实现 Userbot 监听新消息并实时推送到 Meilisearch。
        *   实现 Userbot 批量拉取历史消息并推送到 Meilisearch。
        *   实现白名单机制（初期可基于配置文件）。
        *   设计 Meilisearch 索引结构（字段、可搜索属性、可排序属性等）。
    3.  **M3: 核心搜索功能实现 (预计1.5周)**
        *   实现 Telegram Bot 接收搜索关键词。
        *   实现 Bot 调用 Meilisearch API 进行搜索。
        *   格式化 Meilisearch 返回结果并在 Bot 中友好展示（包括消息原文、发送者、时间、原始消息链接）。
    4.  **M4: MVP 测试、优化与部署 (预计1.5周)**
        *   内部测试核心功能，修复 BUG。
        *   性能优化（缓存效率、搜索速度）。
        *   编写基础使用文档。
        *   MVP 版本部署（Userbot 和 Search Bot 可以部署在同一台服务器或 Docker 容器中）。
    5.  **M5: 次要功能 - 筛选与时间搜索 (预计2周)**
        *   实现按消息来源类别筛选。
        *   实现按时间段搜索。
        *   更新 Bot 命令和交互。
    6.  **M6: 次要功能 - Mini App/网页端 (预计3周)**
        *   设计 Mini App/网页端 UI/UX。
        *   开发前端界面 (React)。
            **近期具体成果 (截至 2025-05-25):**
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

        *   开发后端 API (FastAPI/Flask) 供前端调用。
        *   部署前端和后端 API。
    7.  **M7: 未来功能探索与迭代 (持续)**
        *   根据用户反馈和技术发展，逐步实现未来功能。

## 2. 技术选型

### 2.1 前端框架 (Mini App/网页端)

*   **React:** (已选定) 成熟生态，组件化开发。
*   **备选:** Vue.js (如果团队或AI更熟悉)。
*   **UI库:** Tailwind CSS (实用优先) 或 Material-UI/Ant Design (快速搭建美观界面)。
*   **状态管理:** Zustand (轻量) 或 Redux Toolkit (中大型应用)。
*   **TMA SDK:** 使用 Telegram 官方提供的 Mini Apps SDK (`@tma.js/sdk` 或 `telegram-web-app.js`).

### 2.2 后端框架选择

*   **语言:** Python (已选定)
*   **核心库:**
    *   **Telethon:** 与 Telegram User API 和 Bot API 交互 (用于 Userbot 和 Search Bot)。
    *   **Meilisearch-Python:** Meilisearch 官方 Python客户端。
    *   **FastAPI:** (推荐，用于API服务) 高性能，易于学习，自带数据校验和 OpenAPI 文档生成。如果只是 Bot，可以不单独引入 Web 框架，但若有 Mini App 则必须。
*   **配置管理:** `python-dotenv` (管理 `.env` 文件), `Pydantic` (用于 FastAPI 和配置模型)。

#### Python 版本管理
项目推荐使用 `uv` 进行虚拟环境和包管理。Python 的版本约束通过项目根目录下的 [`pyproject.toml`](pyproject.toml:0) 文件中的 `[project.requires-python]` 字段进行定义 (例如, `requires-python = ">=3.9"`). `uv` 在创建虚拟环境时会遵循此设置。

### 2.3 数据库选择

*   **Meilisearch:** (已选定) 作为核心搜索引擎和消息缓存库。
*   **(可选) SQLite/TinyDB:** 用于存储 Userbot 配置（如白名单 Chat ID、上次同步时间戳等），轻量级，无需额外服务。或者直接用 JSON 文件配置。

## 3. 架构设计

### 3.1 整体架构图

```mermaid
graph TD
    subgraph "用户交互层"
        User[Telegram User]
        WebApp[Mini App / Web Browser]
    end

    subgraph "服务层"
        TG_Bot[TelegramBot(python-telegram-bot)]
        User_Bot[Telethon Userbot (Python)]
        API_Server[API Server (FastAPI, 可选)]
    end

    subgraph "数据存储与搜索层"
        Meili[Meilisearch]
        ConfigDB[(Optional) SQLite/JSON for Config]
    end

    subgraph "外部服务"
        TG_API[Telegram API]
    end

    User -- Search Commands --> TG_Bot
    User -- Interactions --> WebApp
    WebApp -- HTTP API Calls --> API_Server
    TG_Bot -- Search Queries --> Meili
    TG_Bot -- Control Commands (e.g., add to whitelist) --> User_Bot
    API_Server -- Search Queries --> Meili

    User_Bot -- Listen/Fetch Messages --> TG_API
    User_Bot -- Index Messages --> Meili
    User_Bot -- Read/Write Config --> ConfigDB

    style User_Bot fill:#f9d,stroke:#333,stroke-width:2px
    style TG_Bot fill:#ccf,stroke:#333,stroke-width:2px
    style Meili fill:#9cf,stroke:#333,stroke-width:2px
```

### 3.2 目录结构示例

#### 后端项目结构 (Python 应用示例 - 整合 Userbot 和 Searchbot)

```
project_root/
├── user_bot/                     # Telethon Userbot 相关代码
│   ├── __init__.py
│   ├── client.py                 # Telethon client 初始化和管理
│   ├── event_handlers.py         # 消息事件处理
│   ├── history_syncer.py         # 历史消息同步逻辑
│   └── utils.py                  # Userbot 工具函数
├── search_bot/                   # Telegram Bot (python-telegram-bot) 相关代码
│   ├── __init__.py
│   ├── bot.py                    # Bot 初始化和运行
│   ├── command_handlers.py       # 命令处理 (e.g., /search, /help)
│   ├── callback_query_handlers.py # 回调查询处理 (e.g., 翻页)
│   └── message_formatters.py     # 消息格式化
├── core/                         # 核心业务逻辑和共享服务
│   ├── __init__.py
│   ├── meilisearch_service.py    # Meilisearch 交互封装
│   ├── config_manager.py         # 配置管理 (白名单等)
│   └── models.py                 # 数据模型 (e.g., Pydantic 模型用于Meilisearch文档)
├── api/                          # (可选) FastAPI 应用，供 Mini App/Web 调用
│   ├── __init__.py
│   ├── main.py                   # FastAPI app 入口
│   ├── routers/                  # API 路由
│   │   └── search.py
│   └── dependencies.py           # FastAPI 依赖项
├── tests/                        # 测试文件
│   ├── unit/
│   └── integration/
├── .env.example                  # 环境变量模板
├── .env                          # 环境变量 (本地开发，不提交到git)
├── config.ini.example            # (可选) 配置文件模板
├── config.ini                    # (可选) 配置文件
├── requirements.txt              # Python 依赖
├── Dockerfile                    # Docker 配置文件
├── docker-compose.yml            # Docker Compose (用于本地开发 Meilisearch 和应用)
├── main.py                       # 主程序入口 (启动 Userbot 和 Searchbot)
└── README.md
```

#### 前端项目结构 (React 应用示例)
```
frontend/
├── public/               # 静态资源
│   ├── index.html
│   ├── favicon.ico
│   └── assets/
├── src/
│   ├── assets/           # 项目资源文件（图片、字体等）
│   ├── components/       # 可复用组件
│   │   ├── common/       # 通用组件
│   │   └── feature/      # 特定功能组件
│   ├── hooks/            # 自定义 React Hooks
│   ├── pages/            # 页面组件
│   ├── services/         # API 服务
│   ├── utils/            # 工具函数
│   ├── contexts/         # React Context
│   ├── styles/           # 全局样式
│   ├── App.jsx           # 应用根组件
│   └── index.jsx         # 入口文件
├── .env                  # 环境变量
├── .eslintrc.js          # ESLint 配置
├── .prettierrc           # Prettier 配置
├── package.json
└── README.md
```

### 3.3 模块拆分原则
- **单一职责原则**：每个模块、组件或函数只负责一个明确的功能
- **高内聚低耦合**：相关功能集中在一起，减少模块间依赖
- **关注点分离**：UI 展示、业务逻辑、数据处理应当分开
- **可测试性**：模块设计应便于单元测试

### 3.4 命名与代码风格规范
- **文件命名**：
  - 组件文件：PascalCase（如 `UserProfile.jsx`）
  - 工具/服务文件：camelCase（如 `apiService.js`）
  - 样式文件：与对应组件同名（如 `UserProfile.css`）
  
- **变量命名**：
  - 变量/函数：camelCase（如 `getUserData`）
  - 常量：UPPER_SNAKE_CASE（如 `MAX_RETRY_COUNT`）
  - 组件：PascalCase（如 `LoginForm`）
  
- **CSS 类名**：kebab-case（如 `user-profile-container`）或 BEM 命名法

#### 命名规范 (Python补充)
*   **模块名**：`lower_snake_case.py` (如 `meilisearch_service.py`)
*   **类名**：`PascalCase` (如 `MeilisearchService`)
*   **函数/方法名**：`lower_snake_case` (如 `search_messages`)
*   **变量名**：`lower_snake_case` (如 `user_data`)
*   **常量名**：`UPPER_SNAKE_CASE` (如 `MAX_RESULTS_PER_PAGE`)

#### 代码风格 (Python)
*   遵循 **PEP 8** 规范。
*   使用 **Black**进行代码格式化，**Flake8** 或 **Pylint** 进行代码检查。
*   添加类型提示 (Type Hinting)，并使用 **MyPy** 进行静态类型检查。

## 4. 详细设计

### 4.1 核心模块详细设计

#### 4.1.1 Userbot 模块 (`user_bot/`)
*   **`client.py`**:
    *   初始化 `TelegramClient` (Telethon)。
    *   处理登录、会话保存与加载。
    *   提供获取 `client` 实例的方法。
*   **`event_handlers.py`**:
    *   `on_new_message(event)`:
        *   检查消息来源是否在白名单中。
        *   提取消息内容 (文本、发送者、时间、chat_id, message_id)。
        *   调用 `MeilisearchService.index_message()`。
    *   `on_message_edited(event)`: (可选，考虑更新逻辑)
        *   类似新消息处理，但更新 Meilisearch 中的现有文档。
*   **`history_syncer.py`**:
    *   `sync_chat_history(chat_id, limit=None, offset_date=None)`:
        *   从指定 `chat_id` 拉取历史消息。
        *   分批处理，避免 API 限制和内存问题。
        *   对每条消息进行处理并调用 `MeilisearchService.index_messages_bulk()`。
        *   记录每个 chat 的最后同步点 (如 last_message_id 或 last_date)。
        *   检查消息日期是否早于最旧同步时间戳，如果是则停止向前同步，避免缓存过于久远的消息。
    *   `initial_sync_all_whitelisted_chats()`: 遍历白名单，对每个 chat 执行历史同步。
*   **`utils.py`**:
    *   `generate_message_link(chat_id, message_id)`: 生成 Telegram 消息的永久链接。

#### 4.1.2 Search Bot 模块 (`search_bot/`)
*   **`bot.py`**:
    *   初始化 `Application` (python-telegram-bot)。
    *   注册命令处理函数、回调查询处理函数。
    *   启动 Bot (polling 或 webhook)。
*   **`command_handlers.py`**:
    *   `start_command(update, context)`: 发送欢迎消息和使用说明。
    *   `help_command(update, context)`: 发送帮助信息。
    *   `search_command(update, context)`:
        *   获取用户输入的搜索关键词。
        *   (可选) 解析高级搜索语法，如 `type:group "关键词" date:2023-01-01_2023-12-31`。
        *   调用 `MeilisearchService.search()`。
        *   调用 `MessageFormatters.format_search_results()`。
        *   发送格式化后的结果给用户，支持分页 (使用 InlineKeyboard)。
    *   `add_whitelist_command(update, context)`: (管理员权限)
        *   获取 Chat ID，调用 `ConfigManager.add_to_whitelist()`。
        *   (可选) 提示 Userbot 重新加载配置或开始同步该新 Chat。
    *   `remove_whitelist_command(update, context)`: (管理员权限)
        *   获取 Chat ID，调用 `ConfigManager.remove_from_whitelist()`。
*   **`callback_query_handlers.py`**:
    *   处理搜索结果分页按钮的回调。
    *   重新执行搜索并获取指定页码的结果，编辑原消息。
*   **`message_formatters.py`**:
    *   `format_search_results(results, current_page, total_pages)`:
        *   将 Meilisearch 返回的原始数据格式化为用户友好的文本。
        *   每条结果包含：消息摘要、发送者、时间、[原始消息链接](t.me/c/chat_id/message_id)。
        *   生成分页按钮。

#### 4.1.3 Core 模块 (`core/`)
*   **`meilisearch_service.py`**:
    *   `__init__(host, api_key, index_name)`: 初始化 Meilisearch 客户端。
    *   `ensure_index_setup()`: 检查索引是否存在，如果不存在则创建，并配置索引设置 (searchableAttributes, filterableAttributes, sortableAttributes, rankingRules 中文优化)。
    *   `index_message(message_data)`: 索引单条消息。
    *   `index_messages_bulk(messages_data_list)`: 批量索引消息。
    *   `search(query, filters=None, sort=None, page=1, hits_per_page=10)`:
        *   构建 Meilisearch 搜索请求。
        *   执行搜索并返回结果。
    *   `delete_message(message_id)`: (可选) 删除索引中的消息。
*   **`config_manager.py`**:
    *   加载 `.env` 和/或 `config.ini`。
    *   提供获取配置项（API Key, Token, 白名单列表等）的方法。
    *   `get_whitelist()`: 返回白名单 Chat ID 列表。
    *   `add_to_whitelist(chat_id)`: 添加到白名单并保存配置。
    *   `remove_from_whitelist(chat_id)`: 从白名单移除并保存配置。
    *   `get_oldest_sync_timestamp(chat_id)`: 获取指定聊天的最旧同步时间戳，优先使用聊天特定设置，其次使用全局设置。
    *   `set_oldest_sync_timestamp(chat_id, timestamp)`: 设置全局或聊天特定的最旧同步时间戳，支持ISO 8601字符串格式和时间戳格式。
*   **`models.py`**:
    *   `MeiliMessageDoc(BaseModel)`: Pydantic 模型，定义 Meilisearch 中存储的消息文档结构。
        *   `id: str` (e.g., `chatid_messageid`)
        *   `message_id: int`
        *   `chat_id: int`
        *   `chat_title: Optional[str]`
        *   `chat_type: str` (user, group, channel)
        *   `sender_id: int`
        *   `sender_name: Optional[str]`
        *   `text: str`
        *   `date: int` (Unix timestamp)
        *   `message_link: str`

### 4.2 Meilisearch 索引配置
*   **`index_name`**: e.g., `telegram_messages`
*   **`searchableAttributes`**: `["text", "sender_name", "chat_title"]` (text 优先级最高)
*   **`filterableAttributes`**: `["chat_id", "chat_type", "sender_id", "date"]`
*   **`sortableAttributes`**: `["date"]`
*   **`rankingRules`**: 默认规则通常对中文友好，可根据需要调整，如优先匹配 `text`。
    *   `["words", "typo", "proximity", "attribute", "sort", "exactness"]`
*   **`stopWords`**: (可选) 添加中文停用词列表，如果发现搜索结果被常见无意义词干扰。
*   **`synonyms`**: (可选) 配置同义词，提升搜索召回。

### 4.3 前端组件设计原则 (React 应用示例)
(你提供的原则已经很好，保持不变)

### 4.4 API 设计与集成 (若有 Mini App/Web API)
(你提供的 RESTful API 设计原则很好，保持不变)

#### 具体 API 端点示例 (FastAPI)

*   **Search API**
    *   `POST /api/v1/search`
    *   Request Body (JSON):
        ```json
        {
            "query": "搜索关键词",
            "filters": { // 可选
                "chat_type": ["group", "channel"], // 筛选类型
                "date_from": 1672531200, // Unix timestamp
                "date_to": 1704067199 // Unix timestamp
            },
            "page": 1,
            "hits_per_page": 10
        }
        ```
    *   Response Body (JSON):
        ```json
        {
            "hits": [
                {
                    "id": "12345_67890",
                    "chat_title": "技术交流群",
                    "sender_name": "张三",
                    "text_snippet": "关于...的讨论，我觉得...", // Meilisearch可返回高亮片段
                    "date": 1698883200,
                    "message_link": "t.me/c/12345/67890"
                }
                // ... more hits
            ],
            "query": "搜索关键词",
            "processingTimeMs": 25,
            "limit": 10,
            "offset": 0,
            "estimatedTotalHits": 150
        }
        ```
*   **Configuration API (Admin only, if needed for Web UI to manage whitelist)**
    *   `GET /api/v1/admin/whitelist`
    *   `POST /api/v1/admin/whitelist` (Body: `{"chat_id": 123456789}`)
    *   `DELETE /api/v1/admin/whitelist/{chat_id}`

## 5. 测试与调试

*   **单元测试 (Unit Tests)**:
    *   使用 `pytest`。
    *   测试独立函数和方法，如：
        *   `core.models.MeiliMessageDoc` 的数据转换。
        *   `user_bot.utils.generate_message_link`。
        *   `search_bot.message_formatters` 的格式化逻辑。
        *   `core.meilisearch_service` 中构造查询的逻辑 (mock Meilisearch client)。
*   **集成测试 (Integration Tests)**:
    *   使用 `pytest`，可能需要 `pytest-asyncio`。
    *   测试模块间的交互：
        *   Userbot 消息处理 -> Meilisearch 索引。
        *   Search Bot 命令 -> Meilisearch 搜索 -> 结果格式化。
    *   本地启动一个 Meilisearch Docker 实例进行测试。
    *   Mock `TelethonClient` 和 `python-telegram-bot.Bot` 的外部 API 调用。
*   **端到端测试 (E2E Tests - 手动为主，自动化较复杂)**:
    *   在真实的 Telegram 环境中，通过 Bot 进行完整流程测试。
    *   Userbot 监听真实群组，Bot 进行搜索。
*   **API 测试 (若有 API Server)**:
    *   FastAPI 自带的 Swagger UI (`/docs`) 或 OpenAPI (`/redoc`) 界面进行手动测试。
    *   使用 `requests` 或 `httpx` 配合 `pytest` 编写自动化 API 测试脚本。
*   **调试技巧**:
    *   **Logging**: 大量使用 `logging` 模块，在关键步骤输出信息，设置不同级别 (DEBUG, INFO, WARNING, ERROR)。
    *   **Python Debugger**: `pdb` 或 IDE (VS Code, PyCharm) 内置的调试器。
    *   **Meilisearch Dashboard**: Meilisearch 自带一个 Web UI (默认不开启，可通过配置或参数开启)，可以查看索引、文档、配置和执行测试搜索。
    *   **Telethon Logging**: Telethon 有自己的日志系统，可以配置级别。
    *   **Sentry / GlitchTip**: (可选，用于生产环境) 错误追踪服务。

## 6. 部署

*   **Meilisearch**:
    *   **Docker**: 官方推荐，易于部署和管理。 `docker run -p 7700:7700 -v $(pwd)/meili_data:/meili_data getmeili/meilisearch:latest meilisearch --master-key='YOUR_MASTER_KEY' --env='production'`
    *   **Meilisearch Cloud**: 官方提供的托管服务。
    *   **云服务商**: 直接在 VPS 上运行二进制文件或 Docker。
*   **Python 应用 (Userbot & Search Bot & API Server)**:
    *   **Docker**: 将 Python 应用打包成 Docker 镜像，与 Meilisearch 一起通过 `docker-compose` 管理。
        *   `Dockerfile` 需要包含 Python 环境、依赖安装、代码复制和启动命令。
    *   **服务器/VPS**:
        *   使用 `systemd` 或 `supervisor` 管理 Python 进程，确保后台运行和自动重启。
        *   使用虚拟环境 (`venv` 或 `conda`)。
    *   **PaaS (Platform as a Service)**: Heroku, Railway, Render 等 (注意免费套餐的限制，特别是对于需要持久运行的 Userbot)。
*   **前端应用 (Mini App/Web)**:
    *   **静态站点托管**: Netlify, Vercel, GitHub Pages, Cloudflare Pages。
    *   如果 API Server 使用 FastAPI，也可以配置其提供静态文件服务。
*   **环境变量管理**:
    *   严格使用环境变量配置敏感信息 (API Keys, Tokens, Meilisearch Master Key)。
    *   Docker: 通过 `docker-compose.yml` 或 `docker run -e` 传递。
    *   服务器: 设置系统环境变量或使用 `.env` 文件 (确保 `.env` 不被提交到 Git)。
*   **CI/CD (持续集成/持续部署)**:
    *   **GitHub Actions (推荐)** / GitLab CI / Jenkins。
    *   自动化流程：代码提交 -> 运行测试 (linting, unit, integration) -> 构建 Docker 镜像 -> 推送镜像到 Docker Hub/GHCR -> 部署到服务器/PaaS。

## 7. 文档与维护
(你提供的文档类型、自动化文档方案、README 模板、Issue 跟踪和版本管理、技术债务管理都非常棒，可以直接沿用。)

**补充一点关于AI辅助开发的思考：**

*   **代码生成：** 对于明确定义的模块和函数（如 `MeilisearchService` 中的方法，Bot 的命令处理函数），AI 代码助手（如 GitHub Copilot, GPT-4）可以高效生成初始代码框架甚至完整实现。
*   **测试用例生成：** AI 可以辅助生成单元测试的 boilerplate 和一些基础测试用例。
*   **文档编写：** AI 可以根据代码注释（如 docstrings）生成初步的 API 文档或模块说明。
*   **调试辅助：** 描述问题给 AI，它可能能提供一些调试思路或指出潜在错误。
*   **重构建议：** AI 或许能分析代码并给出一些重构建议。
**关键是提供给 AI 清晰、结构化的需求和上下文，就像这份完善后的项目计划一样。**