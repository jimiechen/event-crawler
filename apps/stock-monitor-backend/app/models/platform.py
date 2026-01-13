#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台配置和会话模型
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class PlatformConfig(BaseModel):
    """平台配置表"""
    __tablename__ = "platform_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    platform_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="平台标识(weibo/bilibili等)")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="平台名称")
    domain: Mapped[str] = mapped_column(String(255), nullable=False, comment="Cookie域名")
    login_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="登录URL")
    home_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="首页URL")
    verify_api: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="验证API")
    verify_type: Mapped[str] = mapped_column(String(20), default="json", comment="验证类型(json/text)")
    verify_xpath: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="XPath配置")
    verify_parser: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="解析器配置(JSON)")
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="平台图标(emoji)")

    __table_args__ = (
        Index("idx_platform_id", "platform_id"),
        {"comment": "平台配置表"}
    )


class PlatformSession(BaseModel):
    """平台会话表"""
    __tablename__ = "platform_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    platform_id: Mapped[str] = mapped_column(String(50), nullable=False, comment="平台标识")
    user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="用户ID/账号标识")
    account_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="账号名称/昵称")
    cookies_json: Mapped[str] = mapped_column(Text, nullable=False, comment="Cookie JSON数据")
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="User-Agent")
    status: Mapped[str] = mapped_column(String(20), default="active", comment="状态(active/expired/unknown)")
    health_score: Mapped[int] = mapped_column(Integer, default=100, comment="健康度评分(0-100)")
    last_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="最后验证时间")
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="最后使用时间")

    __table_args__ = (
        Index("idx_platform_user", "platform_id", "user_id"),
        Index("idx_session_status", "status"),
        Index("idx_health_score", "health_score"),
        {"comment": "平台会话表"}
    )
