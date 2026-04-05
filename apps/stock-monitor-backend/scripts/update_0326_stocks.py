#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新0326选股股票的今天(0402)价格和条件
"""

import sys
import os
import asyncio
import time
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

from loguru import logger


async def update_0326_stocks():
    """更新0326选股股票的今天价格和条件"""
    logger.info("=" * 60)
    logger.info("📊 更新0326选股股票的今天价格和条件")
    logger.info("=" * 60)
    
    # 初始化通达信
    from tqcenter import tq
    logger.info("[初始化] 连接通达信...")
    tq.initialize(__file__)
    
    # 导入服务
    from app.database import db_manager
    from sqlalchemy import select, and_
    from app.models.stock import WencaiStock, WencaiCrawlBatch
    from app.services.stock_data_manager import StockDataManager
    from app.services.volume_analysis_service import VolumeAnalysisService
    from app.services.feishu_client import FeishuClient
    
    await db_manager.initialize()
    
    # 获取0326的选股批次
    async with db_manager.get_session() as session:
        # 查询0326的批次
        stmt = select(WencaiCrawlBatch).where(
            WencaiCrawlBatch.query_date == date(2026, 3, 26)
        )
        result = await session.execute(stmt)
        batch = result.scalar_one_or_none()
        
        if not batch:
            logger.error("未找到0326的选股批次")
            return
        
        logger.info(f"找到0326批次: ID={batch.id}, 名称={batch.batch_name}")
        
        # 查询该批次的股票
        stmt2 = select(WencaiStock).where(
            WencaiStock.crawl_batch_id == batch.id,
            WencaiStock.is_active == True
        )
        result2 = await session.execute(stmt2)
        stocks_0326 = result2.scalars().all()
        
        logger.info(f"找到 {len(stocks_0326)} 只0326选股股票")
        
        # 获取今天(0403)的价格数据
        today = date(2026, 4, 3)
        stock_data_manager = StockDataManager(db_manager)
        
        updated_stocks = []
        for stock in stocks_0326:
            stock_code = stock.stock_code
            code = stock_code.split('.')[0] if '.' in stock_code else stock_code
            
            logger.info(f"\n📈 处理 {stock_code} {stock.stock_name}")
            
            try:
                # 获取今天数据
                daily_data = await stock_data_manager.get_stock_data(
                    code=code,
                    start_date=today,
                    end_date=today,
                    sync_if_missing=False
                )
                
                if daily_data and len(daily_data) > 0:
                    today_data = daily_data[-1]
                    logger.info(f"   今天收盘价: {today_data.close}")
                    logger.info(f"   今天成交量: {today_data.vol}")
                    
                    # 计算地量标签
                    tags = await VolumeAnalysisService.generate_daily_tags(
                        code=code,
                        target_date=today,
                        session=session
                    )
                    
                    # 检查是否满足各种条件
                    is_low_volume_5 = '5日地量' in tags
                    is_low_volume_10 = '10日地量' in tags
                    is_low_volume_20 = '20日地量' in tags
                    is_low_volume_30 = '30日地量' in tags
                    is_low_volume_60 = '60日地量' in tags
                    
                    logger.info(f"   5日地量: {is_low_volume_5}")
                    logger.info(f"   10日地量: {is_low_volume_10}")
                    logger.info(f"   20日地量: {is_low_volume_20}")
                    logger.info(f"   30日地量: {is_low_volume_30}")
                    logger.info(f"   60日地量: {is_low_volume_60}")
                    
                    updated_stocks.append({
                        'stock_code': code,
                        'stock_name': stock.stock_name,
                        'today_close': float(today_data.close),
                        'today_volume': float(today_data.vol),
                        'low_volume_5': is_low_volume_5,
                        'low_volume_10': is_low_volume_10,
                        'low_volume_20': is_low_volume_20,
                        'low_volume_30': is_low_volume_30,
                        'low_volume_60': is_low_volume_60,
                        'tags': tags
                    })
                else:
                    logger.warning(f"   未找到今天数据")
            except Exception as e:
                logger.error(f"   处理异常: {e}")
        
        # 更新飞书表格
        if updated_stocks:
            logger.info(f"\n📤 更新 {len(updated_stocks)} 只股票到飞书表格...")
            
            feishu_client = FeishuClient()
            date_timestamp = int(time.mktime(today.timetuple())) * 1000
            
            records = []
            for s in updated_stocks:
                record = {
                    "股票代码": s['stock_code'],
                    "股票名称": s['stock_name'],
                    "最新日期": "2026-04-02",  # 文本格式
                    "最新收盘价": s['today_close'],
                    "最新成交量": s['today_volume'],
                    "5日地量": s['low_volume_5'],
                    "10日地量": s['low_volume_10'],
                    "20日地量": s['low_volume_20'],
                    "30日地量": s['low_volume_30'],
                    "60日地量": s['low_volume_60'],
                    "备注": f"更新于0402, 标签: {', '.join(s['tags'])}"
                }
                records.append(record)
            
            # 批量插入
            result = feishu_client.add_records_to_bitable(records)
            logger.info(f"📊 更新结果: {result}")
        
        return updated_stocks


async def main():
    """主函数"""
    logger.info("🚀 开始更新0326股票数据")
    
    updated = await update_0326_stocks()
    
    logger.info("\n" + "=" * 60)
    logger.info(f"✅ 更新完成，共处理 {len(updated) if updated else 0} 只股票")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
