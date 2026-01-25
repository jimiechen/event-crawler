#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同花顺股票监控系统 - FastAPI应用入口
"""

import os
import sys
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from loguru import logger
import uvicorn
# import nest_asyncio

# 解决 Playwright 在某些环境下的事件循环问题
# nest_asyncio.apply()

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .config.settings import get_settings
from .config.logging import setup_logging
from .database import DatabaseManager, db_manager
from .services.scheduler_service import scheduler_service
from .services.task_executor import executor

# 初始化配置和日志
settings = get_settings()
setup_logging()

# 导入控制器 (在日志配置后导入，确保日志sink正确设置)
from .api import stock_controller, monitor_controller, health_controller, wencai_controller, network_controller, stock_daily_controller, favorites_controller, analysis_controller, trading_rules_controller, morphology_controller, test_tool_controller, system_controller, tag_controller, timed_task_controller, stock_score_controller, dashboard_controller, volume_analysis_controller, debug_controller, ranking_controller, stock_sync_controller, cookie_controller, crawler_controller, adb_controller, automation_controller, pattern_analysis_controller, platform_controller, session_controller, data_merge_controller, decision_controller, arena_controller, test_page_controller
from .api import generic_task_controller, mcp_controller, simulation_controller
from .api.schemas import ErrorResponse


# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 启动同花顺股票监控系统...")
    
    scheduler = None
    
    try:
        # 初始化数据库连接
        # db_manager = DatabaseManager()
        await db_manager.initialize()
        logger.info("✅ 数据库连接初始化完成")
        
        # 创建数据库表
        await db_manager.create_tables()
        logger.info("✅ 数据库表创建完成")
        
        # 启动定时任务调度器
        scheduler_service.start()
        logger.info("✅ 定时任务调度器已启动")

        # 初始化配置
        try:
            from .services.pattern_analysis_service import PatternAnalysisService
            from .services.platform_service import PlatformService
            async with db_manager.get_session() as session:
                pattern_service = PatternAnalysisService(session)
                await pattern_service.init_configs()
                logger.info("✅ 评分配置初始化完成")
                
                # 初始化平台配置
                platform_service = PlatformService(session)
                await platform_service.init_default_platforms()
                logger.info("✅ 平台配置初始化完成")
        except Exception as e:
            logger.warning(f"⚠️ 初始化配置失败: {e}")

        # 启动任务执行器 (APScheduler)
        executor.start()
        logger.info("✅ 任务执行器已启动")
        
        # 检查数据库健康状态
        if await db_manager.health_check():
            logger.info("✅ 数据库健康检查通过")
        else:
            logger.warning("⚠️ 数据库健康检查失败")
        
        logger.info("🎉 系统启动完成")
        
    except Exception as e:
        logger.error(f"❌ 系统启动失败: {e}")
        raise
    
    yield
    
    # 关闭时执行
    logger.info("🛑 正在关闭同花顺股票监控系统...")
    
    try:
        # 关闭定时任务调度器
        if scheduler_service:
            scheduler_service.shutdown()
            logger.info("✅ 定时任务调度器已关闭")

        # 关闭任务执行器
        executor.stop()
        logger.info("✅ 任务执行器已关闭")

        # 关闭数据库连接
        # db_manager = DatabaseManager()
        await db_manager.close()
        logger.info("✅ 数据库连接已关闭")
        
    except Exception as e:
        logger.error(f"❌ 系统关闭时出错: {e}")
    
    logger.info("👋 系统已关闭")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.app_name,
    description="提供股票数据采集、存储、监控和查询的API服务",
    version=settings.app_version,
    docs_url=settings.docs_url if not settings.is_production() else None,
    redoc_url=settings.redoc_url if not settings.is_production() else None,
    openapi_url=settings.openapi_url if not settings.is_production() else None,
    lifespan=lifespan
)


# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# 配置可信主机中间件（生产环境使用）
if settings.is_production():
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.trusted_hosts
    )


# 全局异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail} - {request.url}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            message=exc.detail,
            error_code=f"HTTP_{exc.status_code}",
            details={"path": str(request.url)}
        ).model_dump()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理器"""
    logger.warning(f"请求验证失败: {exc.errors()} - {request.url}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            success=False,
            message="请求参数验证失败",
            error_code="VALIDATION_ERROR",
            details={"validation_errors": exc.errors()}
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(f"未处理的异常: {type(exc).__name__}: {str(exc)} - {request.url}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            success=False,
            message="服务器内部错误",
            error_code="INTERNAL_SERVER_ERROR",
            details={"path": str(request.url), "exception_type": type(exc).__name__}
        ).dict()
    )


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志中间件"""
    start_time = asyncio.get_event_loop().time()
    
    # 记录请求开始
    logger.info(f"📥 {request.method} {request.url} - 开始处理")
    
    try:
        response = await call_next(request)
        
        # 计算处理时间
        process_time = asyncio.get_event_loop().time() - start_time
        
        # 记录响应
        logger.info(
            f"📤 {request.method} {request.url} - "
            f"状态码: {response.status_code} - "
            f"处理时间: {process_time:.3f}s"
        )
        
        # 添加处理时间到响应头
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        # 计算处理时间
        process_time = asyncio.get_event_loop().time() - start_time
        
        # 记录异常
        logger.error(
            f"💥 {request.method} {request.url} - "
            f"异常: {type(e).__name__}: {str(e)} - "
            f"处理时间: {process_time:.3f}s"
        )
        
        raise


# 注册路由
app.include_router(health_controller.router)
app.include_router(stock_controller.router)
app.include_router(monitor_controller.router)
app.include_router(wencai_controller.router)
app.include_router(network_controller.router)
app.include_router(stock_daily_controller.router)
app.include_router(favorites_controller.router)
app.include_router(analysis_controller.router)
app.include_router(trading_rules_controller.router)
app.include_router(morphology_controller.router)
app.include_router(test_tool_controller.router)
app.include_router(system_controller.router, prefix="/api/v1/system", tags=["System"])
app.include_router(tag_controller.router)
app.include_router(timed_task_controller.router)
app.include_router(stock_score_controller.router)
app.include_router(ranking_controller.router)
app.include_router(stock_sync_controller.router)
app.include_router(dashboard_controller.router)
app.include_router(volume_analysis_controller.router)
app.include_router(debug_controller.router)
app.include_router(cookie_controller.router)

# 注册SSE控制器
try:
    from .api import sse_controller
    app.include_router(sse_controller.router)
except ImportError as e:
    logger.warning(f"未找到SSE控制器，跳过注册: {e}")

app.include_router(crawler_controller.router)
app.include_router(adb_controller.router)
app.include_router(automation_controller.router)
app.include_router(pattern_analysis_controller.router)
app.include_router(platform_controller.router)
app.include_router(session_controller.router)
app.include_router(data_merge_controller.router)
app.include_router(decision_controller.router)
app.include_router(arena_controller.router)
app.include_router(generic_task_controller.router)
app.include_router(test_page_controller.router)
app.include_router(mcp_controller.router)
app.include_router(simulation_controller.router)

# 配置静态文件服务
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"✅ 静态文件服务已配置: {static_dir}")
else:
    logger.warning(f"⚠️ 静态文件目录不存在: {static_dir}")


# 根路径
@app.get("/", summary="根路径", tags=["基础"])
async def root():
    """根路径，返回API基本信息"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "提供股票数据采集、存储、监控和查询的API服务",
        "environment": settings.environment,
        "docs_url": settings.docs_url if not settings.is_production() else None,
        "health_check": f"{settings.api_v1_prefix}/health"
    }


