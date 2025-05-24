# Subtask: Implement "Oldest Sync Timestamp" Feature

This log will detail the steps taken by the 💻 Code mode to implement the feature allowing users to set an oldest sync time for message caching.

---

## 1. 初步分析与理解

### 1.1 功能概述

"最旧同步时间"(Oldest Sync Timestamp)功能允许用户设置一个截止日期，早于这个日期的历史消息将不会被缓存。这个设置可以全局生效，也可以针对特定的聊天（群组/私聊/频道）生效。

### 1.2 需要修改的文件

1. `whitelist.json` - 添加新的配置结构
2. `core/config_manager.py` - 更新配置管理器以支持新的配置结构
3. `user_bot/history_syncer.py` - 修改同步逻辑以考虑最旧同步时间限制
4. `FOLLOWME.md` - 更新设计文档
5. 可能需要查看 `main.py` 是否需要调整（通过分析确认）

### 1.3 当前代码分析

- `whitelist.json` 当前是一个简单的JSON文件，包含一个"whitelist"数组和"updated_at"字段
- `core/config_manager.py` 提供了配置管理功能，包括加载和管理白名单
- `user_bot/history_syncer.py` 包含了消息同步的核心逻辑
- `main.py` 是应用程序的主入口，初始化和管理各个组件

## 2. 实现计划

### 2.1 修改 `whitelist.json` 格式

添加新的 `sync_settings` 字段，支持以下结构：
```json
{
    "whitelist": [-1001926579047],
    "updated_at": null,
    "sync_settings": {
        "global_oldest_sync_timestamp": "2024-01-01T00:00:00Z",
        "-1001926579047": {
            "oldest_sync_timestamp": "2025-01-01T00:00:00Z"
        }
    }
}
```

### 2.2 更新 `ConfigManager` 类

1. 修改 `load_whitelist` 方法以加载新的 `sync_settings` 字段
2. 添加新方法 `get_oldest_sync_timestamp(chat_id)` 用于获取特定聊天的最旧同步时间
3. 更新 `save_whitelist` 方法以保存新的配置结构

### 2.3 修改 `HistorySyncer` 类

更新 `sync_chat_history` 和 `initial_sync_all_whitelisted_chats` 方法，以在同步过程中考虑最旧同步时间限制。

### 2.4 更新设计文档

在 `FOLLOWME.md` 中添加关于"最旧同步时间"功能的描述。

### 2.5 编写单元测试

为新增和修改的功能编写单元测试，确保功能正确性和代码质量。

## 3. 实现过程

### 3.1 检查相关文件

我已经检查了以下关键文件，了解了当前的代码结构和功能：

1. `whitelist.json` - 当前是一个简单的JSON文件，包含白名单ID列表和更新时间
2. `core/config_manager.py` - 包含 `ConfigManager` 类，负责加载和管理配置
3. `user_bot/history_syncer.py` - 包含 `HistorySyncer` 类，负责同步历史消息
4. `main.py` - 应用程序入口点
5. `FOLLOWME.md` - 项目设计文档
6. 相关单元测试文件

### 3.2 修改 ConfigManager

我已更新 `core/config_manager.py` 文件，添加了以下功能：

1. 引入 `dateutil` 库用于解析 ISO 8601 日期格式
2. 在 `ConfigManager` 类中添加 `sync_settings` 字段以存储同步配置
3. 修改 `load_whitelist()` 方法以加载 `sync_settings` 配置
4. 修改 `save_whitelist()` 方法以保存 `sync_settings` 配置
5. 添加 `get_oldest_sync_timestamp(chat_id)` 方法，根据聊天ID返回适用的最旧同步时间戳
6. 添加 `_parse_timestamp()` 辅助方法解析时间戳值
7. 添加 `set_oldest_sync_timestamp(chat_id, timestamp)` 方法，用于设置全局或聊天特定的最旧同步时间戳

这些修改使 `ConfigManager` 能够管理和提供最旧同步时间戳信息，支持两种配置方式：
- 全局设置：适用于所有聊天
- 聊天特定设置：仅适用于指定的聊天

### 3.3 修改 HistorySyncer

我已更新 `user_bot/history_syncer.py`，实现了以下功能：

1. 在 `sync_chat_history` 方法中添加对 `get_oldest_sync_timestamp` 的调用，获取适用于当前聊天的最旧同步时间戳
2. 在历史消息迭代过程中检查每条消息的日期，如果早于最旧同步时间戳，则停止向前同步
3. 添加相应的日志记录，以便于跟踪和调试

这些修改使同步过程能够在遇到早于最旧同步时间戳的消息时停止，从而避免缓存过于久远的消息。

### 3.4 更新单元测试

我已经更新了以下单元测试文件：

#### 3.4.1 修改 `tests/unit/test_config_manager.py`

为 `ConfigManager` 类添加了两个新的测试方法：
1. `test_oldest_sync_timestamp` - 测试设置和获取最旧同步时间戳的功能
2. `test_timestamp_parser` - 测试时间戳解析功能

这些测试验证了：
- 获取全局和聊天特定时间戳的功能
- 使用不同格式（ISO 8601字符串、datetime对象、Unix时间戳）设置时间戳
- 删除时间戳设置的功能
- 时间戳解析的准确性

#### 3.4.2 修改 `tests/unit/test_history_syncer.py`

添加了新的测试方法 `test_oldest_sync_timestamp_limit`，测试历史同步器在遇到早于最旧同步时间戳的消息时是否会停止同步。

测试用例模拟了两条消息：
- 一条较新的消息（在最旧同步时间戳之后）
- 一条较旧的消息（在最旧同步时间戳之前）

