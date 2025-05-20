# MeiliSearchService 开发笔记

## 1. 需求分析

我需要开发 `core/meilisearch_service.py` 文件，实现 `MeiliSearchService` 类，主要功能包括：

1. 初始化 Meilisearch 客户端并连接到 Meilisearch 服务
2. 确保索引存在并正确配置
3. 提供索引单条消息和批量消息的方法
4. 提供搜索功能，支持关键词、过滤器、排序和分页
5. 可选：提供删除消息的方法

## 2. 技术选型

- 使用 `meilisearch-python` 官方客户端库与 Meilisearch 通信
- 使用 `core.models.MeiliMessageDoc` 作为文档结构
- 使用 `core.config_manager.ConfigManager` 获取 Meilisearch 配置

## 3. 实现步骤

1. **初始化**:
   - 初始化 Meilisearch 客户端
   - 配置连接参数（host, api_key）
   - 获取或创建指定索引

2. **索引配置**:
   - 根据 FOLLOWME.md 中定义的配置设置索引属性
   - 包括 searchableAttributes, filterableAttributes, sortableAttributes, rankingRules 等

3. **索引方法**:
   - 单条消息索引方法
   - 批量消息索引方法
   - 可选：删除消息方法

4. **搜索方法**:
   - 支持基本关键词搜索
   - 支持过滤条件（如按 chat_id, chat_type, sender_id, date 过滤）
   - 支持排序（主要是按 date 排序）
   - 支持分页
   
5. **集成测试**:
   - 测试 Meilisearch 连接
   - 测试索引配置
   - 测试单条和批量索引消息
   - 测试搜索功能（关键词、过滤器、排序、分页）
   - 测试可选的删除功能

## 4. 接口设计

```python
class MeiliSearchService:
    def __init__(self, host: str, api_key: Optional[str] = None, index_name: str = "telegram_messages") -> None:
        """初始化 Meilisearch 客户端"""
        pass
        
    def ensure_index_setup(self) -> None:
        """确保索引存在并正确配置"""
        pass
        
    def index_message(self, message_doc: MeiliMessageDoc) -> dict:
        """索引单条消息"""
        pass
        
    def index_messages_bulk(self, message_docs: List[MeiliMessageDoc]) -> List[dict]:
        """批量索引消息"""
        pass
        
    def search(self, query: str, filters: Optional[str] = None, sort: Optional[List[str]] = None, 
               page: int = 1, hits_per_page: int = 10) -> dict:
        """搜索消息"""
        pass
        
    def delete_message(self, document_id: str) -> dict:
        """删除单条消息（可选实现）"""
        pass
```

## 5. 实现完成情况

已完成 `core/meilisearch_service.py` 文件的实现，包括：

1. MeiliSearchService 类的基本结构
2. 初始化方法，连接到 Meilisearch 服务
3. ensure_index_setup 方法，确保索引存在并配置正确
4. index_message 方法，索引单条消息
5. index_messages_bulk 方法，批量索引消息
6. search 方法，搜索消息，支持过滤和排序
7. delete_message 方法，删除消息
8. 额外添加了 update_stop_words 和 update_synonyms 方法，用于配置停用词和同义词

## 6. 集成测试设计

为了测试 `MeiliSearchService` 类的功能，我创建了集成测试文件 `tests/integration/test_meilisearch_service.py`。这些测试需要一个运行中的 Meilisearch 实例。

### 测试环境设置

1. 使用 Docker Compose 启动的 Meilisearch 实例进行测试
2. 使用唯一的索引名，避免与生产环境冲突
3. 在测试前后清理测试数据

### 测试用例

1. **测试连接与索引设置**
   - 测试能否成功连接到 Meilisearch
   - 测试索引是否正确创建
   - 测试索引配置是否符合预期

2. **测试消息索引**
   - 测试索引单条消息
   - 测试批量索引多条消息
   - 测试索引后能否通过 ID 获取文档

3. **测试搜索功能**
   - 测试基本关键词搜索
   - 测试带过滤条件的搜索
   - 测试带排序的搜索
   - 测试分页功能

4. **测试删除功能**
   - 测试删除单条消息
   - 测试删除后文档是否确实不存在

## 7. 实现细节与注意事项

### 7.1 搜索特性的实现

`search` 方法实现了全面的搜索能力，支持：

1. **关键词搜索**：通过 `query` 参数，用户可以输入任意关键词
2. **过滤**：通过 `filters` 参数，使用 Meilisearch 的过滤字符串语法
   - 例如：`"chat_id = 12345 AND date > 1672531200"`
3. **排序**：通过 `sort` 参数，支持按任意可排序字段升序或降序排序
   - 例如：`["date:desc"]` 按时间从新到旧排序
4. **分页**：通过 `page` 和 `hits_per_page` 参数，支持分页加载结果

