# Search Bot 缓存功能实现日志

## 任务目标
为 Search Bot 实现搜索结果缓存机制，优化用户体验和响应速度。

## 步骤 1: 更新配置文件和依赖

*   **`config.ini`**:
    *   在 `[Telegram]` 和 `[General]` 之间添加了 `[SearchBot]` section。
    *   添加了以下配置项：
        *   `enable_search_cache = true`
        *   `search_cache_ttl_seconds = 7200`
        *   `search_cache_initial_fetch_count = 15`
*   **`requirements.txt`**:
    *   添加了 `cachetools` 依赖。

## 步骤 2: 更新 `core/config_manager.py`

*   在 `ConfigManager` 类中为新的搜索缓存配置添加了属性和默认值。
*   创建了私有方法 `_load_search_bot_config()` 来从 `config.ini` 读取 `[SearchBot]` section 的配置，并处理了配置项不存在时使用默认值的情况。
*   在 `__init__` 方法中调用了 `_load_search_bot_config()`。
*   为每个新的缓存配置项添加了公共的 getter 方法:
    *   `get_search_cache_enabled() -> bool`
    *   `get_search_cache_ttl() -> int`
    *   `get_search_cache_initial_fetch_count() -> int`
*   更新了 `create_default_config()` 方法，以在生成默认 `config.ini` 文件时包含 `[SearchBot]` section 及其默认值。
*   更新了 `create_example_files()` 方法，以在生成 `config.ini.example` 文件时包含 `[SearchBot]` section 及其说明。

## 步骤 3: 实现内存缓存服务 (`search_bot/cache_service.py`)

*   创建了新文件 `search_bot/cache_service.py`。
*   定义了 `SearchCacheService` 类：
    *   `__init__(self, config_manager: ConfigManager, maxsize: int = 200)`:
        *   初始化 `TTLCache` 实例，使用从 `config_manager` 获取的 `ttl` 和 `initial_fetch_count`，以及固定的 `maxsize` (例如 200)。
        *   如果缓存被禁用，则 `self.cache` 为 `None`。
    *   `_generate_cache_key(self, query: str, filters: Optional[Dict[str, Any]] = None) -> str`:
        *   根据搜索查询和过滤器（排序后）生成 MD5 哈希作为缓存键，确保一致性。
    *   `get_from_cache(self, query: str, filters: Optional[Dict[str, Any]] = None) -> Optional[CacheEntry]`:
        *   如果缓存启用，则生成键并尝试从 `TTLCache` 获取条目。
        *   返回 `CacheEntry` (包含 `data`, `is_partial`, `total_hits`, `full_fetch_initiated_timestamp`) 或 `None`。
    *   `store_in_cache(self, query: str, filters: Optional[Dict[str, Any]], data: Any, total_hits: int, is_partial: bool = True, full_fetch_initiated_timestamp: Optional[float] = None) -> None`:
        *   如果缓存启用，则生成键并将 `CacheEntry` 存入 `TTLCache`。
    *   `update_cache_to_complete(self, query: str, filters: Optional[Dict[str, Any]], full_data: Any, total_hits: int) -> None`:
        *   如果缓存启用，则生成键并用完整的搜索结果更新缓存条目，将 `is_partial` 标记为 `False`，并将 `full_fetch_initiated_timestamp` 设为 `None`。
    *   `get_initial_fetch_count(self) -> int`: 返回配置的初始获取数量。
    *   `is_cache_enabled(self) -> bool`: 检查缓存是否启用。
    *   `clear_cache(self) -> None`: 清空缓存。
    *   `get_cache_stats(self) -> Dict[str, Any]`: 获取缓存统计信息。
*   定义了 `CacheEntry` 类型别名 `Tuple[Any, bool, Optional[int], Optional[float]]` 来表示缓存中存储的元组结构。

## 步骤 4: 修改搜索工作流程 (`search_bot/command_handlers.py`)

### 步骤 4.1: 初始化服务和添加管理员命令

