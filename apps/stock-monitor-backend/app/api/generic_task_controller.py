from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from loguru import logger

from app.database import get_db_session
from app.api.schemas import BaseResponse
from app.services.generic_task_service import GenericTaskService
from app.services.task_execution_detail_service import TaskExecutionDetailService
from app.services.task_executor import task_executor
from app.services.scheduler_service import scheduler_service

router = APIRouter(prefix="/api/v1/generic-task", tags=["通用定时任务"])

class GenericTaskCreate(BaseModel):
    name: str
    task_category: str
    api_method: str = "GET"
    api_endpoint: str
    request_params: Optional[Dict[str, Any]] = None
    cron_expression: str
    is_active: bool = True
    timeout: int = 60
    max_retries: int = 3
    retry_delay: int = 5
    priority: int = 5
    description: Optional[str] = None
    notify_on_failure: bool = True
    notify_channels: str = "desktop,log"

class GenericTaskUpdate(BaseModel):
    name: Optional[str] = None
    task_category: Optional[str] = None
    api_method: Optional[str] = None
    api_endpoint: Optional[str] = None
    request_params: Optional[Dict[str, Any]] = None
    cron_expression: Optional[str] = None
    is_active: Optional[bool] = None
    timeout: Optional[int] = None
    max_retries: Optional[int] = None
    retry_delay: Optional[int] = None
    priority: Optional[int] = None
    description: Optional[str] = None
    notify_on_failure: Optional[bool] = None
    notify_channels: Optional[str] = None

class GenericTaskBatchCreate(BaseModel):
    tasks: List[GenericTaskCreate]

class GenericTaskBatchToggle(BaseModel):
    task_ids: List[int]
    is_active: bool

@router.post("", response_model=BaseResponse, summary="创建通用任务")
async def create_generic_task(
    task_in: GenericTaskCreate,
    db: AsyncSession = Depends(get_db_session)
):
    try:
        service = GenericTaskService(db)
        task = await service.create_generic_task(task_in.model_dump())
        
        # 刷新调度器
        await scheduler_service.refresh_task(task.id)
        
        return BaseResponse(data=task.to_dict(), message="创建成功")
    except Exception as e:
        logger.error(f"创建通用任务失败: {e}")
        return BaseResponse(success=False, message=str(e))

@router.post("/batch/create", response_model=BaseResponse, summary="批量创建通用任务")
async def batch_create_generic_tasks(
    batch_in: GenericTaskBatchCreate,
    db: AsyncSession = Depends(get_db_session)
):
    try:
        service = GenericTaskService(db)
        tasks_data = [task.model_dump() for task in batch_in.tasks]
        tasks = await service.batch_create_generic_tasks(tasks_data)
        
        # 刷新调度器
        for task in tasks:
            await scheduler_service.refresh_task(task.id)
            
        return BaseResponse(data=[t.to_dict() for t in tasks], message=f"批量创建成功，共 {len(tasks)} 个任务")
    except Exception as e:
        logger.error(f"批量创建通用任务失败: {e}")
        return BaseResponse(success=False, message=str(e))

@router.post("/batch/toggle", response_model=BaseResponse, summary="批量启用/禁用任务")
async def batch_toggle_generic_tasks(
    batch_in: GenericTaskBatchToggle,
    db: AsyncSession = Depends(get_db_session)
):
    try:
        service = GenericTaskService(db)
        task_ids = await service.batch_toggle_generic_tasks(batch_in.task_ids, batch_in.is_active)
        
        # 刷新调度器
        for task_id in task_ids:
            await scheduler_service.refresh_task(task_id)
            
        action = "启用" if batch_in.is_active else "禁用"
        return BaseResponse(message=f"批量{action}成功，共 {len(task_ids)} 个任务")
    except Exception as e:
        logger.error(f"批量更新任务状态失败: {e}")
        return BaseResponse(success=False, message=str(e))

@router.get("", response_model=BaseResponse, summary="获取通用任务列表")
async def get_generic_tasks(
    db: AsyncSession = Depends(get_db_session)
):
    try:
        service = GenericTaskService(db)
        tasks = await service.get_all_generic_tasks()
        return BaseResponse(data=[t.to_dict() for t in tasks])
    except Exception as e:
        return BaseResponse(success=False, message=str(e))

@router.put("/{task_id}", response_model=BaseResponse, summary="更新通用任务")
async def update_generic_task(
    task_id: int,
    task_in: GenericTaskUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    try:
        service = GenericTaskService(db)
        task = await service.update_generic_task(task_id, task_in.model_dump(exclude_unset=True))
        if not task:
            return BaseResponse(success=False, message="任务不存在")
            
        # 刷新调度器
        await scheduler_service.refresh_task(task.id)
        
        return BaseResponse(data=task.to_dict(), message="更新成功")
    except Exception as e:
        return BaseResponse(success=False, message=str(e))

@router.delete("/{task_id}", response_model=BaseResponse, summary="删除通用任务")
async def delete_generic_task(
    task_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    try:
        service = GenericTaskService(db)
        success = await service.delete_generic_task(task_id)
        if not success:
            return BaseResponse(success=False, message="任务不存在")
            
        # 移除调度
        scheduler_service.remove_task(task_id)
        
        return BaseResponse(message="删除成功")
    except Exception as e:
        return BaseResponse(success=False, message=str(e))

@router.post("/{task_id}/execute", response_model=BaseResponse, summary="立即执行任务")
async def execute_task_manually(
    task_id: int,
    background_tasks: bool = Query(True, description="是否后台执行"),
    db: AsyncSession = Depends(get_db_session)
):
    try:
        service = GenericTaskService(db)
        task = await service.get_generic_task_by_id(task_id)
        if not task:
            return BaseResponse(success=False, message="任务不存在")
        
        if background_tasks:
            # 异步后台执行
            # 注意：这里我们调用 task_executor 的方法，它内部会创建新的 DB session
            # 所以不需要传递当前的 db session
            import asyncio
            asyncio.create_task(task_executor.execute_generic_task(task_id))
            return BaseResponse(message="任务已提交后台执行")
        else:
            # 同步等待执行结果
            result = await task_executor.execute_generic_task(task_id)
            return BaseResponse(data=result, message="执行完成")
            
    except Exception as e:
        return BaseResponse(success=False, message=str(e))

@router.get("/{task_id}/history", response_model=BaseResponse, summary="获取任务执行历史")
async def get_task_history(
    task_id: int,
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session)
):
    try:
        detail_service = TaskExecutionDetailService(db)
        history = await detail_service.get_execution_details_by_task_id(task_id, limit)
        return BaseResponse(data=[h.to_dict() for h in history])
    except Exception as e:
        return BaseResponse(success=False, message=str(e))
