#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cookie数据模型
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel

class ChromeCookie(BaseModel):
    """Chrome浏览器Cookie表"""
    __tablename__ = "chrome_cookies"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    domain: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, comment="域名")
    cookies_json: Mapped[str] = mapped_column(Text, nullable=False, comment="Cookie JSON数据")
    
    # 新增字段
    account_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="账号名称/备注")
    test_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="测试URL")
    xpath_config: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="XPath配置(JSON): {'nickname': '//...', 'avatar': '//...'}")
    status: Mapped[str] = mapped_column(String(20), default="unknown", comment="状态: active, expired, unknown")
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="上次检查时间")
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, comment="Cookie是否有效")
