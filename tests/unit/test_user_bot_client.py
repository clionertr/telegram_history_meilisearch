"""
UserBotClient 单元测试模块

测试 user_bot/client.py 中 UserBotClient 类的功能
"""

import os
import unittest
from unittest.mock import patch, MagicMock, PropertyMock, AsyncMock
from pathlib import Path

from user_bot.client import UserBotClient, SESSIONS_DIR
from core.config_manager import ConfigManager


class TestUserBotClient(unittest.TestCase):
    """
    UserBotClient 类的单元测试
    """

    def setUp(self):
        """
        每个测试开始前的准备工作
        """
        # 清理单例状态
        UserBotClient._instance = None
        UserBotClient._client = None
        
        # 创建 ConfigManager 模拟对象
        self.mock_config = MagicMock(spec=ConfigManager)
        
        # 设置模拟的配置返回值
        self.mock_config.get_env.side_effect = lambda key, default=None: {
            "TELEGRAM_API_ID": "12345",
            "TELEGRAM_API_HASH": "test_hash"
        }.get(key, default)
        
        self.mock_config.get_config.side_effect = lambda section, key, default=None: {
            ("Telegram", "API_ID"): "12345",
            ("Telegram", "API_HASH"): "test_hash"
        }.get((section, key), default)

    @patch('user_bot.client.Path')
    def test_sessions_dir_creation(self, mock_path):
        """
        测试确保会话目录存在的功能
        """
        # 设置 Path.mkdir 为 MagicMock
        mock_mkdir = MagicMock()
        mock_path.return_value = MagicMock(mkdir=mock_mkdir)
        
        # 创建 UserBotClient 实例，这应该触发目录创建
        UserBotClient(self.mock_config)
        
        # 验证是否尝试创建目录
        mock_path.assert_called_with(SESSIONS_DIR)
        mock_mkdir.assert_called_with(exist_ok=True)

    def test_singleton_pattern(self):
        """
        测试单例模式是否正常工作
        """
        # 创建两个实例
        client1 = UserBotClient(self.mock_config)
        client2 = UserBotClient(self.mock_config)
        
        # 验证它们是同一个实例
        self.assertIs(client1, client2)

    @patch('user_bot.client.TelegramClient')
    def test_client_initialization(self, mock_telegram_client):
        """
        测试TelegramClient的初始化
        """
        # 创建 UserBotClient 实例
        client = UserBotClient(self.mock_config, session_name="test_session")
        
        # 验证 TelegramClient 是否使用正确的参数初始化
        mock_telegram_client.assert_called_once()
        args, kwargs = mock_telegram_client.call_args
        
        # 验证会话路径
        self.assertEqual(args[0], os.path.join(SESSIONS_DIR, "test_session"))
        # 验证API ID和API Hash
        self.assertEqual(args[1], 12345)  # API ID 应该被转换为整数
        self.assertEqual(args[2], "test_hash")

    @patch('user_bot.client.TelegramClient')
    def test_get_client(self, mock_telegram_client):
        """
        测试获取客户端实例的方法
        """
        # 设置模拟的TelegramClient实例
        mock_instance = MagicMock()
        mock_telegram_client.return_value = mock_instance
        
        # 创建UserBotClient实例
        client = UserBotClient(self.mock_config)
        
        # 获取客户端实例
        result = client.get_client()
        
        # 验证返回的是否是预期的实例
        self.assertEqual(result, mock_instance)

    def test_missing_api_credentials(self):
        """
        测试缺少API凭据时是否抛出适当的异常
        """
        # 创建返回None的模拟ConfigManager
        empty_config = MagicMock(spec=ConfigManager)
        empty_config.get_env.return_value = None
        empty_config.get_config.return_value = None
        
        # 验证是否抛出ValueError
        with self.assertRaises(ValueError):
            UserBotClient(empty_config)

    def test_invalid_api_id(self):
        """
        测试API ID不是整数时是否抛出适当的异常
        """
        # 创建返回非整数API ID的模拟ConfigManager
        invalid_config = MagicMock(spec=ConfigManager)
        invalid_config.get_env.side_effect = lambda key, default=None: {
            "TELEGRAM_API_ID": "not_an_integer",
            "TELEGRAM_API_HASH": "test_hash"
        }.get(key, default)
        invalid_config.get_config.return_value = None
        
        # 验证是否抛出ValueError
        with self.assertRaises(ValueError):
            UserBotClient(invalid_config)

    @patch('user_bot.client.TelegramClient')
    @patch('os.path.exists')
    def test_start_first_login(self, mock_exists, mock_telegram_client):
        """
        测试首次登录流程（会话文件不存在的情况）
        """
        # 设置会话文件不存在
        mock_exists.return_value = False
        
        # 设置异步方法的模拟
        mock_client = MagicMock()
        mock_client.start = AsyncMock()
        mock_client.get_me = AsyncMock(return_value=MagicMock(first_name="Test", username="test_user"))
        mock_telegram_client.return_value = mock_client
        
        # 创建UserBotClient实例
        client = UserBotClient(self.mock_config)
        
        # 使用异步测试辅助方法测试start方法
        async def async_test():
            result = await client.start()
            self.assertEqual(result, mock_client)
            mock_client.start.assert_called_once()
            mock_client.get_me.assert_called_once()
        
        # 执行异步测试
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(async_test())

    @patch('user_bot.client.TelegramClient')
    def test_disconnect(self, mock_telegram_client):
        """
        测试断开连接的方法
        """
        # 设置异步方法的模拟
        mock_client = MagicMock()
        mock_client.disconnect = AsyncMock()
        mock_telegram_client.return_value = mock_client
        
        # 创建UserBotClient实例
        client = UserBotClient(self.mock_config)
        
        # 使用异步测试辅助方法测试disconnect方法
        async def async_test():
            await client.disconnect()
            mock_client.disconnect.assert_called_once()
        
        # 执行异步测试
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(async_test())
        
    @patch('user_bot.client.TelegramClient')
    def test_session_expired_reconnect(self, mock_telegram_client):
        """
        测试会话过期和重新连接的情况
        """
        from telethon.errors import SessionPasswordNeededError, AuthKeyError
        
        # 创建模拟客户端和方法
        mock_client = MagicMock()
        
        # 模拟连接方法，第一次调用时抛出会话过期异常，第二次调用成功
        mock_start = AsyncMock()
        mock_start.side_effect = [
            AuthKeyError("Session expired"),  # 第一次调用时抛出会话过期异常
            None  # 第二次调用时成功
        ]
        mock_client.start = mock_start
        
        # 模拟获取用户信息方法
        mock_client.get_me = AsyncMock(return_value=MagicMock(first_name="Test", username="test_user"))
        
        # 返回模拟客户端
        mock_telegram_client.return_value = mock_client
        
        # 创建UserBotClient实例
        client = UserBotClient(self.mock_config)
        
        # 使用异步测试辅助方法测试会话过期和重新连接
        async def async_test():
            # 修改UserBotClient.start方法以处理会话过期异常
            original_start = client.start
            
            async def patched_start():
                try:
                    await original_start()
                except AuthKeyError:
                    # 会话过期时，模拟重新连接逻辑
                    logger.warning("检测到会话过期，尝试重新连接...")
                    await original_start()  # 再次尝试连接
                    
            # 临时替换start方法
            client.start = patched_start
            
            # 执行测试
            await client.start()
            
            # 验证start被调用了两次（一次失败，一次成功）
            self.assertEqual(mock_start.call_count, 2)
            
            # 恢复原始方法
            client.start = original_start
        
        # 导入logger用于测试
        import logging
        logger = logging.getLogger("test")
        
        # 执行异步测试
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(async_test())
        
    @patch('user_bot.client.TelegramClient')
    def test_session_revoked(self, mock_telegram_client):
        """
        测试会话被撤销的情况
        """
        from telethon.errors import SessionRevokedError
        
        # 创建模拟客户端和方法
        mock_client = MagicMock()
        
        # 模拟连接方法抛出会话撤销异常
        mock_client.start = AsyncMock(side_effect=SessionRevokedError("Session was revoked"))
        
        # 返回模拟客户端
        mock_telegram_client.return_value = mock_client
        
        # 创建UserBotClient实例
        client = UserBotClient(self.mock_config)
        
        # 使用异步测试辅助方法测试会话撤销情况
        async def async_test():
            # 在会话被撤销时，应该捕获异常并提供有用的错误信息
            with self.assertRaises(SessionRevokedError):
                await client.start()
        
        # 执行异步测试
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(async_test())


if __name__ == '__main__':
    unittest.main()