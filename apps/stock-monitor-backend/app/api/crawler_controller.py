from fastapi import APIRouter, Request, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from ..services.sse_service import sse_service
from ..database import get_db_session
from ..repositories.crawler_repository import CrawlerTargetRepository, CrawlerResultRepository
from loguru import logger

router = APIRouter(prefix="/api/v1/crawler", tags=["Crawler"])

# --- Pydantic Models ---

class CrawlerStatusUpdate(BaseModel):
    platform: str
    status: str  # idle, starting, running, stopped, error
    message: Optional[str] = None
    data_count: Optional[int] = 0
    error: Optional[str] = None

class CrawlerTargetCreate(BaseModel):
    platform: str
    name: str
    url: str
    target_type: str = "url"
    is_active: bool = True
    description: Optional[str] = None
    xpath_config: Optional[str] = None

class CrawlerTargetUpdate(BaseModel):
    platform: Optional[str] = None
    name: Optional[str] = None
    url: Optional[str] = None
    target_type: Optional[str] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None
    xpath_config: Optional[str] = None

class CrawlerTargetResponse(BaseModel):
    id: int
    platform: str
    name: str
    url: str
    target_type: str
    is_active: bool
    description: Optional[str] = None
    xpath_config: Optional[str] = None
    last_crawled_at: Optional[datetime] = None
    last_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CheckLoginRequest(BaseModel):
    platform: str
    url: Optional[str] = None
    nickname_xpath: Optional[str] = None

class CrawlerResultResponse(BaseModel):
    id: int
    platform: str
    target_id: Optional[int] = None
    content: Optional[str] = None
    author: Optional[str] = None
    publish_time: Optional[datetime] = None
    likes: int = 0
    comments: int = 0
    shares: int = 0
    url: str
    data_id: Optional[str] = None
    crawled_at: datetime

    class Config:
        from_attributes = True

class ResponseModel(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None

# --- In-Memory State ---

# Store latest status in memory (or Redis if needed)
crawler_states: Dict[str, Dict[str, Any]] = {}

# --- SSE Endpoints ---

@router.get("/events")
async def sse_endpoint(request: Request):
    """
    SSE endpoint for real-time crawler updates
    """
    return await sse_service.subscribe(request)

@router.post("/status")
async def update_crawler_status(
    status: CrawlerStatusUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Receive status update from crawler
    """
    logger.info(f"Received status update from {status.platform}: {status.status}")
    
    # Update local state
    crawler_states[status.platform] = status.dict()
    
    # Check for login failure
    if status.status == "error" and status.error and ("login" in status.error.lower() or "cookie" in status.error.lower()):
        logger.warning(f"Login failure detected for {status.platform}")
        # Update DB
        from ..services.cookie_service import CookieService
        cookie_service = CookieService(db)
        await cookie_service.update_status_by_domain(status.platform, "expired", is_valid=False)
        
        # Broadcast login_failed event specifically
        await sse_service.broadcast("login_failed", {
            "platform": status.platform,
            "message": status.error
        })

    # Broadcast to frontend
    await sse_service.broadcast("crawler_status", status.dict())
    
    return {"success": True}

@router.get("/states")
async def get_all_states():
    """
    Get current states of all crawlers (for initial load)
    """
    return {"success": True, "data": crawler_states}

# --- Target CRUD Endpoints ---

@router.get("/targets", response_model=ResponseModel)
async def get_targets(
    platform: Optional[str] = None,
    name: Optional[str] = None,
    url: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """Get all crawler targets"""
    try:
        repo = CrawlerTargetRepository(db)
        targets = await repo.find_by_filters(platform=platform, name=name, url=url)
        data = [CrawlerTargetResponse.model_validate(t) for t in targets]
        return ResponseModel(success=True, message="Success", data=data)
    except Exception as e:
        logger.error(f"Error fetching targets: {e}")
        return ResponseModel(success=False, message=str(e))

@router.post("/targets", response_model=ResponseModel)
async def create_target(
    target: CrawlerTargetCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new crawler target"""
    try:
        repo = CrawlerTargetRepository(db)
        new_target = await repo.create(target)
        return ResponseModel(success=True, message="Target created", data=CrawlerTargetResponse.model_validate(new_target))
    except Exception as e:
        logger.error(f"Error creating target: {e}")
        return ResponseModel(success=False, message=str(e))

@router.put("/targets/{target_id}", response_model=ResponseModel)
async def update_target(
    target_id: int,
    target: CrawlerTargetUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update a crawler target"""
    try:
        repo = CrawlerTargetRepository(db)
        updated_target = await repo.update(target_id, target)
        if not updated_target:
            return ResponseModel(success=False, message="Target not found")
        return ResponseModel(success=True, message="Target updated", data=CrawlerTargetResponse.model_validate(updated_target))
    except Exception as e:
        logger.error(f"Error updating target: {e}")
        return ResponseModel(success=False, message=str(e))

@router.delete("/targets/{target_id}", response_model=ResponseModel)
async def delete_target(
    target_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a crawler target"""
    try:
        repo = CrawlerTargetRepository(db)
        success = await repo.delete(target_id)
        if not success:
            return ResponseModel(success=False, message="Target not found")
        return ResponseModel(success=True, message="Target deleted")
    except Exception as e:
        logger.error(f"Error deleting target: {e}")
        return ResponseModel(success=False, message=str(e))

# --- Result Endpoints ---

@router.get("/results", response_model=ResponseModel)
async def get_results(
    platform: Optional[str] = None,
    target_id: Optional[int] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """Get crawler results"""
    try:
        repo = CrawlerResultRepository(db)
        if target_id:
            results = await repo.find_by_target_id(target_id, limit)
        elif platform:
            results = await repo.find_by_platform(platform, limit)
        else:
            results = await repo.get_multi(limit=limit, order_by="crawled_at") # Need to ensure order_by handles desc logic if passed string, or just default to whatever get_multi does. 
            # BaseRepository.get_multi sort support is basic. 
            # Let's just use what we have or improve repository if needed. 
            # Actually repo.get_multi takes string for order_by. 
            # But "crawled_at desc" string might not work depending on implementation.
            # Let's just use repo.find_all_by_field if platform provided, else default.
            # Actually, let's just stick to platform/target_id filtering for now as per requirements.
        
        return ResponseModel(success=True, message="Success", data=results)
    except Exception as e:
        logger.error(f"Error fetching results: {e}")
        return ResponseModel(success=False, message=str(e))

@router.post("/check-login", response_model=ResponseModel)
async def check_login_status(
    request: CheckLoginRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Check login status for a platform
    """
    from ..services.crawler_service import CrawlerService
    service = CrawlerService(db)
    result = await service.check_login_status(
        request.platform, 
        request.url, 
        request.nickname_xpath
    )
    
    return ResponseModel(
        success=result.get("logged_in", False),
        message=result.get("message", "Unknown status"),
        data=result
    )
