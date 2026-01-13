#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话服务测试
测试SessionService的所有方法
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta


class TestSessionService:
    """会话服务测试类"""

    @pytest.mark.asyncio
    async def test_upsert_session_create(self, test_session: AsyncSession):
        """测试创建新会话"""
        from app.services.session_service import SessionService
        
        service = SessionService(test_session)
        
        session_data = {
            "platform_id": "weibo",
            "user_id": "test_user_001",
            "account_name": "测试用户",
            "cookies": [
                {"name": "sessionid", "value": "test_value", "domain": ".weibo.com", "path": "/"},
                {"name": "user_id", "value": "123456", "domain": ".weibo.com", "path": "/"}
            ],
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        
        with patch.object(test_session, 'execute') as mock_execute:
            mock_execute.return_value = None
            
            result = await service.upsert_session(
                platform_id="weibo",
                user_id="test_user_001",
                account_name="测试用户",
                cookies=session_data["cookies"],
                user_agent=session_data["user_agent"]
            )
            
            assert result is not None
            assert result["platform_id"] == "weibo"
            assert result["user_id"] == "test_user_001"
            assert result["account_name"] == "测试用户"
            assert result["status"] == "active"
            assert result["health_score"] == 100

    @pytest.mark.asyncio
    async def test_upsert_session_update(self, test_session: AsyncSession):
        """测试更新已存在的会话"""
        from app.services.session_service import SessionService
        from app.models.platform import PlatformSession
        
        service = SessionService(test_session)
        
        existing_session = MagicMock(spec=PlatformSession)
        existing_session.id = 1
        existing_session.platform_id = "weibo"
        existing_session.user_id = "test_user_001"
        
        with patch.object(test_session, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = existing_session
            
            mock_execute.return_value = mock_result
            
            result = await service.upsert_session(
                platform_id="weibo",
                user_id="test_user_001",
                account_name="测试用户(更新)",
                cookies=[{"name": "sessionid", "value": "updated_value", "domain": ".weibo.com", "path": "/"}]
            )
            
            assert result is not None
            assert result["account_name"] == "测试用户(更新)"

    @pytest.mark.asyncio
    async def test_upsert_session_invalid_data(self, test_session: AsyncSession):
        """测试创建会话（缺少必需字段）"""
        from app.services.session_service import SessionService
        
        service = SessionService(test_session)
        
        with pytest.raises(Exception):
            await service.upsert_session(
                platform_id="weibo",
                user_id="",  # 空user_id
                account_name="测试用户",
                cookies=[]
            )

    @pytest.mark.asyncio
    async def test_get_best_session(self, test_session: AsyncSession):
        """测试获取最佳会话"""
        from app.services.session_service import SessionService
        from app.models.platform import PlatformSession
        
        service = SessionService(test_session)
        
        session1 = MagicMock(spec=PlatformSession)
        session1.id = 1
        session1.platform_id = "weibo"
        session1.user_id = "user_001"
        session1.account_name = "用户1"
        session1.status = "active"
        session1.health_score = 90
        session1.cookies_json = '[{"name": "cookie1"}]'
        session1.user_agent = "Mozilla/5.0"
        
        session2 = MagicMock(spec=PlatformSession)
        session2.id = 2
        session2.platform_id = "weibo"
        session2.user_id = "user_002"
        session2.account_name = "用户2"
        session2.status = "active"
        session2.health_score = 95  # 更高健康度
        session2.cookies_json = '[{"name": "cookie2"}]'
        session2.user_agent = "Mozilla/5.0"
        
        with patch.object(test_session, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalars().all.return_value = [session1, session2]
            mock_execute.return_value = mock_result
            
            result = await service.get_best_session("weibo")
            
            assert result is not None
            assert result["id"] == 2  # 应该返回健康度更高的会话
            assert result["health_score"] == 95

    @pytest.mark.asyncio
    async def test_get_best_session_no_active(self, test_session: AsyncSession):
        """测试获取最佳会话（无活跃会话）"""
        from app.services.session_service import SessionService
        
        service = SessionService(test_session)
        
        with patch.object(test_session, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalars().all.return_value = []
            mock_execute.return_value = mock_result
            
            result = await service.get_best_session("weibo")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_get_sessions_by_platform(self, test_session: AsyncSession):
        """测试获取平台的所有会话"""
        from app.services.session_service import SessionService
        from app.models.platform import PlatformSession
        
        service = SessionService(test_session)
        
        session1 = MagicMock(spec=PlatformSession)
        session1.id = 1
        session1.platform_id = "weibo"
        session1.user_id = "user_001"
        session1.account_name = "用户1"
        session1.status = "active"
        session1.health_score = 90
        session1.last_verified_at = datetime.now()
        session1.last_used_at = datetime.now()
        
        session2 = MagicMock(spec=PlatformSession)
        session2.id = 2
        session2.platform_id = "weibo"
        session2.user_id = "user_002"
        session2.account_name = "用户2"
        session2.status = "expired"
        session2.health_score = 50
        session2.last_verified_at = datetime.now() - timedelta(days=1)
        session2.last_used_at = datetime.now() - timedelta(days=2)
        
        with patch.object(test_session, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalars().all.return_value = [session1, session2]
            mock_execute.return_value = mock_result
            
            result = await service.get_sessions_by_platform("weibo")
            
            assert len(result) == 2
            assert result[0]["id"] == 1
            assert result[1]["id"] == 2
            assert result[0]["health_score"] == 90
            assert result[1]["health_score"] == 50

    @pytest.mark.asyncio
    async def test_get_sessions_by_platform_empty(self, test_session: AsyncSession):
        """测试获取平台的会话（无会话）"""
        from app.services.session_service import SessionService
        
        service = SessionService(test_session)
        
        with patch.object(test_session, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalars().all.return_value = []
            mock_execute.return_value = mock_result
            
            result = await service.get_sessions_by_platform("nonexistent")
            
            assert result == []

    @pytest.mark.asyncio
    async def test_verify_session_success(self, test_session: AsyncSession):
        """测试验证会话（成功）"""
        from app.services.session_service import SessionService
        from app.models.platform import PlatformSession
        
        service = SessionService(test_session)
        
        session = MagicMock(spec=PlatformSession)
        session.id = 1
        session.health_score = 80
        
        with patch.object(test_session, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = session
            mock_execute.return_value = mock_result
            
            result = await service.verify_session(1, True)
            
            assert result is True
            # 验证健康度应该增加
            assert session.health_score == 85

    @pytest.mark.asyncio
    async def test_verify_session_failure(self, test_session: AsyncSession):
        """测试验证会话（失败）"""
        from app.services.session_service import SessionService
        from app.models.platform import PlatformSession
        
        service = SessionService(test_session)
        
        session = MagicMock(spec=PlatformSession)
        session.id = 1
        session.health_score = 80
        session.status = "active"
        
        with patch.object(test_session, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = session
            mock_execute.return_value = mock_result
            
            result = await service.verify_session(1, False)
            
            assert result is True
            # 验证健康度应该降低
            assert session.health_score == 60
            # 验证状态应该保持为active（因为健康度>60）
            assert session.status == "active"

    @pytest.mark.asyncio
    async def test_verify_session_failure_expire(self, test_session: AsyncSession):
        """测试验证会话（失败，导致过期）"""
        from app.services.session_service import SessionService
        from app.models.platform import PlatformSession
        
        service = SessionService(test_session)
        
        session = MagicMock(spec=PlatformSession)
        session.id = 1
        session.health_score = 70  # 接近过期阈值
        
        with patch.object(test_session, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = session
            mock_execute.return_value = mock_result
            
            result = await service.verify_session(1, False)
            
            assert result is True
            # 验证健康度应该降低到50
            assert session.health_score == 50
            # 验证状态应该变为expired
            assert session.status == "expired"

    @pytest.mark.asyncio
    async def test_verify_session_not_found(self, test_session: AsyncSession):
        """测试验证不存在的会话"""
        from app.services.session_service import SessionService
        
        service = SessionService(test_session)
        
        with patch.object(test_session, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result
            
            result = await service.verify_session(999, True)
            
            assert result is False

    @pytest.mark.asyncio
    async def test_delete_session(self, test_session: AsyncSession):
        """测试删除会话"""
        from app.services.session_service import SessionService
        
        service = SessionService(test_session)
        
        with patch.object(test_session, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = MagicMock(id=1)
            mock_execute.return_value = mock_result
            
            result = await service.delete_session(1)
            
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, test_session: AsyncSession):
        """测试删除不存在的会话"""
        from app.services.session_service import SessionService
        
        service = SessionService(test_session)
        
        with patch.object(test_session, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result
            
            result = await service.delete_session(999)
            
            assert result is False

    @pytest.mark.asyncio
    async def test_health_score_max_limit(self, test_session: AsyncSession):
        """测试健康度评分上限"""
        from app.services.session_service import SessionService
        from app.models.platform import PlatformSession
        
        service = SessionService(test_session)
        
        session = MagicMock(spec=PlatformSession)
        session.id = 1
        session.health_score = 98  # 接近100
        
        with patch.object(test_session, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = session
            mock_execute.return_value = mock_result
            
            result = await service.verify_session(1, True)
            
            assert result is True
            # 验证健康度不应该超过100
            assert session.health_score == 100

    @pytest.mark.asyncio
    async def test_health_score_min_limit(self, test_session: AsyncSession):
        """测试健康度评分下限"""
        from app.services.session_service import SessionService
        from app.models.platform import PlatformSession
        
        service = SessionService(test_session)
        
        session = MagicMock(spec=PlatformSession)
        session.id = 1
        session.health_score = 10  # 接近0
        
        with patch.object(test_session, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = session
            mock_execute.return_value = mock_result
            
            result = await service.verify_session(1, False)
            
            assert result is True
            # 验证健康度不应该低于0
            assert session.health_score == 0

    @pytest.mark.asyncio
    async def test_session_cookies_json_format(self, test_session: AsyncSession):
        """测试会话Cookie JSON格式"""
        from app.services.session_service import SessionService
        from app.models.platform import PlatformSession
        import json
        
        service = SessionService(test_session)
        
        session = MagicMock(spec=PlatformSession)
        session.id = 1
        session.cookies_json = json.dumps([
            {"name": "cookie1", "value": "value1", "domain": ".weibo.com", "path": "/"},
            {"name": "cookie2", "value": "value2", "domain": ".weibo.com", "path": "/"}
        ])
        
        with patch.object(test_session, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = session
            mock_execute.return_value = mock_result
            
            result = await service.get_best_session("weibo")
            
            assert result is not None
            assert "cookies_json" in result
            
            # 验证cookies_json是有效的JSON字符串
            cookies = json.loads(result["cookies_json"])
            assert isinstance(cookies, list)
            assert len(cookies) == 2

    @pytest.mark.asyncio
    async def test_multiple_platforms_sessions(self, test_session: AsyncSession):
        """测试多平台会话管理"""
        from app.services.session_service import SessionService
        
        service = SessionService(test_session)
        
        platforms = ["weibo", "bilibili", "douyin"]
        
        for platform_id in platforms:
            session_data = {
                "platform_id": platform_id,
                "user_id": f"{platform_id}_user",
                "account_name": f"{platform_id}用户",
                "cookies": [{"name": "sessionid", "value": f"{platform_id}_value", "domain": f".{platform_id}.com", "path": "/"}]
            }
            
            with patch.object(test_session, 'execute'):
                await service.upsert_session(**session_data)
        
        # 获取每个平台的会话
        for platform_id in platforms:
            with patch.object(test_session, 'execute') as mock_execute:
                mock_result = MagicMock()
                mock_result.scalars().all.return_value = [MagicMock(platform_id=platform_id)]
                mock_execute.return_value = mock_result
                
                result = await service.get_sessions_by_platform(platform_id)
                
                assert len(result) > 0
                assert result[0]["platform_id"] == platform_id
