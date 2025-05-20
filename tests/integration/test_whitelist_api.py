"""
白名单 API 集成测试模块

此模块测试 FastAPI 的白名单管理 API 端点功能，包括：
1. 获取白名单列表
2. 添加 ID 到白名单
3. 从白名单移除 ID
4. 重置白名单
"""

import pytest
from httpx import AsyncClient
import json
from fastapi.testclient import TestClient

from api.main import app


@pytest.mark.asyncio
async def test_get_whitelist():
    """测试获取白名单列表"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/admin/whitelist")
        
        # 断言响应状态码为 200
        assert response.status_code == 200
        
        # 解析响应 JSON
        response_data = response.json()
        
        # 断言响应包含必要的字段
        assert "whitelist" in response_data
        assert "count" in response_data
        assert isinstance(response_data["whitelist"], list)
        assert isinstance(response_data["count"], int)
        assert response_data["count"] == len(response_data["whitelist"])


@pytest.mark.asyncio
async def test_add_to_whitelist():
    """测试添加 ID 到白名单"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 创建添加白名单请求
        request_data = {
            "chat_id": 123456789  # 测试用户 ID
        }
        
        response = await ac.post("/api/v1/admin/whitelist", json=request_data)
        
        # 断言响应状态码为 201 Created
        assert response.status_code == 201
        
        # 解析响应 JSON
        response_data = response.json()
        
        # 断言响应包含必要的字段
        assert "success" in response_data
        assert "message" in response_data
        assert "chat_id" in response_data
        assert response_data["chat_id"] == 123456789
        
        # 添加第二次应该返回"已在白名单中"的消息
        response_again = await ac.post("/api/v1/admin/whitelist", json=request_data)
        assert response_again.status_code == 201
        response_data_again = response_again.json()
        assert response_data_again["success"] is False  # 因为已经存在
        assert "已在白名单中" in response_data_again["message"]


@pytest.mark.asyncio
async def test_remove_from_whitelist():
    """测试从白名单移除 ID"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 首先添加一个 ID 到白名单
        chat_id = 987654321
        add_data = {"chat_id": chat_id}
        await ac.post("/api/v1/admin/whitelist", json=add_data)
        
        # 然后移除这个 ID
        response = await ac.delete(f"/api/v1/admin/whitelist/{chat_id}")
        
        # 断言响应状态码为 200
        assert response.status_code == 200
        
        # 解析响应 JSON
        response_data = response.json()
        
        # 断言响应包含必要的字段
        assert "success" in response_data
        assert "message" in response_data
        assert "chat_id" in response_data
        assert response_data["chat_id"] == chat_id
        
        # 移除第二次应该返回"不在白名单中"的消息
        response_again = await ac.delete(f"/api/v1/admin/whitelist/{chat_id}")
        assert response_again.status_code == 200
        response_data_again = response_again.json()
        assert response_data_again["success"] is False  # 因为已经不存在
        assert "不在白名单中" in response_data_again["message"]


@pytest.mark.asyncio
async def test_reset_whitelist():
    """测试重置白名单"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 首先添加一些 ID 到白名单
        await ac.post("/api/v1/admin/whitelist", json={"chat_id": 111111})
        await ac.post("/api/v1/admin/whitelist", json={"chat_id": 222222})
        
        # 获取白名单，确认有元素
        get_response = await ac.get("/api/v1/admin/whitelist")
        whitelist_before = get_response.json()["whitelist"]
        
        # 重置白名单
        response = await ac.delete("/api/v1/admin/whitelist")
        
        # 断言响应状态码为 200
        assert response.status_code == 200
        
        # 解析响应 JSON
        response_data = response.json()
        
        # 断言响应包含必要的字段
        assert "success" in response_data
        assert "message" in response_data
        assert response_data["success"] is True
        
        # 再次获取白名单，确认为空
        get_response_after = await ac.get("/api/v1/admin/whitelist")
        whitelist_after = get_response_after.json()["whitelist"]
        assert len(whitelist_after) == 0


@pytest.mark.asyncio
async def test_whitelist_workflow():
    """测试完整的白名单工作流"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 1. 重置白名单，确保开始时为空
        await ac.delete("/api/v1/admin/whitelist")
        
        # 2. 获取白名单，确认为空
        response = await ac.get("/api/v1/admin/whitelist")
        assert response.json()["count"] == 0
        
        # 3. 添加多个 ID
        chat_ids = [12345, 67890, -111222]
        for chat_id in chat_ids:
            await ac.post("/api/v1/admin/whitelist", json={"chat_id": chat_id})
        
        # 4. 再次获取白名单，确认数量正确
        response = await ac.get("/api/v1/admin/whitelist")
        whitelist = response.json()["whitelist"]
        assert response.json()["count"] == len(chat_ids)
        assert all(chat_id in whitelist for chat_id in chat_ids)
        
        # 5. 移除一个 ID
        removal_id = chat_ids[0]
        await ac.delete(f"/api/v1/admin/whitelist/{removal_id}")
        
        # 6. 获取白名单，确认数量减少
        response = await ac.get("/api/v1/admin/whitelist")
        whitelist = response.json()["whitelist"]
        assert response.json()["count"] == len(chat_ids) - 1
        assert removal_id not in whitelist
        assert all(chat_id in whitelist for chat_id in chat_ids[1:])
        
        # 7. 重置白名单
        await ac.delete("/api/v1/admin/whitelist")
        
        # 8. 最后获取白名单，确认为空
        response = await ac.get("/api/v1/admin/whitelist")
        assert response.json()["count"] == 0