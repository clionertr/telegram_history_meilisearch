"""
HistorySyncer 单元测试
"""

import os
import json
import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta

from core.config_manager import SyncPointManager
from user_bot.history_syncer import HistorySyncer


class TestHistorySyncer(unittest.TestCase):
    """测试 HistorySyncer 类"""
    
    def setUp(self):
        """测试前准备工作"""
        # 创建临时同步点文件路径
        self.test_sync_points_path = "test_sync_points.json"
        
        # 清理可能存在的临时文件
        if os.path.exists(self.test_sync_points_path):
            os.remove(self.test_sync_points_path)
        
        # 创建模拟对象
        self.mock_client = MagicMock()
        self.mock_client.get_client = MagicMock(return_value=MagicMock())
        
        self.mock_config_manager = MagicMock()
        self.mock_config_manager.get_whitelist = MagicMock(return_value=[123456, 789012])
        self.mock_config_manager.get_oldest_sync_timestamp = MagicMock(return_value=None)  # 默认无限制
        
        self.mock_meili_service = MagicMock()
        self.mock_meili_service.index_messages_bulk = MagicMock(return_value={"taskUid": "mock-task-id"})
        
        # 创建真实的SyncPointManager，但使用测试文件路径
        self.sync_point_manager = SyncPointManager(self.test_sync_points_path)
        
        # 创建HistorySyncer实例
        self.syncer = HistorySyncer(
            client=self.mock_client,
            config_manager=self.mock_config_manager,
            meili_service=self.mock_meili_service,
            sync_point_manager=self.sync_point_manager
        )
        
    def tearDown(self):
        """测试后清理工作"""
        # 删除临时同步点文件
        if os.path.exists(self.test_sync_points_path):
            os.remove(self.test_sync_points_path)

    @patch('user_bot.history_syncer.HistorySyncer._build_message_doc')
    @patch('telethon.client.messages.MessageMethods.iter_messages')
    async def test_incremental_sync(self, mock_iter_messages, mock_build_message_doc):
        """测试增量同步功能"""
        # 设置模拟消息
        chat_id = 123456
        now = datetime.now()
        
        # 第一条消息
        mock_message1 = MagicMock()
        mock_message1.id = 1001
        mock_message1.text = "测试消息1"
        mock_message1.date = now - timedelta(days=2)
        
        # 第二条消息
        mock_message2 = MagicMock()
        mock_message2.id = 1002
        mock_message2.text = "测试消息2"
        mock_message2.date = now - timedelta(days=1)
        
        # 设置模拟迭代器返回消息列表
        mock_iter_messages.return_value = [mock_message2, mock_message1]
        
        # 模拟_build_message_doc返回有效的消息文档
        mock_build_message_doc.side_effect = lambda msg, *args, **kwargs: MagicMock(
            id=f"{chat_id}_{msg.id}",
            message_id=msg.id,
            text=msg.text
        )
        
        # 模拟获取聊天实体
        self.mock_client.get_client.return_value.get_entity = AsyncMock(return_value=MagicMock(
            id=chat_id,
            title="测试聊天"
        ))
        
        # 执行全量同步
        _, _ = await self.syncer.sync_chat_history(chat_id, incremental=False)
        
        # 验证同步点是否已记录
        sync_point = self.sync_point_manager.get_sync_point(chat_id)
        self.assertIsNotNone(sync_point)
        self.assertEqual(sync_point["message_id"], 1001)  # 应该记录较早的消息作为同步点
        
        # 第三条消息（更新的消息）
        mock_message3 = MagicMock()
        mock_message3.id = 1003
        mock_message3.text = "测试消息3"
        mock_message3.date = now
        
        # 更新模拟迭代器返回新消息
        mock_iter_messages.return_value = [mock_message3]
        
        # 执行增量同步
        _, _ = await self.syncer.sync_chat_history(chat_id, incremental=True)
        
        # 验证是否正确传递了offset_date参数
        call_kwargs = mock_iter_messages.call_args[1]
        self.assertIn("offset_date", call_kwargs)
        
        # 验证同步点是否已更新
        updated_sync_point = self.sync_point_manager.get_sync_point(chat_id)
        self.assertEqual(updated_sync_point["message_id"], 1003)  # 应该更新为最新消息ID

    @patch('user_bot.history_syncer.HistorySyncer._build_message_doc')
    @patch('telethon.client.messages.MessageMethods.iter_messages')
    async def test_date_range_sync(self, mock_iter_messages, mock_build_message_doc):
        """测试时间段过滤功能"""
        chat_id = 789012
        now = datetime.now()
        
        # 创建时间范围
        date_from = now - timedelta(days=5)
        date_to = now - timedelta(days=2)
        
        # 三条消息，分别在时间范围前、中、后
        mock_message1 = MagicMock()  # 在范围前（太早）
        mock_message1.id = 2001
        mock_message1.text = "范围前消息"
        mock_message1.date = now - timedelta(days=7)
        
        mock_message2 = MagicMock()  # 在范围中（应包含）
        mock_message2.id = 2002
        mock_message2.text = "范围中消息"
        mock_message2.date = now - timedelta(days=3)
        
        mock_message3 = MagicMock()  # 在范围后（太新）
        mock_message3.id = 2003
        mock_message3.text = "范围后消息"
        mock_message3.date = now - timedelta(days=1)
        
        # 设置模拟迭代器返回所有消息
        mock_iter_messages.return_value = [mock_message3, mock_message2, mock_message1]
        
        # 模拟_build_message_doc返回有效的消息文档
        mock_build_message_doc.side_effect = lambda msg, *args, **kwargs: MagicMock(
            id=f"{chat_id}_{msg.id}",
            message_id=msg.id,
            text=msg.text
        )
        
        # 模拟获取聊天实体
        self.mock_client.get_client.return_value.get_entity = AsyncMock(return_value=MagicMock(
            id=chat_id,
            title="测试聊天2"
        ))
        
        # 执行时间段同步
        _, _ = await self.syncer.sync_chat_history(
            chat_id=chat_id,
            incremental=False,  # 禁用增量同步
            date_from=date_from,
            date_to=date_to
        )
        
        # 验证是否正确传递了offset_date参数
        call_kwargs = mock_iter_messages.call_args[1]
        self.assertEqual(call_kwargs["offset_date"], date_from)
        
        # 应该只有一条消息被处理（范围中的消息2）
        self.assertEqual(mock_build_message_doc.call_count, 1)
        # 确认是正确的消息
        self.assertEqual(mock_build_message_doc.call_args[0][0].id, 2002)
        
    @patch('user_bot.history_syncer.HistorySyncer._build_message_doc')
    @patch('telethon.client.messages.MessageMethods.iter_messages')
    async def test_oldest_sync_timestamp_limit(self, mock_iter_messages, mock_build_message_doc):
        """测试最旧同步时间戳限制功能"""
        chat_id = 123456
        now = datetime.now()
        
        # 设置模拟消息
        mock_message1 = MagicMock()  # 最旧的消息（应被过滤）
        mock_message1.id = 1001
        mock_message1.text = "旧消息"
        mock_message1.date = now - timedelta(days=10)
        
        mock_message2 = MagicMock()  # 较新消息（应包含）
        mock_message2.id = 1002
        mock_message2.text = "新消息"
        mock_message2.date = now - timedelta(days=2)
        
        # 设置模拟迭代器返回所有消息
        mock_iter_messages.return_value = [mock_message2, mock_message1]
        
        # 模拟_build_message_doc返回有效的消息文档
        mock_build_message_doc.side_effect = lambda msg, *args, **kwargs: MagicMock(
            id=f"{chat_id}_{msg.id}",
            message_id=msg.id,
            text=msg.text
        )
        
        # 模拟获取聊天实体
        self.mock_client.get_client.return_value.get_entity = AsyncMock(return_value=MagicMock(
            id=chat_id,
            title="测试聊天"
        ))
        
        # 设置最旧同步时间戳（5天前）
        oldest_timestamp = now - timedelta(days=5)
        self.mock_config_manager.get_oldest_sync_timestamp.return_value = oldest_timestamp
        
        # 执行同步
        processed_count, indexed_count = await self.syncer.sync_chat_history(chat_id)
        
        # 验证是否正确传递了参数
        self.mock_config_manager.get_oldest_sync_timestamp.assert_called_once_with(chat_id)
        
        # 应该只有一条消息被处理（较新的消息2）
        self.assertEqual(mock_build_message_doc.call_count, 1)
        # 确认是正确的消息
        self.assertEqual(mock_build_message_doc.call_args[0][0].id, 1002)


if __name__ == "__main__":
    asyncio.run(unittest.main())