#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API数据模型
定义请求和响应的数据结构
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, ConfigDict


# 基础响应模型
class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


# 股票相关模型
class StockInfoCreate(BaseModel):
    """创建股票信息请求"""
    stock_code: str = Field(..., min_length=6, max_length=6, description="股票代码")
    stock_name: Optional[str] = Field(default=None, max_length=50, description="股票名称")
    market: str = Field(default="SZ", description="市场代码")
    industry: Optional[str] = Field(None, max_length=50, description="行业")
    is_active: bool = Field(default=True, description="是否活跃")
    
    @field_validator('stock_code')
    @classmethod
    def validate_stock_code(cls, v):
        if not v.isdigit():
            raise ValueError('股票代码必须为6位数字')
        return v


class StockInfoUpdate(BaseModel):
    """更新股票信息请求"""
    stock_name: Optional[str] = Field(None, min_length=1, max_length=50, description="股票名称")
    market: Optional[str] = Field(None, description="市场代码")
    industry: Optional[str] = Field(None, max_length=50, description="行业")
    is_active: Optional[bool] = Field(None, description="是否活跃")


class StockInfoResponse(BaseModel):
    """股票信息响应"""
    id: int
    code: str
    name: str
    market: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class StockDataCreate(BaseModel):
    """创建股票数据请求"""
    stock_code: str = Field(..., min_length=6, max_length=6, description="股票代码")
    price: Decimal = Field(..., gt=0, description="股票价格")
    volume: int = Field(default=0, ge=0, description="成交量")
    turnover: Decimal = Field(default=Decimal(0), ge=0, description="成交额")
    change_amount: Decimal = Field(default=Decimal(0), description="涨跌额")
    change_percent: Decimal = Field(default=Decimal(0), description="涨跌幅")
    high_price: Optional[Decimal] = Field(None, gt=0, description="最高价")
    low_price: Optional[Decimal] = Field(None, gt=0, description="最低价")
    open_price: Optional[Decimal] = Field(None, gt=0, description="开盘价")
    close_price: Optional[Decimal] = Field(None, gt=0, description="收盘价")
    data_time: Optional[datetime] = Field(None, description="数据时间")
    
    @field_validator('stock_code')
    @classmethod
    def validate_stock_code(cls, v):
        if not v.isdigit():
            raise ValueError('股票代码必须为6位数字')
        return v


class StockDataBatchCreate(BaseModel):
    """批量创建股票数据请求"""
    data_list: List[StockDataCreate] = Field(..., min_length=1, max_length=1000, description="股票数据列表")


class StockDataResponse(BaseModel):
    """股票数据响应"""
    id: int
    stock_code: str = Field(alias="code")
    price: Decimal
    volume: int
    turnover: Decimal
    change_amount: Decimal
    change_percent: Decimal
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    open_price: Optional[Decimal] = None
    close_price: Optional[Decimal] = None
    timestamp: datetime = Field(alias="data_time")
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class StockTdxRiskResponse(BaseModel):
    """通达信风险数据响应"""
    id: int
    stock_code: str
    stock_name: Optional[str] = None
    date: date
    total_score: int = 0
    total_items: int = 0
    risk_items: int = 0
    safe_items: int = 0
    highlight_items: int = 0
    raw_json: Optional[Dict[str, Any]] = None
    change_percent: Optional[Decimal] = None
    volume: Optional[int] = None
    turnover: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    open_price: Optional[Decimal] = None
    timestamp: date
    
    model_config = ConfigDict(from_attributes=True)


class StockDataQuery(BaseModel):
    """股票数据查询参数"""
    stock_code: str = Field(..., description="股票代码")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    limit: int = Field(default=100, ge=1, le=500, description="返回数量限制")


class BatchSubmitResponse(BaseModel):
    """批量提交响应"""
    success: int = Field(..., description="成功数量")
    failed: int = Field(..., description="失败数量")
    duplicated: int = Field(..., description="重复数量")
    total: int = Field(..., description="总数量")
    errors: List[str] = Field(default=[], description="错误信息列表")


