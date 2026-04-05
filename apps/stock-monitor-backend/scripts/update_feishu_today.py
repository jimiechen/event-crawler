#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新今天选股结果到飞书表格
并更新0326历史数据的今天价格
"""

import sys
import os
import time
import asyncio
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

from loguru import logger


async def update_today_selection():
    """更新今天选股结果"""
    logger.info("=" * 60)
    logger.info("📊 更新今天(0402)选股结果到飞书表格")
    logger.info("=" * 60)
    
    # 初始化通达信
    from tqcenter import tq
    logger.info("[初始化] 连接通达信...")
    tq.initialize(__file__)
    
    # 导入服务
    from app.services.tdx_selection_workflow import TdxSelectionWorkflow
    from app.services.feishu_client import FeishuClient
    
    # 初始化飞书客户端
    feishu_client = FeishuClient()
    
    # 创建选股服务
    selection_service = TdxSelectionWorkflow(
        tdx_client=tq,
        feishu_client=feishu_client
    )
    
    # 今天日期
    trade_date = date(2026, 4, 3)
    sector_code = "3BL260402"
    
    logger.info(f"\n📅 执行选股: {trade_date}")
    logger.info(f"📁 板块代码: {sector_code}")
    
    # 执行选股（跳过截图）
    result = await selection_service.execute_selection(
        trade_date=trade_date,
        sector_code=sector_code,
        skip_screenshot=True
    )
    
    if result['status'] == 'success':
        logger.info(f"✅ 选股完成: 选中 {result.get('selected_count', 0)} 只")
    else:
        logger.error(f"❌ 选股失败: {result.get('reason', '未知错误')}")
    
    return result


async def update_0326_stocks():
    """更新0326选股股票的今天价格"""
    logger.info("\n" + "=" * 60)
    logger.info("📊 更新0326选股股票的今天价格")
    logger.info("=" * 60)
    
    # 初始化通达信
    from tqcenter import tq
    logger.info("[初始化] 连接通达信...")
    tq.initialize(__file__)
    
    # 导入服务
    from app.database import db_manager
    from sqlalchemy import select, desc
    from app.models.stock import WencaiStock
    from app.services.stock_data_manager import StockDataManager
    from app.services.volume_analysis_service import VolumeAnalysisService
    
    await db_manager.initialize()
    
    # 获取0326的选股结果
    async with db_manager.get_session() as session:
        # 查询0326选中的股票
        stmt = select(WencaiStock).where(
            WencaiStock.created_at >= date(2026, 3, 26),
            WencaiStock.created_at < date(2026, 3, 27)
        )
        
        result = await session.execute(stmt)
        stocks_0326 = result.scalars().all()
        
        logger.info(f"找到 {len(stocks_0326)} 只0326选股股票")
        
        # 获取今天的价格数据
        today = date(2026, 4, 3)
        stock_data_manager = StockDataManager(db_manager)
        
        updated_stocks = []
        for stock in stocks_0326:
            stock_code = stock.stock_code
            code = stock_code.split('.')[0] if '.' in stock_code else stock_code
            
            logger.info(f"\n📈 更新 {stock_code} {stock.stock_name}")
            
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
                
                updated_stocks.append({
                    'stock_code': stock_code,
                    'stock_name': stock.stock_name,
                    'today_close': today_data.close,
                    'today_volume': today_data.vol,
                    'tags': tags
                })
            else:
                logger.warning(f"   未找到今天数据")
        
        return updated_stocks


async def main():
    """主函数"""
    logger.info("🚀 开始更新飞书表格数据")
    
    # 1. 更新今天选股结果
    today_result = await update_today_selection()
    
    # 2. 更新0326股票今天价格
    # updated_0326 = await update_0326_stocks()
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ 更新完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
