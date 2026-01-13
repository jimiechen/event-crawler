#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Realhead 爬虫简单测试
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.crawler.realhead_crawler import RealheadCrawler
from app.models.stock import TonghuashunStock
from loguru import logger


async def test_realhead_crawler():
    """测试 realhead 爬虫"""
    
    # 创建数据库连接
    DATABASE_URL = "sqlite+aiosqlite:///./stock_monitor.db"
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_maker() as db:
        try:
            # 创建爬虫实例
            crawler = RealheadCrawler(db)
            
            # 测试1：抓取指定股票
            logger.info("=== 测试1：抓取指定股票 (000795) ===")
            result1 = await crawler.crawl(['000795'])
            logger.info(f"结果: {result1}")
            
            # 测试2：抓取自选股
            logger.info("\n=== 测试2：抓取自选股 ===")
            result2 = await crawler.crawl([])
            logger.info(f"结果: {result2}")
            
            # 验证数据库
            logger.info("\n=== 验证数据库 ===")
            from sqlalchemy import select
            stmt = select(TonghuashunStock).where(TonghuashunStock.code == '000795').order_by(TonghuashunStock.created_at.desc()).limit(5)
            result = await db.execute(stmt)
            stocks = result.scalars().all()
            
            logger.info(f"数据库中找到 {len(stocks)} 条 000795 的记录")
            for stock in stocks:
                logger.info(f"  - {stock.timestamp}: {stock.current_price}, {stock.volume}")
            
            logger.info("\n✅ 测试完成！")
            
        except Exception as e:
            logger.error(f"测试失败: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_realhead_crawler())
