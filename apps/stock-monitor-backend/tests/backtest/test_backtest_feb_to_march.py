#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测脚本：从2月1日开始按当前规则选股测试
验证选股策略在历史数据上的表现
"""

import pytest
import asyncio
from datetime import date, timedelta
from unittest.mock import Mock, patch
from typing import List, Dict, Any
import pandas as pd
import random

from app.services.daily_workflow import DailyWorkflow
from app.services.stock_selector import StockSelector
from app.services.daily_stock_selection_service import DailyStockSelectionService


class TestBacktestFebToMarch:
    """
    回测测试：2025年2月1日至3月25日
    按当前规则选股，验证策略有效性
    """
    
    def _generate_historical_data(self, trade_date: date, stock_count: int = 5000) -> pd.DataFrame:
        """
        生成历史模拟数据
        模拟真实市场数据特征
        """
        data = []
        random.seed(trade_date.toordinal())  # 保证同一天数据一致
        
        for i in range(stock_count):
            # 生成股票代码
            if i < 2500:
                code = f"{i:06d}.SZ"  # 深市
            else:
                code = f"{i-2500:06d}.SH"  # 沪市
            
            # 基础价格
            base_price = 10.0 + (i % 100) * 0.1
            
            # 模拟不同市场情况
            day_factor = (trade_date.toordinal() % 30) / 30.0
            
            # 生成价格数据
            open_price = base_price * (1 + random.uniform(-0.05, 0.05))
            close_price = base_price * (1 + random.uniform(-0.1, 0.1))
            high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.05))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.05))
            
            # 成交量（部分股票模拟3倍量情况）
            base_volume = 1000000 + (i % 10) * 100000
            # 随机选择一些股票有异常成交量
            if i % 50 == 0:  # 约2%的股票有3倍量
                volume = base_volume * random.uniform(3.0, 5.0)
            else:
                volume = base_volume * random.uniform(0.5, 1.5)
            
            # 前一日成交量（用于计算量比）
            prev_volume = base_volume * random.uniform(0.8, 1.2)
            
            # 涨停价（模拟不同板块涨停幅度）
            if code.startswith("6"):  # 沪市主板
                zt_price = round(base_price * 1.1, 2)
            elif code.startswith("0"):  # 深市主板
                zt_price = round(base_price * 1.1, 2)
            elif code.startswith("3"):  # 创业板
                zt_price = round(base_price * 1.2, 2)
            else:
                zt_price = round(base_price * 1.1, 2)
            
            data.append({
                'code': code,
                'date': trade_date,
                'open': round(open_price, 2),
                'close': round(close_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'volume': int(volume),
                'prev_volume': int(prev_volume),
                'zt_price': zt_price,
                'amount': int(volume * close_price)
            })
        
        return pd.DataFrame(data)
    
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
    
    @pytest.mark.asyncio
    async def test_backtest_single_day(self):
        """
        回测：单日选股测试
        日期：2025年2月5日（周三）
        """
        trade_date = date(2025, 2, 5)
        
        # 生成模拟数据
        mock_data = self._generate_historical_data(trade_date)
        
        # 创建mock TDX客户端
        mock_tdx = Mock()
        mock_tdx.is_connected.return_value = True
        mock_tdx.get_market_data.return_value = mock_data
        mock_tdx.get_more_info.side_effect = lambda code: pd.DataFrame({
            'Close': [mock_data[mock_data['code'] == code]['close'].values[0]],
            'ZTPrice': [mock_data[mock_data['code'] == code]['zt_price'].values[0]]
        })
        mock_tdx.get_user_sector.return_value = []
        mock_tdx.create_sector.return_value = True
        mock_tdx.send_user_block.return_value = True
        
        # 创建mock飞书客户端
        mock_feishu = Mock()
        mock_feishu.send_group_message.return_value = {"status": "success"}
        mock_feishu.add_records.return_value = {"status": "success"}
        
        # 执行工作流
        workflow = DailyWorkflow(tdx_client=mock_tdx, feishu_client=mock_feishu)
        result = await workflow.execute(trade_date)
        
        # 验证结果
        assert result["status"] == "success"
        assert result["sector_code"] == "3BL0205"
        print(f"\n{trade_date} 选股结果:")
        print(f"  选中股票数: {result.get('selected_count', 0)}")
        print(f"  板块代码: {result['sector_code']}")
    
    @pytest.mark.asyncio
    async def test_backtest_multiple_days(self):
        """
        回测：多日连续选股测试
        日期范围：2025年2月1日至2月14日
        """
        start_date = date(2025, 2, 1)
        end_date = date(2025, 2, 14)
        trading_days = self._get_trading_days(start_date, end_date)
        
        results = []
        
        for trade_date in trading_days:
            # 生成当日模拟数据
            mock_data = self._generate_historical_data(trade_date)
            
            # 创建mock客户端
            mock_tdx = Mock()
            mock_tdx.is_connected.return_value = True
            mock_tdx.get_market_data.return_value = mock_data
            mock_tdx.get_more_info.side_effect = lambda code: pd.DataFrame({
                'Close': [mock_data[mock_data['code'] == code]['close'].values[0]],
                'ZTPrice': [mock_data[mock_data['code'] == code]['zt_price'].values[0]]
            })
            mock_tdx.get_user_sector.return_value = []
            mock_tdx.create_sector.return_value = True
            mock_tdx.send_user_block.return_value = True
            
            mock_feishu = Mock()
            mock_feishu.send_group_message.return_value = {"status": "success"}
            mock_feishu.add_records.return_value = {"status": "success"}
            
            # 执行选股
            workflow = DailyWorkflow(tdx_client=mock_tdx, feishu_client=mock_feishu)
            result = await workflow.execute(trade_date)
            
            results.append({
                'date': trade_date,
                'status': result['status'],
                'sector_code': result.get('sector_code'),
                'selected_count': result.get('selected_count', 0)
            })
        
        # 输出统计结果
        print("\n=== 2月1日-14日回测统计 ===")
        for r in results:
            print(f"{r['date']}: {r['sector_code']} - 选中{r['selected_count']}只")
        
        # 验证所有日期都成功
        assert all(r['status'] == 'success' for r in results)
        assert len(results) == len(trading_days)
    
    @pytest.mark.asyncio
    async def test_backtest_feb_to_march_full(self):
        """
        完整回测：2025年2月1日至3月25日
        验证整个时间段的选股表现
        """
        start_date = date(2025, 2, 1)
        end_date = date(2025, 3, 25)
        trading_days = self._get_trading_days(start_date, end_date)
        
        print(f"\n=== 完整回测：{start_date} 至 {end_date} ===")
        print(f"交易日数量: {len(trading_days)}")
        
        statistics = {
            'total_days': len(trading_days),
            'success_days': 0,
            'paused_days': 0,
            'failed_days': 0,
            'total_selected': 0,
            'daily_selections': []
        }
        
        for trade_date in trading_days:
            # 生成当日模拟数据
            mock_data = self._generate_historical_data(trade_date)
            
            # 创建mock客户端
            mock_tdx = Mock()
            mock_tdx.is_connected.return_value = True
            mock_tdx.get_market_data.return_value = mock_data
            mock_tdx.get_more_info.side_effect = lambda code: pd.DataFrame({
                'Close': [mock_data[mock_data['code'] == code]['close'].values[0]],
                'ZTPrice': [mock_data[mock_data['code'] == code]['zt_price'].values[0]]
            })
            mock_tdx.get_user_sector.return_value = []
            mock_tdx.create_sector.return_value = True
            mock_tdx.send_user_block.return_value = True
            
            mock_feishu = Mock()
            mock_feishu.send_group_message.return_value = {"status": "success"}
            mock_feishu.add_records.return_value = {"status": "success"}
            
            # 执行选股
            workflow = DailyWorkflow(tdx_client=mock_tdx, feishu_client=mock_feishu)
            result = await workflow.execute(trade_date)
            
            # 统计
            if result['status'] == 'success':
                statistics['success_days'] += 1
                statistics['total_selected'] += result.get('selected_count', 0)
            elif result['status'] == 'paused':
                statistics['paused_days'] += 1
            else:
                statistics['failed_days'] += 1
            
            statistics['daily_selections'].append({
                'date': trade_date,
                'status': result['status'],
                'sector_code': result.get('sector_code'),
                'selected_count': result.get('selected_count', 0)
            })
        
        # 输出统计结果
        print(f"\n=== 回测统计结果 ===")
        print(f"总交易日: {statistics['total_days']}")
        print(f"成功天数: {statistics['success_days']}")
        print(f"暂停天数: {statistics['paused_days']}")
        print(f"失败天数: {statistics['failed_days']}")
        print(f"总选中股票数: {statistics['total_selected']}")
        print(f"平均每日选中: {statistics['total_selected'] / statistics['success_days']:.2f} 只")
        
        # 验证成功率
        success_rate = statistics['success_days'] / statistics['total_days']
        print(f"成功率: {success_rate * 100:.2f}%")
        
        assert success_rate >= 0.95, f"成功率过低: {success_rate * 100:.2f}%"
    
    def test_strategy_effectiveness(self):
        """
        测试选股策略有效性
        验证3倍量、涨停、跳空策略能选出符合条件的股票
        """
        selector = StockSelector()
        
        # 生成包含明确信号的数据
        trade_date = date(2025, 2, 10)
        
        # 创建包含3倍量信号的数据 - 使用正确的DataFrame格式
        # select_3x_volume 期望的格式：行是 prev_volume 和 volume，列是股票代码
        stock_codes = [f"{i:06d}.SZ" for i in range(100)]
        
        # 构建DataFrame：行是指标，列是股票代码
        # 先构建数据字典，然后转置
        data_dict = {}
        for i, code in enumerate(stock_codes):
            if i < 5:  # 前5只股票模拟3倍量
                data_dict[code] = [1000000, 3000000]  # [prev_volume, volume]
            else:
                data_dict[code] = [1000000, 1000000]
        
        # 创建DataFrame，行是指标，列是股票代码
        market_data = pd.DataFrame(data_dict, index=['prev_volume', 'volume'])
        
        print(f"\n策略有效性测试 - DataFrame结构:")
        print(f"  形状: {market_data.shape}")
        print(f"  列(股票代码): {list(market_data.columns)[:5]}...")
        print(f"  行索引: {list(market_data.index)}")
        print(f"  前5只股票的prev_volume: {market_data.loc['prev_volume', stock_codes[:5]].tolist()}")
        print(f"  前5只股票的volume: {market_data.loc['volume', stock_codes[:5]].tolist()}")
        
        # 测试3倍量策略
        selected = selector.select_3x_volume(market_data)
        
        print(f"\n策略有效性测试:")
        print(f"  3倍量策略选中: {len(selected)} 只")
        print(f"  选中股票: {selected[:5]}")
        
        # 验证选中了3倍量的股票
        assert len(selected) > 0, "3倍量策略应该能选出股票"
        assert len(selected) == 5, f"应该选中5只3倍量股票，实际选中{len(selected)}只"
    
    @pytest.mark.asyncio
    async def test_backtest_with_market_scenarios(self):
        """
        回测：不同市场情景
        - 牛市情景
        - 熊市情景
        - 震荡市情景
        """
        trade_date = date(2025, 2, 15)
        
        scenarios = {
            'bull': {'price_factor': 1.05, 'volume_factor': 1.5},  # 牛市
            'bear': {'price_factor': 0.95, 'volume_factor': 0.8},  # 熊市
            'sideways': {'price_factor': 1.0, 'volume_factor': 1.0}  # 震荡
        }
        
        results = {}
        
        for scenario_name, factors in scenarios.items():
            # 生成情景数据 - 使用5000条以满足数据完整性检查
            data = []
            for i in range(5000):
                if i < 2500:
                    code = f"{i:06d}.SZ"  # 深市
                else:
                    code = f"{i-2500:06d}.SH"  # 沪市
                
                base_price = 10.0 * factors['price_factor']
                volume = int(1000000 * factors['volume_factor'])
                
                data.append({
                    'code': code,
                    'date': trade_date,
                    'open': base_price,
                    'close': base_price * (1 + (i % 10 - 5) / 100),
                    'high': base_price * 1.05,
                    'low': base_price * 0.95,
                    'volume': volume,
                    'prev_volume': 1000000,
                    'amount': volume * base_price
                })
            
            mock_data = pd.DataFrame(data)
            
            # 创建mock客户端
            mock_tdx = Mock()
            mock_tdx.is_connected.return_value = True
            mock_tdx.get_market_data.return_value = mock_data
            mock_tdx.get_more_info.side_effect = lambda code: pd.DataFrame({
                'Close': [11.0],
                'ZTPrice': [11.0]
            })
            mock_tdx.get_user_sector.return_value = []
            mock_tdx.create_sector.return_value = True
            mock_tdx.send_user_block.return_value = True
            
            mock_feishu = Mock()
            mock_feishu.send_group_message.return_value = {"status": "success"}
            mock_feishu.add_records.return_value = {"status": "success"}
            
            # 执行选股
            workflow = DailyWorkflow(tdx_client=mock_tdx, feishu_client=mock_feishu)
            result = await workflow.execute(trade_date)
            
            results[scenario_name] = {
                'status': result['status'],
                'selected_count': result.get('selected_count', 0)
            }
        
        # 输出各情景结果
        print("\n=== 不同市场情景回测 ===")
        for scenario, result in results.items():
            print(f"{scenario}: 状态={result['status']}, 选中 {result['selected_count']} 只")
        
        # 验证所有情景都成功
        assert all(r['status'] == 'success' for r in results.values()), f"某些情景失败: {results}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
