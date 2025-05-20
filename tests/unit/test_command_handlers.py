"""
command_handlers.py 的单元测试

此模块测试 search_bot.command_handlers 中的函数和类，主要测试：
1. 高级搜索语法解析 (_parse_advanced_syntax)
2. Meilisearch 过滤条件构建 (_build_meilisearch_filters)
3. 管理员权限检查 (is_admin)
4. 各个命令处理函数的基本功能
"""

import unittest
from unittest import mock
import datetime
import re
from typing import Dict, Any, Tuple, List

from telethon import events
from telethon.tl.types import User, Chat, Message

from search_bot.command_handlers import CommandHandlers


class TestParseAdvancedSyntax(unittest.TestCase):
    """测试高级搜索语法解析功能"""

    def setUp(self):
        """设置测试环境"""
        # 创建 CommandHandlers 实例，但 mock 所有依赖
        self.client_mock = mock.MagicMock()
        self.meilisearch_service_mock = mock.MagicMock()
        self.config_manager_mock = mock.MagicMock()
        
        self.handler = CommandHandlers(
            client=self.client_mock,
            meilisearch_service=self.meilisearch_service_mock,
            config_manager=self.config_manager_mock,
            admin_ids=[123456]
        )

    def test_parse_simple_query(self):
        """测试简单查询，没有高级语法"""
        query = "python 教程"
        parsed_query, filters = self.handler._parse_advanced_syntax(query)
        
        self.assertEqual(parsed_query, "python 教程")
        self.assertEqual(filters, {})

    def test_parse_type_filter(self):
        """测试类型过滤语法 type:xxx"""
        # 测试有效的类型过滤
        for chat_type in ['user', 'group', 'channel']:
            query = f"python 教程 type:{chat_type}"
            parsed_query, filters = self.handler._parse_advanced_syntax(query)
            
            self.assertEqual(parsed_query, "python 教程")
            self.assertIn('chat_type', filters)
            self.assertEqual(filters['chat_type'], chat_type)
        
        # 测试无效的类型过滤
        query = "python 教程 type:invalid"
        parsed_query, filters = self.handler._parse_advanced_syntax(query)
        
        self.assertEqual(parsed_query, "python 教程 type:invalid")
        self.assertEqual(filters, {})

    def test_parse_date_filter(self):
        """测试日期过滤语法 date:xxx_yyy"""
        # 测试完整日期范围
        query = "python 教程 date:2023-01-01_2023-12-31"
        parsed_query, filters = self.handler._parse_advanced_syntax(query)
        
        self.assertEqual(parsed_query, "python 教程")
        self.assertIn('date_range', filters)
        self.assertIn('start', filters['date_range'])
        self.assertIn('end', filters['date_range'])
        
        # 验证时间戳转换正确性
        start_date = datetime.datetime.strptime("2023-01-01", "%Y-%m-%d")
        start_timestamp = int(start_date.timestamp())
        self.assertEqual(filters['date_range']['start'], start_timestamp)
        
        end_date = datetime.datetime.strptime("2023-12-31 23:59:59", "%Y-%m-%d %H:%M:%S")
        end_timestamp = int(end_date.timestamp())
        self.assertEqual(filters['date_range']['end'], end_timestamp)
        
        # 测试只有开始日期
        query = "python 教程 date:2023-01-01"
        parsed_query, filters = self.handler._parse_advanced_syntax(query)
        
        self.assertEqual(parsed_query, "python 教程")
        self.assertIn('date_range', filters)

    def test_parse_combined_filters(self):
        """测试组合多个过滤条件"""
        query = "python 教程 type:group date:2023-01-01_2023-12-31"
        parsed_query, filters = self.handler._parse_advanced_syntax(query)
        
        self.assertEqual(parsed_query, "python 教程")
        self.assertIn('chat_type', filters)
        self.assertEqual(filters['chat_type'], 'group')
        self.assertIn('date_range', filters)

    def test_parse_with_exact_phrase(self):
        """测试包含精确短语的查询（引号内容）"""
        # 注意：当前实现没有特别处理引号，这是一个简单测试
        query = '"python 教程" type:group'
        parsed_query, filters = self.handler._parse_advanced_syntax(query)
        
        self.assertEqual(parsed_query, '"python 教程"')
        self.assertIn('chat_type', filters)
        self.assertEqual(filters['chat_type'], 'group')


