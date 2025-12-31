#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络数据控制器
处理Chrome扩展网络数据的API接口
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..database import get_db_session
from ..services.network_service import NetworkService
from .schemas import (
    BaseResponse, ErrorResponse,
    NetworkDataCreate, NetworkDataResponse, NetworkDataQuery,
    NetworkDataListResponse, NetworkDataStatsResponse
)

router = APIRouter(prefix="/api/v1/network", tags=["网络数据"])


@router.post("/data", response_model=BaseResponse, summary="创建网络数据记录")
async def create_network_data(
    data: NetworkDataCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """接收Chrome扩展推送的网络数据"""
    try:
        network_service = NetworkService(db)
        network_data = await network_service.create_network_data(data.dict())
        
        return BaseResponse(
            data=NetworkDataResponse.from_orm(network_data),
            message="网络数据创建成功"
        )
    except Exception as e:
        logger.error(f"创建网络数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建网络数据失败"
        )


@router.get("/data", response_model=NetworkDataListResponse, summary="获取网络数据列表")
async def get_network_data_list(
    url_pattern: Optional[str] = Query(None, description="URL模式过滤"),
    source: Optional[str] = Query(None, description="数据来源过滤"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db_session)
):
    """获取网络数据列表"""
    try:
        network_service = NetworkService(db)
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 获取数据列表
        data_list = await network_service.get_network_data_list(
            url_pattern=url_pattern,
            source=source,
            start_time=start_time,
            end_time=end_time,
            limit=page_size,
            offset=offset
        )
        
        # 获取总数
        total = await network_service.get_network_data_count(
            url_pattern=url_pattern,
            source=source,
            start_time=start_time,
            end_time=end_time
        )
        
        # 转换为响应格式
        data_responses = [NetworkDataResponse.from_orm(data) for data in data_list]
        
        # 计算总页数
        total_pages = (total + page_size - 1) // page_size
        
        return NetworkDataListResponse(
            data=data_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except Exception as e:
        logger.error(f"获取网络数据列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取网络数据列表失败"
        )


@router.get("/data/{data_id}", response_model=BaseResponse, summary="获取单条网络数据")
async def get_network_data_by_id(
    data_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """根据ID获取网络数据"""
    try:
        network_service = NetworkService(db)
        
        # 获取单条数据
        data_list = await network_service.get_network_data_list(
            limit=1,
            offset=0
        )
        
        # 这里简化处理，实际应该在服务层添加按ID查询的方法
        network_data = None
        for data in data_list:
            if data.id == data_id:
                network_data = data
                break
        
        if not network_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"网络数据记录不存在: {data_id}"
            )
        
        return BaseResponse(
            data=NetworkDataResponse.from_orm(network_data),
            message="获取网络数据成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取网络数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取网络数据失败"
        )


@router.get("/stats", response_model=NetworkDataStatsResponse, summary="获取网络数据统计")
async def get_network_data_stats(
    db: AsyncSession = Depends(get_db_session)
):
    """获取网络数据统计信息"""
    try:
        network_service = NetworkService(db)
        stats = await network_service.get_network_data_stats()
        
        return NetworkDataStatsResponse(**stats)
    except Exception as e:
        logger.error(f"获取网络数据统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取网络数据统计失败"
        )


@router.delete("/data/clear", response_model=BaseResponse, summary="清理网络数据")
async def clear_network_data(
    before_days: int = Query(7, ge=1, description="清理多少天前的数据"),
    source: Optional[str] = Query(None, description="指定数据来源"),
    db: AsyncSession = Depends(get_db_session)
):
    """清理指定时间之前的网络数据"""
    try:
        network_service = NetworkService(db)
        
        # 计算清理时间点
        before_date = datetime.now() - timedelta(days=before_days)
        
        # 执行清理
        deleted_count = await network_service.clear_network_data(
            before_date=before_date,
            source=source
        )
        
        return BaseResponse(
            data={"deleted_count": deleted_count},
            message=f"数据清理成功，删除了 {deleted_count} 条记录"
        )
    except Exception as e:
        logger.error(f"清理网络数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="清理网络数据失败"
        )


@router.delete("/data/{data_id}", response_model=BaseResponse, summary="删除网络数据记录")
async def delete_network_data(
    data_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """删除指定的网络数据记录"""
    try:
        network_service = NetworkService(db)
        
        # 执行删除
        deleted = await network_service.delete_network_data(data_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"网络数据记录不存在: {data_id}"
            )
        
        return BaseResponse(
            data={"deleted": True},
            message="数据删除成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除网络数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除网络数据失败"
        )