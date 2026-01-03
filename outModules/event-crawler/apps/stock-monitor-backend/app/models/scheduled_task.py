#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务模型
用于存储定时任务的配置信息
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

class ScheduledTask(BaseModel):
    """定时任务配置表"""
    
    __tablename__ = "scheduled_task"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="任务ID")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="任务名称")
    task_type: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, comment="任务类型(唯一标识): daily_sync, daily_score等")
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False, comment="Cron表达式")
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="任务描述")
    
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="上次运行时间")
    last_run_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="上次运行状态: success, failed")
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="下次运行时间")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def __repr__(self):
        return f"<ScheduledTask(id={self.id}, name={self.name}, type={self.task_type}, cron={self.cron_expression})>"
