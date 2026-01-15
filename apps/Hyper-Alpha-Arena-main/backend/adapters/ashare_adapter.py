from typing import Dict, List, Optional, Any
from datetime import datetime, date
from decimal import Decimal
import json
import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from schemas.ashare import AShareContext

class AShareDataAdapter:
    """A股数据适配器"""
    
    def __init__(self, db_url: Optional[str] = None):
        # 默认使用环境变量配置，或者 fallback 到本地开发配置
        # 注意：这里使用 stock_user 用户，需要确保该用户在目标数据库中有权限
        self.db_url = db_url or os.getenv(
            "ASHARE_DB_URL", 
            "mysql+aiomysql://stock_user:stock123456@localhost:3306/stock_monitor?charset=utf8mb4"
        )
        self.engine = create_async_engine(
            self.db_url,
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_recycle=3600
        )
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def get_stock_context(self, symbol: str) -> Optional[AShareContext]:
        """
        获取股票完整上下文信息
        
        Args:
            symbol: 股票代码 (e.g., "000001")
            
        Returns:
            AShareContext or None if not found
        """
        async with self.async_session() as session:
            try:
                # 1. 获取基本信息
                # 使用 text() 构建原生 SQL 查询，确保与 stock-monitor 数据库结构兼容
                info_query = text("""
                    SELECT code, name, market, volume_anomaly_score, tdx_plugin_score, bonus_items 
                    FROM stock_info 
                    WHERE code = :code
                """)
                info_result = await session.execute(info_query, {"code": symbol})
                info_row = info_result.mappings().first()
                
                if not info_row:
                    return None
                
                # 2. 获取最新行情
                # 注意：stock_monitor 使用 stock_prices 表存储行情
                price_query = text("""
                    SELECT close_price, change_rate, volume, amount, trade_date 
                    FROM stock_prices 
                    WHERE symbol = :code 
                    ORDER BY trade_date DESC, request_timestamp DESC 
                    LIMIT 1
                """)
                price_result = await session.execute(price_query, {"code": symbol})
                price_row = price_result.mappings().first()
                
                # 3. 获取风险/评分数据
                # 注意：stock_tdx_risk 表存储通达信风险检测数据
                risk_query = text("""
                    SELECT total_score, risk_items, safe_items, highlight_items, raw_json 
                    FROM stock_tdx_risk 
                    WHERE stock_code = :code 
                    ORDER BY date DESC 
                    LIMIT 1
                """)
                risk_result = await session.execute(risk_query, {"code": symbol})
                risk_row = risk_result.mappings().first()
                
                # 数据处理与类型转换
                price = float(price_row['close_price']) if price_row else 0.0
                change_percent = float(price_row['change_rate']) if price_row else 0.0
                volume = int(price_row['volume']) if price_row else 0
                amount = float(price_row['amount']) if price_row else 0.0
                trade_date = price_row['trade_date'] if price_row else None
                
                # 解析 Tags 和 评分
                score = 0
                tags = []
                risk_info = {}
                
                # 解析 bonus_items (加分项)
                if info_row['bonus_items']:
                    try:
                        bonus = json.loads(info_row['bonus_items'])
                        if isinstance(bonus, list):
                            tags.extend([str(item) for item in bonus])
                        elif isinstance(bonus, dict):
                            tags.extend(bonus.keys())
                    except:
                        pass
                
                if risk_row:
                    score = risk_row['total_score'] or 0
                    risk_info = {
                        "risk_items": risk_row['risk_items'],
                        "safe_items": risk_row['safe_items'],
                        "highlight_items": risk_row['highlight_items']
                    }
                    # 尝试从 raw_json 提取更多标签
                    if risk_row['raw_json']:
                        try:
                            raw_data = risk_row['raw_json'] 
                            if isinstance(raw_data, str):
                                raw_data = json.loads(raw_data)
                            
                            # 假设 raw_json 结构中有 tags 或 similar
                            if isinstance(raw_data, dict) and 'tags' in raw_data:
                                tags.extend(raw_data['tags'])
                        except:
                            pass
                else:
                    # 如果没有 risk 数据，使用 info 中的评分作为备选
                    score = (info_row['tdx_plugin_score'] or 0) + (info_row['volume_anomaly_score'] or 0)

                return AShareContext(
                    symbol=info_row['code'],
                    name=info_row['name'],
                    market=info_row['market'],
                    price=price,
                    change_percent=change_percent,
                    volume=volume,
                    amount=amount,
                    trade_date=trade_date,
                    score=score,
                    tags=list(set(tags)),  # 去重
                    technical_pattern="N/A", # 暂无直接字段，后续可从 tags 推导
                    risk_info=risk_info,
                    last_updated=datetime.now()
                )
            except Exception as e:
                # 记录错误但不要崩溃，返回 None 或者抛出自定义异常
                print(f"Error fetching A-Share context for {symbol}: {e}")
                raise e

    async def get_multiple_stocks(self, symbols: List[str]) -> Dict[str, Optional[AShareContext]]:
        """
        批量获取股票信息
        """
        results = {}
        # TODO: 优化为批量查询以提高性能
        for symbol in symbols:
            results[symbol] = await self.get_stock_context(symbol)
        return results

    async def close(self):
        """关闭数据库连接"""
        await self.engine.dispose()