# 监控相关模型
class MonitorCreate(BaseModel):
    """创建监控请求"""
    stock_code: str = Field(..., min_length=6, max_length=6, description="股票代码")
    priority: int = Field(default=1, ge=1, le=10, description="优先级(1-10)")
    auto_create_stock: bool = Field(default=True, description="自动创建股票信息")
    
    @field_validator('stock_code')
    @classmethod
    def validate_stock_code(cls, v):
        if not v.isdigit():
            raise ValueError('股票代码必须为6位数字')
        return v


class MonitorUpdate(BaseModel):
    """更新监控请求"""
    priority: Optional[int] = Field(None, ge=1, le=10, description="优先级(1-10)")
    is_active: Optional[bool] = Field(None, description="是否活跃")


class MonitorResponse(BaseModel):
    """监控响应"""
    id: int
    stock_code: str
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MonitorWithStockResponse(BaseModel):
    """监控及股票信息响应"""
    monitor_id: int
    stock_code: str
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    stock_info: Optional[Dict[str, Any]]


class MonitorWithDataResponse(BaseModel):
    """监控及最新数据响应"""
    monitor_id: int
    stock_code: str
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    stock_info: Optional[Dict[str, Any]]
    latest_data: Optional[Dict[str, Any]]


class MonitorBatchCreate(BaseModel):
    """批量创建监控请求"""
    stock_codes: List[str] = Field(..., min_length=1, max_length=100, description="股票代码列表")
    default_priority: int = Field(default=1, ge=1, le=10, description="默认优先级")
    
    @field_validator('stock_codes')
    @classmethod
    def validate_stock_codes(cls, v):
        for code in v:
            if not isinstance(code, str) or len(code) != 6 or not code.isdigit():
                raise ValueError(f'无效的股票代码: {code}')
        return v


class MonitorBatchUpdate(BaseModel):
    """批量更新监控请求"""
    updates: List[Dict[str, Any]] = Field(..., min_length=1, max_length=100, description="更新列表")


class MonitorBatchOperation(BaseModel):
    """批量操作监控请求"""
    stock_codes: List[str] = Field(..., min_length=1, max_length=100, description="股票代码列表")
    
    @field_validator('stock_codes')
    @classmethod
    def validate_stock_codes(cls, v):
        for code in v:
            if not isinstance(code, str) or len(code) != 6 or not code.isdigit():
                raise ValueError(f'无效的股票代码: {code}')
        return v


class BatchOperationResponse(BaseModel):
    """批量操作响应"""
    success: int = Field(..., description="成功数量")
    failed: int = Field(..., description="失败数量")
    total: int = Field(..., description="总数量")
    errors: List[str] = Field(default=[], description="错误信息列表")


# 统计相关模型
class StockStatisticsResponse(BaseModel):
    """股票统计响应"""
    stock_code: str
    period_days: int
    data_count: int
    price_stats: Dict[str, Any]
    volume_stats: Dict[str, Any]
    time_range: Dict[str, Any]
    price_change: Optional[Dict[str, Any]] = None


class MonitorStatisticsResponse(BaseModel):
    """监控统计响应"""
    total_monitors: int
    active_monitors: int
    inactive_monitors: int
    stocks_with_data: int
    stocks_without_data: int
    priority_distribution: Dict[str, int]


class DedupStatisticsResponse(BaseModel):
    """去重统计响应"""
    total_logs: int
    unique_hashes: int
    period_days: int
    stocks_processed: int
    avg_logs_per_stock: float


# 健康检查模型
class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = "healthy"
    timestamp: datetime
    version: str = "1.0.0"
    uptime: Optional[float] = None
    database: Optional[Dict[str, Any]] = None
    services: Optional[Dict[str, Any]] = None


# 查询参数模型
class PaginationParams(BaseModel):
    """分页参数"""
    limit: int = Field(default=100, ge=1, le=500, description="每页数量")
    offset: int = Field(default=0, ge=0, description="偏移量")


class StockListQuery(PaginationParams):
    """股票列表查询参数"""
    market: Optional[str] = Field(None, description="市场代码")
    active_only: bool = Field(default=True, description="仅活跃股票")


class MonitorListQuery(PaginationParams):
    """监控列表查询参数"""
    active_only: bool = Field(default=True, description="仅活跃监控")
    priority_filter: Optional[int] = Field(None, ge=1, le=10, description="优先级过滤")
    include_stock_info: bool = Field(default=False, description="包含股票信息")
    include_latest_data: bool = Field(default=False, description="包含最新数据")


