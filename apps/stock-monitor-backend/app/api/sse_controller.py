from fastapi import APIRouter, Request
from app.services.sse_service import sse_service

router = APIRouter(prefix="/api/sse", tags=["SSE"])

@router.get("/subscribe")
async def sse_endpoint(request: Request):
    """
    通用SSE订阅端点
    """
    return await sse_service.subscribe(request)
