import pandas as pd
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.repositories.stock_repository import StockRepository, StockDataRepository
from app.models.stock import StockData
from app.models.tag_management import StockTagInfo, StockTagRelation
from loguru import logger

class AShareAdapter:
    """
    Adapter for accessing A-Share data and normalizing it for the AI context.
    Phase 1: Data Adapter Layer.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.stock_repo = StockRepository(session)
        self.data_repo = StockDataRepository(session)

    async def get_stock_context(self, stock_code: str) -> Dict[str, Any]:
        """
        Retrieves full context for a stock to be used in AI prompts.
        Includes basic info, latest price, and calculated indicators.
        """
        context = {}
        
        try:
            # 1. Basic Info
            stock_info = await self.stock_repo.find_by_code(stock_code)
            if stock_info:
                context["stock_name"] = stock_info.name
                context["stock_code"] = stock_code
                context["industry"] = getattr(stock_info, 'industry', "Unknown")
            else:
                context["stock_name"] = "Unknown"
                context["stock_code"] = stock_code
                context["industry"] = "Unknown"

            # 2. Latest Daily Data
            latest_daily = await self.data_repo.find_latest_by_code(stock_code)
            
            if latest_daily:
                context["current_price"] = float(latest_daily.close) if latest_daily.close else 0.0
                context["volume"] = float(latest_daily.vol) if latest_daily.vol else 0.0
                context["change_percent"] = float(latest_daily.pct_chg) if hasattr(latest_daily, 'pct_chg') and latest_daily.pct_chg else 0.0
                context["date"] = latest_daily.trade_date.isoformat() if latest_daily.trade_date else ""
            else:
                context["current_price"] = 0.0
                context["volume"] = 0.0
                context["change_percent"] = 0.0
                context["date"] = ""

            # 3. Get Tags (Simulating Signals)
            tags = await self._get_tags(stock_code)
            context["tags"] = tags
            
            # 4. Technical Indicators
            indicators = await self._calculate_indicators(stock_code)
            context.update(indicators)
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting stock context for {stock_code}: {e}")
            return context

    async def _calculate_indicators(self, stock_code: str) -> Dict[str, Any]:
        """Calculate technical indicators (MA, RSI) using pandas."""
        try:
            # Fetch last 30 days of data for MA20 and RSI14 calculation
            # Note: find_by_code returns data sorted by timestamp DESC
            data_list = await self.data_repo.find_by_code(stock_code, limit=40)
            
            if not data_list or len(data_list) < 5:
                return {}
            
            # Convert to DataFrame
            records = []
            for d in data_list:
                records.append({
                    "date": d.trade_date,
                    "close": float(d.close) if d.close else 0.0
                })
            
            df = pd.DataFrame(records)
            # Sort by date ASC for calculation
            df = df.sort_values("date", ascending=True)
            
            # Calculate MAs
            df["ma5"] = df["close"].rolling(window=5).mean()
            df["ma10"] = df["close"].rolling(window=10).mean()
            df["ma20"] = df["close"].rolling(window=20).mean()
            
            # Calculate RSI (14)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            
            # Avoid division by zero
            loss = loss.replace(0, 0.0001)
            rs = gain / loss
            df['rsi14'] = 100 - (100 / (1 + rs))
            
            # Get latest values (last row)
            latest = df.iloc[-1]
            
            indicators = {
                "ma5": round(latest["ma5"], 2) if pd.notna(latest["ma5"]) else None,
                "ma10": round(latest["ma10"], 2) if pd.notna(latest["ma10"]) else None,
                "ma20": round(latest["ma20"], 2) if pd.notna(latest["ma20"]) else None,
                "rsi14": round(latest["rsi14"], 2) if pd.notna(latest["rsi14"]) else None,
            }
            
            return indicators
        except Exception as e:
            logger.error(f"Error calculating indicators for {stock_code}: {e}")
            return {}
            
    async def _get_tags(self, stock_code: str) -> List[Dict[str, Any]]:
        """Get tags for the stock."""
        try:
            stmt = select(StockTagInfo.name, StockTagInfo.score, StockTagInfo.tag_type)\
                .join(StockTagRelation, StockTagInfo.id == StockTagRelation.tag_id)\
                .where(
                    StockTagRelation.stock_code == stock_code,
                    StockTagInfo.is_deleted == False
                )
            result = await self.session.execute(stmt)
            tags = []
            for name, score, tag_type in result.all():
                tags.append({
                    "name": name,
                    "score": float(score),
                    "type": tag_type
                })
            return tags
        except Exception as e:
            logger.error(f"Failed to get tags for {stock_code}: {e}")
            return []
