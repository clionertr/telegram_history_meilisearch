# Telegram 中文历史消息搜索工具

本项目旨在打造一款高效、易用的 Telegram 中文历史消息搜索工具。

## 项目愿景

解决 Telegram 原生搜索在中文语境下的不足，例如分词不准确、对中文优化不够等问题，从而显著提升用户在大量历史消息中获取目标信息的效率。

## 主要功能 (规划中)

*   **高效索引:** 利用 Meilisearch 对 Telegram 消息进行快速、准确的索引。
*   **精准搜索:** 提供更符合中文习惯的搜索体验，支持关键词、短语搜索等。
*   **用户友好:** 通过 Telegram Bot 和 Web/Mini App 提供便捷的搜索界面和交互。
*   **灵活配置:** 支持白名单、黑名单等配置，满足个性化需求。

## 技术栈 (初步设想)

*   **后端:** Python (Telethon, python-telegram-bot, FastAPI), Meilisearch
*   **前端:** React (或其他现代前端框架)
*   **部署:** Docker

## 配置说明

本系统使用多个配置文件来管理不同的设置。了解它们的作用和优先级对于正确配置和运行本工具至关重要。

### 配置文件概览

1.  **`config.ini`**:
    *   **作用**: 存放通用的、非敏感的应用程序级配置。这些配置可能被项目中的多个部分共享。
    *   **示例**: MeiliSearch 服务地址、通用日志级别、缓存目录等。
    *   **模板**: [`config.ini.example`](config.ini.example:0)

2.  **`.env`**:
    *   **作用**: 主要用于存放环境变量，特别是**敏感信息**或根据不同部署环境需要改变的配置。此文件中的变量会被加载到操作系统的环境变量中。
    *   **示例**: Search Bot (主机器人) 的 `TELEGRAM_BOT_TOKEN`、全局 `TELEGRAM_API_ID` 和 `TELEGRAM_API_HASH`、MeiliSearch API Key、管理员用户 ID 列表 (`ADMIN_IDS`)。
    *   **重要**: 此文件**不应提交到版本控制系统 (Git)**。请将其添加到 `.gitignore` 文件中。
    *   **模板**: [`.env.example`](.env.example:0) (列出需要配置的环境变量，但不包含具体值)。

3.  **`.env.userbot`**:
    *   **作用**: 专门用于存放 **User Bot (用户机器人)** 的特定配置，尤其是 API ID 和 API Hash 等敏感信息。
    *   **优点**: 配置隔离、增强安全性、方便通过 Search Bot 命令动态修改。
    *   **示例**: `USER_API_ID`、`USER_API_HASH`、`USER_SESSION_NAME`、`USER_PROXY_URL`。
    *   **重要**: 此文件**不应提交到版本控制系统 (Git)**。
    *   **模板**: [`.env.userbot.example`](.env.userbot.example:0)
    *   **管理**: 可以通过 Search Bot 的 `/set_userbot_config` 命令修改此文件。

### 配置加载优先级

程序在加载配置时，遵循以下优先级顺序：

*   **User Bot 特定配置** (如 `USER_API_ID`, `USER_API_HASH`):
    1.  [`.env.userbot`](.env.userbot:0) (最高优先级)
    2.  `.env` (作为环境变量加载)
    3.  [`config.ini`](config.ini:0) (最低优先级)
*   **其他非 User Bot 专属配置** (如 MeiliSearch 设置, Search Bot Token):
    1.  `.env` (作为环境变量加载) (最高优先级)
    2.  [`config.ini`](config.ini:0) (最低优先级)

### 管理员设置

管理员权限允许用户执行特定的管理命令，如管理白名单、配置和重启 User Bot。

**设置管理员用户 ID (Telegram User ID):**

1.  **通过 `.env` 文件 (推荐):**
    在项目根目录的 `.env` 文件中添加或修改 `ADMIN_IDS` 变量。多个 ID 用逗号分隔：
    ```env
    ADMIN_IDS=123456789,987654321
    ```
2.  **通过 `config.ini` 文件:**
    在项目根目录的 [`config.ini`](config.ini:0) 文件的 `[Telegram]` 部分添加或修改 `ADMIN_IDS` 配置项:
    ```ini
    [Telegram]
    ADMIN_IDS=123456789,987654321
    ```
    *注意: `.env` 文件中的设置会覆盖 `config.ini` 中的设置。*

**获取 Telegram User ID:**
*   与 Telegram 上的 **@userinfobot** 机器人对话。
*   当有用户尝试执行管理员命令但权限不足时，系统日志中也会记录该用户的 ID。

修改配置后，请**重启应用程序**使管理员设置生效。

### User Bot 管理命令 (仅限管理员)

*   `/set_userbot_config <配置项> <值>`: 设置 User Bot 的配置 (写入 [`.env.userbot`](.env.userbot:0))。
    *   例如: `/set_userbot_config USER_SESSION_NAME my_new_session`
    *   可配置项: `USER_API_ID`, `USER_API_HASH`, `USER_SESSION_NAME`, `USER_PROXY_URL`。
*   `/view_userbot_config`: 查看 User Bot 当前的主要配置项 (敏感信息会打码)。
*   `/restart_userbot`: 重启 User Bot 以应用新的配置。

欢迎参与贡献，共同完善这款工具！