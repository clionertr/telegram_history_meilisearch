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


@pytest.mark.asyncio
async def test_advanced_search_api_with_timestamps():
    """测试带时间戳过滤的高级搜索API"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 创建带有时间戳过滤的高级搜索请求
        request_data = {
            "query": "测试",
            "start_timestamp": 1672531200,  # 2023-01-01 00:00:00 UTC
            "end_timestamp": 1704067199,    # 2023-12-31 23:59:59 UTC
            "page": 1,
            "hits_per_page": 10
        }
        
        response = await ac.post("/api/v1/search/advanced", json=request_data)
        
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
async def test_advanced_search_api_with_chat_types():
    """测试带聊天类型过滤的高级搜索API"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 创建带有聊天类型过滤的高级搜索请求
        request_data = {
            "query": "测试消息",
            "chat_types": ["group", "channel"],
            "page": 1,
            "hits_per_page": 15
        }
        
        response = await ac.post("/api/v1/search/advanced", json=request_data)
        
        # 断言响应状态码为 200
        assert response.status_code == 200
        
        # 解析响应 JSON
        response_data = response.json()
        
        # 断言响应包含必要的字段
        assert "hits" in response_data
        assert "limit" in response_data
        assert response_data["limit"] == 15  # 确认每页结果数量与请求一致


@pytest.mark.asyncio
async def test_advanced_search_api_with_chat_ids():
    """测试带聊天ID过滤的高级搜索API"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 创建带有聊天ID过滤的高级搜索请求
        request_data = {
            "query": "测试",
            "chat_ids": [-1001234567890, -1009876543210],
            "page": 1,
            "hits_per_page": 20
        }
        
        response = await ac.post("/api/v1/search/advanced", json=request_data)
        
        # 断言响应状态码为 200
        assert response.status_code == 200
        
        # 解析响应 JSON
        response_data = response.json()
        
        # 断言响应包含必要的字段
        assert "hits" in response_data
        assert "query" in response_data
        assert "estimatedTotalHits" in response_data


@pytest.mark.asyncio
async def test_advanced_search_api_combined_filters():
    """测试高级搜索API的组合过滤条件"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 创建包含所有过滤条件的高级搜索请求
        request_data = {
            "query": "综合测试",
            "start_timestamp": 1672531200,  # 2023-01-01 00:00:00 UTC
            "end_timestamp": 1704067199,    # 2023-12-31 23:59:59 UTC
            "chat_types": ["group"],
            "chat_ids": [-1001234567890],
            "page": 1,
            "hits_per_page": 25
        }
        
        response = await ac.post("/api/v1/search/advanced", json=request_data)
        
        # 断言响应状态码为 200
        assert response.status_code == 200
        
        # 解析响应 JSON
        response_data = response.json()
        
        # 断言响应包含必要的字段
        assert "hits" in response_data
        assert "query" in response_data
        assert "processingTimeMs" in response_data
        assert "limit" in response_data
        assert "offset" in response_data
        assert "estimatedTotalHits" in response_data
        
        # 验证分页参数
        assert response_data["limit"] == 25
        assert response_data["offset"] == 0


@pytest.mark.asyncio
async def test_advanced_search_api_invalid_request():
    """测试高级搜索API的无效请求处理"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 创建缺少必需字段的请求
        request_data = {
            "start_timestamp": 1672531200,
            "chat_types": ["group"],
            "page": 1,
            "hits_per_page": 10
            # 缺少 query 字段
        }
        
        response = await ac.post("/api/v1/search/advanced", json=request_data)
        
        # 断言响应状态码为 422（验证错误）
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_advanced_search_api_edge_cases():
    """测试高级搜索API的边界情况"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 测试空过滤条件
        request_data = {
            "query": "边界测试",
            "chat_types": [],
            "chat_ids": [],
            "page": 1,
            "hits_per_page": 10
        }
        
        response = await ac.post("/api/v1/search/advanced", json=request_data)
        assert response.status_code == 200
        
        # 测试无效的时间戳顺序（end_timestamp < start_timestamp）
        request_data_invalid_time = {
            "query": "时间戳测试",
            "start_timestamp": 1704067199,  # 2023-12-31
            "end_timestamp": 1672531200,    # 2023-01-01（错误的顺序）
            "page": 1,
            "hits_per_page": 10
        }
        
        response_invalid_time = await ac.post("/api/v1/search/advanced", json=request_data_invalid_time)
        # 即使时间戳顺序错误，API也应该正常响应（由Meilisearch处理逻辑）
        assert response_invalid_time.status_code == 200
        
        # 测试极大的分页参数
        request_data_large_page = {
            "query": "分页测试",
            "page": 1,
            "hits_per_page": 100  # 最大允许值
        }
        
        response_large_page = await ac.post("/api/v1/search/advanced", json=request_data_large_page)
        assert response_large_page.status_code == 200
        
        # 测试超出最大限制的分页参数
        request_data_exceeds_limit = {
            "query": "超限测试",
            "page": 1,
            "hits_per_page": 101  # 超过最大限制
        }
        
        response_exceeds = await ac.post("/api/v1/search/advanced", json=request_data_exceeds_limit)
        # 应该返回验证错误
        assert response_exceeds.status_code == 422


@pytest.mark.asyncio
async def test_backward_compatibility_with_old_search():
    """测试新功能与旧搜索API的向后兼容性"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 使用旧的搜索API格式
        old_request_data = {
            "query": "兼容性测试",
            "filters": {
                "chat_type": ["group"],
                "date_from": 1672531200,
                "date_to": 1704067199
            },
            "page": 1,
            "hits_per_page": 10
        }
        
        # 使用新的高级搜索API格式
        new_request_data = {
            "query": "兼容性测试",
            "start_timestamp": 1672531200,
            "end_timestamp": 1704067199,
            "chat_types": ["group"],
            "page": 1,
            "hits_per_page": 10
        }
        
        # 发送旧格式请求
        old_response = await ac.post("/api/v1/search", json=old_request_data)
        assert old_response.status_code == 200
        
        # 发送新格式请求
        new_response = await ac.post("/api/v1/search/advanced", json=new_request_data)
        assert new_response.status_code == 200
        
        # 两种API都应该正常工作
        old_data = old_response.json()
        new_data = new_response.json()
        
        # 基本结构应该相同
        assert "hits" in old_data and "hits" in new_data
        assert "query" in old_data and "query" in new_data
        assert old_data["query"] == new_data["query"]