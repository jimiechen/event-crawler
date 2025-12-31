#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控管理控制器
提供股票监控管理的API接口
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..database import get_db_session
from ..services.monitor_service import MonitorService
from .schemas import (
    BaseResponse, ErrorResponse, ListResponse,
    MonitorCreate, MonitorUpdate, MonitorResponse,
    MonitorWithStockResponse, MonitorWithDataResponse,
    MonitorBatchCreate, MonitorBatchUpdate, MonitorBatchOperation,
    BatchOperationResponse, MonitorStatisticsResponse,
    MonitorListQuery, AlertQuery
)

router = APIRouter(prefix="/api/v1/monitors", tags=["监控管理"])


@router.post("", response_model=BaseResponse, summary="添加监控股票")
async def add_monitor(
    monitor_data: MonitorCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """添加监控股票"""
    try:
        monitor_service = MonitorService(db)
        monitor = await monitor_service.add_monitor(
            stock_code=monitor_data.stock_code,
            priority=monitor_data.priority,
            auto_create_stock=monitor_data.auto_create_stock
        )
        
        return BaseResponse(
            data=MonitorResponse.from_orm(monitor),
            message="添加监控股票成功"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"添加监控股票失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="添加监控股票失败"
        )


@router.delete("/{stock_code}", response_model=BaseResponse, summary="移除监控股票")
async def remove_monitor(
    stock_code: str,
    db: AsyncSession = Depends(get_db_session)
):
    """移除监控股票"""
    try:
        monitor_service = MonitorService(db)
        result = await monitor_service.remove_monitor(stock_code)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"监控股票不存在: {stock_code}"
            )
        
        return BaseResponse(
            data={'removed': True},
            message="移除监控股票成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"移除监控股票失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="移除监控股票失败"
        )


@router.put("/{stock_code}", response_model=BaseResponse, summary="更新监控设置")
async def update_monitor(
    stock_code: str,
    update_data: MonitorUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """更新监控设置"""
    try:
        monitor_service = MonitorService(db)
        
        # 更新优先级
        if update_data.priority is not None:
            monitor = await monitor_service.update_monitor_priority(
                stock_code, update_data.priority
            )
            if not monitor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"监控股票不存在: {stock_code}"
                )
        
        # 更新活跃状态
        if update_data.is_active is not None:
            if update_data.is_active:
                monitor = await monitor_service.activate_monitor(stock_code)
            else:
                monitor = await monitor_service.deactivate_monitor(stock_code)
            
            if not monitor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"监控股票不存在: {stock_code}"
                )
        
        return BaseResponse(
            data=MonitorResponse.from_orm(monitor),
            message="更新监控设置成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新监控设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新监控设置失败"
        )


