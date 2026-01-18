from fastapi import APIRouter, Depends
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

@router.post("/simulation/step2")
async def simulation_step2(db: AsyncSession = Depends(get_db_session)):
    service = SimulationService(db)
    result = await service.step2_wencai_crawler_and_score()
    return result
