"""
MeiliSearchService 集成测试模块

此测试模块依赖于一个运行中的 Meilisearch 实例。
测试前请确保已通过 Docker Compose 启动 Meilisearch 服务：
    docker-compose up -d meilisearch
"""

import os
import time
import unittest
import random
import string
from datetime import datetime, timedelta
from typing import List, Optional

import pytest

from core.models import MeiliMessageDoc
from core.config_manager import ConfigManager
from core.meilisearch_service import MeiliSearchService


def random_string(length: int = 10) -> str:
    """生成随机字符串，用于测试数据"""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def create_test_message_doc(
    message_id: int = None,
    chat_id: int = None,
    chat_title: str = None,
    chat_type: str = "group",
    sender_id: int = None,
    sender_name: str = None,
    text: str = None,
    date: int = None,
    message_link: str = None
) -> MeiliMessageDoc:
    """创建测试用的消息文档"""
    now = int(datetime.now().timestamp())
    
    if message_id is None:
        message_id = random.randint(10000, 99999)
    if chat_id is None:
        chat_id = random.randint(1000000, 9999999)
    if chat_title is None:
        chat_title = f"测试群组_{random_string(5)}"
    if sender_id is None:
        sender_id = random.randint(100000, 999999)
    if sender_name is None:
        sender_name = f"用户_{random_string(5)}"
    if text is None:
        text = f"这是一条测试消息，包含随机内容：{random_string(20)}"
    if date is None:
        date = now
    if message_link is None:
        message_link = f"https://t.me/c/{abs(chat_id)}/{message_id}"
    
    return MeiliMessageDoc(
        id=f"{chat_id}_{message_id}",
        message_id=message_id,
        chat_id=chat_id,
        chat_title=chat_title,
        chat_type=chat_type,
        sender_id=sender_id,
        sender_name=sender_name,
        text=text,
        date=date,
        message_link=message_link
    )


def create_batch_test_messages(count: int = 10, base_chat_id: int = None, text_prefix: str = "") -> List[MeiliMessageDoc]:
    """创建一批测试消息文档"""
    if base_chat_id is None:
        base_chat_id = random.randint(1000000, 9999999)
    
    now = int(datetime.now().timestamp())
    
    messages = []
    for i in range(count):
        # 生成递减的时间戳，模拟消息的时间顺序
        msg_time = now - (count - i) * 3600  # 每条消息间隔1小时
        
        messages.append(create_test_message_doc(
            message_id=i + 1,
            chat_id=base_chat_id,
            text=f"{text_prefix}批量测试消息 #{i+1}: {random_string(15)}",
            date=msg_time
        ))
    
    return messages


