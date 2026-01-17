#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据同步服务
"""

import os
import csv
import pandas as pd
import asyncio
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import DatabaseManager
from app.models.stock_daily import StockDaily
from app.repositories.stock_daily_repository import StockDailyRepository
from app.repositories.sync_log_repository import SyncLogRepository
from app.models.sync_log import SyncTaskType, SyncTaskStatus
from app.services.tushare_service import TushareService
from app.services.pathway_engine import PathwayVolumePriceEngine
from app.config.settings import get_settings


import akshare as ak
from app.services.pathway_engine import PathwayVolumePriceEngine

class StockSyncService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.tushare_service = TushareService(db_manager)
        self.repository = StockDailyRepository(db_manager)
        self.log_repository = SyncLogRepository(db_manager)
        self.pathway_engine = None
        self.pathway_enabled = get_settings().pathway_enabled
    
    def _get_csv_latest_date(self, code: str) -> Optional[date]:
        """
        获取CSV文件中的最新日期
        
        Args:
            code: 股票代码
        
        Returns:
            CSV文件中的最新日期，如果文件不存在或为空则返回None
        """
        csv_path = self._find_csv_path(code)
        if not csv_path or not os.path.exists(csv_path):
            return None
        
        try:
            df = pd.read_csv(csv_path)
            if df.empty or 'trade_date' not in df.columns:
                return None
            
            # Normalize date column
            df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d', errors='coerce').dt.date
            
            # 返回最新日期
            return df['trade_date'].max()
        except Exception as e:
            logger.warning(f"读取CSV最新日期失败 {code}: {e}")
            return None
    
    async def _get_db_latest_date(self, code: str) -> Optional[date]:
        """
        获取数据库中的最新日期
        
        Args:
            code: 股票代码
        
        Returns:
            数据库中的最新日期，如果没有数据则返回None
        """
        async with self.db_manager.get_session() as session:
            try:
                stmt = select(StockDaily.trade_date).where(
                    StockDaily.code == code
                ).order_by(StockDaily.trade_date.desc()).limit(1)
                
                result = await session.execute(stmt)
                row = result.scalar_one_or_none()
                
                return row.trade_date if row else None
            except Exception as e:
                logger.warning(f"读取数据库最新日期失败 {code}: {e}")
                return None
    
    def _detect_missing_dates(self, code: str, csv_latest: Optional[date], db_latest: Optional[date]) -> List[date]:
        """
        检测缺失的日期
        
        Args:
            code: 股票代码
            csv_latest: CSV文件中的最新日期
            db_latest: 数据库中的最新日期
        
        Returns:
            缺失的日期列表
        """
        # 确定起始日期（取较晚者）
        start_date = None
        if csv_latest and db_latest:
            start_date = max(csv_latest, db_latest)
        elif csv_latest:
            start_date = csv_latest
        elif db_latest:
            start_date = db_latest
        else:
            return []
        
        if not start_date:
            return []
        
        # 获取交易日历（简单实现：从start_date到今天的所有工作日）
        end_date = date.today()
        missing_dates = []
        
        current_date = start_date
        while current_date <= end_date:
            # 跳过周末
            if current_date.weekday() < 5:  # 周一到周五
                missing_dates.append(current_date)
            
            # 移动到下一天
            current_date += timedelta(days=1)
        
        return missing_dates
    
    def _append_to_csv(self, csv_path: str, new_data: pd.DataFrame) -> int:
        """
        追加数据到CSV文件
        
        Args:
            csv_path: CSV文件路径
            new_data: 新数据DataFrame
        
        Returns:
            追加的行数
        """
        try:
            # 读取现有数据
            if os.path.exists(csv_path):
                existing_df = pd.read_csv(csv_path)
            else:
                existing_df = pd.DataFrame()
            
            # 合并数据
            merged_df = pd.concat([existing_df, new_data], ignore_index=True)
            
            # 去重（按日期）
            if 'trade_date' in merged_df.columns:
                merged_df.drop_duplicates(subset=['trade_date'], keep='last', inplace=True)
            
            # 排序
            if 'trade_date' in merged_df.columns:
                merged_df.sort_values('trade_date', inplace=True)
            
            # 保存回CSV
            merged_df.to_csv(csv_path, index=False)
            
            return len(new_data)
        except Exception as e:
            logger.error(f"追加数据到CSV失败: {e}")
            return 0

    async def fetch_from_akshare(self, code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        从 Akshare 获取日线数据 (作为 Tushare 的降级方案)
        :param code: 股票代码 (如 000001)
        :param start_date: YYYYMMDD
        :param end_date: YYYYMMDD
        """
        try:
            symbol = code.split('.')[0]
            # Akshare 接受 YYYYMMDD
            def _fetch():
                return ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
            
            df = await asyncio.to_thread(_fetch)
            if df is not None and not df.empty:
                 # Standardize columns to Tushare format
                 # Akshare: 日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额...
                 df = df.rename(columns={
                     '日期': 'trade_date',
                     '开盘': 'open',
                     '收盘': 'close',
                     '最高': 'high',
                     '最低': 'low',
                     '成交量': 'vol',
                     '成交额': 'amount'
                 })
                 # Convert date format to YYYYMMDD to match Tushare
                 df['trade_date'] = pd.to_datetime(df['trade_date']).dt.strftime('%Y%m%d')
                 
                 # Convert amount from Yuan to Thousands (Tushare standard)
                 if 'amount' in df.columns:
                     df['amount'] = df['amount'] / 1000.0
                     
                 return df
            return None
        except Exception as e:
            logger.warning(f"Akshare fallback failed for {code}: {e}")
            return None

    async def get_batch_stocks(self, batch_id: int) -> List[str]:
        """获取批次下的股票代码列表. batch_id=-1 表示获取所有股票"""
        async with self.db_manager.get_session() as session:
            try:
                # 直接查询 wencai_stocks 表
                if batch_id == -1:
                    query = text("SELECT stock_code FROM wencai_stocks")
                    result = await session.execute(query)
                else:
                    query = text("SELECT stock_code FROM wencai_stocks WHERE crawl_batch_id = :batch_id")
                    result = await session.execute(query, {'batch_id': batch_id})
                return [row[0] for row in result.fetchall()]
            except Exception as e:
                logger.error(f"获取批次股票失败: {e}")
                return []

    def _find_csv_path(self, code: str) -> Optional[str]:
        """
        查找股票对应的CSV文件路径
        支持直接匹配和自动添加后缀 (.SH, .SZ, .BJ)
        """
        history_daily_path = get_settings().csv_data_path_stock_daily
        # 1. 尝试直接匹配
        path = os.path.join(history_daily_path, f"{code}.csv")
        if os.path.exists(path):
            return path
        
        # 2. 尝试添加后缀
        for suffix in [".SH", ".SZ", ".BJ"]:
            path = os.path.join(history_daily_path, f"{code}{suffix}.csv")
            if os.path.exists(path):
                return path
                
        return None

    def _normalize_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize DataFrame columns to standard English names.
        Handles Chinese, English, and Mixed columns.
        """
        cn_map = {
            '股票代码': 'code', '交易日期': 'trade_date', '开盘价': 'open',
            '最高价': 'high', '最低价': 'low', '收盘价': 'close',
            '成交量(手)': 'vol', '成交量（手）': 'vol', '成交量': 'vol', 
            '成交额(千元)': 'amount', '成交额（千元）': 'amount', '成交额': 'amount'
        }
        en_map = {
            'ts_code': 'code', 'code': 'code', 'trade_date': 'trade_date', 'open': 'open',
            'high': 'high', 'low': 'low', 'close': 'close',
            'vol': 'vol', 'volume': 'vol', 'Volume': 'vol', 'VOLUME': 'vol',
            'amount': 'amount', 'Amount': 'amount'
        }
        
        def get_col(target_col):
            candidates = []
            # Check CN map
            for k, v in cn_map.items():
                if v == target_col and k in df.columns:
                    candidates.append(df[k])
            # Check EN map
            for k, v in en_map.items():
                if v == target_col and k in df.columns:
                    candidates.append(df[k])
            
            if not candidates:
                return None
            
            # Coalesce
            result = candidates[0]
            for c in candidates[1:]:
                result = result.fillna(c)
            return result

        new_df = pd.DataFrame()
        found_any = False
        columns_order = ['code', 'trade_date', 'open', 'high', 'low', 'close', 'vol', 'amount']
        
        for field in columns_order:
            col_data = get_col(field)
            if col_data is not None:
                new_df[field] = col_data
                found_any = True
                
        if not found_any:
             return pd.DataFrame()

        # Remove duplicate columns
        new_df = new_df.loc[:, ~new_df.columns.duplicated()]
        
        # Standardize Data Types and Formats
        if 'trade_date' in new_df.columns:
            # Clean float dates (e.g. 20251223.0 -> 20251223)
            new_df['trade_date'] = new_df['trade_date'].astype(str).str.replace(r'\.0$', '', regex=True)
            # Convert to datetime to standardize
            new_df['trade_date'] = pd.to_datetime(new_df['trade_date'], errors='coerce')
            # Format back to YYYYMMDD string
            new_df['trade_date'] = new_df['trade_date'].dt.strftime('%Y%m%d')
            
        # Ensure numeric columns
        numeric_cols = ['open', 'high', 'low', 'close', 'vol', 'amount']
        for col in numeric_cols:
            if col in new_df.columns:
                # Handle strings with commas or other artifacts
                if new_df[col].dtype == 'object':
                     # Remove commas
                     new_df[col] = new_df[col].astype(str).str.replace(',', '')
                     # Try to clean non-numeric characters (except dot, minus, E)
                     # But be careful not to break valid formats. 
                     # For now, primarily focus on commas and whitespace.
                     new_df[col] = new_df[col].str.strip()
                
                new_df[col] = pd.to_numeric(new_df[col], errors='coerce')
                
        return new_df[columns_order] if set(columns_order).issubset(new_df.columns) else new_df

    async def get_mixed_history(self, code: str, days: int = 250, split_date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        混合获取历史数据: CSV (<= split_date) + Tushare (> split_date)
        """
        if not split_date_str:
            split_date_str = get_settings().tushare_incremental_start_date or "2025-12-22"

        try:
            # 1. CSV Data
            csv_path = self._find_csv_path(code)
            csv_records = []
            
            # Split date setup
            try:
                split_date = datetime.strptime(split_date_str, "%Y-%m-%d").date()
            except ValueError:
                # Fallback or error
                split_date = date(2025, 12, 22)

            if csv_path:
                try:
                    df_csv = pd.read_csv(csv_path)
                    # Normalize columns
                    df_csv = self._normalize_df(df_csv)
                    
                    if not df_csv.empty and 'trade_date' in df_csv.columns:
                        # Convert to date object
                        df_csv['trade_date'] = pd.to_datetime(df_csv['trade_date'], format='%Y%m%d', errors='coerce').dt.date
                        
                        # Drop duplicates in CSV based on trade_date, keep last
                        df_csv.drop_duplicates(subset=['trade_date'], keep='last', inplace=True)
                        
                        # Filter
                        df_csv = df_csv[df_csv['trade_date'] <= split_date]
                        
                        # Select columns
                        csv_records = df_csv.to_dict('records')
                except Exception as e:
                    logger.error(f"Error reading CSV for {code}: {e}")
            else:
                logger.warning(f"No CSV found for {code}")

            # 2. Tushare Data
            ts_records = []
            start_date_ts = (split_date + timedelta(days=1)).strftime("%Y%m%d")
            today_str = datetime.now().strftime("%Y%m%d")
            
            ts_code = self.tushare_service._add_suffix(code)
            
            # Fetch from Tushare
            # Note: get_daily is async and rate limited
            df_ts = await self.tushare_service.get_daily(ts_code, start_date_ts, today_str)
            
            # Fallback to Akshare
            if df_ts is None:
                logger.warning(f"Tushare get_mixed_history failed for {code}, trying Akshare fallback...")
                df_ts = await self.fetch_from_akshare(code, start_date_ts, today_str)
            
            if df_ts is not None and not df_ts.empty:
                # Normalize Tushare Data
                # Tushare cols: ts_code, trade_date, open, high, low, close, pre_close, change, pct_chg, vol, amount
                # Need to match standard keys if possible, or just return what we have
                # Standard keys: code, trade_date, open, close, high, low, vol, amount
                
                df_ts['trade_date'] = pd.to_datetime(df_ts['trade_date'], format='%Y%m%d').dt.date
                # Ensure vol is numeric
                df_ts['vol'] = pd.to_numeric(df_ts['vol'], errors='coerce')
                
                # Rename ts_code to code for consistency
                if 'ts_code' in df_ts.columns:
                    df_ts = df_ts.rename(columns={'ts_code': 'code'})
                
                ts_records = df_ts.to_dict('records')

            # 3. Merge
            all_records = csv_records + ts_records
            
            # Filter valid records (must have trade_date)
            all_records = [r for r in all_records if r.get('trade_date') is not None]
            
            # Deduplicate by trade_date (Global Dedup)
            # Use a dict to keep the last occurrence for each date
            unique_records_map = {}
            for r in all_records:
                unique_records_map[r['trade_date']] = r
            
            all_records = list(unique_records_map.values())
            
            # Sort by date
            all_records.sort(key=lambda x: x['trade_date'])
            
            # 4. Limit (Last N days)
            if len(all_records) > days:
                all_records = all_records[-days:]
                
            return {
                "success": True,
                "data": all_records,
                "count": len(all_records)
            }
            
        except Exception as e:
            logger.error(f"get_mixed_history failed: {e}")
            return {"success": False, "message": str(e), "data": []}

    async def sync_csv_to_db(self, batch_id: int, days: int = 250, end_date_str: str = "2025-12-22", stock_codes: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        同步CSV数据到数据库
        :param batch_id: 批次ID
        :param days: 同步天数
        :param end_date_str: 截止日期 (含)
        :param stock_codes: 指定同步的股票代码列表 (可选)
        """
        # Create Log
        log = await self.log_repository.create_log(
            task_type=SyncTaskType.CSV_FULL,
            batch_id=batch_id
        )

        try:
            batch_stocks = await self.get_batch_stocks(batch_id)
            if not batch_stocks:
                await self.log_repository.update_log(
                    log_id=log.id,
                    status=SyncTaskStatus.FAILED,
                    end_time=datetime.now(),
                    message="该批次无关联股票"
                )
                return {"success": False, "message": "该批次无关联股票"}

            # 如果指定了股票代码，则取交集
            if stock_codes:
                target_codes = list(set(batch_stocks) & set(stock_codes))
                if not target_codes:
                    return {"success": False, "message": "指定的股票不在该批次中"}
            else:
                target_codes = batch_stocks

            # end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            # start_date = end_date - timedelta(days=days)
            # 修改为读取 end_date 之前的所有数据，然后取最后 days 条
            target_end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            
            stats = {"processed": 0, "inserted": 0, "errors": 0, "read_rows": 0}

            # 调用原子方法
            for code in target_codes:
                try:
                    result = await self.sync_csv_single(code, days, end_date_str)
                    stats["processed"] += 1
                    if result["success"]:
                         # 这里的 inserted 只是简单计数，实际 sync_csv_single 内部会插入
                        stats["inserted"] += result.get("inserted", 0)
                    else:
                        stats["errors"] += 1
                        logger.warning(f"Stock {code} sync failed: {result['message']}")
                except Exception as e:
                    stats["errors"] += 1
                    logger.error(f"Stock {code} sync exception: {e}")

            await self.log_repository.update_log(
                log_id=log.id,
                status=SyncTaskStatus.SUCCESS if stats["errors"] == 0 else SyncTaskStatus.FAILED, # Partial success?
                end_time=datetime.now(),
                message=f"Success: {stats['inserted']}, Errors: {stats['errors']}",
                processed_count=stats["processed"],
                inserted_count=stats["inserted"],
                error_count=stats["errors"]
            )
            return {"success": True, "data": stats}
            
        except Exception as e:
            logger.error(f"Batch sync failed: {e}")
            await self.log_repository.update_log(
                log_id=log.id,
                status=SyncTaskStatus.FAILED,
                end_time=datetime.now(),
                message=str(e)
            )
            return {"success": False, "message": str(e)}

    async def sync_csv_single(self, code: str, days: int = 250, end_date_str: str = "2025-12-22") -> Dict[str, Any]:
        """
        同步单只股票的CSV数据
        """
        csv_path = self._find_csv_path(code)
        if not csv_path:
            return {"success": False, "message": f"CSV file not found for {code}"}

        target_end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        
        try:
            # 读取CSV
            df = pd.read_csv(csv_path)
            
            # 处理混合列名 (支持 Tushare 格式和中文格式同时存在的情况)
            df = self._normalize_df(df)
            
            # Fill missing code with the function argument 'code' (handling bad CSV data)
            if 'code' not in df.columns:
                 df['code'] = code
            else:
                 df['code'] = df['code'].fillna(code)
            
            if df.empty:
                 return {"success": False, "message": "No recognized columns found in CSV"}
            
            # 检查必要字段
            required_fields = ['code', 'trade_date', 'open', 'high', 'low', 'close', 'vol', 'amount']
            missing_fields = [f for f in required_fields if f not in df.columns]
            if missing_fields:
                 return {"success": False, "message": f"Missing columns: {missing_fields}"}
            
            # Format
            # 去除代码后缀
            df['code'] = df['code'].apply(lambda x: str(x).split('.')[0] if pd.notnull(x) else x)
            # 处理日期 (兼容 float/int/str)
            df['trade_date'] = df['trade_date'].astype(str).str.replace(r'\.0$', '', regex=True)
            df['trade_date'] = pd.to_datetime(df['trade_date'], errors='coerce', format='mixed').dt.date
            
            # Filter Date
            df = df[df['trade_date'] <= target_end_date]
            df.sort_values('trade_date', ascending=True, inplace=True)
            
            # Limit days (last N days)
            if len(df) > days:
                df = df.iloc[-days:]
                
            if df.empty:
                return {"success": True, "message": "No data in range (0 inserted)", "inserted": 0}

            # Convert to dict list
            records = df.to_dict('records')
            
            # Clean data (handle NaN, types)
            cleaned_records = []
            for r in records:
                try:
                    cleaned_records.append({
                        "code": r['code'],
                        "trade_date": r['trade_date'],
                        "open": float(r['open']) if pd.notnull(r['open']) else None,
                        "high": float(r['high']) if pd.notnull(r['high']) else None,
                        "low": float(r['low']) if pd.notnull(r['low']) else None,
                        "close": float(r['close']) if pd.notnull(r['close']) else None,
                        "vol": int(r['vol']) if pd.notnull(r['vol']) else None,
                        "amount": float(r['amount']) if pd.notnull(r['amount']) else None
                    })
                except Exception as row_err:
                    logger.warning(f"Skipping row for {code} due to error: {row_err}")
                    continue
            
            inserted_count = await self.repository.batch_save_daily_data_ignore(cleaned_records)
            
            if self.pathway_enabled:
                try:
                    async with self.db_manager.get_session() as session:
                        self.pathway_engine = PathwayVolumePriceEngine(session)
                        for record in cleaned_records:
                            stmt = select(StockDaily).where(
                                StockDaily.code == record['code'],
                                StockDaily.trade_date == record['trade_date']
                            )
                            result = await session.execute(stmt)
                            stock_daily = result.scalar_one_or_none()
                            if stock_daily:
                                await self.pathway_engine.process_new_data(stock_daily)
                except Exception as e:
                    logger.error(f"Pathway处理失败: {e}")
            
            return {"success": True, "inserted": inserted_count}

        except Exception as e:
            logger.error(f"Error syncing CSV for {code}: {e}")
            return {"success": False, "message": str(e)}



    async def sync_tushare_increment(self, batch_id: int, start_date_str: Optional[str] = None, stock_codes: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Tushare增量同步
        :param batch_id: 批次ID
        :param start_date_str: 开始日期 (含)
        :param stock_codes: 指定同步的股票代码列表 (可选)
        """
        if not start_date_str:
            # Default to settings date + 1 day
            split_date_str = get_settings().tushare_incremental_start_date or "2025-12-22"
            try:
                split_date = datetime.strptime(split_date_str, "%Y-%m-%d").date()
                start_date_str = (split_date + timedelta(days=1)).strftime("%Y-%m-%d")
            except ValueError:
                start_date_str = "2025-12-23"

        # Create Log
        log = await self.log_repository.create_log(
            task_type=SyncTaskType.TUSHARE_INCREMENT,
            batch_id=batch_id
        )

        try:
            batch_stocks = await self.get_batch_stocks(batch_id)
            if not batch_stocks:
                await self.log_repository.update_log(
                    log_id=log.id,
                    status=SyncTaskStatus.FAILED,
                    end_time=datetime.now(),
                    message="该批次无关联股票"
                )
                return {"success": False, "message": "该批次无关联股票"}

            # 如果指定了股票代码，则取交集
            if stock_codes:
                target_codes = list(set(batch_stocks) & set(stock_codes))
                if not target_codes:
                    return {"success": False, "message": "指定的股票不在该批次中"}
            else:
                target_codes = batch_stocks

            # Initialize stats
            stats = {
                "processed": 0,
                "inserted": 0,
                "csv_appended": 0,
                "errors": 0
            }

            # 调用原子方法
            for code in target_codes:
                try:
                    result = await self.sync_tushare_single(code, start_date_str)
                    stats["processed"] += 1
                    if result["success"]:
                        stats["inserted"] += result.get("inserted", 0)
                        stats["csv_appended"] += result.get("csv_appended", 0)
                    else:
                        stats["errors"] += 1
                        logger.warning(f"Stock {code} tushare sync failed: {result['message']}")
                except Exception as e:
                    stats["errors"] += 1
                    logger.error(f"Stock {code} tushare sync exception: {e}")

            # Update Log Success
            await self.log_repository.update_log(
                log_id=log.id,
                status=SyncTaskStatus.SUCCESS,
                end_time=datetime.now(),
                processed_count=stats["processed"],
                inserted_count=stats["inserted"],
                error_count=stats["errors"],
                message=f"Synced {stats['inserted']} records from {stats['processed']} stocks"
            )
            return {"success": True, "data": stats}

        except Exception as e:
            # Update Log Failed
            await self.log_repository.update_log(
                log_id=log.id,
                status=SyncTaskStatus.FAILED,
                end_time=datetime.now(),
                message=str(e)
            )
            logger.error(f"Sync Tushare failed: {e}")
            return {"success": False, "message": str(e)}

    async def sync_tushare_single(self, code: str, start_date_str: str = "2025-12-23") -> Dict[str, Any]:
        """
        同步单只股票的Tushare数据
        """
        try:
            # Tushare 日期格式 YYYYMMDD
            ts_start_date = start_date_str.replace("-", "")
            today_str = datetime.now().strftime("%Y%m%d")
            
            # 1. 获取 Tushare 数据
            # Tushare code format: 000001.SZ
            # 使用 TushareService 的辅助方法添加后缀
            ts_code = self.tushare_service._add_suffix(code)
            # Use rate-limited async wrapper
            df = await self.tushare_service.get_daily(ts_code=ts_code, start_date=ts_start_date, end_date=today_str)
            
            # Fallback to AkShare
            if df is None:
                logger.info(f"Tushare returned None for {code}, attempting AkShare fallback...")
                df = await self.fetch_from_akshare(code, ts_start_date, today_str)
                if df is not None and not df.empty and 'amount' in df.columns:
                     # AkShare amount is usually in Yuan, Tushare is in Thousands.
                     df['amount'] = df['amount'] / 1000.0
            
            if df is None or df.empty:
                 return {"success": True, "inserted": 0, "csv_appended": 0, "message": "No data from Tushare or AkShare"}
            
            # Tushare 返回字段: ts_code, trade_date, open, high, low, close, pre_close, change, pct_chg, vol, amount
            
            # 2. 存入数据库
            db_data_list = []
            csv_rows = []
            
            # 按日期升序排序 (Tushare通常返回降序)
            df = df.sort_values('trade_date')
            
            for _, row in df.iterrows():
                # DB Data
                # trade_date is string 'YYYYMMDD'
                t_date = datetime.strptime(row['trade_date'], "%Y%m%d").date()
                
                item = {
                    "code": code,
                    "trade_date": t_date,
                    "open": float(row['open']),
                    "high": float(row['high']),
                    "low": float(row['low']),
                    "close": float(row['close']),
                    "vol": int(row['vol']), # Tushare vol is in 手
                    "amount": float(row['amount']), # Tushare amount is in 千元
                }
                db_data_list.append(item)
                
                # CSV Data (Prepare for appending)
                # Keep original format or match CSV file format
                # CSV format usually: ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount
                # We need to match what's in the CSV files on disk
                csv_row = row.to_dict()
                csv_rows.append(csv_row)

            inserted_count = 0
            csv_appended_count = 0
             # 3. Save to DB (with Deadlock Retry)
            if db_data_list:
                retries = 3
                for attempt in range(retries):
                    try:
                        inserted_count = await self.repository.batch_save_daily_data_ignore(db_data_list)
                        break
                    except Exception as e:
                        if "Deadlock" in str(e) or "deadlock" in str(e):
                            if attempt < retries - 1:
                                wait_time = 0.5 * (2 ** attempt)
                                logger.warning(f"Deadlock saving {code}, retrying {attempt+1}/{retries} in {wait_time}s")
                                await asyncio.sleep(wait_time)
                                continue
                        # Not deadlock or max retries reached
                        raise e
            
            # 4. Append to CSV file
            csv_path = self._find_csv_path(code)
            if csv_path and csv_rows:
                try:
                    # Append mode 'a'
                    # Check if header exists? Usually yes.
                    # We just append new rows.
                    # CAUTION: Need to ensure we don't duplicate. 
                    # Ideally, read existing CSV, concat, drop duplicates, save.
                    
                    existing_df = pd.read_csv(csv_path)
                    
                    # Normalize existing DF to prevent mixed columns
                    existing_df = self._normalize_df(existing_df)
                    
                    new_df = pd.DataFrame(csv_rows)
                    # Normalize new DF to ensure same columns and format
                    new_df = self._normalize_df(new_df)
                    
                    # Ensure strict incremental date
                    if not existing_df.empty and 'trade_date' in existing_df.columns:
                        last_date = existing_df['trade_date'].max()
                        # Ensure comparison is done on strings YYYYMMDD
                        if isinstance(last_date, str):
                            # Filter new_df to only include dates strictly greater than last_date
                            new_df = new_df[new_df['trade_date'] > last_date]
                    
                    if new_df.empty:
                        # No new data to append
                        return {"success": True, "inserted": inserted_count, "csv_appended": 0, "message": "No new data to append"}

                    # Append and Save
                    combined_df = pd.concat([existing_df, new_df])
                    
                    # Double check date format before saving (should be YYYYMMDD string from _normalize_df)
                    # But if user wants consistent CSV, YYYYMMDD is good.
                    
                    combined_df.to_csv(csv_path, index=False)
                    csv_appended_count = len(new_df)
                    
                except Exception as e:
                    logger.error(f"Error appending CSV for {code}: {e}")
                    # Don't fail the whole task if CSV append fails? 
                    # Maybe just log it.

            return {"success": True, "inserted": inserted_count, "csv_appended": csv_appended_count}
        
        except Exception as e:
            logger.error(f"Error syncing Tushare for {code}: {e}")
            return {"success": False, "message": str(e)}
        
        if self.pathway_enabled:
            try:
                async with self.db_manager.get_session() as session:
                    self.pathway_engine = PathwayVolumePriceEngine(session)
                    for record in db_data_list:
                        stmt = select(StockDaily).where(
                            StockDaily.code == record['code'],
                            StockDaily.trade_date == record['trade_date']
                        )
                        result = await session.execute(stmt)
                        stock_daily = result.scalar_one_or_none()
                        if stock_daily:
                            await self.pathway_engine.process_new_data(stock_daily)
            except Exception as e:
                logger.error(f"Pathway处理失败: {e}")

    async def check_csv_health(self) -> Dict[str, Any]:
        """
        检查所有CSV文件格式健康状况
        :return: 检查结果摘要
        """
        history_path = get_settings().csv_data_path
        if not os.path.exists(history_path):
            return {"success": False, "message": "History directory not found"}

        import glob
        csv_files = glob.glob(os.path.join(history_path, "*.csv"))
        
        total_files = len(csv_files)
        checked_count = 0
        error_count = 0
        errors = []
        
        logger.info(f"Starting CSV health check for {total_files} files...")
        
        for file_path in csv_files:
            file_name = os.path.basename(file_path)
            try:
                # Read header only first to check columns
                df_header = pd.read_csv(file_path, nrows=0)
                expected_cols = {'code', 'trade_date', 'open', 'high', 'low', 'close', 'vol', 'amount'}
                current_cols = set(df_header.columns)
                
                issues = []
                
                # Check 1: Column Consistency
                if not expected_cols.issubset(current_cols):
                    missing = expected_cols - current_cols
                    issues.append(f"Missing columns: {missing}")
                
                # Read full file for data checks (or sample?)
                # Reading full file might be slow for 5000+ files. 
                # Let's read first and last few rows + sample?
                # For comprehensive check, we need to read 'trade_date' and 'vol'.
                # Use usecols to optimize
                
                if not issues:
                    try:
                        df = pd.read_csv(file_path, usecols=['trade_date', 'vol'])
                        
                        # Check 2: Date Format
                        # Check if dates are parsable and not float strings like '20251223.0'
                        # We expect YYYYMMDD or YYYY-MM-DD string, or int.
                        # If it's float string ending in .0, it's an issue we want to flag (though we auto-fix it now during sync).
                        
                        # Check for float-like strings
                        if df['trade_date'].dtype == 'object':
                            if df['trade_date'].astype(str).str.contains(r'\.0$').any():
                                issues.append("Contains float-formatted dates (e.g. 20230101.0)")
                        
                        # Check 3: Volume Units
                        # Heuristic: if volume is consistently very small (< 100) or very large?
                        # Tushare vol is in Hands (100 shares).
                        # If vol is in shares, it would be 100x larger.
                        # Typical daily volume for a stock: 10,000 hands to 1,000,000 hands.
                        # If we see < 1 (except 0), might be weird.
                        # But some inactive stocks have 0 vol.
                        # Let's just check for negative values.
                        
                        if (pd.to_numeric(df['vol'], errors='coerce') < 0).any():
                             issues.append("Contains negative volume")
                             
                    except Exception as e:
                        issues.append(f"Data read error: {e}")

                if issues:
                    error_count += 1
                    errors.append({"file": file_name, "issues": issues})
                    logger.warning(f"CSV Health Issue in {file_name}: {issues}")

                checked_count += 1
                if checked_count % 100 == 0:
                    logger.info(f"Checked {checked_count}/{total_files} files...")

            except Exception as e:
                error_count += 1
                errors.append({"file": file_name, "issues": [f"File read error: {e}"]})
                logger.error(f"Error checking {file_name}: {e}")

        logger.info(f"CSV Health Check completed. Found {error_count} files with issues.")
        
        # Alert if errors found (could integrate with a notification service later)
        return {
            "success": True,
            "total_files": total_files,
            "checked_count": checked_count,
            "error_count": error_count,
            "errors": errors[:100] # Limit response size
        }
    
    async def sync_wencai_stocks_to_db(self) -> Dict[str, Any]:
        """
        批量同步问财股票到数据库
        从wencai_stocks表获取所有股票代码并批量同步
        
        Returns:
            同步结果
        """
        try:
            from sqlalchemy import select, text
            
            # 获取所有问财股票代码
            async with self.db_manager.get_session() as session:
                query = text("SELECT DISTINCT stock_code FROM wencai_stocks")
                result = await session.execute(query)
                codes = [row[0] for row in result.fetchall()]
            
            logger.info(f"开始同步 {len(codes)} 只问财股票到数据库")
            
            success_count = 0
            failed_count = 0
            
            for code in codes:
                try:
                    # 同步单只股票（使用sync_csv_single方法）
                    result = await self.sync_csv_single(code, days=250, end_date_str=datetime.now().strftime("%Y-%m-%d"))
                    
                    if result["success"]:
                        success_count += 1
                    else:
                        failed_count += 1
                        logger.warning(f"同步 {code} 失败: {result.get('message', 'Unknown error')}")
                except Exception as e:
                    failed_count += 1
                    logger.error(f"同步 {code} 异常: {e}")
            
            logger.info(f"问财股票同步完成: 成功 {success_count}, 失败 {failed_count}")
            
            return {
                "success": True,
                "total_count": len(codes),
                "success_count": success_count,
                "failed_count": failed_count
            }
        except Exception as e:
            logger.error(f"批量同步问财股票失败: {e}")
            return {
                "success": False,
                "message": str(e)
            }



