#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Job Controller
Exposes internal scheduler logic as API endpoints for Generic Task system.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from loguru import logger
from app.api.schemas import BaseResponse
from app.services.scheduler_service import scheduler_service

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])

@router.post("/post-market-update", response_model=BaseResponse, summary="执行盘后积分更新")
async def run_post_market_update():
    """
    执行盘后积分更新任务:
    1. 同步最新日线数据
    2. 执行Pathway积分计算
    3. 计算排名
    """
    try:
        logger.info("API Trigger: run_post_market_update")
        await scheduler_service.run_post_market_update()
        return BaseResponse(success=True, message="盘后积分更新任务执行完成")
    except Exception as e:
        logger.error(f"Failed to run post market update: {e}")
        return BaseResponse(success=False, message=f"任务执行失败: {str(e)}")

@router.post("/daily-acceptance", response_model=BaseResponse, summary="执行每日验收测试")
async def run_daily_acceptance():
    """
    执行每日验收测试任务
    """
    try:
        logger.info("API Trigger: run_daily_acceptance")
        await scheduler_service.run_daily_acceptance()
        return BaseResponse(success=True, message="每日验收测试执行完成")
    except Exception as e:
        logger.error(f"Failed to run daily acceptance: {e}")
        return BaseResponse(success=False, message=f"任务执行失败: {str(e)}")

@router.post("/realtime-monitor", response_model=BaseResponse, summary="执行盘中实时监控检查")
async def run_realtime_monitor():
    """
    执行盘中实时监控检查
    """
    try:
        logger.info("API Trigger: run_realtime_monitor_check")
        await scheduler_service.run_realtime_monitor_check()
        return BaseResponse(success=True, message="盘中实时监控检查执行完成")
    except Exception as e:
        logger.error(f"Failed to run realtime monitor: {e}")
        return BaseResponse(success=False, message=f"任务执行失败: {str(e)}")

@router.post("/daily-ai-review", response_model=BaseResponse, summary="执行每日AI复盘")
async def run_daily_ai_review():
    """
    执行每日AI复盘任务
    """
    try:
        logger.info("API Trigger: run_daily_ai_review")
        await scheduler_service.run_daily_ai_review()
        return BaseResponse(success=True, message="每日AI复盘执行完成")
    except Exception as e:
        logger.error(f"Failed to run daily ai review: {e}")
        return BaseResponse(success=False, message=f"任务执行失败: {str(e)}")

@router.post("/wencai-daily-crawler", response_model=BaseResponse, summary="执行每日问财爬虫")
async def run_wencai_daily_crawler():
    """
    执行每日问财爬虫任务 (爬取前一天数据)
    """
    try:
        logger.info("API Trigger: run_wencai_daily_crawler")
        await scheduler_service.run_wencai_daily_crawler()
        return BaseResponse(success=True, message="每日问财爬虫执行完成")
    except Exception as e:
        logger.error(f"Failed to run wencai daily crawler: {e}")
        return BaseResponse(success=False, message=f"任务执行失败: {str(e)}")

@router.post("/wencai-data-sync", response_model=BaseResponse, summary="执行问财数据同步与评分")
async def run_wencai_data_sync():
    """
    执行问财数据同步与评分 (通常在爬虫完成后执行)
    """
    try:
        logger.info("API Trigger: run_wencai_data_sync")
        await scheduler_service.run_wencai_data_sync()
        return BaseResponse(success=True, message="问财数据同步与评分执行完成")
    except Exception as e:
        logger.error(f"Failed to run wencai data sync: {e}")
        return BaseResponse(success=False, message=f"任务执行失败: {str(e)}")
