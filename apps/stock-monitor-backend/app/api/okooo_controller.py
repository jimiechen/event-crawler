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

class CrawlIdsRequest(BaseModel):
    match_ids: list[str] = Field(..., description="比赛ID列表")
    headless: bool = Field(True, description="是否使用无头模式")
    use_cache: bool = Field(False, description="是否使用会话缓存")
    force: bool = Field(False, description="是否强制爬取（忽略去重）")

@router.post("/start_ids", summary="启动Okooo指定ID爬虫", response_model=BaseResponse)
async def start_crawl_ids(request: CrawlIdsRequest):
    success = await okooo_service.start_crawl_ids(request.match_ids, request.headless, request.use_cache, request.force)
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
    success = await okooo_service.start_crawl_lists(config.headless, config.use_cache)
    if success:
        return BaseResponse(success=True, message="列表爬虫任务已启动")
    else:
        return BaseResponse(success=False, message="爬虫正在运行中，请先停止或等待结束")

@router.post("/fetch_lists", summary="获取Okooo比赛列表", response_model=BaseResponse)
async def fetch_match_lists(config: CrawlConfig = Body(default=CrawlConfig())):
    try:
        matches = await okooo_service.fetch_match_lists(config.headless, config.use_cache)
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
