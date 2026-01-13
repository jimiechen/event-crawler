#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务调度服务
"""

import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from app.database import db_manager
from app.services.pattern_analysis_service import PatternAnalysisService

class SchedulerService:
    """定时任务调度服务"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.db_manager = db_manager
        self.is_running = False
        
    def start(self):
        """启动调度器"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
            
        logger.info("Starting scheduler...")
        
        # 1. 盘后积分更新（15:30）
        self.scheduler.add_job(
            self.run_post_market_update,
            CronTrigger(hour=15, minute=30),
            id="post_market_update",
            name="盘后积分更新",
            replace_existing=True
        )
        
        # 2. 每日验收测试（16:00）
        self.scheduler.add_job(
            self.run_daily_acceptance,
            CronTrigger(hour=16, minute=0),
            id="daily_acceptance",
            name="每日验收测试",
            replace_existing=True
        )
        
        # 3. 盘中实时监控检查（14:00-15:00，每5分钟）
        self.scheduler.add_job(
            self.run_realtime_monitor_check,
            CronTrigger(day_of_week='mon-fri', hour='14', minute='*/5'),
            id="realtime_monitor",
            name="盘中实时监控检查",
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info("Scheduler started successfully")

        # logger.info("Starting scheduler...")
        
        # # 1. 每日全量爬虫任务 (17:00)
        # self.scheduler.add_job(
        #     self.run_crawler_all,
        #     CronTrigger(hour=17, minute=0),
        #     id="daily_crawler_all",
        #     name="每日全量爬虫",
        #     replace_existing=True
        # )
        
        # # 2. 每日临时数据清洗 (00:00)
        # self.scheduler.add_job(
        #     self.run_temp_data_cleaning,
        #     CronTrigger(hour=0, minute=0),
        #     id="daily_temp_cleaning",
        #     name="每日临时数据清洗",
        #     replace_existing=True
        # )
        
        # # 3. 核心池监控 (每1分钟)
        # self.scheduler.add_job(
        #     self.run_pool_monitor,
        #     IntervalTrigger(minutes=1),
        #     id="core_pool_monitor",
        #     name="核心池监控",
        #     replace_existing=True
        # )
        
        # self.scheduler.start()
        # self.is_running = True
        # logger.info("Scheduler started successfully")

    def shutdown(self):
        """关闭调度器"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Scheduler shutdown")

    async def run_crawler_all(self):
        """执行全量爬虫任务"""
        logger.info("定时任务: 开始全量爬虫任务")
        try:
            from app.crawler.wencai_crawler import WencaiCrawler
            
            async with self.db_manager.get_session() as session:
                crawler = WencaiCrawler(session)
                
                # 构建查询语句
                # 动态获取昨天的日期
                today = datetime.now()
                yesterday = today - timedelta(days=1)
                
                d1 = today.strftime("%Y年%m月%d日")
                d2 = yesterday.strftime("%Y年%m月%d日")
                
                # 查询条件: 3倍量, 非北交/创业/科创/ST, 涨幅<13%, 收盘价<25
                # "2025年12月31日成交量是2025年12月30日成交量的2.5倍以上，非北交 非创业版，非科创版，非ST，概念 行业，2025年12月30日和2025年12月31日涨幅低于13%  收盘价低于25"
                
                query = f"{d1}成交量是{d2}成交量的2.5倍以上，非北交 非创业版，非科创版，非ST，概念 行业，{d2}和{d1}涨幅低于13% 收盘价低于25"
                
                logger.info(f"执行爬虫查询: {query}")
                
                result = await crawler.fetch_and_parse(query)
                
                if result.get("status") == "completed":
                    logger.info(f"爬虫任务完成，获取到 {result.get('success')} 条数据")
                    
                    # 触发形态筛选
                    await self.run_pattern_screening()
                else:
                    logger.error(f"爬虫任务失败: {result.get('error')}")

        except Exception as e:
            logger.error(f"Crawler task failed: {e}")
            # 不抛出异常，以免中断调度器
            
    async def run_pattern_screening(self):
        """执行缠论形态筛选"""
        logger.info("定时任务: 开始缠论形态筛选")
        try:
            async with self.db_manager.get_session() as session:
                service = PatternAnalysisService(session)
                result = await service.perform_screening()
                logger.info(f"形态筛选完成: {result}")
        except Exception as e:
            logger.error(f"Pattern screening failed: {e}")

    async def run_temp_data_cleaning(self):
        """执行临时数据清洗"""
        logger.info("定时任务: 开始临时数据清洗")
        try:
            async with self.db_manager.get_session() as session:
                service = PatternAnalysisService(session)
                # 默认保留3天，可从配置读取
                deleted = await service.clean_expired_data(retention_days=3)
                logger.info(f"临时数据清洗完成，删除了 {deleted} 条记录")
        except Exception as e:
            logger.error(f"Temp data cleaning failed: {e}")

    async def run_pool_monitor(self):
        """执行核心池监控"""
        # 简单判断是否在交易时间
        now = datetime.now()
        # 粗略判断: 9:30-11:30, 13:00-15:00
        is_trading = (
            (now.hour == 9 and now.minute >= 30) or
            (now.hour == 10) or
            (now.hour == 11 and now.minute <= 30) or
            (now.hour >= 13 and now.hour < 15)
        )
        
        if not is_trading:
            # logger.debug("非交易时间，跳过监控")
            return

        logger.info("定时任务: 执行核心池监控")
        try:
            from app.services.sse_service import sse_service
            from app.services.notification_service import notification_service
            
            async with self.db_manager.get_session() as session:
                service = PatternAnalysisService(session)
                
                # Get Core Pool
                from app.models.pattern_config import PatternStockPool
                from sqlalchemy import select
                
                stmt = select(PatternStockPool).where(PatternStockPool.status == 'core')
                result = await session.execute(stmt)
                core_stocks = result.scalars().all()
                
                for stock in core_stocks:
                    try:
                        # 检查地量
                        alert_result = await service.check_low_volume_alert(stock.stock_code)
                        if alert_result.get("is_low_vol"):
                            msg = f"核心池监控: {stock.stock_name}({stock.stock_code}) 触发地量提醒! 现量:{alert_result.get('current_vol')}"
                            logger.info(msg)
                            
                            # 1. SSE 推送 (前端)
                            await sse_service.broadcast("core_alert", {
                                "type": "low_volume",
                                "stock_code": stock.stock_code,
                                "stock_name": stock.stock_name,
                                "message": msg,
                                "data": alert_result,
                                "timestamp": datetime.now().isoformat()
                            })
                            
                            # 2. 系统通知 (桌面/日志)
                            await notification_service.send_alert(
                                title="地量提醒",
                                message=msg,
                                level="warning",
                                data=alert_result
                            )
                            
                    except Exception as e:
                        logger.error(f"Error monitoring stock {stock.code}: {e}")
        except Exception as e:
            logger.error(f"Pool monitor failed: {e}")
    
    async def run_post_market_update(self):
        """盘后积分更新任务"""
        logger.info("盘后任务: 开始积分更新")
        try:
            # 1. 同步最新日线数据
            await self._sync_latest_daily_data()
            
            # 2. 执行Pathway分析
            from app.services.volume_analysis_service import VolumeAnalysisService
            await VolumeAnalysisService.analyze_all_stocks(batch_size=10)
            
            # 3. 计算排名
            await self._calculate_rankings()
            
            logger.info("盘后任务完成")
        except Exception as e:
            logger.error(f"盘后任务失败: {e}")
    
    async def _sync_latest_daily_data(self):
        """同步最新日线数据"""
        from app.services.stock_data_manager import StockDataManager
        from app.models.stock import StockInfo
        from sqlalchemy import select
        
        # 获取所有活跃股票
        stmt = select(StockInfo.code).where(StockInfo.is_active == True)
        result = await self.db_manager.session.execute(stmt)
        codes = result.scalars().all()
        
        logger.info(f"开始同步 {len(codes)} 只活跃股票的日线数据")
        
        # 批量同步
        stock_data_manager = StockDataManager(self.db_manager)
        for code in codes:
            try:
                await stock_data_manager.sync_stock_daily(code)
            except Exception as e:
                logger.error(f"同步 {code} 日线数据失败: {e}")
                continue
        
        logger.info("日线数据同步完成")
    
    async def _calculate_rankings(self):
        """计算排名"""
        from app.models.stock_daily import StockScoreResult
        from sqlalchemy import select, update, func
        from datetime import date
        
        # 1. 计算当日积分排名
        stmt = select(
            StockScoreResult.code,
            StockScoreResult.trade_date,
            StockScoreResult.total_score,
            func.row_number().over(
                order_by=StockScoreResult.total_score.desc()
            ).label('ranking')
        ).where(
            StockScoreResult.trade_date == date.today()
        )
        result = await self.db_manager.session.execute(stmt)
        
        # 2. 更新排名
        for row in result:
            update_stmt = update(StockScoreResult).where(
                StockScoreResult.code == row.code,
                StockScoreResult.trade_date == row.trade_date
            ).values(ranking=row.ranking)
            await self.db_manager.session.execute(update_stmt)
        
        await self.db_manager.session.commit()
        logger.info("排名计算完成")
    
    async def run_realtime_monitor_check(self):
        """盘中实时监控检查（14:00-15:00）"""
        logger.info("盘中监控检查")
        # 这个任务主要用于检查是否有遗漏的数据
        # 实时预警主要依靠浏览器插件推送触发
    
    async def run_daily_acceptance(self):
        """每日验收测试（16:00）"""
        logger.info("定时任务: 开始每日验收测试")
        try:
            async with self.db_manager.get_session() as session:
                from app.services.daily_acceptance_service import daily_acceptance_service
                await daily_acceptance_service.run_daily_acceptance(session)
                logger.info("每日验收测试完成")
        except Exception as e:
            logger.error(f"每日验收测试失败: {e}")

# 全局单例
scheduler_service = SchedulerService()
