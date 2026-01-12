from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# --- Tag Schemas ---

class TagBase(BaseModel):
    name: str = Field(..., max_length=50, description="标签名称")
    score: Decimal = Field(default=0.00, description="分值")
    tag_type: str = Field(default="calculation", description="标签类型")

class TagCreate(TagBase):
    pass

class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50, description="标签名称")
    score: Optional[Decimal] = Field(None, description="分值")
    tag_type: Optional[str] = Field(None, description="标签类型")

class TagResponse(TagBase):
    id: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    relation_created_at: Optional[datetime] = Field(None, description="关联时间")
    stocks: List[Dict[str, Any]] = Field(default_factory=list, description="关联股票列表 [{'code': '...', 'name': '...', 'daily_change': float}]")
    
    model_config = ConfigDict(from_attributes=True)

class TagListResponse(BaseModel):
    total: int
    items: List[TagResponse]

# --- Stock Association Schemas ---

class StockTagsBatchRequest(BaseModel):
    stock_code: str = Field(..., description="股票代码")
    tags: List[TagCreate] = Field(..., description="标签列表")


class StockRelationCreate(BaseModel):
    stock_codes: List[str] = Field(..., description="股票代码列表")
    tag_id: int = Field(..., description="标签ID")

class StockRelationRemove(BaseModel):
    stock_codes: List[str] = Field(..., description="股票代码列表")
    tag_id: int = Field(..., description="标签ID")

class TagStockRelationResponse(BaseModel):
    stock_code: str
    tag_id: int
    tag_name: str
    tag_score: Decimal
    created_at: datetime

class StockTagsResponse(BaseModel):
    stock_code: str
    tags: List[TagResponse]
    total_score: Decimal

# --- Operation Log Schemas ---

class OperationLogResponse(BaseModel):
    id: int
    operator: str
    action: str
    target_type: str
    target_id: str
    details: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
