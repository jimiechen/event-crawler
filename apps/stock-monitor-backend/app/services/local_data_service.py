import csv
import os
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict
import logging
from app.config.settings import get_settings

# We assume models are available, but this service returns dicts primarily to decouple from DB session management here.
# The consumer (WencaiService) will use StockService to save these dicts.

logger = logging.getLogger(__name__)

class LocalDataService:
    @classmethod
    def get_daily_dir(cls):
        return get_settings().csv_data_path_stock_daily

    @classmethod
    def get_base_dir(cls):
        return os.path.dirname(cls.get_daily_dir())

    @classmethod
    def get_stock_basic_path(cls):
        return os.path.join(cls.get_base_dir(), "stock_basic", "stock_basic.csv")
    
    @classmethod
    def get_daily_basic_dir(cls):
        return os.path.join(cls.get_base_dir(), "daily_basic")

    @classmethod
    async def load_all_local_data(cls, stock_service):
        """
        加载所有本地历史数据到数据库 (优先级最高)
        """
        logger.info("开始加载本地历史数据...")
        
        # 1. 加载股票基本信息
        await cls.load_all_stock_basics(stock_service)
        
        # 2. 加载日线数据
        daily_dir = cls.get_daily_dir()
        if not os.path.exists(daily_dir):
            logger.warning(f"Local daily data directory not found: {daily_dir}")
            return

        files = [f for f in os.listdir(daily_dir) if f.endswith('.csv')]
        total = len(files)
        logger.info(f"发现 {total} 个本地数据文件")
        
        processed = 0
        for filename in files:
            try:
                code = filename.replace('.csv', '')
                
                # 加载日线数据
                daily_data = await cls.get_daily_data(code, limit=250)
                if daily_data:
                    await stock_service.stock_daily_repo.batch_save_daily_data(daily_data)
                
                processed += 1
                if processed % 100 == 0:
                    logger.info(f"本地数据加载进度: {processed}/{total}")
                    
            except Exception as e:
                logger.error(f"Failed to load local data for {filename}: {e}")
                
        logger.info("本地历史数据加载完成")

    @classmethod
    async def load_local_data_for_stocks(cls, stock_service, codes: List[str], end_date: Optional[date] = None):
        """
        加载指定股票列表的本地历史数据
        """
        daily_dir = cls.get_daily_dir()
        if not os.path.exists(daily_dir):
            logger.warning(f"Local daily data directory not found: {daily_dir}")
            return

        logger.info(f"开始加载 {len(codes)} 只指定股票的本地数据... (End Date: {end_date})")
        processed = 0
        for code in codes:
            try:
                # 加载日线数据
                daily_data = await cls.get_daily_data(code, limit=250, end_date=end_date)
                if daily_data:
                    await stock_service.stock_daily_repo.batch_save_daily_data(daily_data)
                
                processed += 1
                if processed % 10 == 0:
                     logger.info(f"指定股票数据加载进度: {processed}/{len(codes)}")
            except Exception as e:
                logger.error(f"Failed to load local data for {code}: {e}")
        
        logger.info(f"指定股票本地数据加载完成: {processed}/{len(codes)}")

    @classmethod
    async def load_stock_basics_for_stocks(cls, stock_service, codes: List[str]):
        """
        加载指定股票列表的本地股票基本信息
        """
        stock_basic_path = cls.get_stock_basic_path()
        if not os.path.exists(stock_basic_path):
            logger.warning(f"Local stock basic file not found: {stock_basic_path}")
            return
            
        logger.info(f"开始加载 {len(codes)} 只指定股票的本地基本信息...")
        codes_set = set(codes)
        
        try:
            with open(stock_basic_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    if row['股票代码'] not in codes_set:
                        continue
                        
                    try:
                        stock_info = {
                            "stock_code": row['股票代码'],
                            "stock_name": row['股票名称'],
                            "market": cls._get_market_from_code(row['股票代码']),
                            "industry": row.get('行业'),
                            "area": row.get('地区'),
                            "is_active": True
                        }
                        await stock_service.create_or_update_stock_info(stock_info)
                        count += 1
                    except Exception as e:
                        logger.warning(f"Error loading stock basic row {row}: {e}")
                        
                logger.info(f"已加载 {count} 条指定股票基本信息")
        except Exception as e:
            logger.error(f"Error reading local stock basic file: {e}")

    @classmethod
    async def load_all_stock_basics(cls, stock_service):
        """
        加载本地股票基本信息
        """
        stock_basic_path = cls.get_stock_basic_path()
        if not os.path.exists(stock_basic_path):
            logger.warning(f"Local stock basic file not found: {stock_basic_path}")
            return
            
        logger.info("开始加载本地股票基本信息...")
        try:
            with open(stock_basic_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    try:
                        stock_info = {
                            "stock_code": row['股票代码'],
                            "stock_name": row['股票名称'],
                            "market": cls._get_market_from_code(row['股票代码']),
                            "industry": row.get('行业'),
                            "area": row.get('地区'),
                            "is_active": True
                        }
                        await stock_service.create_or_update_stock_info(stock_info)
                        count += 1
                    except Exception as e:
                        logger.warning(f"Error loading stock basic row {row}: {e}")
                        
                logger.info(f"已加载 {count} 条股票基本信息")
        except Exception as e:
            logger.error(f"Error reading local stock basic file: {e}")

    @classmethod
    async def get_stock_basic(cls, code: str) -> Optional[Dict]:
        """
        从本地CSV读取股票基本信息
        Returns a dict suitable for StockService.create_or_update_stock_info
        """
        stock_basic_path = cls.get_stock_basic_path()
        if not os.path.exists(stock_basic_path):
            logger.warning(f"Local stock basic file not found: {stock_basic_path}")
            return None
        
        try:
            with open(stock_basic_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['股票代码'] == code:
                        return {
                            "stock_code": row['股票代码'],
                            "stock_name": row['股票名称'],
                            "market": cls._get_market_from_code(row['股票代码']),
                            "industry": row.get('行业'),
                            "area": row.get('地区'),
                            "is_active": True
                        }
        except Exception as e:
            logger.error(f"Error reading local stock basic for {code}: {e}")
            return None
        return None

    @classmethod
    async def get_daily_data(cls, code: str, limit: int = 250, end_date: Optional[date] = None) -> List[Dict]:
        """
        从本地CSV读取日线数据 (近 limit 天)
        合并 daily (OHLC) 和 daily_basic (换手率/量比) 数据
        支持自动匹配文件名后缀 (e.g. code='600724' can find '600724.SH.csv')
        返回数据的 code 字段将统一为无后缀格式
        """
        # Normalize input code
        normalized_code = code.split('.')[0]
        
        # Try to find the file
        candidates = [
            f"{code}.csv",
            f"{normalized_code}.SH.csv",
            f"{normalized_code}.SZ.csv",
            f"{normalized_code}.BJ.csv",
            f"{normalized_code}.csv"
        ]
        
        daily_path = None
        found_filename = None
        
        daily_dir = cls.get_daily_dir()
        for fname in candidates:
            path = os.path.join(daily_dir, fname)
            if os.path.exists(path):
                daily_path = path
                found_filename = fname
                break
        
        if not daily_path:
            # logger.warning(f"Local daily data file not found for {code} (tried {candidates})")
            return []

        # Determine daily_basic path (try to match the same suffix/filename pattern)
        daily_basic_path = os.path.join(cls.get_daily_basic_dir(), found_filename)
        
        # 1. Read daily data (OHLC, vol, amount)
        daily_records = {}
        try:
            with open(daily_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        date_str = row['交易日期']
                        daily_records[date_str] = row
                    except KeyError:
                        continue
        except Exception as e:
            logger.error(f"Error reading daily file {daily_path}: {e}")
            return []

        # 2. Read daily_basic data (turnover, volume_ratio)
        basic_records = {}
        if os.path.exists(daily_basic_path):
            try:
                with open(daily_basic_path, mode='r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            date_str = row['交易日期']
                            basic_records[date_str] = row
                        except KeyError:
                            continue
            except Exception as e:
                logger.warning(f"Error reading daily_basic file {daily_basic_path}: {e}")
                # Continue without basic data

        # 3. Merge and process
        data_list = []
        
        # Sort dates descending to get latest 'limit' days
        sorted_dates = sorted(daily_records.keys(), reverse=True)
        
        if end_date:
            end_date_str = end_date.strftime("%Y-%m-%d")
            sorted_dates = [d for d in sorted_dates if d <= end_date_str]
            
        sorted_dates = sorted_dates[:limit]
        
        for date_str in sorted_dates:
            daily_row = daily_records[date_str]
            basic_row = basic_records.get(date_str, {})
            
            try:
                trade_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                
                # Parse OHLC etc.
                open_price = Decimal(daily_row.get('开盘价') or 0)
                high_price = Decimal(daily_row.get('最高价') or 0)
                low_price = Decimal(daily_row.get('最低价') or 0)
                close_price = Decimal(daily_row.get('收盘价') or 0)
                vol = Decimal(daily_row.get('成交量(手)') or 0)
                amount = Decimal(daily_row.get('成交额(千元)') or 0)
                
                # Parse basic data
                turnover_rate = Decimal(basic_row.get('换手率(%)') or 0)
                volume_ratio = Decimal(basic_row.get('量比') or 0)
                
                data_list.append({
                    "code": normalized_code, # Ensure code is normalized
                    "trade_date": trade_date,
                    "open": open_price,
                    "close": close_price,
                    "high": high_price,
                    "low": low_price,
                    "vol": int(vol),
                    "amount": amount,
                    "turnover_rate": turnover_rate,
                    "volume_ratio": volume_ratio
                })
                
            except Exception as e:
                logger.warning(f"Error processing row for {code} on {date_str}: {e}")
                continue
                
        # Return sorted by date ascending
        return sorted(data_list, key=lambda x: x['trade_date'])

    @staticmethod
    def _get_market_from_code(code: str) -> str:
        if code.endswith('.SH'):
            return 'sh'
        if code.endswith('.SZ'):
            return 'sz'
        if code.endswith('.BJ'):
            return 'bj'
        return 'unknown'
