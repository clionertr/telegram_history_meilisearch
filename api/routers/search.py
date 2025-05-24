"""
搜索 API 路由模块

此模块负责：
1. 定义搜索相关的 API 端点
2. 创建请求和响应数据模型
3. 调用 MeilisearchService 执行搜索操作
"""

import logging
import math
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.meilisearch_service import MeiliSearchService
from api.dependencies import get_meilisearch_service


# 定义数据模型
class AdvancedSearchRequest(BaseModel):
    """高级搜索请求模型"""
    query: str = Field(..., description="搜索关键词")
    start_timestamp: Optional[int] = Field(None, description="起始时间的 Unix 时间戳")
    end_timestamp: Optional[int] = Field(None, description="结束时间的 Unix 时间戳")
    chat_types: Optional[List[str]] = Field(None, description="聊天类型列表，可选值: user, group, channel")
    chat_ids: Optional[List[int]] = Field(None, description="聊天 ID 列表")
    page: int = Field(1, ge=1, description="页码，从 1 开始")
    hits_per_page: int = Field(10, ge=1, le=100, description="每页结果数量")


# 保持向后兼容的旧模型
class SearchFilters(BaseModel):
    """搜索过滤条件模型"""
    chat_type: Optional[List[str]] = Field(None, description="聊天类型筛选，可选值: user, group, channel")
    date_from: Optional[int] = Field(None, description="起始日期的 Unix 时间戳")
    date_to: Optional[int] = Field(None, description="结束日期的 Unix 时间戳")


class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: str = Field(..., description="搜索关键词")
    filters: Optional[SearchFilters] = Field(None, description="过滤条件")
    page: int = Field(1, ge=1, description="页码，从 1 开始")
    hits_per_page: int = Field(10, ge=1, le=100, description="每页结果数量")


class SearchResultItem(BaseModel):
    """搜索结果项模型"""
    id: str
    chat_title: Optional[str] = None
    sender_name: Optional[str] = None
    text_snippet: str = Field(..., description="消息文本摘要")
    date: int
    message_link: str


class SearchResponse(BaseModel):
    """搜索响应模型"""
    hits: List[SearchResultItem]
    query: str
    processingTimeMs: int
    limit: int
    offset: int
    estimatedTotalHits: int


# 创建路由器
router = APIRouter(
    prefix="/search",
    tags=["search"],
    responses={404: {"description": "Not found"}},
)


