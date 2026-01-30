# -*- coding: utf-8 -*-
from typing import Optional
from fastapi import APIRouter, Body, HTTPException, Query, Request
from pydantic import BaseModel, Field
from app.services.okooo_service import okooo_service
from app.services.sse_service import sse_service
from app.api.schemas import BaseResponse

router = APIRouter(prefix="/api/v1/okooo", tags=["Okooo竞彩"])

@router.get("/matches", summary="从数据库获取比赛列表", response_model=BaseResponse)
async def get_db_matches(date: Optional[str] = Query(None, description="日期 (YYYY-MM-DD)")):
    matches = await okooo_service.get_db_matches(date)
    return BaseResponse(success=True, data=matches)

@router.get("/matches/dates", summary="获取有比赛的日期列表", response_model=BaseResponse)
async def get_matches_dates():
    dates = await okooo_service.get_matches_dates()
    return BaseResponse(success=True, data=dates)

class CrawlRequest(BaseModel):
    start_id: int = Field(..., description="起始比赛ID", example=1143895)
    end_id: int = Field(..., description="结束比赛ID", example=1143900)

class CrawlConfig(BaseModel):
    headless: bool = Field(True, description="是否使用无头模式")
    use_cache: bool = Field(False, description="是否使用会话缓存")
    use_proxy: bool = Field(False, description="是否使用代理")

class CrawlIdsRequest(BaseModel):
    match_ids: list[str] = Field(..., description="比赛ID列表")
    headless: bool = Field(True, description="是否使用无头模式")
    use_cache: bool = Field(False, description="是否使用会话缓存")
    force: bool = Field(False, description="是否强制爬取（忽略去重）")
    use_proxy: bool = Field(False, description="是否使用代理")

@router.post("/start_ids", summary="启动Okooo指定ID爬虫", response_model=BaseResponse)
async def start_crawl_ids(request: CrawlIdsRequest):
    success = await okooo_service.start_crawl_ids(request.match_ids, request.headless, request.use_cache, request.force, request.use_proxy)
    if success:
        return BaseResponse(success=True, message="指定ID爬虫任务已启动")
    else:
        return BaseResponse(success=False, message="爬虫正在运行中，请先停止或等待结束")

@router.post("/start", summary="启动Okooo爬虫", response_model=BaseResponse)
async def start_crawl(request: CrawlRequest):
    if request.start_id > request.end_id:
        return BaseResponse(success=False, message="起始ID不能大于结束ID")
        
    success = await okooo_service.start_crawl(request.start_id, request.end_id)
    if success:
        return BaseResponse(success=True, message="爬虫任务已启动")
    else:
        return BaseResponse(success=False, message="爬虫正在运行中，请先停止或等待结束")

@router.post("/start_lists", summary="启动Okooo列表爬虫", response_model=BaseResponse)
async def start_crawl_lists(config: CrawlConfig = Body(default=CrawlConfig())):
    success = await okooo_service.start_crawl_lists(config.headless, config.use_cache, config.use_proxy)
    if success:
        return BaseResponse(success=True, message="列表爬虫任务已启动")
    else:
        return BaseResponse(success=False, message="爬虫正在运行中，请先停止或等待结束")

@router.post("/fetch_lists", summary="获取Okooo比赛列表", response_model=BaseResponse)
async def fetch_match_lists(config: CrawlConfig = Body(default=CrawlConfig())):
    try:
        matches = await okooo_service.fetch_match_lists(config.headless, config.use_cache, config.use_proxy)
        return BaseResponse(success=True, data=matches)
    except Exception as e:
        return BaseResponse(success=False, message=str(e))

@router.post("/stop", summary="停止Okooo爬虫", response_model=BaseResponse)
async def stop_crawl():
    await okooo_service.stop_crawl()
    return BaseResponse(success=True, message="停止指令已发送")

@router.get("/status", summary="获取Okooo爬虫实时状态(SSE)", description="Server-Sent Events 实时日志流")
async def get_status(request: Request):
    """
    获取Okooo爬虫实时状态日志 (SSE模式)
    """
    return await sse_service.subscribe(request)

