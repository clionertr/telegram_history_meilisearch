from fastapi import APIRouter, Depends, HTTPException
from typing import List, Any
# 假设 user_bot_client 是一个可以获取 UserBot 客户端实例的依赖项或全局变量
# from ...user_bot.client import get_user_bot_client_instance # 这种相对导入可能需要调整
# 临时的处理方式，直到我们有更好的 UserBot 客户端注入方式
from user_bot.client import UserBotClient # 直接导入，假设 UserBotClient 可以被实例化或有一个全局实例
from core.config_manager import ConfigManager # 假设配置管理器可以这样导入

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

@router.get("/dialogs") # 响应模型已调整为包含分页信息的字典
async def get_dialogs_api(
    page: int = 1, 
    limit: int = 20,
    include_avatars: bool = True,  # 新增参数：是否包含头像
    # user_bot: UserBotClient = Depends(get_user_bot_client) # 依赖注入 UserBot 客户端
):
    """
    获取用户的所有会话（dialogs）。
    包含会话ID、会话名称/标题、以及会话类型（用户、群组、频道）。
    支持分页。
    
    参数说明：
    - page: 页码，从1开始
    - limit: 每页显示的会话数量，默认20
    - include_avatars: 是否包含头像，默认True。设置为False可大幅提升加载速度。
    
    返回格式：
    {
        "items": [...],           // 会话列表
        "total": 100,            // 总会话数
        "page": 1,               // 当前页码
        "limit": 20,             // 每页数量
        "total_pages": 5,        // 总页数
        "has_avatars": true      // 是否包含头像数据
    }
    """
    # 获取UserBotClient实例
    try:
        # UserBotClient使用单例模式，通过_instance类变量存储实例
        user_bot = UserBotClient._instance
        
        if not user_bot:
            raise HTTPException(status_code=503, detail="UserBot client is not initialized.")
        
        # 检查客户端是否已连接
        if not user_bot._client or not user_bot._client.is_connected():
            raise HTTPException(status_code=503, detail="UserBot client is not connected.")
            
    except Exception as e:
        print(f"Error getting UserBot client for API: {e}")
        raise HTTPException(status_code=503, detail=f"UserBot client is not available: {str(e)}")

    try:
        # 调用 UserBotClient 中的 get_dialogs_info 方法
        # 注意：get_dialogs_info 方法需要支持分页参数和头像参数
        dialogs_info = await user_bot.get_dialogs_info(page=page, limit=limit, include_avatars=include_avatars)
        
        if dialogs_info is None:
             raise HTTPException(status_code=500, detail="Failed to retrieve dialogs from UserBot.")
        return dialogs_info
    except AttributeError as e:
        # 如果 get_dialogs_info 方法不存在或不支持分页参数
        print(f"AttributeError in get_dialogs_api: {e}")
        raise HTTPException(status_code=501, detail=f"UserBot's get_dialogs_info method is not implemented or does not support pagination: {e}")
    except Exception as e:
        print(f"Error calling get_dialogs_info: {e}")
        # 可以根据具体的异常类型返回不同的错误码
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching dialogs: {str(e)}")

# 后续需要将此路由添加到主 FastAPI 应用中