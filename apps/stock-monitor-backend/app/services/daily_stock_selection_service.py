#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日板块创建与选股服务
TDD Step 2: 实现代码 (绿)
"""

import pandas as pd
from datetime import date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger

from app.services.tdx_data_sync_checker import TdxDataSyncChecker
from app.services.stock_selector import StockSelector


class DailyStockSelectionService:
    """
    每日板块创建与选股服务
    
    功能:
    1. 生成日期命名的板块代码和名称
    2. 执行盘后数据同步检查
    3. 执行选股策略 (三倍量、涨停、缺口)
    4. 创建通达信板块并写入股票
    """
    
    # 板块命名规则
    SECTOR_CODE_PREFIX = "3BL"
    SECTOR_NAME_PREFIX = "3倍量"
    
    def __init__(self, tdx_client=None):
        """
        初始化服务
        
        Args:
            tdx_client: 通达信客户端实例
        """
        self.tdx_client = tdx_client
        self.data_sync_checker = TdxDataSyncChecker(tdx_client=tdx_client)
        self.stock_selector = StockSelector()
    
    def _get_all_stock_codes(self) -> List[str]:
        """
        获取所有A股股票代码
        
        Returns:
            List[str]: 股票代码列表
        """
        stock_list = []
        
        # 深市主板 (000001-004999)
        for i in range(1, 5000):
            stock_list.append(f"{i:06d}.SZ")
        
        # 深市中小板 (002001-002999)
        for i in range(2001, 3000):
            stock_list.append(f"{i:06d}.SZ")
        
        # 深市创业板 (300001-301999)
        for i in range(300001, 302000):
            stock_list.append(f"{i:06d}.SZ")
        
        # 沪市主板 (600000-604999)
        for i in range(600000, 605000):
            stock_list.append(f"{i:06d}.SH")
        
        # 沪市科创板 (688001-689999)
        for i in range(688001, 690000):
            stock_list.append(f"{i:06d}.SH")
        
        return stock_list
    
    def generate_sector_names(self, trade_date: date) -> Tuple[str, str]:
        """
        生成板块代码和名称
        
        Args:
            trade_date: 交易日期
            
        Returns:
            Tuple[str, str]: (板块代码, 板块名称)
            例如: ("3BL0325", "3倍量20260325")
        """
        # 板块代码: 3BL{MMDD}
        date_str = trade_date.strftime("%m%d")
        sector_code = f"{self.SECTOR_CODE_PREFIX}{date_str}"
        
        # 板块名称: 3倍量{YYYYMMDD}
        full_date_str = trade_date.strftime("%Y%m%d")
        sector_name = f"{self.SECTOR_NAME_PREFIX}{full_date_str}"
        
        return sector_code, sector_name
    
    def create_sector(self, sector_code: str, sector_name: str) -> bool:
        """
        创建通达信板块
        
        Args:
            sector_code: 板块代码
            sector_name: 板块名称
            
        Returns:
            bool: 是否创建成功
        """
        try:
            if self.tdx_client is None:
                logger.error("通达信客户端未初始化")
                return False
            
            # 调用通达信API创建板块
            result = self.tdx_client.create_sector(
                block_code=sector_code,
                block_name=sector_name
            )
            
            if result:
                logger.info(f"成功创建板块: {sector_name} ({sector_code})")
                return True
            else:
                logger.error(f"创建板块失败: {sector_name} ({sector_code})")
                return False
                
        except Exception as e:
            logger.error(f"创建板块时出错: {e}")
            return False
    
    def send_stocks_to_sector(self, sector_code: str, stocks: List[str]) -> bool:
        """
        将股票发送到板块
        
        Args:
            sector_code: 板块代码
            stocks: 股票代码列表
            
        Returns:
            bool: 是否发送成功
        """
        try:
            if self.tdx_client is None:
                logger.error("通达信客户端未初始化")
                return False
            
            if not stocks:
                logger.warning(f"股票列表为空，清空板块: {sector_code}")
            
            # 调用通达信API发送股票到板块
            result = self.tdx_client.send_user_block(
                block_code=sector_code,
                stocks=stocks
            )
            
            if result:
                logger.info(f"成功发送 {len(stocks)} 只股票到板块: {sector_code}")
                return True
            else:
                logger.error(f"发送股票到板块失败: {sector_code}")
                return False
                
        except Exception as e:
            logger.error(f"发送股票到板块时出错: {e}")
            return False
    
    def execute_daily_selection(self, 
                               trade_date: date,
                               strategies: List[str] = None) -> Dict[str, Any]:
        """
        执行每日选股
        
        Args:
            trade_date: 交易日期
            strategies: 选股策略列表，默认为 ["3x_volume_and_limit_up"]
            
        Returns:
            Dict: {
                "status": "success" | "paused" | "failed",
                "sector_code": str,
                "sector_name": str,
                "selected_count": int,
                "strategies": Dict[str, List[str]],
                "reason": str (如果失败)
            }
        """
        if strategies is None:
            strategies = ["3x_volume_and_limit_up"]
        
        logger.info(f"开始执行每日选股: {trade_date}, 策略: {strategies}")
        
        # Step 1: 盘后数据同步检查
        logger.info("Step 1: 执行盘后数据同步检查")
        sync_check = self.data_sync_checker.check_daily_data_sync(trade_date)
        
        if sync_check["status"] != "success":
            message = f"数据同步检查失败: {sync_check['message']}"
            logger.error(message)
            return {
                "status": "paused",
                "sector_code": None,
                "sector_name": None,
                "selected_count": 0,
                "strategies": {},
                "reason": "data_sync_failed"
            }
        
        logger.info("数据同步检查通过")
        
        # Step 2: 生成板块名称
        logger.info("Step 2: 生成板块名称")
        sector_code, sector_name = self.generate_sector_names(trade_date)
        logger.info(f"板块代码: {sector_code}, 板块名称: {sector_name}")
        
        # Step 3: 获取市场数据
        logger.info("Step 3: 获取市场数据")
        try:
            if self.tdx_client is None:
                raise ValueError("通达信客户端未初始化")
            
            # 生成全量股票列表
            all_stocks = self._get_all_stock_codes()
            logger.info(f"获取 {len(all_stocks)} 只股票的数据")
            
            # 获取市场数据（2天，用于计算量比）
            start_date = trade_date - timedelta(days=5)
            end_date = trade_date + timedelta(days=1)
            
            market_data = self.tdx_client.get_market_data(
                field_list=['Volume', 'Close', 'Open', 'High', 'Low'],
                stock_list=all_stocks,
                period='1d',
                start_time=start_date.strftime('%Y%m%d'),
                end_time=end_date.strftime('%Y%m%d'),
                dividend_type='front'
            )
            
            # 检查数据是否为空
            if market_data is None:
                raise ValueError("获取市场数据失败")
            
            # 处理字典类型（通达信返回格式）
            if isinstance(market_data, dict):
                if not market_data or 'Volume' not in market_data:
                    raise ValueError("获取市场数据失败")
            elif isinstance(market_data, pd.DataFrame):
                if market_data.empty:
                    raise ValueError("获取市场数据失败")
            elif not market_data:
                raise ValueError("获取市场数据失败")
                
        except Exception as e:
            logger.error(f"获取市场数据时出错: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "failed",
                "sector_code": sector_code,
                "sector_name": sector_name,
                "selected_count": 0,
                "strategies": {},
                "reason": f"获取市场数据失败: {e}"
            }
        
        # Step 4: 执行选股策略
        logger.info("Step 4: 执行选股策略")
        strategy_results = {}
        all_selected_stocks = set()
        
        for strategy in strategies:
            logger.info(f"执行策略: {strategy}")
            try:
                selected = self.stock_selector.select_stocks_by_strategy(
                    strategy=strategy,
                    market_data=market_data,
                    trade_date=trade_date
                )
                strategy_results[strategy] = selected
                all_selected_stocks.update(selected)
                logger.info(f"策略 {strategy} 选中 {len(selected)} 只股票")
                
            except Exception as e:
                logger.error(f"执行策略 {strategy} 时出错: {e}")
                import traceback
                traceback.print_exc()
                strategy_results[strategy] = []
        
        selected_stocks = list(all_selected_stocks)
        logger.info(f"总共选中 {len(selected_stocks)} 只股票")
        
        # Step 5: 创建板块
        logger.info("Step 5: 创建板块")
        if not self.create_sector(sector_code, sector_name):
            return {
                "status": "failed",
                "sector_code": sector_code,
                "sector_name": sector_name,
                "selected_count": len(selected_stocks),
                "strategies": strategy_results,
                "reason": "创建板块失败"
            }
        
        # Step 6: 发送股票到板块
        logger.info("Step 6: 发送股票到板块")
        if not self.send_stocks_to_sector(sector_code, selected_stocks):
            return {
                "status": "failed",
                "sector_code": sector_code,
                "sector_name": sector_name,
                "selected_count": len(selected_stocks),
                "strategies": strategy_results,
                "reason": "发送股票到板块失败"
            }
        
        # 所有步骤成功
        logger.info(f"每日选股执行成功: {sector_name} ({sector_code})，共 {len(selected_stocks)} 只股票")
        return {
            "status": "success",
            "sector_code": sector_code,
            "sector_name": sector_name,
            "selected_count": len(selected_stocks),
            "strategies": strategy_results
        }
