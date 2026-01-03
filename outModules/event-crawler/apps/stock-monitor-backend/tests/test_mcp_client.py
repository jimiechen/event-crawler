#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP客户端测试
测试同花顺MCP客户端的数据抓取功能和错误处理
"""

import pytest
import asyncio
import json
import logging
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.tonghuashun_mcp_client import TongHuaShunMCPClient
from app.services.stock_data_service import StockDataService, StockInfo, StockData
from app.utils.data_deduplication import DataDeduplicationManager

# 配置pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestTongHuaShunMCPClient:
    """
    同花顺MCP客户端测试类
    """
    
    def setup_method(self):
        """测试前置设置"""
        self.client = TongHuaShunMCPClient()
        self.test_stock_codes = ['000001', '000002', '600000']
    
    def test_client_initialization(self):
        """测试客户端初始化"""
        assert self.client.mcp_server_url == "http://localhost:56889/mcp"
        assert self.client.session_id is not None
        assert self.client.request_id == 1
        assert 'user_stocks' in self.client.base_urls
        assert 'stock_api' in self.client.base_urls
        
        logger.info("✓ 客户端初始化测试通过")
    
    def test_generate_session_id(self):
        """测试会话ID生成"""
        session_id = self.client._generate_session_id()
        assert session_id.startswith('ths_session_')
        assert len(session_id) > 15
        
        # 测试ID格式正确
        import re
        pattern = r'^ths_session_\d+$'
        assert re.match(pattern, session_id)
        
        logger.info("✓ 会话ID生成测试通过")
    
    def test_hash_generation(self):
        """测试哈希生成"""
        test_data = {
            'code': '000001',
            'price': 10.25,
            'volume': 1000000
        }
        
        hash1 = self.client.generate_data_hash(test_data)
        hash2 = self.client.generate_data_hash(test_data)
        
        # 相同数据应该生成相同哈希
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256长度
        
        # 不同数据应该生成不同哈希
        test_data2 = test_data.copy()
        test_data2['price'] = 10.26
        hash3 = self.client.generate_data_hash(test_data2)
        assert hash1 != hash3
        
        logger.info("✓ 哈希生成测试通过")
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_chrome_get_web_content_success(self, mock_post):
        """测试成功获取网页内容"""
        # 模拟成功响应
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "content": "<html><body>Test Content</body></html>",
                "isError": False
            }
        })
        
        mock_post.return_value.__aenter__.return_value = mock_response
        
        result = await self.client.chrome_get_web_content("https://test.com")
        
        assert result is not None
        assert result.get('content') == "<html><body>Test Content</body></html>"
        assert not result.get('isError', True)
        
        logger.info("✓ 网页内容获取成功测试通过")
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_chrome_get_web_content_http_error(self, mock_post):
        """测试HTTP错误处理"""
        # 模拟HTTP错误
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text.return_value = "Internal Server Error"
        
        mock_post.return_value.__aenter__.return_value = mock_response
        
        with pytest.raises(Exception) as exc_info:
            await self.client.chrome_get_web_content("https://test.com")
        
        assert "HTTP错误 500" in str(exc_info.value)
        
        logger.info("✓ HTTP错误处理测试通过")
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_chrome_get_web_content_sse_format(self, mock_post):
        """测试SSE格式响应解析"""
        # 模拟SSE格式响应 - 修复JSON格式
        sse_response = 'event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":"{\\"htmlContent\\":\\"<html>SSE Content</html>\\"}"}],"isError":false}}\n\n'
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = sse_response
        
        mock_post.return_value.__aenter__.return_value = mock_response
        
        result = await self.client.chrome_get_web_content("https://test.com")
        
        assert result is not None
        assert result.get('content') == "<html>SSE Content</html>"
        
        logger.info("✓ SSE格式响应解析测试通过")
    
    def test_parse_stock_list_from_html(self):
        """测试从HTML解析股票列表"""
        html_content = '''
        <div data-code="000001"><span class="name">平安银行</span></div>
        <div data-code="000002"><span class="name">万科A</span></div>
        <div data-code="600000"><span class="name">浦发银行</span></div>
        '''
        
        stocks = self.client._parse_stock_list_from_html(html_content)
        
        assert len(stocks) == 3
        assert stocks[0]['code'] == '000001'
        assert stocks[0]['name'] == '平安银行'
        assert stocks[0]['market'] == 'SZ'
        assert stocks[2]['code'] == '600000'
        assert stocks[2]['market'] == 'SH'
        
        logger.info("✓ HTML股票列表解析测试通过")
    
    def test_parse_jsonp_response(self):
        """测试JSONP响应解析"""
        jsonp_content = '''callback({"data":[["000001","平安银行","10.25","0.15","1.48","1000000","1025000000"]]})
        '''
        
        stock_data = self.client._parse_jsonp_response(jsonp_content)
        
        assert len(stock_data) == 1
        assert stock_data[0]['code'] == '000001'
        assert stock_data[0]['name'] == '平安银行'
        assert stock_data[0]['current_price'] == 10.25
        assert stock_data[0]['change_amount'] == 0.15
        assert stock_data[0]['change_percent'] == 1.48
        assert stock_data[0]['volume'] == 1000000
        
        logger.info("✓ JSONP响应解析测试通过")
    
    @pytest.mark.asyncio
    @patch.object(TongHuaShunMCPClient, 'chrome_get_web_content')
    async def test_get_user_stock_list_success(self, mock_get_content):
        """测试获取用户自选股列表成功"""
        # 模拟成功响应
        mock_get_content.return_value = {
            'content': '<div data-code="000001"><span class="name">平安银行</span></div>'
        }
        
        result = await self.client.get_user_stock_list()
        
        assert result['success'] is True
        assert len(result['stocks']) == 1
        assert result['stocks'][0]['code'] == '000001'
        assert result['total_count'] == 1
        
        logger.info("✓ 获取用户自选股列表成功测试通过")
    
    @pytest.mark.asyncio
    @patch.object(TongHuaShunMCPClient, 'chrome_get_web_content')
    async def test_get_user_stock_list_error(self, mock_get_content):
        """测试获取用户自选股列表失败"""
        # 模拟异常
        mock_get_content.side_effect = Exception("网络错误")
        
        result = await self.client.get_user_stock_list()
        
        assert result['success'] is False
        assert '网络错误' in result['error']
        assert result['total_count'] == 0
        
        logger.info("✓ 获取用户自选股列表失败测试通过")
    
    @pytest.mark.asyncio
    @patch.object(TongHuaShunMCPClient, 'chrome_get_web_content')
    async def test_get_stock_realtime_data_success(self, mock_get_content):
        """测试获取股票实时数据成功"""
        # 模拟JSONP响应
        mock_get_content.return_value = {
            'content': 'callback({"data":[["000001","平安银行","10.25","0.15","1.48","1000000","1025000000"]]})',
        }
        
        result = await self.client.get_stock_realtime_data(['000001'])
        
        assert result['success'] is True
        assert len(result['stock_data']) == 1
        assert result['stock_data'][0]['code'] == '000001'
        assert result['stock_data'][0]['current_price'] == 10.25
        
        logger.info("✓ 获取股票实时数据成功测试通过")

class TestStockDataService:
    """
    股票数据服务测试类
    """
    
    def setup_method(self):
        """测试前置设置"""
        # 使用模拟的MCP客户端
        self.mock_client = AsyncMock(spec=TongHuaShunMCPClient)
        self.service = StockDataService()
    
    @pytest.mark.asyncio
    @patch('app.services.stock_data_service.execute_one')
    @patch('app.services.stock_data_service.execute_update')
    async def test_sync_stock_info_from_web(self, mock_execute_update, mock_execute_one):
        """测试从网页同步股票信息"""
        # 模拟MCP客户端返回
        self.mock_client.get_user_stock_list.return_value = {
            'success': True,
            'stocks': [
                {'code': '000001', 'name': '平安银行', 'market': 'SZ'},
                {'code': '600000', 'name': '浦发银行', 'market': 'SH'}
            ]
        }
        
        # 模拟数据库查询（股票不存在）
        mock_execute_one.return_value = None
        mock_execute_update.return_value = 1
        
        result = await self.service.sync_stock_info_from_web()
        
        assert result['success'] is True
        assert result['synced_count'] == 2
        assert result['updated_count'] == 0
        
        logger.info("✓ 股票信息同步测试通过")
    
    @pytest.mark.asyncio
    @patch('app.services.stock_data_service.execute_query')
    async def test_get_monitor_stock_list(self, mock_execute_query):
        """测试获取监控股票列表"""
        # 模拟数据库返回
        mock_execute_query.return_value = [
            {'stock_code': '000001'},
            {'stock_code': '000002'},
            {'stock_code': '600000'}
        ]
        
        stock_codes = await self.service.get_monitor_stock_list()
        
        assert len(stock_codes) == 3
        assert '000001' in stock_codes
        assert '600000' in stock_codes
        
        logger.info("✓ 获取监控股票列表测试通过")
    
    @pytest.mark.asyncio
    @patch('app.services.stock_data_service.execute_update')
    @patch('app.services.stock_data_service.execute_one')
    async def test_fetch_and_store_stock_data(self, mock_execute_one, mock_execute_update):
        """测试抓取并存储股票数据"""
        # 模拟MCP客户端返回
        self.mock_client.get_stock_realtime_data.return_value = {
            'success': True,
            'stock_data': [
                {
                    'code': '000001',
                    'name': '平安银行',
                    'current_price': 10.25,
                    'change_amount': 0.15,
                    'change_percent': 1.48,
                    'volume': 1000000,
                    'turnover': 1025000000.0,
                    'timestamp': '2024-01-01T10:00:00'
                }
            ],
            'raw_content': 'test content'
        }
        
        # 模拟哈希生成
        self.mock_client.generate_data_hash.return_value = 'test_hash_123'
        
        # 模拟去重检查（不重复）
        mock_execute_one.return_value = None
        mock_execute_update.return_value = 1
        
        result = await self.service.fetch_and_store_stock_data(['000001'])
        
        assert result['success'] is True
        assert result['fetched_count'] == 1
        assert result['stored_count'] == 1
        assert result['duplicate_count'] == 0
        
        logger.info("✓ 抓取并存储股票数据测试通过")
    
    @pytest.mark.asyncio
    @patch('app.services.stock_data_service.execute_one')
    async def test_add_monitor_stock(self, mock_execute_one):
        """测试添加监控股票"""
        # 模拟股票存在
        mock_execute_one.side_effect = [
            {'code': '000001'},  # 股票存在
            None  # 监控列表中不存在
        ]
        
        with patch('app.services.stock_data_service.execute_update') as mock_update:
            mock_update.return_value = 1
            result = await self.service.add_monitor_stock('000001', priority=5)
        
        assert result is True
        
        logger.info("✓ 添加监控股票测试通过")

class TestDataDeduplication:
    """
    数据去重测试类
    """
    
    def setup_method(self):
        """测试前置设置"""
        self.dedup = DataDeduplicationManager(cache_size=100)
    
    def test_generate_hash_consistency(self):
        """测试哈希生成一致性"""
        test_data = {
            'code': '000001',
            'price': 10.25,
            'volume': 1000000,
            'timestamp': '2024-01-01T10:00:00'
        }
        
        hash1 = self.dedup.generate_hash(test_data)
        hash2 = self.dedup.generate_hash(test_data)
        
        assert hash1 == hash2
        assert len(hash1) == 64
        
        logger.info("✓ 哈希生成一致性测试通过")
    
    def test_generate_hash_with_precision(self):
        """测试带精度控制的哈希生成"""
        test_data = {
            'code': '000001',
            'price': 10.2567,
            'volume': 1000000
        }
        
        # 精度控制到2位小数
        precision = {'price': 2}
        hash1 = self.dedup.generate_hash(test_data, precision=precision)
        
        # 修改价格到第3位小数
        test_data['price'] = 10.2589
        hash2 = self.dedup.generate_hash(test_data, precision=precision)
        
        # 由于精度控制，哈希应该相同
        assert hash1 == hash2
        
        logger.info("✓ 精度控制哈希生成测试通过")
    
    def test_generate_hash_with_fields(self):
        """测试指定字段哈希生成"""
        test_data = {
            'code': '000001',
            'price': 10.25,
            'volume': 1000000,
            'extra_field': 'should_be_ignored'
        }
        
        # 只使用指定字段
        hash_fields = ['code', 'price', 'volume']
        hash1 = self.dedup.generate_hash(test_data, hash_fields=hash_fields)
        
        # 修改未指定的字段
        test_data['extra_field'] = 'changed_value'
        hash2 = self.dedup.generate_hash(test_data, hash_fields=hash_fields)
        
        # 哈希应该相同
        assert hash1 == hash2
        
        logger.info("✓ 指定字段哈希生成测试通过")
    
    @pytest.mark.asyncio
    @patch('app.utils.data_deduplication.execute_one')
    async def test_check_duplicate_not_found(self, mock_execute_one):
        """测试检查重复数据（未找到）"""
        mock_execute_one.return_value = None
        
        test_data = {'code': '000001', 'price': 10.25}
        result = await self.dedup.check_duplicate(test_data, '000001')
        
        assert result.is_duplicate is False
        assert result.hash_value is not None
        assert result.existing_id is None
        
        logger.info("✓ 检查重复数据（未找到）测试通过")
    
    @pytest.mark.asyncio
    @patch('app.utils.data_deduplication.execute_one')
    async def test_check_duplicate_found(self, mock_execute_one):
        """测试检查重复数据（找到）"""
        mock_execute_one.return_value = {
            'id': 123,
            'stock_code': '000001',
            'data_timestamp': datetime(2024, 1, 1, 10, 0, 0)
        }
        
        test_data = {'code': '000001', 'price': 10.25}
        result = await self.dedup.check_duplicate(test_data, '000001')
        
        assert result.is_duplicate is True
        assert result.existing_id == 123
        assert result.existing_timestamp is not None
        
        logger.info("✓ 检查重复数据（找到）测试通过")
    
    @pytest.mark.asyncio
    @patch('app.utils.data_deduplication.execute_update')
    async def test_record_hash(self, mock_execute_update):
        """测试记录哈希值"""
        mock_execute_update.return_value = 1
        
        result = await self.dedup.record_hash('test_hash', '000001')
        
        assert result is True
        assert 'test_hash' in self.dedup._hash_cache
        
        logger.info("✓ 记录哈希值测试通过")

async def run_integration_test():
    """
    集成测试：测试完整的数据抓取流程
    """
    logger.info("开始集成测试...")
    
    try:
        # 创建MCP客户端（使用模拟）
        with patch('aiohttp.ClientSession.post') as mock_post:
            # 模拟成功的网页内容获取
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text.return_value = json.dumps({
                "result": {
                    "content": '<div data-code="000001"><span class="name">平安银行</span></div>',
                    "isError": False
                }
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            client = TongHuaShunMCPClient()
            
            # 测试获取自选股列表
            stock_list_result = await client.get_user_stock_list()
            assert stock_list_result['success'] is True
            logger.info("✓ 自选股列表获取成功")
            
            # 模拟实时数据获取
            mock_response.text.return_value = json.dumps({
                "result": {
                    "content": 'callback({"data":[["000001","平安银行","10.25","0.15","1.48","1000000","1025000000"]]})',
                    "isError": False
                }
            })
            
            # 测试获取实时数据
            realtime_result = await client.get_stock_realtime_data(['000001'])
            assert realtime_result['success'] is True
            assert len(realtime_result['stock_data']) == 1
            logger.info("✓ 实时数据获取成功")
            
            # 测试数据去重
            dedup = DataDeduplicationManager()
            test_data = realtime_result['stock_data'][0]
            
            with patch('app.utils.data_deduplication.execute_one') as mock_execute_one:
                mock_execute_one.return_value = None  # 模拟数据不重复
                
                result = await dedup.check_duplicate(test_data, test_data['code'])
                assert result.is_duplicate is False
                logger.info("✓ 数据去重检查成功")
        
        logger.info("✓ 集成测试全部通过")
        return True
        
    except Exception as e:
        logger.error(f"✗ 集成测试失败: {e}")
        return False

async def run_performance_test():
    """
    性能测试：测试大量数据的处理性能
    """
    logger.info("开始性能测试...")
    
    try:
        dedup = DataDeduplicationManager(cache_size=1000)
        
        # 生成测试数据
        test_data_list = []
        for i in range(1000):
            test_data_list.append({
                'code': f'{i:06d}',
                'price': 10.0 + i * 0.01,
                'volume': 1000000 + i * 1000,
                'timestamp': f'2024-01-01T{i%24:02d}:00:00'
            })
        
        # 测试批量哈希生成
        start_time = datetime.now()
        hashes = [dedup.generate_hash(data) for data in test_data_list]
        hash_time = (datetime.now() - start_time).total_seconds()
        
        assert len(hashes) == 1000
        assert len(set(hashes)) == 1000  # 所有哈希都应该不同
        
        logger.info(f"✓ 批量哈希生成完成: {len(hashes)} 条数据，耗时 {hash_time:.3f} 秒")
        
        # 测试缓存性能
        with patch('app.utils.data_deduplication.execute_one') as mock_execute_one:
            mock_execute_one.return_value = None
            
            start_time = datetime.now()
            results = await dedup.batch_check_duplicates(test_data_list[:100])
            batch_time = (datetime.now() - start_time).total_seconds()
            
            assert len(results) == 100
            logger.info(f"✓ 批量去重检查完成: {len(results)} 条数据，耗时 {batch_time:.3f} 秒")
        
        logger.info("✓ 性能测试全部通过")
        return True
        
    except Exception as e:
        logger.error(f"✗ 性能测试失败: {e}")
        return False

async def run_error_handling_test():
    """
    错误处理测试：测试各种异常情况的处理
    """
    logger.info("开始错误处理测试...")
    
    try:
        client = TongHuaShunMCPClient()
        
        # 测试网络错误处理
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = Exception("网络连接失败")
            
            with pytest.raises(Exception):
                await client.chrome_get_web_content("https://test.com")
            
            logger.info("✓ 网络错误处理测试通过")
        
        # 测试无效数据处理
        invalid_jsonp = "invalid_jsonp_format"
        stock_data = client._parse_jsonp_response(invalid_jsonp)
        assert len(stock_data) == 0
        logger.info("✓ 无效数据处理测试通过")
        
        # 测试去重错误处理
        dedup = DataDeduplicationManager()
        
        with patch('app.utils.data_deduplication.execute_one') as mock_execute_one:
            mock_execute_one.side_effect = Exception("数据库连接失败")
            
            # 即使数据库失败，也应该返回结果（假设不重复）
            result = await dedup.check_duplicate({'test': 'data'})
            assert result.is_duplicate is False
            logger.info("✓ 去重错误处理测试通过")
        
        logger.info("✓ 错误处理测试全部通过")
        return True
        
    except Exception as e:
        logger.error(f"✗ 错误处理测试失败: {e}")
        return False

async def main():
    """
    运行所有测试
    """
    logger.info("=" * 60)
    logger.info("开始MCP客户端测试套件")
    logger.info("=" * 60)
    
    test_results = []
    
    # 单元测试
    logger.info("\n1. 单元测试")
    logger.info("-" * 30)
    
    try:
        # TongHuaShunMCPClient测试
        client_test = TestTongHuaShunMCPClient()
        client_test.setup_method()
        
        client_test.test_client_initialization()
        client_test.test_generate_session_id()
        client_test.test_hash_generation()
        await client_test.test_chrome_get_web_content_success()
        await client_test.test_chrome_get_web_content_http_error()
        await client_test.test_chrome_get_web_content_sse_format()
        client_test.test_parse_stock_list_from_html()
        client_test.test_parse_jsonp_response()
        await client_test.test_get_user_stock_list_success()
        await client_test.test_get_user_stock_list_error()
        await client_test.test_get_stock_realtime_data_success()
        
        # StockDataService测试
        service_test = TestStockDataService()
        service_test.setup_method()
        
        await service_test.test_sync_stock_info_from_web()
        await service_test.test_get_monitor_stock_list()
        await service_test.test_fetch_and_store_stock_data()
        await service_test.test_add_monitor_stock()
        
        # DataDeduplication测试
        dedup_test = TestDataDeduplication()
        dedup_test.setup_method()
        
        dedup_test.test_generate_hash_consistency()
        dedup_test.test_generate_hash_with_precision()
        dedup_test.test_generate_hash_with_fields()
        await dedup_test.test_check_duplicate_not_found()
        await dedup_test.test_check_duplicate_found()
        await dedup_test.test_record_hash()
        
        test_results.append(("单元测试", True))
        logger.info("✓ 单元测试全部通过")
        
    except Exception as e:
        test_results.append(("单元测试", False))
        logger.error(f"✗ 单元测试失败: {e}")
    
    # 集成测试
    logger.info("\n2. 集成测试")
    logger.info("-" * 30)
    integration_result = await run_integration_test()
    test_results.append(("集成测试", integration_result))
    
    # 性能测试
    logger.info("\n3. 性能测试")
    logger.info("-" * 30)
    performance_result = await run_performance_test()
    test_results.append(("性能测试", performance_result))
    
    # 错误处理测试
    logger.info("\n4. 错误处理测试")
    logger.info("-" * 30)
    error_handling_result = await run_error_handling_test()
    test_results.append(("错误处理测试", error_handling_result))
    
    # 测试结果汇总
    logger.info("\n" + "=" * 60)
    logger.info("测试结果汇总")
    logger.info("=" * 60)
    
    passed_count = 0
    total_count = len(test_results)
    
    for test_name, result in test_results:
        status = "✓ 通过" if result else "✗ 失败"
        logger.info(f"{test_name}: {status}")
        if result:
            passed_count += 1
    
    logger.info(f"\n总计: {passed_count}/{total_count} 测试通过")
    
    if passed_count == total_count:
        logger.info("🎉 所有测试都通过了！")
        return True
    else:
        logger.error(f"❌ {total_count - passed_count} 个测试失败")
        return False

if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())
    exit(0 if success else 1)