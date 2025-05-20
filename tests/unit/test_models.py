"""
数据模型单元测试模块

测试core.models模块中定义的数据模型，包括：
1. MeiliMessageDoc模型的创建和验证
2. 字段的类型约束
3. 必需字段和可选字段的行为
4. Literal类型约束的行为
"""

import unittest
from pydantic import ValidationError

# 确保能够导入models模块
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.models import MeiliMessageDoc


class TestMeiliMessageDoc(unittest.TestCase):
    """测试MeiliMessageDoc模型的功能"""

    def setUp(self):
        """准备测试数据"""
        # 有效的测试数据
        self.valid_data = {
            "id": "12345_67890",
            "message_id": 67890,
            "chat_id": 12345,
            "chat_title": "测试群组",
            "chat_type": "group",
            "sender_id": 98765,
            "sender_name": "测试用户",
            "text": "这是一条测试消息",
            "date": 1621234567,
            "message_link": "https://t.me/c/12345/67890"
        }

    def test_create_valid_model(self):
        """测试使用有效数据创建模型实例"""
        model = MeiliMessageDoc(**self.valid_data)
        
        # 验证所有字段值
        self.assertEqual(model.id, "12345_67890")
        self.assertEqual(model.message_id, 67890)
        self.assertEqual(model.chat_id, 12345)
        self.assertEqual(model.chat_title, "测试群组")
        self.assertEqual(model.chat_type, "group")
        self.assertEqual(model.sender_id, 98765)
        self.assertEqual(model.sender_name, "测试用户")
        self.assertEqual(model.text, "这是一条测试消息")
        self.assertEqual(model.date, 1621234567)
        self.assertEqual(model.message_link, "https://t.me/c/12345/67890")

    def test_invalid_data_types(self):
        """测试提供无效数据类型时的验证行为"""
        # 测试message_id为字符串而非整数
        invalid_data = self.valid_data.copy()
        invalid_data["message_id"] = "not_an_int"
        
        with self.assertRaises(ValidationError):
            MeiliMessageDoc(**invalid_data)
            
        # 测试chat_id为字符串而非整数
        invalid_data = self.valid_data.copy()
        invalid_data["chat_id"] = "not_an_int"
        
        with self.assertRaises(ValidationError):
            MeiliMessageDoc(**invalid_data)
            
        # 测试date为字符串而非整数
        invalid_data = self.valid_data.copy()
        invalid_data["date"] = "not_an_int"
        
        with self.assertRaises(ValidationError):
            MeiliMessageDoc(**invalid_data)

    def test_missing_required_fields(self):
        """测试缺少必需字段时的行为"""
        # 测试缺少id字段
        missing_id_data = self.valid_data.copy()
        del missing_id_data["id"]
        
        with self.assertRaises(ValidationError):
            MeiliMessageDoc(**missing_id_data)
            
        # 测试缺少text字段
        missing_text_data = self.valid_data.copy()
        del missing_text_data["text"]
        
        with self.assertRaises(ValidationError):
            MeiliMessageDoc(**missing_text_data)
            
        # 测试缺少message_id字段
        missing_message_id_data = self.valid_data.copy()
        del missing_message_id_data["message_id"]
        
        with self.assertRaises(ValidationError):
            MeiliMessageDoc(**missing_message_id_data)

    def test_optional_fields(self):
        """测试可选字段的行为"""
        # 测试chat_title为None
        optional_data = self.valid_data.copy()
        optional_data["chat_title"] = None
        
        model = MeiliMessageDoc(**optional_data)
        self.assertIsNone(model.chat_title)
        
        # 测试chat_title缺失（应使用默认值None）
        missing_optional_data = self.valid_data.copy()
        del missing_optional_data["chat_title"]
        
        model = MeiliMessageDoc(**missing_optional_data)
        self.assertIsNone(model.chat_title)
        
        # 测试sender_name为None
        optional_data = self.valid_data.copy()
        optional_data["sender_name"] = None
        
        model = MeiliMessageDoc(**optional_data)
        self.assertIsNone(model.sender_name)
        
        # 测试sender_name缺失（应使用默认值None）
        missing_optional_data = self.valid_data.copy()
        del missing_optional_data["sender_name"]
        
        model = MeiliMessageDoc(**missing_optional_data)
        self.assertIsNone(model.sender_name)

    def test_chat_type_literal_constraint(self):
        """测试chat_type字段的Literal类型约束"""
        # 测试有效的chat_type值
        for valid_type in ["user", "group", "channel"]:
            valid_data = self.valid_data.copy()
            valid_data["chat_type"] = valid_type
            
            model = MeiliMessageDoc(**valid_data)
            self.assertEqual(model.chat_type, valid_type)
            
        # 测试无效的chat_type值
        invalid_data = self.valid_data.copy()
        invalid_data["chat_type"] = "invalid_type"
        
        with self.assertRaises(ValidationError):
            MeiliMessageDoc(**invalid_data)


if __name__ == '__main__':
    unittest.main()