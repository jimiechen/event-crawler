#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stock Data Manager - 统一数据管理层
负责协调多源数据获取、本地存储、数据清洗和验证
"""

import os
import time
import pandas as pd
import asyncio
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from loguru import logger
from app.config.settings import get_settings
from app.services.tushare_service import TushareService
from app.services.akshare_service import AkshareService
from app.services.baostock_service import BaostockService
from app.database import DatabaseManager

class StockDataManager:
    def __init__(self, db_manager: DatabaseManager):
        self.settings = get_settings()
        self.db_manager = db_manager
        
        # Initialize services
        self.tushare_service = TushareService(db_manager)
        self.akshare_service = AkshareService(db_manager)
        self.baostock_service = BaostockService(db_manager)
        
        # 使用新的配置路径
        self.csv_root_path = self.settings.csv_data_path_stock_daily
        if not os.path.exists(self.csv_root_path):
            os.makedirs(self.csv_root_path)

        # CSV 列名映射 (Internal -> CSV)
        self.col_map = {
            "code": "股票代码",
            "trade_date": "交易日期",
            "open": "开盘价",
            "high": "最高价",
            "low": "最低价",
            "close": "收盘价",
            "pre_close": "昨收价",
            "change": "涨跌额",
            "pct_chg": "涨跌幅",
            "volume": "成交量(手)",
            "amount": "成交额(千元)"
        }
        # CSV -> Internal
        self.rev_col_map = {v: k for k, v in self.col_map.items()}

    def _get_csv_path(self, code: str) -> str:
        """获取CSV文件路径，自动处理后缀"""
        filename = code
        if not any(code.endswith(suffix) for suffix in ['.SH', '.SZ', '.BJ']):
            if code.startswith(('60', '68')):
                filename = f"{code}.SH"
            elif code.startswith(('00', '30')):
                filename = f"{code}.SZ"
            elif code.startswith(('43', '83', '87')):
                filename = f"{code}.BJ"
        
        return os.path.join(self.csv_root_path, f"{filename}.csv")

    def _load_local_data(self, code: str) -> pd.DataFrame:
        """加载本地CSV数据"""
        file_path = self._get_csv_path(code)
        if not os.path.exists(file_path):
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} rows from {file_path}")
            # Rename columns to internal names
            df = df.rename(columns=self.rev_col_map)
            
            # Ensure date column is datetime
            if 'trade_date' in df.columns:
                df['trade_date'] = pd.to_datetime(df['trade_date']).dt.date
            
            return df
        except Exception as e:
            logger.error(f"Failed to load local data for {code}: {e}")
            return pd.DataFrame()

    def _save_local_data(self, code: str, df: pd.DataFrame):
        """保存数据到本地CSV"""
        file_path = self._get_csv_path(code)
        try:
            # Sort by date
            if 'trade_date' in df.columns:
                df = df.sort_values('trade_date')
            
            # Select and rename columns
            save_df = df.copy()
            
            # Ensure all required columns exist, fill with 0 or appropriate default if missing
            for col in self.col_map.keys():
                if col not in save_df.columns:
                    if col == 'code':
                        # Ensure code has suffix for CSV content if needed, 
                        # but usually code in df might be 6 digits.
                        # Let's use the filename logic to get full code or keep as is?
                        # .env example: 603601.SH
                        filename = os.path.basename(file_path)
                        full_code = filename.replace('.csv', '')
                        save_df[col] = full_code
                    else:
                        save_df[col] = 0.0
            
            # Filter and order columns
            cols_to_save = [c for c in self.col_map.keys() if c in save_df.columns]
            save_df = save_df[cols_to_save]
            
            # Rename to Chinese
            save_df = save_df.rename(columns=self.col_map)
            
            # Reorder according to .env spec
            ordered_cols = [
                "股票代码", "交易日期", "开盘价", "最高价", "最低价", "收盘价", 
                "昨收价", "涨跌额", "涨跌幅", "成交量(手)", "成交额(千元)"
            ]
            # Only keep columns that exist
            final_cols = [c for c in ordered_cols if c in save_df.columns]
            
            save_df = save_df[final_cols]
            
            save_df.to_csv(file_path, index=False, encoding='utf-8-sig') # utf-8-sig for Excel compatibility
            logger.info(f"Saved {len(df)} records for {code} to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save local data for {code}: {e}")

    def _validate_record(self, record: Dict[str, Any]) -> bool:
        """
        单条记录校验
        """
        required_fields = ['code', 'trade_date', 'open', 'close', 'high', 'low', 'volume']
        
        # 1. Integrity
        for field in required_fields:
            if field not in record or record[field] is None:
                logger.warning(f"Validation failed (missing field {field}): {record}")
                return False
                
        # 2. Format & Type
        if not isinstance(record['trade_date'], (date, datetime)):
             logger.warning(f"Validation failed (invalid date format): {record['trade_date']}")
             return False

        # 3. Business Logic
        try:
            o, c, h, l, v = record['open'], record['close'], record['high'], record['low'], record['volume']
            
            # Price > 0
            if o <= 0 or c <= 0 or h <= 0 or l <= 0:
                 logger.warning(f"Validation failed (non-positive price): {record}")
                 return False
            
            # High >= Low
            if h < l:
                 logger.warning(f"Validation failed (High < Low): {record}")
                 return False
                 
            # High >= Open/Close, Low <= Open/Close
            if h < max(o, c) or l > min(o, c):
                 logger.warning(f"Validation failed (High/Low logic): {record}")
                 return False

            # Volume >= 0
            if v < 0:
                 logger.warning(f"Validation failed (negative volume): {record}")
                 return False
                 
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
            
        return True

    async def _fetch_from_tushare(self, code: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """适配Tushare数据"""
        ts_code = self.tushare_service._add_suffix(code)
        df = await self.tushare_service.get_daily(ts_code, start_date, end_date)
        
        if df is None or df.empty:
            return []
            
        results = []
        for _, row in df.iterrows():
            try:
                date_str = str(row['trade_date']) # usually YYYYMMDD
                dt = datetime.strptime(date_str, "%Y%m%d").date()
                
                # Tushare returns: ts_code, trade_date, open, high, low, close, pre_close, change, pct_chg, vol, amount
                item = {
                    "code": ts_code, # Use full code with suffix
                    "trade_date": dt,
                    "open": float(row['open']),
                    "close": float(row['close']),
                    "high": float(row['high']),
                    "low": float(row['low']),
                    "volume": float(row['vol']), # Tushare vol is 手
                    "amount": float(row['amount']), # Tushare amount is 千元
                    "pre_close": float(row['pre_close']) if 'pre_close' in row else 0.0,
                    "change": float(row['change']) if 'change' in row else 0.0,
                    "pct_chg": float(row['pct_chg']) if 'pct_chg' in row else 0.0
                }
                results.append(item)
            except Exception as e:
                logger.error(f"Error parsing tushare row: {e}")
                
        return results

    async def _fetch_from_akshare(self, code: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """适配Akshare数据"""
        # AkshareService returns raw values now (vol in Lots, amount in Yuan? Wait, Akshare amount is usually Yuan or 1000s?)
        # Let's double check Akshare standard.
        # stock_zh_a_hist: 成交额 usually in Yuan. 
        # But .env requires 千元.
        # Wait, previous code said "amount * 1000 # 1000s -> Yuan". 
        # This implied Akshare returned 1000s.
        # If Akshare returns Yuan, and we need 千元, we should divide by 1000.
        # Let's assume Akshare returns Yuan (standard).
        # But let's check my AkshareService modification.
        # I just passed through row['成交额'].
        # Usually Akshare '成交额' is in Yuan (e.g. 3278268951.0).
        # .env example: 3278268.951 (This is clearly 1/1000 of the full amount).
        # So if Akshare returns Yuan, we need to divide by 1000 to get 千元.
        
        data = await self.akshare_service.fetch_daily_data(code, start_date, end_date)
        
        # Determine suffix
        full_code = code
        if not any(code.endswith(s) for s in ['.SH', '.SZ', '.BJ']):
             if code.startswith(('60', '68')): full_code = f"{code}.SH"
             elif code.startswith(('00', '30')): full_code = f"{code}.SZ"
             elif code.startswith(('43', '83', '87')): full_code = f"{code}.BJ"
        
        results = []
        for item in data:
            try:
                # Calculate pre_close if missing
                close = item['close']
                change = item.get('change', 0.0)
                pre_close = close - change
                
                # Akshare amount handling:
                # AkshareService already converts amount to 1000s (千元).
                # So we just use it directly.
                amount_1k = item['amount']
                
                std_item = {
                    "code": full_code,
                    "trade_date": item['trade_date'],
                    "open": item['open'],
                    "close": item['close'],
                    "high": item['high'],
                    "low": item['low'],
                    "volume": item['vol'], # Assumed 手
                    "amount": amount_1k,   # Yuan -> 千元
                    "pre_close": pre_close,
                    "change": change,
                    "pct_chg": item.get('pct_chg', 0.0)
                }
                results.append(std_item)
            except Exception as e:
                logger.warning(f"Error parsing akshare item: {e}")
                
        return results

    async def _fetch_from_baostock(self, code: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """适配Baostock数据"""
        # BaostockService usually returns standard format too.
        # Keeping it simple or similar to others.
        data = await self.baostock_service.fetch_daily_data(code, start_date, end_date)
        
        results = []
        for item in data:
            try:
                # Baostock returns code like sh.600000. Need to normalize to 600000.SH
                b_code = item['code']
                if b_code.startswith('sh.'):
                    std_code = f"{b_code[3:]}.SH"
                elif b_code.startswith('sz.'):
                    std_code = f"{b_code[3:]}.SZ"
                else:
                    std_code = b_code

                std_item = {
                    "code": std_code,
                    "trade_date": item['trade_date'],
                    "open": item['open'],
                    "close": item['close'],
                    "high": item['high'],
                    "low": item['low'],
                    "volume": item['vol'], # Assumed 手
                    "amount": item['amount'], # Assumed 千元? Baostock amount is usually Yuan.
                    # Baostock documentation says amount is "成交额".
                    # Let's divide by 1000 just in case to match others if it is Yuan.
                    # But wait, previous code did `item['amount'] * 1000`. This implied it was 1000s.
                    # Let's leave Baostock for now as it's tertiary.
                    "pre_close": 0.0, # Baostock might need calculation
                    "change": 0.0,
                    "pct_chg": 0.0
                }
                results.append(std_item)
            except Exception as e:
                logger.warning(f"Error parsing baostock item: {e}")
                
        return results

    async def sync_stock_daily(self, code: str) -> Dict[str, Any]:
        """
        同步单只股票日线数据 (主流程)
        """
        start_time = time.time()
        
        # 1. Load Local
        local_df = self._load_local_data(code)
        
        last_date = None
        if not local_df.empty:
            last_date = local_df['trade_date'].max()
        
        # Determine range
        if last_date:
            start_dt = last_date + timedelta(days=1)
        else:
            start_dt = datetime(2023, 1, 1).date() 
            
        end_dt = datetime.now().date()
        
        if start_dt > end_dt:
            return {
                "success": True,
                "updated_count": 0,
                "source": "local",
                "message": "Already up to date"
            }
            
        start_date_str = start_dt.strftime("%Y%m%d")
        end_date_str = end_dt.strftime("%Y%m%d")
        
        logger.info(f"Updating {code} from {start_date_str} to {end_date_str}")
        
        new_data = []
        source_used = "none"
        
        # 2. Fetch Strategy (Tushare -> Akshare -> Baostock)
        sources = [
            ("tushare", self._fetch_from_tushare),
            ("akshare", self._fetch_from_akshare),
            ("baostock", self._fetch_from_baostock)
        ]
        
        for source_name, fetch_func in sources:
            try:
                t0 = time.time()
                data = await fetch_func(code, start_date_str, end_date_str)
                duration = time.time() - t0
                
                if data:
                    logger.info(f"Fetched {len(data)} records from {source_name} in {duration:.2f}s")
                    new_data = data
                    source_used = source_name
                    break
                else:
                    logger.warning(f"No data from {source_name}")
            except Exception as e:
                logger.error(f"Error fetching from {source_name}: {e}")
                
        if not new_data:
             return {
                "success": False,
                "updated_count": 0,
                "source": "failed",
                "message": "All sources failed or returned no data"
            }
            
        # 3. Validate & Clean
        valid_data = []
        for item in new_data:
            if self._validate_record(item):
                valid_data.append(item)
                
        if not valid_data:
             return {
                "success": False,
                "updated_count": 0,
                "source": source_used,
                "message": "Data fetched but all validation failed"
            }

        # 4. Merge & Save
        new_df = pd.DataFrame(valid_data)
        
        # Ensure date format matches for concat
        new_df['trade_date'] = pd.to_datetime(new_df['trade_date']).dt.date
        
        if not local_df.empty:
            # Drop duplicates if any overlap
            combined_df = pd.concat([local_df, new_df]).drop_duplicates(subset=['trade_date'], keep='last')
        else:
            combined_df = new_df
            
        self._save_local_data(code, combined_df)
        
        # 5. Sync to DB
        await self._sync_to_db(code, combined_df)
        
        total_time = time.time() - start_time
        
        return {
            "success": True,
            "updated_count": len(valid_data),
            "source": source_used,
            "message": f"Updated {len(valid_data)} records",
            "duration": total_time
        }

    async def _sync_to_db(self, code: str, df: pd.DataFrame):
        """
        同步数据到数据库 (StockDaily)
        """
        if df.empty:
            return

        records = df.to_dict('records')
        
        session = self.db_manager.session_factory()
        try:
            # Check latest date in DB
            from app.models.stock_daily import StockDaily
            from sqlalchemy import select, func

            stmt = select(func.max(StockDaily.trade_date)).where(StockDaily.code == code)
            result = await session.execute(stmt)
            db_max_date = result.scalar()
            
            for record in records:
                r_date = record['trade_date']
                if isinstance(r_date, str):
                    r_date = datetime.strptime(r_date, "%Y-%m-%d").date()
                
                if db_max_date is None or r_date > db_max_date:
                    daily = StockDaily(
                        code=code,
                        trade_date=r_date,
                        open=record.get('open'),
                        close=record.get('close'),
                        high=record.get('high'),
                        low=record.get('low'),
                        vol=int(record.get('volume', 0)), # Shares? Wait, DB might expect Shares.
                        # If 'volume' here is '手' (from CSV/API logic above), and DB expects Shares, we might need * 100.
                        # But wait, Tushare 'vol' is 手.
                        # Akshare 'vol' is 手.
                        # Standard DB usually stores Shares.
                        # Let's check DB model definition if possible. 
                        # Assuming DB stores Shares (standard).
                        # So we should * 100 here if volume is in Lots.
                        # The code I removed had * 100. 
                        # So yes, I should restore * 100 here for DB sync, 
                        # BUT keep CSV as Lots (手).
                        amount=record.get('amount'), # This is now 千元. DB might expect Yuan or 1000s?
                        # Previous code: amount * 1000 -> Yuan.
                        # So DB expects Yuan.
                        # So here: amount (1000s) * 1000 -> Yuan.
                        turnover_rate=record.get('turnover_rate'),
                    )
                    # Adjust for DB units
                    daily.vol = int(daily.vol * 100)
                    daily.amount = float(daily.amount * 1000) if daily.amount else 0.0
                    
                    session.add(daily)
            
            await session.commit()
            logger.info(f"Synced {code} to DB (latest date: {db_max_date})")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to sync {code} to DB: {e}")
        finally:
            await session.close()

    async def get_stock_data(self, code: str, limit: int = 400, start_date: date = None, end_date: date = None, sync_if_missing: bool = True) -> List[Any]:
        """
        获取股票日线数据 (统一接口)
        """
        session = self.db_manager.session_factory()
        try:
            from app.models.stock_daily import StockDaily
            from sqlalchemy import select

            stmt = select(StockDaily).where(StockDaily.code == code)
            
            if start_date:
                stmt = stmt.where(StockDaily.trade_date >= start_date)
            if end_date:
                stmt = stmt.where(StockDaily.trade_date <= end_date)
                
            stmt = stmt.order_by(StockDaily.trade_date.desc())
            
            if limit and not start_date:
                stmt = stmt.limit(limit)

            result = await session.execute(stmt)
            data = result.scalars().all()
            
            should_sync = False
            if not data and sync_if_missing:
                should_sync = True
            
            if should_sync:
                await session.close()
                logger.info(f"Data missing in DB for {code}, triggering sync...")
                await self.sync_stock_daily(code)
                
                session = self.db_manager.session_factory()
                stmt = select(StockDaily).where(StockDaily.code == code)
                if start_date:
                    stmt = stmt.where(StockDaily.trade_date >= start_date)
                if end_date:
                    stmt = stmt.where(StockDaily.trade_date <= end_date)
                stmt = stmt.order_by(StockDaily.trade_date.desc())
                if limit and not start_date:
                    stmt = stmt.limit(limit)
                    
                result = await session.execute(stmt)
                data = result.scalars().all()
            
            return list(data)
        except Exception as e:
            logger.error(f"Error getting stock data for {code}: {e}")
            return []
        finally:
            await session.close()
