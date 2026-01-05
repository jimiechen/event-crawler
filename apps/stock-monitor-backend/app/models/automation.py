from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

class AutomationConfig(BaseModel):
    """自动化配置表：存储经过AI验证的坐标映射"""
    __tablename__ = "automation_configs"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    app_version: Mapped[str] = mapped_column(String(50), comment="APP版本号")
    device_model: Mapped[str] = mapped_column(String(50), comment="设备型号")
    resolution: Mapped[str] = mapped_column(String(20), comment="分辨率 (e.g., 1080x2400)")
    config_data: Mapped[Dict[str, Any]] = mapped_column(JSON, comment="坐标配置 (JSON格式)")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

class AutomationTask(BaseModel):
    """自动化任务表：记录下发的指令"""
    __tablename__ = "automation_tasks"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_type: Mapped[str] = mapped_column(String(50), comment="任务类型 (e.g., smart_order)")
    params: Mapped[Dict[str, Any]] = mapped_column(JSON, comment="任务参数")
    status: Mapped[str] = mapped_column(String(20), default="pending", comment="状态: pending, running, success, failed")
    device_id: Mapped[str] = mapped_column(String(50), comment="执行设备ID")
    result_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, comment="执行结果")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

class AutomationLog(BaseModel):
    """执行日志表：用于故障排查"""
    __tablename__ = "automation_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("automation_tasks.id"), nullable=True)
    device_id: Mapped[str] = mapped_column(String(50), comment="设备ID")
    step: Mapped[str] = mapped_column(String(50), comment="步骤名称")
    level: Mapped[str] = mapped_column(String(10), comment="日志级别: INFO, ERROR")
    message: Mapped[str] = mapped_column(Text, comment="日志内容")
    screenshot_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="截图存储路径")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