*   在 `CommandHandlers.__init__` 中:
    *   导入了 `SearchCacheService` 和 `time`。
    *   创建了 `self.cache_service = SearchCacheService(config_manager)` 实例。
    *   添加了 `self.active_full_fetches: Dict[str, asyncio.Task] = {}` 用于跟踪后台异步获取任务。
*   在 `register_handlers` 方法中注册了新的管理员命令：
    *   `/view_search_config`: 调用 `view_search_config_command`。
    *   `/set_search_config <key> <value>`: 调用 `set_search_config_command`。
    *   `/clear_search_cache`: 调用 `clear_search_cache_command`。
*   在 `_is_plain_text_and_not_command` 中将这些新命令模式加入排除列表。
*   实现了以下新的管理员命令处理方法：
    *   `view_search_config_command(self, event)`: 显示当前搜索缓存配置和状态。
    *   `set_search_config_command(self, event)`:
        *   允许管理员修改 `enable_search_cache`, `search_cache_ttl_seconds`, `search_cache_initial_fetch_count`。
        *   进行输入验证。
        *   更新内存中的 `ConfigParser` 对象。
        *   将更改写回 `config.ini` 文件。
        *   调用 `self.config_manager.load_config()` 和 `self.config_manager._load_search_bot_config()` 来重新加载配置到 `ConfigManager` 实例。
        *   使用更新后的配置重新初始化 `self.cache_service`。
        *   清空 `self.active_full_fetches`。
    *   `clear_search_cache_command(self, event)`: 调用 `self.cache_service.clear_cache()` 并清空 `self.active_full_fetches`。

### 步骤 4.2: 修改 `_perform_search` 集成缓存和异步获取

*   添加了辅助方法 `_get_results_from_meili(...)` 封装对 `meilisearch_service.search` 的调用。
*   添加了异步方法 `_fetch_all_results_async(cache_key, parsed_query, filters_dict, meili_filters, sort_options, total_hits_estimate)`:
    *   此方法在后台运行，用于获取指定查询的全部（或最多1000条）结果。
    *   获取结果后，调用 `self.cache_service.update_cache_to_complete()` 更新缓存。
    *   处理潜在错误，并在完成或失败时从 `self.active_full_fetches` 中移除任务。
*   重构了 `_perform_search(self, event, query: str, page: int = 1, is_direct_search: bool = False)`:
    *   **缓存检查**: 首先尝试从 `self.cache_service.get_from_cache()` 获取数据。
    *   **缓存命中 (完整数据)**: 如果缓存命中且数据是完整的 (`is_partial == False`)，则直接从缓存中提取、分页并格式化结果发送给用户。
    *   **缓存命中 (部分数据)**:
        *   如果请求的页面在已缓存的初始数据范围内，则使用缓存数据。
        *   如果请求页面超出初始范围：
            *   检查 `active_full_fetches` 或 `fetch_ts` (时间戳) 判断后台任务是否仍在进行。
            *   **选择方案 A**: 如果后台任务活跃，则提示用户“正在加载更多结果，请稍候”。
            *   如果后台任务不活跃（可能已完成或失败），则再次检查缓存。如果此时缓存已更新为完整数据，则使用它。
    *   **缓存未命中 / 首次请求 (page == 1)**:
        *   发送“正在搜索”提示。
        *   **阶段一 (初始获取)**: 调用 `_get_results_from_meili()` 获取 `initial_fetch_count` 条结果和总命中数。
        *   将初始结果（可能标记为部分）和总命中数存入缓存 (`self.cache_service.store_in_cache()`)。如果需要完整获取，则记录 `full_fetch_initiated_timestamp`。
        *   格式化并发送初始结果给用户。
        *   **阶段二 (异步完整获取)**: 如果总命中数 > 初始获取数，且缓存启用，并且当前查询没有正在进行的后台任务，则使用 `asyncio.create_task()` 启动 `_fetch_all_results_async`，并将其加入 `self.active_full_fetches`。
    *   **后续页面请求且缓存不足**: 如果是请求后续页面 (`page > 1`) 但缓存中没有足够数据（且异步逻辑判断后仍不足），则直接从 MeiliSearch 获取该特定页面的数据并发送。
    *   错误处理得到加强，以适应更复杂的流程。
