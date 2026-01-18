from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db as get_db_session
from app.services.cleaner import DataCleaner
from app.services.simulation_service import SimulationService

router = APIRouter()

@router.post("/clear-all")
async def clear_all_data(db: AsyncSession = Depends(get_db_session)):
    cleaner = DataCleaner(db)
    await cleaner.clear_all_tables()
    return {"status": "success", "message": "All data cleared (except tags)."}

@router.post("/simulation/step1")
async def simulation_step1(db: AsyncSession = Depends(get_db_session)):
    service = SimulationService(db)
    result = await service.step1_calculate_603601_baseline()
    return result

@router.get("/simulation/step2")
async def simulation_step2(db: AsyncSession = Depends(get_db_session)):
    """
    Step 2 Simulation with SSE Streaming
    Use GET for SSE compatibility
    """
    service = SimulationService(db)
    return StreamingResponse(
        service.step2_stream(),
        media_type="text/event-stream"
    )

@router.post("/simulation/step2")
async def simulation_step2_post(db: AsyncSession = Depends(get_db_session)):
    """
    Backward compatible POST endpoint (non-streaming or streaming?)
    Ideally we want streaming here too, but some clients might expect JSON.
    Let's make it stream too, but typically POST streams are rare in browsers.
    But verifying script uses POST.
    Let's support both.
    """
    service = SimulationService(db)
    # If we want JSON result, we can iterate stream and collect last result?
    # Or just stream.
    return StreamingResponse(
        service.step2_stream(),
        media_type="text/event-stream"
    )
