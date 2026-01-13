#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票评分结果查询接口
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Path
from typing import Optional, List
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from loguru import logger

from app.database import get_db_session, db_manager
from app.models.stock_daily import StockScoreResult
from app.api.stock_daily_schemas import StockScoreResultListResponse, StockScoreResultResponse
from app.api.schemas import BaseResponse
from app.services.rule_engine_service import RuleEngineService
from app.services.pathway_engine import PathwayVolumePriceEngine
from datetime import datetime

router = APIRouter(prefix="/api/v1/scores", tags=["评分结果"])

@router.post("/calculate/{date_str}", response_model=BaseResponse, summary="触发每日评分计算")
async def calculate_daily_scores(
    date_str: str = Path(..., description="日期 YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    触发指定日期的 Pathway 积分计算
    """
    try:
        if date_str == "today":
            target_date = datetime.now().date()
        else:
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return BaseResponse(success=False, message="日期格式错误，应为 YYYY-MM-DD 或 today")

        engine = PathwayVolumePriceEngine(db)
        
        # 1. 运行计算
        logger.info(f"开始计算 {target_date} 的 Pathway 积分")
        results = await engine.calculate_daily_scores(target_date)
        
        # 2. (可选) 触发告警检查
        # alerts = await engine.check_anomalies(results)
        
        return BaseResponse(
            data={"count": len(results)}, 
            message=f"计算完成，共生成 {len(results)} 条评分记录"
        )
    except Exception as e:
        logger.error(f"评分计算失败: {e}", exc_info=True)
        return BaseResponse(success=False, message=f"计算失败: {str(e)}")

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


# ==================== 新增GET端点（按日期） ====================

def get_rule_engine_service() -> RuleEngineService:
    return RuleEngineService(db_manager)


@router.get("/calculate/{calculate_date}/{batch_id}", response_model=BaseResponse, summary="按日期计算评分")
async def calculate_scores_by_date(
    calculate_date: str = Path(..., description="计算日期 (YYYY-MM-DD)"),
    batch_id: int = Path(..., description="批次ID"),
    db: AsyncSession = Depends(get_db_session),
    service: RuleEngineService = Depends(get_rule_engine_service)
):
    """
    按日期计算所有股票的评分
    """
    try:
        from datetime import datetime
        target_date = datetime.strptime(calculate_date, "%Y-%m-%d").date()
        
        result = await service.calculate_daily_scores(target_date=target_date, force=True)
        
        if result["status"] == "success":
            return BaseResponse(
                success=True,
                message=f"评分计算完成，日期: {calculate_date}",
                data=result
            )
        else:
            return BaseResponse(
                success=False,
                message=result.get("error", "计算失败"),
                data=None
            )
    except Exception as e:
        logger.error(f"按日期计算评分失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calculate/{calculate_date}/{code}", response_model=BaseResponse, summary="按日期计算单只股票评分")
async def calculate_single_stock_by_date(
    calculate_date: str = Path(..., description="计算日期 (YYYY-MM-DD)"),
    code: str = Path(..., description="股票代码"),
    db: AsyncSession = Depends(get_db_session),
    service: RuleEngineService = Depends(get_rule_engine_service)
):
    """
    按日期计算单只股票的评分
    """
    try:
        from datetime import datetime
        target_date = datetime.strptime(calculate_date, "%Y-%m-%d").date()
        
        result = await service.calculate_daily_scores(target_date=target_date, force=True, stock_code=code)
        
        if result["status"] == "success":
            return BaseResponse(
                success=True,
                message=f"股票 {code} 评分计算完成，日期: {calculate_date}",
                data=result
            )
        else:
            return BaseResponse(
                success=False,
                message=result.get("error", "计算失败"),
                data=None
            )
    except Exception as e:
        logger.error(f"按日期计算单只股票评分失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
