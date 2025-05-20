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


if __name__ == "__main__":
    unittest.main()