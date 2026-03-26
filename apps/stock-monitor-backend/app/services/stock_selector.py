#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票选股器
TDD Step 2: 实现代码 (绿)
"""

import pandas as pd
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger


class StockSelector:
    """
    股票选股器
    
    支持以下选股策略:
    1. 三倍量: 当日成交量 >= 前一日成交量 × 3
    2. 涨停: 当日涨幅达到涨停阈值
    3. 缺口: 当日最低价 > 前一日最高价 (向上缺口)
    """
    
    # 涨停阈值配置
    LIMIT_UP_THRESHOLDS = {
        "SH": 9.8,   # 沪市主板
        "SZ": 9.8,   # 深市主板
        "CY": 19.8,  # 创业板
        "KC": 19.8,  # 科创板
        "BJ": 29.8,  # 北交所
    }
    
    # 新股上市天数限制
    NEW_STOCK_DAYS = 20
    
    def __init__(self):
        """初始化选股器"""
        pass
    
    def select_3x_volume(self, volume_data: pd.DataFrame) -> List[str]:
        """
        三倍量选股
        
        Args:
            volume_data: DataFrame，包含 prev_volume 和 volume 两行，列为股票代码
            
        Returns:
            List[str]: 选中的股票代码列表
        """
        selected = []
        
        for stock_code in volume_data.columns:
            try:
                prev_volume = volume_data.loc["prev_volume", stock_code]
                today_volume = volume_data.loc["volume", stock_code]
                
                # 排除成交量为0或负数的情况
                if prev_volume <= 0 or today_volume <= 0:
                    continue
                
                # 计算量比
                volume_ratio = today_volume / prev_volume
                
                # 量比 >= 3 选中
                if volume_ratio >= 3.0:
                    selected.append(stock_code)
                    
            except Exception as e:
                logger.warning(f"处理股票 {stock_code} 成交量数据时出错: {e}")
                continue
        
        return selected
    
    def check_limit_up(self, stock_data: Dict[str, Any]) -> bool:
        """
        检查是否涨停
        
        Args:
            stock_data: 股票数据，包含 market 和 change_percent
            
        Returns:
            bool: 是否涨停
        """
        market = stock_data.get("market", "SH")
        change_percent = stock_data.get("change_percent", 0)
        
        threshold = self.get_limit_up_threshold(market)
        
        return change_percent >= threshold
    
    def get_limit_up_threshold(self, market: str) -> float:
        """
        获取指定市场的涨停阈值
        
        Args:
            market: 市场代码 (SH, SZ, CY, KC, BJ)
            
        Returns:
            float: 涨停阈值
        """
        return self.LIMIT_UP_THRESHOLDS.get(market, 9.8)
    
    def check_upward_gap(self, price_data: Dict[str, Any]) -> bool:
        """
        检查是否有向上缺口
        
        Args:
            price_data: 价格数据，包含 prev_high 和 today_low
            
        Returns:
            bool: 是否有向上缺口
        """
        prev_high = price_data.get("prev_high", 0)
        today_low = price_data.get("today_low", 0)
        
        # 向上缺口: 当日最低价 > 前日最高价
        return today_low > prev_high
    
    def should_exclude_stock(self, stock_data: Dict[str, Any], reference_date: Optional[date] = None) -> bool:
        """
        判断是否应该排除该股票
        
        Args:
            stock_data: 股票数据
            reference_date: 参考日期，默认为今天
            
        Returns:
            bool: 是否应该排除
        """
        if reference_date is None:
            reference_date = date.today()
        
        # 1. 排除ST股票
        stock_name = stock_data.get("name", "")
        if "ST" in stock_name or "*ST" in stock_name:
            logger.debug(f"排除ST股票: {stock_data.get('code')}")
            return True
        
        # 2. 排除新股（上市<20天）
        list_date = stock_data.get("list_date")
        if list_date:
            if isinstance(list_date, str):
                try:
                    list_date = date.fromisoformat(list_date)
                except ValueError:
                    pass
            
            if isinstance(list_date, date):
                days_since_list = (reference_date - list_date).days
                if days_since_list < self.NEW_STOCK_DAYS:
                    logger.debug(f"排除新股: {stock_data.get('code')}，上市{days_since_list}天")
                    return True
        
        # 3. 排除停牌股票
        if stock_data.get("is_suspended", False):
            logger.debug(f"排除停牌股票: {stock_data.get('code')}")
            return True
        
        return False
    
    def select_3x_volume_and_limit_up(self, market_data, trade_date=None) -> List[str]:
        """
        三倍量 + 涨停 组合策略选股
        
        条件：
        1. 当日成交量 >= 前一日成交量 × 3
        2. 当日涨幅达到涨停阈值
        
        Args:
            market_data: DataFrame或字典，包含Volume, Close等数据
            trade_date: 交易日期，用于匹配数据
            
        Returns:
            List[str]: 选中的股票代码列表
        """
        selected = []
        
        # 处理通达信返回的字典格式
        if isinstance(market_data, dict):
            if 'Volume' not in market_data or 'Close' not in market_data:
                logger.warning("数据中缺少必要字段")
                return selected
            
            volume_df = market_data['Volume']
            close_df = market_data['Close']
            
            if len(volume_df) < 2:
                logger.warning(f"数据行数不足: {len(volume_df)}")
                return selected
            
            # 使用最后两行（最近两天）
            prev_volume_row = volume_df.iloc[-2]
            today_volume_row = volume_df.iloc[-1]
            prev_close_row = close_df.iloc[-2]
            today_close_row = close_df.iloc[-1]
            
            stock_codes = volume_df.columns
        else:
            # DataFrame格式（原始格式）
            stock_codes = market_data.columns
            prev_volume_row = market_data.loc["prev_volume"] if "prev_volume" in market_data.index else None
            today_volume_row = market_data.loc["volume"] if "volume" in market_data.index else None
            prev_close_row = market_data.loc["prev_close"] if "prev_close" in market_data.index else None
            today_close_row = market_data.loc["close"] if "close" in market_data.index else None
        
        for stock_code in stock_codes:
            try:
                # 获取成交量数据
                prev_volume = prev_volume_row[stock_code]
                today_volume = today_volume_row[stock_code]
                
                # 获取价格数据
                prev_close = prev_close_row[stock_code]
                today_close = today_close_row[stock_code]
                
                # 处理Series类型（如果有多行数据，取最后一个值）
                import pandas as pd
                if isinstance(prev_volume, pd.Series):
                    prev_volume = prev_volume.iloc[-1]
                if isinstance(today_volume, pd.Series):
                    today_volume = today_volume.iloc[-1]
                if isinstance(prev_close, pd.Series):
                    prev_close = prev_close.iloc[-1]
                if isinstance(today_close, pd.Series):
                    today_close = today_close.iloc[-1]
                
                # 转换为数值
                try:
                    prev_volume = float(prev_volume)
                    today_volume = float(today_volume)
                    prev_close = float(prev_close)
                    today_close = float(today_close)
                except (ValueError, TypeError):
                    continue
                
                # 排除无效数据
                if prev_volume <= 0 or today_volume <= 0 or prev_close <= 0:
                    continue
                
                # 条件1：三倍量
                volume_ratio = today_volume / prev_volume
                if volume_ratio < 3.0:
                    continue
                
                # 条件2：涨停
                # 计算涨幅
                change_percent = (today_close - prev_close) / prev_close * 100
                
                # 判断市场类型
                if ".SZ" in stock_code:
                    if stock_code.startswith("3"):
                        market = "CY"  # 创业板
                    else:
                        market = "SZ"  # 深市主板
                elif ".SH" in stock_code:
                    if stock_code.startswith("688"):
                        market = "KC"  # 科创板
                    else:
                        market = "SH"  # 沪市主板
                elif ".BJ" in stock_code:
                    market = "BJ"  # 北交所
                else:
                    market = "SH"
                
                threshold = self.get_limit_up_threshold(market)
                
                # 检查是否涨停
                is_limit_up = change_percent >= threshold
                
                # 同时满足两个条件
                if is_limit_up:
                    selected.append(stock_code)
                    logger.info(f"  3倍量+涨停选中: {stock_code}, 量比: {volume_ratio:.2f}, 涨幅: {change_percent:.2f}%")
                    
            except Exception as e:
                # 减少日志输出，只在调试时显示
                # logger.warning(f"处理股票 {stock_code} 组合策略时出错: {e}")
                continue
        
        return selected
    
    def select_stocks_by_strategy(self, 
                                  strategy: str, 
                                  market_data,
                                  stock_info: Optional[Dict[str, Dict]] = None,
                                  trade_date=None) -> List[str]:
        """
        根据策略选股
        
        Args:
            strategy: 策略名称 (3x_volume, limit_up, gap, 3x_volume_and_limit_up)
            market_data: 市场数据DataFrame或字典
            stock_info: 股票信息字典，用于排除规则
            trade_date: 交易日期
            
        Returns:
            List[str]: 选中的股票代码列表
        """
        if strategy == "3x_volume":
            return self.select_3x_volume(market_data)
        
        elif strategy == "3x_volume_and_limit_up":
            return self.select_3x_volume_and_limit_up(market_data, trade_date)
        
        elif strategy == "limit_up":
            selected = []
            # 处理字典格式
            if isinstance(market_data, dict):
                if 'Close' not in market_data:
                    return selected
                close_df = market_data['Close']
                stock_codes = close_df.columns
            else:
                stock_codes = market_data.columns
            
            for stock_code in stock_codes:
                try:
                    # 简化处理，从3倍量+涨停策略中获取数据
                    stock_data = {
                        "code": stock_code,
                        "market": "SH",  # 默认
                        "change_percent": 0
                    }
                    
                    # 应用排除规则
                    if stock_info and stock_code in stock_info:
                        if self.should_exclude_stock(stock_info[stock_code]):
                            continue
                    
                    if self.check_limit_up(stock_data):
                        selected.append(stock_code)
                        
                except Exception as e:
                    logger.warning(f"处理股票 {stock_code} 涨停数据时出错: {e}")
                    continue
            return selected
        
        elif strategy == "gap":
            selected = []
            # 处理字典格式
            if isinstance(market_data, dict):
                if 'High' not in market_data or 'Low' not in market_data:
                    return selected
                stock_codes = market_data['High'].columns
            else:
                stock_codes = market_data.columns
            
            for stock_code in stock_codes:
                try:
                    price_data = {
                        "prev_high": 0,
                        "today_low": 0
                    }
                    
                    if self.check_upward_gap(price_data):
                        selected.append(stock_code)
                        
                except Exception as e:
                    logger.warning(f"处理股票 {stock_code} 缺口数据时出错: {e}")
                    continue
            return selected
        
        else:
            logger.error(f"未知的选股策略: {strategy}")
            return []
