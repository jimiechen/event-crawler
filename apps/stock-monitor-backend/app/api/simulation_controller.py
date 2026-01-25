
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse
from datetime import date, datetime
from loguru import logger

from app.database import get_db_session
from app.services.simulation_service import StockSimulationService

router = APIRouter(prefix="/api/v1/simulation", tags=["Simulation"])

@router.get("/run/{target_date}", summary="Run Daily Simulation (Stream)")
async def run_simulation(
    target_date: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    触发每日仿真任务（SSE 流式返回）
    """
    try:
        if target_date == "today":
            t_date = date.today()
        else:
            t_date = datetime.strptime(target_date, "%Y-%m-%d").date()
    except ValueError:
        logger.warning(f"Invalid date format: {target_date}, using today")
        t_date = date.today()

    service = StockSimulationService(db)
    return EventSourceResponse(service.run_daily_simulation_stream(t_date))
