# 项目更新任务 - 2025/5/19

## 任务概述

根据用户的最新指示，更新项目文档 ([`FOLLOWME.md`](FOLLOWME.md:0), [`memory-bank/PLAN.md`](memory-bank/PLAN.md:0)) 和项目配置文件 ([`requirements.txt`](requirements.txt:0), [`pyproject.toml`](pyproject.toml:0))。核心变更包括：Search Bot 改用 Telethon 实现，以及通过 `pyproject.toml` 的 `requires-python` 结合 `uv` 管理 Python 版本。

## 详细步骤记录

### 任务初始化
- 接收到用户指令，开始执行更新任务。
- 计划按顺序更新以下文件：
    1. [`FOLLOWME.md`](FOLLOWME.md:0)
    2. [`memory-bank/PLAN.md`](memory-bank/PLAN.md:0)
    3. [`requirements.txt`](requirements.txt:0)
    4. [`pyproject.toml`](pyproject.toml:0)
- 所有修改步骤和思考过程将记录在此文件中。

---
### 1. 更新 `FOLLOWME.md`

#### 1.1 修改 "2.2 后端框架选择"

**目标:**
- 将 `python-telegram-bot` 的描述修改为不再用于此项目，Search Bot 改用 Telethon。
- 更新 `Telethon` 的描述，明确其用于 Userbot 和 Search Bot。

**定位 (基于读取到的文件内容):**
- `Telethon` 描述在第 81 行: `    *   **Telethon:** 与 Telegram User API 交互。`
- `python-telegram-bot` 描述在第 83 行: `    *   **python-telegram-bot:** (推荐) 主流的 Telegram Bot API 框架，异步支持良好。`

**计划修改:**
- **第 81 行 (Telethon):**
  ```diff
  -     *   **Telethon:** 与 Telegram User API 交互。
  +     *   **Telethon:** 与 Telegram User API 和 Bot API 交互 (用于 Userbot 和 Search Bot)。
  ```
- **第 83 行 (python-telegram-bot):**
  ```diff
  -     *   **python-telegram-bot:** (推荐) 主流的 Telegram Bot API 框架，异步支持良好。
  +     *   ~~`python-telegram-bot`~~ (不再用于此项目，Search Bot 将改用 Telethon)。
  ```
  或者，考虑直接移除 `python-telegram-bot` 这一条，并将相关信息整合到 Telethon 的描述中。根据用户指示“或者直接移除此条目，并在 Telethon 的描述中整合”，我选择后者，即修改 Telethon 并移除 python-telegram-bot 条目。

**最终计划 (整合后):**
- **修改第 81 行 (Telethon):**
  ```diff
  -     *   **Telethon:** 与 Telegram User API 交互。
  +     *   **Telethon:** 与 Telegram User API 和 Bot API 交互 (用于 Userbot 和 Search Bot)。
  ```
- **移除第 83 行 (python-telegram-bot)。**

#### 1.2 添加 "2.2.1 Python 版本管理"

**目标:**
- 在 "2.2 后端框架选择" 之后，添加关于 Python 版本管理的说明。

**定位:**
- "2.2 后端框架选择" 的核心库列表结束于第 85 行: `    *   **配置管理:** \`python-dotenv\` (管理 \`.env\` 文件), \`Pydantic\` (用于 FastAPI 和配置模型)。`
- 新内容将插入到第 86 行之后 (原文件中的空行)。

**计划插入内容 (从第 86 行开始):**
```markdown

    #### Python 版本管理
    项目推荐使用 `uv` 进行虚拟环境和包管理。Python 的版本约束通过项目根目录下的 [`pyproject.toml`](pyproject.toml:0) 文件中的 `[project.requires-python]` 字段进行定义 (例如, `requires-python = ">=3.9"`). `uv` 在创建虚拟环境时会遵循此设置。
```

---
### 2. 更新 `memory-bank/PLAN.md`

#### 2.1 修改 "阶段 0: 项目初始化与环境准备, 任务 2: 搭建本地开发环境, Python (后端) 部分"

**目标:**
- 修改核心依赖列表的描述，确保反映 Search Bot 使用 Telethon。
- 在其描述下方补充 Python 版本管理说明。

**定位 (基于读取到的文件内容):**
- 核心依赖描述在第 35 行: `            *   根据 \`FOLLOWME.md\` 技术选型，在 \`requirements.txt\` 中列出核心依赖 (Telethon, meilisearch-python, python-telegram-bot, FastAPI, python-dotenv, Pydantic)。`
- 补充内容将插入到第 36 行之后。

**计划修改:**
- **第 35 行 (核心依赖):**
  ```diff
  -             *   根据 `FOLLOWME.md` 技术选型，在 `requirements.txt` 中列出核心依赖 (Telethon, meilisearch-python, python-telegram-bot, FastAPI, python-dotenv, Pydantic)。
  +             *   根据 `FOLLOWME.md` 技术选型，在 `requirements.txt` 中列出核心依赖 (Telethon (用于 Userbot 和 Search Bot), meilisearch-python, FastAPI, python-dotenv, Pydantic, uvicorn)。
  ```
  *(注意：根据用户指示，移除了 `python-telegram-bot` 并添加了 `uvicorn` 到描述中，尽管 `uvicorn` 通常是运行 FastAPI 的方式，但在依赖描述中明确列出是好的)*

- **插入新内容 (从第 37 行开始，原第 36 行是 `pip install`):**
  ```markdown
              *   Python 版本将通过项目根目录下的 pyproject.toml 文件中的 `requires-python` 字段（例如 `requires-python = ">=3.9"`）进行约束，并由 `uv` 在创建虚拟环境时遵循此设置。
  ```

#### 2.2 修改 "阶段 1: 后端核心功能开发与测试"

