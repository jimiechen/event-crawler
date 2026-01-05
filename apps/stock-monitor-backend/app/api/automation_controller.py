from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.database import get_db_session
from app.services.automation_service import AutomationService
from app.services.sse_service import sse_service

router = APIRouter(prefix="/api/v1/automation", tags=["Automation"])

class ConfigRequest(BaseModel):
    device_model: str
    resolution: str
    app_version: str
    config_data: Optional[Dict[str, Any]] = None

class TaskCreateRequest(BaseModel):
    task_type: str
    params: Dict[str, Any]
    device_id: str

class TaskStatusUpdate(BaseModel):
    task_id: int
    status: str
    result_data: Optional[Dict[str, Any]] = None

class LogCreateRequest(BaseModel):
    task_id: Optional[int] = None
    device_id: str
    step: str
    level: str
    message: str
    screenshot_path: Optional[str] = None

@router.get("/config")
async def get_config(
    device_model: str,
    resolution: str,
    app_version: str,
    db: AsyncSession = Depends(get_db_session)
):
    service = AutomationService(db)
    config = await service.get_config(device_model, resolution, app_version)
    if not config:
        return {"success": False, "message": "Config not found"}
    return {"success": True, "data": config}

@router.post("/config")
async def save_config(
    request: ConfigRequest,
    db: AsyncSession = Depends(get_db_session)
):
    if not request.config_data:
        raise HTTPException(status_code=400, detail="config_data is required")
        
    service = AutomationService(db)
    config = await service.save_config(request.model_dump())
    return {"success": True, "data": config}

@router.post("/task/create")
async def create_task(
    request: TaskCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    service = AutomationService(db)
    # 1. 创建任务记录
    task = await service.create_task(request.model_dump())
    
    # 2. 通过SSE发送指令
    payload = {
        "type": "command",
        "task_id": task.id,
        "task_type": request.task_type,
        "params": request.params
    }
    
    # 广播给特定设备 (目前SSE广播是群发，客户端需要过滤 device_id)
    # 也可以在 sse_service 中实现单播，这里简化为广播带 device_id
    await sse_service.broadcast("automation_command", {
        "target_device_id": request.device_id,
        "command": payload
    })
    
    return {"success": True, "data": task}

@router.post("/task/update")
async def update_task_status(
    request: TaskStatusUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    service = AutomationService(db)
    task = await service.update_task_status(request.task_id, request.status, request.result_data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True, "data": task}

@router.post("/log/report")
async def create_log(
    request: LogCreateRequest,
    db: AsyncSession = Depends(get_db_session)
):
    service = AutomationService(db)
    log = await service.log_event(request.model_dump())
    return {"success": True, "data": log}
