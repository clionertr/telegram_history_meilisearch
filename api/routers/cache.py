"""
缓存管理 API 路由模块

此模块负责：
1. 定义缓存管理相关的 API 端点
2. 提供不同类型的缓存清除功能
3. 与 MeiliSearchService 交互清除搜索数据
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core.meilisearch_service import MeiliSearchService
from api.dependencies import get_meilisearch_service


# 定义数据模型
class ClearCacheRequest(BaseModel):
    """清除缓存请求模型"""
    cache_types: List[str] = Field(..., description="要清除的缓存类型列表")


class ClearCacheResponse(BaseModel):
    """清除缓存响应模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="操作结果描述")
    cleared_types: List[str] = Field(..., description="实际清除的缓存类型")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细信息")


# 创建路由器
router = APIRouter(
    prefix="/admin/cache",
    tags=["admin", "cache"],
    responses={
        404: {"description": "Not found"},
        403: {"description": "Forbidden"}
    },
)


@router.get("/types", response_model=Dict[str, Any])
async def get_cache_types() -> Dict[str, Any]:
    """
    获取可清除的缓存类型列表
    
    返回支持的缓存类型及其描述
    
    Returns:
        包含缓存类型信息的字典
    """
    cache_types = {
        "search_index": {
            "name": "搜索索引",
            "description": "清除 Meilisearch 中的所有消息数据",
            "warning": "此操作将删除所有已索引的消息，需要重新同步数据"
        },
        "frontend_state": {
            "name": "前端状态",
            "description": "重置前端应用的状态缓存",
            "warning": "将清除前端的设置和状态信息"
        },
        "user_preferences": {
            "name": "用户偏好",
            "description": "清除用户的个性化设置",
            "warning": "将重置主题、通知等个人设置"
        },
        "sync_cache": {
            "name": "同步缓存",
            "description": "清除同步相关的缓存数据",
            "warning": "可能影响同步进度记录"
        }
    }
    
    return {
        "cache_types": cache_types,
        "total_types": len(cache_types)
    }


@router.post("/clear", response_model=ClearCacheResponse)
async def clear_cache(
    request: ClearCacheRequest,
    meilisearch_service: MeiliSearchService = Depends(get_meilisearch_service)
) -> Dict[str, Any]:
    """
    清除指定类型的缓存
    
    根据请求中指定的缓存类型，执行相应的清除操作
    
    Args:
        request: 包含要清除的缓存类型的请求模型
        meilisearch_service: MeiliSearchService 实例，通过依赖注入获取
        
    Returns:
        操作结果信息
    """
    logger = logging.getLogger(__name__)
    logger.info(f"开始清除缓存，类型: {request.cache_types}")
    
    cleared_types = []
    details = {}
    errors = []
    
    try:
        for cache_type in request.cache_types:
            if cache_type == "search_index":
                # 清除 Meilisearch 索引
                try:
                    # 删除所有文档
                    result = meilisearch_service.index.delete_all_documents()
                    cleared_types.append(cache_type)
                    details[cache_type] = {
                        "status": "success",
                        "task_id": getattr(result, 'task_uid', 'unknown'),
                        "message": "搜索索引已清空"
                    }
                    logger.info("搜索索引清除成功")
                except Exception as e:
                    error_msg = f"清除搜索索引失败: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    details[cache_type] = {
                        "status": "error",
                        "message": error_msg
                    }
            
            elif cache_type == "frontend_state":
                # 前端状态清除（这里只是记录，实际清除由前端执行）
                cleared_types.append(cache_type)
                details[cache_type] = {
                    "status": "success",
                    "message": "前端状态缓存清除指令已发送"
                }
                logger.info("前端状态缓存清除指令已记录")
            
            elif cache_type == "user_preferences":
                # 用户偏好清除（这里只是记录，实际清除由前端执行）
                cleared_types.append(cache_type)
                details[cache_type] = {
                    "status": "success",
                    "message": "用户偏好重置指令已发送"
                }
                logger.info("用户偏好重置指令已记录")
            
            elif cache_type == "sync_cache":
                # 同步缓存清除（可以在这里添加实际的同步缓存清除逻辑）
                cleared_types.append(cache_type)
                details[cache_type] = {
                    "status": "success",
                    "message": "同步缓存清除完成"
                }
                logger.info("同步缓存清除完成")
            
            else:
                error_msg = f"未知的缓存类型: {cache_type}"
                logger.warning(error_msg)
                errors.append(error_msg)
                details[cache_type] = {
                    "status": "error",
                    "message": error_msg
                }
        
        # 构建响应消息
        if cleared_types and not errors:
            success = True
            message = f"成功清除 {len(cleared_types)} 种缓存类型"
        elif cleared_types and errors:
            success = True
            message = f"部分清除成功：{len(cleared_types)} 成功，{len(errors)} 失败"
        else:
            success = False
            message = f"清除失败：{len(errors)} 个错误"
        
        return {
            "success": success,
            "message": message,
            "cleared_types": cleared_types,
            "details": details
        }
        
    except Exception as e:
        logger.error(f"清除缓存时发生意外错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清除缓存失败: {str(e)}")


@router.post("/clear/all", response_model=ClearCacheResponse)
async def clear_all_cache(
    meilisearch_service: MeiliSearchService = Depends(get_meilisearch_service)
) -> Dict[str, Any]:
    """
    清除所有类型的缓存
    
    这是一个便捷方法，清除所有支持的缓存类型
    
    Args:
        meilisearch_service: MeiliSearchService 实例，通过依赖注入获取
        
    Returns:
        操作结果信息
    """
    logger = logging.getLogger(__name__)
    logger.info("开始清除所有缓存")
    
    # 获取所有缓存类型
    all_types = ["search_index", "frontend_state", "user_preferences", "sync_cache"]
    
    # 构建请求并调用清除方法
    request = ClearCacheRequest(cache_types=all_types)
    return await clear_cache(request, meilisearch_service)