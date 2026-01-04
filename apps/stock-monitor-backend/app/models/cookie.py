#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cookie数据模型
"""

from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel

class ChromeCookie(BaseModel):
    """Chrome浏览器Cookie表"""
    __tablename__ = "chrome_cookies"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    domain: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, comment="域名")
    cookies_json: Mapped[str] = mapped_column(Text, nullable=False, comment="Cookie JSON数据")
