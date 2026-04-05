#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日复盘任务执行脚本
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 添加通达信Python模块路径
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

import asyncio
from datetime import date
from loguru import logger

# 初始化通达信
from tqcenter import tq

async def run_daily_review():
    """执行每日复盘任务"""
    
    logger.info("=" * 60)
    logger.info("📊 开始执行每日复盘任务")
    logger.info("=" * 60)
    
    try:
        # 初始化通达信连接
        logger.info("[初始化] 连接通达信客户端...")
        tq.initialize(__file__)
        logger.info("✅ 通达信连接成功")
        
        # 导入复盘服务
        from app.services.daily_review_service import DailyReviewService
        
        # 创建复盘服务（直接使用 tq 作为客户端）
        review_service = DailyReviewService(tdx_client=tq)
        
        # 执行复盘
        trade_date = date.today()
        logger.info(f"[执行] 复盘日期: {trade_date}")
        
        result = await review_service.update_stock_pool_daily_data(trade_date)
        
        # 输出结果
        logger.info("=" * 60)
        logger.info("📋 复盘任务执行结果:")
        logger.info("=" * 60)
        
        if result['status'] == 'success':
            logger.info(f"✅ 状态: 成功")
            logger.info(f"📅 交易日期: {result['trade_date']}")
            logger.info(f"📦 选股批次: {result['batches_count']} 个")
            logger.info(f"📈 股票总数: {result['stocks_count']} 只")
            logger.info(f"💾 日线同步: {result['synced_count']} 条")
            logger.info(f"🎯 得分更新: {result.get('score_updated', 0)} 只")
            logger.info(f"📉 地量股票: {len(result.get('low_volume_stocks', []))} 只")
            
            if result.get('low_volume_stocks'):
                logger.info("📉 地量股票列表:")
                for stock_code, tags in result['low_volume_stocks']:
                    logger.info(f"   - {stock_code}: {tags}")
        else:
            logger.error(f"❌ 状态: 失败")
            logger.error(f"错误信息: {result.get('error', '未知错误')}")
        
        logger.info("=" * 60)
        logger.info("🎉 复盘任务完成")
        logger.info("=" * 60)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 复盘任务执行失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    asyncio.run(run_daily_review())
