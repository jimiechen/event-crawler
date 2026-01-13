#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据同步控制器
提供CSV和Tushare数据同步接口
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Body, Query, Path
from pydantic import BaseModel
from loguru import logger

from app.database import DatabaseManager, db_manager
from app.services.stock_sync_service import StockSyncService
from app.api.schemas import BaseResponse
from app.models.sync_log import SyncTaskType, SyncTaskStatus

router = APIRouter(prefix="/api/v1/stock/sync", tags=["股票数据同步"])

class CsvSyncRequest(BaseModel):
    batch_id: int
    days: int = 250
    end_date: Optional[str] = None
    stock_codes: Optional[List[str]] = None

class TushareSyncRequest(BaseModel):
    batch_id: int
    start_date: Optional[str] = None
    stock_codes: Optional[List[str]] = None

def get_stock_sync_service() -> StockSyncService:
    return StockSyncService(db_manager)

@router.post("/csv", response_model=BaseResponse, summary="CSV数据同步")
async def sync_csv(
    request: CsvSyncRequest,
    service: StockSyncService = Depends(get_stock_sync_service)
):
    """
    从CSV文件同步数据到数据库 (2025-12-22日前数据)
    """
    try:
        result = await service.sync_csv_to_db(
            batch_id=request.batch_id,
            days=request.days,
            end_date_str=request.end_date,
            stock_codes=request.stock_codes
        )
        if result["success"]:
            return BaseResponse(
                success=True,
                message="CSV数据同步完成",
                data=result["data"]
            )
        else:
            return BaseResponse(
                success=False,
                message=result.get("message", "CSV数据同步失败"),
                data=None
            )
    except Exception as e:
        logger.error(f"CSV同步API异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/csv/health", response_model=BaseResponse, summary="CSV健康检查")
async def check_csv_health(
    service: StockSyncService = Depends(get_stock_sync_service)
):
    """
    检查CSV文件数据完整性和健康状况
    """
    try:
        result = await service.check_csv_health()
        return BaseResponse(
            success=True,
            message="CSV健康检查完成",
            data=result
        )
    except Exception as e:
        logger.error(f"CSV健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs", response_model=BaseResponse, summary="获取同步日志")
async def get_sync_logs(
    limit: int = Query(50, description="限制条数"),
    offset: int = Query(0, description="偏移量"),
    task_type: Optional[str] = Query(None, description="任务类型"),
    batch_id: Optional[int] = Query(None, description="批次ID"),
    service: StockSyncService = Depends(get_stock_sync_service)
):
    """
    获取同步任务执行日志
    """
    try:
        logs = await service.log_repository.get_logs(
            limit=limit, 
            offset=offset, 
            task_type=task_type, 
            batch_id=batch_id
        )
        return BaseResponse(
            success=True,
            message="获取日志成功",
            data=[log.to_dict() for log in logs]
        )
    except Exception as e:
        logger.error(f"获取同步日志失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tushare", response_model=BaseResponse, summary="Tushare增量同步")
async def sync_tushare(
    request: TushareSyncRequest,
    service: StockSyncService = Depends(get_stock_sync_service)
):
    """
    Tushare增量数据同步 (默认从昨天开始)
    """
    try:
        # 如果未提供开始日期，默认使用昨天
        start_date = request.start_date
        if not start_date:
            from datetime import timedelta
            yesterday = datetime.now() - timedelta(days=1)
            start_date = yesterday.strftime("%Y-%m-%d")

        result = await service.sync_tushare_increment(
            batch_id=request.batch_id,
            start_date_str=start_date,
            stock_codes=request.stock_codes
        )
        if result["success"]:
            return BaseResponse(
                success=True,
                message="Tushare数据同步完成",
                data=result["data"]
            )
        else:
            return BaseResponse(
                success=False,
                message=result.get("message", "Tushare数据同步失败"),
                data=None
            )
    except Exception as e:
        logger.error(f"Tushare同步API异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/csv/{stock_code}", response_model=BaseResponse, summary="单只股票CSV同步")
async def sync_csv_single(
    stock_code: str,
    service: StockSyncService = Depends(get_stock_sync_service)
):
    """
    同步单只股票的CSV数据
    """
    log = None
    try:
        # Create Log for tracking
        log = await service.log_repository.create_log(
            task_type=SyncTaskType.CSV_FULL,
            batch_id=0
        )

        # Hardcoded parameters as per requirement
        days = 250
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Use sync_csv_single to handle single stock logic without batch dependency
        result = await service.sync_csv_single(stock_code, days, end_date)
        
        status = SyncTaskStatus.SUCCESS if result["success"] else SyncTaskStatus.FAILED
        msg = result.get("message", "Success") if result["success"] else result.get("message", "Unknown Error")
        final_message = f"Single Stock {stock_code}: {msg}"

        # Update Log
        await service.log_repository.update_log(
            log_id=log.id,
            status=status,
            end_time=datetime.now(),
            message=final_message,
            processed_count=1,
            inserted_count=result.get("inserted", 0),
            error_count=0 if result["success"] else 1
        )

        if result["success"]:
            return BaseResponse(success=True, message=f"股票 {stock_code} CSV同步成功", data=result)
        else:
            return BaseResponse(success=False, message=result.get("message", "CSV同步失败"), data=None)
    except Exception as e:
        error_msg = f"Single CSV sync error for {stock_code}: {e}"
        logger.error(error_msg)
        if log:
            await service.log_repository.update_log(
                log_id=log.id,
                status=SyncTaskStatus.FAILED,
                end_time=datetime.now(),
                message=error_msg,
                error_count=1
            )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tushare/{stock_code}", response_model=BaseResponse, summary="单只股票Tushare同步")
