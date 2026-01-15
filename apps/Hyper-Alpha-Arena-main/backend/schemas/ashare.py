from typing import List, Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field

class AShareContext(BaseModel):
    """A股上下文数据模型"""
    symbol: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    market: str = Field(..., description="市场类型")
    price: float = Field(..., description="当前价格")
    change_percent: float = Field(..., description="涨跌幅(%)")
    volume: int = Field(..., description="成交量")
    amount: float = Field(..., description="成交额")
    trade_date: Optional[date] = Field(None, description="交易日期")
    score: int = Field(0, description="综合评分")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    technical_pattern: Optional[str] = Field(None, description="技术形态")
    risk_info: Dict[str, Any] = Field(default_factory=dict, description="风险信息")
    last_updated: datetime = Field(default_factory=datetime.now, description="最后更新时间")

    class Config:
        from_attributes = True