class OkoooLogRequest(BaseModel):
    message: str = Field(..., description="日志内容")
    level: str = Field("info", description="日志级别")
    timestamp: Optional[str] = Field(None, description="时间戳")

@router.post("/log", summary="接收爬虫日志(SSE广播)", response_model=BaseResponse)
async def receive_log(request: OkoooLogRequest):
    """
    接收前端爬虫日志并广播到 SSE 流
    """
    from datetime import datetime
    data = {
        "message": request.message,
        "level": request.level,
        "timestamp": request.timestamp or datetime.now().strftime("%H:%M:%S")
    }
    await sse_service.broadcast("log", data)
    return BaseResponse(success=True)

class OkoooHistoryCaptureRequest(BaseModel):
    url: str = Field(..., description="比赛详情页 URL")
    match_id: str = Field(..., description="比赛 ID")
    parent_match_id: str = Field(..., description="父级比赛 ID")
    timestamp: float = Field(..., description="时间戳")
    source: str = Field("okooo_crawler", description="来源")

@router.post("/history-capture", summary="接收历史记录页面捕获", response_model=BaseResponse)
async def capture_history_request(request: OkoooHistoryCaptureRequest):
    """
    接收 Chrome 扩展遍历的历史记录页面 URL
    保存到 data/okooo/history/[date]/[match_id]/
    """
    try:
        result = await okooo_service.capture_history_match(
            url=request.url,
            match_id=request.match_id,
            parent_match_id=request.parent_match_id,
            source=request.source
        )
        return BaseResponse(success=True, data=result)
    except Exception as e:
        return BaseResponse(success=False, message=str(e))

class OkoooHistoryWithTabRequest(BaseModel):
    html: str = Field(..., description="历史记录页面 HTML")
    url: str = Field(..., description="页面 URL")
    match_id: str = Field(..., description="比赛 ID (带 tab 编号)")
    parent_match_id: str = Field(..., description="父级比赛 ID")
    tab_name: str = Field(..., description="Tab 名称")
    captured_at: str = Field(..., description="捕获时间")
    date: str = Field(..., description="日期")

@router.post("/save-history-with-tab", summary="保存历史记录 HTML（带 Tab 名称）", response_model=BaseResponse)
async def save_history_with_tab(request: OkoooHistoryWithTabRequest):
    """
    接收 Chrome 扩展捕获的历史记录页面 HTML（带 tab 编号）
    保存到 data/okooo/history/[date]/[parent_match_id]/[match_id]_[tab_name]/
    """
    try:
        result = await okooo_service.save_history_with_tab(
            html=request.html,
            url=request.url,
            match_id=request.match_id,
            parent_match_id=request.parent_match_id,
            tab_name=request.tab_name,
            captured_at=request.captured_at,
            date=request.date
        )
        return BaseResponse(success=True, data=result)
    except Exception as e:
        return BaseResponse(success=False, message=str(e))

class SqlQueryRequest(BaseModel):
    sql: str = Field(..., description="SQL 查询语句")
    limit: int = Field(100, description="返回结果数量限制")

@router.post("/query-matches", summary="执行 SQL 查询获取比赛数据", response_model=BaseResponse)
async def query_matches(request: SqlQueryRequest):
    """
    执行 SQL 查询语句，返回匹配的比赛数据
    """
    try:
        result = await okooo_service.query_matches(request.sql, request.limit)
        return BaseResponse(success=True, data=result)
    except Exception as e:
        return BaseResponse(success=False, message=str(e))

class OkoooHandicapHtmlRequest(BaseModel):
    html: str = Field(..., description="让球盘页面 HTML")
    url: str = Field(..., description="页面 URL")
    match_id: str = Field(..., description="比赛 ID")
    captured_at: str = Field(..., description="捕获时间")
    date: str = Field(..., description="日期")

