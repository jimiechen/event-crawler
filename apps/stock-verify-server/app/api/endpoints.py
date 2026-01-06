from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.services.cleaner import DataCleaner
from app.services.simulator import SimulationEngine
from app.services.verifier import Verifier
from app.services.backend_client import BackendClient
from pydantic import BaseModel
import httpx
from typing import Optional, List
from loguru import logger

router = APIRouter()

from pydantic import BaseModel, Field

class StockRequest(BaseModel):
    stock_code: str

class SimulationRequest(BaseModel):
    stock_code: str
    days: int = 5
    interval: int = 1

class SignalRequest(BaseModel):
    code: str
    trade_date: Optional[str] = None
    close: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[float] = None
    timestamp: Optional[str] = None
    
    class Config:
        extra = "allow" # Allow extra fields


@router.post("/cleanup")
async def cleanup_data(req: StockRequest, db: AsyncSession = Depends(get_db)):
    cleaner = DataCleaner(db)
    try:
        await cleaner.clear_stock_data(req.stock_code)
        return {"status": "success", "message": f"Data cleared for {req.stock_code}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulate")
async def run_simulation(req: SimulationRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    simulator = SimulationEngine(db)
    # Run in background to avoid blocking
    background_tasks.add_task(simulator.run_time_compression, req.stock_code, req.days, req.interval)
    return {"status": "success", "message": "Simulation started in background"}

@router.post("/simulate/batch")
async def run_batch_simulation(req: SimulationRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    simulator = SimulationEngine(db)
    background_tasks.add_task(simulator.run_time_compression, req.stock_code, req.days, 0.1) # Faster interval
    return {"status": "success", "message": "Batch simulation started"}

@router.post("/simulate/signal")
async def send_simulation_signal(req: SignalRequest):
    """
    Sends a single simulated K-line signal to the backend (8000) for validation.
    Logs the interaction.
    """
    client = BackendClient()
    logger.info(f"Sending simulation signal for {req.code} on {req.trade_date}")
    
    # Construct payload expected by backend validation endpoint
    # Schema: WencaiValidateRequest(stock_code, check_date, query_template)
    
    payload = {
        "stock_code": req.code,
        "check_date": req.trade_date,
    }
    
    # Add extra fields if present (e.g. query_template)
    if hasattr(req, "query_template"):
        payload["query_template"] = getattr(req, "query_template")
    # Also check if it's in the extra dict if pydantic puts it there
    if hasattr(req, "__dict__"):
         for key, value in req.__dict__.items():
             if key not in ["code", "trade_date"] and key in ["query_template"]:
                 payload[key] = value

    async with httpx.AsyncClient(timeout=120.0) as http:
        try:
            # Forward to backend
            resp = await http.post(
                f"{client.BASE_URL}/wencai/validate", 
                json=payload
            )
            resp.raise_for_status()
            data = resp.json()
            
            logger.info(f"Backend response: {data}")
            return {"status": "success", "backend_response": data}
            
        except Exception as e:
            import traceback
            logger.error(f"Failed to send signal: {e}")
            logger.error(traceback.format_exc())
            return {"status": "error", "message": f"{type(e).__name__}: {str(e)}"}

@router.get("/verify/{stock_code}")
async def verify_status(stock_code: str, db: AsyncSession = Depends(get_db)):
    verifier = Verifier(db)
    results = await verifier.run_acceptance_checks(stock_code)
    return {"status": "success", "data": results}

@router.post("/step/ingest")
async def step_ingest(req: StockRequest):
    client = BackendClient()
    # Trigger Wencai Search on Backend
    res = await client.search_wencai(req.stock_code)
    return {"status": "called", "backend_response": res}

@router.get("/stock/{stock_code}/history")
async def get_stock_history(stock_code: str, days: int = 300):
    """
    Fetch history from Backend (8000) using the new mixed history endpoint.
    Proxies the request to /api/stock/daily/{code}/mixed_history
    """
    client = BackendClient()
    logger.info(f"Fetching history for {stock_code} via proxy (days={days})...")
    
    async with httpx.AsyncClient() as http:
        try:
            # Call the new endpoint on port 8000
            # Note: client.BASE_URL includes /api/v1, but stock_daily endpoint is at /api/stock/daily
            # We need to construct the URL correctly
            base_url = client.BASE_URL.replace("/api/v1", "")
            target_url = f"{base_url}/api/stock/daily/{stock_code}/mixed_history"
            
            resp = await http.get(
                target_url,
                params={"days": days, "split_date": "2025-12-22"},
                timeout=30.0
            )
            
            if resp.status_code != 200:
                logger.warning(f"Backend returned {resp.status_code}")
                return {"status": "error", "message": f"Backend error: {resp.status_code}"}
                
            data = resp.json()
            if not data.get("success"):
                return {"status": "error", "message": data.get("message", "Unknown backend error")}
                
            daily_data = data.get("data", [])
            
            return {"status": "success", "data": daily_data}
            
        except Exception as e:
            logger.error(f"Proxy fetch error: {e}")
            return {"status": "error", "message": str(e)}

@router.get("/proxy/health")
async def proxy_health():
    client = BackendClient()
    async with httpx.AsyncClient() as http:
        try:
            # Try a simple health check or root
            resp = await http.get("http://localhost:8000/") # Or a known endpoint
            return {"status": "ok" if resp.status_code < 500 else "error"}
        except:
            return {"status": "error"}