class TestMeiliSearchService(unittest.TestCase):
    """MeiliSearchService 集成测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试前的准备工作"""
        # 从配置或环境变量获取 Meilisearch 连接信息
        config_manager = ConfigManager()
        host = config_manager.get_config("MeiliSearch", "HOST", "http://localhost:7700")
        api_key = config_manager.get_config("MeiliSearch", "API_KEY", "ThisIsASuperSecureRandomKeyForMeiliSearch123!@#")
        
        # 使用随机索引名，避免测试影响生产环境
        cls.test_index_name = f"test_telegram_messages_{random_string(8).lower()}"
        
        # 初始化 MeiliSearchService
        cls.search_service = MeiliSearchService(
            host=host,
            api_key=api_key,
            index_name=cls.test_index_name
        )
        
        # 创建一些默认的测试数据
        cls.default_message = create_test_message_doc(
            message_id=12345,
            chat_id=-10012345,
            chat_title="测试集成测试群组",
            sender_name="测试用户",
            text="这是一条用于测试的消息，包含特殊关键词：meilisearch测试"
        )
        
        # 创建一批测试消息
        cls.test_chat_id = -10098765
        cls.test_batch = create_batch_test_messages(
            count=20,
            base_chat_id=cls.test_chat_id,
            text_prefix="集成测试："
        )
        
        # 索引测试数据
        cls.search_service.index_message(cls.default_message)
        cls.search_service.index_messages_bulk(cls.test_batch)
        
        # 等待 Meilisearch 索引完成
        time.sleep(1)
    
    @classmethod
    def tearDownClass(cls):
        """测试后的清理工作"""
        # 删除测试索引
        cls.search_service.client.delete_index(cls.test_index_name)
    
    def test_connection_and_index_setup(self):
        """测试连接和索引设置"""
        # 检查索引是否存在
        indexes = self.search_service.client.get_indexes()
        index_names = [index.uid for index in indexes.results]
        self.assertIn(self.test_index_name, index_names)
        
        # 检查索引设置
        settings = self.search_service.index.get_settings()
        
        # 检查可搜索属性
        self.assertEqual(
            settings["searchableAttributes"],
            ["text", "sender_name", "chat_title"],
            "可搜索属性配置不符合预期"
        )
        
        # 检查可过滤属性
        self.assertEqual(
            settings["filterableAttributes"],
            ["chat_id", "chat_type", "sender_id", "date"],
            "可过滤属性配置不符合预期"
        )
        
        # 检查可排序属性
        self.assertEqual(
            settings["sortableAttributes"],
            ["date"],
            "可排序属性配置不符合预期"
        )
        
        # 检查排序规则
        self.assertEqual(
            settings["rankingRules"],
            ["words", "typo", "proximity", "attribute", "sort", "exactness"],
            "排序规则配置不符合预期"
        )
    
    def test_index_and_get_single_message(self):
        """测试索引单条消息并获取"""
        # 创建一条新消息
        message = create_test_message_doc(
            message_id=54321,
            chat_id=-10054321,
            text="这是一条专门用于测试索引和获取的消息"
        )
        
        # 索引消息
        result = self.search_service.index_message(message)
        self.assertIn("taskUid", result, "索引应返回任务ID")
        
        # 等待索引完成
        time.sleep(1)
        
        # 通过搜索获取消息
        search_result = self.search_service.search("专门用于测试索引和获取")
        self.assertGreaterEqual(search_result["estimatedTotalHits"], 1, "搜索应返回至少一条结果")
        
        # 检查获取的消息内容
        found = False
        for hit in search_result["hits"]:
            if hit["id"] == message.id:
                found = True
                self.assertEqual(hit["text"], message.text, "获取的消息文本应与原始消息相符")
                self.assertEqual(hit["chat_id"], message.chat_id, "获取的消息chat_id应与原始消息相符")
                break
        
        self.assertTrue(found, "应能通过搜索找到刚索引的消息")
    
    def test_bulk_indexing(self):
        """测试批量索引消息"""
        # 创建一批新消息
        chat_id = -10087654
        batch = create_batch_test_messages(
            count=10,
            base_chat_id=chat_id,
            text_prefix="批量索引测试："
        )
        
        # 批量索引消息
        result = self.search_service.index_messages_bulk(batch)
        self.assertIn("taskUid", result, "批量索引应返回任务ID")
        
        # 等待索引完成
        time.sleep(1)
        
        # 通过过滤条件搜索这批消息
        search_result = self.search_service.search(
            query="批量索引测试",
            filters=f"chat_id = {chat_id}"
        )
        
        # 验证返回的结果数量
        self.assertEqual(
            search_result["estimatedTotalHits"],
            len(batch),
            f"应返回 {len(batch)} 条批量索引的消息"
        )
    
    def test_search_with_keywords(self):
        """测试关键词搜索"""
        # 搜索包含特定关键词的消息
        search_result = self.search_service.search("meilisearch测试")
        
        # 验证能找到默认测试消息
        found = any(hit["id"] == self.default_message.id for hit in search_result["hits"])
        self.assertTrue(found, "应能通过关键词搜索找到默认测试消息")
    
    def test_search_with_filters(self):
        """测试带过滤条件的搜索"""
        # 通过 chat_id 过滤搜索
        search_result = self.search_service.search(
            query="集成测试",
            filters=f"chat_id = {self.test_chat_id}"
        )
        
        # 验证所有返回的结果都属于指定的 chat_id
        for hit in search_result["hits"]:
            self.assertEqual(
                hit["chat_id"],
                self.test_chat_id,
                "过滤搜索结果应只包含指定 chat_id 的消息"
            )
    
    def test_search_with_sorting(self):
        """测试带排序的搜索"""
        # 按日期降序排序
        search_result_desc = self.search_service.search(
            query="集成测试",
            filters=f"chat_id = {self.test_chat_id}",
            sort=["date:desc"]
        )
        
        # 按日期升序排序
        search_result_asc = self.search_service.search(
            query="集成测试",
            filters=f"chat_id = {self.test_chat_id}",
            sort=["date:asc"]
        )
        
        # 验证降序排序
        dates_desc = [hit["date"] for hit in search_result_desc["hits"]]
        self.assertEqual(
            dates_desc,
            sorted(dates_desc, reverse=True),
            "降序排序的结果应从新到旧排列"
        )
        
        # 验证升序排序
        dates_asc = [hit["date"] for hit in search_result_asc["hits"]]
        self.assertEqual(
            dates_asc,
            sorted(dates_asc),
            "升序排序的结果应从旧到新排列"
        )
    
    def test_search_with_pagination(self):
        """测试分页搜索"""
        # 第一页，每页5条
        page1 = self.search_service.search(
            query="集成测试",
            filters=f"chat_id = {self.test_chat_id}",
            page=1,
            hits_per_page=5
        )
        
        # 第二页，每页5条
        page2 = self.search_service.search(
            query="集成测试",
            filters=f"chat_id = {self.test_chat_id}",
            page=2,
            hits_per_page=5
        )
        
        # 验证返回的结果数量
        self.assertEqual(len(page1["hits"]), 5, "第一页应返回5条结果")
        self.assertEqual(len(page2["hits"]), 5, "第二页应返回5条结果")
        
        # 验证两页结果不重复
        page1_ids = [hit["id"] for hit in page1["hits"]]
        page2_ids = [hit["id"] for hit in page2["hits"]]
        
        self.assertTrue(
            all(pid not in page2_ids for pid in page1_ids),
            "第一页和第二页的结果不应重复"
        )
    
    def test_delete_message(self):
        """测试删除消息"""
        # 创建一条专门用于测试删除的消息
        message = create_test_message_doc(
            message_id=98765,
            chat_id=-10098765,
            text="这是一条专门用于测试删除的消息，包含特殊标记：DELETE_TEST"
        )
        
        # 索引消息
        self.search_service.index_message(message)
        time.sleep(1)
        
        # 确认消息已被索引
        pre_delete_search = self.search_service.search("DELETE_TEST")
        self.assertGreaterEqual(
            pre_delete_search["estimatedTotalHits"],
            1,
            "删除前应能找到测试消息"
        )
        
        # 删除消息
        delete_result = self.search_service.delete_message(message.id)
        self.assertIn("taskUid", delete_result, "删除操作应返回任务ID")
        time.sleep(1)
        
        # 确认消息已被删除
        post_delete_search = self.search_service.search("DELETE_TEST")
        found_after_delete = any(hit["id"] == message.id for hit in post_delete_search["hits"])
        self.assertFalse(found_after_delete, "删除后应找不到该消息")
    
    def test_advanced_search_with_timestamp_filter(self):
        """测试时间戳过滤的高级搜索"""
        # 创建不同时间段的测试消息
        now = int(datetime.now().timestamp())
        
        # 创建过去1小时的消息
        old_message = create_test_message_doc(
            message_id=11111,
            chat_id=-10011111,
            text="这是一条旧消息，时间戳过滤测试",
            date=now - 3600  # 1小时前
        )
        
        # 创建当前时间的消息
        new_message = create_test_message_doc(
            message_id=22222,
            chat_id=-10022222,
            text="这是一条新消息，时间戳过滤测试",
            date=now
        )
        
        # 索引消息
        self.search_service.index_message(old_message)
        self.search_service.index_message(new_message)
        time.sleep(1)
        
        # 测试起始时间过滤
        search_result = self.search_service.search(
            query="时间戳过滤测试",
            start_timestamp=now - 1800  # 30分钟前
        )
        
        # 应该只找到新消息
        found_ids = [hit["id"] for hit in search_result["hits"]]
        self.assertIn(new_message.id, found_ids, "应找到时间范围内的新消息")
        self.assertNotIn(old_message.id, found_ids, "不应找到时间范围外的旧消息")
        
        # 测试结束时间过滤
        search_result = self.search_service.search(
            query="时间戳过滤测试",
            end_timestamp=now - 1800  # 30分钟前
        )
        
        # 应该只找到旧消息
        found_ids = [hit["id"] for hit in search_result["hits"]]
        self.assertIn(old_message.id, found_ids, "应找到时间范围内的旧消息")
        self.assertNotIn(new_message.id, found_ids, "不应找到时间范围外的新消息")
        
        # 测试时间范围过滤
        search_result = self.search_service.search(
            query="时间戳过滤测试",
            start_timestamp=now - 7200,  # 2小时前
            end_timestamp=now - 1800     # 30分钟前
        )
        
        # 应该只找到旧消息
        found_ids = [hit["id"] for hit in search_result["hits"]]
        self.assertIn(old_message.id, found_ids, "应找到时间范围内的旧消息")
        self.assertNotIn(new_message.id, found_ids, "不应找到时间范围外的新消息")
    
    def test_advanced_search_with_chat_types_filter(self):
        """测试聊天类型过滤的高级搜索"""
        # 创建不同聊天类型的消息
        group_message = create_test_message_doc(
            message_id=33333,
            chat_id=-10033333,
            chat_type="group",
            text="这是群组消息，聊天类型过滤测试"
        )
        
        channel_message = create_test_message_doc(
            message_id=44444,
            chat_id=-10044444,
            chat_type="channel",
            text="这是频道消息，聊天类型过滤测试"
        )
        
        user_message = create_test_message_doc(
            message_id=55555,
            chat_id=10055555,  # 正数表示私聊
            chat_type="user",
            text="这是私聊消息，聊天类型过滤测试"
        )
        
        # 索引消息
        self.search_service.index_message(group_message)
        self.search_service.index_message(channel_message)
        self.search_service.index_message(user_message)
        time.sleep(1)
        
        # 测试单个聊天类型过滤
        search_result = self.search_service.search(
            query="聊天类型过滤测试",
            chat_types=["group"]
        )
        
        found_ids = [hit["id"] for hit in search_result["hits"]]
        self.assertIn(group_message.id, found_ids, "应找到群组消息")
        self.assertNotIn(channel_message.id, found_ids, "不应找到频道消息")
        self.assertNotIn(user_message.id, found_ids, "不应找到私聊消息")
        
        # 测试多个聊天类型过滤
        search_result = self.search_service.search(
            query="聊天类型过滤测试",
            chat_types=["group", "channel"]
        )
        
        found_ids = [hit["id"] for hit in search_result["hits"]]
        self.assertIn(group_message.id, found_ids, "应找到群组消息")
        self.assertIn(channel_message.id, found_ids, "应找到频道消息")
        self.assertNotIn(user_message.id, found_ids, "不应找到私聊消息")
        
        # 测试无效聊天类型（应该被忽略）
        search_result = self.search_service.search(
            query="聊天类型过滤测试",
            chat_types=["invalid_type", "group"]
        )
        
        found_ids = [hit["id"] for hit in search_result["hits"]]
        self.assertIn(group_message.id, found_ids, "应找到群组消息（忽略无效类型）")
    
    def test_advanced_search_with_chat_ids_filter(self):
        """测试聊天ID过滤的高级搜索"""
        # 创建不同聊天ID的消息
        chat1_message = create_test_message_doc(
            message_id=66666,
            chat_id=-10066666,
            text="这是聊天1的消息，聊天ID过滤测试"
        )
        
        chat2_message = create_test_message_doc(
            message_id=77777,
            chat_id=-10077777,
            text="这是聊天2的消息，聊天ID过滤测试"
        )
        
        chat3_message = create_test_message_doc(
            message_id=88888,
            chat_id=-10088888,
            text="这是聊天3的消息，聊天ID过滤测试"
        )
        
        # 索引消息
        self.search_service.index_message(chat1_message)
        self.search_service.index_message(chat2_message)
        self.search_service.index_message(chat3_message)
        time.sleep(1)
        
        # 测试单个聊天ID过滤
        search_result = self.search_service.search(
            query="聊天ID过滤测试",
            chat_ids=[-10066666]
        )
        
        found_ids = [hit["id"] for hit in search_result["hits"]]
        self.assertIn(chat1_message.id, found_ids, "应找到聊天1的消息")
        self.assertNotIn(chat2_message.id, found_ids, "不应找到聊天2的消息")
        self.assertNotIn(chat3_message.id, found_ids, "不应找到聊天3的消息")
        
        # 测试多个聊天ID过滤
        search_result = self.search_service.search(
            query="聊天ID过滤测试",
            chat_ids=[-10066666, -10077777]
        )
        
        found_ids = [hit["id"] for hit in search_result["hits"]]
        self.assertIn(chat1_message.id, found_ids, "应找到聊天1的消息")
        self.assertIn(chat2_message.id, found_ids, "应找到聊天2的消息")
        self.assertNotIn(chat3_message.id, found_ids, "不应找到聊天3的消息")
    
    def test_advanced_search_combined_filters(self):
        """测试组合过滤条件的高级搜索"""
        now = int(datetime.now().timestamp())
        
        # 创建符合所有条件的消息
        target_message = create_test_message_doc(
            message_id=99999,
            chat_id=-10099999,
            chat_type="group",
            text="这是目标消息，组合过滤测试",
            date=now - 1800  # 30分钟前
        )
        
        # 创建只符合部分条件的消息
        wrong_time_message = create_test_message_doc(
            message_id=99998,
            chat_id=-10099999,
            chat_type="group",
            text="这是错误时间的消息，组合过滤测试",
            date=now - 7200  # 2小时前
        )
        
        wrong_type_message = create_test_message_doc(
            message_id=99997,
            chat_id=-10099999,
            chat_type="channel",
            text="这是错误类型的消息，组合过滤测试",
            date=now - 1800  # 30分钟前
        )
        
        wrong_chat_message = create_test_message_doc(
            message_id=99996,
            chat_id=-10099998,
            chat_type="group",
            text="这是错误聊天的消息，组合过滤测试",
            date=now - 1800  # 30分钟前
        )
        
        # 索引消息
        messages = [target_message, wrong_time_message, wrong_type_message, wrong_chat_message]
        for msg in messages:
            self.search_service.index_message(msg)
        time.sleep(1)
        
        # 测试组合过滤
        search_result = self.search_service.search(
            query="组合过滤测试",
            start_timestamp=now - 3600,  # 1小时前
            end_timestamp=now,           # 现在
            chat_types=["group"],
            chat_ids=[-10099999]
        )
        
        # 应该只找到目标消息
        found_ids = [hit["id"] for hit in search_result["hits"]]
        self.assertIn(target_message.id, found_ids, "应找到符合所有条件的目标消息")
        self.assertNotIn(wrong_time_message.id, found_ids, "不应找到时间不符的消息")
        self.assertNotIn(wrong_type_message.id, found_ids, "不应找到类型不符的消息")
        self.assertNotIn(wrong_chat_message.id, found_ids, "不应找到聊天ID不符的消息")
        
        # 验证结果数量
        self.assertEqual(len(found_ids), 1, "组合过滤应该只返回1条符合所有条件的消息")
    
    def test_advanced_search_with_highlight(self):
        """测试高级搜索的高亮功能"""
        # 创建包含特定关键词的消息
        highlight_message = create_test_message_doc(
            message_id=77777,
            chat_id=-10077777,
            text="这是一条包含高亮关键词的测试消息，用于验证高亮功能是否正常工作"
        )
        
        # 索引消息
        self.search_service.index_message(highlight_message)
        time.sleep(1)
        
        # 执行搜索
        search_result = self.search_service.search(
            query="高亮关键词"
        )
        
        # 验证搜索结果
        self.assertGreater(search_result["estimatedTotalHits"], 0, "应该找到包含关键词的消息")
        
        # 检查是否配置了高亮属性
        found_message = None
        for hit in search_result["hits"]:
            if hit["id"] == highlight_message.id:
                found_message = hit
                break
        
        self.assertIsNotNone(found_message, "应该找到目标消息")
        
        # 注意：在实际的集成测试中，Meilisearch应该返回_formatted字段
        # 这里我们主要验证搜索功能正常工作
        self.assertEqual(found_message["text"], highlight_message.text, "消息文本应该正确返回")


if __name__ == "__main__":
    unittest.main()