@router.post("/save-handicap-html", summary="保存让球盘 HTML", response_model=BaseResponse)
async def save_handicap_html(request: OkoooHandicapHtmlRequest):
    """
    接收 Chrome 扩展捕获的让球盘页面 HTML
    保存到 data/okooo/handicap/[date]/[match_id]/
    """
    try:
        result = await okooo_service.save_handicap_html(
            html=request.html,
            url=request.url,
            match_id=request.match_id,
            captured_at=request.captured_at,
            date=request.date
        )
        return BaseResponse(success=True, data=result)
    except Exception as e:
        return BaseResponse(success=False, message=str(e))

class RepairRequest(BaseModel):
    date: str = Field(..., description="日期 (YYYY-MM-DD)")

@router.post("/repair", summary="检查并修复比赛数据", response_model=BaseResponse)
async def repair_matches(request: RepairRequest):
    """
    检查指定日期的比赛数据完整性，并重新爬取缺失或无效的比赛
    """
    try:
        result = await okooo_service.repair_daily_data(request.date)
        return BaseResponse(success=True, data=result)
    except Exception as e:
        return BaseResponse(success=False, message=str(e))


class OkoooListHtmlRequest(BaseModel):
    html: str = Field(..., description="比赛列表页面 HTML")
    url: str = Field(..., description="页面 URL")
    captured_at: str = Field(..., description="捕获时间")
    date: str = Field(..., description="日期")

@router.post("/save-list-html", summary="保存比赛列表 HTML", response_model=BaseResponse)
async def save_list_html(request: OkoooListHtmlRequest):
    """
    接收 Chrome 扩展捕获的比赛列表 HTML
    保存到 data/okooo/list/[date]/
    """
    try:
        result = await okooo_service.save_list_html(
            html=request.html,
            url=request.url,
            captured_at=request.captured_at,
            date=request.date
        )
        return BaseResponse(success=True, data=result)
    except Exception as e:
        return BaseResponse(success=False, message=str(e))

class OkoooMatchHtmlRequest(BaseModel):
    html: str = Field(..., description="比赛页面 HTML")
    url: str = Field(..., description="页面 URL")
    match_id: str = Field(..., description="比赛 ID")
    page_type: Optional[str] = Field(None, description="页面类型")
    captured_at: str = Field(..., description="捕获时间")
    date: str = Field(..., description="日期")

@router.post("/save-match-html", summary="保存比赛详情 HTML", response_model=BaseResponse)
async def save_match_html(request: OkoooMatchHtmlRequest):
    """
    接收 Chrome 扩展捕获的比赛详情页面 HTML
    保存到 data/okooo/matches/[date]/[match_id]/
    """
    try:
        result = await okooo_service.save_match_html(
            html=request.html,
            url=request.url,
            match_id=request.match_id,
            page_type=request.page_type,
            captured_at=request.captured_at,
            date=request.date
        )
        return BaseResponse(success=True, data=result)
    except Exception as e:
        return BaseResponse(success=False, message=str(e))

class OkoooHistoryHtmlRequest(BaseModel):
    html: str = Field(..., description="历史记录页面 HTML")
    url: str = Field(..., description="页面 URL")
    match_id: str = Field(..., description="比赛 ID")
    parent_match_id: str = Field(..., description="父级比赛 ID")
    page_type: Optional[str] = Field(None, description="页面类型")
    captured_at: str = Field(..., description="捕获时间")
    date: str = Field(..., description="日期")

@router.post("/save-history-html", summary="保存历史记录 HTML", response_model=BaseResponse)
async def save_history_html(request: OkoooHistoryHtmlRequest):
    """
    接收 Chrome 扩展捕获的历史记录页面 HTML
    保存到 data/okooo/history/[date]/[parent_match_id]/[match_id]/
    """
    try:
        result = await okooo_service.save_history_html(
            html=request.html,
            url=request.url,
            match_id=request.match_id,
            parent_match_id=request.parent_match_id,
            page_type=request.page_type,
            captured_at=request.captured_at,
            date=request.date
        )
        return BaseResponse(success=True, data=result)
    except Exception as e:
        return BaseResponse(success=False, message=str(e))
