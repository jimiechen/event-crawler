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
from app.models.platform import PlatformConfig
from app.models.crawler import CrawlerTarget, CrawlerLoginStatus
from loguru import logger


async def test_realhead_crawler():
    """测试 realhead 爬虫"""
    
    # 创建数据库连接
    DATABASE_URL = "sqlite+aiosqlite:///./stock_monitor.db"
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # 创建数据库表
    from app.models.platform import PlatformConfig
    from app.models.crawler import CrawlerTarget, CrawlerLoginStatus
    async with engine.begin() as conn:
        await conn.run_sync(lambda conn: PlatformConfig.metadata.create_all(conn, checkfirst=True))
        await conn.run_sync(lambda conn: CrawlerTarget.metadata.create_all(conn, checkfirst=True))
        await conn.run_sync(lambda conn: CrawlerLoginStatus.metadata.create_all(conn, checkfirst=True))
        await conn.run_sync(lambda conn: TonghuashunStock.metadata.create_all(conn, checkfirst=True))
    
    # 初始化平台配置
    async with async_session_maker() as db:
        from app.services.platform_service import PlatformService
        platform_service = PlatformService(db)
        await platform_service.init_default_platforms()
    
    async with async_session_maker() as db:
        try:
            # 创建爬虫实例
            crawler = RealheadCrawler(db)
            
            # 测试1：抓取指定股票
            logger.info("=== 测试1：抓取指定股票 (000795) ===")
            result1 = await crawler.crawl(['000795'])
            logger.info(f"结果: {result1}")
            
            # 保存到数据库
            if result1.get('data'):
                from app.services.stock_service import StockService
                stock_service = StockService(db)
                for stock_data in result1['data']:
                    try:
                        await stock_service.create_or_update_stock_info({
                            'stock_code': stock_data.get('stock_code'),
                            'stock_name': stock_data.get('stock_name'),
                            'market': 'SZ' if stock_data.get('stock_code', '').startswith(('0', '2', '3')) else 'SH'
                        })
                        
                        # 保存到 tonghuashun_stocks 表
                        await stock_service.submit_stock_data([stock_data])
                        
                        logger.info(f"✅ 成功保存股票数据: {stock_data.get('stock_code')}")
                    except Exception as e:
                        logger.error(f"保存股票数据失败: {e}")
                        continue
            
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
