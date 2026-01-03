#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仪表盘控制器
提供首页仪表盘所需的数据接口
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..database import get_db_session
from ..services.dashboard_service import DashboardService
from .schemas import (
    BaseResponse, 
    DashboardStatisticsResponse, 
    DashboardStockListResponse, 
    DashboardWencaiListResponse,
    DashboardStockExtraResponse
)

router = APIRouter(prefix="/api/v1/dashboard", tags=["仪表盘"])

@router.get("/stats", response_model=BaseResponse, summary="获取仪表盘统计数据")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db_session)
):
    """获取仪表盘统计数据"""
    try:
        service = DashboardService(db)
        stats = await service.get_statistics()
        
        return BaseResponse(
            data=DashboardStatisticsResponse(**stats),
            message="获取统计数据成功"
        )
    except Exception as e:
        logger.error(f"获取统计数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取统计数据失败"
        )

@router.get("/stocks", response_model=BaseResponse, summary="获取股票列表(Tab1)")
async def get_dashboard_stocks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    active_only: bool = Query(False, description="只显示活跃股票"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    sort_by: str = Query("volume_anomaly_score", description="排序字段"),
    sort_order: str = Query("desc", description="排序顺序 (asc/desc)"),
    db: AsyncSession = Depends(get_db_session)
):
    """获取股票列表"""
    try:
        service = DashboardService(db)
        result = await service.get_stock_list(
            page=page, 
            page_size=page_size, 
            active_only=active_only,
            start_time=start_time,
            end_time=end_time,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return BaseResponse(
            data=DashboardStockListResponse(**result),
            message="获取股票列表成功"
        )
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取股票列表失败"
        )

@router.get("/wencai", response_model=BaseResponse, summary="获取问财列表(Tab2)")
async def get_dashboard_wencai(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(15, ge=1, le=100, description="每页数量"),
    tag: Optional[str] = Query(None, description="标签搜索"),
    db: AsyncSession = Depends(get_db_session)
):
    """获取问财列表"""
    try:
        service = DashboardService(db)
        result = await service.get_wencai_list(page=page, page_size=page_size, tag_filter=tag)
        
        return BaseResponse(
            data=DashboardWencaiListResponse(**result),
            message="获取问财列表成功"
        )
    except Exception as e:
        logger.error(f"获取问财列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取问财列表失败"
        )

@router.get("/stocks/extra", response_model=BaseResponse, summary="获取股票额外信息")
async def get_dashboard_stock_extra(
    code: str = Query(..., description="股票代码"),
    db: AsyncSession = Depends(get_db_session)
):
    """获取股票额外信息 (TDX评分, 数据存在性, Sparkline)"""
    try:
        service = DashboardService(db)
        result = await service.get_stock_extra_info(code)
        
        return BaseResponse(
            data=DashboardStockExtraResponse(**result),
            message="获取股票额外信息成功"
        )
    except Exception as e:
        logger.error(f"获取股票额外信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取股票额外信息失败: {e}"
        )

@router.post("/stocks/{code}/sync-tdx", response_model=BaseResponse, summary="同步TDX评分")
async def sync_tdx_score(
    code: str,
    db: AsyncSession = Depends(get_db_session)
):
    """同步TDX评分"""
    try:
        service = DashboardService(db)
        score = await service.sync_tdx_score(code)
        
        return BaseResponse(
            data={"score": score},
            message="同步TDX评分成功"
        )
    except Exception as e:
        logger.error(f"同步TDX评分失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"同步TDX评分失败: {e}"
        )