class TestBuildMeilisearchFilters(unittest.TestCase):
    """测试 Meilisearch 过滤条件构建功能"""

    def setUp(self):
        """设置测试环境"""
        # 创建 CommandHandlers 实例，但 mock 所有依赖
        self.client_mock = mock.MagicMock()
        self.meilisearch_service_mock = mock.MagicMock()
        self.config_manager_mock = mock.MagicMock()
        
        self.handler = CommandHandlers(
            client=self.client_mock,
            meilisearch_service=self.meilisearch_service_mock,
            config_manager=self.config_manager_mock,
            admin_ids=[123456]
        )

    def test_build_empty_filters(self):
        """测试空过滤条件"""
        filters_dict = {}
        filter_string = self.handler._build_meilisearch_filters(filters_dict)
        
        self.assertIsNone(filter_string)

    def test_build_chat_type_filter(self):
        """测试聊天类型过滤条件"""
        filters_dict = {'chat_type': 'group'}
        filter_string = self.handler._build_meilisearch_filters(filters_dict)
        
        self.assertEqual(filter_string, "chat_type = 'group'")

    def test_build_date_range_filter(self):
        """测试日期范围过滤条件"""
        filters_dict = {
            'date_range': {
                'start': 1672531200,  # 2023-01-01 00:00:00
                'end': 1704067199     # 2023-12-31 23:59:59
            }
        }
        filter_string = self.handler._build_meilisearch_filters(filters_dict)
        
        self.assertEqual(filter_string, "date >= 1672531200 AND date <= 1704067199")

    def test_build_combined_filters(self):
        """测试组合过滤条件"""
        filters_dict = {
            'chat_type': 'group',
            'date_range': {
                'start': 1672531200,  # 2023-01-01 00:00:00
                'end': 1704067199     # 2023-12-31 23:59:59
            }
        }
        filter_string = self.handler._build_meilisearch_filters(filters_dict)
        
        self.assertTrue("chat_type = 'group'" in filter_string)
        self.assertTrue("date >= 1672531200 AND date <= 1704067199" in filter_string)
        self.assertTrue(" AND " in filter_string)


class TestAdminCheck(unittest.TestCase):
    """测试管理员权限检查功能"""

    def setUp(self):
        """设置测试环境"""
        # 创建 CommandHandlers 实例，但 mock 所有依赖
        self.client_mock = mock.MagicMock()
        self.meilisearch_service_mock = mock.MagicMock()
        self.config_manager_mock = mock.MagicMock()
        
        self.admin_ids = [123456, 789012]
        self.handler = CommandHandlers(
            client=self.client_mock,
            meilisearch_service=self.meilisearch_service_mock,
            config_manager=self.config_manager_mock,
            admin_ids=self.admin_ids
        )

    async def test_is_admin_with_admin_user(self):
        """测试管理员用户权限检查"""
        # 模拟事件和发送者
        event_mock = mock.MagicMock()
        user_mock = mock.MagicMock(spec=User)
        user_mock.id = self.admin_ids[0]
        
        # 模拟 get_sender() 返回管理员用户
        event_mock.get_sender = mock.AsyncMock(return_value=user_mock)
        
        # 测试 is_admin 方法
        is_admin = await self.handler.is_admin(event_mock)
        
        self.assertTrue(is_admin)
        event_mock.get_sender.assert_called_once()

    async def test_is_admin_with_non_admin_user(self):
        """测试非管理员用户权限检查"""
        # 模拟事件和发送者
        event_mock = mock.MagicMock()
        user_mock = mock.MagicMock(spec=User)
        user_mock.id = 999999  # 非管理员 ID
        
        # 模拟 get_sender() 返回非管理员用户
        event_mock.get_sender = mock.AsyncMock(return_value=user_mock)
        
        # 测试 is_admin 方法
        is_admin = await self.handler.is_admin(event_mock)
        
        self.assertFalse(is_admin)
        event_mock.get_sender.assert_called_once()


