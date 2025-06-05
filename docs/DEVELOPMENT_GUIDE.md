# 开发指引与规划

本文件旨在向新加入的开发者和 AI 助手概述项目当前的状态、代码结构以及后续开发的计划。项目的详细背景和历史请参考 `memory-bank/` 目录下的文档。

## 1. 项目概览

- **目标**：提供面向中文环境的 Telegram 历史消息全文搜索工具。
- **核心组件**：
  - `user_bot/`：使用 Telethon 实现的 UserBot，负责同步并索引历史消息。
  - `search_bot/`：基于 Telethon 的搜索机器人，供终端用户查询。
  - `api/`：FastAPI 服务，向前端或其他客户端提供搜索和配置接口。
  - `frontend/`：Vite + React 前端，兼容 Telegram Mini App。
  - `core/`：通用功能模块，如配置管理和 Meilisearch 服务封装。
  - `tests/`：Pytest 单元与集成测试。

## 2. 仓库结构

```
├── api/               # FastAPI 应用及路由
├── core/              # Meilisearch 服务、配置管理等核心模块
├── frontend/          # 前端 React 应用
├── search_bot/        # 供用户使用的搜索机器人
├── user_bot/          # 监听并同步消息的 UserBot
├── tests/             # 单元测试与集成测试
├── config.ini*        # 主配置文件（模板在 config.ini.example）
├── .env*              # 环境变量文件（模板在 .env.example）
├── docker-compose.yml # 启动 Meilisearch 的示例配置
├── README.md          # 项目简介及基本说明
└── memory-bank/       # 项目计划、决策日志与进度记录
```
带 * 号的文件需要在本地创建或复制模板后再填入实际值。

## 3. 环境搭建

1. **Python**：项目要求 Python 3.9 以上，可使用 [`uv`](https://github.com/astral-sh/uv) 创建虚拟环境：
   ```bash
   uv venv .venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```
2. **Meilisearch**：通过 `docker-compose up -d` 启动，服务默认监听 `localhost:7700`。
3. **前端依赖**：
   ```bash
   cd frontend
   npm install
   ```
4. 复制 `config.ini.example`、`.env.example` 等模板文件，填入 Telegram API ID、HASH、Bot Token 等信息。

## 4. 运行方式

启动全部服务的典型流程：

```bash
# 1. 启动后端 API（含 SearchBot）
python main.py

# 2. 另一个终端中运行前端开发服务器
cd frontend
npm run dev
```

首次运行时 UserBot 会要求登录 Telegram 账号，请根据提示完成登录。

## 5. 测试

项目使用 `pytest` 管理测试用例：

```bash
pytest -vv
```

测试覆盖核心模型、事件处理、API 路由等模块，详见 `tests/` 目录。

## 6. 开发规划简述

根据 `memory-bank/PLAN.md`，项目分为多个阶段推进：

1. **阶段 0：环境准备**（已完成）
2. **阶段 1：后端核心功能开发**（已完成）
3. **阶段 2：前端基础功能开发**（已完成）
4. **阶段 3：前后端协同与功能优化**（进行中）
5. **阶段 4：部署与后续增强**（未开始）

详细进度可查看 `memory-bank/progress.md`，关键技术决策记录在 `memory-bank/decisionLog.md`。

## 7. 后续工作建议

- 按 `progress.md` 中最新的 commit 描述继续完善同步时间管理和白名单交互体验。
- 补充更多单元测试和端到端测试，提高稳定性。
- 关注 `productContext.md` 中提及的会话模块和性能优化，确保在大规模数据下仍能流畅运行。
- 规划部署方案，可参考 `docker-compose.yml` 或其它 PaaS 服务。

## 8. 参考文档

- `memory-bank/FOLLOWME.md`：总体项目愿景与功能分类。
- `memory-bank/PLAN.md`：面向 AI 的执行计划和里程碑。
- `memory-bank/progress.md`：已完成任务的时间线与成果。
- `memory-bank/decisionLog.md`：重要决策及其理由。

以上内容应能帮助新开发者或 AI 助手迅速了解项目现状并继续开发。
