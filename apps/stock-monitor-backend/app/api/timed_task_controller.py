#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务控制接口
"""

from fastapi import APIRouter, Depends, Query, BackgroundTasks, HTTPException, Body, WebSocket, WebSocketDisconnect
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.database import get_db_session, db_manager
from app.services.tushare_service import TushareService
from app.services.rule_engine_service import RuleEngineService
from app.services.stock_service import StockService
from app.services.local_data_service import LocalDataService
from app.repositories.task_log_repository import TaskExecutionLogRepository
from app.api.schemas import BaseResponse
from app.api.stock_daily_schemas import TaskLogListResponse, TaskLogResponse
from app.services.stock_sync_service import StockSyncService
from app.services.task_executor import executor, manager
from app.services.scheduler_service import scheduler_service
from app.models.scheduled_task import ScheduledTask
from app.models.task_log import TaskExecutionLog

router = APIRouter(prefix="/api/v1/timed-task", tags=["定时任务"])

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@router.post("/executor/start", summary="启动自动执行", response_model=BaseResponse)
async def start_executor():
    executor.start()
    return BaseResponse(success=True, message="自动执行已启动")

@router.post("/executor/stop", summary="暂停自动执行", response_model=BaseResponse)
async def stop_executor():
    executor.stop()
    return BaseResponse(success=True, message="自动执行已暂停")

@router.get("/executor/status", summary="获取执行器状态", response_model=BaseResponse)
async def get_executor_status():
    return BaseResponse(success=True, data={"is_running": executor.is_running})

class BatchCreateTaskRequest(BaseModel):
    task_type: str = Field(..., description="任务类型: csv_sync, tushare_sync, calculate")
    
class ExecuteTaskRequest(BaseModel):
    log_ids: List[int] = Field(..., description="要执行的任务ID列表")

@router.post("/batch-create", summary="批量创建任务", response_model=BaseResponse)
async def batch_create_tasks(
    request: BatchCreateTaskRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    批量创建任务
    根据 StockInfo 表中的所有股票，创建对应的原子任务
    """
    try:
        # 1. 获取所有股票代码
        from app.repositories.stock_repository import StockRepository
        repo = StockRepository(db)
        codes = await repo.get_all_codes()
        
        if not codes:
             return BaseResponse(success=False, message="没有找到股票代码")

        # 2. 构造日志数据
        task_type = request.task_type
        logs_data = []
        
        base_url_sync = "http://localhost:8000/api/v1/stock/sync"
        base_url_analysis = "http://localhost:8000/api/v1/volume-analysis"
        
        for code in codes:
            if task_type == "csv_sync":
                url = f"{base_url_sync}/csv/{code}"
            elif task_type == "tushare_sync":
                url = f"{base_url_sync}/tushare/{code}"
            elif task_type == "calculate":
                url = f"{base_url_analysis}/run/{code}"
            else:
                continue
                
            logs_data.append({
                "task_type": task_type,
                "task_url": url,
                "stock_code": code
            })
            
        # 3. 批量插入
        repo_log = TaskExecutionLogRepository(db_manager)
        count = await repo_log.batch_create_logs(logs_data)
        
        return BaseResponse(success=True, message=f"已创建 {count} 个任务")
        
    except Exception as e:
        logger.error(f"批量创建任务失败: {e}")
        return BaseResponse(success=False, message=str(e))

@router.get("/execution-logs", summary="获取任务日志列表", response_model=TaskLogListResponse)
async def get_task_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    task_name: Optional[str] = None,
    task_url: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    try:
        offset = (page - 1) * page_size
        
        # Build Query
        stmt = select(TaskExecutionLog).order_by(desc(TaskExecutionLog.id)).offset(offset).limit(page_size)
        
        if status:
            stmt = stmt.where(TaskExecutionLog.status == status)
        if task_name:
             stmt = stmt.where(TaskExecutionLog.task_type.like(f"%{task_name}%"))
        if task_url:
             stmt = stmt.where(TaskExecutionLog.task_url.like(f"%{task_url}%"))
             
        result = await db.execute(stmt)
        logs = result.scalars().all()
        
        # Count
        count_stmt = select(func.count(TaskExecutionLog.id))
        if task_name:
            count_stmt = count_stmt.where(TaskExecutionLog.task_type.like(f"%{task_name}%"))
        if status:
            count_stmt = count_stmt.where(TaskExecutionLog.status == status)
        if task_url:
            count_stmt = count_stmt.where(TaskExecutionLog.task_url.like(f"%{task_url}%"))
        
        total = (await db.execute(count_stmt)).scalar() or 0
        
        # Prepare response data with manual mapping if needed
        response_data = []
        for log in logs:
            log_dict = {
                "id": log.id,
                "task_type": log.task_type,
                "task_name": log.task_type, # Use task_type as name
                "task_url": log.task_url,
                "stock_code": log.stock_code,
                "status": log.status,
                "result_message": log.result_message,
                "executed_at": log.executed_at,
                "created_at": log.executed_at, # Fallback to executed_at if created_at is not available, or None
                "duration": None # Calculate if needed
            }
            # If created_at is actually available on the model, use it. 
            # Checking model: TaskExecutionLog inherits BaseModel which has TimestampMixin? 
            # Let's check imports. TaskExecutionLog in app/models/task_log.py usually inherits BaseModel from app.models.base
            # which usually has CreatedMixin.
            if hasattr(log, 'created_at'):
                log_dict["created_at"] = log.created_at
            
            response_data.append(TaskLogResponse(**log_dict))
        
        return TaskLogListResponse(
            success=True,
            message="ok",
            data=response_data,
            total=total
        )
    except Exception as e:
        logger.error(f"获取任务日志失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute", summary="执行任务", response_model=BaseResponse)
