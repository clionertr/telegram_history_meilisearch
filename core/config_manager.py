"""
配置管理模块

此模块提供了管理应用程序配置的功能，包括：
1. 从.env文件加载环境变量
2. 从config.ini文件加载配置项
3. 管理白名单（添加、移除、获取）
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from configparser import ConfigParser
import dotenv


class ConfigError(Exception):
    """配置相关错误的基类"""
    pass


class ConfigFileNotFoundError(ConfigError):
    """配置文件不存在时抛出的错误"""
    pass


class ConfigManager:
    """
    配置管理器类

    负责加载和管理应用程序的配置，包括环境变量、配置文件和白名单
    """

    def __init__(self,
                 env_path: str = ".env",
                 config_path: str = "config.ini",
                 whitelist_path: str = "whitelist.json",
                 create_if_not_exists: bool = True) -> None:
        """
        初始化配置管理器

        Args:
            env_path: .env文件的路径，默认为项目根目录下的.env
            config_path: 配置文件的路径，默认为项目根目录下的config.ini
            whitelist_path: 白名单文件的路径，默认为项目根目录下的whitelist.json
            create_if_not_exists: 如果配置文件不存在，是否创建默认文件，默认为True
        """
        self.logger = logging.getLogger(__name__)
        
        # 存储路径
        self.env_path = env_path
        self.config_path = config_path
        self.whitelist_path = whitelist_path
        
        # 存储配置数据
        self.env_vars: Dict[str, str] = {}
        self.config = ConfigParser()
        self.whitelist: List[int] = []
        
        # 加载配置
        self.load_env()
        
        # 文件不存在且需要创建默认文件
        if create_if_not_exists:
            if not os.path.exists(config_path):
                self.create_default_config()
            if not os.path.exists(whitelist_path):
                self.save_whitelist()  # 创建空白名单
                
        # 加载配置文件和白名单
        self.load_config()
        self.load_whitelist()
        
        # 创建示例文件
        self.create_example_files()

    def load_env(self) -> None:
        """
        从.env文件加载环境变量

        如果.env文件不存在，会记录警告但不会抛出异常
        """
        if os.path.exists(self.env_path):
            dotenv.load_dotenv(self.env_path)
            self.logger.info(f"从 {self.env_path} 加载环境变量")
        else:
            self.logger.warning(f"{self.env_path} 文件不存在，无法加载环境变量")
            
        # 存储当前环境变量，便于后续访问
        self.env_vars = dict(os.environ)

    def load_config(self) -> None:
        """
        从配置文件加载配置项

        如果配置文件不存在，会记录警告但不会抛出异常
        """
        if os.path.exists(self.config_path):
            try:
                self.config.read(self.config_path, encoding="utf-8")
                self.logger.info(f"从 {self.config_path} 加载配置项")
            except Exception as e:
                self.logger.error(f"加载配置文件 {self.config_path} 时出错: {e}")
        else:
            self.logger.warning(f"{self.config_path} 文件不存在，无法加载配置项")

    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        获取环境变量

        Args:
            key: 环境变量名
            default: 默认值，如果环境变量不存在则返回此值

        Returns:
            环境变量的值，如果不存在则返回默认值
        """
        return self.env_vars.get(key, default)

    def get_config(self, section: str, key: str, default: Any = None) -> Any:
        """
        获取配置项

        Args:
            section: 配置节名称
            key: 配置项名称
            default: 默认值，如果配置项不存在则返回此值

        Returns:
            配置项的值，如果不存在则返回默认值
        """
        if section in self.config and key in self.config[section]:
            return self.config[section][key]
        return default

    def create_default_config(self) -> None:
        """
        创建默认配置文件

        如果配置文件不存在，创建一个包含默认节和注释的配置文件
        """
        self.config["MeiliSearch"] = {
            "HOST": "http://localhost:7700",
            "API_KEY": "# 在此处填入 MeiliSearch 的 API Key"
        }
        
        self.config["Telegram"] = {
            "# 备注": "Telegram 相关配置，也可以通过环境变量设置",
            "# SESSION_NAME": "userbot"
        }
        
        self.config["General"] = {
            "# CACHE_DIR": "cache",
            "# LOG_LEVEL": "INFO"
        }
        
        with open(self.config_path, "w", encoding="utf-8") as f:
            self.config.write(f)
            
        self.logger.info(f"已创建默认配置文件 {self.config_path}")

    def create_example_files(self) -> None:
        """
        创建示例文件

        创建config.ini.example和whitelist.json.example文件，作为用户的配置模板
        """
        # 创建config.ini.example
        example_config = ConfigParser()
        
        example_config["MeiliSearch"] = {
            "HOST": "http://localhost:7700",
            "API_KEY": "your_meilisearch_api_key_here"
        }
        
        example_config["Telegram"] = {
            "# 以下配置可以通过环境变量设置，也可以在此设置": "",
            "# API_ID": "your_api_id_here",
            "# API_HASH": "your_api_hash_here",
            "# BOT_TOKEN": "your_bot_token_here",
            "SESSION_NAME": "userbot"
        }
        
        example_config["General"] = {
            "CACHE_DIR": "cache",
            "LOG_LEVEL": "INFO",
            "# 其他常规配置项": ""
        }
        
        config_example_path = f"{self.config_path}.example"
        with open(config_example_path, "w", encoding="utf-8") as f:
            example_config.write(f)
            
        self.logger.info(f"已创建配置文件示例 {config_example_path}")
        
        # 创建whitelist.json.example
        whitelist_example = {
            "whitelist": [
                123456789,  # 示例用户ID
                -987654321  # 示例群组ID (负数)
            ],
            "comment": "此文件用于存储允许Userbot缓存消息的用户/群组/频道ID列表"
        }
        
        whitelist_example_path = f"{self.whitelist_path}.example"
        with open(whitelist_example_path, "w", encoding="utf-8") as f:
            json.dump(whitelist_example, f, indent=4, ensure_ascii=False)
            
        self.logger.info(f"已创建白名单文件示例 {whitelist_example_path}")

    def load_whitelist(self) -> None:
        """
        加载白名单

        从whitelist.json文件加载白名单，如果文件不存在或格式错误，会初始化为空白名单
        """
        if os.path.exists(self.whitelist_path):
            try:
                with open(self.whitelist_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "whitelist" in data:
                        self.whitelist = data["whitelist"]
                    else:
                        self.whitelist = []
                        self.logger.warning(f"白名单文件 {self.whitelist_path} 格式错误，已初始化为空白名单")
                self.logger.info(f"从 {self.whitelist_path} 加载白名单，共 {len(self.whitelist)} 个ID")
            except Exception as e:
                self.whitelist = []
                self.logger.error(f"加载白名单文件 {self.whitelist_path} 时出错: {e}")
        else:
            self.whitelist = []
            self.logger.warning(f"{self.whitelist_path} 文件不存在，已初始化为空白名单")

    def save_whitelist(self) -> None:
        """
        保存白名单

        将当前的白名单保存到whitelist.json文件
        """
        data = {
            "whitelist": self.whitelist,
            "updated_at": Path(self.whitelist_path).stat().st_mtime if os.path.exists(self.whitelist_path) else None
        }
        
        with open(self.whitelist_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        self.logger.info(f"已保存白名单到 {self.whitelist_path}，共 {len(self.whitelist)} 个ID")

    def get_whitelist(self) -> List[int]:
        """
        获取白名单

        Returns:
            白名单中的ID列表
        """
        return self.whitelist.copy()

    def add_to_whitelist(self, chat_id: int) -> bool:
        """
        添加ID到白名单

        Args:
            chat_id: 要添加的用户/群组/频道ID

        Returns:
            是否成功添加（如已存在则返回False）
        """
        if chat_id in self.whitelist:
            self.logger.info(f"ID {chat_id} 已在白名单中，无需添加")
            return False
            
        self.whitelist.append(chat_id)
        self.save_whitelist()
        self.logger.info(f"已将ID {chat_id} 添加到白名单")
        return True

    def remove_from_whitelist(self, chat_id: int) -> bool:
        """
        从白名单移除ID

        Args:
            chat_id: 要移除的用户/群组/频道ID

        Returns:
            是否成功移除（如不存在则返回False）
        """
        if chat_id not in self.whitelist:
            self.logger.info(f"ID {chat_id} 不在白名单中，无需移除")
            return False
            
        self.whitelist.remove(chat_id)
        self.save_whitelist()
        self.logger.info(f"已将ID {chat_id} 从白名单移除")
        return True

    def reset_whitelist(self) -> None:
        """
        重置白名单

        清空白名单并保存
        """
        self.whitelist = []
        self.save_whitelist()
        self.logger.info("已重置白名单")

    def is_in_whitelist(self, chat_id: int) -> bool:
        """
        检查ID是否在白名单中

        Args:
            chat_id: 要检查的用户/群组/频道ID

        Returns:
            ID是否在白名单中
        """
        return chat_id in self.whitelist