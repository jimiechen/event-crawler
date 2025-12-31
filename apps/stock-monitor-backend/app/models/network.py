#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络数据模型
定义网络请求数据的数据库模型
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Integer, Text, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class NetworkData(BaseModel):
    """网络数据模型"""
    
    __tablename__ = "network_data"
    __table_args__ = (
        Index('idx_network_data_source', 'source'),
        Index('idx_network_data_timestamp', 'timestamp'),
        Index('idx_network_data_request_id', 'request_id'),
        {'comment': 'Chrome扩展网络数据表'}
    )
    
    # 主键
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="主键ID"
    )
    
    # 请求信息
    url: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
        comment="请求URL"
    )
    
    method: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="GET",
        comment="请求方法"
    )
    
    # 响应数据
    response_data: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="响应数据(JSON格式)"
    )
    
    # 数据属性
    data_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="数据大小(字节)"
    )
    
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="unknown",
        comment="数据来源"
    )
    
    # 请求标识
    request_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="请求ID"
    )
    
    # 请求头信息
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="用户代理"
    )
    
    headers: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="请求头(JSON格式)"
    )
    
    # 时间戳
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="数据时间戳"
    )
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"<NetworkData(id={self.id}, url='{self.url[:50]}...', source='{self.source}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        import json
        
        result = super().to_dict()
        
        # 解析JSON字段
        try:
            result['response_data'] = json.loads(self.response_data) if self.response_data else {}
        except (json.JSONDecodeError, TypeError):
            result['response_data'] = {}
        
        try:
            result['headers'] = json.loads(self.headers) if self.headers else None
        except (json.JSONDecodeError, TypeError):
            result['headers'] = None
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NetworkData':
        """从字典创建实例"""
        import json
        
        # 处理JSON字段
        if 'response_data' in data and isinstance(data['response_data'], (dict, list)):
            data['response_data'] = json.dumps(data['response_data'], ensure_ascii=False)
        
        if 'headers' in data and isinstance(data['headers'], dict):
            data['headers'] = json.dumps(data['headers'], ensure_ascii=False)
        
        return cls(**data)