*   `search_command` 现在调用 `_perform_search` 时传递 `page=1`。
*   在 `_perform_search` 中记录了关于分页请求超出初始数据范围时的处理方案选择（方案A）。

## 步骤 5: 修改回调查询处理器 (`search_bot/callback_query_handlers.py`)

*   导入了 `base64`, `time` 和 `CommandHandlers` (用于类型提示)。
*   修改了 `CallbackQueryHandlers.__init__` 方法，使其接收 `CommandHandlers` 的实例，并存储它及 `cache_service` 的引用。
*   更新了 `setup_callback_handlers` 辅助函数以传递 `CommandHandlers` 实例。
*   更新了 `register_handlers` 中分页回调的 `pattern` 为 `r"^search_page:(\d+):(.+)$"` 以匹配新的回调数据格式（包含 base64 编码的原始查询）。
*   重写了 `pagination_callback(self, event: CallbackQuery.Event)` 方法：
    *   从回调数据中解析目标页码和 base64 编码的原始查询字符串。
    *   解码原始查询字符串。
    *   使用 `self.command_handler._parse_advanced_syntax()` 和 `self.command_handler._build_meilisearch_filters()` 来获取解析后的查询和 MeiliSearch 过滤器。
    *   **缓存交互逻辑**:
        *   尝试从 `self.cache_service.get_from_cache()` 获取缓存条目。
        *   **缓存命中 (完整数据)**: 从缓存中提取、分页、格式化结果并编辑消息。
        *   **缓存命中 (部分数据)**:
            *   如果请求的页面在已缓存的初始数据范围内，则使用缓存数据。
            *   如果请求页面超出初始范围：
                *   检查 `self.command_handler.active_full_fetches` 或缓存条目中的 `fetch_ts`，判断后台完整获取任务是否仍在进行或最近启动。
                *   **方案 A (与 `_perform_search` 一致)**: 如果后台任务活跃，则通过 `event.answer()` 发送toast提示用户“更多结果加载中，请稍候再试...”。
                *   如果后台任务不活跃，则再次检查缓存（可能已更新为完整数据）。如果完整，则使用它。
        *   **缓存未命中或部分缓存不足**: 如果缓存中没有（或没有足够的）数据来满足分页请求（并且异步获取逻辑判断后仍不足），则直接调用 `self.command_handler._get_results_from_meili()` 从 MeiliSearch 获取该特定页面的数据。
    *   使用 `format_search_results` 时传递 `query_original=original_query`，以确保后续分页按钮能正确生成。
    *   更新了错误处理和用户通知（例如使用 `event.answer()`）。

## 步骤 6: 修改消息格式化器 (`search_bot/message_formatters.py`)

*   导入了 `base64`。
*   修改了 `format_search_results` 函数签名，添加了可选参数 `query_original: Optional[str] = None`。
*   在函数内部：
    *   如果 `query_original` 被提供，则使用它来生成分页按钮的回调数据。此 `query_original` 会被 Base64 编码。
    *   如果 `query_original` 未提供，则回退到使用 `results.get('query', '')`，并记录一个警告，因为这可能导致分页时丢失过滤器。
    *   更新了分页按钮的回调数据格式为 `f"search_page:{page_num}:{encoded_original_query}"`。
    *   消息头部显示的查询词会优先使用 `query_original`（如果它与解析后的查询不同），否则使用解析后的查询。

## 步骤 7: 更新 `search_bot/bot.py`

*   在 `SearchBot` 类的 `register_event_handlers` 方法中，当实例化 `CallbackQueryHandlers` 时，将 `self.command_handlers` (即 `CommandHandlers` 的实例) 传递给其构造函数，替换了之前直接传递 `meilisearch_service` 的做法。
    *   旧代码: `self.callback_query_handlers = CallbackQueryHandlers(client=self.client, meilisearch_service=self.meilisearch_service)`
    *   新代码: `self.callback_query_handlers = CallbackQueryHandlers(client=self.client, command_handler=self.command_handlers)`