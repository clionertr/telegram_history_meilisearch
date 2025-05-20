"""
Userbot 工具函数模块

此模块提供各种工具函数，用于支持 Userbot 的功能，包括：
1. 生成 Telegram 消息链接
2. 其他辅助功能
"""

import logging
from typing import Union

# 配置日志记录器
logger = logging.getLogger(__name__)


def generate_message_link(chat_id: int, message_id: int) -> str:
    """
    生成 Telegram 消息链接
    
    根据 chat_id 和 message_id 生成可点击的 Telegram 消息链接。
    不同类型的聊天(用户、群组、频道)可能有不同的链接格式。
    
    Args:
        chat_id: 聊天 ID (正数表示用户，负数表示群组/频道)
        message_id: 消息 ID
        
    Returns:
        str: Telegram 消息链接
    """
    # 处理不同类型的聊天
    # - 用户聊天通常是正数 ID
    # - 群组和频道是负数 ID，需要取绝对值并使用 c/ 路径
    
    # 简化实现：所有消息都使用 c/ 路径格式
    # 注意：这是一个简化的实现，实际的链接格式可能需要根据 Telegram API 的具体行为进行调整
    abs_chat_id = abs(chat_id)
    link = f"https://t.me/c/{abs_chat_id}/{message_id}"
    
    logger.debug(f"为消息生成链接: chat_id={chat_id}, message_id={message_id}, link={link}")
    return link


def format_sender_name(first_name: Union[str, None], last_name: Union[str, None]) -> str:
    """
    格式化发送者姓名
    
    组合 first_name 和 last_name，处理可能的 None 值
    
    Args:
        first_name: 发送者的名字，可能为 None
        last_name: 发送者的姓，可能为 None
        
    Returns:
        str: 格式化后的发送者姓名
    """
    if first_name and last_name:
        return f"{first_name} {last_name}"
    elif first_name:
        return first_name
    elif last_name:
        return last_name
    else:
        return "Unknown"


def determine_chat_type(event) -> str:
    """
    根据事件对象确定聊天类型
    
    Args:
        event: Telethon 事件对象
        
    Returns:
        str: 聊天类型 ("user", "group", "channel")
    """
    if event.is_private:
        return "user"
    elif event.is_group:
        return "group"
    elif event.is_channel:
        return "channel"
    else:
        # 默认为 group，以防无法确定
        logger.warning(f"无法确定聊天类型: {event}, 默认为 'group'")
        return "group"