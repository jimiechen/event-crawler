#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话API测试
测试SessionController的所有接口
"""

import pytest
from httpx import AsyncClient
from datetime import datetime


class TestSessionAPI:
    """会话API测试类"""

    @pytest.mark.asyncio
    async def test_upsert_session(self, test_client: AsyncClient):
        """测试创建或更新会话"""
        session_data = {
            "platform_id": "weibo",
            "user_id": "test_user_001",
            "account_name": "测试用户",
            "cookies": [
                {"name": "sessionid", "value": "test_session_value", "domain": ".weibo.com", "path": "/"},
                {"name": "user_id", "value": "123456", "domain": ".weibo.com", "path": "/"}
            ],
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        
        response = await test_client.post("/api/v1/sessions", json=session_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["platform_id"] == "weibo"
        assert data["data"]["user_id"] == "test_user_001"

    @pytest.mark.asyncio
    async def test_upsert_session_update(self, test_client: AsyncClient):
        """测试更新已存在的会话"""
        # 先创建会话
        session_data = {
            "platform_id": "weibo",
            "user_id": "test_user_002",
            "account_name": "测试用户2",
            "cookies": [{"name": "sessionid", "value": "test_value", "domain": ".weibo.com", "path": "/"}]
        }
        await test_client.post("/api/v1/sessions", json=session_data)
        
        # 更新会话
        update_data = {
            "platform_id": "weibo",
            "user_id": "test_user_002",
            "account_name": "测试用户2(更新)",
            "cookies": [{"name": "sessionid", "value": "updated_value", "domain": ".weibo.com", "path": "/"}]
        }
        
        response = await test_client.post("/api/v1/sessions", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["account_name"] == "测试用户2(更新)"

    @pytest.mark.asyncio
    async def test_upsert_session_invalid_data(self, test_client: AsyncClient):
        """测试创建会话（缺少必需字段）"""
        session_data = {
            "account_name": "测试用户"
            # 缺少platform_id, user_id, cookies
        }
        
        response = await test_client.post("/api/v1/sessions", json=session_data)
        
        # 应该返回验证错误
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_get_sessions_by_platform(self, test_client: AsyncClient):
        """测试获取指定平台的所有会话"""
        # 先创建几个会话
        for i in range(3):
            session_data = {
                "platform_id": "weibo",
                "user_id": f"test_user_{i:03d}",
                "account_name": f"测试用户{i}",
                "cookies": [{"name": "sessionid", "value": f"value_{i}", "domain": ".weibo.com", "path": "/"}]
            }
            await test_client.post("/api/v1/sessions", json=session_data)
        
        # 获取会话列表
        response = await test_client.get("/api/v1/sessions/weibo")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 3

    @pytest.mark.asyncio
    async def test_get_sessions_empty_platform(self, test_client: AsyncClient):
        """测试获取不存在平台的会话"""
        response = await test_client.get("/api/v1/sessions/nonexistent_platform")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []

    @pytest.mark.asyncio
    async def test_get_best_session(self, test_client: AsyncClient):
        """测试获取最佳会话"""
        # 创建多个会话，设置不同的健康度
        platforms = ["weibo", "bilibili", "douyin"]
        
        for i, platform_id in enumerate(platforms):
            session_data = {
                "platform_id": platform_id,
                "user_id": f"user_{i}",
                "account_name": f"用户{i}",
                "cookies": [{"name": "sessionid", "value": f"value_{i}", "domain": f".{platform_id}.com", "path": "/"}]
            }
            await test_client.post("/api/v1/sessions", json=session_data)
        
        # 获取微博的最佳会话
        response = await test_client.get("/api/v1/sessions/weibo/best")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["platform_id"] == "weibo"
        assert "cookies_json" in data["data"]

    @pytest.mark.asyncio
    async def test_get_best_session_no_active(self, test_client: AsyncClient):
        """测试获取最佳会话（无活跃会话）"""
        response = await test_client.get("/api/v1/sessions/nonexistent/best")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "No active session" in data["message"]

    @pytest.mark.asyncio
    async def test_verify_session_success(self, test_client: AsyncClient):
        """测试验证会话（成功）"""
        # 先创建会话
        session_data = {
            "platform_id": "weibo",
            "user_id": "test_verify_user",
            "account_name": "验证用户",
            "cookies": [{"name": "sessionid", "value": "verify_value", "domain": ".weibo.com", "path": "/"}]
        }
        create_response = await test_client.post("/api/v1/sessions", json=session_data)
        session_id = create_response.json()["data"]["id"]
        
        # 验证会话（成功）
        verify_data = {"success": True}
        response = await test_client.post(f"/api/v1/sessions/{session_id}/verify", json=verify_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_verify_session_failure(self, test_client: AsyncClient):
        """测试验证会话（失败）"""
        # 先创建会话
        session_data = {
            "platform_id": "weibo",
            "user_id": "test_verify_fail_user",
            "account_name": "验证失败用户",
            "cookies": [{"name": "sessionid", "value": "verify_fail_value", "domain": ".weibo.com", "path": "/"}]
        }
        create_response = await test_client.post("/api/v1/sessions", json=session_data)
        session_id = create_response.json()["data"]["id"]
        
        # 验证会话（失败）
        verify_data = {"success": False}
        response = await test_client.post(f"/api/v1/sessions/{session_id}/verify", json=verify_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_verify_session_not_found(self, test_client: AsyncClient):
        """测试验证不存在的会话"""
        verify_data = {"success": True}
        response = await test_client.post("/api/v1/sessions/99999/verify", json=verify_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_delete_session(self, test_client: AsyncClient):
        """测试删除会话"""
        # 先创建会话
        session_data = {
            "platform_id": "weibo",
            "user_id": "test_delete_user",
            "account_name": "待删除用户",
            "cookies": [{"name": "sessionid", "value": "delete_value", "domain": ".weibo.com", "path": "/"}]
        }
        create_response = await test_client.post("/api/v1/sessions", json=session_data)
        session_id = create_response.json()["data"]["id"]
        
        # 删除会话
        response = await test_client.delete(f"/api/v1/sessions/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, test_client: AsyncClient):
        """测试删除不存在的会话"""
        response = await test_client.delete("/api/v1/sessions/99999")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_session_data_structure(self, test_client: AsyncClient):
        """测试会话数据结构的完整性"""
        # 创建会话
        session_data = {
            "platform_id": "weibo",
            "user_id": "test_structure_user",
            "account_name": "结构测试用户",
            "cookies": [
                {"name": "sessionid", "value": "test_value", "domain": ".weibo.com", "path": "/"},
                {"name": "user_id", "value": "123456", "domain": ".weibo.com", "path": "/"}
            ],
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        
        response = await test_client.post("/api/v1/sessions", json=session_data)
        
        assert response.status_code == 200
        data = response.json()
        
        session = data["data"]
        # 验证必需字段
        assert "id" in session
        assert "platform_id" in session
        assert "user_id" in session
        assert "account_name" in session
        assert "cookies_json" in session
        
        # 验证可选字段
        if "user_agent" in session:
            assert session["user_agent"] is None or isinstance(session["user_agent"], str)

    @pytest.mark.asyncio
    async def test_session_cookies_json_format(self, test_client: AsyncClient):
        """测试会话Cookie JSON格式"""
        import json
        
        # 创建会话
        session_data = {
            "platform_id": "weibo",
            "user_id": "test_json_user",
            "account_name": "JSON测试用户",
            "cookies": [
                {"name": "cookie1", "value": "value1", "domain": ".weibo.com", "path": "/"},
                {"name": "cookie2", "value": "value2", "domain": ".weibo.com", "path": "/"}
            ]
        }
        
        response = await test_client.post("/api/v1/sessions", json=session_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证cookies_json是有效的JSON字符串
        session = data["data"]
        assert "cookies_json" in session
        
        # 尝试解析cookies_json
        cookies = json.loads(session["cookies_json"])
        assert isinstance(cookies, list)
        assert len(cookies) == 2

    @pytest.mark.asyncio
    async def test_multiple_platforms_sessions(self, test_client: AsyncClient):
        """测试多平台会话管理"""
        platforms = ["weibo", "bilibili", "douyin"]
        
        for platform_id in platforms:
            session_data = {
                "platform_id": platform_id,
                "user_id": f"{platform_id}_user",
                "account_name": f"{platform_id}用户",
                "cookies": [{"name": "sessionid", "value": f"{platform_id}_value", "domain": f".{platform_id}.com", "path": "/"}]
            }
            await test_client.post("/api/v1/sessions", json=session_data)
        
        # 获取每个平台的会话
        for platform_id in platforms:
            response = await test_client.get(f"/api/v1/sessions/{platform_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert isinstance(data["data"], list)
            assert len(data["data"]) > 0