**目标:**
- 重构所有与 `search_bot` 模块相关的任务描述 (任务 8, 9, 10, 11)，以反映其实现将基于 Telethon。
- 修改任务 12 (`main.py` 后端主入口) 的 AI 行动。

**定位与计划修改:**

- **任务 8 (`search_bot/message_formatters.py`) (原文件第 86-90 行):**
    - 描述："此模块的功能可能仍然需要，但其输入可能需要根据 Telethon 的消息对象调整。" - 这个描述是准确的，无需修改AI行动本身，但要确保上下文是Telethon。
    - **AI 行动 (第 88 行):**
      ```diff
      -     *   **AI 行动：**
      -         *   实现 `format_search_results()`，包括分页逻辑。
      +     *   **AI 行动：**
      +         *   实现 `format_search_results()`，处理来自 Meilisearch 的结果，并准备发送给用户的消息格式。其输入可能需要根据 Telethon 的消息对象特性进行调整（例如，如何构建回复）。
      ```

- **任务 9 (`search_bot/command_handlers.py`) (原文件第 91-96 行):**
    - **AI 行动 (第 93-95 行):**
      ```diff
      -     *   **AI 行动：**
      -         *   实现 `start_command`, `help_command`, `search_command`。
      -         *   `search_command` 应调用 `MeilisearchService.search()` 和 `MessageFormatters.format_search_results()`。
      -         *   实现白名单管理命令 (管理员权限，初期可简单实现)。
      +     *   **AI 行动：**
      +         *   使用 Telethon 的事件处理器 (如 `@client.on(events.NewMessage(pattern='/start'))` 或使用 `add_event_handler`) 来处理 `/start`, `/help`, `/search` 等命令。
      +         *   `/search` 命令的处理逻辑应调用 `MeilisearchService.search()` 并使用 `message_formatters.format_search_results()` 格式化结果。
      +         *   白名单管理命令也应通过 Telethon 事件处理。
      ```

- **任务 10 (`search_bot/callback_query_handlers.py`) (原文件第 97-100 行):**
    - **AI 行动 (第 99 行):**
      ```diff
      -     *   **AI 行动：**
      -         *   处理搜索结果分页回调。
      +     *   **AI 行动：**
      +         *   使用 Telethon 的 `events.CallbackQuery` 事件处理器来处理 Inline Button 的回调，例如用于搜索结果的分页。
      ```

- **任务 11 (`search_bot/bot.py`) (原文件第 101-105 行):**
    - **AI 行动 (第 103-104 行):**
      ```diff
      -     *   **AI 行动：**
      -         *   初始化 `Application` (python-telegram-bot)。
      -         *   注册命令和回调处理器。
      +     *   **AI 行动：**
      +         *   初始化 `TelegramClient` (Telethon) 并使用 Bot Token 进行认证 (与 Userbot 的 `TelegramClient` 实例分开，或者根据设计决策共用但需清晰区分)。
      +         *   注册通过 `command_handlers.py` 和 `callback_query_handlers.py` 中定义的事件处理器。
      +         *   启动客户端 (例如 `client.run_until_disconnected()`)。
      ```

- **任务 12 (`main.py` 后端主入口) (原文件第 106-110 行):**
    - **AI 行动 (第 108-109 行):**
      ```diff
      -     *   **AI 行动：**
      -         *   实现启动 Userbot 和 Search Bot 的逻辑。
      -         *   确保可以从命令行运行。
      +     *   **AI 行动：**
      +         *   实现启动 Userbot (Telethon, 使用用户凭据) 和 Search Bot (Telethon, 使用 Bot Token) 的逻辑。这可能涉及异步运行两个独立的 Telethon客户端。
      +         *   确保可以从命令行运行，并能正确管理两个客户端的生命周期。
      ```

#### 2.3 修改 "第 3 节 AI 建议与注意事项"

**目标:**
- 修改关于异步处理的说明，移除对 `python-telegram-bot` 的特定提及。

**定位 (基于读取到的文件内容):**
- 异步处理说明在第 259 行: `*   **异步处理：** Python 后端（Telethon, python-telegram-bot, FastAPI）大量使用异步编程，AI 需熟练运用 \`async/await\`。`

**计划修改:**
- **第 259 行 (异步处理):**
  ```diff
  - *   **异步处理：** Python 后端（Telethon, python-telegram-bot, FastAPI）大量使用异步编程，AI 需熟练运用 `async/await`。
  + *   **异步处理：** Python 后端（Telethon, FastAPI）大量使用异步编程，AI 需熟练运用 `async/await`。
  ```

---
### 3. 更新 `requirements.txt`

**目标:**
- 检查文件内容，如果 `python-telegram-bot` 存在，则移除该行。

**执行:**
- 读取了 [`requirements.txt`](requirements.txt:0) 文件。
- 文件内容为:
  ```
  Telethon
  meilisearch-python
  FastAPI
  python-dotenv
  Pydantic
  uvicorn
  ```
- **结论:** `python-telegram-bot` 不存在于文件中，因此无需修改。

---
### 4. 更新 `pyproject.toml`

**目标:**
- 将 `[project]` 表下的 `requires-python` 行从 `">=3.13"` 修改为 `">=3.9"`。
- 确保 `dependencies = []` 保持不变。

**定位 (基于读取到的文件内容):**
- `requires-python` 在第 6 行: `requires-python = ">=3.13"`
- `dependencies` 在第 7 行: `dependencies = []`

**计划修改:**
- **第 6 行 (`requires-python`):**
  ```diff
  - requires-python = ">=3.13"
  + requires-python = ">=3.9"
  ```
- **第 7 行 (`dependencies`):** 保持 `dependencies = []` 不变。

---