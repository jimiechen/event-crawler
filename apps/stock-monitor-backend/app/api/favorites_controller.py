from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..database import get_db_session
from ..services.monitor_service import MonitorService
from ..services.wencai_service import WencaiService


router = APIRouter(prefix="/api/v1/favorites", tags=["自选股"])


@router.post("/sync-from-wencai")
async def sync_from_wencai(
    batch_id: Optional[int] = Query(None),
    default_priority: int = Query(1, ge=1, le=10),
    db: AsyncSession = Depends(get_db_session)
):
    try:
        wencai = WencaiService(db)
        if batch_id:
            stocks = await wencai.get_stocks_by_batch(batch_id)
        else:
            stocks = await wencai.get_latest_stocks()
        codes: List[str] = []
        for s in stocks:
            c = s.get('stock_code') if isinstance(s, dict) else getattr(s, 'stock_code', None)
            if c and len(c) == 6 and c.isdigit():
                codes.append(c)
        monitor = MonitorService(db)
        result = await monitor.batch_add_monitors(codes, default_priority)
        return {"success": True, "message": "ok", "data": {"added": result['success'], "failed": result['failed'], "total": result['total'], "errors": result['errors']}}
    except Exception as e:
        logger.error(f"favorites sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