# API信息路径
@app.get("/api", summary="API信息", tags=["基础"])
async def api_info():
    """返回API详细信息"""
    return {
        "title": f"{settings.app_name} API",
        "version": settings.app_version,
        "environment": settings.environment,
        "endpoints": {
            "health": f"{settings.api_v1_prefix}/health",
            "stocks": f"{settings.api_v1_prefix}/stocks",
            "monitors": f"{settings.api_v1_prefix}/monitors"
        },
        "documentation": {
            "swagger": settings.docs_url if not settings.is_production() else None,
            "redoc": settings.redoc_url if not settings.is_production() else None,
            "openapi": settings.openapi_url if not settings.is_production() else None
        } if not settings.is_production() else None
    }


# 开发服务器启动函数
def start_dev_server(host=None, port=None):
    """启动开发服务器"""
    uvicorn.run(
        "app.main:app",
        host=host or settings.host,
        port=port or settings.port,
        reload=True,
        log_level=settings.log_level.lower(),
        access_log=True
    )


# 生产服务器启动函数
def start_prod_server(host=None, port=None):
    """启动生产服务器"""
    uvicorn.run(
        "app.main:app",
        host=host or settings.host,
        port=port or settings.port,
        workers=settings.workers,
        log_level="warning",
        access_log=False
    )
