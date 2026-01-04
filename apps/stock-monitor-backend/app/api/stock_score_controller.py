#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票评分结果查询接口
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db_session
from app.models.stock_daily import StockScoreResult
from app.api.stock_daily_schemas import StockScoreResultListResponse, StockScoreResultResponse

router = APIRouter(prefix="/api/v1/scores", tags=["评分结果"])

@router.get("/latest", summary="查询评分结果", response_model=StockScoreResultListResponse)
async def get_latest_scores(
    trade_date: Optional[date] = Query(None, description="交易日期"),
    code: Optional[str] = Query(None, description="股票代码"),
    min_score: Optional[float] = Query(None, description="最低总分"),
    pool_type: Optional[str] = Query(None, description="股票池类型"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    查询股票评分结果
    """
    from sqlalchemy import func
    
    if not trade_date:
        # 默认查询有数据的最近一天
        date_query = select(func.max(StockScoreResult.trade_date))
        trade_date = (await db.execute(date_query)).scalar()

    query = select(StockScoreResult)
    
    if trade_date:
        query = query.where(StockScoreResult.trade_date == trade_date)

    if code:
        query = query.where(StockScoreResult.code == code)
    
    if min_score is not None:
        query = query.where(StockScoreResult.total_score >= min_score)
        
    if pool_type:
        query = query.where(StockScoreResult.pool_type == pool_type)
        
    # 计算总数
    count_stmt = select(func.count(StockScoreResult.id))
    if trade_date:
        count_stmt = count_stmt.where(StockScoreResult.trade_date == trade_date)
    if code:
        count_stmt = count_stmt.where(StockScoreResult.code == code)
    if min_score is not None:
        count_stmt = count_stmt.where(StockScoreResult.total_score >= min_score)
    if pool_type:
        count_stmt = count_stmt.where(StockScoreResult.pool_type == pool_type)

    total = (await db.execute(count_stmt)).scalar() or 0
    
    # 排序
    query = query.order_by(StockScoreResult.trade_date.desc(), StockScoreResult.total_score.desc())
    
    # 分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    data = result.scalars().all()
    
    return StockScoreResultListResponse(
        success=True,
        message="ok",
        data=[StockScoreResultResponse.model_validate(item) for item in data],
        total=total
    )

@router.get("/history/{code}", summary="查询股票历史评分", response_model=StockScoreResultListResponse)
async def get_stock_score_history(
    code: str,
    limit: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db_session)
):
    """
    查询某只股票的历史评分记录
    """
    query = select(StockScoreResult).where(StockScoreResult.code == code)\
        .order_by(StockScoreResult.trade_date.desc()).limit(limit)
        
    result = await db.execute(query)
    data = result.scalars().all()
    
    return StockScoreResultListResponse(
        success=True,
        message="ok",
        data=[StockScoreResultResponse.model_validate(item) for item in data],
        total=len(data)
    )
