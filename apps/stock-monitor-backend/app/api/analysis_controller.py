from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..database import get_db_session
from ..services.analysis_log_service import get_volume_price_logs, delete_volume_price_logs


router = APIRouter(prefix="/api/v1/analysis", tags=["量价分析日志"])


@router.get("/logs/{code}")
async def get_logs(
    code: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session)
):
    try:
        data = await get_volume_price_logs(db, code, start_date, end_date)
        return {"success": True, "message": "ok", "data": data}
    except Exception as e:
        logger.error(f"get logs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/logs/{code}")
async def clear_logs(
    code: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session)
):
    try:
        deleted = await delete_volume_price_logs(db, code, start_date, end_date)
        return {"success": True, "message": "ok", "data": {"deleted": deleted}}
    except Exception as e:
        logger.error(f"delete logs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

