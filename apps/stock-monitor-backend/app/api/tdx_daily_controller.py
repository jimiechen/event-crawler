#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通达信日线数据API接口
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database import get_db_session
from app.api.schemas import BaseResponse
from app.services.tdx_daily_data_service import TdxDailyDataService
from app.services.daily_review_service import DailyReviewService
from app.models.stock import WencaiStock, WencaiCrawlBatch
from sqlalchemy import select

router = APIRouter(prefix="/api/v1/tdx/daily", tags=["通达信日线数据"])


@router.post("/sync-from-selection", response_model=BaseResponse)
async def sync_daily_data_from_selection(
    batch_id: int,
    days: int = Query(250, ge=1, le=500, description="同步天数"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    根据选股批次同步日线数据
    
    Args:
        batch_id: 选股批次ID
        days: 同步天数，默认250天
    """
    try:
        # 获取批次信息
        batch = await db.get(WencaiCrawlBatch, batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="批次不存在")
        
        if batch.source != 'tdx':
            raise HTTPException(status_code=400, detail="仅支持TDX批次")
        
        # 获取股票列表
        stmt = select(WencaiStock.stock_code).where(
            WencaiStock.crawl_batch_id == str(batch_id)
        )
        result = await db.execute(stmt)
        stocks = [r[0] for r in result.all()]
        
        if not stocks:
            return BaseResponse(
                success=False,
                message="该批次无股票"
            )
        
        # 同步数据
        service = TdxDailyDataService()
        sync_result = await service.sync_daily_data_for_selection(
            stock_codes=stocks,
            end_date=batch.query_date,
            batch_id=batch_id,
            days=days
        )
        
        return BaseResponse(
            success=True,
            message=f"同步完成: {sync_result['total_synced']} 条记录",
            data=sync_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"同步日线数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


@router.post("/review-update", response_model=BaseResponse)
async def update_review_daily_data(
    trade_date: Optional[date] = Query(None, description="复盘日期，默认今天"),
    lookback_days: int = Query(30, ge=1, le=90, description="回溯天数"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    手动触发复盘数据更新
    
    Args:
        trade_date: 复盘日期，默认今天
        lookback_days: 回溯天数，默认30天
    """
    try:
        if trade_date is None:
            trade_date = date.today()
        
        service = DailyReviewService()
        result = await service.update_stock_pool_daily_data(
            trade_date=trade_date,
            lookback_days=lookback_days
        )
        
        if result.get("status") == "success":
            return BaseResponse(
                success=True,
                message=f"复盘更新完成: {result['synced_count']} 条记录",
                data=result
            )
        else:
            return BaseResponse(
                success=False,
                message=f"复盘更新失败: {result.get('error')}"
            )
            
    except Exception as e:
        logger.error(f"复盘更新失败: {e}")
        raise HTTPException(status_code=500, detail=f"复盘更新失败: {str(e)}")


@router.get("/stock-pool/status", response_model=BaseResponse)
async def get_stock_pool_status(
    trade_date: Optional[date] = Query(None, description="日期，默认今天"),
    lookback_days: int = Query(30, ge=1, le=90, description="回溯天数"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取股票池状态
    
    Args:
        trade_date: 日期，默认今天
        lookback_days: 回溯天数，默认30天
    """
    try:
        if trade_date is None:
            trade_date = date.today()
        
        service = DailyReviewService()
        status = await service.get_stock_pool_status(
            trade_date=trade_date,
            lookback_days=lookback_days
        )
        
        return BaseResponse(
            success=True,
            message="获取股票池状态成功",
            data=status
        )
        
    except Exception as e:
        logger.error(f"获取股票池状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/{stock_code}/history", response_model=BaseResponse)
async def get_stock_daily_history(
    stock_code: str,
    days: int = Query(250, ge=1, le=500, description="天数"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取股票日线历史数据
    
    Args:
        stock_code: 股票代码 (如: 000001.SZ 或 000001)
        days: 天数，默认250天
    """
    try:
        service = TdxDailyDataService()
        
        end_date = date.today()
        start_date = end_date - __import__('datetime').timedelta(days=days)
        
        data = await service.get_stock_daily_data(
            stock_code=stock_code,
            start_date=start_date,
            end_date=end_date
        )
        
        return BaseResponse(
            success=True,
            message=f"获取 {len(data)} 条记录",
            data=data
        )
        
    except Exception as e:
        logger.error(f"获取日线历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")
