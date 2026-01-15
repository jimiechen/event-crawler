#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试获取昨天的问财数据
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import db_manager
from app.crawler.wencai_crawler import WencaiCrawler
from app.services.wencai_service import WencaiService
from loguru import logger

async def test_fetch_yesterday_wencai():
    """测试获取昨天的问财数据"""
    
    # 初始化数据库
    await db_manager.initialize()
    
    # 创建数据库会话
    async with db_manager.get_session() as session:
        try:
            # 创建爬虫实例
            crawler = WencaiCrawler(session)
            wencai_service = WencaiService(session)
            
            # 昨天的查询条件（参考 fetch_wencai_daily.py）
            # 2026年01月13日成交量是2026年01月12日成交量的2.5倍以上，非北交，非创业板，非科创版，非ST，概念，行业，2026年01月12日和2026年01月13日涨幅低于13%，收盘价低于25
            query = "2026年01月13日成交量是2026年01月12日成交量的2.5倍以上，非北交，非创业板，非科创版，非ST，概念，行业，2026年01月12日和2026年01月13日涨幅低于13%，收盘价低于25"
            
            logger.info(f"查询条件: {query}")
            
            # 创建批次
            batch_name = "FETCH_20260113"
            batch_id = await wencai_service.create_crawl_batch(
                batch_name=batch_name,
                crawl_url=f"http://www.iwencai.com/stockpick/search?w={query}",
                query_string=query
            )
            
            logger.info(f"创建批次: {batch_id}")
            
            # 执行爬取
            result = await crawler.fetch_and_parse(query=query, batch_name=batch_name)
            
            logger.info(f"爬取结果: {result}")
            
            if result.get('status') == 'success':
                stocks = result.get('stocks', [])
                logger.info(f"成功获取 {len(stocks)} 只股票")
                
                # 检查是否有 603601
                found_603601 = False
                for stock in stocks:
                    stock_code = stock.get('stock_code', '')
                    if '603601' in stock_code:
                        found_603601 = True
                        logger.success(f"🎯 找到 603601: {stock.get('stock_name')}")
                        break
                
                if not found_603601:
                    logger.warning("⚠️ 未找到 603601 在结果中")
                
                # 保存数据到数据库
                success_count, failed_count, errors = await wencai_service.save_wencai_stocks(batch_id, stocks)
                
                logger.info(f"保存结果: 成功 {success_count}, 失败 {failed_count}")
                
                if errors:
                    logger.error(f"错误: {errors}")
                
                # 处理批次数据
                await wencai_service.process_batch_data(batch_id)
                
                # 更新批次状态
                await wencai_service.update_batch_status(
                    batch_id, 
                    'completed', 
                    len(stocks), 
                    success_count, 
                    failed_count, 
                    '; '.join(errors) if errors else None
                )
                
                logger.info(f"批次 {batch_id} 已完成")
                
                # 查询数据库验证
                from sqlalchemy import select, text
                stmt = text("SELECT COUNT(*) FROM wencai_stocks WHERE crawl_batch_id = :batch_id")
                result = await session.execute(stmt, {"batch_id": str(batch_id)})
                count = result.scalar()
                
                logger.info(f"数据库中找到 {count} 条记录")
                
                # 查询最新数据
                stmt = text("SELECT stock_code, stock_name, current_price, volume, created_at FROM wencai_stocks ORDER BY created_at DESC LIMIT 5")
                result = await session.execute(stmt)
                latest_stocks = result.fetchall()
                
                logger.info("\n=== 最新 5 条记录 ===")
                for stock in latest_stocks:
                    logger.info(f"  {stock[0]} - {stock[1]} - 价格: {stock[2]} - 成交量: {stock[3]} - 时间: {stock[4]}")
                
            else:
                logger.error(f"爬取失败: {result.get('message')}")
        
        except Exception as e:
            logger.error(f"测试失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fetch_yesterday_wencai())
