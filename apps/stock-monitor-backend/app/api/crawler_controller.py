from fastapi import APIRouter, Request, HTTPException, Depends, Query
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from ..services.sse_service import sse_service
from ..database import get_db_session
from ..repositories.crawler_repository import CrawlerTargetRepository, CrawlerResultRepository
from ..models.crawler import CrawlerLoginStatus
from ..services.cookie_service import CookieService
from ..services.crawler_service import CrawlerService
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

class RealheadFetchRequest(BaseModel):
    stock_codes: Optional[List[str]] = Field(None, description="股票代码列表，为空则抓取自选股")

# --- In-Memory State ---

# Store latest status in memory (or Redis if needed)
crawler_states: Dict[str, Dict[str, Any]] = {}

# --- SSE Endpoints ---

@router.get("/events")
async def sse_endpoint(request: Request):
    """
    SSE endpoint for real-time updates
    """
    # Trigger reload
    return await sse_service.subscribe(request)

@router.post("/check-login", response_model=ResponseModel)
async def check_login(
    request: CheckLoginRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    检查登录状态
    """
    try:
        service = CrawlerService(db)
        result = await service.check_login_status(
            platform=request.platform,
            url=request.url,
            nickname_xpath=request.nickname_xpath
        )
        return ResponseModel(
            success=True,
            message="Check login status completed",
            data=result
        )
    except Exception as e:
        logger.error(f"Check login status failed: {e}")
        return ResponseModel(success=False, message=str(e))

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

@router.post("/realhead/fetch", response_model=ResponseModel)
async def fetch_realhead_data(
    request: RealheadFetchRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    抓取 realhead 数据
    """
    try:
        from app.crawler.realhead_crawler import RealheadCrawler
        
        crawler = RealheadCrawler(db)
        result = await crawler.crawl(request.stock_codes)
        
        # 保存到数据库
        if result.get('data'):
            stock_service = StockService(db)
            for stock_data in result['data']:
                try:
                    await stock_service.create_or_update_stock_info({
                        'stock_code': stock_data.get('stock_code'),
                        'stock_name': stock_data.get('stock_name'),
                        'market': 'SZ' if stock_data.get('stock_code', '').startswith(('0', '2', '3')) else 'SH'
                    })
                    
                    # 保存到 tonghuashun_stocks 表
                    await stock_service.submit_stock_data([stock_data])
                    
                except Exception as e:
                    logger.error(f"保存股票数据失败: {e}")
                    continue
        
        return ResponseModel(
            success=True,
            message=f"抓取成功，共 {result.get('count', 0)} 条数据",
            data=result
        )
        
    except Exception as e:
        logger.error(f"抓取失败: {e}")
        return ResponseModel(
            success=False,
            message=f"抓取失败: {str(e)}"
        )

# --- Targets Endpoints ---
@router.get("/targets", response_model=ResponseModel)
async def get_targets(
    platform: Optional[str] = Query(None, description="平台筛选"),
    name: Optional[str] = Query(None, description="名称筛选"),
    url: Optional[str] = Query(None, description="URL筛选"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取爬虫目标列表
    """
    try:
        repo = CrawlerTargetRepository(db)
        targets = await repo.find_by_filters(platform=platform, name=name, url=url)
        return ResponseModel(
            success=True,
            message="Success",
            data=[CrawlerTargetResponse.model_validate(t) for t in targets]
        )
    except Exception as e:
        logger.error(f"获取目标列表失败: {e}")
        return ResponseModel(success=False, message=str(e))

@router.post("/targets", response_model=ResponseModel)
async def create_target(
    request: CrawlerTargetCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    创建爬虫目标
    """
    try:
        repo = CrawlerTargetRepository(db)
        new_target = CrawlerTarget(
            platform=request.platform,
            name=request.name,
            url=request.url,
            target_type=request.target_type,
            is_active=request.is_active,
            description=request.description,
            xpath_config=request.xpath_config
        )
        await repo.create(new_target)
        return ResponseModel(
            success=True,
            message="Target created successfully",
            data=CrawlerTargetResponse.model_validate(new_target)
        )
    except Exception as e:
        logger.error(f"创建目标失败: {e}")
        return ResponseModel(success=False, message=str(e))

@router.put("/targets/{target_id}", response_model=ResponseModel)
async def update_target(
    target_id: int,
    request: CrawlerTargetUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    更新爬虫目标
    """
    try:
        repo = CrawlerTargetRepository(db)
        target = await repo.get_by_id(target_id)
        if not target:
            return ResponseModel(success=False, message="Target not found")
        
        # Update fields
        if request.platform is not None:
            target.platform = request.platform
        if request.name is not None:
            target.name = request.name
        if request.url is not None:
            target.url = request.url
        if request.target_type is not None:
            target.target_type = request.target_type
        if request.is_active is not None:
            target.is_active = request.is_active
        if request.description is not None:
            target.description = request.description
        if request.xpath_config is not None:
            target.xpath_config = request.xpath_config
        
        await repo.update(target)
        return ResponseModel(
            success=True,
            message="Target updated successfully",
            data=CrawlerTargetResponse.model_validate(target)
        )
    except Exception as e:
        logger.error(f"更新目标失败: {e}")
        return ResponseModel(success=False, message=str(e))

@router.delete("/targets/{target_id}", response_model=ResponseModel)
async def delete_target(
    target_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    删除爬虫目标
    """
    try:
        repo = CrawlerTargetRepository(db)
        success = await repo.delete(target_id)
        if success:
            return ResponseModel(success=True, message="Target deleted successfully")
        return ResponseModel(success=False, message="Target not found")
    except Exception as e:
        logger.error(f"删除目标失败: {e}")
        return ResponseModel(success=False, message=str(e))

@router.post("/targets/{target_id}/toggle", response_model=ResponseModel)
async def toggle_target_active(
    target_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    切换目标激活状态
    """
    try:
        repo = CrawlerTargetRepository(db)
        target = await repo.get_by_id(target_id)
        if not target:
            return ResponseModel(success=False, message="Target not found")
        
        target.is_active = not target.is_active
        await repo.update(target)
        return ResponseModel(
            success=True,
            message=f"Target {'activated' if target.is_active else 'deactivated'} successfully",
            data=CrawlerTargetResponse.model_validate(target)
        )
    except Exception as e:
        logger.error(f"切换目标状态失败: {e}")
        return ResponseModel(success=False, message=str(e))

# --- Cookies Endpoints ---
@router.get("/cookies", response_model=ResponseModel)
async def get_cookies(
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取Cookie列表（兼容旧接口）
    """
    try:
        cookie_service = CookieService(db)
        cookies = await cookie_service.get_all_cookies()
        return ResponseModel(
            success=True,
            message="Success",
            data=cookies
        )
    except Exception as e:
        logger.error(f"获取Cookie列表失败: {e}")
        return ResponseModel(success=False, message=str(e))

# --- Results Endpoints ---
@router.get("/results", response_model=ResponseModel)
async def get_results(
    platform: Optional[str] = Query(None, description="平台筛选"),
    limit: int = Query(100, description="返回数量限制"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取爬虫结果列表
    """
    try:
        repo = CrawlerResultRepository(db)
        if platform:
            results = await repo.find_by_platform(platform, limit=limit)
        else:
            # Get all results if no platform filter
            results = await repo.find_all()
        
        return ResponseModel(
            success=True,
            message="Success",
            data=[CrawlerResultResponse.model_validate(r) for r in results]
        )
    except Exception as e:
        logger.error(f"获取结果列表失败: {e}")
        return ResponseModel(success=False, message=str(e))

# --- States Endpoints ---
@router.get("/states", response_model=ResponseModel)
async def get_states():
    """
    获取爬虫状态列表
    """
    try:
        return ResponseModel(
            success=True,
            message="Success",
            data=crawler_states
        )
    except Exception as e:
        logger.error(f"获取状态列表失败: {e}")
        return ResponseModel(success=False, message=str(e))
