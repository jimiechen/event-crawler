# -*- coding: utf-8 -*-
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import select, desc
from app.models.okooo_match import OkoooMatch
from app.database import db_manager
from app.services.redis_cache_service import RedisCacheService
from app.crawler.okooo.scheduler import OkoooScheduler
from app.services.task_executor import manager  # WebSocket manager
from app.services.sse_service import sse_service  # SSE Service

logger = logging.getLogger(__name__)

class OkoooService:
    """
    Okooo爬虫服务
    管理OkoooScheduler的生命周期，处理API请求和日志推送
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OkoooService, cls).__new__(cls)
            cls._instance.scheduler = None
            cls._instance.is_running = False
            cls._instance._crawl_task = None
        return cls._instance

    def __init__(self):
        # 已经在__new__中初始化，避免重复初始化
        pass

    async def get_db_matches(self, date_str: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        从数据库获取比赛列表
        """
        try:
            async with db_manager.get_session() as session:
                stmt = select(OkoooMatch)
                
                if date_str:
                    try:
                        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                        stmt = stmt.where(OkoooMatch.match_date == target_date)
                    except ValueError:
                        pass
                
                # Order by match time or ID
                stmt = stmt.order_by(desc(OkoooMatch.match_date), desc(OkoooMatch.id))
                
                result = await session.execute(stmt)
                matches = result.scalars().all()
                
                return [{
                    "id": m.id,
                    "league": m.league_name,
                    "home_team": m.home_team,
                    "away_team": m.away_team,
                    "match_time": m.match_time_text,
                    "match_date": m.match_date.strftime("%Y-%m-%d") if m.match_date else None,
                    "history_data": m.history_data
                } for m in matches]
        except Exception as e:
            logger.error(f"Error getting db matches: {e}")
            return []

    async def get_matches_dates(self) -> List[str]:
        """
        获取所有有比赛的日期
        """
        try:
            async with db_manager.get_session() as session:
                stmt = select(OkoooMatch.match_date).distinct().where(OkoooMatch.match_date.isnot(None)).order_by(desc(OkoooMatch.match_date))
                result = await session.execute(stmt)
                dates = result.scalars().all()
                return [d.strftime("%Y-%m-%d") for d in dates if d]
        except Exception as e:
            logger.error(f"Error getting match dates: {e}")
            return []

    async def get_scheduler(self) -> OkoooScheduler:
        """获取或初始化调度器"""
        if self.scheduler is None:
            redis_service = RedisCacheService()
            # 注意：db_manager应该是已经初始化的全局实例
            self.scheduler = OkoooScheduler(db_manager, redis_service)
            self.scheduler.set_callbacks(
                log_cb=self._on_log,
                progress_cb=self._on_progress,
                match_list_cb=self._on_match_list
            )
        return self.scheduler

    async def _on_log(self, level: str, message: str):
        """日志回调"""
        log_data = {
            "type": "okooo_log",
            "level": level,
            "message": message,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        await manager.broadcast(log_data)
        await sse_service.broadcast("okooo_log", log_data)

    async def _on_progress(self, processed: int, total: int):
        """进度回调"""
        progress_data = {
            "type": "okooo_progress",
            "processed": processed,
            "total": total,
            "percentage": round(processed / total * 100, 2) if total > 0 else 0
        }
        await manager.broadcast(progress_data)
        await sse_service.broadcast("okooo_progress", progress_data)

    async def _on_match_list(self, matches: list):
        """比赛列表回调"""
        data = {
            "type": "okooo_matches",
            "matches": matches
        }
        await manager.broadcast(data)
        await sse_service.broadcast("okooo_matches", data)

    async def start_crawl(self, start_id: int, end_id: int) -> bool:
        """启动爬虫任务"""
        if self.is_running:
            logger.warning("Okooo crawler is already running")
            return False

        scheduler = await self.get_scheduler()
        self.is_running = True
        
        # 创建后台任务
        self._crawl_task = asyncio.create_task(self._run_crawl(scheduler, start_id, end_id))
        return True

    async def fetch_match_lists(self, headless: bool = True, use_cache: bool = False) -> list:
        """获取比赛列表"""
        scheduler = await self.get_scheduler()
        
        # Configure
        storage_path = "okooo_session.json" if use_cache else None
        
        # 强制配置更新，确保单例模式下的配置一致性
        await scheduler.configure(headless=headless, storage_state_path=storage_path)
        
        return await scheduler.fetch_match_lists()

    async def start_crawl_lists(self, headless: bool = True, use_cache: bool = False) -> bool:
        """启动列表爬虫任务"""
        if self.is_running:
            logger.warning("Okooo crawler is already running")
            return False

        scheduler = await self.get_scheduler()
        
        # Configure
        storage_path = "okooo_session.json" if use_cache else None
        await scheduler.configure(headless=headless, storage_state_path=storage_path)
        
        self.is_running = True
        
        # 创建后台任务
        self._crawl_task = asyncio.create_task(self._run_crawl_lists(scheduler))
        return True

    async def start_crawl_ids(self, match_ids: list, headless: bool = True, use_cache: bool = False, force: bool = False) -> bool:
        """启动指定ID列表爬虫任务"""
        if self.is_running:
            logger.warning("Okooo crawler is already running")
            return False

        scheduler = await self.get_scheduler()
        
        # Configure
        storage_path = "okooo_session.json" if use_cache else None
        await scheduler.configure(headless=headless, storage_state_path=storage_path)
        
        self.is_running = True
        
        # 创建后台任务
        self._crawl_task = asyncio.create_task(self._run_crawl_ids(scheduler, match_ids, force))
        return True

    async def _run_crawl_ids(self, scheduler: OkoooScheduler, match_ids: list, force: bool = False):
        """执行ID列表爬虫任务的包装器"""
        try:
            await scheduler.crawl_ids(match_ids, force=force)
        except Exception as e:
            logger.error(f"Crawl ids task error: {e}")
            await self._on_log("ERROR", f"Crawl ids task crashed: {e}")
        finally:
            self.is_running = False
            await self._on_log("INFO", "Crawl ids task ended")
            await manager.broadcast({
                "type": "okooo_status",
                "is_running": False
            })
            await sse_service.broadcast("okooo_status", {
                "type": "okooo_status",
                "is_running": False
            })

    async def _run_crawl_lists(self, scheduler: OkoooScheduler):
        """执行列表爬虫任务的包装器"""
        try:
            await scheduler.crawl_match_lists()
        except Exception as e:
            logger.error(f"Crawl lists task error: {e}")
            await self._on_log("ERROR", f"Crawl lists task crashed: {e}")
        finally:
            self.is_running = False
            await self._on_log("INFO", "Crawl lists task ended")
            await manager.broadcast({
                "type": "okooo_status",
                "is_running": False
            })
            await sse_service.broadcast("okooo_status", {
                "type": "okooo_status",
                "is_running": False
            })

    async def _run_crawl(self, scheduler: OkoooScheduler, start_id: int, end_id: int):
        """执行爬虫任务的包装器"""
        try:
            await scheduler.crawl_range(start_id, end_id)
        except Exception as e:
            logger.error(f"Crawl task error: {e}")
            await self._on_log("ERROR", f"Crawl task crashed: {e}")
        finally:
            self.is_running = False
            await self._on_log("INFO", "Crawl task ended")
            # 发送最终状态
            await manager.broadcast({
                "type": "okooo_status",
                "is_running": False
            })
            await sse_service.broadcast("okooo_status", {
                "type": "okooo_status",
                "is_running": False
            })

    async def stop_crawl(self):
        """停止爬虫任务"""
        if self.scheduler and self.is_running:
            self.scheduler.stop()
            await self._on_log("WARNING", "Stopping crawler...")
            
            # Cancel the task to unblock any waits (like queue.join)
            if self._crawl_task and not self._crawl_task.done():
                self._crawl_task.cancel()
                try:
                    await self._crawl_task
                except asyncio.CancelledError:
                    await self._on_log("INFO", "Crawler task cancelled")
                except Exception as e:
                    await self._on_log("ERROR", f"Error waiting for crawler task: {e}")
            
            self.is_running = False

    async def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        stats = self.scheduler.stats if self.scheduler else {
            "total": 0,
            "processed": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
        return {
            "is_running": self.is_running,
            "stats": stats
        }

# 全局实例
okooo_service = OkoooService()
