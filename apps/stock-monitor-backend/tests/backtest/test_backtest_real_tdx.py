#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实通达信环境回测脚本
使用实际通达信数据进行回测
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
import asyncio
from datetime import date, timedelta
from typing import List, Dict, Any
import pandas as pd
from loguru import logger

# 添加通达信Python路径
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

try:
    from tqcenter import tq
    TDX_AVAILABLE = True
except ImportError:
    TDX_AVAILABLE = False
    logger.warning("通达信模块不可用，请确保通达信已安装")

from app.services.stock_selector import StockSelector
from app.services.daily_stock_selection_service import DailyStockSelectionService


class TestBacktestRealTdx:
    """
    使用真实通达信数据进行回测
    要求：通达信客户端必须已启动并登录
    """
    
    @pytest.fixture(scope="class")
    def tdx_client(self):
        """初始化通达信连接"""
        if not TDX_AVAILABLE:
            pytest.skip("通达信模块不可用")
        
        try:
            tq.initialize(__file__)
            logger.info("通达信连接初始化成功")
            return tq
        except Exception as e:
            logger.error(f"通达信连接失败: {e}")
            pytest.skip(f"通达信连接失败: {e}")
    
    def _is_trading_day(self, d: date) -> bool:
        """判断是否为交易日（简化版：排除周末）"""
        return d.weekday() < 5
    
    def _get_trading_days(self, start_date: date, end_date: date) -> List[date]:
        """获取交易日列表"""
        trading_days = []
        current = start_date
        while current <= end_date:
            if self._is_trading_day(current):
                trading_days.append(current)
            current += timedelta(days=1)
        return trading_days
    
    @pytest.mark.skipif(not TDX_AVAILABLE, reason="通达信模块不可用")
    def test_tdx_connection(self, tdx_client):
        """
        测试通达信连接是否正常
        """
        try:
            # 尝试获取市场数据验证连接
            data = tdx_client.get_market_data(
                field_list=['Close', 'Volume'],
                stock_list=['000001.SZ', '600000.SH'],
                period='1d',
                count=1
            )
            assert data is not None, "无法获取市场数据"
            
            # 处理不同数据格式
            if isinstance(data, dict):
                assert len(data) > 0, "市场数据为空字典"
                logger.info(f"通达信连接正常，获取到字典数据，键: {list(data.keys())}")
            elif hasattr(data, 'empty'):
                assert not data.empty, "市场数据为空"
                logger.info(f"通达信连接正常，获取到 {len(data)} 条数据")
            else:
                logger.info(f"通达信连接正常，数据类型: {type(data)}")
                
        except Exception as e:
            pytest.fail(f"通达信连接测试失败: {e}")
    
    @pytest.mark.skipif(not TDX_AVAILABLE, reason="通达信模块不可用")
    def test_get_user_sectors(self, tdx_client):
        """
        测试获取用户自定义板块列表
        """
        try:
            sectors = tdx_client.get_user_sector()
            logger.info(f"获取到 {len(sectors)} 个自定义板块")
            for sector in sectors[:5]:  # 只显示前5个
                logger.info(f"  板块: {sector.get('Name')} ({sector.get('Code')})")
        except Exception as e:
            logger.warning(f"获取板块列表失败: {e}")
    
    @pytest.mark.skipif(not TDX_AVAILABLE, reason="通达信模块不可用")
    def test_single_day_selection_real(self, tdx_client):
        """
        使用真实数据测试单日选股
        日期：最近一个交易日
        """
        from app.services.tdx_data_sync_checker import TdxDataSyncChecker
        from app.services.daily_stock_selection_service import DailyStockSelectionService
        
        # 使用最近一个交易日
        trade_date = date(2025, 2, 10)  # 可以根据需要修改
        
        logger.info(f"\n{'='*60}")
        logger.info(f"开始真实数据回测: {trade_date}")
        logger.info(f"{'='*60}")
        
        # 1. 数据同步检查
        logger.info("Step 1: 数据同步检查")
        checker = TdxDataSyncChecker(tdx_client=tdx_client)
        sync_result = checker.check_daily_data_sync(trade_date)
        
        logger.info(f"  状态: {sync_result['status']}")
        logger.info(f"  客户端在线: {sync_result['checks']['client_online']}")
        logger.info(f"  数据完整: {sync_result['checks']['data_complete']}")
        logger.info(f"  时间戳有效: {sync_result['checks']['timestamp_valid']}")
        logger.info(f"  数据合理: {sync_result['checks']['data_reasonable']}")
        
        if sync_result['status'] != 'success':
            logger.warning(f"数据同步检查未通过: {sync_result.get('message')}")
            return
        
        # 2. 执行选股
        logger.info("\nStep 2: 执行选股")
        selection_service = DailyStockSelectionService(tdx_client=tdx_client)
        result = selection_service.execute_daily_selection(trade_date)
        
        logger.info(f"  选股状态: {result['status']}")
        logger.info(f"  板块代码: {result.get('sector_code')}")
        logger.info(f"  板块名称: {result.get('sector_name')}")
        logger.info(f"  选中股票数: {result.get('selected_count', 0)}")
        
        if result.get('strategies'):
            logger.info("  各策略选中数量:")
            for strategy, count in result['strategies'].items():
                logger.info(f"    {strategy}: {count}只")
        
        # 验证结果
        assert result['status'] == 'success', f"选股失败: {result.get('reason')}"
        assert result.get('sector_code'), "板块代码为空"
        
        logger.info(f"\n{'='*60}")
        logger.info(f"回测完成: {trade_date}")
        logger.info(f"{'='*60}\n")
    
    @pytest.mark.skipif(not TDX_AVAILABLE, reason="通达信模块不可用")
    def test_backtest_feb_to_march_real(self, tdx_client):
        """
        使用真实数据进行2月-3月回测
        注意：这会创建多个板块，请确保通达信环境可用
        """
        from app.services.tdx_data_sync_checker import TdxDataSyncChecker
        from app.services.daily_stock_selection_service import DailyStockSelectionService
        
        # 回测日期范围
        start_date = date(2025, 2, 1)
        end_date = date(2025, 3, 25)
        trading_days = self._get_trading_days(start_date, end_date)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"开始完整回测: {start_date} 至 {end_date}")
        logger.info(f"交易日数量: {len(trading_days)}")
        logger.info(f"{'='*60}\n")
        
        results = []
        checker = TdxDataSyncChecker(tdx_client=tdx_client)
        selection_service = DailyStockSelectionService(tdx_client=tdx_client)
        
        for i, trade_date in enumerate(trading_days):
            logger.info(f"\n[{i+1}/{len(trading_days)}] 处理日期: {trade_date}")
            
            # 数据同步检查
            sync_result = checker.check_daily_data_sync(trade_date)
            if sync_result['status'] != 'success':
                logger.warning(f"  跳过: 数据同步检查失败")
                results.append({
                    'date': trade_date,
                    'status': 'skipped',
                    'reason': 'data_sync_failed'
                })
                continue
            
            # 执行选股
            result = selection_service.execute_daily_selection(trade_date)
            
            results.append({
                'date': trade_date,
                'status': result['status'],
                'sector_code': result.get('sector_code'),
                'selected_count': result.get('selected_count', 0),
                'strategies': result.get('strategies', {})
            })
            
            logger.info(f"  结果: {result['status']}, 选中 {result.get('selected_count', 0)} 只")
            
            # 每处理5天暂停一下，避免请求过快
            if (i + 1) % 5 == 0:
                logger.info("  [暂停2秒...]")
                import time
                time.sleep(2)
        
        # 统计结果
        success_count = sum(1 for r in results if r['status'] == 'success')
        skipped_count = sum(1 for r in results if r['status'] == 'skipped')
        failed_count = sum(1 for r in results if r['status'] == 'failed')
        
        logger.info(f"\n{'='*60}")
        logger.info(f"回测统计")
        logger.info(f"{'='*60}")
        logger.info(f"总交易日: {len(trading_days)}")
        logger.info(f"成功: {success_count}")
        logger.info(f"跳过: {skipped_count}")
        logger.info(f"失败: {failed_count}")
        logger.info(f"成功率: {success_count/len(trading_days)*100:.2f}%")
        logger.info(f"{'='*60}\n")
        
        # 输出每日详细结果
        logger.info("\n每日详细结果:")
        for r in results:
            if r['status'] == 'success':
                logger.info(f"  {r['date']}: {r['sector_code']} - {r['selected_count']}只")
        
        # 验证
        assert success_count > 0, "没有成功执行的交易日"
    
    @pytest.mark.skipif(not TDX_AVAILABLE, reason="通达信模块不可用")
    def test_3x_volume_strategy_real(self, tdx_client):
        """
        使用真实数据测试3倍量策略
        """
        selector = StockSelector()
        
        # 获取市场数据
        logger.info("获取市场数据用于3倍量策略测试")
        
        # 获取股票列表（取前100只测试）
        try:
            # 尝试获取板块中的股票列表
            sectors = tdx_client.get_user_sector()
            if sectors:
                sector_code = sectors[0]['Code']
                stock_list = tdx_client.get_stock_list_in_sector(sector_code)
                stock_codes = [s['Code'] for s in stock_list[:100]]
            else:
                # 使用默认股票列表
                stock_codes = ['000001.SZ', '000002.SZ', '600000.SH'] * 34  # 102只
        except:
            stock_codes = ['000001.SZ', '000002.SZ', '600000.SH'] * 34
        
        # 获取今日和前一日数据
        logger.info(f"获取 {len(stock_codes)} 只股票的成交量数据")
        
        try:
            # 获取两日数据
            data = tdx_client.get_market_data(
                field_list=['Volume'],
                stock_list=stock_codes,
                period='1d',
                count=2,  # 获取2天数据
                dividend_type='front'
            )
            
            logger.info(f"数据形状: {data.shape}")
            logger.info(f"数据索引: {data.index.tolist()}")
            logger.info(f"数据列数: {len(data.columns)}")
            
            # 执行3倍量策略
            selected = selector.select_3x_volume(data)
            
            logger.info(f"\n3倍量策略结果:")
            logger.info(f"  分析股票数: {len(data.columns)}")
            logger.info(f"  选中股票数: {len(selected)}")
            
            if selected:
                logger.info(f"  选中股票: {selected[:10]}")  # 只显示前10只
            
        except Exception as e:
            logger.error(f"3倍量策略测试失败: {e}")
            import traceback
            traceback.print_exc()
    
    @pytest.mark.skipif(not TDX_AVAILABLE, reason="通达信模块不可用")
    def test_sector_creation_real(self, tdx_client):
        """
        测试真实板块创建
        注意：这会实际创建板块，测试后请手动清理
        """
        from app.services.daily_stock_selection_service import DailyStockSelectionService
        
        trade_date = date(2025, 2, 10)
        # 板块代码格式: 3BL250210 (年份后两位+月份+日期)
        sector_code = f"3BL{trade_date.strftime('%y%m%d')}"
        sector_name = f"3倍量涨停{trade_date.strftime('%y%m%d')}"
        
        logger.info(f"\n测试板块创建:")
        logger.info(f"  板块代码: {sector_code}")
        logger.info(f"  板块名称: {sector_name}")
        
        service = DailyStockSelectionService(tdx_client=tdx_client)
        
        # 创建板块
        result = service.create_sector(sector_code, sector_name)
        
        if result:
            logger.info(f"  板块创建成功: {sector_code}")
        else:
            logger.warning(f"  板块创建失败或已存在")
        
        # 获取板块列表验证
        try:
            sectors = tdx_client.get_user_sector()
            sector_codes = [s['Code'] for s in sectors]
            
            if sector_code in sector_codes:
                logger.info(f"  验证成功: 板块 {sector_code} 存在于用户板块列表中")
            else:
                logger.warning(f"  验证失败: 板块 {sector_code} 未找到")
        except Exception as e:
            logger.warning(f"  验证失败: {e}")


if __name__ == "__main__":
    # 如果直接运行，执行简单测试
    if TDX_AVAILABLE:
        print("通达信模块已加载，准备执行回测...")
        
        try:
            tq.initialize(__file__)
            print("通达信连接初始化成功")
            
            # 简单测试：获取市场数据
            print("\n测试获取市场数据...")
            data = tq.get_market_data(
                field_list=['Close', 'Volume'],
                stock_list=['000001.SZ', '600000.SH'],
                period='1d',
                count=1
            )
            print(f"数据类型: {type(data)}")
            if hasattr(data, 'shape'):
                print(f"获取到数据: {data.shape}")
                print(f"\n数据预览:")
                print(data)
            elif isinstance(data, dict):
                print(f"获取到字典数据，键: {list(data.keys())}")
                for key, value in data.items():
                    print(f"  {key}: {type(value)}")
            else:
                print(f"数据: {data}")
            
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("通达信模块不可用，请检查:")
        print("1. 通达信是否已安装")
        print("2. 路径 C:\\new_tdx_test\\PYPlugins\\user 是否存在")
        print("3. 通达信客户端是否已启动")