### 7.2 索引配置

遵循了 FOLLOWME.md 中 4.2 节的要求，配置了：

1. **searchableAttributes**: ["text", "sender_name", "chat_title"]
   - 其中 "text" 优先级最高（列表中的第一个元素自动拥有最高优先级）
2. **filterableAttributes**: ["chat_id", "chat_type", "sender_id", "date"]
3. **sortableAttributes**: ["date"]
4. **rankingRules**: ["words", "typo", "proximity", "attribute", "sort", "exactness"]
   - 使用了 Meilisearch 的默认规则，这些规则对中文搜索较为友好

### 7.3 停用词和同义词

额外实现了 `update_stop_words` 和 `update_synonyms` 方法，允许用户配置：

1. **停用词**：可以设置中文常见的停用词，如"的"、"了"、"在"等，提高搜索质量
2. **同义词**：可以设置同义词映射，如 "大学" -> ["高校", "学府"]，提高搜索召回率

### 7.4 集成测试中的一些技巧

1. **随机测试数据**：使用随机生成的数据，确保测试的多样性和可重复性
2. **唯一索引名**：为每次测试运行使用唯一的索引名，避免测试之间相互干扰
3. **等待索引完成**：在索引操作后添加短暂等待，确保 Meilisearch 完成索引
4. **详细断言**：测试中使用详细的断言消息，便于理解测试失败原因

## 8. 遇到的问题及解决方案

### 8.1 Meilisearch API 的异步特性

**问题**：Meilisearch 的索引和删除操作是异步的，API 返回任务信息而非立即结果

**解决方案**：
- 在测试中添加短暂等待（`time.sleep(1)`），确保操作完成
- 实际生产环境中可以使用 `client.get_task(task_uid)` 监控任务状态

### 8.2 排序和过滤语法

**问题**：Meilisearch 的排序和过滤语法比较特殊，需要正确构造

**解决方案**：
- 排序使用 `["field:asc"]` 或 `["field:desc"]` 格式
- 过滤使用 Meilisearch 专有的字符串语法，如 `"field = value AND another > 123"`
- 在代码注释和文档中提供了示例

### 8.3 测试环境隔离

**问题**：确保测试不影响实际生产环境的数据

**解决方案**：
- 使用随机生成的测试索引名
- 在测试类的 `tearDownClass` 方法中删除测试索引
- 隔离测试数据，使用专门的测试用例数据

## 9. 使用说明

在其他模块中使用 `MeiliSearchService` 的示例：

```python
from core.config_manager import ConfigManager
from core.meilisearch_service import MeiliSearchService
from core.models import MeiliMessageDoc

# 初始化配置管理器
config_manager = ConfigManager()

# 从配置获取 Meilisearch 信息
host = config_manager.get_config("MeiliSearch", "HOST", "http://localhost:7700")
api_key = config_manager.get_config("MeiliSearch", "API_KEY")
index_name = config_manager.get_config("MeiliSearch", "INDEX_NAME", "telegram_messages")

# 初始化 MeiliSearchService
search_service = MeiliSearchService(host=host, api_key=api_key, index_name=index_name)

# 创建消息文档
message_doc = MeiliMessageDoc(
    id="12345_67890",
    message_id=67890,
    chat_id=12345,
    chat_title="测试群组",
    chat_type="group",
    sender_id=98765,
    sender_name="测试用户",
    text="这是一条测试消息",
    date=1685123456,
    message_link="https://t.me/c/12345/67890"
)

# 索引消息
result = search_service.index_message(message_doc)
print(f"索引任务ID: {result['taskUid']}")

# 搜索消息
search_results = search_service.search(
    query="测试消息",
    filters="chat_id = 12345",
    sort=["date:desc"],
    page=1,
    hits_per_page=10
)

# 处理搜索结果
print(f"找到约 {search_results['estimatedTotalHits']} 条结果")
for hit in search_results["hits"]:
    print(f"- {hit['sender_name']}: {hit['text']}")
```

## 10. 总结

本次开发完成了 `MeiliSearchService` 类的所有需求，主要包括：

1. 完成了 `core/meilisearch_service.py` 文件的实现，提供了完整的 Meilisearch 交互功能
2. 完成了 `tests/integration/test_meilisearch_service.py` 文件的实现，提供了全面的集成测试
3. 实现了所有必需的方法，包括初始化、索引设置、消息索引、搜索和删除功能
4. 额外实现了停用词和同义词配置方法，增强了搜索功能
5. 采用了最佳实践，如详细的日志记录、类型提示、全面的注释等

`MeiliSearchService` 类提供了完整的 Meilisearch 交互能力，可以在应用程序的其他部分（如 Userbot 和 Search Bot）中使用，实现消息的索引和搜索功能。