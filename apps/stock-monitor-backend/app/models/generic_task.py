from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Integer, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from .base import Base

class GenericTask(Base):
    """通用定时任务模型"""
    __tablename__ = "generic_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="任务名称")
    task_category: Mapped[str] = mapped_column(String(50), nullable=False, comment="任务分类: data_sync/crawler/calculation/monitor")
    api_method: Mapped[str] = mapped_column(String(10), default="GET", comment="请求方法: GET/POST")
    api_endpoint: Mapped[str] = mapped_column(String(500), nullable=False, comment="API端点")
    request_params: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, comment="请求参数")
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False, comment="CRON表达式")
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    timeout: Mapped[int] = mapped_column(Integer, default=60, comment="超时时间(秒)")
    max_retries: Mapped[int] = mapped_column(Integer, default=3, comment="最大重试次数")
    retry_delay: Mapped[int] = mapped_column(Integer, default=5, comment="重试延迟(秒)")
    priority: Mapped[int] = mapped_column(Integer, default=5, comment="优先级(1-10)")
    
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="任务描述")
    notify_on_failure: Mapped[bool] = mapped_column(Boolean, default=True, comment="失败是否告警")
    notify_channels: Mapped[str] = mapped_column(String(100), default="desktop,log", comment="告警渠道")
    
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="最后运行时间")
    last_run_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="最后运行状态")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="最后一次错误信息")
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="下次运行时间")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<GenericTask(id={self.id}, name='{self.name}', cron='{self.cron_expression}')>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
