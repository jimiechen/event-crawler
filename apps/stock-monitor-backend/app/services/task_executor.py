import asyncio
from typing import List, Dict, Any
from fastapi import WebSocket
from loguru import logger
import httpx
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.repositories.task_log_repository import TaskExecutionLogRepository
from app.database import db_manager

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                self.disconnect(connection)

# Global connection manager instance
manager = ConnectionManager()

class TaskExecutor:
    def __init__(self, concurrency: int = 5):
        self.semaphore = asyncio.Semaphore(concurrency)
        self.processing_ids = set()
        
        # APScheduler setup
        self.scheduler = AsyncIOScheduler()
        # Add job to run every 2 seconds
        self.scheduler.add_job(
            self.scan_and_schedule_tasks,
            trigger=IntervalTrigger(seconds=2),
            id="scan_pending_tasks",
            replace_existing=True,
            coalesce=True,  # Skip if previous execution hasn't finished
            max_instances=1
        )
        logger.info("TaskExecutor initialized with APScheduler")

    @property
    def is_running(self):
        return self.scheduler.running

    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("✅ TaskExecutor (APScheduler) started")
        elif self.scheduler.state == 2: # Paused
            self.scheduler.resume()
            logger.info("✅ TaskExecutor (APScheduler) resumed")
        else:
            logger.info("ℹ️ TaskExecutor is already running")

    def stop(self):
        """Pause the scheduler"""
        if self.scheduler.running:
            self.scheduler.pause()
            logger.info("⏸️ TaskExecutor (APScheduler) paused")

    async def scan_and_schedule_tasks(self):
        """Scheduled job to fetch and execute pending tasks"""
        try:
            repo = TaskExecutionLogRepository(db_manager)
            
            # 1. Fetch pending tasks
            tasks = await repo.get_pending_tasks(limit=50)
            
            if not tasks:
                return
            
            logger.info(f"Executor found {len(tasks)} pending tasks. Scheduling...")

            # 2. Schedule them
            scheduled_count = 0
            for task in tasks:
                if task.id in self.processing_ids: 
                    continue
                
                # Fire and forget (managed by semaphore and processing_ids)
                asyncio.create_task(self.execute_task(task.id, repo))
                scheduled_count += 1
            
            if scheduled_count > 0:
                logger.info(f"Scheduled {scheduled_count} tasks for execution")

        except Exception as e:
            logger.error(f"TaskExecutor scan error: {e}")

    async def execute_task(self, log_id: int, repo: TaskExecutionLogRepository):
        # Check processing lock
        if log_id in self.processing_ids:
            return
        
        self.processing_ids.add(log_id)
        
        try:
            async with self.semaphore:
                # 1. Get log info (Double check status in case it changed)
                log = await repo.get_log_by_id(log_id)
                if not log:
                    return
                
                if log.status != 'pending' and log.status != 'failed': 
                    # Only execute pending or retrying failed. 
                    # But run_loop only fetches pending.
                    # run_batch might pass failed ones.
                    pass

                # Notify Start
                await manager.broadcast({
                    "type": "task_update",
                    "data": {
                        "id": log_id,
                        "status": "running",
                        "message": f"任务 {log_id} 开始执行"
                    }
                })
                
                # Update DB
                await repo.update_status(log_id, "running")

                # 2. Execute Request
                url = log.task_url
                logger.info(f"Executing task {log_id}: {url}")
                
                async with httpx.AsyncClient(timeout=60.0) as client:
                    try:
                        response = await client.get(url)
                        if response.status_code == 200:
                            resp_json = response.json()
                            success = resp_json.get("success", False)
                            status = "success" if success else "failed"
                            
                            if success:
                                # Try to extract a cleaner message
                                base_msg = resp_json.get("message", "")
                                data = resp_json.get("data", {})
                                if isinstance(data, dict):
                                    inserted = data.get("inserted")
                                    if inserted is not None:
                                        msg = f"{base_msg} (Inserted: {inserted})"
                                    else:
                                        msg = base_msg or str(resp_json)
                                else:
                                    msg = base_msg or str(resp_json)
                            else:
                                msg = resp_json.get("message", "Unknown error")
                        else:
                            status = "failed"
                            msg = f"HTTP {response.status_code}"
                    except Exception as http_err:
                         status = "failed"
                         msg = f"Request error: {str(http_err)}"
                
                # 3. Update DB
                await repo.update_status(log_id, status, result_message=msg)
                
                # Notify Result
                await manager.broadcast({
                    "type": "task_result", 
                    "data": {
                        "id": log_id,
                        "status": status,
                        "message": f"任务 {log_id} 执行{ '成功' if status == 'success' else '失败' }: {msg[:50]}..."
                    }
                })
                
                # Also send update for list
                await manager.broadcast({
                    "type": "task_update",
                    "data": {
                        "id": log_id,
                        "status": status,
                        "message": msg
                    }
                })

        except Exception as e:
            logger.error(f"Task {log_id} execution error: {e}")
            await repo.update_status(log_id, "failed", result_message=str(e))
            await manager.broadcast({
                "type": "task_result",
                "data": {
                    "id": log_id,
                    "status": "failed",
                    "message": f"任务 {log_id} 异常: {str(e)}"
                }
            })
            await manager.broadcast({
                "type": "task_update",
                "data": {
                    "id": log_id,
                    "status": "failed",
                    "message": str(e)
                }
            })
        finally:
            if log_id in self.processing_ids:
                self.processing_ids.remove(log_id)

    async def run_batch(self, log_ids: List[int]):
        """Run a batch of tasks concurrently"""
        repo = TaskExecutionLogRepository(db_manager)
        tasks = [self.execute_task(log_id, repo) for log_id in log_ids]
        await asyncio.gather(*tasks)

# Global executor instance
executor = TaskExecutor(concurrency=10)