async def execute_tasks(
    request: ExecuteTaskRequest,
    background_tasks: BackgroundTasks
):
    """
    执行选中的任务 (后台异步)
    """
    try:
        # Use the executor service
        background_tasks.add_task(executor.run_batch, request.log_ids)
        return BaseResponse(success=True, message="任务已提交执行")
    except Exception as e:
        logger.error(f"提交任务失败: {e}")
        return BaseResponse(success=False, message=str(e))

# --- Scheduled Task Management ---

class ScheduledTaskDto(BaseModel):
    id: int
    name: str
    task_type: str
    cron_expression: str
    is_active: bool
    description: Optional[str] = None
    last_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    next_run_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UpdateScheduledTaskRequest(BaseModel):
    id: int
    cron_expression: Optional[str] = None
    is_active: Optional[bool] = None

@router.get("/rules", summary="获取规则配置", response_model=BaseResponse)
async def get_rules():
    service = RuleEngineService(db_manager)
    rules = await service.get_rule_config()
    return BaseResponse(success=True, data=rules)

@router.post("/rules", summary="保存规则配置", response_model=BaseResponse)
async def save_rules(rules: dict):
    try:
        service = RuleEngineService(db_manager)
        await service.save_rule_config(rules)
        return BaseResponse(success=True, message="规则已保存")
    except Exception as e:
        logger.error(f"保存规则失败: {e}")
        return BaseResponse(success=False, message=f"保存规则失败: {str(e)}")

@router.post("/sync/wencai", summary="触发问财同步", response_model=BaseResponse)
async def trigger_wencai_sync(background_tasks: BackgroundTasks):
    try:
        # Trigger the crawler task in background
        task = await scheduler_service.repo.get_task_by_type('crawler_all')
        if task:
            background_tasks.add_task(scheduler_service.execute_task_wrapper, task.id, task.task_type)
            return BaseResponse(success=True, message="问财同步任务已触发")
        else:
            # Fallback if task not found in DB
            background_tasks.add_task(scheduler_service.run_crawler_all)
            return BaseResponse(success=True, message="问财同步任务已触发 (直接执行)")
    except Exception as e:
        logger.error(f"触发问财同步失败: {e}")
        return BaseResponse(success=False, message=f"触发失败: {str(e)}")


@router.get("/scheduled/list", summary="获取定时任务列表", response_model=BaseResponse)
async def get_scheduled_tasks():
    tasks = await scheduler_service.repo.get_all_tasks()
    if not tasks:
        logger.info("No scheduled tasks found, initializing defaults...")
        try:
            await scheduler_service._init_default_tasks()
            # Reload to scheduler as well
            await scheduler_service._load_jobs()
            tasks = await scheduler_service.repo.get_all_tasks()
        except Exception as e:
            logger.error(f"Failed to auto-init tasks: {e}")
            
    # Serialize manually if needed or use Pydantic model
    return BaseResponse(success=True, data=[ScheduledTaskDto.model_validate(t) for t in tasks])

@router.post("/scheduled/update", summary="更新定时任务配置", response_model=BaseResponse)
async def update_scheduled_task(request: UpdateScheduledTaskRequest):
    try:
        await scheduler_service.repo.update_task_config(
            request.id, 
            cron_expression=request.cron_expression, 
            is_active=request.is_active
        )
        # Reload jobs to apply changes
        await scheduler_service._load_jobs()
        return BaseResponse(success=True, message="任务配置已更新")
    except Exception as e:
        logger.error(f"Failed to update task: {e}")
        return BaseResponse(success=False, message=str(e))

@router.post("/scheduled/run/{task_id}", summary="立即运行定时任务", response_model=BaseResponse)
async def run_scheduled_task_manually(task_id: int, background_tasks: BackgroundTasks):
    task = await scheduler_service.repo.get_task_by_id(task_id)
    if not task:
        return BaseResponse(success=False, message="任务不存在")
    
    # Run in background to avoid blocking API
    background_tasks.add_task(scheduler_service.execute_task_wrapper, task.id, task.task_type)
    
    return BaseResponse(success=True, message=f"任务 {task.name} 已触发执行")
