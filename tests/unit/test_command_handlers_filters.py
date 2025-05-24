"""
针对 command_handlers.py 中搜索筛选功能的单元测试

此模块专门测试与按消息来源类别和时间段筛选相关的功能：
1. 解析多个类型筛选参数 (type:xxx type:yyy)
2. 构建包含多个聊天类型的 Meilisearch 过滤条件
3. 确保 _get_results_from_meili 正确传递筛选参数
"""

import unittest
from unittest import mock
import datetime
from typing import Dict, Any, List, Optional, Tuple

from search_bot.command_handlers import CommandHandlers


class TestAdvancedSyntaxParsing(unittest.TestCase):
    """测试高级搜索语法解析功能，特别是多类型筛选"""

    def setUp(self):
        """设置测试环境"""
        self.client_mock = mock.MagicMock()
        self.meilisearch_service_mock = mock.MagicMock()
        self.config_manager_mock = mock.MagicMock()
        
        self.handler = CommandHandlers(
            client=self.client_mock,
            meilisearch_service=self.meilisearch_service_mock,
            config_manager=self.config_manager_mock,
            admin_ids=[123456]
        )

    def test_parse_multiple_type_filters(self):
        """测试解析多个类型筛选参数"""
        # 测试两个有效类型
        query = "python 教程 type:group type:channel"
        parsed_query, filters = self.handler._parse_advanced_syntax(query)
        
        self.assertEqual(parsed_query, "python 教程")
        self.assertIn('chat_type', filters)
        self.assertIsInstance(filters['chat_type'], list)
        self.assertEqual(len(filters['chat_type']), 2)
        self.assertIn('group', filters['chat_type'])
        self.assertIn('channel', filters['chat_type'])
        
        # 测试三个类型（包括一个重复类型）
        query = "python 教程 type:user type:group type:group"
        parsed_query, filters = self.handler._parse_advanced_syntax(query)
        
        self.assertEqual(parsed_query, "python 教程")
        self.assertIn('chat_type', filters)
        self.assertIsInstance(filters['chat_type'], list)
        self.assertEqual(len(filters['chat_type']), 2)  # 应该去重
        self.assertIn('user', filters['chat_type'])
        self.assertIn('group', filters['chat_type'])
        
        # 测试有效类型和无效类型混合
        query = "python 教程 type:channel type:invalid"
        parsed_query, filters = self.handler._parse_advanced_syntax(query)
        
        self.assertEqual(parsed_query, "python 教程")
        self.assertIn('chat_type', filters)
        self.assertIsInstance(filters['chat_type'], list)
        self.assertEqual(len(filters['chat_type']), 1)
        self.assertIn('channel', filters['chat_type'])
        self.assertNotIn('invalid', filters['chat_type'])

    def test_parse_combined_with_date_and_multiple_types(self):
        """测试组合日期范围和多个类型筛选"""
        query = "python 教程 type:group type:channel date:2023-01-01_2023-12-31"
        parsed_query, filters = self.handler._parse_advanced_syntax(query)
        
        self.assertEqual(parsed_query, "python 教程")
        
        # 检查类型过滤
        self.assertIn('chat_type', filters)
        self.assertIsInstance(filters['chat_type'], list)
        self.assertEqual(len(filters['chat_type']), 2)
        self.assertIn('group', filters['chat_type'])
        self.assertIn('channel', filters['chat_type'])
        
        # 检查日期过滤
        self.assertIn('date_range', filters)
        self.assertIn('start', filters['date_range'])
        self.assertIn('end', filters['date_range'])
        
        start_date = datetime.datetime.strptime("2023-01-01", "%Y-%m-%d")
        start_timestamp = int(start_date.timestamp())
        self.assertEqual(filters['date_range']['start'], start_timestamp)
        
        end_date = datetime.datetime.strptime("2023-12-31 23:59:59", "%Y-%m-%d %H:%M:%S")
        end_timestamp = int(end_date.timestamp())
        self.assertEqual(filters['date_range']['end'], end_timestamp)


class TestMeilisearchFiltersBuilding(unittest.TestCase):
    """测试 Meilisearch 过滤条件构建功能，特别是多类型过滤"""

    def setUp(self):
        """设置测试环境"""
        self.client_mock = mock.MagicMock()
        self.meilisearch_service_mock = mock.MagicMock()
        self.config_manager_mock = mock.MagicMock()
        
        self.handler = CommandHandlers(
            client=self.client_mock,
            meilisearch_service=self.meilisearch_service_mock,
            config_manager=self.config_manager_mock,
            admin_ids=[123456]
        )

    def test_build_chat_type_list_filter(self):
        """测试构建多聊天类型过滤条件"""
        # 测试单一类型（作为列表）
        filters_dict = {'chat_type': ['group']}
        filter_string = self.handler._build_meilisearch_filters(filters_dict)
        
        self.assertEqual(filter_string, "(chat_type = 'group')")
        
        # 测试多个类型
        filters_dict = {'chat_type': ['group', 'channel']}
        filter_string = self.handler._build_meilisearch_filters(filters_dict)
        
        self.assertTrue("chat_type = 'group'" in filter_string)
        self.assertTrue("chat_type = 'channel'" in filter_string)
        self.assertTrue(" OR " in filter_string)
        self.assertTrue(filter_string.startswith("(") and filter_string.endswith(")"))

    def test_build_combined_with_date_and_chat_type_list(self):
        """测试组合日期范围和多聊天类型过滤条件"""
        filters_dict = {
            'chat_type': ['group', 'channel'],
            'date_range': {
                'start': 1672531200,  # 2023-01-01 00:00:00
                'end': 1704067199     # 2023-12-31 23:59:59
            }
        }
        filter_string = self.handler._build_meilisearch_filters(filters_dict)
        
        self.assertTrue("(chat_type = 'group' OR chat_type = 'channel')" in filter_string)
        self.assertTrue("date >= 1672531200 AND date <= 1704067199" in filter_string)
        self.assertTrue(" AND " in filter_string)


