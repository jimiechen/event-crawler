#!/usr/bin/env python3
"""
Okooo解析API控制器
"""
from fastapi import APIRouter, Query, BackgroundTasks
from typing import Optional, List
from pydantic import BaseModel
from loguru import logger

from app.api.schemas import BaseResponse
from app.services.okooo_parser_service import okooo_parser_service

router = APIRouter(prefix="/api/v1/okooo", tags=["Okooo解析"])


class ParseDailyRequest(BaseModel):
    date: Optional[str] = None  # YYYY-MM-DD，None或"auto"表示当天


class ParseBatchRequest(BaseModel):
    dates: List[str]  # 批量解析多个日期


@router.post("/parse/daily", summary="解析指定日期的所有比赛", response_model=BaseResponse)
async def parse_daily_matches(
    request: ParseDailyRequest,
    background: bool = Query(True, description="是否后台执行")
):
    """
    解析指定日期的所有比赛数据
    - date: 日期 (YYYY-MM-DD)，不传或传"auto"则使用当天
    - background: 是否后台异步执行
    """
    try:
        date_str = request.date if request.date and request.date != "auto" else None

        if background:
            # 后台异步执行
            import asyncio
            asyncio.create_task(okooo_parser_service.parse_daily_matches(date_str))
            return BaseResponse(
                success=True,
                message=f"解析任务已提交: {date_str or '当天'}"
            )
        else:
            # 同步执行
            result = await okooo_parser_service.parse_daily_matches(date_str)
            return BaseResponse(
                success=result["success"],
                data=result,
                message=f"解析完成: {result.get('processed', 0)}/{result.get('total', 0)}"
            )
    except Exception as e:
        logger.error(f"解析任务失败: {e}")
        return BaseResponse(success=False, message=str(e))


@router.post("/parse/batch", summary="批量解析多个日期", response_model=BaseResponse)
async def parse_batch_dates(request: ParseBatchRequest):
    """批量解析多个日期的比赛数据"""
    results = []
    for date_str in request.dates:
        result = await okooo_parser_service.parse_daily_matches(date_str)
        results.append(result)

    total_processed = sum(r.get("processed", 0) for r in results)
    total_failed = sum(r.get("failed", 0) for r in results)

    return BaseResponse(
        success=True,
        data={"results": results, "total_processed": total_processed, "total_failed": total_failed},
        message=f"批量解析完成: {total_processed} 成功, {total_failed} 失败"
    )


@router.post("/parse/match", summary="解析指定比赛", response_model=BaseResponse)
async def parse_specific_match(
    date: str = Query(..., description="日期 (YYYY-MM-DD)"),
    match_id: str = Query(..., description="比赛ID")
):
    """解析指定日期和比赛ID的数据"""
    try:
        result = await okooo_parser_service.parse_specific_match(date, match_id)
        return BaseResponse(
            success=result["success"],
            data=result,
            message="解析成功" if result["success"] else result.get("error", "解析失败")
        )
    except Exception as e:
        return BaseResponse(success=False, message=str(e))


@router.get("/parse/dates", summary="获取可解析的日期列表", response_model=BaseResponse)
async def get_available_dates():
    """获取所有可解析的日期列表"""
    try:
        dates = okooo_parser_service.get_available_dates()
        return BaseResponse(success=True, data=dates, message=f"共 {len(dates)} 个日期")
    except Exception as e:
        return BaseResponse(success=False, message=str(e))
