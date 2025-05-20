# API 服务使用指南

本文档提供关于 API 服务的使用说明，包括端点说明、请求/响应示例和使用建议。

## 概述

API 服务基于 FastAPI 构建，提供以下功能：

- 搜索 Telegram 历史消息
- 管理白名单（添加、移除、查询聊天ID）

API 服务与主程序集成，在程序启动时会自动运行在 `http://localhost:8000`。

## API 文档

启动服务后，可以通过以下地址访问自动生成的交互式 API 文档：

- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

## 搜索 API

### 端点

```
POST /api/v1/search
```

### 请求参数

```json
{
  "query": "搜索关键词",
  "filters": {
    "chat_type": ["group", "channel"],
    "date_from": 1672531200,
    "date_to": 1704067199
  },
  "page": 1,
  "hits_per_page": 10
}
```

- `query`: (必填) 搜索关键词
- `filters`: (可选) 过滤条件
  - `chat_type`: 聊天类型数组，可选值: "user", "group", "channel"
  - `date_from`: 起始日期的 Unix 时间戳
  - `date_to`: 结束日期的 Unix 时间戳
- `page`: 页码，从 1 开始
- `hits_per_page`: 每页结果数量，默认 10

### 响应格式

```json
{
  "hits": [
    {
      "id": "12345_67890",
      "chat_title": "技术交流群",
      "sender_name": "张三",
      "text_snippet": "关于...的讨论，我觉得...",
      "date": 1698883200,
      "message_link": "t.me/c/12345/67890"
    }
  ],
  "query": "搜索关键词",
  "processingTimeMs": 25,
  "limit": 10,
  "offset": 0,
  "estimatedTotalHits": 150
}
```

### 使用示例

#### curl 示例

```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/search' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "人工智能",
  "filters": {
    "chat_type": ["group"]
  },
  "page": 1,
  "hits_per_page": 10
}'
```

#### JavaScript (fetch) 示例

```javascript
const response = await fetch('http://localhost:8000/api/v1/search', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: '人工智能',
    filters: {
      chat_type: ['group'],
      date_from: 1672531200 // 2023-01-01
    },
    page: 1,
    hits_per_page: 10
  }),
});

const data = await response.json();
console.log(data);
```

#### Python (httpx) 示例

```python
import httpx
import json

async def search_messages(query, filters=None, page=1, hits_per_page=10):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'http://localhost:8000/api/v1/search',
            json={
                'query': query,
                'filters': filters,
                'page': page,
                'hits_per_page': hits_per_page
            }
        )
        return response.json()

# 使用示例
filters = {
    'chat_type': ['group', 'channel'],
    'date_from': 1672531200  # 2023-01-01
}
results = await search_messages('人工智能', filters=filters)
```

## 白名单管理 API

### 获取白名单

```
GET /api/v1/admin/whitelist
```

#### 响应格式

```json
{
  "whitelist": [123456789, -987654321],
  "count": 2
}
```

### 添加到白名单

```
POST /api/v1/admin/whitelist
```

#### 请求参数

```json
{
  "chat_id": 123456789
}
```

#### 响应格式

```json
{
  "success": true,
  "message": "ID 已成功添加到白名单",
  "chat_id": 123456789
}
```

### 从白名单移除

```
DELETE /api/v1/admin/whitelist/{chat_id}
```

#### 响应格式

```json
{
  "success": true,
  "message": "ID 已成功从白名单移除",
  "chat_id": 123456789
}
```

### 重置白名单

```
DELETE /api/v1/admin/whitelist
```

#### 响应格式

```json
{
  "success": true,
  "message": "白名单已成功重置",
  "chat_id": 0
}
```

### 使用示例

#### curl 示例

添加到白名单:
```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/admin/whitelist' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "chat_id": 123456789
}'
```

获取白名单:
```bash
curl -X 'GET' \
  'http://localhost:8000/api/v1/admin/whitelist' \
  -H 'accept: application/json'
```

#### JavaScript (fetch) 示例

```javascript
// 添加到白名单
const addResponse = await fetch('http://localhost:8000/api/v1/admin/whitelist', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    chat_id: 123456789
  }),
});

// 获取白名单
const getResponse = await fetch('http://localhost:8000/api/v1/admin/whitelist', {
  method: 'GET',
  headers: {
    'accept': 'application/json',
  }
});

const whitelist = await getResponse.json();
console.log(whitelist);
```

## 使用建议

1. **前端集成**：前端应用在 `frontend/src/services/api.js` 中封装对这些 API 的调用。

2. **错误处理**：客户端应适当处理 API 可能返回的错误状态码：
   - 400: 请求参数错误
   - 404: 资源不存在
   - 500: 服务器内部错误

3. **分页处理**：使用搜索 API 时，前端应实现分页导航，根据 `estimatedTotalHits` 计算总页数。

4. **安全性考虑**：在生产环境中，应考虑对白名单管理 API 添加认证机制。

5. **CORS 配置**：API 服务已配置允许来自 `localhost:5173` 和 `localhost:3000` 的跨域请求，如需其他源，请修改 `api/main.py` 中的 CORS 配置。