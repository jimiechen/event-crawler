from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel

from ..database import get_db_session
from ..services.volume_analysis_service import VolumeAnalysisService
from ..models.stock_daily import StockDaily
from ..models.volume_analysis import RuleCalculationLog, AlertRecord

router = APIRouter(prefix="/api/v1/debug", tags=["调试工具"])

# --- Models ---
class Scenario(BaseModel):
    id: str
    name: str
    description: str

class TriggerRequest(BaseModel):
    code: str
    scenario_id: str
    override_price: Optional[float] = None
    override_volume: Optional[float] = None
    override_date: Optional[date] = None

class TriggerResponse(BaseModel):
    logs: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]

# --- Constants ---
SCENARIOS = [
    {
        "id": "3x_vol", 
        "name": "3倍放量上涨", 
        "description": "模拟今日成交量为昨日3倍，收盘价上涨2%"
    },
    {
        "id": "2x_vol", 
        "name": "2倍放量上涨", 
        "description": "模拟今日成交量为昨日2倍，收盘价上涨1%"
    },
    {
        "id": "low_vol_60", 
        "name": "60日地量", 
        "description": "模拟今日成交量极低(1手)，触发60日地量(需该股有历史数据)"
    }
]

# --- Endpoints ---

@router.get("/scenarios", response_model=List[Scenario])
async def get_scenarios():
    """获取可用模拟场景"""
    return SCENARIOS

@router.post("/trigger", response_model=TriggerResponse)
async def trigger_scenario(
    request: TriggerRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """触发模拟场景"""
    code = request.code
    scenario_id = request.scenario_id
    
    # 1. Prepare Date
    target_date = request.override_date or date.today()
    
    # 2. Get Previous Data (to calculate multiplier)
    stmt = select(StockDaily).where(
        StockDaily.code == code, 
        StockDaily.trade_date < target_date
    ).order_by(StockDaily.trade_date.desc()).limit(1)
    result = await session.execute(stmt)
    prev_daily = result.scalars().first()
    
    if not prev_daily:
        # If no history, create a dummy yesterday
        yesterday = target_date - timedelta(days=1)
        prev_daily = StockDaily(
            code=code,
            trade_date=yesterday,
            open=10.0, high=10.0, low=10.0, close=10.0,
            vol=10000, amount=100000
        )
        session.add(prev_daily)
        await session.flush()
    
    prev_vol = float(prev_daily.vol) if prev_daily else 10000
    prev_close = float(prev_daily.close) if prev_daily else 10.0
    
    # 3. Construct Simulated Data
    sim_vol = prev_vol
    sim_close = prev_close
    
    if request.override_price is not None:
        sim_close = request.override_price
    if request.override_volume is not None:
        # User input is in Shares (e.g. 10000), but system uses Hands (100 shares/hand)
        # Convert Shares to Hands: 10000 -> 100
        sim_vol = request.override_volume / 100.0

    if request.override_date:
        # If date is overridden, we might be simulating a past or future date
        # If it's the same date as an existing record, we update it
        pass

    # Only apply scenario logic if overrides are NOT provided
    if request.override_price is None and request.override_volume is None:
        if scenario_id == "3x_vol":
            sim_vol = prev_vol * 3.1
            sim_close = prev_close * 1.02
        elif scenario_id == "2x_vol":
            sim_vol = prev_vol * 2.1
            sim_close = prev_close * 1.01
        elif scenario_id == "low_vol_60":
            sim_vol = 1 # Extreme low
            sim_close = prev_close
        elif scenario_id != "manual_input": # Allow 'manual_input' to just use defaults if no overrides
             raise HTTPException(status_code=400, detail="Unknown scenario ID")
        
    # 4. Insert/Update Target Data
    # Check if exists
    stmt = select(StockDaily).where(StockDaily.code == code, StockDaily.trade_date == target_date)
    result = await session.execute(stmt)
    existing = result.scalars().first()
    
    # Calculate amount (Thousands of Yuan)
    # Formula: Vol(Hands) * 100(Shares/Hand) * Price(Yuan) / 1000 = Vol * Price / 10
    sim_amount = sim_vol * sim_close * 0.1
    
    if existing:
        existing.vol = sim_vol
        existing.close = sim_close
        existing.amount = sim_amount
        existing.high = max(existing.high, sim_close)
        existing.low = min(existing.low, sim_close)
    else:
        new_daily = StockDaily(
            code=code,
            trade_date=target_date,
            open=prev_close,
            high=sim_close,
            low=sim_close,
            close=sim_close,
            vol=sim_vol,
            amount=sim_amount
        )
        session.add(new_daily)
    
    await session.commit()
    
    # 5. Run Analysis
    try:
        # Pass manual override info if needed, but for now we just updated the DB row
        # The service will pick up the new row and run analysis
        # Ideally we should pass a flag to analyze_stock to tell it this is a "Simulation/Realtime Check"
        # but the user requirements say "add to volume anomaly list, mark as real-time data".
        # Since we modified the DB, analyze_stock will treat it as normal data.
        # To "mark" it, we might need to update the log details in the service or here.
        # But let's let the Service do the heavy lifting.
        await VolumeAnalysisService.analyze_stock(code, session, is_realtime=True)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    # 6. Fetch Logs
    # RuleCalculationLog
    stmt = select(RuleCalculationLog).where(
        RuleCalculationLog.code == code
        # RuleCalculationLog doesn't have created_at in the model I saw? 
        # Wait, let me check the model again.
    ).order_by(RuleCalculationLog.id.desc()).limit(20)
    
    # AlertRecord
    stmt_alert = select(AlertRecord).where(
        AlertRecord.code == code
    ).order_by(AlertRecord.id.desc()).limit(10)
    
    logs_result = await session.execute(stmt)
    alerts_result = await session.execute(stmt_alert)
    
    logs = logs_result.scalars().all()
    alerts = alerts_result.scalars().all()
    
    # Reverse logs to show oldest first (chronological order) within the latest batch
    # So that "Rule Check Start" appears before "Rule Result"
    logs.reverse()
    
    return {
        "logs": [{"rule": l.rule_name, "match": l.is_match, "details": l.details} for l in logs],
        "alerts": [{"type": a.alert_type, "message": a.message} for a in alerts]
    }
