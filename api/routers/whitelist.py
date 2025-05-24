"""
白名单管理 API 路由模块

此模块负责：
1. 定义白名单管理相关的 API 端点
2. 创建请求和响应数据模型
3. 调用 ConfigManager 执行白名单操作
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, Field

from core.config_manager import ConfigManager
from api.dependencies import get_config_manager


# 定义数据模型
class WhitelistEntry(BaseModel):
    """白名单项模型"""
    chat_id: int = Field(..., description="用户/群组/频道ID")
    is_group: Optional[bool] = Field(None, description="是否是群组ID，基于ID为负数判断")


class WhitelistResponse(BaseModel):
    """白名单响应模型"""
    whitelist: List[int] = Field(..., description="白名单ID列表")
    count: int = Field(..., description="白名单项数量")


class WhitelistAddRequest(BaseModel):
    """添加白名单请求模型"""
    chat_id: int = Field(..., description="要添加的用户/群组/频道ID")


class WhitelistActionResponse(BaseModel):
    """白名单操作响应模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="操作结果描述")
    chat_id: int = Field(..., description="操作的用户/群组/频道ID")


class TimestampSetting(BaseModel):
    """时间戳设置模型"""
    timestamp: Optional[Union[str, int]] = Field(None, description="ISO 8601格式的时间戳或Unix时间戳，None表示移除设置")


