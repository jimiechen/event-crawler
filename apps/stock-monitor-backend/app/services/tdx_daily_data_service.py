#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通达信日线数据同步服务
从通达信获取日K线数据并同步到stock_daily表
"""

import sys
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
from sqlalchemy import text
from sqlalchemy.dialects.mysql import insert
from loguru import logger

sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")
from tqcenter import tq

from app.database import db_manager
from app.models.stock_daily import StockDaily


class TdxDailyDataService:
    """通达信日线数据同步服务"""
    
    def __init__(self, tdx_client=None):
        """
        初始化
        
        Args:
            tdx_client: 通达信客户端实例，默认为None时使用全局tq
        """
        self.tdx_client = tdx_client
        if self.tdx_client is None:
            # 初始化通达信
            tq.initialize(__file__)
            self.tdx_client = tq
    
    async def sync_daily_data_for_selection(
        self,
        stock_codes: List[str],
        end_date: date,
        batch_id: int,
        days: int = 250
    ) -> Dict[str, Any]:
        """
        为选股结果同步250天日线数据
        
        Args:
            stock_codes: 股票代码列表 (格式: 000001.SZ)
            end_date: 结束日期 (选股日期)
            batch_id: 选股批次ID
            days: 获取天数 (默认250天)
            
        Returns:
            Dict: 同步结果统计
        """
        start_date = end_date - timedelta(days=days)
        
        total_synced = 0
        failed_stocks = []
        
        logger.info(f"开始同步 {len(stock_codes)} 只股票的日线数据，"
                   f"日期范围: {start_date} 至 {end_date}")
        
        for i, stock_code in enumerate(stock_codes, 1):
            try:
                logger.debug(f"[{i}/{len(stock_codes)}] 同步 {stock_code} 的日线数据...")
                
                # 从通达信获取K线数据
                # 返回格式: Dict[str, pd.DataFrame], 如 {'Close': df, 'Volume': df, ...}
                data_dict = self.tdx_client.get_market_data(
                    field_list=['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Amount'],
                    stock_list=[stock_code],
                    period='1d',
                    start_time=start_date.strftime('%Y%m%d'),
                    end_time=end_date.strftime('%Y%m%d'),
                    dividend_type='front',
                    fill_data=True
                )
                
                # 检查返回数据是否有效
                if data_dict is None or not isinstance(data_dict, dict):
                    logger.warning(f"{stock_code} 返回数据无效，跳过")
                    failed_stocks.append(stock_code)
                    continue
                
                # 检查是否有Close数据
                if 'Close' not in data_dict or data_dict['Close'] is None or data_dict['Close'].empty:
                    logger.warning(f"{stock_code} 无数据，跳过")
                    failed_stocks.append(stock_code)
                    continue
                
                # 转换为stock_daily格式并插入
                records = self._convert_to_daily_records(data_dict, stock_code, batch_id)
                if records:
                    inserted = await self._bulk_upsert_daily_data(records)
                    total_synced += inserted
                    logger.debug(f"{stock_code} 同步完成: {inserted} 条记录")
                
            except Exception as e:
                logger.error(f"同步 {stock_code} 日线数据失败: {e}")
                failed_stocks.append(stock_code)
        
        result = {
            "total_stocks": len(stock_codes),
            "total_synced": total_synced,
            "failed_count": len(failed_stocks),
            "failed_stocks": failed_stocks
        }
        
        logger.info(f"日线数据同步完成: {result}")
        return result
    
    async def sync_single_stock_daily_data(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
        batch_id: Optional[int] = None
    ) -> int:
        """
        同步单只股票的日线数据
        
        Args:
            stock_code: 股票代码 (格式: 000001.SZ)
            start_date: 开始日期
            end_date: 结束日期
            batch_id: 关联批次ID (可选)
            
        Returns:
            int: 同步的记录数
        """
        try:
            # 返回格式: Dict[str, pd.DataFrame]
            data_dict = self.tdx_client.get_market_data(
                field_list=['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Amount'],
                stock_list=[stock_code],
                period='1d',
                start_time=start_date.strftime('%Y%m%d'),
                end_time=end_date.strftime('%Y%m%d'),
                dividend_type='front',
                fill_data=True
            )
            
            # 检查返回数据是否有效
            if data_dict is None or not isinstance(data_dict, dict):
                return 0
            
            # 检查是否有Close数据
            if 'Close' not in data_dict or data_dict['Close'] is None or data_dict['Close'].empty:
                return 0
            
            records = self._convert_to_daily_records(data_dict, stock_code, batch_id)
            if records:
                return await self._bulk_upsert_daily_data(records)
            
            return 0
            
        except Exception as e:
            logger.error(f"同步 {stock_code} 日线数据失败: {e}")
            return 0
    
    def _convert_to_daily_records(
        self,
        data_dict: Dict[str, pd.DataFrame],
        stock_code: str,
        batch_id: Optional[int] = None
    ) -> List[Dict]:
        """
        转换通达信返回的字典格式为stock_daily记录
        
        Args:
            data_dict: 通达信返回的字典，格式为 {'Close': df, 'Volume': df, ...}
                      每个字段对应一个DataFrame，index为stock_code，columns为日期
            stock_code: 股票代码
            batch_id: 关联批次ID
            
        Returns:
            List[Dict]: 记录列表
        """
        records = []
        
        # 处理股票代码，去掉后缀
        code = stock_code.split('.')[0] if '.' in stock_code else stock_code
        
        # 获取Close数据的DataFrame来确定日期列表
        close_df = data_dict.get('Close')
        if close_df is None or close_df.empty:
            return records
        
        # 通达信返回的DataFrame: index是日期，columns是股票代码
        # 例如: close_df.loc['2026-03-20', '000001.SZ'] = 10.77
        if stock_code not in close_df.columns:
            logger.warning(f"股票 {stock_code} 不在返回数据中，columns: {close_df.columns.tolist()}")
            return records
        
        # 获取日期列表 (index)
        dates = close_df.index.tolist()
        
        for trade_date_idx in dates:
            try:
                # 处理日期 (index是Timestamp)
                if isinstance(trade_date_idx, pd.Timestamp):
                    trade_date = trade_date_idx.date()
                else:
                    trade_date = pd.to_datetime(trade_date_idx).date()
                
                # 从各个字段的DataFrame中获取数据
                close_val = close_df.loc[trade_date_idx, stock_code]
                
                # 获取其他字段
                open_df = data_dict.get('Open')
                high_df = data_dict.get('High')
                low_df = data_dict.get('Low')
                volume_df = data_dict.get('Volume')
                amount_df = data_dict.get('Amount')
                
                open_val = open_df.loc[trade_date_idx, stock_code] if open_df is not None else None
                high_val = high_df.loc[trade_date_idx, stock_code] if high_df is not None else None
                low_val = low_df.loc[trade_date_idx, stock_code] if low_df is not None else None
                volume = volume_df.loc[trade_date_idx, stock_code] if volume_df is not None else None
                amount = amount_df.loc[trade_date_idx, stock_code] if amount_df is not None else None
                
                # 单位转换:
                # - 成交量: 通达信(股) → stock_daily(手), 除以100
                # - 成交额: 通达信(元) → stock_daily(千元), 除以1000
                # - 价格: 单位一致(元), 无需转换
                if pd.notna(volume):
                    volume = int(volume / 100)  # 股 → 手
                else:
                    volume = None
                    
                if pd.notna(amount):
                    amount = float(amount / 1000)  # 元 → 千元
                else:
                    amount = None
                
                record = {
                    "code": code,
                    "trade_date": trade_date,
                    "open": float(open_val) if pd.notna(open_val) else None,
                    "high": float(high_val) if pd.notna(high_val) else None,
                    "low": float(low_val) if pd.notna(low_val) else None,
                    "close": float(close_val) if pd.notna(close_val) else None,
                    "vol": volume,
                    "amount": amount,
                    "source_batch_id": batch_id
                }
                records.append(record)
            except Exception as e:
                logger.warning(f"转换记录失败 {stock_code} @ {trade_date_idx}: {e}")
                continue
        
        return records
    
    async def _bulk_upsert_daily_data(self, records: List[Dict]) -> int:
        """
        批量插入或更新日线数据
        
        Args:
            records: 记录列表
            
        Returns:
            int: 插入/更新的记录数
        """
        if not records:
            return 0
        
        async with db_manager.get_session() as session:
            try:
                # 使用MySQL的INSERT ... ON DUPLICATE KEY UPDATE
                stmt = insert(StockDaily).values(records)
                
                # 定义更新策略：除主键外所有字段都更新
                update_dict = {
                    'open': stmt.inserted.open,
                    'high': stmt.inserted.high,
                    'low': stmt.inserted.low,
                    'close': stmt.inserted.close,
                    'vol': stmt.inserted.vol,
                    'amount': stmt.inserted.amount,
                    'source_batch_id': stmt.inserted.source_batch_id,
                    'updated_at': text('CURRENT_TIMESTAMP')
                }
                
                upsert_stmt = stmt.on_duplicate_key_update(**update_dict)
                result = await session.execute(upsert_stmt)
                await session.commit()
                
                # result.rowcount 在upsert中可能不准确，返回记录数
                return len(records)
                
            except Exception as e:
                await session.rollback()
                logger.error(f"批量插入日线数据失败: {e}")
                raise
    
    async def get_stock_daily_data(
        self,
        stock_code: str,
        start_date: date,
        end_date: date
    ) -> List[StockDaily]:
        """
        获取股票的日线数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            List[StockDaily]: 日线数据列表
        """
        code = stock_code.split('.')[0] if '.' in stock_code else stock_code
        
        async with db_manager.get_session() as session:
            stmt = text("""
                SELECT * FROM stock_daily
                WHERE code = :code
                AND trade_date BETWEEN :start_date AND :end_date
                ORDER BY trade_date DESC
            """)
            result = await session.execute(stmt, {
                'code': code,
                'start_date': start_date,
                'end_date': end_date
            })
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]
