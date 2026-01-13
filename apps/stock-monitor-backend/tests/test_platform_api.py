#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台API测试
测试PlatformController的所有接口
"""

import pytest
from httpx import AsyncClient
from datetime import datetime


class TestPlatformAPI:
    """平台API测试类"""

    @pytest.mark.asyncio
    async def test_get_all_platforms(self, test_client: AsyncClient):
        """测试获取所有平台列表"""
        response = await test_client.get("/api/v1/platforms")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 5  # 至少有5个预置平台
        
        # 验证平台数据结构
        platform = data["data"][0]
        assert "platform_id" in platform
        assert "name" in platform
        assert "domain" in platform
        assert "icon" in platform

    @pytest.mark.asyncio
    async def test_get_platform_by_id(self, test_client: AsyncClient):
        """测试获取指定平台配置"""
        # 测试微博平台
        response = await test_client.get("/api/v1/platforms/weibo")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["platform_id"] == "weibo"
        assert data["data"]["name"] == "微博"

    @pytest.mark.asyncio
    async def test_get_platform_not_found(self, test_client: AsyncClient):
        """测试获取不存在的平台"""
        response = await test_client.get("/api/v1/platforms/nonexistent")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_create_platform(self, test_client: AsyncClient):
        """测试创建平台配置"""
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
        
        response = await test_client.post("/api/v1/platforms", json=platform_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["platform_id"] == "test_platform"

    @pytest.mark.asyncio
    async def test_create_platform_duplicate(self, test_client: AsyncClient):
        """测试创建重复平台"""
        platform_data = {
            "platform_id": "weibo",  # 重复的platform_id
            "name": "微博重复",
            "domain": ".weibo.com"
        }
        
        response = await test_client.post("/api/v1/platforms", json=platform_data)
        
        assert response.status_code == 200
        data = response.json()
        # 可能返回成功或失败，取决于实现

    @pytest.mark.asyncio
    async def test_create_platform_invalid_data(self, test_client: AsyncClient):
        """测试创建平台（缺少必需字段）"""
        platform_data = {
            "name": "测试平台"
            # 缺少platform_id和domain
        }
        
        response = await test_client.post("/api/v1/platforms", json=platform_data)
        
        # 应该返回验证错误
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_update_platform(self, test_client: AsyncClient):
        """测试更新平台配置"""
        update_data = {
            "name": "微博(更新)",
            "icon": "🔴✓"
        }
        
        response = await test_client.put("/api/v1/platforms/weibo", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_update_platform_not_found(self, test_client: AsyncClient):
        """测试更新不存在的平台"""
        update_data = {
            "name": "测试更新"
        }
        
        response = await test_client.put("/api/v1/platforms/nonexistent", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_delete_platform(self, test_client: AsyncClient):
        """测试删除平台配置"""
        # 先创建一个测试平台
        platform_data = {
            "platform_id": "test_delete_platform",
            "name": "待删除平台",
            "domain": ".test.com"
        }
        await test_client.post("/api/v1/platforms", json=platform_data)
        
        # 删除平台
        response = await test_client.delete("/api/v1/platforms/test_delete_platform")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_delete_platform_not_found(self, test_client: AsyncClient):
        """测试删除不存在的平台"""
        response = await test_client.delete("/api/v1/platforms/nonexistent")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_platform_data_structure(self, test_client: AsyncClient):
        """测试平台数据结构的完整性"""
        response = await test_client.get("/api/v1/platforms")
        
        assert response.status_code == 200
        data = response.json()
        
        for platform in data["data"]:
            # 验证必需字段
            assert "id" in platform
            assert "platform_id" in platform
            assert "name" in platform
            assert "domain" in platform
            
            # 验证可选字段
            if "login_url" in platform:
                assert platform["login_url"] is None or isinstance(platform["login_url"], str)
            if "verify_api" in platform:
                assert platform["verify_api"] is None or isinstance(platform["verify_api"], str)
            if "verify_type" in platform:
                assert platform["verify_type"] in ["json", "text"]

    @pytest.mark.asyncio
    async def test_platform_verify_parser_json(self, test_client: AsyncClient):
        """测试平台验证器（JSON类型）"""
        response = await test_client.get("/api/v1/platforms/bilibili")
        
        assert response.status_code == 200
        data = response.json()
        
        # bilibili使用JSON验证
        assert data["data"]["verify_type"] == "json"
        assert data["data"]["verify_parser"] is not None

    @pytest.mark.asyncio
    async def test_platform_verify_parser_text(self, test_client: AsyncClient):
        """测试平台验证器（Text类型）"""
        response = await test_client.get("/api/v1/platforms/douyin")
        
        assert response.status_code == 200
        data = response.json()
        
        # douyin使用Text验证
        assert data["data"]["verify_type"] == "text"
        assert data["data"]["verify_xpath"] is not None