@router.get("", response_model=BaseResponse, summary="获取监控列表")
async def get_monitor_list(
    active_only: bool = Query(True, description="仅活跃监控"),
    priority_filter: Optional[int] = Query(None, ge=1, le=10, description="优先级过滤"),
    stock_code: Optional[str] = Query(None, description="股票代码过滤"),
    include_stock_info: bool = Query(False, description="包含股票信息"),
    include_latest_data: bool = Query(False, description="包含最新数据"),
    limit: int = Query(100, ge=1, le=1000, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: AsyncSession = Depends(get_db_session)
):
    """获取监控列表"""
    try:
        monitor_service = MonitorService(db)
        
        if include_latest_data:
            # 获取包含最新数据的监控列表
            monitors = await monitor_service.get_monitor_with_latest_data(active_only)
            monitor_responses = monitors
        elif include_stock_info:
            # 获取包含股票信息的监控列表
            monitors = await monitor_service.get_monitor_with_stock_info(active_only)
            monitor_responses = monitors
        else:
            # 获取基础监控列表
            monitors = await monitor_service.get_monitor_list(active_only, priority_filter)
            monitor_responses = [
                {
                    'id': monitor.id,
                    'stock_code': getattr(monitor, 'code', None) or getattr(monitor, 'stock_code', None),
                    'priority': monitor.priority,
                    'is_active': monitor.is_active,
                    'created_at': monitor.created_at,
                    'updated_at': monitor.updated_at,
                }
                for monitor in monitors
            ]
        
        # 内存过滤 (Stock Code)
        if stock_code:
            monitor_responses = [
                m for m in monitor_responses 
                if stock_code in (m.get('stock_code') or '')
            ]

        # 应用分页（简化处理）
        total = len(monitor_responses)
        paginated_monitors = monitor_responses[offset:offset + limit]
        has_more = offset + limit < total
        
        list_response = ListResponse(
            items=paginated_monitors,
            total=total,
            limit=limit,
            offset=offset,
            has_more=has_more
        )
        
        return BaseResponse(
            data=list_response,
            message="获取监控列表成功"
        )
    except Exception as e:
        logger.error(f"获取监控列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取监控列表失败"
        )


@router.get("/codes", response_model=BaseResponse, summary="获取监控股票代码列表")
async def get_monitor_codes(
    active_only: bool = Query(True, description="仅活跃监控"),
    db: AsyncSession = Depends(get_db_session)
):
    """获取监控股票代码列表"""
    try:
        monitor_service = MonitorService(db)
        codes = await monitor_service.get_monitor_codes(active_only)
        
        return BaseResponse(
            data=codes,
            message=f"获取监控股票代码成功，共{len(codes)}只"
        )
    except Exception as e:
        logger.error(f"获取监控股票代码失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取监控股票代码失败"
        )


@router.get("/high-priority", response_model=BaseResponse, summary="获取高优先级监控")
async def get_high_priority_monitors(
    min_priority: int = Query(5, ge=1, le=10, description="最低优先级"),
    db: AsyncSession = Depends(get_db_session)
):
    """获取高优先级监控列表"""
    try:
        monitor_service = MonitorService(db)
        monitors = await monitor_service.get_high_priority_monitors(min_priority)
        
        monitor_responses = [MonitorResponse.from_orm(monitor) for monitor in monitors]
        
        return BaseResponse(
            data=monitor_responses,
            message=f"获取高优先级监控成功，共{len(monitor_responses)}只"
        )
    except Exception as e:
        logger.error(f"获取高优先级监控失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取高优先级监控失败"
        )


@router.get("/statistics", response_model=BaseResponse, summary="获取监控统计信息")
async def get_monitor_statistics(
    db: AsyncSession = Depends(get_db_session)
):
    """获取监控统计信息"""
    try:
        monitor_service = MonitorService(db)
        stats = await monitor_service.get_monitor_statistics()
        
        return BaseResponse(
            data=stats,
            message="获取监控统计信息成功"
        )
    except Exception as e:
        logger.error(f"获取监控统计信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取监控统计信息失败"
        )


@router.get("/alerts", response_model=BaseResponse, summary="获取监控告警")
async def get_monitor_alerts(
    hours: int = Query(24, ge=1, le=168, description="检查小时数"),
    db: AsyncSession = Depends(get_db_session)
):
    """获取监控告警信息"""
    try:
        monitor_service = MonitorService(db)
        alerts = await monitor_service.get_monitor_alerts(hours)
        
        return BaseResponse(
            data=alerts,
            message=f"获取监控告警成功，发现{len(alerts)}个告警"
        )
    except Exception as e:
        logger.error(f"获取监控告警失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取监控告警失败"
        )


@router.post("/batch", response_model=BaseResponse, summary="批量添加监控")
async def batch_add_monitors(
    batch_data: MonitorBatchCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """批量添加监控股票"""
    try:
        monitor_service = MonitorService(db)
        result = await monitor_service.batch_add_monitors(
            stock_codes=batch_data.stock_codes,
            default_priority=batch_data.default_priority
        )
        
        response_data = BatchOperationResponse(**result)
        
        return BaseResponse(
            data=response_data,
            message=f"批量添加监控完成: 成功{result['success']}个, 失败{result['failed']}个"
        )
    except Exception as e:
        logger.error(f"批量添加监控失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量添加监控失败"
        )


@router.put("/batch/priority", response_model=BaseResponse, summary="批量更新优先级")
async def batch_update_priority(
    batch_data: MonitorBatchUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """批量更新监控优先级"""
    try:
        monitor_service = MonitorService(db)
        result = await monitor_service.batch_update_priority(batch_data.updates)
        
        response_data = BatchOperationResponse(**result)
        
        return BaseResponse(
            data=response_data,
            message=f"批量更新优先级完成: 成功{result['success']}个, 失败{result['failed']}个"
        )
    except Exception as e:
        logger.error(f"批量更新优先级失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量更新优先级失败"
        )


@router.put("/batch/activate", response_model=BaseResponse, summary="批量激活监控")
async def batch_activate_monitors(
    batch_data: MonitorBatchOperation,
    db: AsyncSession = Depends(get_db_session)
):
    """批量激活监控"""
    try:
        monitor_service = MonitorService(db)
        updated_count = await monitor_service.batch_activate(batch_data.stock_codes)
        
        return BaseResponse(
            data={'updated_count': updated_count},
            message=f"批量激活监控完成，激活了{updated_count}个监控"
        )
    except Exception as e:
        logger.error(f"批量激活监控失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量激活监控失败"
        )


@router.put("/batch/deactivate", response_model=BaseResponse, summary="批量停用监控")
async def batch_deactivate_monitors(
    batch_data: MonitorBatchOperation,
    db: AsyncSession = Depends(get_db_session)
):
    """批量停用监控"""
    try:
        monitor_service = MonitorService(db)
        updated_count = await monitor_service.batch_deactivate(batch_data.stock_codes)
        
        return BaseResponse(
            data={'updated_count': updated_count},
            message=f"批量停用监控完成，停用了{updated_count}个监控"
        )
    except Exception as e:
        logger.error(f"批量停用监控失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量停用监控失败"
        )


@router.post("/{stock_code}/activate", response_model=BaseResponse, summary="激活监控")
async def activate_monitor(
    stock_code: str,
    db: AsyncSession = Depends(get_db_session)
):
    """激活监控股票"""
    try:
        monitor_service = MonitorService(db)
        monitor = await monitor_service.activate_monitor(stock_code)
        
        if not monitor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"监控股票不存在: {stock_code}"
            )
        
        return BaseResponse(
            data=MonitorResponse.from_orm(monitor),
            message="激活监控成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"激活监控失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="激活监控失败"
        )


@router.post("/{stock_code}/deactivate", response_model=BaseResponse, summary="停用监控")
async def deactivate_monitor(
    stock_code: str,
    db: AsyncSession = Depends(get_db_session)
):
    """停用监控股票"""
    try:
        monitor_service = MonitorService(db)
        monitor = await monitor_service.deactivate_monitor(stock_code)
        
        if not monitor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"监控股票不存在: {stock_code}"
            )
        
        return BaseResponse(
            data=MonitorResponse.from_orm(monitor),
            message="停用监控成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停用监控失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="停用监控失败"
        )
