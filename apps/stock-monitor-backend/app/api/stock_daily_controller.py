from typing import Optional, List
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database import get_db_session, db_manager
from app.models.stock_daily import StockDaily, TaskLog
from fastapi import status
from app.api.schemas import BaseResponse
from app.api.stock_daily_schemas import (
    StockDailyResponse,
    StockDailyListResponse,
    StockDailyPageResponse,
    TaskLogResponse,
    StockDailyCreate
)
from app.repositories.stock_daily_repository import StockDailyRepository
from app.services.stock_sync_service import StockSyncService

router = APIRouter(prefix="/api/stock/daily", tags=["股票日线"])

# 实例化Repository
repository = StockDailyRepository(db_manager)

def get_stock_sync_service() -> StockSyncService:
    return StockSyncService(db_manager)

@router.get("/search", response_model=StockDailyPageResponse)
async def search_daily_data(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    code: Optional[str] = Query(None, description="股票代码"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    min_price: Optional[float] = Query(None, description="最低收盘价"),
    max_price: Optional[float] = Query(None, description="最高收盘价"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    分页查询日线数据，支持代码、日期、价格区间过滤
    """
    try:
        data, total = await repository.query_daily_data(
            page, page_size, code, start_date, end_date, min_price, max_price
        )
        
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        
        return {
            "success": True,
            "message": "ok",
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    except Exception as e:
        logger.error(f"search daily error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs", response_model=BaseResponse, summary="获取任务日志")
async def get_task_logs(
    task_name: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取任务日志
    """
    try:
        from sqlalchemy import select, desc
        query = select(TaskLog).order_by(desc(TaskLog.created_at)).limit(limit)
        if task_name:
            query = query.where(TaskLog.task_name == task_name)
        
        result = await db.execute(query)
        data = result.scalars().all()
        
        return BaseResponse(
            data=[TaskLogResponse.from_orm(item) for item in data],
            message="获取任务日志成功"
        )
    except Exception as e:
        logger.error(f"获取任务日志失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务日志失败: {str(e)}"
        )

@router.get("/{code}/mixed_history", response_model=BaseResponse, summary="混合获取股票历史数据(CSV+Tushare)")
async def get_mixed_history(
    code: str,
    days: int = Query(250, description="天数"),
    split_date: str = Query("2025-12-22", description="分割日期"),
    service: StockSyncService = Depends(get_stock_sync_service)
):
    """
    混合获取历史数据: CSV (<= split_date) + Tushare (> split_date)
    """
    try:
        result = await service.get_mixed_history(code, days, split_date)
        if result["success"]:
            return BaseResponse(
                success=True,
                message="ok",
                data=result["data"]
            )
        else:
            return BaseResponse(
                success=False,
                message=result.get("message", "获取失败"),
                data=None
            )
    except Exception as e:
        logger.error(f"get_mixed_history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{code}", response_model=StockDailyListResponse)
async def get_daily_data(
    code: str,
    days: Optional[int] = Query(None, ge=1, le=3650, description="获取最近N天的数据"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取股票日线数据
    """
    try:
        if not start_date:
            if days:
                start_date = date.today() - timedelta(days=days)
            else:
                # 默认最近30天
                start_date = date.today() - timedelta(days=30)
                
        if not end_date:
            end_date = date.today()

        data = await repository.get_daily_data(code, start_date, end_date)
        
        # 计算前复权(QFQ)
        # QFQ = Price * (Current_Adj_Factor / Latest_Adj_Factor) 
        # Wait, formula is: QFQ = Price * Adj_Factor / Latest_Adj_Factor
        latest_factor = await repository.get_latest_adj_factor(code)
        
        if latest_factor and data:
            for item in data:
                if item.adj_factor:
                    # 使用 float 进行计算以避免 Decimal 精度问题
                    try:
                        qfq_rate = item.adj_factor / latest_factor
                        if item.open is not None: item.open = float(item.open) * qfq_rate
                        if item.close is not None: item.close = float(item.close) * qfq_rate
                        if item.high is not None: item.high = float(item.high) * qfq_rate
                        if item.low is not None: item.low = float(item.low) * qfq_rate
                    except Exception as e:
                        logger.warning(f"QFQ calculation error for {code} {item.trade_date}: {e}")

        # 转换为Response格式
        # 注意：StockDaily模型包含id, code, trade_date, open, close...
        # StockDailyResponse需要这些字段
        
        return {
            "success": True, 
            "message": "ok", 
            "data": data,
            "total": len(data)
        }
    except Exception as e:
        logger.error(f"daily error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
