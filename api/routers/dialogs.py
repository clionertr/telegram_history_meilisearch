from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Any, Optional
# 假设 user_bot_client 是一个可以获取 UserBot 客户端实例的依赖项或全局变量
# from ...user_bot.client import get_user_bot_client_instance # 这种相对导入可能需要调整
# 临时的处理方式，直到我们有更好的 UserBot 客户端注入方式
from user_bot.client import UserBotClient # 直接导入，假设 UserBotClient 可以被实例化或有一个全局实例
from core.config_manager import ConfigManager # 假设配置管理器可以这样导入
import logging
from user_bot import user_bot_client

logger = logging.getLogger(__name__)

router = APIRouter()

# 示例：如何获取 UserBotClient 实例 (这部分需要根据项目实际情况调整)
# 这是一个简化的例子，实际项目中 UserBotClient 的实例化和管理会更复杂
# 可能需要一个依赖注入系统或者一个全局的客户端实例
async def get_user_bot_client():
    # 这里需要一个有效的方式来获取或创建 UserBotClient 实例
    # 例如，从应用状态、依赖注入容器，或者一个已经初始化好的全局实例
    # 以下为占位逻辑，需要替换为实际实现
    try:
        # 尝试从配置中获取必要的参数来初始化客户端
        # 这只是一个示例，实际的初始化参数和方式可能不同
        config = ConfigManager()
        api_id = config.get_telegram_api_id()
        api_hash = config.get_telegram_api_hash()
        # 假设 UserBotClient 有一个 get_instance 或类似的静态方法
        # 或者你需要在这里实例化它
        # client = await UserBotClient.get_running_instance() # 如果有这样的方法
        # 或者 client = UserBotClient(api_id, api_hash, ...)
        # 这是一个非常粗略的占位符，实际实现会复杂得多
        
        # 临时解决方案：尝试直接使用 UserBotClient 的方法
        # 这假设 UserBotClient 有一个可以直接调用的静态方法或类似机制
        # 或者 UserBotClient 实例在某处被全局管理
        # 注意：这部分非常依赖 UserBotClient 的具体实现
        if not hasattr(UserBotClient, 'instance') or UserBotClient.instance is None:
             # 尝试创建一个实例，但这可能不是正确的方式，取决于 UserBotClient 的设计
             # UserBotClient.instance = UserBotClient(api_id, api_hash, "user_bot.session") # 示例
             # raise HTTPException(status_code=503, detail="UserBot client is not available.")
             # 更好的做法是让 UserBotClient 在应用启动时初始化并提供一个获取实例的方法
             # 暂时返回 None，并在下面处理
             print("Warning: UserBotClient instance not found. API will likely fail.")
             return None


        return UserBotClient.instance # 假设有一个全局实例
    except Exception as e:
        print(f"Error getting UserBot client: {e}")
        raise HTTPException(status_code=500, detail=f"Could not get UserBot client: {str(e)}")

@router.get("/dialogs")
async def get_dialogs(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    limit: int = Query(20, ge=1, le=100, description="每页显示的对话数量，最大100"),
    include_avatars: bool = Query(True, description="是否包含头像，设置为false可大幅提升加载速度")
):
    """
    获取用户的对话列表，支持分页
    
    - **page**: 页码，从1开始
    - **limit**: 每页显示的对话数量，最大100
    - **include_avatars**: 是否包含头像，设置为false可大幅提升加载速度
    
    返回对话信息列表，包含分页信息。每个对话包含：
    - id: 对话ID
    - name: 对话名称
    - type: 对话类型 (user/group/channel)
    - unread_count: 未读消息数
    - date: 最后一条消息时间戳
    - avatar_base64: 头像数据 (仅当include_avatars=true时)
    """
    try:
        if not user_bot_client or not hasattr(user_bot_client, '_client') or not user_bot_client._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="UserBot客户端未初始化"
            )

        result = await user_bot_client.get_dialogs_info(
            page=page,
            limit=limit,
            include_avatars=include_avatars
        )
        
        return result
        
    except Exception as e:
        logger.error(f"获取对话列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取对话列表失败: {str(e)}"
        )

@router.get("/dialogs/cache/status")
async def get_cache_status():
    """
    获取会话缓存状态
    
    返回缓存的统计信息，包括：
    - cached_dialogs_count: 缓存的会话数量
    - cached_avatars_count: 缓存的头像数量  
    - cache_valid: 缓存是否有效
    - cache_age_seconds: 缓存年龄（秒）
    """
    try:
        if not user_bot_client or not hasattr(user_bot_client, '_client') or not user_bot_client._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="UserBot客户端未初始化"
            )

        import asyncio
        
        cached_dialogs_count = user_bot_client.get_cached_dialogs_count()
        cached_avatars_count = len(user_bot_client._avatars_cache)
        cache_valid = user_bot_client._is_cache_valid()
        
        # 计算缓存年龄
        cache_age_seconds = None
        if user_bot_client._cache_timestamp:
            current_time = asyncio.get_event_loop().time()
            cache_age_seconds = current_time - user_bot_client._cache_timestamp
        
        return {
            "cached_dialogs_count": cached_dialogs_count,
            "cached_avatars_count": cached_avatars_count,
            "cache_valid": cache_valid,
            "cache_age_seconds": cache_age_seconds,
            "cache_ttl_seconds": user_bot_client._cache_ttl
        }
        
    except Exception as e:
        logger.error(f"获取缓存状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取缓存状态失败: {str(e)}"
        )

@router.post("/dialogs/cache/refresh")
async def refresh_cache():
    """
    手动刷新会话缓存
    
    重新从Telegram获取所有会话的基本信息并更新缓存。
    注意：这不会清除头像缓存。
    """
    try:
        if not user_bot_client or not hasattr(user_bot_client, '_client') or not user_bot_client._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="UserBot客户端未初始化"
            )

        await user_bot_client.refresh_dialogs_cache()
        
        return {
            "success": True,
            "message": "会话缓存已刷新",
            "cached_dialogs_count": user_bot_client.get_cached_dialogs_count()
        }
        
    except Exception as e:
        logger.error(f"刷新缓存失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刷新缓存失败: {str(e)}"
        )

@router.delete("/dialogs/cache/avatars")
async def clear_avatars_cache():
    """
    清除头像缓存
    
    清除所有已缓存的头像数据，下次请求时将重新下载。
    会话基本信息缓存不受影响。
    """
    try:
        if not user_bot_client or not hasattr(user_bot_client, '_client') or not user_bot_client._client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="UserBot客户端未初始化"
            )

        user_bot_client.clear_avatars_cache()
        
        return {
            "success": True,
            "message": "头像缓存已清除"
        }
        
    except Exception as e:
        logger.error(f"清除头像缓存失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清除头像缓存失败: {str(e)}"
        )

# 后续需要将此路由添加到主 FastAPI 应用中