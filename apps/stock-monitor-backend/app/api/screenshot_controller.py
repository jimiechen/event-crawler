#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票截图分析控制器
提供 /api/stock/analyze-screenshot 接口
"""

import base64
from typing import Optional, Literal
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, field_validator
from loguru import logger

from ..database import get_db_session
from ..services.screenshot_analysis_service import ScreenshotAnalysisService
from .schemas import BaseResponse

router = APIRouter(prefix="/api/stock", tags=["股票截图分析"])


# ========== 请求/响应模型 ==========

class ScreenshotAnalysisRequest(BaseModel):
    """截图分析请求"""
    task_id: str = Field(..., description="任务ID")
    batch_id: Optional[str] = Field(None, description="批次ID")
    stock_code: str = Field(..., min_length=6, max_length=6, description="股票代码")
    stock_name: Optional[str] = Field(None, description="股票名称")
    screenshot_type: Literal["tlby", "fenxi", "kline", "sanlong"] = Field(
        default="tlby", 
        description="截图类型: tlby=天龙博弈日K, fenxi=分时图, kline=普通K线"
    )
    image_base64: str = Field(..., description="Base64编码的图片数据")
    image_format: Literal["png", "jpg", "jpeg", "webp"] = Field(default="png", description="图片格式")
    source_ip: Optional[str] = Field(None, description="来源IP")
    agent_id: Optional[str] = Field(None, description="Agent标识")
    callback_url: Optional[str] = Field(None, description="回调URL")
    
    @field_validator('stock_code')
    @classmethod
    def validate_stock_code(cls, v):
        if not v.isdigit():
            raise ValueError('股票代码必须为6位数字')
        return v
    
    @field_validator('image_base64')
    @classmethod
    def validate_base64(cls, v):
        if ',' in v:
            v = v.split(',')[1]
        try:
            decoded = base64.b64decode(v)
            if len(decoded) > 10 * 1024 * 1024:  # 限制10MB
                raise ValueError('图片大小不能超过10MB')
            return v
        except Exception:
            raise ValueError('无效的Base64图片数据')


class SanlongIndicators(BaseModel):
    """三龙聚首指标"""
    trend_alert: int = Field(..., description="趋势警戒 0/1")
    volume_alert: int = Field(..., description="量能警戒 0/1")
    mid_alert: int = Field(..., description="中期警戒 0/1")
    short_alert: int = Field(..., description="短期警戒 0/1")
    alert_count: int = Field(..., description="亮灯数量0-4")
    all_red: bool = Field(..., description="是否全红警戒")


class KDSignals(BaseModel):
    """K/D信号"""
    has_k_signal_today: bool = Field(..., description="今天是否有K信号")
    has_d_signal_today: bool = Field(..., description="今天是否有D信号")
    k_signal_count: int = Field(..., description="K信号数量")
    d_signal_count: int = Field(..., description="D信号数量")


class MainForceData(BaseModel):
    """主力控盘数据"""
    main_force_buy_ratio: float = Field(..., description="主力买入占比")
    main_force_sell_ratio: float = Field(..., description="主力卖出占比")
    retail_buy_ratio: float = Field(..., description="散户买入占比")
    retail_sell_ratio: float = Field(..., description="散户卖出占比")


class ScreenshotAnalysisResponse(BaseModel):
    """截图分析响应"""
    id: int
    task_id: str
    batch_id: Optional[str]
    stock_code: str
    stock_name: Optional[str]
    screenshot_type: str
    status: str
    ai_price: Optional[float]
    ai_change_percent: Optional[float]
    ai_volume: Optional[int]
    sanlong: Optional[SanlongIndicators]
    kd_signals: Optional[KDSignals]
    main_force: Optional[MainForceData]
    detected_pattern: Optional[str]
    pattern_confidence: Optional[float]
    is_data_match: Optional[bool]
    match_confidence: Optional[float]
    created_at: datetime
    analyzed_at: Optional[datetime]


# ========== API接口 ==========

@router.post("/analyze-screenshot", response_model=BaseResponse, summary="分析股票截图")
async def analyze_screenshot(
    request: ScreenshotAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    """
    接收Windows Agent上传的股票截图，进行AI识别
    
    支持识别：
    - 三龙聚首指标（趋势/量能/中期/短期警戒）
    - K/D信号（今天是否有信号）
    - 主力控盘数据
    """
    try:
        service = ScreenshotAnalysisService(db)
        
        # 创建分析任务
        request_data = request.model_dump()
        analysis = await service.create_analysis_task(request_data)
        
        # 后台执行分析
        background_tasks.add_task(service.analyze_screenshot, analysis.id)
        
        logger.info(f"截图分析任务已创建: id={analysis.id}, task_id={request.task_id}")
        
        return BaseResponse(
            success=True,
            message="截图已接收，正在后台分析三龙聚首和K/D信号",
            data={
                "id": analysis.id,
                "task_id": analysis.task_id,
                "stock_code": analysis.stock_code,
                "status": "analyzing",
                "created_at": analysis.created_at.isoformat()
            }
        )
        
    except ValueError as e:
        logger.warning(f"参数验证失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"截图分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"截图分析失败: {str(e)}")


@router.get("/analyze-screenshot/{analysis_id}", response_model=BaseResponse, summary="获取分析结果")
async def get_analysis_result(
    analysis_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """获取截图分析结果"""
    try:
        from ..models.screenshot_analysis import ScreenshotAnalysis
        
        analysis = await db.get(ScreenshotAnalysis, analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="分析记录不存在")
        
        # 构建响应
        response_data = {
            "id": analysis.id,
            "task_id": analysis.task_id,
            "batch_id": analysis.batch_id,
            "stock_code": analysis.stock_code,
            "stock_name": analysis.stock_name,
            "screenshot_type": analysis.screenshot_type,
            "status": analysis.status,
            "ai_price": float(analysis.ai_price) if analysis.ai_price else None,
            "ai_change_percent": float(analysis.ai_change_percent) if analysis.ai_change_percent else None,
            "ai_volume": analysis.ai_volume,
            "sanlong": {
                "trend_alert": analysis.sanlong_trend_alert,
                "volume_alert": analysis.sanlong_volume_alert,
                "mid_alert": analysis.sanlong_mid_alert,
                "short_alert": analysis.sanlong_short_alert,
                "alert_count": analysis.sanlong_alert_count,
                "all_red": analysis.sanlong_all_red
            } if analysis.sanlong_alert_count is not None else None,
            "kd_signals": {
                "has_k_signal_today": analysis.has_k_signal_today,
                "has_d_signal_today": analysis.has_d_signal_today,
                "k_signal_count": analysis.k_signal_count,
                "d_signal_count": analysis.d_signal_count
            } if analysis.has_k_signal_today is not None else None,
            "main_force": {
                "main_force_buy_ratio": float(analysis.main_force_buy_ratio) if analysis.main_force_buy_ratio else None,
                "main_force_sell_ratio": float(analysis.main_force_sell_ratio) if analysis.main_force_sell_ratio else None,
                "retail_buy_ratio": float(analysis.retail_buy_ratio) if analysis.retail_buy_ratio else None,
                "retail_sell_ratio": float(analysis.retail_sell_ratio) if analysis.retail_sell_ratio else None
            } if analysis.main_force_buy_ratio is not None else None,
            "detected_pattern": analysis.detected_pattern,
            "pattern_confidence": float(analysis.pattern_confidence) if analysis.pattern_confidence else None,
            "is_data_match": analysis.is_data_match,
            "match_confidence": float(analysis.match_confidence) if analysis.match_confidence else None,
            "created_at": analysis.created_at,
            "analyzed_at": analysis.analyzed_at
        }
        
        return BaseResponse(
            success=True,
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分析结果失败: {e}")
        raise HTTPException(status_code=500, detail="获取分析结果失败")


@router.get("/analyze-screenshot/task/{task_id}", response_model=BaseResponse, summary="按任务ID查询")
async def get_analysis_by_task(
    task_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """按任务ID查询分析结果"""
    try:
        from sqlalchemy import select
        from ..models.screenshot_analysis import ScreenshotAnalysis
        
        stmt = select(ScreenshotAnalysis).where(
            ScreenshotAnalysis.task_id == task_id
        )
        result = await db.execute(stmt)
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 复用get_analysis_result的逻辑
        return await get_analysis_result(analysis.id, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询任务失败: {e}")
        raise HTTPException(status_code=500, detail="查询任务失败")


@router.get("/analyze-screenshot/stock/{stock_code}", response_model=BaseResponse, summary="查询股票历史分析")
async def get_analysis_by_stock(
    stock_code: str,
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session)
):
    """查询某只股票的历史截图分析记录"""
    try:
        from sqlalchemy import select, desc
        from ..models.screenshot_analysis import ScreenshotAnalysis
        
        stmt = select(ScreenshotAnalysis).where(
            ScreenshotAnalysis.stock_code == stock_code
        ).order_by(desc(ScreenshotAnalysis.created_at)).limit(limit)
        
        result = await db.execute(stmt)
        analyses = result.scalars().all()
        
        return BaseResponse(
            success=True,
            data=[{
                "id": a.id,
                "task_id": a.task_id,
                "stock_code": a.stock_code,
                "status": a.status,
                "detected_pattern": a.detected_pattern,
                "created_at": a.created_at
            } for a in analyses]
        )
        
    except Exception as e:
        logger.error(f"查询失败: {e}")
        raise HTTPException(status_code=500, detail="查询失败")
