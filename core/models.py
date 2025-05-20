"""
数据模型模块

此模块定义了应用程序使用的数据模型，主要包括：
1. MeiliMessageDoc: Meilisearch中存储的Telegram消息文档结构
"""

from typing import Optional, Literal
from pydantic import BaseModel


class MeiliMessageDoc(BaseModel):
    """
    Meilisearch中存储的Telegram消息文档模型
    
    此模型定义了Telegram消息在Meilisearch中的索引结构，包含消息的基本信息、
    发送者信息、所属聊天信息以及消息链接等。
    """
    
    id: str  # 唯一标识，通常由chat_id和message_id组合生成，如f"{chat_id}_{message_id}"
    message_id: int  # Telegram消息ID
    chat_id: int  # 聊天ID
    chat_title: Optional[str] = None  # 聊天标题，可能为空
    chat_type: Literal["user", "group", "channel"]  # 聊天类型：用户、群组或频道
    sender_id: int  # 发送者ID
    sender_name: Optional[str] = None  # 发送者名称，可能为空
    text: str  # 消息文本内容
    date: int  # 消息发送时间的Unix时间戳
    message_link: str  # Telegram消息链接