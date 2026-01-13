#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试
测试完整的端到端流程
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime


class TestSessionIntegration:
    """会话管理集成测试类"""

    @pytest.mark.asyncio
    async def test_complete_login_flow(self, test_client: AsyncClient, test_session: AsyncSession):
        """测试完整的登录流程"""
        # 步骤1：获取平台列表
        platforms_response = await test_client.get("/api/v1/platforms")
        assert platforms_response.status_code == 200
        platforms = platforms_response.json()["data"]
        assert len(platforms) >= 5
        
        # 步骤2：选择一个平台（微博）
        weibo_platform = next((p for p in platforms if p["platform_id"] == "weibo"), None)
        assert weibo_platform is not None
        
        # 步骤3：创建会话（模拟用户登录后同步Cookie）
        session_data = {
            "platform_id": "weibo",
            "user_id": "integration_test_user",
            "account_name": "集成测试用户",
            "cookies": [
                {"name": "sessionid", "value": "test_session_value", "domain": ".weibo.com", "path": "/"},
                {"name": "user_id", "value": "123456", "domain": ".weibo.com", "path": "/"}
            ],
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        
        session_response = await test_client.post("/api/v1/sessions", json=session_data)
        assert session_response.status_code == 200
        session = session_response.json()["data"]
        assert session["platform_id"] == "weibo"
        assert session["user_id"] == "integration_test_user"
        assert session["account_name"] == "集成测试用户"
        assert session["status"] == "active"
        assert session["health_score"] == 100
        
        # 步骤4：获取平台的所有会话
        sessions_response = await test_client.get("/api/v1/sessions/weibo")
        assert sessions_response.status_code == 200
        sessions = sessions_response.json()["data"]
        assert len(sessions) >= 1
        
        # 步骤5：获取最佳会话
        best_session_response = await test_client.get("/api/v1/sessions/weibo/best")
        assert best_session_response.status_code == 200
        best_session = best_session_response.json()["data"]
        assert best_session["user_id"] == "integration_test_user"
        
        # 步骤6：验证会话（成功）
        verify_response = await test_client.post(f"/api/v1/sessions/{session['id']}/verify", json={"success": True})
        assert verify_response.status_code == 200
        
        # 步骤7：再次获取会话，验证健康度更新
        updated_session_response = await test_client.get(f"/api/v1/sessions/{session['id']}")
        assert updated_session_response.status_code == 200
        updated_session = updated_session_response.json()["data"]
        # 健康度应该增加5分
        assert updated_session["health_score"] == 105 or updated_session["health_score"] == 100  # 可能被限制在100

    @pytest.mark.asyncio
    async def test_complete_login_flow_with_verify_failure(self, test_client: AsyncClient):
        """测试完整的登录流程（验证失败）"""
        # 步骤1：创建会话
        session_data = {
            "platform_id": "weibo",
            "user_id": "integration_test_fail_user",
            "account_name": "验证失败用户",
            "cookies": [{"name": "sessionid", "value": "test_value", "domain": ".weibo.com", "path": "/"}]
        }
        
        session_response = await test_client.post("/api/v1/sessions", json=session_data)
        assert session_response.status_code == 200
        session = session_response.json()["data"]
        
        # 步骤2：验证会话（失败）
        verify_response = await test_client.post(f"/api/v1/sessions/{session['id']}/verify", json={"success": False})
        assert verify_response.status_code == 200
        
        # 步骤3：再次获取会话，验证健康度降低
        updated_session_response = await test_client.get(f"/api/v1/sessions/{session['id']}")
        assert updated_session_response.status_code == 200
        updated_session = updated_session_response.json()["data"]
        # 健康度应该降低20分
        assert updated_session["health_score"] == 80

    @pytest.mark.asyncio
    async def test_complete_login_flow_multiple_platforms(self, test_client: AsyncClient):
        """测试完整的登录流程（多平台）"""
        platforms = ["weibo", "bilibili", "douyin"]
        
        for platform_id in platforms:
            # 创建会话
            session_data = {
                "platform_id": platform_id,
                "user_id": f"{platform_id}_user",
                "account_name": f"{platform_id}用户",
                "cookies": [{"name": "sessionid", "value": f"{platform_id}_value", "domain": f".{platform_id}.com", "path": "/"}]
            }
            
            session_response = await test_client.post("/api/v1/sessions", json=session_data)
            assert session_response.status_code == 200
            
            # 获取会话
            sessions_response = await test_client.get(f"/api/v1/sessions/{platform_id}")
            assert sessions_response.status_code == 200
            sessions = sessions_response.json()["data"]
            assert len(sessions) >= 1

    @pytest.mark.asyncio
    async def test_complete_login_flow_session_expire(self, test_client: AsyncClient):
        """测试完整的登录流程（会话过期）"""
        # 步骤1：创建会话
        session_data = {
            "platform_id": "weibo",
            "user_id": "expire_test_user",
            "account_name": "过期测试用户",
            "cookies": [{"name": "sessionid", "value": "test_value", "domain": ".weibo.com", "path": "/"}]
        }
        
        session_response = await test_client.post("/api/v1/sessions", json=session_data)
        assert session_response.status_code == 200
        session = session_response.json()["data"]
        
        # 步骤2：连续验证失败，直到健康度低于60
        for i in range(3):
            verify_response = await test_client.post(f"/api/v1/sessions/{session['id']}/verify", json={"success": False})
            assert verify_response.status_code == 200
        
        # 步骤3：获取会话，验证状态变为expired
        updated_session_response = await test_client.get(f"/api/v1/sessions/{session['id']}")
        assert updated_session_response.status_code == 200
        updated_session = updated_session_response.json()["data"]
        # 健康度应该低于60，状态应该变为expired
        assert updated_session["health_score"] < 60
        assert updated_session["status"] == "expired"

    @pytest.mark.asyncio
    async def test_crawler_with_session(self, test_client: AsyncClient, test_session: AsyncSession):
        """测试爬虫使用会话"""
        # 步骤1：创建会话
        session_data = {
            "platform_id": "weibo",
            "user_id": "crawler_test_user",
            "account_name": "爬虫测试用户",
            "cookies": [{"name": "sessionid", "value": "crawler_value", "domain": ".weibo.com", "path": "/"}]
        }
        
        session_response = await test_client.post("/api/v1/sessions", json=session_data)
        assert session_response.status_code == 200
        session = session_response.json()["data"]
        
        # 步骤2：验证会话
        verify_response = await test_client.post(f"/api/v1/sessions/{session['id']}/verify", json={"success": True})
        assert verify_response.status_code == 200
        
        # 步骤3：获取最佳会话
        best_session_response = await test_client.get("/api/v1/sessions/weibo/best")
        assert best_session_response.status_code == 200
        best_session = best_session_response.json()["data"]
        assert best_session["user_id"] == "crawler_test_user"

    @pytest.mark.asyncio
    async def test_session_update_flow(self, test_client: AsyncClient):
        """测试会话更新流程"""
        # 步骤1：创建会话
        session_data = {
            "platform_id": "weibo",
            "user_id": "update_test_user",
            "account_name": "更新测试用户",
            "cookies": [{"name": "sessionid", "value": "old_value", "domain": ".weibo.com", "path": "/"}]
        }
        
        session_response = await test_client.post("/api/v1/sessions", json=session_data)
        assert session_response.status_code == 200
        session = session_response.json()["data"]
        
        # 步骤2：更新会话（使用相同的user_id）
        update_data = {
            "platform_id": "weibo",
            "user_id": "update_test_user",
            "account_name": "更新测试用户(已更新)",
            "cookies": [{"name": "sessionid", "value": "new_value", "domain": ".weibo.com", "path": "/"}]
        }
        
        update_response = await test_client.post("/api/v1/sessions", json=update_data)
        assert update_response.status_code == 200
        updated_session = update_response.json()["data"]
        assert updated_session["account_name"] == "更新测试用户(已更新)"

    @pytest.mark.asyncio
    async def test_session_delete_flow(self, test_client: AsyncClient):
        """测试会话删除流程"""
        # 步骤1：创建会话
        session_data = {
            "platform_id": "weibo",
            "user_id": "delete_test_user",
            "account_name": "删除测试用户",
            "cookies": [{"name": "sessionid", "value": "delete_value", "domain": ".weibo.com", "path": "/"}]
        }
        
        session_response = await test_client.post("/api/v1/sessions", json=session_data)
        assert session_response.status_code == 200
        session = session_response.json()["data"]
        session_id = session["id"]
        
        # 步骤2：删除会话
        delete_response = await test_client.delete(f"/api/v1/sessions/{session_id}")
        assert delete_response.status_code == 200
        
        # 步骤3：验证会话已删除
        get_response = await test_client.get(f"/api/v1/sessions/{session_id}")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["success"] is False

    @pytest.mark.asyncio
    async def test_platform_crud_flow(self, test_client: AsyncClient):
        """测试平台CRUD流程"""
        # 步骤1：创建平台
        platform_data = {
            "platform_id": "test_integration_platform",
            "name": "集成测试平台",
            "domain": ".test.com",
            "login_url": "https://test.com/login",
            "home_url": "https://test.com",
            "verify_api": "https://test.com/api/verify",
            "verify_type": "json",
            "verify_parser": '{"path": "$.data.user.name"}',
            "icon": "🧪"
        }
        
        create_response = await test_client.post("/api/v1/platforms", json=platform_data)
        assert create_response.status_code == 200
        platform = create_response.json()["data"]
        
        # 步骤2：获取平台
        get_response = await test_client.get(f"/api/v1/platforms/{platform['platform_id']}")
        assert get_response.status_code == 200
        get_platform = get_response.json()["data"]
        assert get_platform["platform_id"] == "test_integration_platform"
        
        # 步骤3：更新平台
        update_data = {
            "name": "集成测试平台(已更新)",
            "icon": "🧪✓"
        }
        
        update_response = await test_client.put(f"/api/v1/platforms/{platform['platform_id']}", json=update_data)
        assert update_response.status_code == 200
        
        # 步骤4：删除平台
        delete_response = await test_client.delete(f"/api/v1/platforms/{platform['platform_id']}")
        assert delete_response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_score_flow(self, test_client: AsyncClient):
        """测试健康度评分流程"""
        # 步骤1：创建会话
        session_data = {
            "platform_id": "weibo",
            "user_id": "health_test_user",
            "account_name": "健康度测试用户",
            "cookies": [{"name": "sessionid", "value": "health_value", "domain": ".weibo.com", "path": "/"}]
        }
        
        session_response = await test_client.post("/api/v1/sessions", json=session_data)
        assert session_response.status_code == 200
        session = session_response.json()["data"]
        
        # 步骤2：验证成功（健康度增加）
        verify_response = await test_client.post(f"/api/v1/sessions/{session['id']}/verify", json={"success": True})
        assert verify_response.status_code == 200
        
        # 步骤3：验证失败（健康度降低）
        verify_response = await test_client.post(f"/api/v1/sessions/{session['id']}/verify", json={"success": False})
        assert verify_response.status_code == 200
        
        # 步骤4：获取会话，验证健康度变化
        updated_session_response = await test_client.get(f"/api/v1/sessions/{session['id']}")
        assert updated_session_response.status_code == 200
        updated_session = updated_session_response.json()["data"]
        # 初始100，成功+5=105（限制100），失败-20=80
        assert updated_session["health_score"] == 80

    @pytest.mark.asyncio
    async def test_best_session_selection(self, test_client: AsyncClient):
        """测试最佳会话选择流程"""
        # 步骤1：创建多个会话
        for i in range(3):
            session_data = {
                "platform_id": "weibo",
                "user_id": f"best_test_user_{i}",
                "account_name": f"最佳会话测试用户{i}",
                "cookies": [{"name": "sessionid", "value": f"value_{i}", "domain": ".weibo.com", "path": "/"}]
            }
            
            session_response = await test_client.post("/api/v1/sessions", json=session_data)
            assert session_response.status_code == 200
            session = session_response.json()["data"]
            
            # 设置不同的健康度
            if i == 0:
                # 第一个会话：验证成功
                await test_client.post(f"/api/v1/sessions/{session['id']}/verify", json={"success": True})
            elif i == 1:
                # 第二个会话：验证失败
                await test_client.post(f"/api/v1/sessions/{session['id']}/verify", json={"success": False})
            # 第三个会话：保持默认健康度100
        
        # 步骤2：获取最佳会话
        best_session_response = await test_client.get("/api/v1/sessions/weibo/best")
        assert best_session_response.status_code == 200
        best_session = best_session_response.json()["data"]
        # 应该返回健康度最高的会话（第三个会话，健康度100）
        assert best_session["health_score"] >= 100

    @pytest.mark.asyncio
    async def test_empty_platform_sessions(self, test_client: AsyncClient):
        """测试空平台会话流程"""
        # 步骤1：获取不存在平台的会话
        sessions_response = await test_client.get("/api/v1/sessions/nonexistent_platform")
        assert sessions_response.status_code == 200
        sessions = sessions_response.json()["data"]
        assert sessions == []
        
        # 步骤2：获取不存在平台的最佳会话
        best_session_response = await test_client.get("/api/v1/sessions/nonexistent_platform/best")
        assert best_session_response.status_code == 200
        best_session_data = best_session_response.json()
        assert best_session_data["success"] is False
        assert "No active session" in best_session_data["message"]

    @pytest.mark.asyncio
    async def test_concurrent_session_operations(self, test_client: AsyncClient):
        """测试并发会话操作"""
        import asyncio
        
        # 步骤1：并发创建多个会话
        async def create_session(user_id):
            session_data = {
                "platform_id": "weibo",
                "user_id": user_id,
                "account_name": f"并发测试用户{user_id}",
                "cookies": [{"name": "sessionid", "value": f"{user_id}_value", "domain": ".weibo.com", "path": "/"}]
            }
            return await test_client.post("/api/v1/sessions", json=session_data)
        
        # 并发创建5个会话
        tasks = [create_session(f"concurrent_user_{i}") for i in range(5)]
        responses = await asyncio.gather(*tasks)
        
        # 验证所有会话都创建成功
        for response in responses:
            assert response.status_code == 200
        
        # 步骤2：获取所有会话
        sessions_response = await test_client.get("/api/v1/sessions/weibo")
        assert sessions_response.status_code == 200
        sessions = sessions_response.json()["data"]
        assert len(sessions) >= 5
