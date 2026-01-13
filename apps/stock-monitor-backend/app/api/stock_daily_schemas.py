#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务相关数据Schema
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from .schemas import BaseResponse

# Pagination Params usually are query params, but if we need a schema:
class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20

# --- StockDaily Schemas ---
class StockDailyBase(BaseModel):
    code: str = Field(..., description="股票代码")
    trade_date: date = Field(..., description="交易日期")
    open: Optional[Decimal] = Field(None, description="开盘价")
    close: Optional[Decimal] = Field(None, description="收盘价")
    high: Optional[Decimal] = Field(None, description="最高价")
    low: Optional[Decimal] = Field(None, description="最低价")
    vol: Optional[int] = Field(None, description="成交量(手)")
    amount: Optional[Decimal] = Field(None, description="成交额(千元)")

class StockDailyCreate(StockDailyBase):
    pass

class StockDailyUpdate(BaseModel):
    open: Optional[Decimal] = None
    close: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    vol: Optional[int] = None
    amount: Optional[Decimal] = None

class StockDailyResponse(StockDailyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- StockScoreResult Schemas ---
class StockScoreResultBase(BaseModel):
    code: str = Field(..., description="股票代码")
    trade_date: date = Field(..., description="评分日期")
    rule_scores: Optional[Dict[str, Any]] = Field(None, description="各规则得分详情")
    total_score: Decimal = Field(default=0, description="总分")
    ranking: Optional[int] = Field(None, description="排名")
    pool_type: str = Field(default="unknown", description="股票池类型")

class StockScoreResultCreate(StockScoreResultBase):
    pass

class StockScoreResultResponse(StockScoreResultBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- TaskLog Schemas ---
class TaskLogBase(BaseModel):
    task_name: Optional[str] = Field(None, description="任务名称")
    task_type: Optional[str] = Field(None, description="任务类型")
    task_url: str = Field(..., description="任务URL")
    stock_code: Optional[str] = Field(None, description="股票代码")
    status: str = Field(..., description="状态")
    message: Optional[str] = Field(None, description="执行消息")
    duration: Optional[float] = Field(None, description="耗时(秒)")

class TaskLogCreate(TaskLogBase):
    pass

class TaskLogResponse(TaskLogBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- API Responses ---
class StockDailyListResponse(BaseResponse):
    data: List[StockDailyResponse]
    total: int

class StockDailyPageResponse(BaseResponse):
    data: List[StockDailyResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class StockScoreResultListResponse(BaseResponse):
    data: List[StockScoreResultResponse]
    total: int

class TaskLogListResponse(BaseResponse):
    data: List[TaskLogResponse]
    total: int
