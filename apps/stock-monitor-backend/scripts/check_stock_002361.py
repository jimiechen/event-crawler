#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
排查神剑股份(002361) 0327日K线数据来源
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import date
from loguru import logger

async def check_stock_data():
    """检查股票数据来源"""
    
    from app.database import db_manager
    from sqlalchemy import select, desc
    from app.models.stock_daily import StockDaily
    from app.models.stock import WencaiStock, WencaiCrawlBatch
    
    logger.info("=" * 60)
    logger.info("🔍 排查神剑股份(002361)数据来源")
    logger.info("=" * 60)
    
    await db_manager.initialize()
    
    async with db_manager.get_session() as session:
        # 1. 查询stock_daily表中的数据
        logger.info("\n[1] 查询 stock_daily 表数据...")
        stmt = select(StockDaily).where(
            StockDaily.code == "002361"
        ).order_by(desc(StockDaily.trade_date))
        
        result = await session.execute(stmt)
        records = result.scalars().all()
        
        logger.info(f"   找到 {len(records)} 条记录")
        
        for record in records[:10]:  # 显示最近10条
            logger.info(f"   - 日期: {record.trade_date}, "
                       f"开盘: {record.open}, "
                       f"收盘: {record.close}, "
                       f"成交量: {record.vol}, "
                       f"来源批次: {record.source_batch_id}")
        
        # 2. 查询是否在选股结果中
        logger.info("\n[2] 查询是否在选股结果中...")
        stmt2 = select(WencaiStock).where(
            WencaiStock.stock_code == "002361"
        ).order_by(desc(WencaiStock.created_at))
        
        result2 = await session.execute(stmt2)
        wencai_records = result2.scalars().all()
        
        logger.info(f"   找到 {len(wencai_records)} 条选股记录")
        
        for record in wencai_records[:5]:
            logger.info(f"   - 批次ID: {record.crawl_batch_id}, "
                       f"创建时间: {record.created_at}, "
                       f"是否活跃: {record.is_active}")
        
        # 3. 查询相关批次信息
        if wencai_records:
            logger.info("\n[3] 查询相关批次信息...")
            batch_ids = [r.crawl_batch_id for r in wencai_records[:5]]
            
            stmt3 = select(WencaiCrawlBatch).where(
                WencaiCrawlBatch.id.in_(batch_ids)
            )
            
            result3 = await session.execute(stmt3)
            batches = result3.scalars().all()
            
            for batch in batches:
                logger.info(f"   - 批次ID: {batch.id}, "
                           f"日期: {batch.query_date}, "
                           f"来源: {batch.source}, "
                           f"板块: {batch.sector_code}")
        
        # 4. 检查0327当天的数据详情
        logger.info("\n[4] 检查 2026-03-27 当天数据详情...")
        stmt4 = select(StockDaily).where(
            StockDaily.code == "002361",
            StockDaily.trade_date == date(2026, 3, 27)
        )
        
        result4 = await session.execute(stmt4)
        record_0327 = result4.scalar_one_or_none()
        
        if record_0327:
            logger.info(f"   ✅ 找到 0327 数据:")
            logger.info(f"      - 股票代码: {record_0327.code}")
            logger.info(f"      - 交易日期: {record_0327.trade_date}")
            logger.info(f"      - 开盘价: {record_0327.open}")
            logger.info(f"      - 收盘价: {record_0327.close}")
            logger.info(f"      - 最高价: {record_0327.high}")
            logger.info(f"      - 最低价: {record_0327.low}")
            logger.info(f"      - 成交量: {record_0327.vol}")
            logger.info(f"      - 成交额: {record_0327.amount}")
            logger.info(f"      - 来源批次: {record_0327.source_batch_id}")
            logger.info(f"      - 创建时间: {record_0327.created_at}")
            logger.info(f"      - 更新时间: {record_0327.updated_at}")
        else:
            logger.info("   ❌ 未找到 0327 数据")
    
    await db_manager.close()
    
    logger.info("\n" + "=" * 60)
    logger.info("🔍 排查完成")
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(check_stock_data())