class TimestampResponse(BaseModel):
    """时间戳响应模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="操作结果描述")
    chat_id: Optional[int] = Field(None, description="操作的聊天ID，全局设置时为null")
    timestamp: Optional[Union[str, int]] = Field(None, description="设置的时间戳")


# 创建路由器
router = APIRouter(
    prefix="/admin/whitelist",
    tags=["admin", "whitelist"],
    responses={
        404: {"description": "Not found"},
        403: {"description": "Forbidden"}
    },
)


@router.get("", response_model=WhitelistResponse)
async def get_whitelist(
    config_manager: ConfigManager = Depends(get_config_manager)
) -> Dict[str, Any]:
    """
    获取白名单列表
    
    返回当前白名单中的所有 ID
    
    Args:
        config_manager: ConfigManager 实例，通过依赖注入获取
        
    Returns:
        包含白名单列表和数量的字典
    """
    logger = logging.getLogger(__name__)
    logger.info("获取白名单列表")
    
    try:
        whitelist = config_manager.get_whitelist()
        return {
            "whitelist": whitelist,
            "count": len(whitelist)
        }
    except Exception as e:
        logger.error(f"获取白名单列表时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取白名单失败: {str(e)}")


@router.post("", response_model=WhitelistActionResponse, status_code=status.HTTP_201_CREATED)
async def add_to_whitelist(
    request: WhitelistAddRequest,
    config_manager: ConfigManager = Depends(get_config_manager)
) -> Dict[str, Any]:
    """
    添加 ID 到白名单
    
    将指定的 chat_id 添加到白名单
    
    Args:
        request: 包含要添加的 chat_id 的请求模型
        config_manager: ConfigManager 实例，通过依赖注入获取
        
    Returns:
        操作结果信息
    """
    logger = logging.getLogger(__name__)
    logger.info(f"添加 ID {request.chat_id} 到白名单")
    
    try:
        success = config_manager.add_to_whitelist(request.chat_id)
        message = "ID 已成功添加到白名单" if success else "ID 已在白名单中，无需添加"
        return {
            "success": success,
            "message": message,
            "chat_id": request.chat_id
        }
    except Exception as e:
        logger.error(f"添加 ID 到白名单时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加到白名单失败: {str(e)}")


@router.delete("/{chat_id}", response_model=WhitelistActionResponse)
async def remove_from_whitelist(
    chat_id: int = Path(..., description="要从白名单移除的用户/群组/频道ID"),
    config_manager: ConfigManager = Depends(get_config_manager)
) -> Dict[str, Any]:
    """
    从白名单移除 ID
    
    将指定的 chat_id 从白名单中移除
    
    Args:
        chat_id: 要移除的用户/群组/频道ID
        config_manager: ConfigManager 实例，通过依赖注入获取
        
    Returns:
        操作结果信息
    """
    logger = logging.getLogger(__name__)
    logger.info(f"从白名单移除 ID {chat_id}")
    
    try:
        success = config_manager.remove_from_whitelist(chat_id)
        message = "ID 已成功从白名单移除" if success else "ID 不在白名单中，无需移除"
        return {
            "success": success,
            "message": message,
            "chat_id": chat_id
        }
    except Exception as e:
        logger.error(f"从白名单移除 ID 时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"从白名单移除失败: {str(e)}")


@router.delete("", response_model=WhitelistActionResponse)
async def reset_whitelist(
    config_manager: ConfigManager = Depends(get_config_manager)
) -> Dict[str, Any]:
    """
    重置白名单
    
    清空整个白名单
    
    Args:
        config_manager: ConfigManager 实例，通过依赖注入获取
        
    Returns:
        操作结果信息
    """
    logger = logging.getLogger(__name__)
    logger.info("重置白名单")
    
    try:
        config_manager.reset_whitelist()
        return {
            "success": True,
            "message": "白名单已成功重置",
            "chat_id": 0  # 由于没有特定的 chat_id，使用 0 作为占位符
        }
    except Exception as e:
        logger.error(f"重置白名单时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重置白名单失败: {str(e)}")


@router.get("/sync_settings", response_model=Dict[str, Any])
async def get_sync_settings(
    config_manager: ConfigManager = Depends(get_config_manager)
) -> Dict[str, Any]:
    """
    获取同步设置信息
    
    返回当前的同步设置，包括全局和聊天特定的最旧同步时间戳
    
    Args:
        config_manager: ConfigManager 实例，通过依赖注入获取
        
    Returns:
        包含同步设置的字典
    """
    logger = logging.getLogger(__name__)
    logger.info("获取同步设置")
    
    try:
        sync_settings = config_manager.sync_settings or {}
        return {
            "sync_settings": sync_settings,
        }
    except Exception as e:
        logger.error(f"获取同步设置时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取同步设置失败: {str(e)}")


@router.put("/sync_settings/global", response_model=TimestampResponse)
async def set_global_oldest_sync_timestamp(
    request: TimestampSetting,
    config_manager: ConfigManager = Depends(get_config_manager)
) -> Dict[str, Any]:
    """
    设置全局最旧同步时间戳
    
    设置适用于所有聊天的全局最旧同步时间戳
    
    Args:
        request: 包含时间戳的请求模型
        config_manager: ConfigManager 实例，通过依赖注入获取
        
    Returns:
        操作结果信息
    """
    logger = logging.getLogger(__name__)
    logger.info(f"设置全局最旧同步时间戳: {request.timestamp}")
    
    try:
        success = config_manager.set_oldest_sync_timestamp(None, request.timestamp)
        message = "全局最旧同步时间戳已成功设置" if success else "设置全局最旧同步时间戳失败"
        return {
            "success": success,
            "message": message,
            "chat_id": None,
            "timestamp": request.timestamp
        }
    except Exception as e:
        logger.error(f"设置全局最旧同步时间戳时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"设置全局最旧同步时间戳失败: {str(e)}")


@router.put("/sync_settings/chat/{chat_id}", response_model=TimestampResponse)
async def set_chat_oldest_sync_timestamp(
    request: TimestampSetting,
    chat_id: int = Path(..., description="聊天ID"),
    config_manager: ConfigManager = Depends(get_config_manager)
) -> Dict[str, Any]:
    """
    设置特定聊天的最旧同步时间戳
    
    为指定的聊天设置最旧同步时间戳，覆盖全局设置
    
    Args:
        request: 包含时间戳的请求模型
        chat_id: 聊天ID
        config_manager: ConfigManager 实例，通过依赖注入获取
        
    Returns:
        操作结果信息
    """
    logger = logging.getLogger(__name__)
    logger.info(f"设置聊天 {chat_id} 的最旧同步时间戳: {request.timestamp}")
    
    try:
        success = config_manager.set_oldest_sync_timestamp(chat_id, request.timestamp)
        message = f"聊天 {chat_id} 的最旧同步时间戳已成功设置" if success else f"设置聊天 {chat_id} 的最旧同步时间戳失败"
        return {
            "success": success,
            "message": message,
            "chat_id": chat_id,
            "timestamp": request.timestamp
        }
    except Exception as e:
        logger.error(f"设置聊天 {chat_id} 的最旧同步时间戳时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"设置聊天的最旧同步时间戳失败: {str(e)}")


@router.get("/sync_settings/chat/{chat_id}", response_model=TimestampResponse)
async def get_chat_oldest_sync_timestamp(
    chat_id: int = Path(..., description="聊天ID"),
    config_manager: ConfigManager = Depends(get_config_manager)
) -> Dict[str, Any]:
    """
    获取特定聊天的最旧同步时间戳
    
    获取应用于指定聊天的最旧同步时间戳（特定设置或全局设置）
    
    Args:
        chat_id: 聊天ID
        config_manager: ConfigManager 实例，通过依赖注入获取
        
    Returns:
        包含时间戳的响应信息
    """
    logger = logging.getLogger(__name__)
    logger.info(f"获取聊天 {chat_id} 的最旧同步时间戳")
    
    try:
        timestamp = config_manager.get_oldest_sync_timestamp(chat_id)
        timestamp_str = timestamp.isoformat() if timestamp else None
        
        return {
            "success": True,
            "message": "成功获取最旧同步时间戳",
            "chat_id": chat_id,
            "timestamp": timestamp_str
        }
    except Exception as e:
        logger.error(f"获取聊天 {chat_id} 的最旧同步时间戳时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取最旧同步时间戳失败: {str(e)}")