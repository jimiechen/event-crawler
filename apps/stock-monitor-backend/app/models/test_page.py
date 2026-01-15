#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试页面模型
用于存储测试页面的配置和结果
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.sql.sqltypes import JSON
from datetime import datetime

from app.models.base import Base


class TestPage(Base):
    """测试页面模型"""
    __tablename__ = "test_pages"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    name = Column(String(200), nullable=False, comment="测试页面名称")
    url = Column(Text, nullable=False, comment="测试页面URL")
    platform = Column(String(50), nullable=False, comment="平台标识")
    description = Column(Text, nullable=True, comment="页面描述")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    test_results = Column(JSON, nullable=True, comment="测试结果")


class TestResult(Base):
    """测试结果模型"""
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    test_page_id = Column(Integer, nullable=False, comment="测试页面ID")
    test_type = Column(String(50), nullable=False, comment="测试类型：session/crawler")
    status = Column(String(20), nullable=False, comment="测试状态：success/failed/pending")
    message = Column(Text, nullable=True, comment="测试消息")
    result_data = Column(JSON, nullable=True, comment="测试结果数据")
    tested_at = Column(DateTime, default=datetime.now, comment="测试时间")
    duration_ms = Column(Integer, nullable=True, comment="测试耗时（毫秒）")