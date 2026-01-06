from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.database import get_db_session
from app.services.pattern_analysis_service import PatternAnalysisService
from app.models.pattern_config import PatternConfig, PatternStockPool
from sqlalchemy import select, update
from app.api.schemas import BaseResponse

router = APIRouter(prefix="/api/pattern", tags=["Pattern Analysis"])

class ConfigUpdate(BaseModel):
    code: str
    score: float
    enabled: bool

class ScreeningRequest(BaseModel):
    force: bool = False

@router.get("/configs", response_model=BaseResponse)
async def get_configs(db: AsyncSession = Depends(get_db_session)):
    """获取所有评分配置"""
    try:
        stmt = select(PatternConfig)
        result = await db.execute(stmt)
        configs = result.scalars().all()
        return BaseResponse(success=True, data=configs)
    except Exception as e:
        return BaseResponse(success=False, message=str(e))

@router.post("/config", response_model=BaseResponse)
async def update_config(config: ConfigUpdate, db: AsyncSession = Depends(get_db_session)):
    """更新评分配置"""
    try:
        stmt = select(PatternConfig).where(PatternConfig.pattern_code == config.code)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.score = config.score
            existing.is_enabled = config.enabled
            await db.commit()
            return BaseResponse(success=True, message="Config updated")
        else:
            return BaseResponse(success=False, message="Config not found")
    except Exception as e:
        return BaseResponse(success=False, message=str(e))

@router.post("/screen", response_model=BaseResponse)
async def run_screening(request: ScreeningRequest = None, db: AsyncSession = Depends(get_db_session)):
    """触发形态筛选"""
    try:
        service = PatternAnalysisService(db)
        result = await service.perform_screening()
        return BaseResponse(success=True, data=result)
    except Exception as e:
        return BaseResponse(success=False, message=str(e))

@router.get("/pool", response_model=BaseResponse)
async def get_pool(status: Optional[str] = None, db: AsyncSession = Depends(get_db_session)):
    """获取股票池"""
    try:
        stmt = select(PatternStockPool)
        if status:
            stmt = stmt.where(PatternStockPool.status == status)
        stmt = stmt.order_by(PatternStockPool.score.desc())
        
        result = await db.execute(stmt)
        stocks = result.scalars().all()
        return BaseResponse(success=True, data=stocks)
    except Exception as e:
        return BaseResponse(success=False, message=str(e))

@router.get("/tag-cloud", response_model=Dict[str, Any])
async def get_tag_cloud(days: int = 3, db: AsyncSession = Depends(get_db_session)):
    """获取标签云数据"""
    try:
        service = PatternAnalysisService(db)
        data = await service.get_tag_cloud_data(days=days)
        return data # Directly return dict for frontend compatibility
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
