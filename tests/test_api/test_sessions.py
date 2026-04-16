import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """测试健康检查端点"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_create_session(client: AsyncClient):
    """测试创建会话端点"""
    # 注意：这里需要JWT认证，实际测试需要先生成token
    # 这是一个简化示例
    response = await client.post("/api/v1/sessions", json={"title": "Test Session"})
    # 由于没有认证，应该返回401
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_sessions_unauthorized(client: AsyncClient):
    """测试未授权访问会话列表"""
    response = await client.get("/api/v1/sessions")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_session_not_found(client: AsyncClient):
    """测试获取不存在的会话"""
    response = await client.get("/api/v1/sessions/non-existent-id")
    assert response.status_code == 401  # 先检查认证
