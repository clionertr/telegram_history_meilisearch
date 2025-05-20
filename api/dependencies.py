"""
API 依赖模块

此模块提供用于 FastAPI 依赖注入的函数，主要包括：
1. MeilisearchService 实例的工厂函数
2. 其他可能需要的依赖项
"""

import logging
import os
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv

from core.meilisearch_service import MeiliSearchService
from core.config_manager import ConfigManager


# 加载环境变量（确保配置可用）
load_dotenv()


@lru_cache()
def get_meilisearch_service() -> MeiliSearchService:
    """
    获取 MeilisearchService 实例的工厂函数
    
    使用 lru_cache 装饰器确保只创建一个实例（单例模式）
    
    Returns:
        配置好的 MeilisearchService 实例
    """
    logger = logging.getLogger(__name__)
    
    # 从环境变量获取 Meilisearch 配置
    host = os.getenv("MEILISEARCH_HOST", "http://localhost:7700")
    api_key = os.getenv("MEILISEARCH_API_KEY", None)
    index_name = os.getenv("MEILISEARCH_INDEX", "telegram_messages")
    
    logger.info(f"创建 MeilisearchService 实例，连接到 {host}")
    
    # 创建并返回 MeilisearchService 实例
    return MeiliSearchService(
        host=host,
        api_key=api_key,
        index_name=index_name
    )


@lru_cache()
def get_config_manager() -> ConfigManager:
    """
    获取 ConfigManager 实例的工厂函数
    
    使用 lru_cache 装饰器确保只创建一个实例（单例模式）
    
    Returns:
        配置好的 ConfigManager 实例
    """
    logger = logging.getLogger(__name__)
    
    # 配置文件路径
    env_path = os.getenv("ENV_PATH", ".env")
    config_path = os.getenv("CONFIG_PATH", "config.ini")
    whitelist_path = os.getenv("WHITELIST_PATH", "whitelist.json")
    
    logger.info(f"创建 ConfigManager 实例，使用配置文件 {config_path} 和白名单文件 {whitelist_path}")
    
    # 创建并返回 ConfigManager 实例
    return ConfigManager(
        env_path=env_path,
        config_path=config_path,
        whitelist_path=whitelist_path,
        create_if_not_exists=True
    )