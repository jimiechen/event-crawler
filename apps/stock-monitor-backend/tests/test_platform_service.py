#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台服务测试
测试PlatformService的所有方法
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestPlatformService:
    """平台服务测试类"""

    @pytest.mark.asyncio
    async def test_get_platform_by_id(self, test_session: AsyncSession):
        """测试获取指定平台配置"""
        from app.services.platform_service import PlatformService
        
        service = PlatformService(test_session)
        
        # Mock数据库查询
        with patch.object(test_session, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = MagicMock(
                id=1,
                platform_id="weibo",
                name="微博",
                domain=".weibo.com",
                login_url="https://weibo.com/login.php",
                home_url="https://weibo.com",
                verify_api="https://weibo.com/ajax/profile/info",
                verify_type="json",
                verify_xpath=None,
                verify_parser='{"path": "$.data.user.screen_name"}',
                icon="🔴",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            mock_execute.return_value.scalar_one_or_none.return_value = mock_result
            
            result = await service.get_platform_by_id("weibo")
            
            assert result is not None
            assert result["platform_id"] == "weibo"
            assert result["name"] == "微博"

    @pytest.mark.asyncio
    async def test_get_platform_by_id_not_found(self, test_session: AsyncSession):
        """测试获取不存在的平台"""
        from app.services.platform_service import PlatformService
        
        service = PlatformService(test_session)
        
        with patch.object(test_session, 'execute') as mock_execute:
            mock_execute.return_value.scalar_one_or_none.return_value = None
            
            result = await service.get_platform_by_id("nonexistent")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_get_all_platforms(self, test_session: AsyncSession):
        """测试获取所有平台"""
        from app.services.platform_service import PlatformService
        
        service = PlatformService(test_session)
        
        with patch.object(test_session, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalars().all.return_value = [
                MagicMock(
                    id=1,
                    platform_id="weibo",
                    name="微博",
                    domain=".weibo.com",
                    icon="🔴"
                ),
                MagicMock(
                    id=2,
                    platform_id="bilibili",
                    name="B站",
                    domain=".bilibili.com",
                    icon="📺"
                )
            ]
            mock_execute.return_value.scalars.return_value.all.return_value = mock_result
            
            result = await service.get_all_platforms()
            
            assert len(result) == 2
            assert result[0]["platform_id"] == "weibo"
            assert result[1]["platform_id"] == "bilibili"

    @pytest.mark.asyncio
    async def test_create_platform(self, test_session: AsyncSession):
        """测试创建平台配置"""
        from app.services.platform_service import PlatformService
        from app.models.platform import PlatformConfig
        
        service = PlatformService(test_session)
        
        platform_data = {
            "platform_id": "test_platform",
            "name": "测试平台",
            "domain": ".test.com",
            "login_url": "https://test.com/login",
            "home_url": "https://test.com",
            "verify_api": "https://test.com/api/verify",
            "verify_type": "json",
            "verify_parser": '{"path": "$.data.user.name"}',
            "icon": "🧪"
        }
        
        with patch.object(test_session, 'add') as mock_add:
            mock_platform = MagicMock(spec=PlatformConfig)
            mock_add.return_value = mock_platform
            
            result = await service.create_platform(platform_data)
            
            assert result is not None
            assert result["platform_id"] == "test_platform"

    @pytest.mark.asyncio
    async def test_create_platform_duplicate(self, test_session: AsyncSession):
        """测试创建重复平台"""
        from app.services.platform_service import PlatformService
        from sqlalchemy.exc import IntegrityError
        
        service = PlatformService(test_session)
        
        platform_data = {
            "platform_id": "weibo",
            "name": "微博重复",
            "domain": ".weibo.com"
        }
        
        with patch.object(test_session, 'add') as mock_add:
            mock_add.side_effect = IntegrityError("Duplicate entry")
            
            with pytest.raises(IntegrityError):
                await service.create_platform(platform_data)

    @pytest.mark.asyncio
    async def test_create_platform_invalid_data(self, test_session: AsyncSession):
        """测试创建平台（缺少必需字段）"""
        from app.services.platform_service import PlatformService
        
        service = PlatformService(test_session)
        
        # 缺少必需字段
        platform_data = {
            "name": "测试平台"
            # 缺少platform_id和domain
        }
        
        with pytest.raises(ValueError):
            await service.create_platform(platform_data)

    @pytest.mark.asyncio
    async def test_update_platform(self, test_session: AsyncSession):
        """测试更新平台配置"""
        from app.services.platform_service import PlatformService
        
        service = PlatformService(test_session)
        
        update_data = {
            "name": "微博(更新)",
            "icon": "🔴✓"
        }
        
        with patch.object(test_session, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = MagicMock(
                id=1,
                platform_id="weibo",
                name="微博",
                domain=".weibo.com"
            )
            mock_execute.return_value.scalar_one_or_none.return_value = mock_result
            
            result = await service.update_platform("weibo", update_data)
            
            assert result is True

    @pytest.mark.asyncio
    async def test_update_platform_not_found(self, test_session: AsyncSession):
        """测试更新不存在的平台"""
        from app.services.platform_service import PlatformService
        
        service = PlatformService(test_session)
        
        with patch.object(test_session, 'execute') as mock_execute:
            mock_execute.return_value.scalar_one_or_none.return_value = None
            
            result = await service.update_platform("nonexistent", {"name": "测试更新"})
            
            assert result is False

    @pytest.mark.asyncio
    async def test_delete_platform(self, test_session: AsyncSession):
        """测试删除平台配置"""
        from app.services.platform_service import PlatformService
        
        service = PlatformService(test_session)
        
        with patch.object(test_session, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = MagicMock(id=1)
            mock_execute.return_value.scalar_one_or_none.return_value = mock_result
            
            result = await service.delete_platform("weibo")
            
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_platform_not_found(self, test_session: AsyncSession):
        """测试删除不存在的平台"""
        from app.services.platform_service import PlatformService
        
        service = PlatformService(test_session)
        
        with patch.object(test_session, 'execute') as mock_execute:
            mock_execute.return_value.scalar_one_or_none.return_value = None
            
            result = await service.delete_platform("nonexistent")
            
            assert result is False

    @pytest.mark.asyncio
    async def test_platform_data_validation(self, test_session: AsyncSession):
        """测试平台数据验证"""
        from app.services.platform_service import PlatformService
        
        service = PlatformService(test_session)
        
        # 测试有效的verify_type
        valid_types = ["json", "text"]
        for verify_type in valid_types:
            platform_data = {
                "platform_id": f"test_{verify_type}",
                "name": "测试平台",
                "domain": ".test.com",
                "verify_type": verify_type
            }
            
            with patch.object(test_session, 'add'):
                result = await service.create_platform(platform_data)
                assert result is not None

    @pytest.mark.asyncio
    async def test_platform_data_validation_invalid_verify_type(self, test_session: AsyncSession):
        """测试平台数据验证（无效verify_type）"""
        from app.services.platform_service import PlatformService
        
        service = PlatformService(test_session)
        
        platform_data = {
            "platform_id": "test_invalid",
            "name": "测试平台",
            "domain": ".test.com",
            "verify_type": "invalid_type"
        }
        
        with pytest.raises(ValueError):
            await service.create_platform(platform_data)

    @pytest.mark.asyncio
    async def test_platform_verify_parser_json(self, test_session: AsyncSession):
        """测试平台验证器（JSON类型）"""
        from app.services.platform_service import PlatformService
        
        service = PlatformService(test_session)
        
        platform_data = {
            "platform_id": "test_json_parser",
            "name": "JSON解析测试平台",
            "domain": ".test.com",
            "verify_type": "json",
            "verify_parser": '{"path": "$.data.user.name"}'
        }
        
        with patch.object(test_session, 'add'):
            result = await service.create_platform(platform_data)
            assert result is not None

    @pytest.mark.asyncio
    async def test_platform_verify_parser_text(self, test_session: AsyncSession):
        """测试平台验证器（Text类型）"""
        from app.services.platform_service import PlatformService
        
        service = PlatformService(test_session)
        
        platform_data = {
            "platform_id": "test_text_parser",
            "name": "Text解析测试平台",
            "domain": ".test.com",
            "verify_type": "text",
            "verify_xpath": '//*[@class="user_name"]',
            "verify_parser": '{"regex": "class=\\"user_name\\"[^>]*>([^<]+)"}'
        }
        
        with patch.object(test_session, 'add'):
            result = await service.create_platform(platform_data)
            assert result is not None
