#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ranking Controller
Provides endpoints for stock score rankings (growth and total).
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from typing import List, Optional
from datetime import date

from ..database import get_db_session
from ..models.stock_daily import StockScoreResult
from ..models.stock import StockInfo
from .schemas import BaseResponse

router = APIRouter(prefix="/api/v1/rankings", tags=["Rankings"])

@router.get("/growth", response_model=BaseResponse, summary="Get score growth ranking")
async def get_growth_ranking(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    limit: int = Query(10, ge=1, le=100, description="Limit number of results"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get stock ranking based on score growth between start_date and end_date.
    Growth = Sum(daily_score) in range.
    """
    try:
        service = RankingService(db)
        ranking_data = await service.get_score_growth_ranking(start_date, end_date, limit=limit)
        return BaseResponse(success=True, message="ok", data=ranking_data)

    except Exception as e:
        import logging
        logging.error(f"Error fetching growth ranking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


from ..services.ranking_service import RankingService

@router.get("/total", response_model=BaseResponse, summary="Get total score ranking (250 days)")
async def get_total_ranking(
    target_date: Optional[date] = Query(None, description="Target date (defaults to today)"),
    limit: int = Query(10, ge=1, le=100, description="Limit number of results"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get stock ranking based on sum of total scores for the last 250 days ending at target_date.
    Logic: Sum(daily_score) where trade_date in [target_date - 250 days, target_date]
    """
    try:
        # If no date provided, default to today
        if not target_date:
            target_date = date.today()
            
        service = RankingService(db)
        ranking_data = await service.get_total_score_ranking(target_date, limit=limit)
        
        return BaseResponse(success=True, message="ok", data=ranking_data)
    except Exception as e:
        import logging
        logging.error(f"Error fetching total ranking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 新增GET端点（按日期） ====================

@router.get("/calculate/{calculate_date}", response_model=BaseResponse, summary="按日期计算排名")
async def calculate_ranking_by_date(
    calculate_date: str = Path(..., description="计算日期 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    按日期计算股票排名
    如果该日期没有评分数据，会自动触发Pathway引擎进行计算
    """
    try:
        from datetime import datetime
        target_date = datetime.strptime(calculate_date, "%Y-%m-%d").date()
        
        service = RankingService(db)
        
        # 1. 检查该日期是否已有评分数据
        has_scores = await service.has_scores_for_date(target_date)
        
        message_prefix = "排名数据已存在"
        if not has_scores:
            # 2. 如果没有，触发Pathway引擎计算
            # 导入放在这里避免潜在的循环依赖
            from ..services.pathway_engine import PathwayVolumePriceEngine
            engine = PathwayVolumePriceEngine(db)
            
            # 计算该日期的评分
            await engine.calculate_daily_scores(target_date)
            message_prefix = "排名计算完成(新触发)"
        
        # 3. 获取排名数据
        ranking_data = await service.get_total_score_ranking(target_date, limit=1000)
        
        return BaseResponse(
            success=True,
            message=f"{message_prefix}，日期: {calculate_date}",
            data=ranking_data
        )
    except Exception as e:
        import logging
        logging.error(f"Error calculating ranking: {e}")
        raise HTTPException(status_code=500, detail=str(e))
