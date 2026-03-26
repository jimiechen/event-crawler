#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TDX数据同步服务
从通达信获取日K线数据，存入MySQL数据库
"""

import sys
from datetime import date, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from decimal import Decimal
from loguru import logger

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 添加通达信路径
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

import pandas as pd
from sqlalchemy import select, insert, update
from sqlalchemy.dialects.mysql import insert as mysql_insert

from app.database import db_manager
from app.models.stock_daily import StockDaily


class TdxDataSyncService:
    """
    TDX数据同步服务
    从通达信获取日K线数据并存储到MySQL
    """
    
    def __init__(self):
        """初始化服务"""
        self.tdx_client = None
        self._initialized = False
    
    def initialize_tdx(self) -> bool:
        """初始化通达信连接"""
        if self._initialized:
            return True
        
        try:
            from tqcenter import tq
            tq.initialize(__file__)
            self.tdx_client = tq
            self._initialized = True
            logger.info("✅ 通达信连接初始化成功")
            return True
        except Exception as e:
            logger.error(f"❌ 通达信连接失败: {e}")
            return False
    
    def _get_all_stock_codes(self) -> List[str]:
        """获取所有A股股票代码"""
        stock_list = []
        
        # 深市主板
        for i in range(1, 5000):
            stock_list.append(f"{i:06d}.SZ")
        
        # 中小板
        for i in range(2001, 3000):
            stock_list.append(f"{i:06d}.SZ")
        
        # 创业板
        for i in range(300001, 302000):
            stock_list.append(f"{i:06d}.SZ")
        
        # 沪市主板
        for i in range(600000, 605000):
            stock_list.append(f"{i:06d}.SH")
        
        # 科创板
        for i in range(688001, 690000):
            stock_list.append(f"{i:06d}.SH")
        
        logger.info(f"生成股票列表: {len(stock_list)} 只")
        return stock_list
    
    def _fetch_daily_data_from_tdx(self, 
                                   stock_codes: List[str],
                                   trade_date: date,
                                   days: int = 5) -> List[Dict]:
        """
        从通达信获取日K线数据
        
        Args:
            stock_codes: 股票代码列表
            stock_codes: 股票代码列表
            trade_date: 交易日期
            days: 获取天数
            
        Returns:
            List[Dict]: 日K线数据列表
        """
        # 计算日期范围
        end_date = trade_date
        start_date = trade_date - timedelta(days=days)
        
        logger.info(f"从通达信获取数据: {start_date} 至 {end_date}")
        logger.info(f"股票数量: {len(stock_codes)}")
        
        try:
            # 获取市场数据
            data = self.tdx_client.get_market_data(
                field_list=['Open', 'Close', 'High', 'Low', 'Volume', 'Amount'],
                stock_list=stock_codes,
                period='1d',
                start_time=start_date.strftime('%Y%m%d'),
                end_time=end_date.strftime('%Y%m%d'),
                dividend_type='front'
            )
            
            if not data or 'Close' not in data:
                logger.error("获取市场数据失败")
                return []
            
            # 转换数据格式
            results = []
            close_df = data['Close']
            volume_df = data['Volume']
            
            # 获取其他字段
            open_df = data.get('Open')
            high_df = data.get('High')
            low_df = data.get('Low')
            amount_df = data.get('Amount')
            
            # 遍历每只股票
            for stock_code in close_df.columns:
                try:
                    # 获取最近一天的数据
                    close_row = close_df[stock_code]
                    volume_row = volume_df[stock_code]
                    
                    if len(close_row) < 2:
                        continue
                    
                    # 取最后一条（最新数据）
                    today_close = float(close_row.iloc[-1])
                    prev_close = float(close_row.iloc[-2])
                    today_volume = int(volume_row.iloc[-1])
                    prev_volume = int(volume_row.iloc[-2])
                    
                    # 获取OHLC数据
                    today_open = float(open_df[stock_code].iloc[-1]) if open_df is not None else today_close
                    today_high = float(high_df[stock_code].iloc[-1]) if high_df is not None else today_close
                    today_low = float(low_df[stock_code].iloc[-1]) if low_df is not None else today_close
                    today_amount = float(amount_df[stock_code].iloc[-1]) if amount_df is not None else 0
                    
                    # 计算量比
                    volume_ratio = today_volume / prev_volume if prev_volume > 0 else 0
                    
                    # 获取日期
                    trade_date_str = close_row.index[-1]
                    
                    results.append({
                        'code': stock_code,
                        'trade_date': trade_date_str,
                        'open': Decimal(str(today_open)),
                        'close': Decimal(str(today_close)),
                        'high': Decimal(str(today_high)),
                        'low': Decimal(str(today_low)),
                        'vol': today_volume,
                        'amount': Decimal(str(today_amount)),
                        'volume_ratio': Decimal(str(round(volume_ratio, 4))),
                    })
                    
                except Exception as e:
                    logger.warning(f"处理股票 {stock_code} 数据失败: {e}")
                    continue
            
            logger.info(f"成功获取 {len(results)} 条数据")
            return results
            
        except Exception as e:
            logger.error(f"从通达信获取数据失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def sync_daily_data(self, trade_date: date, batch_size: int = 100) -> Dict[str, Any]:
        """
        同步日K线数据到MySQL
        
        Args:
            trade_date: 交易日期
            batch_size: 每批处理的股票数量
            
        Returns:
            Dict: 同步结果统计
        """
        if not self.initialize_tdx():
            return {
                "status": "failed",
                "reason": "通达信初始化失败"
            }
        
        logger.info(f"\n{'='*60}")
        logger.info(f"开始同步日K线数据: {trade_date}")
        logger.info(f"{'='*60}\n")
        
        # 确保数据库连接
        if not db_manager._initialized:
            await db_manager.initialize()
        
        # 获取股票列表
        stock_codes = self._get_all_stock_codes()
        
        # 统计
        total_stocks = len(stock_codes)
        success_count = 0
        skip_count = 0
        error_count = 0
        
        # 分批处理
        for i in range(0, total_stocks, batch_size):
            batch_codes = stock_codes[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_stocks + batch_size - 1) // batch_size
            
            logger.info(f"\n处理批次 {batch_num}/{total_batches}: {len(batch_codes)} 只股票")
            
            # 从通达信获取数据
            daily_data = self._fetch_daily_data_from_tdx(batch_codes, trade_date, days=5)
            
            if not daily_data:
                logger.warning(f"批次 {batch_num} 无数据")
                continue
            
            # 存储到数据库
            try:
                async with db_manager.get_session() as session:
                    for record in daily_data:
                        try:
                            # 转换日期格式
                            trade_date_val = record['trade_date']
                            if isinstance(trade_date_val, str):
                                from datetime import datetime
                                trade_date_dt = datetime.strptime(trade_date_val[:10], '%Y-%m-%d').date()
                            else:
                                trade_date_dt = trade_date_val.date() if hasattr(trade_date_val, 'date') else trade_date_val
                            
                            # 创建或更新记录
                            stmt = mysql_insert(StockDaily).values(
                                code=record['code'],
                                trade_date=trade_date_dt,
                                open=record['open'],
                                close=record['close'],
                                high=record['high'],
                                low=record['low'],
                                vol=record['vol'],
                                amount=record['amount'],
                                volume_ratio=record.get('volume_ratio')
                            )
                            
                            # ON DUPLICATE KEY UPDATE
                            stmt = stmt.on_duplicate_key_update(
                                open=stmt.inserted.open,
                                close=stmt.inserted.close,
                                high=stmt.inserted.high,
                                low=stmt.inserted.low,
                                vol=stmt.inserted.vol,
                                amount=stmt.inserted.amount,
                                volume_ratio=stmt.inserted.volume_ratio
                            )
                            
                            await session.execute(stmt)
                            success_count += 1
                            
                        except Exception as e:
                            logger.warning(f"存储记录失败: {e}")
                            error_count += 1
                    
                    await session.commit()
                    logger.info(f"批次 {batch_num} 完成: 成功 {len(daily_data)}, 失败 {error_count}")
                    
            except Exception as e:
                logger.error(f"批次 {batch_num} 数据库操作失败: {e}")
                error_count += len(daily_data)
        
        result = {
            "status": "success",
            "trade_date": str(trade_date),
            "total_stocks": total_stocks,
            "success_count": success_count,
            "skip_count": skip_count,
            "error_count": error_count
        }
        
        logger.info(f"\n{'='*60}")
        logger.info(f"数据同步完成")
        logger.info(f"交易日期: {trade_date}")
        logger.info(f"总股票数: {total_stocks}")
        logger.info(f"成功同步: {success_count}")
        logger.info(f"跳过: {skip_count}")
        logger.info(f"失败: {error_count}")
        logger.info(f"{'='*60}\n")
        
        return result
    
    async def get_daily_data_from_db(self, trade_date: date) -> List[Dict]:
        """
        从数据库获取日K线数据
        
        Args:
            trade_date: 交易日期
            
        Returns:
            List[Dict]: 日K线数据列表
        """
        if not db_manager._initialized:
            await db_manager.initialize()
        
        try:
            async with db_manager.get_session() as session:
                stmt = select(StockDaily).where(StockDaily.trade_date == trade_date)
                result = await session.execute(stmt)
                records = result.scalars().all()
                
                return [
                    {
                        'code': r.code,
                        'trade_date': r.trade_date,
                        'open': float(r.open) if r.open else 0,
                        'close': float(r.close) if r.close else 0,
                        'high': float(r.high) if r.high else 0,
                        'low': float(r.low) if r.low else 0,
                        'vol': r.vol or 0,
                        'amount': float(r.amount) if r.amount else 0,
                        'volume_ratio': float(r.volume_ratio) if r.volume_ratio else 0
                    }
                    for r in records
                ]
        except Exception as e:
            logger.error(f"从数据库获取数据失败: {e}")
            return []


async def main():
    """测试函数"""
    service = TdxDataSyncService()
    
    # 测试日期
    trade_date = date(2026, 3, 25)
    
    # 执行同步
    result = await service.sync_daily_data(trade_date)
    
    print(f"\n同步结果: {result}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
