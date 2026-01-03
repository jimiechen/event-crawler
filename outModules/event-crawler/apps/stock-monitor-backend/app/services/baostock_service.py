#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Baostock数据服务 (作为Tushare的备用)
"""

import baostock as bs
import pandas as pd
import asyncio
import os
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from loguru import logger
from app.database import DatabaseManager
from app.repositories.stock_daily_repository import StockDailyRepository

class BaostockService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
        # Unset proxy to avoid connection issues
        for k in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
            if k in os.environ:
                logger.info(f"Removing proxy env var {k} for Baostock service")
                os.environ.pop(k)
                
        self.repository = StockDailyRepository(db_manager)

    async def check_connectivity(self) -> bool:
        """检查Baostock连接状态"""
        try:
            loop = asyncio.get_event_loop()
            def _check():
                lg = bs.login()
                success = lg.error_code == '0'
                bs.logout()
                return success
            return await loop.run_in_executor(None, _check)
        except Exception as e:
            logger.warning(f"Baostock connectivity check failed: {e}")
            return False

    def _normalize_code_to_baostock(self, code: str) -> str:
        """
        转换代码格式为Baostock格式
        例如: 600000 -> sh.600000, 000001 -> sz.000001
        """
        # Remove existing suffixes first
        clean_code = code.split('.')[0]
        
        if clean_code.startswith(('60', '68')):
            return f"sh.{clean_code}"
        elif clean_code.startswith(('00', '30')):
            return f"sz.{clean_code}"
        elif clean_code.startswith(('43', '83', '87')):
            return f"bj.{clean_code}"
        return f"sh.{clean_code}" # Default fallback

    def _normalize_code_from_baostock(self, bs_code: str) -> str:
        """
        将Baostock代码转换为内部格式
        sh.600000 -> 600000
        """
        if "." in bs_code:
            return bs_code.split(".")[1]
        return bs_code

    async def fetch_daily_data(self, code: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        从Baostock获取日线数据
        """
        logger.info(f"Using Baostock to fetch {code} from {start_date} to {end_date}")
        
        try:
            # Run in executor to avoid blocking async loop
            loop = asyncio.get_event_loop()
            
            def _fetch():
                # 1. Login
                lg = bs.login()
                if lg.error_code != '0':
                    logger.error(f"Baostock login failed: {lg.error_msg}")
                    return []
                
                try:
                    bs_code = self._normalize_code_to_baostock(code)
                    
                    # 2. Query
                    # frequency="d", adjustflag="3" (默认不复权，为了保持原始数据一致性，或者我们可以用1后复权？Tushare通常存不复权+复权因子)
                    # 这里先用不复权，因为我们的模型存的是 open/close 等原始值 + adj_factor
                    # 但是Baostock似乎不直接返回adj_factor，而是通过 adjustflag=2 (前复权) or 1 (后复权) 直接返回复权后的价格
                    # 既然TushareService是存原始价格+adj_factor，我们这里尽量保持一致
                    # 只要我们能拿到原始价格就行。
                    
                    fields = "date,code,open,high,low,close,volume,amount,pctChg"
                    rs = bs.query_history_k_data_plus(
                        bs_code,
                        fields,
                        start_date=start_date,
                        end_date=end_date,
                        frequency="d",
                        adjustflag="3" 
                    )
                    
                    if rs.error_code != '0':
                        logger.error(f"Baostock query failed: {rs.error_msg}")
                        return []
                    
                    data_list = []
                    while (rs.error_code == '0') & rs.next():
                        data_list.append(rs.get_row_data())
                    
                    return pd.DataFrame(data_list, columns=rs.fields)
                    
                finally:
                    bs.logout()

            df = await loop.run_in_executor(None, _fetch)
            
            if df is None or df.empty:
                return []
                
            # Convert to list of dicts matching our schema
            result = []
            for _, row in df.iterrows():
                try:
                    # Baostock returns strings, need conversion
                    item = {
                        "code": self._normalize_code_from_baostock(row['code']),
                        "trade_date": datetime.strptime(row['date'], "%Y-%m-%d").date(),
                        "open": float(row['open']) if row['open'] else 0.0,
                        "close": float(row['close']) if row['close'] else 0.0,
                        "high": float(row['high']) if row['high'] else 0.0,
                        "low": float(row['low']) if row['low'] else 0.0,
                        "vol": float(row['volume']) if row['volume'] else 0.0, # Baostock volume is in shares? Need to check. Tushare is in lots (100 shares)? 
                        # Tushare vol: 手 (100股). Baostock volume: 股?
                        # Checked Docs: volume:成交量（单位：股）
                        # So we need to divide by 100 to match Tushare if Tushare uses lots.
                        # Wait, Tushare doc says: vol: 成交量 （手）
                        # So Baostock / 100 = Tushare vol.
                        
                        "amount": float(row['amount']) if row['amount'] else 0.0, # amount: 成交额（单位：人民币元）
                        "adj_factor": 1.0 # Default to 1.0 as we don't fetch it easily from basic k_data
                    }
                    
                    # Adjust volume to lots (手)
                    item['vol'] = int(item['vol'] / 100.0)
                    
                    # Adjust amount to thousands (千元)
                    item['amount'] = item['amount'] / 1000.0
                    
                    result.append(item)
                except ValueError as e:
                    logger.warning(f"Error parsing baostock row: {row} - {e}")
                    continue
                    
            return result

        except Exception as e:
            logger.error(f"Baostock fetch error: {e}")
            return []

    async def sync_daily_data(self, code: str, mode: str = "incremental") -> int:
        """
        同步单个股票数据
        """
        try:
            # Determine date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            if mode == "incremental":
                last_date = await self.repository.get_latest_date(code)
                if last_date:
                    start_date = last_date + timedelta(days=1)
                    if start_date > date.today():
                        return 0
            
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")
            
            data_list = await self.fetch_daily_data(code, start_str, end_str)
            
            if data_list:
                count = await self.repository.batch_save_daily_data(data_list)
                logger.info(f"Baostock: Saved {count} records for {code}")
                return count
            
            return 0
            
        except Exception as e:
            logger.error(f"Baostock sync failed for {code}: {e}")
            return 0
