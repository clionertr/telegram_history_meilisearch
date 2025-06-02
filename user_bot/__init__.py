"""
UserBot模块初始化文件

提供全局的user_bot_client实例，供API路由使用。
"""

from .client import UserBotClient

# 创建全局UserBotClient实例
# 使用单例模式，确保整个应用只有一个实例
user_bot_client = UserBotClient()

# 导出主要组件
__all__ = ['UserBotClient', 'user_bot_client']
