"""
ConfigManager单元测试模块

测试ConfigManager类的功能，包括：
1. 环境变量加载和获取
2. 配置文件加载和获取
3. 白名单管理
4. 文件创建
"""

import os
import json
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# 确保能够导入ConfigManager
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.config_manager import ConfigManager, ConfigError


class TestConfigManager(unittest.TestCase):
    """测试ConfigManager类的功能"""

    def setUp(self):
        """测试前准备，创建临时目录和文件"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()

        # 创建测试用的.env文件
        self.env_path = os.path.join(self.temp_dir, ".env")
        with open(self.env_path, "w", encoding="utf-8") as f:
            f.write("TELEGRAM_API_ID=12345\n")
            f.write("TELEGRAM_API_HASH=abcdef1234567890\n")
            f.write("BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11\n")
            f.write("MEILISEARCH_HOST=http://localhost:7700\n")
            f.write("MEILISEARCH_API_KEY=test_key\n")

        # 创建测试用的config.ini文件
        self.config_path = os.path.join(self.temp_dir, "config.ini")
        with open(self.config_path, "w", encoding="utf-8") as f:
            f.write("[MeiliSearch]\n")
            f.write("HOST=http://localhost:7700\n")
            f.write("API_KEY=test_config_key\n\n")
            f.write("[Telegram]\n")
            f.write("SESSION_NAME=test_session\n\n")
            f.write("[General]\n")
            f.write("CACHE_DIR=cache\n")
            f.write("LOG_LEVEL=DEBUG\n")

        # 创建测试用的whitelist.json文件
        self.whitelist_path = os.path.join(self.temp_dir, "whitelist.json")
        with open(self.whitelist_path, "w", encoding="utf-8") as f:
            json.dump({
                "whitelist": [12345, -67890],
                "comment": "Test whitelist"
            }, f)

        # 创建不带create_if_not_exists参数的ConfigManager实例
        self.config_manager = ConfigManager(
            env_path=self.env_path,
            config_path=self.config_path,
            whitelist_path=self.whitelist_path
        )

    def tearDown(self):
        """测试后清理临时文件"""
        # 删除临时目录和所有内容
        shutil.rmtree(self.temp_dir)

    def test_load_env(self):
        """测试加载环境变量"""
        # 环境变量已在setUp中加载到self.config_manager中，这里直接测试结果
        self.assertEqual(self.config_manager.get_env("TELEGRAM_API_ID"), "12345")
        self.assertEqual(self.config_manager.get_env("TELEGRAM_API_HASH"), "abcdef1234567890")
        self.assertEqual(self.config_manager.get_env("BOT_TOKEN"), "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
        self.assertEqual(self.config_manager.get_env("MEILISEARCH_HOST"), "http://localhost:7700")
        self.assertEqual(self.config_manager.get_env("MEILISEARCH_API_KEY"), "test_key")
        
        # 测试不存在的环境变量返回默认值
        self.assertIsNone(self.config_manager.get_env("NON_EXISTENT_VAR"))
        self.assertEqual(self.config_manager.get_env("NON_EXISTENT_VAR", "default"), "default")

    def test_load_config(self):
        """测试加载配置文件"""
        # 配置已在setUp中加载到self.config_manager中，这里直接测试结果
        self.assertEqual(self.config_manager.get_config("MeiliSearch", "HOST"), "http://localhost:7700")
        self.assertEqual(self.config_manager.get_config("MeiliSearch", "API_KEY"), "test_config_key")
        self.assertEqual(self.config_manager.get_config("Telegram", "SESSION_NAME"), "test_session")
        self.assertEqual(self.config_manager.get_config("General", "CACHE_DIR"), "cache")
        self.assertEqual(self.config_manager.get_config("General", "LOG_LEVEL"), "DEBUG")
        
        # 测试不存在的配置项返回默认值
        self.assertIsNone(self.config_manager.get_config("NonExistentSection", "NonExistentKey"))
        self.assertEqual(
            self.config_manager.get_config("NonExistentSection", "NonExistentKey", "default"), 
            "default"
        )
        self.assertEqual(
            self.config_manager.get_config("MeiliSearch", "NonExistentKey", "default"), 
            "default"
        )

    def test_whitelist_operations(self):
        """测试白名单操作"""
        # 测试获取白名单
        whitelist = self.config_manager.get_whitelist()
        self.assertEqual(len(whitelist), 2)
        self.assertIn(12345, whitelist)
        self.assertIn(-67890, whitelist)
        
        # 测试添加到白名单
        result = self.config_manager.add_to_whitelist(54321)
        self.assertTrue(result)  # 添加成功返回True
        whitelist = self.config_manager.get_whitelist()
        self.assertEqual(len(whitelist), 3)
        self.assertIn(54321, whitelist)
        
        # 测试添加已存在的ID（应返回False）
        result = self.config_manager.add_to_whitelist(12345)
        self.assertFalse(result)  # 已存在返回False
        whitelist = self.config_manager.get_whitelist()
        self.assertEqual(len(whitelist), 3)  # 长度未变
        
        # 测试从白名单移除
        result = self.config_manager.remove_from_whitelist(12345)
        self.assertTrue(result)  # 移除成功返回True
        whitelist = self.config_manager.get_whitelist()
        self.assertEqual(len(whitelist), 2)
        self.assertNotIn(12345, whitelist)
        
        # 测试移除不存在的ID（应返回False）
        result = self.config_manager.remove_from_whitelist(99999)
        self.assertFalse(result)  # 不存在返回False
        whitelist = self.config_manager.get_whitelist()
        self.assertEqual(len(whitelist), 2)  # 长度未变
        
        # 测试检查ID是否在白名单中
        self.assertTrue(self.config_manager.is_in_whitelist(-67890))
        self.assertFalse(self.config_manager.is_in_whitelist(12345))  # 已被移除
        
        # 测试重置白名单
        self.config_manager.reset_whitelist()
        whitelist = self.config_manager.get_whitelist()
        self.assertEqual(len(whitelist), 0)  # 白名单为空

    def test_file_creation(self):
        """测试文件创建功能"""
        # 创建新的临时目录测试文件创建
        test_dir = os.path.join(self.temp_dir, "test_creation")
        os.makedirs(test_dir, exist_ok=True)
        
        env_path = os.path.join(test_dir, ".env")
        config_path = os.path.join(test_dir, "config.ini")
        whitelist_path = os.path.join(test_dir, "whitelist.json")
        
        # 确保文件不存在
        for path in [config_path, whitelist_path]:
            if os.path.exists(path):
                os.remove(path)
        
        # 创建ConfigManager实例，启用自动创建文件
        config_manager = ConfigManager(
            env_path=env_path,  # .env文件不存在也没关系
            config_path=config_path,
            whitelist_path=whitelist_path,
            create_if_not_exists=True
        )
        
        # 测试默认配置文件是否已创建
        self.assertTrue(os.path.exists(config_path))
        self.assertTrue(os.path.exists(whitelist_path))
        
        # 测试示例文件是否已创建
        self.assertTrue(os.path.exists(f"{config_path}.example"))
        self.assertTrue(os.path.exists(f"{whitelist_path}.example"))
        
        # 检查默认配置文件内容
        config = config_manager.config
        self.assertIn("MeiliSearch", config)
        self.assertIn("Telegram", config)
        self.assertIn("General", config)
        
        # 检查白名单是否为空列表
        self.assertEqual(len(config_manager.get_whitelist()), 0)

    def test_file_not_exists_without_creation(self):
        """测试文件不存在且不自动创建的情况"""
        # 创建新的临时目录
        test_dir = os.path.join(self.temp_dir, "test_no_creation")
        os.makedirs(test_dir, exist_ok=True)
        
        env_path = os.path.join(test_dir, ".env")  # 不存在
        config_path = os.path.join(test_dir, "config.ini")  # 不存在
        whitelist_path = os.path.join(test_dir, "whitelist.json")  # 不存在
        
        # 确保文件不存在
        for path in [env_path, config_path, whitelist_path]:
            if os.path.exists(path):
                os.remove(path)
        
        # 创建ConfigManager实例，禁用自动创建文件
        config_manager = ConfigManager(
            env_path=env_path,
            config_path=config_path,
            whitelist_path=whitelist_path,
            create_if_not_exists=False
        )
        
        # 文件应该还是不存在
        self.assertFalse(os.path.exists(config_path))
        self.assertFalse(os.path.exists(whitelist_path))
        
        # 但应该有示例文件
        self.assertTrue(os.path.exists(f"{config_path}.example"))
        self.assertTrue(os.path.exists(f"{whitelist_path}.example"))
        
        # 配置应该为空
        self.assertEqual(len(config_manager.config.sections()), 0)
        
        # 白名单应该为空列表
        self.assertEqual(len(config_manager.get_whitelist()), 0)

    @patch('logging.Logger.warning')
    def test_missing_files_warnings(self, mock_warning):
        """测试缺失文件时的警告日志"""
        # 创建新的临时目录
        test_dir = os.path.join(self.temp_dir, "test_warnings")
        os.makedirs(test_dir, exist_ok=True)
        
        env_path = os.path.join(test_dir, ".env")  # 不存在
        config_path = os.path.join(test_dir, "config.ini")  # 不存在
        whitelist_path = os.path.join(test_dir, "whitelist.json")  # 不存在
        
        # 确保文件不存在
        for path in [env_path, config_path, whitelist_path]:
            if os.path.exists(path):
                os.remove(path)
        
        # 创建ConfigManager实例，禁用自动创建文件
        ConfigManager(
            env_path=env_path,
            config_path=config_path,
            whitelist_path=whitelist_path,
            create_if_not_exists=False
        )
        
        # 检查是否有关于缺失文件的警告
        # 检查警告调用次数（应该有3个警告：.env, config.ini, whitelist.json）
        self.assertEqual(mock_warning.call_count, 3)
        
        # 确认警告内容包含文件路径
        warning_messages = [call.args[0] for call in mock_warning.call_args_list]
        self.assertTrue(any(env_path in msg for msg in warning_messages))
        self.assertTrue(any(config_path in msg for msg in warning_messages))
        self.assertTrue(any(whitelist_path in msg for msg in warning_messages))


if __name__ == '__main__':
    unittest.main()