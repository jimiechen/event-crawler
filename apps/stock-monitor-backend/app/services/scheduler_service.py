#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务调度服务
"""

import asyncio
from datetime import datetime, timedelta, date as datetime_date
from typing import Dict, Any, List, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
import httpx

from app.database import db_manager
from app.services.pattern_analysis_service import PatternAnalysisService

class SchedulerService:
    """定时任务调度服务"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.db_manager = db_manager
        self.is_running = False
        self.api_base_url = "http://localhost:8000"
        self.http_client = None
        
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
        
        # 4. 【新增】每日问财爬虫（17:00）
        self.scheduler.add_job(
            self.run_wencai_daily_crawler,
            CronTrigger(hour=17, minute=0),
            id="wencai_daily_crawler",
            name="每日问财爬虫",
            replace_existing=True
        )

        # 5. 【新增】每日AI复盘 (15:40) - 在盘后数据更新后
        self.scheduler.add_job(
            self.run_daily_ai_review,
            CronTrigger(hour=15, minute=40),
            id="daily_ai_review",
            name="每日AI复盘",
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info("Scheduler started successfully")
        
        # Load generic tasks
        asyncio.create_task(self.refresh_all_tasks())

    async def refresh_all_tasks(self):
        """刷新所有通用任务"""
        from app.services.generic_task_service import GenericTaskService
        from app.services.task_executor import task_executor
        
        async with self.db_manager.get_session() as session:
            service = GenericTaskService(session)
            tasks = await service.get_active_tasks()
            
            logger.info(f"Loading {len(tasks)} generic tasks from DB...")
            
            for task in tasks:
                self._schedule_generic_task(task)

    def _schedule_generic_task(self, task):
        from app.services.task_executor import task_executor
        
        job_id = f"generic_task_{task.id}"
        
        try:
            trigger = CronTrigger.from_crontab(task.cron_expression)
            self.scheduler.add_job(
                task_executor.execute_generic_task,
                trigger,
                args=[task.id],
                id=job_id,
                name=task.name,
                replace_existing=True
            )
            logger.info(f"Scheduled generic task {task.id}: {task.name} ({task.cron_expression})")
        except Exception as e:
            logger.error(f"Failed to schedule task {task.id}: {e}")

    async def refresh_task(self, task_id: int):
        from app.services.generic_task_service import GenericTaskService
        
        async with self.db_manager.get_session() as session:
            service = GenericTaskService(session)
            task = await service.get_generic_task_by_id(task_id)
            
            job_id = f"generic_task_{task_id}"
            
            if not task or not task.is_active:
                if self.scheduler.get_job(job_id):
                    self.scheduler.remove_job(job_id)
                    logger.info(f"Removed generic task {task_id}")
                return
            
            self._schedule_generic_task(task)

    def remove_task(self, task_id: int):
        job_id = f"generic_task_{task_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed generic task {task_id}")

    # Legacy methods below
        
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
        
        # 关闭HTTP客户端
        if self.http_client:
            asyncio.create_task(self.http_client.aclose())
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self.http_client is None or self.http_client.is_closed:
            self.http_client = httpx.AsyncClient(timeout=60.0)
        return self.http_client
    
    async def _call_api(self, endpoint: str, params: dict = None) -> dict:
        """调用API端点"""
        client = await self._get_http_client()
        url = f"{self.api_base_url}{endpoint}"
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API调用失败: {endpoint}, 错误: {e}")
            raise

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
            today_str = datetime_date.today().strftime("%Y-%m-%d")
            
            # 1. 同步最新日线数据（调用API）
            endpoint = f"/api/v1/stock/sync/tushare/{today_str}/0"
            sync_result = await self._call_api(endpoint)
            logger.info(f"数据同步完成: {sync_result}")
            
            # 2. 执行Pathway分析（调用API）
            endpoint = f"/api/v1/scores/calculate/{today_str}/0"
            score_result = await self._call_api(endpoint)
            logger.info(f"评分计算完成: {score_result}")
            
            # 3. 计算排名（调用API）
            endpoint = f"/api/v1/ranking/calculate/{today_str}"
            ranking_result = await self._call_api(endpoint)
            logger.info(f"排名计算完成: {ranking_result}")
            
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
    
    async def run_wencai_daily_crawler(self):
        """每日问财爬虫任务（爬取前一天的数据）"""
        logger.info("定时任务: 开始每日问财爬虫")
        
        try:
            # 获取昨天的日期
            yesterday = datetime_date.today() - timedelta(days=1)
            yesterday_str = yesterday.strftime("%Y-%m-%d")
            
            # 调用API端点
            endpoint = f"/api/v1/wencai/crawler/{yesterday_str}/1"
            result = await self._call_api(endpoint)
            
            logger.info(f"每日问财爬虫完成: {result}")
            
        except Exception as e:
            logger.error(f"每日问财爬虫失败: {e}")
    
    async def run_wencai_date_range_crawler(self, start_date: datetime_date, end_date: datetime_date) -> Dict[str, Any]:
        """
        执行日期范围爬虫任务
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            爬取结果统计
        """
        logger.info(f"开始日期范围爬虫: {start_date} 到 {end_date}")
        
        # 生成日期列表
        date_list = []
        current_date = start_date
        
        while current_date <= end_date:
            # 跳过周末
            if current_date.weekday() < 5:  # 周一到周五
                date_list.append(current_date)
                current_date += timedelta(days=1)
        
        logger.info(f"共 {len(date_list)} 个交易日需要爬取")
        
        # 批量爬取
        from app.crawler.wencai_crawler import WencaiCrawler
        
        success_count = 0
        failed_count = 0
        
        for crawl_date in date_list:
            try:
                async with self.db_manager.get_session() as session:
                    crawler = WencaiCrawler(session)
                    
                    # 使用新的日期参数方式执行爬取
                    logger.info(f"执行爬虫查询，日期: {crawl_date}")
                    
                    # 执行爬取（使用target_date自动生成查询条件）
                    result = await crawler.fetch_and_parse(
                        query=None,
                        batch_name=f"AutoCrawl_{crawl_date.strftime('%Y%m%d')}",
                        target_stock_code=None,
                        target_date=crawl_date
                    )
                    
                    if result.get("status") == "completed":
                        success_count += 1
                        logger.info(f"✅ {crawl_date} 爬取成功: {result.get('success')} 条")
                    else:
                        failed_count += 1
                        logger.error(f"❌ {crawl_date} 爬取失败: {result.get('error')}")
            
            except Exception as e:
                failed_count += 1
                logger.error(f"❌ {crawl_date} 爬取异常: {e}")
        
        logger.info(f"日期范围爬虫完成: 成功 {success_count}, 失败 {failed_count}")
        
        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "total_count": len(date_list)
        }
    
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

    async def _init_default_tasks(self):
        """初始化默认定时任务"""
        default_tasks = [
            {
                "name": "每日AI复盘",
                "task_type": "daily_ai_review",
                "cron_expression": "40 15 * * *",
                "description": "每日收盘后自动分析核心池股票",
                "is_active": True
            },
            {
                "name": "盘后积分更新",
                "task_type": "post_market_update",
                "cron_expression": "30 15 * * *",
                "description": "更新股票评分和排名",
                "is_active": True
            }
        ]
        
        async with self.db_manager.get_session() as session:
            for task_data in default_tasks:
                stmt = select(ScheduledTask).where(ScheduledTask.task_type == task_data["task_type"])
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if not existing:
                    new_task = ScheduledTask(**task_data)
                    session.add(new_task)
                    logger.info(f"Initialized default task: {task_data['name']}")
            await session.commit()

    async def run_daily_ai_review(self):
        """每日AI复盘任务"""
        logger.info("定时任务: 开始每日AI复盘")
        
        # 1. Update Task Status (Running)
        task_id = None
        try:
            async with self.db_manager.get_session() as session:
                 stmt = select(ScheduledTask).where(ScheduledTask.task_type == 'daily_ai_review')
                 result = await session.execute(stmt)
                 task = result.scalar_one_or_none()
                 if task:
                     task.last_run_at = datetime.now()
                     task.last_run_status = "running"
                     await session.commit()
                     task_id = task.id
        except Exception as e:
            logger.warning(f"Failed to update task status (start): {e}")

        try:
            from app.services.ai_decision_service import AIDecisionService, AIDecisionConfig
            from app.config.settings import get_settings
            from app.models.pattern_config import PatternStockPool
            from sqlalchemy import select
            
            settings = get_settings()
            if not settings.deepseek_api_key:
                logger.warning("DeepSeek API Key未配置，跳过AI复盘")
                return

            async with self.db_manager.get_session() as session:
                # 1. Get target stocks (Core Pool)
                stmt = select(PatternStockPool).where(PatternStockPool.status == 'core')
                result = await session.execute(stmt)
                core_stocks = result.scalars().all()
                
                logger.info(f"AI复盘: 找到 {len(core_stocks)} 只核心池股票")
                
                # 2. Init Service
                config = AIDecisionConfig(
                    api_key=settings.deepseek_api_key,
                    base_url=settings.deepseek_base_url,
                    model=settings.deepseek_model
                )
                ai_service = AIDecisionService(config)
                
                # 3. Analyze
                for stock in core_stocks:
                    try:
                        logger.info(f"AI复盘: 正在分析 {stock.stock_name}({stock.stock_code})")
                        await ai_service.generate_decision(session, stock.stock_code)
                        await asyncio.sleep(2)
                    except Exception as e:
                        logger.error(f"AI复盘失败 {stock.stock_code}: {e}")
                        
            logger.info("定时任务: 每日AI复盘完成")
            
            # 2. Update Task Status (Success)
            if task_id:
                async with self.db_manager.get_session() as session:
                    task = await session.get(ScheduledTask, task_id)
                    if task:
                        task.last_run_status = "success"
                        await session.commit()

        except Exception as e:
            logger.error(f"Daily AI review failed: {e}")
            # 3. Update Task Status (Failed)
            if task_id:
                async with self.db_manager.get_session() as session:
                    task = await session.get(ScheduledTask, task_id)
                    if task:
                        task.last_run_status = "failed"
                        await session.commit()

# 全局单例
scheduler_service = SchedulerService()