@router.post("/advanced", response_model=SearchResponse)
async def advanced_search_messages(
    search_request: AdvancedSearchRequest,
    meili_service: MeiliSearchService = Depends(get_meilisearch_service)
) -> Dict[str, Any]:
    """
    高级搜索消息 API 端点
    
    支持时间范围、聊天类型和聊天ID的高级过滤功能
    
    Args:
        search_request: 包含查询条件和高级过滤参数的请求模型
        meili_service: MeilisearchService 实例，通过依赖注入获取
        
    Returns:
        符合 SearchResponse 模型的响应字典
    """
    logger = logging.getLogger(__name__)
    logger.info(f"收到高级搜索请求: {search_request.query}, 时间范围: {search_request.start_timestamp}-{search_request.end_timestamp}, "
                f"聊天类型: {search_request.chat_types}, 聊天ID: {search_request.chat_ids}")
    
    try:
        # 设置排序（默认按日期降序）
        sort = ["date:desc"]
        
        # 执行高级搜索
        search_results = meili_service.search(
            query=search_request.query,
            sort=sort,
            page=search_request.page,
            hits_per_page=search_request.hits_per_page,
            start_timestamp=search_request.start_timestamp,
            end_timestamp=search_request.end_timestamp,
            chat_types=search_request.chat_types,
            chat_ids=search_request.chat_ids
        )
        
        # 处理搜索结果
        hits = []
        for hit in search_results.get('hits', []):
            # 创建文本摘要，优先使用高亮结果
            text = hit.get('text', '')
            
            # 检查是否有高亮信息
            if '_formatted' in hit and 'text' in hit['_formatted']:
                text_snippet = hit['_formatted']['text'][:300] + ('...' if len(hit['_formatted']['text']) > 300 else '')
            else:
                text_snippet = text[:200] + ('...' if len(text) > 200 else '')
            
            # 创建结果项
            hit_item = SearchResultItem(
                id=hit.get('id', ''),
                chat_title=hit.get('chat_title', None),
                sender_name=hit.get('sender_name', None),
                text_snippet=text_snippet,
                date=hit.get('date', 0),
                message_link=hit.get('message_link', '')
            )
            hits.append(hit_item)
        
        # 构建响应
        response = {
            "hits": hits,
            "query": search_request.query,
            "processingTimeMs": search_results.get('processingTimeMs', 0),
            "limit": search_request.hits_per_page,
            "offset": (search_request.page - 1) * search_request.hits_per_page,
            "estimatedTotalHits": search_results.get('estimatedTotalHits', 0)
        }
        
        logger.info(f"高级搜索 '{search_request.query}' 找到 {len(hits)} 条结果，estimatedTotalHits={response['estimatedTotalHits']}")
        return response
        
    except Exception as e:
        logger.error(f"高级搜索时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"高级搜索失败: {str(e)}")


@router.post("", response_model=SearchResponse)
async def search_messages(
    search_request: SearchRequest,
    meili_service: MeiliSearchService = Depends(get_meilisearch_service)
) -> Dict[str, Any]:
    """
    搜索消息 API 端点
    
    接收搜索请求，调用 MeilisearchService 执行搜索，并返回格式化的结果
    
    Args:
        search_request: 包含查询条件、过滤条件和分页信息的请求模型
        meili_service: MeilisearchService 实例，通过依赖注入获取
        
    Returns:
        符合 SearchResponse 模型的响应字典
    """
    logger = logging.getLogger(__name__)
    logger.info(f"收到搜索请求: {search_request.query}, 页码: {search_request.page}, 每页结果数: {search_request.hits_per_page}")
    
    try:
        # 构建过滤条件字符串
        filters = None
        if search_request.filters:
            filter_parts = []
            
            # 处理聊天类型过滤
            if search_request.filters.chat_type:
                chat_type_filters = [f"chat_type = '{chat_type}'" for chat_type in search_request.filters.chat_type]
                if chat_type_filters:
                    filter_parts.append(f"({' OR '.join(chat_type_filters)})")
            
            # 处理日期范围过滤
            date_filters = []
            if search_request.filters.date_from:
                date_filters.append(f"date >= {search_request.filters.date_from}")
            if search_request.filters.date_to:
                date_filters.append(f"date <= {search_request.filters.date_to}")
            
            if date_filters:
                filter_parts.append(f"({' AND '.join(date_filters)})")
            
            # 组合所有过滤条件
            if filter_parts:
                filters = " AND ".join(filter_parts)
        
        # 设置排序（默认按日期降序）
        sort = ["date:desc"]
        
        # 转换旧格式参数到新格式
        start_timestamp = None
        end_timestamp = None
        chat_types = None
        
        if search_request.filters:
            if search_request.filters.date_from:
                start_timestamp = search_request.filters.date_from
            if search_request.filters.date_to:
                end_timestamp = search_request.filters.date_to
            if search_request.filters.chat_type:
                chat_types = search_request.filters.chat_type
        
        # 执行搜索（使用新的高级搜索功能）
        search_results = meili_service.search(
            query=search_request.query,
            filters=filters,  # 保留原有的filters参数以确保向后兼容
            sort=sort,
            page=search_request.page,
            hits_per_page=search_request.hits_per_page,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            chat_types=chat_types
        )
        # 详细记录搜索结果原始数据
        logger.info(f"Meilisearch返回的estimatedTotalHits: {search_results.get('estimatedTotalHits', 0)}")
        logger.info(f"请求的hits_per_page: {search_request.hits_per_page}")
        logger.info(f"Meilisearch返回的hits数量: {len(search_results.get('hits', []))}")
        
        # 处理搜索结果，确保符合响应模型
        hits = []
        for hit in search_results.get('hits', []):
            # 创建文本摘要，优先使用高亮结果
            text = hit.get('text', '')
            
            # 检查是否有高亮信息
            if '_formatted' in hit and 'text' in hit['_formatted']:
                text_snippet = hit['_formatted']['text'][:300] + ('...' if len(hit['_formatted']['text']) > 300 else '')
            else:
                text_snippet = text[:200] + ('...' if len(text) > 200 else '')
            
            # 创建结果项
            hit_item = SearchResultItem(
                id=hit.get('id', ''),
                chat_title=hit.get('chat_title', None),
                sender_name=hit.get('sender_name', None),
                text_snippet=text_snippet,
                date=hit.get('date', 0),
                message_link=hit.get('message_link', '')
            )
            hits.append(hit_item)
        
        # 构建响应
        response = {
            "hits": hits,
            "query": search_request.query,
            "processingTimeMs": search_results.get('processingTimeMs', 0),
            "limit": search_request.hits_per_page,
            "offset": (search_request.page - 1) * search_request.hits_per_page,
            "estimatedTotalHits": search_results.get('estimatedTotalHits', 0)
        }
        
        logger.info(f"搜索 '{search_request.query}' 找到 {len(hits)} 条结果，estimatedTotalHits={response['estimatedTotalHits']}，计算得到totalPages={math.ceil(response['estimatedTotalHits'] / search_request.hits_per_page)}")
        return response
        
    except Exception as e:
        logger.error(f"搜索时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")