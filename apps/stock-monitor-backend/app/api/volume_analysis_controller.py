#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成交量异动分析控制器
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy import select, func, desc
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..database import db_manager, get_db_session
from ..services.volume_analysis_service import VolumeAnalysisService
from ..models.volume_analysis import StockVolumeBaseline
from .schemas import BaseResponse

router = APIRouter(prefix="/api/v1/volume-analysis", tags=["成交量异动分析"])

class LogRequest(BaseModel):
    code: str
    rule_name: str
    is_match: bool
    details: str

class AlertRequest(BaseModel):
    code: str
    alert_type: str
    message: str

class LowVolumeRecordRequest(BaseModel):
    code: str
    trade_date: str
    days: int
    volume: float

import traceback

@router.get("/baselines", response_model=BaseResponse)
async def get_baseline_list(
    page: int = 1,
    page_size: int = 20,
    code: Optional[str] = None,
    session: AsyncSession = Depends(get_db_session)
):
    """
    获取基准数据列表
    """
    try:
        stmt = select(StockVolumeBaseline)
        if code:
            stmt = stmt.where(StockVolumeBaseline.code.like(f"%{code}%"))
        
        # Count total
        # Create subquery correctly
        subq = stmt.subquery()
        count_stmt = select(func.count()).select_from(subq)
        total = await session.scalar(count_stmt) or 0
        
        # Pagination
        stmt = stmt.order_by(desc(StockVolumeBaseline.updated_at)).offset((page - 1) * page_size).limit(page_size)
        result = await session.execute(stmt)
        items = result.scalars().all()
        
        # Convert to dicts to ensure serialization
        items_dict = [item.to_dict() for item in items]
        
        return BaseResponse(data={
            "items": items_dict,
            "total": total,
            "page": page,
            "page_size": page_size
        })
    except Exception as e:
        from loguru import logger
        logger.error(f"Error in get_baseline_list: {e}")
        logger.exception("Traceback:")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.get("/baseline/{code}", response_model=BaseResponse)
async def get_volume_baseline(code: str, session: AsyncSession = Depends(get_db_session)):
    """
    获取股票的成交量异动基准数据
    包含: 最近一次2倍/3倍量收盘价, 最近一次5/10/20/30/60日地量成交量
    """
    # Try to get existing baseline
    baseline = await VolumeAnalysisService.get_baseline(code, session)
    
    # If empty, run analysis first?
    if not baseline:
        # Use internal session management with retry logic for analysis
        baseline = await VolumeAnalysisService.analyze_stock(code)
        
    return BaseResponse(data=baseline)

@router.get("/run/{code}", response_model=BaseResponse)
async def run_analysis(code: str, session: AsyncSession = Depends(get_db_session)):
    """
    手动触发异动分析并保存结果
    """
    try:
        # Use internal session management with retry logic for analysis
        result = await VolumeAnalysisService.analyze_stock(code)
        return BaseResponse(data=result)
    except Exception as e:
        from loguru import logger
        logger.error(f"Error in run_analysis: {e}")
        logger.exception("Traceback:")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.post("/batch-run", response_model=BaseResponse)
async def batch_run_analysis(
    background_tasks: BackgroundTasks,
    batch_size: int = 5,
    session: AsyncSession = Depends(get_db_session)
):
    """
    批量执行全量股票异动分析
    - batch_size: 每批并发执行数量 (默认5)
    - 异步后台执行
    """
    background_tasks.add_task(VolumeAnalysisService.analyze_all_stocks, batch_size)
    return BaseResponse(message=f"全量异动分析任务已启动 (Batch Size: {batch_size})")

@router.post("/log-rule", response_model=BaseResponse)
async def log_rule_calculation(req: LogRequest, session: AsyncSession = Depends(get_db_session)):
    """
    记录规则计算日志
    """
    await VolumeAnalysisService.log_rule_calculation(req.code, req.rule_name, req.is_match, req.details, session)
    return BaseResponse(message="日志已记录")

@router.get("/anomalies", summary="Get volume anomalies for a stock")
async def get_volume_anomalies(
    code: str = Query(..., description="Stock Code"),
    start_date: date = Query(..., description="Start Date"),
    end_date: date = Query(..., description="End Date"),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get volume anomalies for a specific stock in a date range.
    Replaces client-side detection in test-tool.html.
    """
    try:
        results = await VolumeAnalysisService.get_anomalies(code, start_date, end_date, session)
        return BaseResponse(success=True, data=results)
    except Exception as e:
        import logging
        logging.error(f"Error getting anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/log-alert", response_model=BaseResponse)
async def log_alert(req: AlertRequest, session: AsyncSession = Depends(get_db_session)):
    """
    记录告警
    """
    await VolumeAnalysisService.log_alert(req.code, req.alert_type, req.message, session)
    return BaseResponse(message="告警已记录")
@router.post("/record-low-volume", response_model=BaseResponse)
async def record_low_volume(req: LowVolumeRecordRequest, session: AsyncSession = Depends(get_db_session)):
    """
    手动记录地量数据（用于测试或补录）
    """
    # Assuming this updates the main table or logs it.
    # Given the user's request "Insert corresponding low volume record", 
    # we'll assume it's adding to the analysis result if it's a valid date, 
    # but for simulation we might just log it or add to the result table.
    # Let's add to VolumeAnalysisResult.
    
    from ..models.volume_analysis import VolumeAnalysisResult
    from datetime import datetime
    
    try:
        date_obj = datetime.strptime(req.trade_date, "%Y-%m-%d").date()
    except:
        date_obj = datetime.now().date()

    entry = VolumeAnalysisResult(
        code=req.code,
        trade_date=date_obj,
        analysis_type=f"{req.days}日地量",
        value=req.volume,
        description=f"模拟/触发: {req.days}日内地量",
        extra_data={"source": "simulation"}
    )
    session.add(entry)
    await session.commit()
    
    return BaseResponse(message="地量记录已保存")
