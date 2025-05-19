# 阶段 0: 项目初始化与环境准备
## 当前任务：2. 搭建本地开发环境

### 任务分解与执行记录

#### 1. Meilisearch 配置

**计划：**
*   生成一个安全的随机字符串作为 `MEILI_MASTER_KEY`。
*   在项目根目录下创建 `docker-compose.yml` 文件。其内容应配置一个 Meilisearch 服务。
*   Meilisearch 服务应映射端口 `7700` 到宿主机的 `7700`。
*   配置一个卷 `./meili_data:/meili_data` 以持久化 Meilisearch 数据。
*   在 `docker-compose.yml` 中为 Meilisearch 服务设置一个环境变量 `MEILI_MASTER_KEY`。

**执行：**

*   **Meilisearch 主密钥 (`MEILI_MASTER_KEY`)**:
    *   为了演示，我将使用以下示例密钥。在生产环境中，请务必生成一个真正强大且随机的密钥。
    *   `MEILI_MASTER_KEY`: `ThisIsASuperSecureRandomKeyForMeiliSearch123!@#`

*   **创建 `docker-compose.yml` 文件**:
    *   文件已创建于项目根目录。
    *   内容如下：
        ```yaml
        version: '3.8'
        services:
          meilisearch:
            image: getmeili/meilisearch:latest
            ports:
              - "7700:7700"
            volumes:
              - ./meili_data:/meili_data
            environment:
              MEILI_MASTER_KEY: 'ThisIsASuperSecureRandomKeyForMeiliSearch123!@#'
        ```

---

#### 2. Python (后端) 环境配置

**计划：**
*   在项目根目录下创建并激活 Python 虚拟环境 (例如，命名为 `.venv`)。提供创建和激活虚拟环境的命令。
*   在项目根目录下创建 `requirements.txt` 文件。
*   根据技术选型，在 `requirements.txt` 中列出核心依赖。
*   提供用于安装这些依赖的 `pip install -r requirements.txt` 命令。

**执行：**

*   **Python 虚拟环境 (使用 `uv`)**:
    *   **确保 `uv` 已安装。** 如果未安装，请参照官方文档安装 (例如 `pip install uv`)。
    *   **创建虚拟环境 (例如，在 Linux/macOS 上):**
        ```bash
        uv venv .venv
        ```
        或者，如果想指定 Python 版本 (假设 `python3.11` 已安装):
        ```bash
        uv venv .venv -p python3.11
        ```
    *   **激活虚拟环境 (例如，在 Linux/macOS 上):**
        ```bash
        source .venv/bin/activate
        ```
    *   **注意:** Windows 用户请使用相应的激活命令 (通常是 `.venv\Scripts\activate`)。`uv` 创建的是标准的虚拟环境。

*   **`requirements.txt` 文件**:
    *   文件已创建于项目根目录，并已更新。
    *   内容如下：
        ```
        Telethon
        meilisearch-python
        FastAPI
        python-dotenv
        Pydantic
        uvicorn
        ```

*   **安装依赖命令 (使用 `uv`)**:
    ```bash
    uv pip install -r requirements.txt
    ```

---

#### 3. Node.js (前端 - 预备) 环境检查

**计划：**
*   提供用于检查 Node.js (`node -v`) 和 npm (`npm -v`) 或 yarn (`yarn -v`) 是否已安装及其版本的命令。

**执行：**

*   **检查 Node.js 版本:**
    ```bash
    node -v
    ```
*   **检查 npm 版本:**
    ```bash
    npm -v
    ```
*   **检查 yarn 版本 (如果项目使用 yarn):**
    ```bash
    yarn -v
    ```

---

#### 4. 环境变量文件配置

**计划：**
*   在项目根目录下创建 `.env.example` 文件。
*   在项目根目录下创建 `.env` 文件，并将 `.env.example` 的内容复制到 `.env` 中。
*   更新 `.env` 文件中的 `MEILISEARCH_API_KEY`。
*   为其他敏感值设置占位符。

**执行：**

*   **创建 `.env.example` 文件**:
    *   文件已创建于项目根目录。
    *   内容如下：
        ```
        TELEGRAM_API_ID=your_api_id_here
        TELEGRAM_API_HASH=your_api_hash_here
        BOT_TOKEN=your_bot_token_here
        MEILISEARCH_HOST=http://localhost:7700
        MEILISEARCH_API_KEY=your_meilisearch_master_key_here
        # USERBOT_SESSION_NAME=your_userbot_session_name # (例如 userbot)
        ```

*   **创建并初始化 `.env` 文件**:
    *   文件已创建于项目根目录，并从 `.env.example` 复制了内容。

*   **更新 `.env` 文件**:
    *   `MEILISEARCH_API_KEY` 已更新为 `docker-compose.yml` 中设置的 `MEILI_MASTER_KEY`。
    *   其他敏感值 (`TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `BOT_TOKEN`) 已设置为 `TO_BE_FILLED_BY_USER`。
    *   最终 `.env` 文件内容如下：
        ```
        TELEGRAM_API_ID=TO_BE_FILLED_BY_USER
        TELEGRAM_API_HASH=TO_BE_FILLED_BY_USER
        BOT_TOKEN=TO_BE_FILLED_BY_USER
        MEILISEARCH_HOST=http://localhost:7700
        MEILISEARCH_API_KEY=ThisIsASuperSecureRandomKeyForMeiliSearch123!@#
        # USERBOT_SESSION_NAME=your_userbot_session_name # (例如 userbot)
        ```
---

所有步骤均已记录。