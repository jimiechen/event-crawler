from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict
import logging
from adapters.ashare_adapter import AShareDataAdapter
from schemas.ashare import AShareContext

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ashare", tags=["ashare"])

# Global adapter instance
_adapter: Optional[AShareDataAdapter] = None

def get_adapter() -> AShareDataAdapter:
    global _adapter
    if _adapter is None:
        _adapter = AShareDataAdapter()
    return _adapter

@router.on_event("shutdown")
async def shutdown_event():
    global _adapter
    if _adapter:
        await _adapter.close()
        _adapter = None

@router.get("/context/{symbol}", response_model=AShareContext)
async def get_stock_context(
    symbol: str,
    adapter: AShareDataAdapter = Depends(get_adapter)
):
    """
    获取单只股票的完整上下文信息
    """
    try:
        context = await adapter.get_stock_context(symbol)
        if not context:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
        return context
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stock context for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/batch", response_model=Dict[str, Optional[AShareContext]])
async def get_batch_context(
    symbols: List[str] = Query(..., description="List of stock symbols"),
    adapter: AShareDataAdapter = Depends(get_adapter)
):
    """
    批量获取股票上下文信息
    """
    try:
        return await adapter.get_multiple_stocks(symbols)
    except Exception as e:
        logger.error(f"Error fetching batch context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