class TestGetResultsFromMeili(unittest.TestCase):
    """测试 _get_results_from_meili 方法，确保正确传递筛选参数"""

    def setUp(self):
        """设置测试环境"""
        self.client_mock = mock.MagicMock()
        self.meilisearch_service_mock = mock.MagicMock()
        self.config_manager_mock = mock.MagicMock()
        
        self.handler = CommandHandlers(
            client=self.client_mock,
            meilisearch_service=self.meilisearch_service_mock,
            config_manager=self.config_manager_mock,
            admin_ids=[123456]
        )

    async def test_get_results_with_filter_params(self):
        """测试 _get_results_from_meili 传递筛选参数"""
        # 设置参数
        parsed_query = "测试查询"
        filters = "chat_type = 'group' OR chat_type = 'channel'"
        sort = ["date:desc"]
        page = 1
        hits_per_page = 10
        start_timestamp = 1672531200
        end_timestamp = 1704067199
        chat_types = ['group', 'channel']
        
        # 调用方法
        await self.handler._get_results_from_meili(
            parsed_query=parsed_query,
            filters=filters,
            sort=sort,
            page=page,
            hits_per_page=hits_per_page,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            chat_types=chat_types
        )
        
        # 验证 search 方法被正确调用
        self.meilisearch_service_mock.search.assert_called_once_with(
            query=parsed_query,
            filters=filters,
            sort=sort,
            page=page,
            hits_per_page=hits_per_page,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            chat_types=chat_types
        )


class TestPerformSearch(unittest.TestCase):
    """测试 _perform_search 方法的筛选参数传递"""
    
    def setUp(self):
        """设置测试环境"""
        self.client_mock = mock.MagicMock()
        self.meilisearch_service_mock = mock.MagicMock()
        self.config_manager_mock = mock.MagicMock()
        self.cache_service_mock = mock.MagicMock()
        
        # 创建实例，但替换缓存服务为 mock
        self.handler = CommandHandlers(
            client=self.client_mock,
            meilisearch_service=self.meilisearch_service_mock,
            config_manager=self.config_manager_mock,
            admin_ids=[123456]
        )
        self.handler.cache_service = self.cache_service_mock
        
        # 禁用缓存，确保直接调用 meili
        self.cache_service_mock.is_cache_enabled.return_value = False
        
        # 创建 patch，以便我们可以检查 _get_results_from_meili 的调用
        self.get_results_patcher = mock.patch.object(
            self.handler, '_get_results_from_meili',
            return_value={'hits': [], 'estimatedTotalHits': 0}
        )
        self.mock_get_results = self.get_results_patcher.start()
        
        # 创建能被调用但不会有副作用的 respond 方法
        self.event_mock = mock.MagicMock()
        self.event_mock.respond = mock.AsyncMock()
        self.event_mock.get_sender = mock.AsyncMock(return_value=mock.MagicMock(id=999))
        
        # 修改 _parse_advanced_syntax 以返回我们控制的值
        self.parse_syntax_patcher = mock.patch.object(self.handler, '_parse_advanced_syntax')
        self.mock_parse_syntax = self.parse_syntax_patcher.start()
        
        # 修改 _build_meilisearch_filters 以返回我们控制的值
        self.build_filters_patcher = mock.patch.object(self.handler, '_build_meilisearch_filters')
        self.mock_build_filters = self.build_filters_patcher.start()

    def tearDown(self):
        """清理测试环境"""
        self.get_results_patcher.stop()
        self.parse_syntax_patcher.stop()
        self.build_filters_patcher.stop()

    async def test_perform_search_with_type_and_date_filters(self):
        """测试执行搜索时传递类型和日期过滤条件"""
        # 设置模拟返回值
        self.mock_parse_syntax.return_value = ("测试查询", {
            'chat_type': ['group', 'channel'],
            'date_range': {
                'start': 1672531200,  # 2023-01-01
                'end': 1704067199     # 2023-12-31
            }
        })
        self.mock_build_filters.return_value = "(chat_type = 'group' OR chat_type = 'channel') AND date >= 1672531200 AND date <= 1704067199"
        
        # 执行搜索
        await self.handler._perform_search(self.event_mock, "测试查询 type:group type:channel date:2023-01-01_2023-12-31")
        
        # 验证 _get_results_from_meili 被正确调用（包括过滤参数）
        # 注意我们只关心 start_timestamp, end_timestamp 和 chat_types 参数
        call_args = self.mock_get_results.call_args[1]
        self.assertEqual(call_args["start_timestamp"], 1672531200)
        self.assertEqual(call_args["end_timestamp"], 1704067199)
        self.assertEqual(call_args["chat_types"], ['group', 'channel'])


if __name__ == '__main__':
    unittest.main()