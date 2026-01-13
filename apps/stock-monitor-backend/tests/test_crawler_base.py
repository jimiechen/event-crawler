#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫基类测试
测试CrawlerBase的所有方法
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, AsyncMock as Mock
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession


class TestCrawlerBase:
    """爬虫基类测试类"""

    @pytest.mark.asyncio
    async def test_crawler_base_init(self, test_session: AsyncSession):
        """测试爬虫基类初始化"""
        from app.crawler.base import CrawlerBase
        
        # Mock服务
        with patch('app.crawler.base.SessionService') as mock_session_service:
            with patch('app.crawler.base.PlatformService') as mock_platform_service:
                crawler = CrawlerBase(test_session, 'weibo')
                
                assert crawler.db == test_session
                assert crawler.platform_id == 'weibo'
                assert crawler.session_service is not None
                assert crawler.platform_service is not None

    @pytest.mark.asyncio
    async def test_get_platform_config(self, test_session: AsyncSession):
        """测试获取平台配置"""
        from app.crawler.base import CrawlerBase
        
        with patch('app.crawler.base.SessionService') as mock_session_service:
            with patch('app.crawler.base.PlatformService') as mock_platform_service:
                crawler = CrawlerBase(test_session, 'weibo')
                
                # 第一次调用应该从服务获取
                config1 = await crawler.get_platform_config()
                assert config1 is not None
                assert config1["platform_id"] == "weibo"
                
                # 第二次调用应该使用缓存
                config2 = await crawler.get_platform_config()
                assert config2 == config1

    @pytest.mark.asyncio
    async def test_get_best_session(self, test_session: AsyncSession):
        """测试获取最佳会话"""
        from app.crawler.base import CrawlerBase
        from app.models.platform import PlatformSession
        
        with patch('app.crawler.base.SessionService') as mock_session_service:
            with patch('app.crawler.base.PlatformService') as mock_platform_service:
                crawler = CrawlerBase(test_session, 'weibo')
                
                session = MagicMock(spec=PlatformSession)
                session.id = 1
                session.platform_id = 'weibo'
                session.user_id = 'test_user'
                session.account_name = '测试用户'
                session.cookies_json = '[{"name": "cookie1"}]'
                session.user_agent = 'Mozilla/5.0'
                session.health_score = 90
                
                with patch.object(mock_session_service, 'get_best_session') as mock_get_best:
                    mock_get_best.return_value = {
                        "id": 1,
                        "platform_id": "weibo",
                        "user_id": "test_user",
                        "account_name": "测试用户",
                        "cookies_json": '[{"name": "cookie1"}]',
                        "user_agent": "Mozilla/5.0",
                        "health_score": 90
                    }
                    
                    result = await crawler.get_best_session()
                    
                    assert result is not None
                    assert result["id"] == 1
                    assert result["health_score"] == 90

    @pytest.mark.asyncio
    async def test_get_best_session_no_active(self, test_session: AsyncSession):
        """测试获取最佳会话（无活跃会话）"""
        from app.crawler.base import CrawlerBase
        
        with patch('app.crawler.base.SessionService') as mock_session_service:
            with patch('app.crawler.base.PlatformService') as mock_platform_service:
                crawler = CrawlerBase(test_session, 'weibo')
                
                with patch.object(mock_session_service, 'get_best_session') as mock_get_best:
                    mock_get_best.return_value = None
                    
                    result = await crawler.get_best_session()
                    
                    assert result is None

    @pytest.mark.asyncio
    async def test_create_browser_context(self, test_session: AsyncSession):
        """测试创建浏览器上下文"""
        from app.crawler.base import CrawlerBase
        from unittest.mock import AsyncMock as Mock
        
        with patch('app.crawler.base.SessionService') as mock_session_service:
            with patch('app.crawler.base.PlatformService') as mock_platform_service:
                crawler = CrawlerBase(test_session, 'weibo')
                
                # Mock平台配置
                with patch.object(crawler, 'get_platform_config') as mock_get_config:
                    mock_get_config.return_value = {
                        "platform_id": "weibo",
                        "domain": ".weibo.com",
                        "login_url": "https://weibo.com/login",
                        "home_url": "https://weibo.com",
                        "verify_api": "https://weibo.com/api/verify",
                        "verify_type": "json",
                        "verify_parser": '{"path": "$.data.user.screen_name"}',
                        "icon": "🔴"
                    }
                    
                    # Mock会话
                    with patch.object(crawler, 'get_best_session') as mock_get_session:
                        mock_get_session.return_value = {
                            "id": 1,
                            "platform_id": "weibo",
                            "user_id": "test_user",
                            "account_name": "测试用户",
                            "cookies_json": '[{"name": "cookie1", "value": "test_value", "domain": ".weibo.com", "path": "/"}]',
                            "user_agent": "Mozilla/5.0",
                            "health_score": 90
                        }
                        
                        # Mock Playwright
                        with patch('app.crawler.base.async_playwright') as mock_playwright:
                            mock_p = Mock()
                            mock_playwright.return_value.start = Mock()
                            
                            mock_browser = Mock()
                            mock_p.return_value.chromium = Mock(return_value=mock_browser)
                            
                            mock_context = Mock()
                            mock_browser.new_context = Mock(return_value=mock_context)
                            
                            # 调用方法
                            context, session, browser = await crawler.create_browser_context()
                            
                            # 验证结果
                            assert context is not None
                            assert session is not None
                            assert browser is not None
                            assert session["id"] == 1
                            
                            # 验证Cookie注入
                            assert mock_context.add_cookies.called
                            
                            # 验证反爬脚本注入
                            assert mock_context.add_init_script.called

    @pytest.mark.asyncio
    async def test_create_browser_context_no_session(self, test_session: AsyncSession):
        """测试创建浏览器上下文（无会话）"""
        from app.crawler.base import CrawlerBase
        from unittest.mock import AsyncMock as Mock
        
        with patch('app.crawler.base.SessionService') as mock_session_service:
            with patch('app.crawler.base.PlatformService') as mock_platform_service:
                crawler = CrawlerBase(test_session, 'weibo')
                
                # Mock平台配置
                with patch.object(crawler, 'get_platform_config') as mock_get_config:
                    mock_get_config.return_value = {
                        "platform_id": "weibo",
                        "domain": ".weibo.com"
                    }
                    
                    # Mock无会话
                    with patch.object(crawler, 'get_best_session') as mock_get_session:
                        mock_get_session.return_value = None
                        
                        # Mock Playwright
                        with patch('app.crawler.base.async_playwright') as mock_playwright:
                            mock_p = Mock()
                            mock_playwright.return_value.start = Mock()
                            
                            mock_browser = Mock()
                            mock_p.return_value.chromium = Mock(return_value=mock_browser)
                            
                            mock_context = Mock()
                            mock_browser.new_context = Mock(return_value=mock_context)
                            
                            # 调用方法
                            context, session, browser = await crawler.create_browser_context()
                            
                            # 验证结果
                            assert context is not None
                            assert session is None
                            assert browser is not None
                            
                            # 验证没有Cookie注入
                            assert not mock_context.add_cookies.called

    @pytest.mark.asyncio
    async def test_verify_session_success(self, test_session: AsyncSession):
        """测试验证会话（成功）"""
        from app.crawler.base import CrawlerBase
        from app.models.platform import PlatformSession
        
        with patch('app.crawler.base.SessionService') as mock_session_service:
            with patch('app.crawler.base.PlatformService') as mock_platform_service:
                crawler = CrawlerBase(test_session, 'weibo')
                
                session = MagicMock(spec=PlatformSession)
                session.id = 1
                
                # Mock平台配置（JSON验证）
                with patch.object(crawler, 'get_platform_config') as mock_get_config:
                    mock_get_config.return_value = {
                        "verify_api": "https://weibo.com/api/verify",
                        "verify_type": "json",
                        "verify_parser": '{"path": "$.data.user.screen_name"}'
                    }
                    
                    # Mock页面
                    mock_page = Mock()
                    mock_page.content = Mock(return_value='<script>{"data": {"user": {"screen_name": "测试用户"}}}</script>')
                    
                    result = await crawler.verify_session(mock_page, session)
                    
                    assert result is True

    @pytest.mark.asyncio
    async def test_verify_session_failure(self, test_session: AsyncSession):
        """测试验证会话（失败）"""
        from app.crawler.base import CrawlerBase
        from app.models.platform import PlatformSession
        
        with patch('app.crawler.base.SessionService') as mock_session_service:
            with patch('app.crawler.base.PlatformService') as mock_platform_service:
                crawler = CrawlerBase(test_session, 'weibo')
                
                session = MagicMock(spec=PlatformSession)
                session.id = 1
                
                # Mock平台配置（JSON验证）
                with patch.object(crawler, 'get_platform_config') as mock_get_config:
                    mock_get_config.return_value = {
                        "verify_api": "https://weibo.com/api/verify",
                        "verify_type": "json",
                        "verify_parser": '{"path": "$.data.user.screen_name"}'
                    }
                    
                    # Mock页面（无用户信息）
                    mock_page = Mock()
                    mock_page.content = Mock(return_value='<script>{"data": {}}</script>')
                    
                    result = await crawler.verify_session(mock_page, session)
                    
                    assert result is False

    @pytest.mark.asyncio
    async def test_verify_session_text_type(self, test_session: AsyncSession):
        """测试验证会话（Text类型）"""
        from app.crawler.base import CrawlerBase
        from app.models.platform import PlatformSession
        
        with patch('app.crawler.base.SessionService') as mock_session_service:
            with patch('app.crawler.base.PlatformService') as mock_platform_service:
                crawler = CrawlerBase(test_session, 'weibo')
                
                session = MagicMock(spec=PlatformSession)
                session.id = 1
                
                # Mock平台配置（Text验证）
                with patch.object(crawler, 'get_platform_config') as mock_get_config:
                    mock_get_config.return_value = {
                        "verify_api": "https://weibo.com/api/verify",
                        "verify_type": "text",
                        "verify_xpath": '//*[@class="user_name"]',
                        "verify_parser": '{"regex": "class=\\"user_name\\"[^>]*>([^<]+)"}'
                    }
                    
                    # Mock页面
                    mock_page = Mock()
                    mock_page.query_selector = Mock(return_value=MagicMock())
                    mock_element = Mock()
                    mock_element.inner_text = Mock(return_value='测试用户')
                    mock_page.query_selector.return_value = mock_element
                    
                    result = await crawler.verify_session(mock_page, session)
                    
                    assert result is True

    @pytest.mark.asyncio
    async def test_verify_session_no_config(self, test_session: AsyncSession):
        """测试验证会话（无验证配置）"""
        from app.crawler.base import CrawlerBase
        from app.models.platform import PlatformSession
        
        with patch('app.crawler.base.SessionService') as mock_session_service:
            with patch('app.crawler.base.PlatformService') as mock_platform_service:
                crawler = CrawlerBase(test_session, 'weibo')
                
                session = MagicMock(spec=PlatformSession)
                session.id = 1
                
                # Mock平台配置（无验证接口）
                with patch.object(crawler, 'get_platform_config') as mock_get_config:
                    mock_get_config.return_value = {
                        "platform_id": "weibo",
                        "domain": ".weibo.com"
                    }
                    
                    # Mock页面
                    mock_page = Mock()
                    
                    result = await crawler.verify_session(mock_page, session)
                    
                    assert result is True  # 无验证接口时默认返回True

    @pytest.mark.asyncio
    async def test_sync_session(self, test_session: AsyncSession):
        """测试同步会话"""
        from app.crawler.base import CrawlerBase
        from app.models.platform import PlatformSession
        
        with patch('app.crawler.base.SessionService') as mock_session_service:
            with patch('app.crawler.base.PlatformService') as mock_platform_service:
                crawler = CrawlerBase(test_session, 'weibo')
                
                session = MagicMock(spec=PlatformSession)
                session.id = 1
                session.user_id = 'test_user'
                session.account_name = '测试用户'
                
                # Mock浏览器上下文
                mock_context = Mock()
                mock_cookies = [
                    {"name": "cookie1", "value": "value1", "domain": ".weibo.com", "path": "/"},
                    {"name": "cookie2", "value": "value2", "domain": ".weibo.com", "path": "/"}
                ]
                mock_context.cookies = Mock(return_value=mock_cookies)
                
                result = await crawler.sync_session(mock_context, session)
                
                assert result is not None
                assert result["user_id"] == 'test_user'
                
                # 验证upsert被调用
                assert mock_session_service.return_value.upsert_session.called

    @pytest.mark.asyncio
    async def test_sync_session_no_session(self, test_session: AsyncSession):
        """测试同步会话（无会话）"""
        from app.crawler.base import CrawlerBase
        
        with patch('app.crawler.base.SessionService') as mock_session_service:
            with patch('app.crawler.base.PlatformService') as mock_platform_service:
                crawler = CrawlerBase(test_session, 'weibo')
                
                # Mock浏览器上下文（无Cookie）
                mock_context = Mock()
                mock_context.cookies = Mock(return_value=[])
                
                result = await crawler.sync_session(mock_context, None)
                
                assert result is None
                
                # 验证upsert没有被调用
                assert not mock_session_service.return_value.upsert_session.called

    @pytest.mark.asyncio
    async def test_execute(self, test_session: AsyncSession):
        """测试执行爬取流程"""
        from app.crawler.base import CrawlerBase
        from app.models.platform import PlatformSession
        
        with patch('app.crawler.base.SessionService') as mock_session_service:
            with patch('app.crawler.base.PlatformService') as mock_platform_service:
                crawler = CrawlerBase(test_session, 'weibo')
                
                # Mock抽象方法
                with patch.object(crawler, 'crawl') as mock_crawl:
                    mock_crawl.return_value = {"status": "success", "data": "test_data"}
                    
                    # Mock平台配置
                    with patch.object(crawler, 'get_platform_config') as mock_get_config:
                        mock_get_config.return_value = {
                            "platform_id": "weibo",
                            "domain": ".weibo.com"
                        }
                        
                        # Mock会话
                        with patch.object(crawler, 'get_best_session') as mock_get_session:
                            mock_get_session.return_value = {
                                "id": 1,
                                "platform_id": "weibo",
                                "user_id": "test_user",
                                "cookies_json": '[{"name": "cookie1"}]'
                            }
                            
                            # Mock Playwright
                            with patch('app.crawler.base.async_playwright') as mock_playwright:
                                mock_p = Mock()
                                mock_playwright.return_value.start = Mock()
                                
                                mock_browser = Mock()
                                mock_p.return_value.chromium = Mock(return_value=mock_browser)
                                
                                mock_context = Mock()
                                mock_browser.new_context = Mock(return_value=mock_context)
                                
                                mock_page = Mock()
                                mock_context.new_page = Mock(return_value=mock_page)
                                
                                # 调用execute
                                result = await crawler.execute()
                                
                                # 验证结果
                                assert result is not None
                                assert result["status"] == "success"
                                assert result["data"] == "test_data"
                                
                                # 验证流程
                                assert mock_crawl.called
                                assert mock_context.new_page.called
                                assert mock_context.close.called
                                assert mock_browser.close.called

    @pytest.mark.asyncio
    async def test_execute_verify_failure(self, test_session: AsyncSession):
        """测试执行爬取流程（验证失败）"""
        from app.crawler.base import CrawlerBase
        from app.models.platform import PlatformSession
        
        with patch('app.crawler.base.SessionService') as mock_session_service:
            with patch('app.crawler.base.PlatformService') as mock_platform_service:
                crawler = CrawlerBase(test_session, 'weibo')
                
                # Mock抽象方法
                with patch.object(crawler, 'crawl') as mock_crawl:
                    mock_crawl.return_value = {"status": "success", "data": "test_data"}
                    
                    # Mock平台配置（JSON验证）
                    with patch.object(crawler, 'get_platform_config') as mock_get_config:
                        mock_get_config.return_value = {
                            "platform_id": "weibo",
                            "verify_api": "https://weibo.com/api/verify",
                            "verify_type": "json",
                            "verify_parser": '{"path": "$.data.user.screen_name"}'
                        }
                        
                        # Mock会话
                        with patch.object(crawler, 'get_best_session') as mock_get_session:
                            mock_get_session.return_value = {
                                "id": 1,
                                "platform_id": "weibo",
                                "user_id": "test_user",
                                "cookies_json": '[{"name": "cookie1"}]'
                            }
                            
                            # Mock Playwright
                            with patch('app.crawler.base.async_playwright') as mock_playwright:
                                mock_p = Mock()
                                mock_playwright.return_value.start = Mock()
                                
                                mock_browser = Mock()
                                mock_p.return_value.chromium = Mock(return_value=mock_browser)
                                
                                mock_context = Mock()
                                mock_browser.new_context = Mock(return_value=mock_context)
                                
                                mock_page = Mock()
                                mock_page.content = Mock(return_value='<script>{"data": {}}</script>')
                                mock_context.new_page = Mock(return_value=mock_page)
                                
                                # 调用execute
                                result = await crawler.execute()
                                
                                # 验证结果
                                assert result is not None
                                assert result["status"] == "success"
                                
                                # 验证验证失败时健康度降低
                                assert mock_session_service.return_value.verify_session.called
