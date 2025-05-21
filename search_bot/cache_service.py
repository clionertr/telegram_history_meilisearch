import hashlib
import json
from typing import Optional, Any, Dict, Tuple

from cachetools import TTLCache
from core.config_manager import ConfigManager
import logging

logger = logging.getLogger(__name__)

# 定义缓存中存储的数据结构
# (data, is_partial, total_hits, timestamp_of_full_fetch_start_if_any)
CacheEntry = Tuple[Any, bool, Optional[int], Optional[float]]


class SearchCacheService:
    """
    管理搜索结果缓存的服务。
    """
    def __init__(self, config_manager: ConfigManager, maxsize: int = 200):
        """
        初始化缓存服务。

        Args:
            config_manager: 配置管理器实例。
            maxsize: 缓存的最大条目数。
        """
        self.config = config_manager
        self.cache_enabled = self.config.get_search_cache_enabled()
        self.ttl = self.config.get_search_cache_ttl()
        self.initial_fetch_count = self.config.get_search_cache_initial_fetch_count()

        if self.cache_enabled:
            self.cache: TTLCache[str, CacheEntry] = TTLCache(maxsize=maxsize, ttl=self.ttl)
            logger.info(
                f"搜索缓存已启用。TTL: {self.ttl}s, Maxsize: {maxsize}, Initial Fetch: {self.initial_fetch_count}"
            )
        else:
            self.cache = None # type: ignore
            logger.info("搜索缓存已禁用。")

    def _generate_cache_key(self, query: str, filters: Optional[Dict[str, Any]] = None) -> str:
        """
        根据搜索关键词和过滤器生成唯一的缓存键。
        过滤器需要排序以保证键的一致性。
        """
        key_parts = [query.lower().strip()]
        if filters:
            # 对过滤器按键排序，然后按值排序（如果值是列表，也排序）
            sorted_filters = sorted(filters.items())
            for k, v in sorted_filters:
                if isinstance(v, list):
                    key_parts.append(f"{k}:{','.join(sorted(str(item) for item in v))}")
                else:
                    key_parts.append(f"{k}:{str(v)}")
        
        raw_key = "|".join(key_parts)
        return hashlib.md5(raw_key.encode('utf-8')).hexdigest()

    def get_from_cache(self, query: str, filters: Optional[Dict[str, Any]] = None) -> Optional[CacheEntry]:
        """
        从缓存中获取数据。

        Args:
            query: 搜索查询。
            filters: 应用的过滤器。

        Returns:
            缓存条目 (data, is_partial, total_hits, timestamp_of_full_fetch_start_if_any) 或 None。
        """
        if not self.cache_enabled or self.cache is None:
            return None
        
        cache_key = self._generate_cache_key(query, filters)
        cached_item = self.cache.get(cache_key)
        if cached_item:
            logger.debug(f"缓存命中: key='{cache_key}'")
            # cached_item is (data, is_partial, total_hits, timestamp_of_full_fetch_start_if_any)
            return cached_item
        logger.debug(f"缓存未命中: key='{cache_key}'")
        return None

    def store_in_cache(self, 
                       query: str, 
                       filters: Optional[Dict[str, Any]], 
                       data: Any, 
                       total_hits: int,
                       is_partial: bool = True,
                       full_fetch_initiated_timestamp: Optional[float] = None) -> None:
        """
        将数据存入缓存。

        Args:
            query: 搜索查询。
            filters: 应用的过滤器。
            data: 要缓存的数据 (例如，搜索结果列表)。
            total_hits: MeiliSearch返回的总命中数。
            is_partial: 标记数据是否为部分数据 (初始获取)。默认为 True。
            full_fetch_initiated_timestamp: 如果启动了完整获取，则为启动时间戳。
        """
        if not self.cache_enabled or self.cache is None:
            return

        cache_key = self._generate_cache_key(query, filters)
        # Store: (actual_data, is_partial_flag, total_hits_from_meili, timestamp_of_full_fetch_start_if_any)
        entry: CacheEntry = (data, is_partial, total_hits, full_fetch_initiated_timestamp)
        self.cache[cache_key] = entry
        status = "部分" if is_partial else "完整"
        logger.info(f"结果已存入缓存: key='{cache_key}', 状态='{status}', 条目数={len(data) if isinstance(data, list) else 1}, 总命中数={total_hits}")

    def update_cache_to_complete(self, 
                                 query: str, 
                                 filters: Optional[Dict[str, Any]], 
                                 full_data: Any, 
                                 total_hits: int) -> None:
        """
        当后台异步获取完成后，用完整数据更新缓存。

        Args:
            query: 搜索查询。
            filters: 应用的过滤器。
            full_data: 完整的搜索结果数据。
            total_hits: MeiliSearch返回的总命中数 (应该与初始获取时一致)。
        """
        if not self.cache_enabled or self.cache is None:
            return

        cache_key = self._generate_cache_key(query, filters)
        # Update to: (full_data, False (not partial), total_hits, None (full fetch completed))
        entry: CacheEntry = (full_data, False, total_hits, None)
        self.cache[cache_key] = entry
        logger.info(f"缓存已更新为完整数据: key='{cache_key}', 条目数={len(full_data) if isinstance(full_data, list) else 1}, 总命中数={total_hits}")

    def get_initial_fetch_count(self) -> int:
        """返回配置的初始获取数量"""
        return self.initial_fetch_count

    def is_cache_enabled(self) -> bool:
        """检查缓存是否启用"""
        return self.cache_enabled

    def clear_cache(self) -> None:
        """清空整个缓存"""
        if self.cache_enabled and self.cache:
            self.cache.clear()
            logger.info("搜索缓存已清空。")

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存的统计信息"""
        if self.cache_enabled and self.cache:
            return {
                "currsize": self.cache.currsize,
                "maxsize": self.cache.maxsize,
                "ttl": self.ttl,
                "enabled": True
            }
        return {"enabled": False}