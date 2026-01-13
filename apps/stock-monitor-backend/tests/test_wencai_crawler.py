#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问财爬虫测试
测试WencaiCrawler的所有方法
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession


class TestWencaiCrawler:
    """问财爬虫测试类"""

    @pytest.mark.asyncio
    async def test_wencai_crawler_init(self, test_session: AsyncSession):
        """测试问财爬虫初始化"""
        from app.crawler.wencai_crawler import WencaiCrawler
        
        with patch('app.crawler.wencai_crawler.WencaiService') as mock_wencai_service:
            crawler = WencaiCrawler(test_session)
            
            assert crawler.db == test_session
            assert crawler.platform_id == 'wencai'
            assert crawler.base_url == "http://www.iwencai.com/stockpick/search"
            assert crawler.wencai_service is not None

    @pytest.mark.asyncio
    async def test_wencai_crawler_inherits_base(self, test_session: AsyncSession):
        """测试问财爬虫继承基类"""
        from app.crawler.wencai_crawler import WencaiCrawler
        from app.crawler.base import CrawlerBase
        
        crawler = WencaiCrawler(test_session)
        
        assert isinstance(crawler, CrawlerBase)
        assert crawler.session_service is not None
        assert crawler.platform_service is not None

    @pytest.mark.asyncio
    async def test_fetch_page_source_success(self, test_session: AsyncSession):
        """测试获取页面源码（成功）"""
        from app.crawler.wencai_crawler import WencaiCrawler
        from unittest.mock import AsyncMock as Mock
        
        with patch('app.crawler.wencai_crawler.WencaiService') as mock_wencai_service:
            crawler = WencaiCrawler(test_session)
            
            # Mock平台配置
            with patch.object(crawler, 'get_platform_config') as mock_get_config:
                mock_get_config.return_value = {
                    "platform_id": "wencai",
                    "domain": ".iwencai.com"
                }
                
                # Mock会话
                with patch.object(crawler, 'get_best_session') as mock_get_session:
                    mock_get_session.return_value = {
                        "id": 1,
                        "platform_id": "wencai",
                        "user_id": "test_user",
                        "cookies_json": '[{"name": "cookie1"}]'
                    }
                    
                    # Mock Playwright
                    with patch('app.crawler.wencai_crawler.async_playwright') as mock_playwright:
                        mock_p = Mock()
                        mock_playwright.return_value.start = Mock()
                        
                        mock_browser = Mock()
                        mock_p.return_value.chromium = Mock(return_value=mock_browser)
                        
                        mock_context = Mock()
                        mock_browser.new_context = Mock(return_value=mock_context)
                        
                        mock_page = Mock()
                        mock_page.goto = Mock()
                        mock_page.query_selector = Mock(return_value=Mock())
                        mock_page.content = Mock(return_value='<html><body><table><tr><td>股票代码</td><td>股票名称</td></tr></table></body></html>')
                        mock_context.new_page = Mock(return_value=mock_page)
                        
                        # Mock同步会话
                        with patch.object(crawler, 'sync_session') as mock_sync:
                            mock_sync.return_value = None
                            
                            # 调用方法
                            result = await crawler.fetch_page_source("000001")
                            
                            # 验证结果
                            assert result is not None
                            assert '<html>' in result
                            assert '<table>' in result
                            
                            # 验证流程
                            assert mock_page.goto.called
                            assert mock_page.content.called
                            assert mock_sync.called
                            assert mock_context.close.called
                            assert mock_browser.close.called

    @pytest.mark.asyncio
    async def test_fetch_page_source_anti_crawler(self, test_session: AsyncSession):
        """测试获取页面源码（反爬检测）"""
        from app.crawler.wencai_crawler import WencaiCrawler
        from unittest.mock import AsyncMock as Mock
        
        with patch('app.crawler.wencai_crawler.WencaiService') as mock_wencai_service:
            crawler = WencaiCrawler(test_session)
            
            # Mock平台配置
            with patch.object(crawler, 'get_platform_config') as mock_get_config:
                mock_get_config.return_value = {
                    "platform_id": "wencai",
                    "domain": ".iwencai.com"
                }
                
                # Mock会话
                with patch.object(crawler, 'get_best_session') as mock_get_session:
                    mock_get_session.return_value = {
                        "id": 1,
                        "platform_id": "wencai",
                        "user_id": "test_user",
                        "cookies_json": '[{"name": "cookie1"}]'
                    }
                    
                    # Mock Playwright
                    with patch('app.crawler.wencai_crawler.async_playwright') as mock_playwright:
                        mock_p = Mock()
                        mock_playwright.return_value.start = Mock()
                        
                        mock_browser = Mock()
                        mock_p.return_value.chromium = Mock(return_value=mock_browser)
                        
                        mock_context = Mock()
                        mock_browser.new_context = Mock(return_value=mock_context)
                        
                        mock_page = Mock()
                        mock_page.goto = Mock()
                        mock_page.query_selector = Mock(return_value=Mock())
                        mock_page.content = Mock(return_value='<html><body>robot verification</body></html>')
                        mock_context.new_page = Mock(return_value=mock_page)
                        
                        # 调用方法
                        result = await crawler.fetch_page_source("000001")
                        
                        # 验证结果（检测到反爬，返回None）
                        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_page_source_no_session(self, test_session: AsyncSession):
        """测试获取页面源码（无会话）"""
        from app.crawler.wencai_crawler import WencaiCrawler
        from unittest.mock import AsyncMock as Mock
        
        with patch('app.crawler.wencai_crawler.WencaiService') as mock_wencai_service:
            crawler = WencaiCrawler(test_session)
            
            # Mock平台配置
            with patch.object(crawler, 'get_platform_config') as mock_get_config:
                mock_get_config.return_value = {
                    "platform_id": "wencai",
                    "domain": ".iwencai.com"
                }
                
                # Mock无会话
                with patch.object(crawler, 'get_best_session') as mock_get_session:
                    mock_get_session.return_value = None
                    
                    # Mock Playwright
                    with patch('app.crawler.wencai_crawler.async_playwright') as mock_playwright:
                        mock_p = Mock()
                        mock_playwright.return_value.start = Mock()
                        
                        mock_browser = Mock()
                        mock_p.return_value.chromium = Mock(return_value=mock_browser)
                        
                        mock_context = Mock()
                        mock_browser.new_context = Mock(return_value=mock_context)
                        
                        mock_page = Mock()
                        mock_page.goto = Mock()
                        mock_page.query_selector = Mock(return_value=Mock())
                        mock_page.content = Mock(return_value='<html><body><table><tr><td>股票代码</td></tr></table></body></html>')
                        mock_context.new_page = Mock(return_value=mock_page)
                        
                        # Mock同步会话
                        with patch.object(crawler, 'sync_session') as mock_sync:
                            mock_sync.return_value = None
                            
                            # 调用方法
                            result = await crawler.fetch_page_source("000001")
                            
                            # 验证结果
                            assert result is not None
                            assert '<html>' in result

    @pytest.mark.asyncio
    async def test_fetch_and_parse_success(self, test_session: AsyncSession):
        """测试执行抓取并解析（成功）"""
        from app.crawler.wencai_crawler import WencaiCrawler
        
        with patch('app.crawler.wencai_crawler.WencaiService') as mock_wencai_service:
            crawler = WencaiCrawler(test_session)
            
            # Mock fetch_page_source
            with patch.object(crawler, 'fetch_page_source') as mock_fetch:
                mock_fetch.return_value = '<html><body><table><tr><td>000001</td><td>平安银行</td></tr></table></body></html>'
                
                # Mock WencaiService方法
                mock_wencai_service.return_value.create_crawl_batch = Mock(return_value=1)
                mock_wencai_service.return_value.parse_html_table = Mock(return_value=[
                    {"stock_code": "000001", "stock_name": "平安银行"}
                ])
                mock_wencai_service.return_value.save_wencai_stocks = Mock(return_value=(1, 0, []))
                mock_wencai_service.return_value.process_batch_data = Mock()
                mock_wencai_service.return_value.update_batch_status = Mock()
                
                # 调用方法
                result = await crawler.fetch_and_parse("000001", "test_batch", "000001.SZ")
                
                # 验证结果
                assert result is not None
                assert result["status"] == "completed"
                assert result["batch_id"] == 1
                assert result["total"] == 1
                assert result["success"] == 1
                assert result["found_target"] is True
                assert len(result["stocks"]) == 1

    @pytest.mark.asyncio
    async def test_fetch_and_parse_no_data(self, test_session: AsyncSession):
        """测试执行抓取并解析（无数据）"""
        from app.crawler.wencai_crawler import WencaiCrawler
        
        with patch('app.crawler.wencai_crawler.WencaiService') as mock_wencai_service:
            crawler = WencaiCrawler(test_session)
            
            # Mock fetch_page_source
            with patch.object(crawler, 'fetch_page_source') as mock_fetch:
                mock_fetch.return_value = '<html><body></body></html>'
                
                # Mock WencaiService方法
                mock_wencai_service.return_value.create_crawl_batch = Mock(return_value=1)
                mock_wencai_service.return_value.parse_html_table = Mock(return_value=[])
                mock_wencai_service.return_value.save_wencai_stocks = Mock(return_value=(0, 0, []))
                mock_wencai_service.return_value.process_batch_data = Mock()
                mock_wencai_service.return_value.update_batch_status = Mock()
                
                # 调用方法
                result = await crawler.fetch_and_parse("000001", "test_batch")
                
                # 验证结果
                assert result is not None
                assert result["status"] == "completed"
                assert result["total"] == 0
                assert result["success"] == 0
                assert len(result["stocks"]) == 0

    @pytest.mark.asyncio
    async def test_fetch_and_parse_fetch_failed(self, test_session: AsyncSession):
        """测试执行抓取并解析（抓取失败）"""
        from app.crawler.wencai_crawler import WencaiCrawler
        
        with patch('app.crawler.wencai_crawler.WencaiService') as mock_wencai_service:
            crawler = WencaiCrawler(test_session)
            
            # Mock fetch_page_source（失败）
            with patch.object(crawler, 'fetch_page_source') as mock_fetch:
                mock_fetch.return_value = None
                
                # 调用方法
                result = await crawler.fetch_and_parse("000001", "test_batch")
                
                # 验证结果
                assert result is not None
                assert result["status"] == "failed"
                assert result["error"] == "Fetch failed"

    @pytest.mark.asyncio
    async def test_fetch_and_parse_target_not_found(self, test_session: AsyncSession):
        """测试执行抓取并解析（目标股票未找到）"""
        from app.crawler.wencai_crawler import WencaiCrawler
        
        with patch('app.crawler.wencai_crawler.WencaiService') as mock_wencai_service:
            crawler = WencaiCrawler(test_session)
            
            # Mock fetch_page_source
            with patch.object(crawler, 'fetch_page_source') as mock_fetch:
                mock_fetch.return_value = '<html><body><table><tr><td>000002</td><td>万科A</td></tr></table></body></html>'
                
                # Mock WencaiService方法
                mock_wencai_service.return_value.create_crawl_batch = Mock(return_value=1)
                mock_wencai_service.return_value.parse_html_table = Mock(return_value=[
                    {"stock_code": "000002", "stock_name": "万科A"}
                ])
                mock_wencai_service.return_value.save_wencai_stocks = Mock(return_value=(1, 0, []))
                mock_wencai_service.return_value.process_batch_data = Mock()
                mock_wencai_service.return_value.update_batch_status = Mock()
                
                # 调用方法（目标股票是000001.SZ，但结果中只有000002）
                result = await crawler.fetch_and_parse("000002", "test_batch", "000001.SZ")
                
                # 验证结果
                assert result is not None
                assert result["status"] == "completed"
                assert result["found_target"] is False

    @pytest.mark.asyncio
    async def test_wencai_crawler_session_management(self, test_session: AsyncSession):
        """测试问财爬虫的会话管理"""
        from app.crawler.wencai_crawler import WencaiCrawler
        
        crawler = WencaiCrawler(test_session)
        
        # 验证会话服务已初始化
        assert crawler.session_service is not None
        assert crawler.platform_service is not None
        
        # 验证平台ID正确
        assert crawler.platform_id == 'wencai'

    @pytest.mark.asyncio
    async def test_wencai_crawler_base_url(self, test_session: AsyncSession):
        """测试问财爬虫的基础URL"""
        from app.crawler.wencai_crawler import WencaiCrawler
        
        crawler = WencaiCrawler(test_session)
        
        assert crawler.base_url == "http://www.iwencai.com/stockpick/search"

    @pytest.mark.asyncio
    async def test_fetch_and_parse_auto_batch_name(self, test_session: AsyncSession):
        """测试执行抓取并解析（自动生成批次名称）"""
        from app.crawler.wencai_crawler import WencaiCrawler
        
        with patch('app.crawler.wencai_crawler.WencaiService') as mock_wencai_service:
            crawler = WencaiCrawler(test_session)
            
            # Mock fetch_page_source
            with patch.object(crawler, 'fetch_page_source') as mock_fetch:
                mock_fetch.return_value = '<html><body><table><tr><td>000001</td><td>平安银行</td></tr></table></body></html>'
                
                # Mock WencaiService方法
                mock_wencai_service.return_value.create_crawl_batch = Mock(return_value=1)
                mock_wencai_service.return_value.parse_html_table = Mock(return_value=[
                    {"stock_code": "000001", "stock_name": "平安银行"}
                ])
                mock_wencai_service.return_value.save_wencai_stocks = Mock(return_value=(1, 0, []))
                mock_wencai_service.return_value.process_batch_data = Mock()
                mock_wencai_service.return_value.update_batch_status = Mock()
                
                # 调用方法（不提供batch_name）
                result = await crawler.fetch_and_parse("000001")
                
                # 验证结果
                assert result is not None
                assert result["status"] == "completed"
                
                # 验证create_crawl_batch被调用，并且batch_name以AutoCrawl_开头
                assert mock_wencai_service.return_value.create_crawl_batch.called
                call_args = mock_wencai_service.return_value.create_crawl_batch.call_args
                assert call_args[1]['batch_name'].startswith('AutoCrawl_')

    @pytest.mark.asyncio
    async def test_fetch_page_source_wait_for_table(self, test_session: AsyncSession):
        """测试获取页面源码（等待表格加载）"""
        from app.crawler.wencai_crawler import WencaiCrawler
        from unittest.mock import AsyncMock as Mock
        import asyncio
        
        with patch('app.crawler.wencai_crawler.WencaiService') as mock_wencai_service:
            crawler = WencaiCrawler(test_session)
            
            # Mock平台配置
            with patch.object(crawler, 'get_platform_config') as mock_get_config:
                mock_get_config.return_value = {
                    "platform_id": "wencai",
                    "domain": ".iwencai.com"
                }
                
                # Mock会话
                with patch.object(crawler, 'get_best_session') as mock_get_session:
                    mock_get_session.return_value = {
                        "id": 1,
                        "platform_id": "wencai",
                        "user_id": "test_user",
                        "cookies_json": '[{"name": "cookie1"}]'
                    }
                    
                    # Mock Playwright
                    with patch('app.crawler.wencai_crawler.async_playwright') as mock_playwright:
                        mock_p = Mock()
                        mock_playwright.return_value.start = Mock()
                        
                        mock_browser = Mock()
                        mock_p.return_value.chromium = Mock(return_value=mock_browser)
                        
                        mock_context = Mock()
                        mock_browser.new_context = Mock(return_value=mock_context)
                        
                        mock_page = Mock()
                        mock_page.goto = Mock()
                        # 第一次query_selector返回None，第二次返回Mock
                        mock_page.query_selector = Mock(side_effect=[None, Mock()])
                        mock_page.content = Mock(return_value='<html><body><table><tr><td>股票代码</td></tr></table></body></html>')
                        mock_context.new_page = Mock(return_value=mock_page)
                        
                        # Mock同步会话
                        with patch.object(crawler, 'sync_session') as mock_sync:
                            mock_sync.return_value = None
                            
                            # 调用方法
                            result = await crawler.fetch_page_source("000001")
                            
                            # 验证结果
                            assert result is not None
                            assert '<html>' in result
                            
                            # 验证query_selector被多次调用（轮询检查）
                            assert mock_page.query_selector.call_count > 1

    @pytest.mark.asyncio
    async def test_fetch_and_parse_save_error(self, test_session: AsyncSession):
        """测试执行抓取并解析（保存错误）"""
        from app.crawler.wencai_crawler import WencaiCrawler
        
        with patch('app.crawler.wencai_crawler.WencaiService') as mock_wencai_service:
            crawler = WencaiCrawler(test_session)
            
            # Mock fetch_page_source
            with patch.object(crawler, 'fetch_page_source') as mock_fetch:
                mock_fetch.return_value = '<html><body><table><tr><td>000001</td><td>平安银行</td></tr></table></body></html>'
                
                # Mock WencaiService方法
                mock_wencai_service.return_value.create_crawl_batch = Mock(return_value=1)
                mock_wencai_service.return_value.parse_html_table = Mock(return_value=[
                    {"stock_code": "000001", "stock_name": "平安银行"}
                ])
                mock_wencai_service.return_value.save_wencai_stocks = Mock(return_value=(0, 1, ["保存错误"]))
                mock_wencai_service.return_value.process_batch_data = Mock()
                mock_wencai_service.return_value.update_batch_status = Mock()
                
                # 调用方法
                result = await crawler.fetch_and_parse("000001", "test_batch")
                
                # 验证结果
                assert result is not None
                assert result["status"] == "failed"
                assert result["success"] == 0
                assert result["failed"] == 1