验证了同步器只处理最旧同步时间戳之后的消息。

### 3.5 检查依赖项

由于我在 `ConfigManager` 中使用了 `dateutil` 库来解析 ISO 8601 日期格式，需要确保这个库在项目依赖中。检查后发现 `requirements.txt` 文件中没有包含这个依赖，因此我已经将 `python-dateutil` 添加到依赖列表中。

### 3.6 更新设计文档

我已经更新了 `FOLLOWME.md` 设计文档，添加了关于"最旧同步时间"功能的描述：

1. 在 `1.1 用户需求` -> `次要功能 (V2)` 部分，添加了关于"最旧同步时间"功能的描述。
2. 在 `4.1.3 Core 模块 (core/)` -> `config_manager.py` 部分，描述了新增的用于处理 `oldest_sync_timestamp` 的逻辑和方法。
3. 在 `4.1.1 Userbot 模块 (user_bot/)` -> `history_syncer.py` 部分，描述了其如何使用 `oldest_sync_timestamp` 来限制历史消息的同步范围。

## 4. 最终实现结果

### 4.1 更新后的 `whitelist.json` 示例

以下是更新后的 `whitelist.json` 文件示例，展示了新增的 `sync_settings` 结构：

```json
{
    "whitelist": [-1001926579047, -1001234567890],
    "updated_at": 1714898400,
    "sync_settings": {
        "global_oldest_sync_timestamp": "2024-01-01T00:00:00Z",
        "-1001926579047": {
            "oldest_sync_timestamp": "2025-01-01T00:00:00Z"
        }
    }
}
```

在这个例子中：

- `sync_settings` 字段包含全局设置和特定聊天的设置
- 全局设置 `global_oldest_sync_timestamp` 适用于所有聊天，设置为 "2024-01-01T00:00:00Z"
- 聊天 `-1001926579047` 有特定设置，其 `oldest_sync_timestamp` 为 "2025-01-01T00:00:00Z"
- 聊天 `-1001234567890` 没有特定设置，将使用全局设置

### 4.2 实现的功能概述

1. **配置管理**
   - 添加了新的配置结构支持，允许设置全局和聊天特定的最旧同步时间戳
   - 支持ISO 8601格式的日期时间字符串和Unix时间戳两种格式
   - 提供API用于获取和设置最旧同步时间戳

2. **历史同步限制**
   - 历史同步器在遍历消息时检查消息日期，当遇到早于最旧同步时间戳的消息时停止同步
   - 添加了适当的日志记录，便于追踪同步过程和限制原因

3. **依赖管理**
   - 添加了`python-dateutil`依赖以支持ISO 8601日期格式的解析

### 4.3 添加用户接口

我已经添加了两种管理"最旧同步时间"功能的接口：

#### 4.3.1 API接口

在 `api/routers/whitelist.py` 中添加了以下端点：

1. `GET /admin/whitelist/sync_settings` - 获取所有同步设置
2. `PUT /admin/whitelist/sync_settings/global` - 设置全局最旧同步时间戳
3. `PUT /admin/whitelist/sync_settings/chat/{chat_id}` - 设置特定聊天的最旧同步时间戳
4. `GET /admin/whitelist/sync_settings/chat/{chat_id}` - 获取特定聊天的最旧同步时间戳

这些API端点支持JSON格式的请求和响应，可以与前端应用集成。

#### 4.3.2 命令行接口

在 `search_bot/command_handlers.py` 中添加了以下命令：

1. `/set_oldest_sync_time [chat_id] <timestamp>` - 设置全局或特定聊天的最旧同步时间戳
   - 例如：`/set_oldest_sync_time 2023-01-01T00:00:00Z` (设置全局)
   - 例如：`/set_oldest_sync_time -1001234567890 2023-01-01T00:00:00Z` (设置特定聊天)
   - 支持移除设置：`/set_oldest_sync_time remove` 或 `/set_oldest_sync_time -1001234567890 remove`

2. `/view_oldest_sync_time [chat_id]` - 查看全局或特定聊天的最旧同步时间设置
   - 例如：`/view_oldest_sync_time` (查看所有设置)
   - 例如：`/view_oldest_sync_time -1001234567890` (查看特定聊天设置)

这些命令使管理员可以直接通过Telegram机器人管理同步时间设置，无需访问API。

### 4.4 总结

"最旧同步时间"功能已成功实现，并提供了灵活的配置和管理选项：

- 配置方面：
  - 设置全局最旧同步时间，适用于所有聊天
  - 为特定聊天设置独立的最旧同步时间，覆盖全局设置
  - 支持多种时间格式，便于用户配置
  - 有效减少缓存过于久远消息的存储需求，提高系统效率

- 接口方面：
  - 提供RESTful API接口，便于集成到前端应用
  - 提供Telegram Bot命令接口，便于管理员直接管理
  - 支持查看、设置和删除操作

### 4.5 文档更新

我已更新了搜索机器人的帮助文档，在 `/help` 命令的输出中添加了有关"最旧同步时间"功能的详细说明：

1. 添加了可用命令的说明：
   - `/set_oldest_sync_time` - 设置全局或特定聊天的最旧同步时间戳
   - `/view_oldest_sync_time` - 查看当前的最旧同步时间设置

2. 提供了具体的使用示例：
   - 设置全局时间戳
   - 设置特定聊天的时间戳
   - 移除设置
   - 查看所有设置或特定聊天设置

3. 添加了关于功能用途的说明，帮助用户理解这个功能的价值

这些文档更新使管理员能够更容易地理解和使用这个新功能，从而有效管理历史消息的同步范围。