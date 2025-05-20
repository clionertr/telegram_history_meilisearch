"""
Userbot 事件处理模块

此模块提供 Telegram 事件处理功能，包括：
1. 处理新消息事件
2. 处理消息编辑事件
3. 将符合条件的消息索引到 Meilisearch
"""

import logging
from typing import Optional, Dict, Any

from telethon import events, TelegramClient
from telethon.tl.types import User, Chat, Channel

from core.config_manager import ConfigManager
from core.meilisearch_service import MeiliSearchService
from core.models import MeiliMessageDoc
from user_bot.utils import generate_message_link, format_sender_name, determine_chat_type

# 配置日志记录器
logger = logging.getLogger(__name__)

# 模块级别的服务实例
_config_manager: Optional[ConfigManager] = None
_meili_search_service: Optional[MeiliSearchService] = None


def get_config_manager() -> ConfigManager:
    """
    获取 ConfigManager 单例实例
    
    Returns:
        ConfigManager: 配置管理器实例
    """
    global _config_manager
    if _config_manager is None:
        logger.info("初始化 ConfigManager 实例")
        _config_manager = ConfigManager()
    return _config_manager


def get_meili_search_service() -> MeiliSearchService:
    """
    获取 MeiliSearchService 单例实例
    
    如果 MeiliSearchService 实例不存在，则创建一个新实例。
    使用 ConfigManager 获取 Meilisearch 的连接配置。
    
    Returns:
        MeiliSearchService: Meilisearch 服务实例
    """
    global _meili_search_service
    if _meili_search_service is None:
        logger.info("初始化 MeiliSearchService 实例")
        
        config = get_config_manager()
        
        # 从环境变量获取配置
        host = config.get_env("MEILISEARCH_HOST")
        api_key = config.get_env("MEILISEARCH_API_KEY")
        
        # 如果环境变量中没有配置，从配置文件获取
        if not host:
            host = config.get_config("MeiliSearch", "HOST", "http://localhost:7700")
        if not api_key:
            api_key = config.get_config("MeiliSearch", "API_KEY")
            
        _meili_search_service = MeiliSearchService(host=host, api_key=api_key)
        
    return _meili_search_service


def extract_message_data(event) -> Dict[str, Any]:
    """
    从事件对象中提取消息数据
    
    Args:
        event: Telethon 事件对象
        
    Returns:
        Dict[str, Any]: 包含消息数据的字典
    """
    message = event.message
    chat = event.chat
    sender = event.sender
    
    # 提取 chat_title
    chat_title = None
    if hasattr(chat, 'title') and chat.title:
        chat_title = chat.title
    
    # 提取 sender_name
    sender_name = None
    if isinstance(sender, User) and sender:
        sender_name = format_sender_name(sender.first_name, sender.last_name)
    
    # 确定聊天类型
    chat_type = determine_chat_type(event)
    
    # 生成消息 ID
    doc_id = f"{message.chat_id}_{message.id}"
    
    # 生成消息链接
    message_link = generate_message_link(message.chat_id, message.id)
    
    # 提取消息文本
    text = message.text or message.message or ""
    
    # 将事件数据整合为字典
    message_data = {
        "id": doc_id,
        "message_id": message.id,
        "chat_id": message.chat_id,
        "chat_title": chat_title,
        "chat_type": chat_type,
        "sender_id": sender.id if sender else 0,
        "sender_name": sender_name,
        "text": text,
        "date": int(message.date.timestamp()),
        "message_link": message_link
    }
    
    return message_data


async def handle_new_message(event) -> None:
    """
    处理新消息事件
    
    此处理器将符合条件的消息索引到 Meilisearch：
    1. 检查消息来源是否在白名单中
    2. 提取消息数据并构建 MeiliMessageDoc 实例
    3. 将消息索引到 Meilisearch
    
    Args:
        event: Telethon 事件对象
    """
    try:
        # 提取 chat_id
        chat_id = event.chat_id
        
        # 检查白名单
        config_manager = get_config_manager()
        if not config_manager.is_in_whitelist(chat_id):
            logger.debug(f"忽略非白名单消息: chat_id={chat_id}")
            return
        
        logger.info(f"处理来自白名单的新消息: chat_id={chat_id}, message_id={event.message.id}")
        
        # 提取消息数据
        message_data = extract_message_data(event)
        
        # 构建 MeiliMessageDoc 实例
        message_doc = MeiliMessageDoc(**message_data)
        
        # 索引消息
        meili_service = get_meili_search_service()
        result = meili_service.index_message(message_doc)
        
        logger.info(f"消息索引成功: id={message_doc.id}, task_id={result.get('taskUid', 'unknown')}")
        
    except Exception as e:
        logger.error(f"处理新消息时发生错误: {str(e)}", exc_info=True)


async def handle_message_edited(event) -> None:
    """
    处理消息编辑事件
    
    此处理器将更新 Meilisearch 中已索引的消息：
    1. 检查消息来源是否在白名单中
    2. 提取消息数据并构建 MeiliMessageDoc 实例
    3. 更新 Meilisearch 中的消息（通过替换同 ID 文档）
    
    Args:
        event: Telethon 事件对象
    """
    try:
        # 提取 chat_id
        chat_id = event.chat_id
        
        # 检查白名单
        config_manager = get_config_manager()
        if not config_manager.is_in_whitelist(chat_id):
            logger.debug(f"忽略非白名单消息编辑: chat_id={chat_id}")
            return
        
        logger.info(f"处理来自白名单的消息编辑: chat_id={chat_id}, message_id={event.message.id}")
        
        # 提取消息数据
        message_data = extract_message_data(event)
        
        # 构建 MeiliMessageDoc 实例
        message_doc = MeiliMessageDoc(**message_data)
        
        # 更新索引中的消息
        # 由于 Meilisearch 会自动替换同 ID 的文档，我们可以直接使用 index_message 方法
        meili_service = get_meili_search_service()
        result = meili_service.index_message(message_doc)
        
        logger.info(f"消息更新成功: id={message_doc.id}, task_id={result.get('taskUid', 'unknown')}")
        logger.debug(f"更新策略: 使用文档替换方式更新索引中的消息")
        
    except Exception as e:
        logger.error(f"处理消息编辑时发生错误: {str(e)}", exc_info=True)


# 事件处理器注册说明
"""
为了注册上述事件处理器，应在 Userbot 的启动逻辑中添加以下代码：

```python
from user_bot import event_handlers
from telethon import events

# 获取 Telethon 客户端实例
client = user_bot_client_instance.get_client()

# 注册新消息处理器
client.add_event_handler(
    event_handlers.handle_new_message,
    events.NewMessage()
)

# 注册消息编辑处理器
client.add_event_handler(
    event_handlers.handle_message_edited,
    events.MessageEdited()
)
```

注意事项:
1. 确保在客户端连接成功后再注册事件处理器
2. 可以通过 events.NewMessage() 和 events.MessageEdited() 的参数来过滤事件
   例如: events.NewMessage(chats=whitelist) 只处理特定聊天的消息
3. 事件处理器会在后台异步执行，不会阻塞主线程
"""