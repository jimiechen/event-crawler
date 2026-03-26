#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模型
使用 SQLite 存储每日K线数据和选股结果
"""

import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from loguru import logger


class StockDatabase:
    """股票数据库管理类"""
    
    def __init__(self, db_path: str = "data/stock_monitor.db"):
        """
        初始化数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_tables(self):
        """初始化数据表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 日K线数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_kline (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT NOT NULL,
                    trade_date DATE NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    amount REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(stock_code, trade_date)
                )
            """)
            
            # 选股结果表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_selection (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT NOT NULL,
                    trade_date DATE NOT NULL,
                    strategy TEXT NOT NULL,
                    sector_code TEXT,
                    close_price REAL,
                    volume_ratio REAL,
                    change_percent REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(stock_code, trade_date, strategy)
                )
            """)
            
            # 板块表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sectors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sector_code TEXT NOT NULL UNIQUE,
                    sector_name TEXT,
                    trade_date DATE NOT NULL,
                    stock_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 板块-股票关联表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sector_stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sector_code TEXT NOT NULL,
                    stock_code TEXT NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(sector_code, stock_code)
                )
            """)
            
            # 截图记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS screenshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT NOT NULL,
                    trade_date DATE NOT NULL,
                    screenshot_type TEXT,  -- 'tdx', 'tlby_intraday', 'tlby_daily'
                    file_path TEXT,
                    ai_analysis TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info("数据库表初始化完成")
    
    def save_daily_kline(self, data: Dict[str, Any]) -> bool:
        """
        保存日K线数据
        
        Args:
            data: {
                "stock_code": str,
                "trade_date": date,
                "open": float,
                "high": float,
                "low": float,
                "close": float,
                "volume": int,
                "amount": float
            }
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO daily_kline 
                    (stock_code, trade_date, open, high, low, close, volume, amount)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data["stock_code"],
                    data["trade_date"],
                    data.get("open", 0),
                    data.get("high", 0),
                    data.get("low", 0),
                    data.get("close", 0),
                    data.get("volume", 0),
                    data.get("amount", 0)
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"保存日K线数据失败: {e}")
            return False
    
    def save_daily_klines_batch(self, data_list: List[Dict[str, Any]]) -> int:
        """
        批量保存日K线数据
        
        Args:
            data_list: 日K线数据列表
            
        Returns:
            int: 成功保存的记录数
        """
        success_count = 0
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for data in data_list:
                    try:
                        cursor.execute("""
                            INSERT OR REPLACE INTO daily_kline 
                            (stock_code, trade_date, open, high, low, close, volume, amount)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            data["stock_code"],
                            data["trade_date"],
                            data.get("open", 0),
                            data.get("high", 0),
                            data.get("low", 0),
                            data.get("close", 0),
                            data.get("volume", 0),
                            data.get("amount", 0)
                        ))
                        success_count += 1
                    except Exception as e:
                        logger.warning(f"保存单条K线数据失败: {e}")
                conn.commit()
                logger.info(f"批量保存日K线数据: {success_count}/{len(data_list)} 条成功")
                return success_count
        except Exception as e:
            logger.error(f"批量保存日K线数据失败: {e}")
            return success_count
    
    def get_daily_kline(self, stock_code: str, trade_date: date) -> Optional[Dict[str, Any]]:
        """获取单只股票的日K线数据"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM daily_kline 
                    WHERE stock_code = ? AND trade_date = ?
                """, (stock_code, trade_date))
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"获取日K线数据失败: {e}")
            return None
    
    def get_daily_klines(self, trade_date: date) -> List[Dict[str, Any]]:
        """获取某日的所有股票K线数据"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM daily_kline 
                    WHERE trade_date = ?
                """, (trade_date,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取日K线数据失败: {e}")
            return []
    
    def save_stock_selection(self, data: Dict[str, Any]) -> bool:
        """
        保存选股结果
        
        Args:
            data: {
                "stock_code": str,
                "trade_date": date,
                "strategy": str,
                "sector_code": str,
                "close_price": float,
                "volume_ratio": float,
                "change_percent": float
            }
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO stock_selection 
                    (stock_code, trade_date, strategy, sector_code, close_price, volume_ratio, change_percent)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    data["