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

class StockRequest(BaseModel):
    stock_code: str

class SimulationRequest(BaseModel):
    stock_code: str
    days: int = 5
    interval: int = 1

class SignalRequest(BaseModel):
    code: str
    trade_date: str
    close: float
    open: float
    high: float
    low: float
    volume: float
    timestamp: str

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
    # Assuming backend has an endpoint /api/v1/test-tool/validate or similar
    # If not, we might need to use a different endpoint or the generic ingest one.
    # Based on original test-tool.html, it calls /api/v1/test-tool/validate
    
    # We will use httpx directly here or via client if extended
    async with httpx.AsyncClient() as http:
        try:
            # Forward to backend
            resp = await http.post(
                f"{client.BASE_URL}/test-tool/validate", 
                json={
                    "data": {
                        "code": req.code,
                        "name": req.code, # Simplified
                        "current_price": req.close,
                        "volume": req.volume,
                        "change_percent": 0, # Calculated if needed
                        "timestamp": req.trade_date
                    }
                }
            )
            resp.raise_for_status()
            data = resp.json()
            
            logger.info(f"Backend response: {data}")
            return {"status": "success", "backend_response": data}
            
        except Exception as e:
            logger.error(f"Failed to send signal: {e}")
            return {"status": "error", "message": str(e)}

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
async def get_stock_history(stock_code: str):
    """
    Fetch history from Backend (8000) acting as a proxy.
    Mimics the behavior of test-tool.html fetching data.
    """
    client = BackendClient()
    logger.info(f"Fetching history for {stock_code} via proxy...")
    
    async with httpx.AsyncClient() as http:
        try:
            # We use the 'add-custom-stock' endpoint as seen in test-tool.html
            # payload: { code, label, custom_date }
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")
            
            resp = await http.post(
                f"{client.BASE_URL}/test-tool/add-custom-stock",
                json={
                    "code": stock_code,
                    "label": "auto-verify",
                    "custom_date": today
                },
                timeout=10.0
            )
            
            if resp.status_code != 200:
                logger.warning(f"Backend returned {resp.status_code}")
                return {"status": "error", "message": f"Backend error: {resp.status_code}"}
                
            data = resp.json()
            if not data.get("success"):
                return {"status": "error", "message": data.get("message", "Unknown backend error")}
                
            daily_data = data.get("daily_data", [])
            
            # Transform if necessary, but kline.html expects standard fields which daily_data usually has
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
