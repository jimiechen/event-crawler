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
    Growth = Score(end_date) - Score(start_date)
    """
    try:
        # Calculate growth as Sum(total_score) in range
        # User feedback implies "Growth Score" = "Points gained in this period"
        # Since StockScoreResult stores daily scores, we sum them up.
        
        # Also fetch the total score of the LAST day for display if needed (or just return 0/growth)
        # The frontend expects "total_score" field.
        
        # Subquery to get sum of scores in range
        growth_query = select(
            StockScoreResult.code,
            func.sum(StockScoreResult.total_score).label('growth')
        ).where(
            and_(
                StockScoreResult.trade_date >= start_date,
                StockScoreResult.trade_date <= end_date
            )
        ).group_by(
            StockScoreResult.code
        ).order_by(
            desc('growth')
        ).limit(limit)
        
        growth_result = await db.execute(growth_query)
        growth_data = growth_result.all()
        
        # Get names and maybe latest score for context
        ranking_data = []
        if growth_data:
            codes = [row.code for row in growth_data]
            
            # Fetch names
            names_query = select(StockInfo.code, StockInfo.name).where(StockInfo.code.in_(codes))
            names_result = await db.execute(names_query)
            names_map = {row.code: row.name for row in names_result.all()}
            
            # Fetch latest daily score (for "Details" column which often shows latest rule match)
            # Or fetch the score on end_date specifically?
            # Let's try to get score and rule_scores on end_date
            details_query = select(
                StockScoreResult.code, 
                StockScoreResult.total_score,
                StockScoreResult.rule_scores
            ).where(
                and_(
                    StockScoreResult.code.in_(codes),
                    StockScoreResult.trade_date == end_date
                )
            )
            details_result = await db.execute(details_query)
            details_map = {row.code: row for row in details_result.all()}
            
            for row in growth_data:
                code = row.code
                growth = float(row.growth or 0)
                
                detail = details_map.get(code)
                end_score = float(detail.total_score) if detail else 0.0
                rule_scores = detail.rule_scores if detail else {}
                
                ranking_data.append({
                    "code": code,
                    "name": names_map.get(code, code),
                    "growth": growth,
                    "total_score": end_score, # Return end_date score as total_score for consistency with frontend expectations?
                    "rule_scores": rule_scores
                })

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
    Logic: Sum(total_score) where trade_date in [target_date - 250 days, target_date]
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
    """
    try:
        from datetime import datetime
        target_date = datetime.strptime(calculate_date, "%Y-%m-%d").date()
        
        service = RankingService(db)
        ranking_data = await service.get_total_score_ranking(target_date, limit=1000)
        
        return BaseResponse(
            success=True,
            message=f"排名计算完成，日期: {calculate_date}",
            data=ranking_data
        )
    except Exception as e:
        import logging
        logging.error(f"Error calculating ranking: {e}")
        raise HTTPException(status_code=500, detail=str(e))
