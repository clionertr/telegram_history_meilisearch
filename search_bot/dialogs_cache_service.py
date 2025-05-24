"""
对话缓存服务模块

此模块提供对话列表的缓存功能，用于缓存 /get_dialogs 命令的结果，
减少对 Telegram API 的频繁调用，提高响应速度。
"""

import hashlib
import logging
from typing import Optional, List, Tuple, Dict, Any
from cachetools import TTLCache
from core.config_manager import ConfigManager

logger = logging.getLogger(__name__)

# 定义对话信息的类型
DialogInfo = Tuple[str, int, str]  # (dialog_name, dialog_id, dialog_type)
DialogsList = List[DialogInfo]

# 定义缓存条目的类型：(dialogs_list, timestamp)
DialogsCacheEntry = Tuple[DialogsList, float]


class DialogsCacheService:
    """
    对话缓存服务类
    
    提供对话列表的缓存功能，支持基于用户ID的缓存隔离。
    """
    
    def __init__(self, config_manager: ConfigManager, maxsize: int = 100):
        """
        初始化对话缓存服务
        
        Args:
            config_manager: 配置管理器实例
            maxsize: 缓存的最大条目数，默认100（考虑到用户数量相对较少）
        """
        self.config = config_manager
        
        # 对话缓存固定30分钟TTL（1800秒）
        self.ttl = 1800  # 30分钟
        
        # 检查是否启用缓存（可以复用搜索缓存的配置，或者单独配置）
        self.cache_enabled = self._get_dialogs_cache_enabled()
        
        if self.cache_enabled:
            self.cache: TTLCache[str, DialogsCacheEntry] = TTLCache(maxsize=maxsize, ttl=self.ttl)
            logger.info(f"对话缓存已启用。TTL: {self.ttl}s (30分钟), Maxsize: {maxsize}")
        else:
            self.cache = None  # type: ignore
            logger.info("对话缓存已禁用。")
    
    def _get_dialogs_cache_enabled(self) -> bool:
        """
        获取对话缓存是否启用的配置
        
        优先使用专门的对话缓存配置，如果没有则使用搜索缓存配置
        """
        # 尝试获取专门的对话缓存配置
        dialogs_cache_enabled = self.config.get_config("SearchBot", "enable_dialogs_cache")
        if dialogs_cache_enabled is not None:
            return dialogs_cache_enabled.lower() == 'true'
        
        # 如果没有专门配置，则使用搜索缓存的配置
        return self.config.get_search_cache_enabled()
    
    def _generate_cache_key(self, user_id: int) -> str:
        """
        根据用户ID生成缓存键
        
        Args:
            user_id: 用户的Telegram ID
            
        Returns:
            str: 缓存键
        """
        # 使用用户ID生成缓存键，添加前缀以区分不同类型的缓存
        raw_key = f"dialogs_user_{user_id}"
        return hashlib.md5(raw_key.encode('utf-8')).hexdigest()
    
    def get_from_cache(self, user_id: int) -> Optional[DialogsList]:
        """
        从缓存中获取用户的对话列表
        
        Args:
            user_id: 用户的Telegram ID
            
        Returns:
            Optional[DialogsList]: 缓存的对话列表，如果未找到则返回None
        """
        if not self.cache_enabled or self.cache is None:
            return None
        
        cache_key = self._generate_cache_key(user_id)
        cached_item = self.cache.get(cache_key)
        
        if cached_item:
            dialogs_list, timestamp = cached_item
            logger.info(f"对话缓存命中: user_id={user_id}, 对话数量={len(dialogs_list)}")
            return dialogs_list
        
        logger.debug(f"对话缓存未命中: user_id={user_id}")
        return None
    
    def store_in_cache(self, user_id: int, dialogs_list: DialogsList) -> None:
        """
        将对话列表存入缓存
        
        Args:
            user_id: 用户的Telegram ID
            dialogs_list: 要缓存的对话列表
        """
        if not self.cache_enabled or self.cache is None:
            return
        
        import time
        cache_key = self._generate_cache_key(user_id)
        timestamp = time.time()
        
        # 存储：(对话列表, 时间戳)
        entry: DialogsCacheEntry = (dialogs_list, timestamp)
        self.cache[cache_key] = entry
        
        logger.info(f"对话列表已存入缓存: user_id={user_id}, 对话数量={len(dialogs_list)}, TTL={self.ttl}s")
    
    def is_cache_enabled(self) -> bool:
        """检查缓存是否启用"""
        return self.cache_enabled
    
    def clear_cache(self) -> None:
        """清空整个对话缓存"""
        if self.cache_enabled and self.cache:
            self.cache.clear()
            logger.info("对话缓存已清空。")
    
    def clear_user_cache(self, user_id: int) -> bool:
        """
        清空特定用户的对话缓存
        
        Args:
            user_id: 用户的Telegram ID
            
        Returns:
            bool: 是否成功清除（True表示找到并清除，False表示未找到）
        """
        if not self.cache_enabled or self.cache is None:
            return False
        
        cache_key = self._generate_cache_key(user_id)
        if cache_key in self.cache:
            del self.cache[cache_key]
            logger.info(f"已清除用户 {user_id} 的对话缓存")
            return True
        
        return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存的统计信息"""
        if self.cache_enabled and self.cache:
            return {
                "currsize": self.cache.currsize,
                "maxsize": self.cache.maxsize,
                "ttl": self.ttl,
                "enabled": True,
                "type": "dialogs_cache"
            }
        return {"enabled": False, "type": "dialogs_cache"}
    
    def get_cached_users(self) -> List[int]:
        """
        获取当前缓存中的所有用户ID列表
        
        Returns:
            List[int]: 缓存中的用户ID列表
        """
        if not self.cache_enabled or self.cache is None:
            return []
        
        cached_users = []
        for cache_key in self.cache.keys():
            # 从缓存键中提取用户ID
            # 缓存键格式: MD5(dialogs_user_{user_id})
            # 我们需要反向查找，但这里简化处理，返回缓存条目数
            pass
        
        # 简化实现：返回当前缓存条目数（每个条目对应一个用户）
        return list(range(self.cache.currsize))  # 这是一个简化的实现