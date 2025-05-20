"""
回调查询处理模块单元测试
"""

import unittest
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
from telethon.events import CallbackQuery

from search_bot.callback_query_handlers import CallbackQueryHandlers, setup_callback_handlers
from core.meilisearch_service import MeiliSearchService


class TestCallbackQueryHandlers(unittest.TestCase):
    """测试回调查询处理器类"""
    
    def setUp(self):
        """
        测试前的准备工作
        
        初始化模拟对象和处理器实例
        """
        # 创建模拟对象
        self.mock_client = MagicMock()
        self.mock_client.add_event_handler = MagicMock()
        
        self.mock_meilisearch_service = MagicMock(spec=MeiliSearchService)
        
        # 创建处理器实例
        self.handler = CallbackQueryHandlers(
            client=self.mock_client,
            meilisearch_service=self.mock_meilisearch_service
        )
    
    def test_register_handlers(self):
        """测试注册回调处理函数"""
        # 重置模拟对象的调用记录
        self.mock_client.add_event_handler.reset_mock()
        
        # 调用 register_handlers 方法
        self.handler.register_handlers()
        
        # 验证是否添加了两个事件处理器（分页和noop）
        self.assertEqual(self.mock_client.add_event_handler.call_count, 2)
    
    def test_setup_callback_handlers(self):
        """测试创建回调查询处理器的辅助函数"""
        # 创建模拟对象
        mock_client = MagicMock()
        mock_meilisearch_service = MagicMock(spec=MeiliSearchService)
        
        # 调用辅助函数
        handler = setup_callback_handlers(
            client=mock_client,
            meilisearch_service=mock_meilisearch_service
        )
        
        # 验证返回的处理器是否是 CallbackQueryHandlers 实例
        self.assertIsInstance(handler, CallbackQueryHandlers)
        
        # 验证是否在初始化过程中注册了处理器
        self.assertEqual(mock_client.add_event_handler.call_count, 2)


@pytest.mark.asyncio
class TestCallbackQueryHandlersAsync:
    """测试回调查询处理器的异步方法"""
    
    @pytest.fixture
    async def setup(self):
        """
        测试前的准备工作
        
        创建模拟对象和处理器实例
        """
        # 创建模拟对象
        mock_client = MagicMock()
        mock_meilisearch_service = MagicMock(spec=MeiliSearchService)
        
        # 创建回调处理器实例
        handler = CallbackQueryHandlers(
            client=mock_client,
            meilisearch_service=mock_meilisearch_service
        )
        
        return handler, mock_client, mock_meilisearch_service
    
    async def test_pagination_callback(self, setup):
        """测试分页回调处理"""
        handler, mock_client, mock_meilisearch_service = await setup
        
        # 创建模拟事件对象
        mock_event = AsyncMock()
        mock_event.data = b"page_2_test query"
        mock_event.get_sender = AsyncMock(return_value=MagicMock(id=12345))
        mock_event.answer = AsyncMock()
        mock_event.edit = AsyncMock()
        
        # 模拟搜索结果
        mock_results = {
            'hits': [{'text': 'Test message', 'sender_name': 'Test User'}],
            'query': 'test query',
            'estimatedTotalHits': 10,
            'processingTimeMs': 20,
        }
        mock_meilisearch_service.search.return_value = mock_results
        
        # 模拟格式化结果
        with patch('search_bot.callback_query_handlers.format_search_results') as mock_format:
            mock_format.return_value = ("Formatted message", [["Button"]])
            
            # 调用分页回调方法
            await handler.pagination_callback(mock_event)
            
            # 验证是否调用了 MeiliSearchService.search
            mock_meilisearch_service.search.assert_called_once()
            # 验证调用时传递的参数
            query_arg = mock_meilisearch_service.search.call_args[1]['query']
            page_arg = mock_meilisearch_service.search.call_args[1]['page']
            self.assertEqual(query_arg, "test query")
            self.assertEqual(page_arg, 2)
            
            # 验证是否调用了 format_search_results
            mock_format.assert_called_once()
            
            # 验证是否调用了 event.edit
            mock_event.edit.assert_called_once()
    
    async def test_pagination_callback_invalid_data(self, setup):
        """测试无效回调数据的处理"""
        handler, mock_client, mock_meilisearch_service = await setup
        
        # 创建模拟事件对象，使用无效的回调数据
        mock_event = AsyncMock()
        mock_event.data = b"invalid_data"
        mock_event.get_sender = AsyncMock(return_value=MagicMock(id=12345))
        mock_event.answer = AsyncMock()
        
        # 调用分页回调方法
        await handler.pagination_callback(mock_event)
        
        # 验证是否显示了错误提示
        mock_event.answer.assert_called_once()
        self.assertTrue("无效的请求格式" in mock_event.answer.call_args[0][0])
        
        # 验证没有调用 search 方法
        mock_meilisearch_service.search.assert_not_called()
    
    async def test_noop_callback(self, setup):
        """测试 noop 回调处理"""
        handler, mock_client, mock_meilisearch_service = await setup
        
        # 创建模拟事件对象
        mock_event = AsyncMock()
        mock_event.answer = AsyncMock()
        
        # 调用 noop 回调方法
        await handler.noop_callback(mock_event)
        
        # 验证是否调用了 event.answer 且传递了正确的消息
        mock_event.answer.assert_called_once()
        self.assertEqual(mock_event.answer.call_args[0][0], "这是当前页面")