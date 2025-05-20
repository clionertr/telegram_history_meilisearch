"""
搜索机器人消息格式化模块的单元测试
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

from search_bot.message_formatters import (
    format_search_results,
    format_error_message,
    format_help_message
)


class TestMessageFormatters(unittest.TestCase):
    """测试消息格式化功能"""

    def test_format_empty_results(self):
        """测试格式化空结果"""
        # 空结果
        empty_results = {'hits': []}
        message, buttons = format_search_results(empty_results, 1, 1)
        
        self.assertIn("未找到匹配的消息", message)
        self.assertIsNone(buttons)
        
        # None结果
        message, buttons = format_search_results(None, 1, 1)
        self.assertIn("未找到匹配的消息", message)
        self.assertIsNone(buttons)

    def test_format_single_result(self):
        """测试格式化单条结果"""
        timestamp = int(datetime(2023, 5, 20, 12, 30, 0).timestamp())
        results = {
            'hits': [{
                'chat_title': '测试群组',
                'sender_name': '张三',
                'date': timestamp,
                'text': '这是一条测试消息',
                'message_link': 'https://t.me/c/12345/67890'
            }],
            'query': '测试',
            'estimatedTotalHits': 1,
            'processingTimeMs': 15
        }
        
        message, buttons = format_search_results(results, 1, 1)
        
        # 验证消息格式
        self.assertIn("搜索结果: \"测试\"", message)
        self.assertIn("找到约 1 条匹配消息", message)
        self.assertIn("张三", message)
        self.assertIn("测试群组", message)
        self.assertIn("这是一条测试消息", message)
        self.assertIn("https://t.me/c/12345/67890", message)
        
        # 验证没有分页按钮
        self.assertIsNone(buttons)

    def test_format_with_formatted_text(self):
        """测试格式化带有高亮片段的结果"""
        timestamp = int(datetime(2023, 5, 20, 12, 30, 0).timestamp())
        results = {
            'hits': [{
                'chat_title': '测试群组',
                'sender_name': '张三',
                'date': timestamp,
                'text': '这是一条关于Python和机器学习的测试消息',
                '_formatted': {
                    'text': '这是一条关于<em>Python</em>和<em>机器学习</em>的测试消息'
                },
                'message_link': 'https://t.me/c/12345/67890'
            }],
            'query': 'Python 机器学习',
            'estimatedTotalHits': 1,
            'processingTimeMs': 15
        }
        
        message, buttons = format_search_results(results, 1, 1)
        
        # 验证高亮文本被使用
        self.assertIn("<em>Python</em>", message)
        self.assertIn("<em>机器学习</em>", message)

    @patch('search_bot.message_formatters.Button')
    def test_format_with_pagination(self, mock_button):
        """测试带分页的结果格式化"""
        # 模拟Button.inline的行为
        mock_button.inline = MagicMock(side_effect=lambda text, data: {'text': text, 'data': data})
        
        # 创建测试数据
        timestamp = int(datetime(2023, 5, 20, 12, 30, 0).timestamp())
        results = {
            'hits': [
                {
                    'chat_title': '测试群组',
                    'sender_name': '张三',
                    'date': timestamp,
                    'text': '消息1',
                    'message_link': 'https://t.me/c/12345/1'
                }
            ],
            'query': '测试',
            'estimatedTotalHits': 30,  # 假设有30条结果
            'processingTimeMs': 15
        }
        
        # 测试第1页，共3页
        message, buttons = format_search_results(results, 1, 3)
        
        # 验证消息
        self.assertIn("搜索结果: \"测试\"", message)
        self.assertIn("第 1/3 页", message)
        
        # 验证分页按钮
        self.assertIsNotNone(buttons)
        self.assertEqual(len(buttons), 1)  # 一行按钮
        
        # 第一页应该有：当前页/总页数、下一页、末页按钮
        buttons_row = buttons[0]
        button_texts = [btn['text'] for btn in buttons_row]
        button_data = [btn['data'] for btn in buttons_row]
        
        self.assertEqual(len(buttons_row), 3)
        self.assertIn("📄 1/3", button_texts)
        self.assertIn("▶️ 下一页", button_texts)
        self.assertIn("⏭ 末页", button_texts)
        self.assertIn("page_2_测试", button_data[1])  # 下一页按钮数据
        self.assertIn("page_3_测试", button_data[2])  # 末页按钮数据
        
        # 测试中间页(第2页，共3页)
        message, buttons = format_search_results(results, 2, 3)
        
        # 中间页应该有：首页、上一页、当前页/总页数、下一页、末页按钮
        buttons_row = buttons[0]
        button_texts = [btn['text'] for btn in buttons_row]
        
        self.assertEqual(len(buttons_row), 5)
        self.assertIn("⏮ 首页", button_texts)
        self.assertIn("◀️ 上一页", button_texts)
        self.assertIn("📄 2/3", button_texts)
        self.assertIn("▶️ 下一页", button_texts)
        self.assertIn("⏭ 末页", button_texts)
        
        # 测试最后一页(第3页，共3页)
        message, buttons = format_search_results(results, 3, 3)
        
        # 最后一页应该有：首页、上一页、当前页/总页数按钮
        buttons_row = buttons[0]
        button_texts = [btn['text'] for btn in buttons_row]
        
        self.assertEqual(len(buttons_row), 3)
        self.assertIn("⏮ 首页", button_texts)
        self.assertIn("◀️ 上一页", button_texts)
        self.assertIn("📄 3/3", button_texts)

    def test_format_error_message(self):
        """测试错误消息格式化"""
        error_msg = "搜索查询语法错误"
        formatted = format_error_message(error_msg)
        
        self.assertIn("⚠️ **搜索出错**", formatted)
        self.assertIn(error_msg, formatted)

    def test_format_help_message(self):
        """测试帮助消息格式化"""
        help_msg = format_help_message()
        
        # 验证帮助信息包含关键部分
        self.assertIn("Telegram 中文历史消息搜索", help_msg)
        self.assertIn("基本搜索", help_msg)
        self.assertIn("高级搜索", help_msg)
        self.assertIn("精确短语", help_msg)
        self.assertIn("类型筛选", help_msg)
        self.assertIn("时间筛选", help_msg)


if __name__ == '__main__':
    unittest.main()