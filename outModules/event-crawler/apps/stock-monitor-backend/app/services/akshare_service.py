#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AkShare数据服务 (作为备用数据源)
"""

try:
    import akshare as ak
except ImportError:
    ak = None

import pandas as pd
import asyncio
import os
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from loguru import logger
from app.database import DatabaseManager
from app.repositories.stock_daily_repository import StockDailyRepository

class AkshareService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
        # Unset proxy to avoid connection issues
        for k in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
            if k in os.environ:
                logger.info(f"Removing proxy env var {k} for AkShare service")
                os.environ.pop(k)
                
        self.repository = StockDailyRepository(db_manager)

    def _normalize_code(self, code: str) -> str:
        """
        标准化代码，AkShare通常直接使用6位代码，
        或者特定接口需要带市场标识?
        stock_zh_a_hist 只需要6位代码
        """
        if "." in code:
            return code.split(".")[0]
        return code

    async def fetch_daily_data(self, code: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        从AkShare获取日线数据
        接口: stock_zh_a_hist
        """
        if ak is None:
            logger.warning("AkShare is not installed. Skipping fetch.")
            return []

        logger.info(f"Using AkShare to fetch {code} from {start_date} to {end_date}")
        
        try:
            # AkShare is synchronous, run in executor
            loop = asyncio.get_event_loop()
            
            clean_code = self._normalize_code(code)
            # Format dates for AkShare (YYYYMMDD)
            start_date_str = start_date.replace("-", "")
            end_date_str = end_date.replace("-", "")
            
            def _fetch():
                try:
                    # adjust="" (不复权)
                    df = ak.stock_zh_a_hist(
                        symbol=clean_code, 
                        period="daily", 
                        start_date=start_date_str, 
                        end_date=end_date_str, 
                        adjust=""
                    )
                    return df
                except Exception as e:
                    logger.error(f"AkShare internal error for {code}: {e}")
                    return None

            df = await loop.run_in_executor(None, _fetch)
            
            if df is None or df.empty:
                return []
                
            # Columns: 日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, ...
            # Rename to match our schema
            
            result = []
            for _, row in df.iterrows():
                try:
                    # AkShare return dates as strings usually 'YYYY-MM-DD' or 'YYYYMMDD' depending on source
                    # stock_zh_a_hist returns 'YYYY-MM-DD' usually
                    trade_date = row['日期']
                    if isinstance(trade_date, str):
                        trade_date = datetime.strptime(trade_date, "%Y-%m-%d").date()
                    
                    item = {
                        "code": clean_code,
                        "trade_date": trade_date,
                        "open": float(row['开盘']),
                        "close": float(row['收盘']),
                        "high": float(row['最高']),
                        "low": float(row['最低']),
                        "vol": int(float(row['成交量'])), # Ensure int for BigInteger
                        "amount": float(row['成交额']), # Usually in Yuan
                        "adj_factor": 1.0
                    }
                    
                    # Tushare vol is in Lots (手)
                    # AkShare stock_zh_a_hist source is usually EastMoney.
                    # EastMoney web shows Volume in Lots (手).
                    # But let's be careful. If the number is huge, it might be shares.
                    # For 600000, daily vol is ~200,000 lots (20 million shares).
                    # If AkShare returns 200,000, it's lots. If 20,000,000, it's shares.
                    # Usually stock_zh_a_hist returns Lots.
                    
                    # Amount is usually in Yuan. Tushare uses thousands (千元).
                    # So we divide amount by 1000.
                    
                    item['amount'] = item['amount'] / 1000.0
                    
                    result.append(item)
                except Exception as e:
                    logger.warning(f"Error parsing AkShare row: {e}")
                    continue
                    
            return result

        except Exception as e:
            logger.error(f"AkShare fetch error: {e}")
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
                last_date = await self.repository.get_latest_date(self._normalize_code(code))
                if last_date:
                    start_date = last_date + timedelta(days=1)
                    if start_date > date.today():
                        return 0
            
            start_str = start_date.strftime("%Y%m%d") # AkShare format check? 
            # Wait, my fetch_daily_data handles conversion from YYYY-MM-DD to YYYYMMDD
            # So I should pass YYYY-MM-DD here to be consistent with my interface
            start_str_dash = start_date.strftime("%Y-%m-%d")
            end_str_dash = end_date.strftime("%Y-%m-%d")
            
            data_list = await self.fetch_daily_data(code, start_str_dash, end_str_dash)
            
            if data_list:
                count = await self.repository.batch_save_daily_data(data_list)
                logger.info(f"AkShare: Saved {count} records for {code}")
                return count
            
            return 0
            
        except Exception as e:
            logger.error(f"AkShare sync failed for {code}: {e}")
            return 0

    async def check_connectivity(self) -> bool:
        """
        Check if AkShare is working by fetching 1 row of a major index
        """
        try:
            loop = asyncio.get_event_loop()
            def _check():
                # Fetch SH Index (000001) for last 2 days
                end = datetime.now()
                start = end - timedelta(days=5)
                df = ak.stock_zh_index_daily(symbol="sh000001")
                return not df.empty
            
            return await loop.run_in_executor(None, _check)
        except Exception:
            return False
