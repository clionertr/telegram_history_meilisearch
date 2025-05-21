"""
配置管理模块

此模块提供了管理应用程序配置的功能，包括：
1. 从.env文件加载环境变量
2. 从config.ini文件加载配置项
3. 管理白名单（添加、移除、获取）
4. 管理聊天同步点信息
"""

import os
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from configparser import ConfigParser
import dotenv


class UserBotConfigError(Exception):
    """User Bot 配置相关错误"""
    pass


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
                 userbot_env_path: str = ".env.userbot",
                 create_if_not_exists: bool = True) -> None:
        """
        初始化配置管理器

        Args:
            env_path: .env文件的路径，默认为项目根目录下的.env
            config_path: 配置文件的路径，默认为项目根目录下的config.ini
            whitelist_path: 白名单文件的路径，默认为项目根目录下的whitelist.json
            userbot_env_path: User Bot 环境变量文件的路径，默认为项目根目录下的.env.userbot
            create_if_not_exists: 如果配置文件不存在，是否创建默认文件，默认为True
        """
        self.logger = logging.getLogger(__name__)
        
        # 存储路径
        self.env_path = env_path
        self.config_path = config_path
        self.whitelist_path = whitelist_path
        self.userbot_env_path = userbot_env_path
        
        # 存储配置数据
        self.env_vars: Dict[str, str] = {}
        self.userbot_env_vars: Dict[str, str] = {}
        self.config = ConfigParser()
        self.whitelist: List[int] = []
        
        # 加载配置
        self.load_env()
        self.load_userbot_env()
        
        # 文件不存在且需要创建默认文件
        if create_if_not_exists:
            if not os.path.exists(config_path):
                self.create_default_config()
            if not os.path.exists(whitelist_path):
                self.save_whitelist()  # 创建空白名单
            if not os.path.exists(userbot_env_path):
                self.create_default_userbot_env()
                
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
        
    def load_userbot_env(self) -> None:
        """
        从.env.userbot文件加载User Bot环境变量
        
        如果.env.userbot文件不存在，会记录警告但不会抛出异常
        """
        if os.path.exists(self.userbot_env_path):
            # 加载User Bot环境变量但不设置到os.environ中，防止影响全局环境
            with open(self.userbot_env_path) as f:
                self.userbot_env_vars = dotenv.dotenv_values(stream=f)
            self.logger.info(f"从 {self.userbot_env_path} 加载User Bot环境变量")
        else:
            self.userbot_env_vars = {}
            self.logger.warning(f"{self.userbot_env_path} 文件不存在，无法加载User Bot环境变量")
            
    def create_default_userbot_env(self) -> None:
        """
        创建默认User Bot环境变量文件
        
        如果.env.userbot文件不存在，创建一个包含注释和默认值的.env.userbot文件
        """
        default_content = """# User Bot环境变量配置文件
# 此文件包含User Bot的专用配置

# Telegram API凭据（必需）
# USER_API_ID=your_api_id
# USER_API_HASH=your_api_hash

# 会话名称（可选，默认为user_bot_session）
USER_SESSION_NAME=user_bot_session

# 其他配置项
# USER_PROXY_URL=socks5://user:pass@host:port
"""
        with open(self.userbot_env_path, "w", encoding="utf-8") as f:
            f.write(default_content)
            
        self.logger.info(f"已创建默认User Bot环境变量文件 {self.userbot_env_path}")

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
        
        # 创建.env.userbot.example
        userbot_env_example_content = """# User Bot环境变量配置文件示例
# 此文件包含User Bot的专用配置

# Telegram API凭据（必需）
USER_API_ID=your_api_id_here
USER_API_HASH=your_api_hash_here

# 会话名称（可选，默认为user_bot_session）
USER_SESSION_NAME=user_bot_session

# 其他配置项
# USER_PROXY_URL=socks5://user:pass@host:port
"""
        userbot_env_example_path = f"{self.userbot_env_path}.example"
        with open(userbot_env_example_path, "w", encoding="utf-8") as f:
            f.write(userbot_env_example_content)
            
        self.logger.info(f"已创建User Bot环境变量文件示例 {userbot_env_example_path}")

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
        
    def get_userbot_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        获取User Bot环境变量
        
        Args:
            key: 环境变量名
            default: 默认值，如果环境变量不存在则返回此值
            
        Returns:
            环境变量的值，如果不存在则返回默认值
        """
        return self.userbot_env_vars.get(key, default)
        
    def set_userbot_env(self, key: str, value: str) -> None:
        """
        设置User Bot环境变量
        
        Args:
            key: 环境变量名
            value: 环境变量值
        """
        self.userbot_env_vars[key] = value
        self.save_userbot_env()
        self.logger.info(f"已设置User Bot环境变量 {key}")
        
    def save_userbot_env(self) -> None:
        """
        保存User Bot环境变量到文件
        """
        # 构建环境变量文件内容
        content = "# User Bot环境变量配置文件\n"
        content += "# 此文件包含User Bot的专用配置\n\n"
        
        # 添加所有环境变量
        for key, value in self.userbot_env_vars.items():
            content += f"{key}={value}\n"
            
        # 写入文件
        with open(self.userbot_env_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        self.logger.info(f"已保存User Bot环境变量到 {self.userbot_env_path}")
        
    def get_userbot_config_dict(self, exclude_sensitive: bool = True) -> Dict[str, str]:
        """
        获取User Bot配置字典，用于显示给用户
        
        Args:
            exclude_sensitive: 是否排除敏感信息（如API_HASH），默认为True
            
        Returns:
            User Bot配置字典
        """
        result = {}
        
        # 复制所有环境变量
        for key, value in self.userbot_env_vars.items():
            # 排除敏感信息
            if exclude_sensitive and key in ["USER_API_HASH"]:
                value = "******"  # 用星号替换敏感信息
                
            result[key] = value
            
        return result
        
    def delete_userbot_env(self, key: str) -> bool:
        """
        删除User Bot环境变量
        
        Args:
            key: 要删除的环境变量名
            
        Returns:
            是否成功删除（如不存在则返回False）
        """
        if key not in self.userbot_env_vars:
            self.logger.info(f"User Bot环境变量 {key} 不存在，无需删除")
            return False
            
        del self.userbot_env_vars[key]
        self.save_userbot_env()
        self.logger.info(f"已删除User Bot环境变量 {key}")
        return True


class SyncPointManager:
    """
    同步点管理器类
    
    负责管理和持久化聊天的同步点信息，包括：
    1. 加载同步点信息
    2. 获取特定聊天的同步点
    3. 更新同步点信息
    """
    
    def __init__(self, sync_points_path: str = "sync_points.json") -> None:
        """
        初始化同步点管理器
        
        Args:
            sync_points_path: 同步点文件的路径，默认为项目根目录下的sync_points.json
        """
        self.logger = logging.getLogger(__name__)
        self.sync_points_path = sync_points_path
        self.sync_points: Dict[str, Dict[str, Any]] = {}
        
        # 加载同步点信息
        self.load_sync_points()
        
    def load_sync_points(self) -> None:
        """
        从文件加载同步点信息
        
        如果文件不存在，会初始化为空字典
        """
        if os.path.exists(self.sync_points_path):
            try:
                with open(self.sync_points_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "sync_points" in data:
                        self.sync_points = data["sync_points"]
                    else:
                        self.sync_points = {}
                        self.logger.warning(f"同步点文件 {self.sync_points_path} 格式错误，已初始化为空")
                self.logger.info(f"从 {self.sync_points_path} 加载同步点信息，共 {len(self.sync_points)} 个聊天")
            except Exception as e:
                self.sync_points = {}
                self.logger.error(f"加载同步点文件 {self.sync_points_path} 时出错: {e}")
        else:
            self.sync_points = {}
            self.logger.info(f"{self.sync_points_path} 文件不存在，已初始化为空")
            
    def save_sync_points(self) -> None:
        """
        保存同步点信息到文件
        """
        data = {
            "sync_points": self.sync_points,
            "updated_at": int(time.time())
        }
        
        with open(self.sync_points_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        self.logger.info(f"已保存同步点信息到 {self.sync_points_path}，共 {len(self.sync_points)} 个聊天")
        
    def get_sync_point(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """
        获取特定聊天的同步点信息
        
        Args:
            chat_id: 聊天ID
            
        Returns:
            同步点信息字典，包含message_id、date等，如不存在则返回None
        """
        chat_id_str = str(chat_id)  # JSON中的键必须是字符串
        return self.sync_points.get(chat_id_str)
        
    def update_sync_point(self, chat_id: int, message_id: int, date: Union[datetime, int], additional_info: Optional[Dict[str, Any]] = None) -> None:
        """
        更新特定聊天的同步点信息
        
        Args:
            chat_id: 聊天ID
            message_id: 消息ID
            date: 消息日期（datetime对象或时间戳）
            additional_info: 其他额外信息，可选
        """
        chat_id_str = str(chat_id)  # JSON中的键必须是字符串
        
        # 转换date为时间戳
        if isinstance(date, datetime):
            date_timestamp = int(date.timestamp())
        else:
            date_timestamp = date
            
        # 创建同步点信息
        sync_point = {
            "message_id": message_id,
            "date": date_timestamp,
            "updated_at": int(time.time())
        }
        
        # 添加额外信息
        if additional_info and isinstance(additional_info, dict):
            sync_point.update(additional_info)
            
        # 更新同步点
        self.sync_points[chat_id_str] = sync_point
        
        # 保存到文件
        self.save_sync_points()
        
        self.logger.debug(f"更新聊天 {chat_id} 的同步点: message_id={message_id}, date={date_timestamp}")
        
    def delete_sync_point(self, chat_id: int) -> bool:
        """
        删除特定聊天的同步点信息
        
        Args:
            chat_id: 聊天ID
            
        Returns:
            是否成功删除（如不存在则返回False）
        """
        chat_id_str = str(chat_id)
        if chat_id_str not in self.sync_points:
            self.logger.info(f"聊天 {chat_id} 的同步点不存在，无需删除")
            return False
            
        del self.sync_points[chat_id_str]
        self.save_sync_points()
        self.logger.info(f"已删除聊天 {chat_id} 的同步点")
        return True
        
    def reset_all_sync_points(self) -> None:
        """
        重置所有同步点信息
        """
        self.sync_points = {}
        self.save_sync_points()
        self.logger.info("已重置所有同步点信息")