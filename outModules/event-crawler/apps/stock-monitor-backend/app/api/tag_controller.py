from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.services.tag_management_service import TagManagementService
from app.api.tag_schemas import (
    TagCreate, TagUpdate, TagResponse, TagListResponse,
    StockRelationCreate, StockRelationRemove, StockTagsResponse,
    OperationLogResponse, StockTagsBatchRequest
)
from app.api.schemas import BaseResponse

router = APIRouter(prefix="/api/v1/tags", tags=["Tag Management"])

def get_service(db: AsyncSession = Depends(get_db_session)) -> TagManagementService:
    return TagManagementService(db)

@router.get("", response_model=BaseResponse)
async def get_tags(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=5000),
    name: Optional[str] = None,
    date_filter: Optional[str] = None,
    tag_type: Optional[str] = None,
    service: TagManagementService = Depends(get_service)
):
    """获取标签列表"""
    items, total = await service.get_tags(page, page_size, name, date_filter, tag_type)
    tag_list = [TagResponse.model_validate(item) for item in items]
    return BaseResponse(data={"total": total, "items": tag_list})

@router.get("/{tag_id}/stocks", response_model=BaseResponse)
async def get_tag_stocks_paginated_endpoint(
    tag_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=5000),
    service: TagManagementService = Depends(get_service)
):
    """获取标签关联的股票列表 (分页)"""
    stocks, total = await service.get_tag_stocks_paginated(tag_id, page, page_size)
    return BaseResponse(data={"total": total, "items": stocks})

@router.post("", response_model=BaseResponse)
async def create_tag(
    tag: TagCreate,
    service: TagManagementService = Depends(get_service)
):
    """创建标签"""
    try:
        new_tag = await service.create_tag(tag)
        return BaseResponse(data=TagResponse.model_validate(new_tag))
    except ValueError as e:
        return BaseResponse(success=False, message=str(e))

@router.post("/batch", response_model=BaseResponse)
async def batch_import_tags(
    tags: List[TagCreate],
    service: TagManagementService = Depends(get_service)
):
    """批量导入标签"""
    result = await service.batch_import_tags(tags)
    return BaseResponse(data=result)

@router.put("/{tag_id}", response_model=BaseResponse)
async def update_tag(
    tag_id: int,
    tag: TagUpdate,
    service: TagManagementService = Depends(get_service)
):
    """更新标签"""
    try:
        updated_tag = await service.update_tag(tag_id, tag)
        if not updated_tag:
            return BaseResponse(success=False, message="Tag not found")
        return BaseResponse(data=TagResponse.model_validate(updated_tag))
    except ValueError as e:
        return BaseResponse(success=False, message=str(e))

@router.delete("/{tag_id}", response_model=BaseResponse)
async def delete_tag(
    tag_id: int,
    service: TagManagementService = Depends(get_service)
):
    """删除标签"""
    success = await service.delete_tag(tag_id)
    if not success:
        return BaseResponse(success=False, message="Tag not found")
    return BaseResponse(message="Deleted successfully")

# --- Relations ---

@router.post("/{tag_id}/stocks", response_model=BaseResponse)
async def associate_stocks(
    tag_id: int,
    relation: StockRelationCreate,
    service: TagManagementService = Depends(get_service)
):
    """关联股票"""
    try:
        await service.associate_stocks(tag_id, relation.stock_codes)
        return BaseResponse(message="Associated successfully")
    except ValueError as e:
        return BaseResponse(success=False, message=str(e))

@router.delete("/{tag_id}/stocks", response_model=BaseResponse)
async def dissociate_stocks(
    tag_id: int,
    relation: StockRelationRemove,
    service: TagManagementService = Depends(get_service)
):
    """取消关联股票"""
    await service.dissociate_stocks(tag_id, relation.stock_codes)
    return BaseResponse(message="Dissociated successfully")

@router.post("/stock/batch-add", response_model=BaseResponse)
async def add_tags_to_stock(
    request: StockTagsBatchRequest,
    service: TagManagementService = Depends(get_service)
):
    """批量给股票添加标签"""
    try:
        result = await service.add_tags_to_stock(request.stock_code, request.tags)
        return BaseResponse(data=result)
    except Exception as e:
        return BaseResponse(success=False, message=str(e))

@router.get("/stocks/{stock_code}", response_model=BaseResponse)
async def get_stock_tags(
    stock_code: str,
    service: TagManagementService = Depends(get_service)
):
    """获取股票的标签和总分"""
    result = await service.get_stock_tags(stock_code)
    if result.get("tags"):
        result["tags"] = [TagResponse.model_validate(t) for t in result["tags"]]
    return BaseResponse(data=result)

@router.get("/{tag_id}/all-stocks", response_model=BaseResponse)
async def get_all_tag_stocks_endpoint(
    tag_id: int,
    service: TagManagementService = Depends(get_service)
):
    """获取标签关联的所有股票代码"""
    result = await service.get_all_tag_stocks(tag_id)
    return BaseResponse(data=result)

# --- Logs ---

@router.get("/logs", response_model=BaseResponse)
async def get_operation_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: TagManagementService = Depends(get_service)
):
    """获取操作日志"""
    items, total = await service.get_logs(page, page_size)
    log_list = [OperationLogResponse.model_validate(item) for item in items]
    return BaseResponse(data={"total": total, "items": log_list})
