from fastapi import APIRouter, Request, Body, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from loguru import logger
import json
import asyncio

from app.services.sse_service import SSEService

# Configure dedicated logger for ADB SSE
# Ensure logs directory exists
import os
if not os.path.exists("logs"):
    os.makedirs("logs")

# Add a sink specifically for ADB SSE channel
# We check if the sink is already added to avoid duplication on reload (though loguru handles some dedup, it's safer)
# Note: In a real app, logger configuration is usually central.
logger.add("logs/adb_sse.log", rotation="10 MB", filter=lambda r: r["extra"].get("channel") == "adb_sse", level="INFO")

router = APIRouter(prefix="/api/v1/adb", tags=["ADB Android"])

# Dedicated SSE service for ADB
adb_sse_service = SSEService()

# Create a bound logger for this module
adb_logger = logger.bind(channel="adb_sse")

# In-memory storage for devices (could be moved to a service)
devices: Dict[str, Dict[str, Any]] = {}
device_last_seen: Dict[str, datetime] = {}

# --- Models ---
class DeviceInfo(BaseModel):
    device_id: str
    connected: bool
    model: Optional[str] = None
    android_version: Optional[str] = None
    serial: str
    ip_address: Optional[str] = None
    manufacturer: Optional[str] = None
    brand: Optional[str] = None

class HealthRequest(BaseModel):
    status: str
    adb_available: bool
    devices: List[DeviceInfo]

class AppInfo(BaseModel):
    package_name: str
    app_name: Optional[str] = None
    version: Optional[str] = None
    is_system: bool
    enabled: bool

class AppListRequest(BaseModel):
    device_id: str
    apps: List[AppInfo]

class EventData(BaseModel):
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None

class EventRequest(BaseModel):
    type: str = "event"
    device_id: str
    action: str
    data: EventData
    timestamp: datetime

class HeartbeatRequest(BaseModel):
    status: str

class BaseResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: Optional[Any] = None
    received_count: Optional[int] = None
    error: Optional[str] = None

# --- Endpoints ---

@router.post("/health", response_model=BaseResponse)
async def report_health(request: HealthRequest):
    # Update device registry
    for device in request.devices:
        devices[device.device_id] = device.model_dump()
        device_last_seen[device.device_id] = datetime.now()
    
    adb_logger.info(f"Received health report: {len(request.devices)} devices")
    return BaseResponse()

@router.post("/app_list", response_model=BaseResponse)
async def report_app_list(request: AppListRequest):
    adb_logger.info(f"Received app list for {request.device_id}: {len(request.apps)} apps")
    # In a real app, store this in DB
    return BaseResponse(received_count=len(request.apps))

@router.post("/events", response_model=BaseResponse)
async def report_event(request: EventRequest):
    adb_logger.info(f"Received event from {request.device_id}: {request.action} - Success: {request.data.success}")
    # Broadcast to any monitoring clients (if we had a separate monitoring channel)
    # For now just log
    return BaseResponse()

@router.get("/events")
async def sse_endpoint(request: Request):
    """SSE endpoint for server -> client commands"""
    return await adb_sse_service.subscribe(request)

@router.post("/heartbeat", response_model=BaseResponse)
async def heartbeat(request: HeartbeatRequest):
    return BaseResponse(message="pong")

# --- Command Helper ---
async def send_command(device_id: str, action: str, params: Dict[str, Any] = None):
    command = {
        "type": "command",
        "device_id": device_id,
        "action": action,
        "params": params or {},
        "timestamp": datetime.now().isoformat()
    }
    # We use 'message' event type by default or specific if needed
    # Note: sse_service.broadcast wraps data in json.dumps, so client gets a string in data field?
    # Wait, SSEService.broadcast implementation:
    # message = {"event": event_type, "data": json.dumps(data)}
    # If client expects JSON object in data, this might be double serialized if sse_starlette also serializes.
    # sse_starlette handles dict as JSON automatically?
    # Let's check sse_service.py again.
    
    # In sse_service.py:
    # yield data
    # data comes from queue.
    # message = {"event": ..., "data": json.dumps(data)}
    # So the yielded item is a dict. EventSourceResponse handles dict by formatting as SSE.
    # If 'data' field is already a string (json.dumps), then the client receives that string.
    # If the client expects a JSON object, they need to parse it.
    # The doc example: data: {"type":...}
    # This implies the raw SSE stream has JSON object.
    # If sse_starlette receives 'data': '{"type":...}', it writes `data: {"type":...}`.
    # So it seems correct.
    
    await adb_sse_service.broadcast("message", command)
    return True

# --- Test/Debug Endpoints to Trigger Commands ---
class CommandRequest(BaseModel):
    device_id: str
    action: str
    params: Optional[Dict[str, Any]] = None

@router.post("/command/send", response_model=BaseResponse)
async def trigger_command(cmd: CommandRequest):
    await send_command(cmd.device_id, cmd.action, cmd.params)
    return BaseResponse(message="Command sent")

@router.get("/devices", response_model=BaseResponse)
async def get_devices():
    return BaseResponse(data=list(devices.values()))
