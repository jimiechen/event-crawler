#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通达信选股API接口
"""

from typing import Optional
from datetime import date
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database import get_db_session
from app.api.schemas import BaseResponse
from app.services.tdx_selection_workflow import run_tdx_selection_workflow
from app.services.tdx_daily_data_service import TdxDailyDataService
from app.services.daily_review_service import DailyReviewService
from app.models.stock import WencaiStock, WencaiCrawlBatch
from sqlalchemy import select

router = APIRouter(prefix="/api/v1/tdx/selection", tags=["通达信选股"])


@router.post("/execute", response_model=BaseResponse)
async def execute_tdx_selection(
    strategy: str = Query("3x_volume_and_limit_up", description="选股策略"),
    auto_sync_250d: bool = Query(True, description="是否自动同步250天日线数据"),
    trade_date: Optional[date] = Query(None, description="交易日期，默认今天"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    执行通达信选股工作流
    
    流程:
    1. 执行3倍量+涨停选股
    2. 创建通达信板块
    3. 保存选股结果到数据库
    4. 同步250天日线数据到stock_daily (如果auto_sync_250d=True)
    5. 计算量价得分
    6. 发送飞书通知
    
    Args:
        strategy: 选股策略，默认3倍量+涨停
        auto_sync_250d: 是否自动同步250天数据
        trade_date: 交易日期
    """
    try:
        if trade_date is None:
            trade_date = date.today()
        
        logger.info(f"开始通达信选股: {trade_date}, 策略: {strategy}")
        
        # 初始化通达信客户端
        try:
            import sys
            sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")
            from tqcenter import tq
            tq.initialize(__file__)
        except Exception as e:
            logger.error(f"通达信客户端初始化失败: {e}")
            return BaseResponse(
                success=False,
                message=f"通达信客户端初始化失败: {str(e)}"
            )
        
        # 执行选股工作流
        result = await run_tdx_selection_workflow(
            tdx_client=tq,
            trade_date=trade_date
        )
        
        if result.get("status") != "success":
            return BaseResponse(
                success=False,
                message=f"选股失败: {result.get('reason', '未知错误')}"
            )
        
        selected_count = result.get("selected_count", 0)
        wencai_batch_id = result.get("wencai_batch_id")
        
        logger.info(f"选股完成: 选中{selected_count}只股票, 批次ID: {wencai_batch_id}")
        
        # 如果选股成功且有选中股票，同步250天数据
        if auto_sync_250d and selected_count > 0 and wencai_batch_id:
            logger.info(f"开始同步250天日线数据...")
            
            # 获取选中的股票列表
            stmt = select(WencaiStock.stock_code).where(
                WencaiStock.crawl_batch_id == str(wencai_batch_id)
            )
            stock_result = await db.execute(stmt)
            stock_codes = [r[0] for r in stock_result.all()]
            
            if stock_codes:
                daily_service = TdxDailyDataService(tq)
                sync_result = await daily_service.sync_daily_data_for_selection(
                    stock_codes=stock_codes,
                    end_date=trade_date,
                    batch_id=wencai_batch_id,
                    days=250
                )
                
                logger.info(f"250天数据同步完成: {sync_result}")
                
                return BaseResponse(
                    success=True,
                    message=f"选股成功: 选中{selected_count}只股票, 同步{sync_result.get('total_synced', 0)}条日线数据",
                    data={
                        "selected_count": selected_count,
                        "batch_id": wencai_batch_id,
                        "sync_result": sync_result
                    }
                )
        
        return BaseResponse(
            success=True,
            message=f"选股成功: 选中{selected_count}只股票",
            data={
                "selected_count": selected_count,
                "batch_id": wencai_batch_id
            }
        )
        
    except Exception as e:
        logger.error(f"通达信选股执行失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"选股失败: {str(e)}")


@router.post("/sync-250d", response_model=BaseResponse)
async def sync_250d_daily_data(
    batch_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    为选股批次同步250天日线数据
    
    Args:
        batch_id: 选股批次ID
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
        stock_codes = [r[0] for r in result.all()]
        
        if not stock_codes:
            return BaseResponse(
                success=False,
                message="该批次无股票"
            )
        
        # 初始化通达信客户端
        try:
            import sys
            sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")
            from tqcenter import tq
            tq.initialize(__file__)
        except Exception as e:
            logger.error(f"通达信客户端初始化失败: {e}")
            return BaseResponse(
                success=False,
                message=f"通达信客户端初始化失败: {str(e)}"
            )
        
        # 同步数据
        daily_service = TdxDailyDataService(tq)
        sync_result = await daily_service.sync_daily_data_for_selection(
            stock_codes=stock_codes,
            end_date=batch.query_date,
            batch_id=batch_id,
            days=250
        )
        
        return BaseResponse(
            success=True,
            message=f"同步完成: {sync_result['total_synced']} 条记录",
            data=sync_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"同步250天数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


@router.get("/status", response_model=BaseResponse)
async def get_selection_status(
    trade_date: Optional[date] = Query(None, description="日期，默认今天"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取今日选股状态
    
    Args:
        trade_date: 日期
    """
    try:
        if trade_date is None:
            trade_date = date.today()
        
        # 查询今日通达信选股批次
        stmt = select(WencaiCrawlBatch).where(
            WencaiCrawlBatch.source == 'tdx',
            WencaiCrawlBatch.query_date == trade_date
        )
        result = await db.execute(stmt)
        batches = result.scalars().all()
        
        if not batches:
            return BaseResponse(
                success=True,
                message="今日无通达信选股记录",
                data={"has_selection": False}
            )
        
        batch = batches[0]  # 取第一个批次
        
        # 查询stock_daily中该批次同步的数据量
        from app.models.stock_daily import StockDaily
        from sqlalchemy import func
        
        sync_stmt = select(func.count()).select_from(StockDaily).where(
            StockDaily.source_batch_id == str(batch.id)
        )
        sync_result = await db.execute(sync_stmt)
        sync_count = sync_result.scalar()
        
        expected_count = batch.total_records * 250 if batch.total_records else 0
        
        return BaseResponse(
            success=True,
            message="获取选股状态成功",
            data={
                "has_selection": True,
                "batch_id": batch.id,
                "sector_code": batch.sector_code,
                "selected_count": batch.total_records,
                "synced_count": sync_count,
                "expected_count": expected_count,
                "sync_progress": round(sync_count / expected_count * 100, 1) if expected_count > 0 else 0
            }
        )
        
    except Exception as e:
        logger.error(f"获取选股状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")
