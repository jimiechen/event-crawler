#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.monitor_engine import monitor_engine
from app.services.stock_pool_service import stock_pool_service
from app.config.logging import setup_logging, get_logger

# 配置日志
setup_logging()
logger = get_logger("QuantMonitor")

async def daily_pool_refresh():
    """每日股票池刷新任务"""
    logger.info("开始每日股票池刷新...")
    try:
        # 示例策略：量比大于2，涨幅大于2%
        query = "量比大于2, 涨幅大于2%, 上市时间大于1年"
        result = await stock_pool_service.refresh_pool_by_wencai(query, priority=8)
        logger.info(f"股票池刷新结果: {result}")
    except Exception as e:
        logger.error(f"股票池刷新失败: {e}")

async def scheduler_loop():
    """简单的调度循环"""
    logger.info("启动定时调度器...")
    
    # 上次执行日期
    last_run_date = None
    
    while True:
        now = datetime.now()
        
        # 设定每天 09:10 执行选股
        target_hour = 9
        target_minute = 10
        
        # 如果时间匹配且今天未执行
        if (now.hour == target_hour and now.minute >= target_minute) and \
           (last_run_date is None or last_run_date != now.date()):
            
            await daily_pool_refresh()
            last_run_date = now.date()
            
        # 每分钟检查一次
        await asyncio.sleep(60)

async def main():
    logger.info("正在启动量化监控系统...")
    
    # 1. 启动监控引擎 (后台运行)
    monitor_task = asyncio.create_task(monitor_engine.start())
    
    # 2. 启动调度器 (后台运行)
    scheduler_task = asyncio.create_task(scheduler_loop())
    
    # 3. (可选) 启动时立即执行一次刷新，方便调试
    if os.getenv('RUN_ON_STARTUP', 'false').lower() == 'true':
        await daily_pool_refresh()
    
    logger.info("系统启动完成，按 Ctrl+C 停止")
    
    try:
        # 等待所有任务
        await asyncio.gather(monitor_task, scheduler_task)
    except asyncio.CancelledError:
        logger.info("任务被取消")
    except KeyboardInterrupt:
        logger.info("接收到停止信号")
    finally:
        await monitor_engine.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