class TestCommandHandlers(unittest.TestCase):
    """测试命令处理函数基本功能"""

    def setUp(self):
        """设置测试环境"""
        # 创建 CommandHandlers 实例，但 mock 所有依赖
        self.client_mock = mock.MagicMock()
        self.meilisearch_service_mock = mock.MagicMock()
        self.config_manager_mock = mock.MagicMock()
        
        self.admin_ids = [123456]
        self.handler = CommandHandlers(
            client=self.client_mock,
            meilisearch_service=self.meilisearch_service_mock,
            config_manager=self.config_manager_mock,
            admin_ids=self.admin_ids
        )

    async def test_start_command(self):
        """测试 start 命令处理函数"""
        # 模拟事件和发送者
        event_mock = mock.MagicMock()
        user_mock = mock.MagicMock(spec=User)
        user_mock.id = 999999
        user_mock.first_name = "Test User"
        
        # 模拟 get_sender() 返回用户
        event_mock.get_sender = mock.AsyncMock(return_value=user_mock)
        
        # 模拟 respond() 方法
        event_mock.respond = mock.AsyncMock()
        
        # 执行 start_command
        await self.handler.start_command(event_mock)
        
        # 验证 respond() 被调用
        event_mock.respond.assert_called_once()
        # 验证欢迎消息包含用户名
        self.assertTrue("Test User" in event_mock.respond.call_args[0][0])

    async def test_help_command(self):
        """测试 help 命令处理函数"""
        # 模拟事件和发送者
        event_mock = mock.MagicMock()
        user_mock = mock.MagicMock(spec=User)
        user_mock.id = 999999
        
        # 模拟 get_sender() 返回用户
        event_mock.get_sender = mock.AsyncMock(return_value=user_mock)
        
        # 模拟 respond() 方法
        event_mock.respond = mock.AsyncMock()
        
        # 使用 patch 模拟 format_help_message
        with mock.patch('search_bot.command_handlers.format_help_message', return_value="测试帮助消息"):
            # 执行 help_command
            await self.handler.help_command(event_mock)
            
            # 验证 respond() 被调用，并且使用了 format_help_message 的返回值
            event_mock.respond.assert_called_once_with("测试帮助消息")

    async def test_search_command_with_empty_query(self):
        """测试 search 命令处理函数（空查询）"""
        # 模拟事件和消息
        event_mock = mock.MagicMock()
        message_mock = mock.MagicMock(spec=Message)
        message_mock.text = "/search"
        event_mock.message = message_mock
        
        # 模拟 respond() 方法
        event_mock.respond = mock.AsyncMock()
        
        # 执行 search_command
        await self.handler.search_command(event_mock)
        
        # 验证提示消息被发送
        event_mock.respond.assert_called_once()
        self.assertTrue("请提供搜索关键词" in event_mock.respond.call_args[0][0])

    async def test_search_command_with_valid_query(self):
        """测试 search 命令处理函数（有效查询）"""
        # 模拟事件和消息
        event_mock = mock.MagicMock()
        message_mock = mock.MagicMock(spec=Message)
        message_mock.text = "/search python 教程"
        event_mock.message = message_mock
        
        # 模拟用户
        user_mock = mock.MagicMock(spec=User)
        user_mock.id = 999999
        event_mock.get_sender = mock.AsyncMock(return_value=user_mock)
        
        # 模拟 respond() 方法
        event_mock.respond = mock.AsyncMock()
        
        # 模拟 meilisearch_service.search() 方法
        search_result = {
            'hits': [{'id': '123_456', 'text': 'python 教程示例'}],
            'estimatedTotalHits': 1,
            'query': 'python 教程'
        }
        self.meilisearch_service_mock.search.return_value = search_result
        
        # 模拟 format_search_results
        formatted_result = "格式化的搜索结果"
        buttons = [[mock.MagicMock()]]
        
        with mock.patch('search_bot.command_handlers.format_search_results', return_value=(formatted_result, buttons)):
            # 执行 search_command
            await self.handler.search_command(event_mock)
            
            # 验证 meilisearch_service.search 被调用
            self.meilisearch_service_mock.search.assert_called_once()
            # 验证搜索结果被发送
            event_mock.respond.assert_called()
            # 验证最后一次调用发送了格式化结果
            event_mock.respond.assert_any_call(formatted_result, buttons=buttons)

    async def test_add_whitelist_command_with_non_admin(self):
        """测试 add_whitelist 命令（非管理员）"""
        # 模拟事件和消息
        event_mock = mock.MagicMock()
        message_mock = mock.MagicMock(spec=Message)
        message_mock.text = "/add_whitelist -1001234567890"
        event_mock.message = message_mock
        
        # 模拟用户（非管理员）
        user_mock = mock.MagicMock(spec=User)
        user_mock.id = 999999  # 非管理员 ID
        event_mock.get_sender = mock.AsyncMock(return_value=user_mock)
        
        # 模拟 respond() 方法
        event_mock.respond = mock.AsyncMock()
        
        # 修改 is_admin 方法以返回 False
        self.handler.is_admin = mock.AsyncMock(return_value=False)
        
        # 执行 add_whitelist_command
        await self.handler.add_whitelist_command(event_mock)
        
        # 验证权限不足消息被发送
        event_mock.respond.assert_called_once()
        self.assertTrue("需要管理员权限" in event_mock.respond.call_args[0][0])
        
        # 验证 add_to_whitelist 没有被调用
        self.config_manager_mock.add_to_whitelist.assert_not_called()

    async def test_add_whitelist_command_with_admin(self):
        """测试 add_whitelist 命令（管理员）"""
        # 模拟事件和消息
        event_mock = mock.MagicMock()
        message_mock = mock.MagicMock(spec=Message)
        message_mock.text = "/add_whitelist -1001234567890"
        event_mock.message = message_mock
        
        # 模拟用户（管理员）
        user_mock = mock.MagicMock(spec=User)
        user_mock.id = self.admin_ids[0]  # 管理员 ID
        event_mock.get_sender = mock.AsyncMock(return_value=user_mock)
        
        # 模拟 respond() 方法
        event_mock.respond = mock.AsyncMock()
        
        # 修改 is_admin 方法以返回 True
        self.handler.is_admin = mock.AsyncMock(return_value=True)
        
        # 模拟 add_to_whitelist 方法
        self.config_manager_mock.add_to_whitelist.return_value = True
        
        # 执行 add_whitelist_command
        await self.handler.add_whitelist_command(event_mock)
        
        # 验证 add_to_whitelist 被调用
        self.config_manager_mock.add_to_whitelist.assert_called_once_with(-1001234567890)
        
        # 验证成功消息被发送
        event_mock.respond.assert_called_once()
        self.assertTrue("成功" in event_mock.respond.call_args[0][0])

    async def test_remove_whitelist_command(self):
        """测试 remove_whitelist 命令"""
        # 模拟事件和消息
        event_mock = mock.MagicMock()
        message_mock = mock.MagicMock(spec=Message)
        message_mock.text = "/remove_whitelist -1001234567890"
        event_mock.message = message_mock
        
        # 模拟用户（管理员）
        user_mock = mock.MagicMock(spec=User)
        user_mock.id = self.admin_ids[0]  # 管理员 ID
        event_mock.get_sender = mock.AsyncMock(return_value=user_mock)
        
        # 模拟 respond() 方法
        event_mock.respond = mock.AsyncMock()
        
        # 修改 is_admin 方法以返回 True
        self.handler.is_admin = mock.AsyncMock(return_value=True)
        
        # 模拟 remove_from_whitelist 方法
        self.config_manager_mock.remove_from_whitelist.return_value = True
        
        # 执行 remove_whitelist_command
        await self.handler.remove_whitelist_command(event_mock)
        
        # 验证 remove_from_whitelist 被调用
        self.config_manager_mock.remove_from_whitelist.assert_called_once_with(-1001234567890)
        
        # 验证成功消息被发送
        event_mock.respond.assert_called_once()
        self.assertTrue("成功" in event_mock.respond.call_args[0][0])


if __name__ == '__main__':
    unittest.main()