class AlertQuery(BaseModel):
    """告警查询参数"""
    hours: int = Field(default=24, ge=1, le=168, description="检查小时数")


# 通用列表响应模型
class ListResponse(BaseModel):
    """列表响应模型"""
    items: List[Any]
    total: int
    limit: int
    offset: int
    has_more: bool


# 问财数据相关模型
class WencaiStockData(BaseModel):
    """问财股票数据模型"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    current_price: Optional[Decimal] = Field(None, description="现价")
    price_change: Optional[Decimal] = Field(None, description="涨跌额")
    price_change_percent: Optional[Decimal] = Field(None, description="涨跌幅(%)")
    volume: Optional[int] = Field(None, description="成交量")
    turnover: Optional[Decimal] = Field(None, description="成交额")
    amplitude: Optional[Decimal] = Field(None, description="振幅(%)")
    highest_price: Optional[Decimal] = Field(None, description="最高价")
    lowest_price: Optional[Decimal] = Field(None, description="最低价")
    opening_price: Optional[Decimal] = Field(None, description="今开")
    previous_close: Optional[Decimal] = Field(None, description="昨收")
    volume_ratio: Optional[Decimal] = Field(None, description="量比")
    turnover_rate: Optional[Decimal] = Field(None, description="换手率(%)")
    pe_ratio: Optional[Decimal] = Field(None, description="市盈率(动态)")
    pb_ratio: Optional[Decimal] = Field(None, description="市净率")
    total_market_value: Optional[Decimal] = Field(None, description="总市值")
    circulating_market_value: Optional[Decimal] = Field(None, description="流通市值")
    speed_60_days: Optional[Decimal] = Field(None, description="60日涨跌幅(%)")
    speed_year_to_date: Optional[Decimal] = Field(None, description="年初至今涨跌幅(%)")
    company_address: Optional[str] = Field(None, description="公司地址")
    business_scope: Optional[str] = Field(None, description="经营范围")


class WencaiParseRequest(BaseModel):
    """问财数据解析请求"""
    html_content: str = Field(..., description="问财页面HTML内容")
    batch_name: Optional[str] = Field(None, description="批次名称")
    crawl_url: Optional[str] = Field(None, description="抓取URL")
    query_string: Optional[str] = Field(None, description="查询条件")


class WencaiValidateRequest(BaseModel):
    """问财验证请求"""
    stock_code: str = Field(..., description="股票代码")
    check_date: Optional[str] = Field(None, description="校验日期 (YYYY-MM-DD 或 YYYYMMDD)")
    query_template: Optional[str] = Field(None, description="自定义查询模板")


class WencaiValidateResponse(BaseModel):
    """问财验证响应"""
    stock_code: str
    is_valid: bool
    query: str
    found_in_wencai: bool
    added_to_pool: bool
    message: str
    all_found_stocks: List[Dict[str, str]] = []


class WencaiParseFileRequest(BaseModel):
    """问财文件解析请求"""
    file_path: str = Field(..., description="HTML文件路径或文件名")
    batch_name: Optional[str] = Field(None, description="批次名称")
    crawl_url: Optional[str] = Field(None, description="抓取URL")


class WencaiParseResponse(BaseModel):
    """问财解析响应"""
    batch_id: int = Field(..., description="批次ID")
    total_records: int = Field(..., description="总记录数")
    success_records: int = Field(..., description="成功记录数")
    failed_records: int = Field(..., description="失败记录数")
    errors: List[str] = Field(default=[], description="错误信息列表")
    parsed_stocks: List[WencaiStockData] = Field(default=[], description="解析的股票数据")


class WencaiSaveResponse(BaseModel):
    """问财HTML保存响应"""
    file_path: str = Field(..., description="保存的HTML文件路径")
    file_name: str = Field(..., description="保存的HTML文件名")
    file_size: int = Field(..., description="文件大小(字节)")
    saved_at: datetime = Field(..., description="保存时间")


class WencaiBatchResponse(BaseModel):
    """问财批次响应"""
    id: int
    batch_name: str
    crawl_url: Optional[str]
    total_records: int
    success_records: int
    failed_records: int
    status: str
    error_message: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    created_by: str
    
    model_config = ConfigDict(from_attributes=True)


class WencaiStockResponse(BaseModel):
    """问财股票数据响应"""
    id: int
    stock_code: str
    stock_name: str
    current_price: Optional[Decimal]
    price_change: Optional[Decimal]
    price_change_percent: Optional[Decimal]
    volume: Optional[int]
    turnover: Optional[Decimal]
    amplitude: Optional[Decimal]
    highest_price: Optional[Decimal]
    lowest_price: Optional[Decimal]
    opening_price: Optional[Decimal]
    previous_close: Optional[Decimal]
    volume_ratio: Optional[Decimal]
    turnover_rate: Optional[Decimal]
    pe_ratio: Optional[Decimal]
    pb_ratio: Optional[Decimal]
    total_market_value: Optional[Decimal]
    circulating_market_value: Optional[Decimal]
    speed_60_days: Optional[Decimal]
    speed_year_to_date: Optional[Decimal]
    company_address: Optional[str]
    business_scope: Optional[str]
    crawl_batch_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# 网络数据相关模型
class NetworkDataCreate(BaseModel):
    """创建网络数据请求"""
    url: str = Field(..., description="请求URL")
    method: str = Field(default="GET", description="请求方法")
    response_data: Dict[str, Any] = Field(..., description="响应数据")
    data_size: int = Field(default=0, ge=0, description="数据大小(字节)")
    source: str = Field(default="unknown", description="数据来源")
    request_id: Optional[str] = Field(None, description="请求ID")
    user_agent: Optional[str] = Field(None, description="用户代理")
    headers: Optional[Dict[str, str]] = Field(None, description="请求头")


class NetworkDataResponse(BaseModel):
    """网络数据响应"""
    id: int
    url: str
    method: str
    response_data: Dict[str, Any]
    data_size: int
    source: str
    request_id: Optional[str]
    user_agent: Optional[str]
    headers: Optional[Dict[str, str]]
    timestamp: datetime
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class NetworkDataQuery(BaseModel):
    """网络数据查询参数"""
    url_filter: Optional[str] = Field(None, description="URL过滤关键词")
    source: Optional[str] = Field(None, description="数据源过滤")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=50, ge=1, le=500, description="每页数量")


class NetworkDataListResponse(BaseModel):
    """网络数据列表响应"""
    data: List[NetworkDataResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class NetworkDataStatsResponse(BaseModel):
    """网络数据统计响应"""
    total_count: int = Field(..., description="总数量")
    total_size: int = Field(..., description="总大小(字节)")
    source_stats: Dict[str, int] = Field(..., description="来源统计")
    recent_count: int = Field(..., description="最近1小时数量")
    last_update: Optional[datetime] = Field(None, description="最后更新时间")
# 仪表盘相关模型
class DashboardStatisticsResponse(BaseModel):
    """仪表盘统计数据响应"""
    total_stocks: int
    active_stocks: int
    today_wencai_count: int
    last_update_time: Optional[datetime]

class DashboardStockItem(BaseModel):
    """仪表盘股票列表项"""
    code: str
    name: str
    is_active: bool
    market: str
    latest_price: Optional[float] = None
    sync_250d_kline: bool = False
    sync_incremental: bool = False
    is_held: bool = False
    volume_anomaly_score: int = 0
    tdx_plugin_score: int = 0
    score_update_time: Optional[datetime] = None
    bonus_items: Optional[str] = None

class DashboardStockExtraResponse(BaseModel):
    """仪表盘股票额外信息响应"""
    code: str
    tdx_plugin_score: int
    has_history_data: bool
    has_incremental_data: bool
    sparkline_data: List[float]

class DashboardWencaiItem(BaseModel):
    """仪表盘问财列表项"""
    id: int
    stock_code: str
    stock_name: str
    date_tag: str
    tags: str
    created_at: datetime

class DashboardStockListResponse(BaseModel):
    """仪表盘股票列表响应"""
    total: int
    items: List[DashboardStockItem]
    page: int
    page_size: int

class DashboardWencaiListResponse(BaseModel):
    """仪表盘问财列表响应"""
    total: int
    items: List[DashboardWencaiItem]
    page: int
    page_size: int