async def sync_tushare_single(
    stock_code: str,
    service: StockSyncService = Depends(get_stock_sync_service)
):
    """
    同步单只股票的Tushare数据
    """
    try:
        # Hardcoded parameters as per requirement
        start_date = "2025-12-23"
        
        # Use sync_tushare_single to handle single stock logic without batch dependency
        result = await service.sync_tushare_single(stock_code, start_date)
        
        if result["success"]:
            return BaseResponse(success=True, message=f"股票 {stock_code} Tushare同步成功", data=result)
        else:
            return BaseResponse(success=False, message=result.get("message", "Tushare同步失败"), data=None)
    except Exception as e:
        logger.error(f"Single Tushare sync error for {stock_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from app.services.rule_engine_service import RuleEngineService

def get_rule_engine_service() -> RuleEngineService:
    return RuleEngineService(db_manager)

@router.get("/calculate/{stock_code}", response_model=BaseResponse, summary="单只股票计算")
async def calculate_single(
    stock_code: str,
    service: RuleEngineService = Depends(get_rule_engine_service)
):
    """
    计算单只股票指标
    """
    try:
        # Calculate for latest available date automatically
        result = await service.calculate_daily_scores(stock_code=stock_code, force=True)
        if result["status"] == "success":
             return BaseResponse(success=True, message=f"股票 {stock_code} 计算完成", data=result)
        else:
             return BaseResponse(success=False, message=result.get("error", "计算失败"), data=None)
    except Exception as e:
        logger.error(f"Single calculation error for {stock_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 新增GET端点（按日期和批次） ====================

@router.get("/csv/{sync_date}/{batch_id}", response_model=BaseResponse, summary="CSV数据同步（按日期）")
async def sync_csv_by_date(
    sync_date: str = Path(..., description="同步日期 (YYYY-MM-DD)"),
    batch_id: int = Path(..., description="批次ID"),
    service: StockSyncService = Depends(get_stock_sync_service)
):
    """
    按日期同步CSV数据到数据库
    - 检测缺失的日期
    - 同步缺失日期的数据
    """
    try:
        # 解析日期
        target_date = datetime.strptime(sync_date, "%Y-%m-%d").date()
        
        # 执行同步
        result = await service.sync_csv_to_db(
            batch_id=batch_id,
            days=250,
            end_date_str=sync_date,
            stock_codes=None
        )
        
        if result["success"]:
            return BaseResponse(
                success=True,
                message=f"CSV数据同步完成，日期: {sync_date}",
                data=result["data"]
            )
        else:
            return BaseResponse(
                success=False,
                message=result.get("message", "CSV数据同步失败"),
                data=None
            )
    except Exception as e:
        logger.error(f"CSV同步API异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tushare/{sync_date}/{batch_id}", response_model=BaseResponse, summary="Tushare数据同步（按日期）")
async def sync_tushare_by_date(
    sync_date: str = Path(..., description="同步日期 (YYYY-MM-DD)"),
    batch_id: int = Path(..., description="批次ID"),
    service: StockSyncService = Depends(get_stock_sync_service)
):
    """
    按日期从Tushare同步数据
    - 从CSV最后一行或数据库读取最新日期
    - 检测缺失的日期
    - 从Tushare获取缺失日期的数据
    - 追加到CSV文件
    - 同步到数据库
    """
    try:
        # 解析日期
        target_date = datetime.strptime(sync_date, "%Y-%m-%d").date()
        
        # 执行同步
        result = await service.sync_tushare_increment(
            batch_id=batch_id,
            start_date_str=sync_date,
            stock_codes=None
        )
        
        if result["success"]:
            return BaseResponse(
                success=True,
                message=f"Tushare数据同步完成，日期: {sync_date}",
                data=result["data"]
            )
        else:
            return BaseResponse(
                success=False,
                message=result.get("message", "Tushare数据同步失败"),
                data=None
            )
    except Exception as e:
        logger.error(f"Tushare同步API异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wencai/{sync_date}/{batch_id}", response_model=BaseResponse, summary="问财股票数据同步（按日期）")
async def sync_wencai_by_date(
    sync_date: str = Path(..., description="同步日期 (YYYY-MM-DD)"),
    batch_id: int = Path(..., description="批次ID"),
    service: StockSyncService = Depends(get_stock_sync_service)
):
    """
    按日期同步问财股票数据
    """
    try:
        # 解析日期
        target_date = datetime.strptime(sync_date, "%Y-%m-%d").date()
        
        # 从wencai_stocks表获取股票代码并批量同步
        result = await service.sync_wencai_stocks_to_db()
        
        return BaseResponse(
            success=True,
            message=f"问财股票数据同步完成，日期: {sync_date}",
            data=result
        )
    except Exception as e:
        logger.error(f"问财同步API异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))

