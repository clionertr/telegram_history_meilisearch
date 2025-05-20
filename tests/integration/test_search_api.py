"""
搜索 API 集成测试模块

此模块测试 FastAPI 的搜索 API 端点功能，包括：
1. 简单搜索测试
2. 带有过滤条件的搜索测试
3. 无效搜索测试
"""

import pytest
from httpx import AsyncClient
import json
from fastapi.testclient import TestClient

from api.main import app


@pytest.mark.asyncio
async def test_search_api_simple():
    """测试基本搜索功能"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 创建一个简单的搜索请求
        request_data = {
            "query": "测试",
            "page": 1,
            "hits_per_page": 10
        }
        
        response = await ac.post("/api/v1/search", json=request_data)
        
        # 断言响应状态码为 200
        assert response.status_code == 200
        
        # 解析响应 JSON
        response_data = response.json()
        
        # 断言响应包含必要的字段
        assert "hits" in response_data
        assert "query" in response_data
        assert "processingTimeMs" in response_data
        assert "estimatedTotalHits" in response_data
        
        # 断言查询字段匹配请求
        assert response_data["query"] == "测试"


@pytest.mark.asyncio
async def test_search_api_with_filters():
    """测试带有过滤条件的搜索功能"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 创建带有过滤条件的搜索请求
        request_data = {
            "query": "测试",
            "filters": {
                "chat_type": ["group", "channel"],
                "date_from": 1672531200,  # 2023-01-01 00:00:00 UTC
                "date_to": 1704067199     # 2023-12-31 23:59:59 UTC
            },
            "page": 1,
            "hits_per_page": 20
        }
        
        response = await ac.post("/api/v1/search", json=request_data)
        
        # 断言响应状态码为 200
        assert response.status_code == 200
        
        # 解析响应 JSON
        response_data = response.json()
        
        # 断言响应包含必要的字段
        assert "hits" in response_data
        assert "limit" in response_data
        assert response_data["limit"] == 20  # 确认每页结果数量与请求一致


@pytest.mark.asyncio
async def test_search_api_invalid_request():
    """测试无效请求的处理"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 创建缺少必需字段的请求
        request_data = {
            "page": 1,
            "hits_per_page": 10
            # 缺少 query 字段
        }
        
        response = await ac.post("/api/v1/search", json=request_data)
        
        # 断言响应状态码为 422（验证错误）
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_search_api_pagination():
    """测试分页功能"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 创建第一页的请求
        request_data_page1 = {
            "query": "测试",
            "page": 1,
            "hits_per_page": 5
        }
        
        # 创建第二页的请求
        request_data_page2 = {
            "query": "测试",
            "page": 2,
            "hits_per_page": 5
        }
        
        # 请求第一页
        response_page1 = await ac.post("/api/v1/search", json=request_data_page1)
        assert response_page1.status_code == 200
        response_data_page1 = response_page1.json()
        
        # 请求第二页
        response_page2 = await ac.post("/api/v1/search", json=request_data_page2)
        assert response_page2.status_code == 200
        response_data_page2 = response_page2.json()
        
        # 断言两页的偏移量不同
        assert response_data_page1["offset"] == 0
        assert response_data_page2["offset"] == 5
        
        # 如果结果总数足够多，两页的结果应该不同
        if response_data_page1["estimatedTotalHits"] > 5:
            # 获取两页结果中的第一条记录ID（如果有）
            page1_first_hit_id = response_data_page1["hits"][0]["id"] if response_data_page1["hits"] else None
            page2_first_hit_id = response_data_page2["hits"][0]["id"] if response_data_page2["hits"] else None
            
            # 如果两页都有结果，断言它们不同
            if page1_first_hit_id and page2_first_hit_id:
                assert page1_first_hit_id != page2_first_hit_id