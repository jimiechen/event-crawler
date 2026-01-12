from fastapi import APIRouter, Request, HTTPException, Depends, Query
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from ..services.sse_service import sse_service
from ..database import get_db_session
from ..repositories.crawler_repository import CrawlerTargetRepository, CrawlerResultRepository
from ..models.crawler import CrawlerLoginStatus
from loguru import logger
import sys
import os

# Add module path dynamically
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../../../.."))
crawler_module_path = os.path.join(project_root, "modules/module-playwright-crawler/src")
if crawler_module_path not in sys.path:
    sys.path.append(crawler_module_path)

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

    model_config = ConfigDict(from_attributes=True)

class CookieUpdate(BaseModel):
    account_name: Optional[str] = None
    test_url: Optional[str] = None
    xpath_config: Optional[str] = None
    is_valid: Optional[bool] = None

class CheckLoginRequest(BaseModel):
    platform: str
    url: Optional[str] = None
    nickname_xpath: Optional[str] = None

class ParseHtmlRequest(BaseModel):
    platform: str
    html: str
    url: Optional[str] = None

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

    model_config = ConfigDict(from_attributes=True)

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
    SSE endpoint for real-time updates
    """
    return await sse_service.subscribe(request)

@router.post("/parse_html")
async def parse_html(
    request: ParseHtmlRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    解析HTML并检查登录状态
    """
    try:
        from playwright_crawler import LovartCrawler, TempmailCrawler, StitchCrawler, DeepseekCrawler
    except ImportError as e:
         logger.error(f"Failed to import crawler module: {e}")
         raise HTTPException(status_code=500, detail=f"Failed to import crawler module: {e}")

    crawler = None
    if request.platform == 'lovart':
        crawler = LovartCrawler()
    elif request.platform == 'tempmail':
        crawler = TempmailCrawler()
    elif request.platform == 'stitch':
        crawler = StitchCrawler()
    elif request.platform == 'deepseek':
        crawler = DeepseekCrawler()
    
    if not crawler:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {request.platform}")

    try:
        # Parse HTML
        parsed_data = crawler.parse_html(request.html)
        
        # Check Login Status
        login_status = crawler.check_login_status_from_html(request.html)
        
        # Save login status
        new_status = CrawlerLoginStatus(
            platform=request.platform,
            is_logged_in=login_status.get('logged_in', False),
            message=login_status.get('message'),
            checked_at=datetime.now()
        )
        db.add(new_status)
        await db.commit()
        
        return {
            "success": True,
            "data": parsed_data,
            "login_status": login_status
        }
    except Exception as e:
        logger.error(f"Error processing HTML for {request.platform}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

# --- Debug Log Storage ---
debug_logs = []

class DebugHtmlRequest(BaseModel):
    platform: str
    url: str
    xpath: str
    html: str

@router.post("/debughtml")
async def debug_html(request: DebugHtmlRequest):
    """
    Debug HTML with XPath
    """
    try:
        from playwright_crawler import LovartCrawler, TempmailCrawler, StitchCrawler, DeepseekCrawler
        from lxml import etree
    except ImportError as e:
         logger.error(f"Failed to import crawler module: {e}")
         raise HTTPException(status_code=500, detail=f"Failed to import crawler module: {e}")

    logger.info(f"Debugging HTML for {request.platform} with XPath: {request.xpath}")

    # Use lxml for XPath
    try:
        parser = etree.HTMLParser()
        tree = etree.fromstring(request.html, parser)
        results = tree.xpath(request.xpath)
        
        extracted_data = []
        if results:
            for res in results:
                if hasattr(res, 'text'):
                    extracted_data.append(res.text)
                elif isinstance(res, str):
                    extracted_data.append(res)
                else:
                    extracted_data.append(str(res))
            
            result_str = "\n".join(extracted_data)
        else:
            result_str = "No match found"
            
    except Exception as e:
        result_str = f"XPath Error: {str(e)}"

    # Log the debug session
    log_entry = {
        "platform": request.platform,
        "url": request.url,
        "xpath": request.xpath,
        "result": result_str,
        "created_at": datetime.now().isoformat()
    }
    
    # Keep last 50 logs
    debug_logs.insert(0, log_entry)
    if len(debug_logs) > 50:
        debug_logs.pop()
        
    return {"success": True, "data": log_entry}

@router.get("/debug_logs")
async def get_debug_logs():
    """
    Get recent debug logs
    """
    return {"success": True, "data": debug_logs}
