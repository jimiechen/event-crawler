from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class MockStockData(BaseModel):
    code: str = Field(..., description="股票代码")
    name: str = Field(default="模拟股票", description="股票名称")
    current_price: float = Field(..., description="当前价格")
    volume: int = Field(..., description="成交量")
    volume_ratio: Optional[float] = Field(None, description="量比")
    change_percent: float = Field(..., description="涨跌幅(%)")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="时间戳")

class ValidationRequest(BaseModel):
    data: MockStockData
    strategy_config: Optional[Dict[str, Any]] = None

class ValidationResult(BaseModel):
    is_triggered: bool
    trigger_reason: str
    details: Dict[str, Any]

class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    data: MockStockData

class TemplateResponse(TemplateCreate):
    id: str

class RawValidationRequest(BaseModel):
    raw_data: Any = Field(..., description="原始同花顺数据(列表或字典)")
    strategy_config: Optional[Dict[str, Any]] = None

class RawValidationResult(BaseModel):
    decoded_success: bool
    decoded_data: Optional[Dict[str, Any]] = None
    decoding_errors: List[str] = []
    strategy_results: Dict[str, Any] = {}

class EnvCheckResult(BaseModel):
    component: str
    status: str
    message: str
    details: Dict[str, Any] = {}

class AddCustomStockRequest(BaseModel):
    code: str = Field(..., description="股票代码")
    label: str = Field(..., description="自定义标签")
    days: int = Field(250, description="加载K线天数")
    custom_date: Optional[str] = Field(None, description="自定义结束日期 (YYYY-MM-DD)")
    platform: Optional[str] = Field(None, description="强制使用指定平台: tushare, baostock, akshare")

class StockDailyData(BaseModel):
    trade_date: str
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    volume: Optional[float]
    amount: Optional[float]
    pct_chg: Optional[float] = None
    change_percent: Optional[float] = None
    adj_factor: Optional[float] = None

class AddCustomStockResponse(BaseModel):
    success: bool
    message: str
    stock_info: Dict[str, Any]
    daily_data: List[StockDailyData] = []
