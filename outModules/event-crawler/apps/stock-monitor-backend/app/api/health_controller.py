#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康检查控制器
提供系统健康状态检查的API接口
"""

import time
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..database import get_db_session, db_manager
from ..services.stock_service import StockService
from ..services.monitor_service import MonitorService
from ..services.data_dedup_service import DataDedupService
from .schemas import BaseResponse, HealthResponse

router = APIRouter(prefix="/api/v1/health", tags=["健康检查"])


@router.get("", response_model=BaseResponse, summary="基础健康检查")
async def health_check():
    """基础健康检查"""
    return BaseResponse(
        data=HealthResponse(
            status="healthy",
            timestamp=datetime.now(),
            version="1.0.0",
            uptime=time.time()
        ),
        message="系统运行正常"
    )


@router.get("/detailed", response_model=BaseResponse, summary="详细健康检查")
async def detailed_health_check(
    db: AsyncSession = Depends(get_db_session)
):
    """详细健康检查，包含数据库连接和服务状态"""
    try:
        start_time = time.time()
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now(),
            "version": "1.0.0",
            "uptime": time.time(),
            "checks": {}
        }
        
        # 数据库连接检查
        try:
            db_healthy = await db_manager.health_check()
            health_data["checks"]["database"] = {
                "status": "healthy" if db_healthy else "unhealthy",
                "response_time": time.time() - start_time
            }
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            health_data["checks"]["database"] = {
                "status": "unhealthy",
                "error": str(e),
                "response_time": time.time() - start_time
            }
            health_data["status"] = "degraded"
        
        # 服务状态检查
        try:
            # 检查股票服务
            stock_service = StockService(db)
            stock_count = await stock_service.get_stock_statistics()
            health_data["checks"]["stock_service"] = {
                "status": "healthy",
                "stock_count": stock_count.get("total_stocks", 0)
            }
            
            # 检查监控服务
            monitor_service = MonitorService(db)
            monitor_stats = await monitor_service.get_monitor_statistics()
            health_data["checks"]["monitor_service"] = {
                "status": "healthy",
                "active_monitors": monitor_stats.get("active_monitors", 0),
                "total_monitors": monitor_stats.get("total_monitors", 0)
            }
            
            # 检查去重服务
            dedup_service = DataDedupService(db)
            dedup_stats = await dedup_service.get_dedup_statistics()
            health_data["checks"]["dedup_service"] = {
                "status": "healthy",
                "total_logs": dedup_stats.get("total_logs", 0),
                "duplicate_rate": dedup_stats.get("duplicate_rate", 0.0)
            }
            
        except Exception as e:
            logger.error(f"服务状态检查失败: {e}")
            health_data["checks"]["services"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_data["status"] = "degraded"
        
        # 计算总响应时间
        health_data["response_time"] = time.time() - start_time
        
        # 确定整体状态
        if health_data["status"] == "healthy":
            # 检查是否有任何服务不健康
            for check_name, check_data in health_data["checks"].items():
                if check_data.get("status") != "healthy":
                    health_data["status"] = "degraded"
                    break
        
        return BaseResponse(
            data=health_data,
            message=f"系统状态: {health_data['status']}"
        )
        
    except Exception as e:
        logger.error(f"详细健康检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="健康检查失败"
        )


@router.get("/database", response_model=BaseResponse, summary="数据库健康检查")
async def database_health_check():
    """数据库连接健康检查"""
    try:
        start_time = time.time()
        
        # 检查数据库连接
        is_healthy = await db_manager.health_check()
        response_time = time.time() - start_time
        
        if is_healthy:
            return BaseResponse(
                data={
                    "status": "healthy",
                    "response_time": response_time,
                    "timestamp": datetime.now()
                },
                message="数据库连接正常"
            )
        else:
            return BaseResponse(
                data={
                    "status": "unhealthy",
                    "response_time": response_time,
                    "timestamp": datetime.now()
                },
                message="数据库连接异常"
            )
            
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"数据库健康检查失败: {str(e)}"
        )


@router.get("/services", response_model=BaseResponse, summary="服务状态检查")
async def services_health_check(
    db: AsyncSession = Depends(get_db_session)
):
    """各个服务的健康状态检查"""
    try:
        services_status = {}
        overall_status = "healthy"
        
        # 检查股票服务
        try:
            stock_service = StockService(db)
            stats = await stock_service.get_stock_statistics()
            services_status["stock_service"] = {
                "status": "healthy",
                "statistics": stats
            }
        except Exception as e:
            logger.error(f"股票服务检查失败: {e}")
            services_status["stock_service"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            overall_status = "degraded"
        
        # 检查监控服务
        try:
            monitor_service = MonitorService(db)
            stats = await monitor_service.get_monitor_statistics()
            services_status["monitor_service"] = {
                "status": "healthy",
                "statistics": stats
            }
        except Exception as e:
            logger.error(f"监控服务检查失败: {e}")
            services_status["monitor_service"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            overall_status = "degraded"
        
        # 检查去重服务
        try:
            dedup_service = DataDedupService(db)
            stats = await dedup_service.get_dedup_statistics()
            services_status["dedup_service"] = {
                "status": "healthy",
                "statistics": stats
            }
        except Exception as e:
            logger.error(f"去重服务检查失败: {e}")
            services_status["dedup_service"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            overall_status = "degraded"
        
        return BaseResponse(
            data={
                "overall_status": overall_status,
                "services": services_status,
                "timestamp": datetime.now()
            },
            message=f"服务状态检查完成: {overall_status}"
        )
        
    except Exception as e:
        logger.error(f"服务状态检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务状态检查失败"
        )


@router.get("/readiness", response_model=BaseResponse, summary="就绪状态检查")
async def readiness_check(
    db: AsyncSession = Depends(get_db_session)
):
    """检查系统是否准备好接收请求"""
    try:
        # 检查数据库连接
        db_ready = await db_manager.health_check()
        
        if not db_ready:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="数据库未就绪"
            )
        
        # 检查基础服务是否可用
        try:
            stock_service = StockService(db)
            monitor_service = MonitorService(db)
            dedup_service = DataDedupService(db)
            
            # 简单的服务可用性检查
            await stock_service.get_stock_statistics()
            await monitor_service.get_monitor_statistics()
            await dedup_service.get_dedup_statistics()
            
        except Exception as e:
            logger.error(f"服务就绪检查失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="服务未就绪"
            )
        
        return BaseResponse(
            data={
                "status": "ready",
                "timestamp": datetime.now()
            },
            message="系统已就绪"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"就绪状态检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="就绪状态检查失败"
        )


@router.get("/liveness", response_model=BaseResponse, summary="存活状态检查")
async def liveness_check():
    """检查应用程序是否存活"""
    try:
        return BaseResponse(
            data={
                "status": "alive",
                "timestamp": datetime.now(),
                "uptime": time.time()
            },
            message="应用程序存活"
        )
    except Exception as e:
        logger.error(f"存活状态检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="存活状态检查失败"
        )