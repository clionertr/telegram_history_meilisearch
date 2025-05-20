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
    不同类型的聊天(用户、群组、频道)有不同的链接格式。
    
    链接格式说明:
    1. 超级群组和频道: t.me/c/{chat_id}/{message_id} (需取chat_id绝对值)
    2. 用户私聊: 通常不能通过公共链接访问，但在某些情况下可使用 t.me/{username}/{message_id}
       由于我们没有username信息，对用户私聊也使用 c/ 格式
    
    Args:
        chat_id: 聊天 ID (正数通常表示用户，负数表示群组/频道)
        message_id: 消息 ID
        
    Returns:
        str: Telegram 消息链接
    """
    # 获取绝对值，去掉可能的负号
    abs_chat_id = abs(chat_id)
    
    # 根据chat_id的符号判断聊天类型
    # 注意：这是基于一般规则的判断，可能存在例外情况
    if chat_id < 0:
        # 负数ID: 通常是超级群组或频道，使用c/路径格式
        link = f"https://t.me/c/{abs_chat_id}/{message_id}"
        logger.debug(f"为群组/频道消息生成链接: chat_id={chat_id}, link={link}")
    else:
        # 正数ID: 通常是用户私聊
        # 私聊消息一般无法通过公共链接访问，除非是与机器人的对话
        # 我们也使用c/路径尝试生成链接，但这可能不适用于所有情况
        link = f"https://t.me/c/{abs_chat_id}/{message_id}"
        logger.debug(f"为用户私聊消息生成链接: chat_id={chat_id}, link={link}")
        # 注意：如果已知username，理想的形式是 f"https://t.me/{username}/{message_id}"
    
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