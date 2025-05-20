"""
白名单管理 API 路由模块

此模块负责：
1. 定义白名单管理相关的 API 端点
2. 创建请求和响应数据模型
3. 调用 ConfigManager 执行白名单操作
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Path, status
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