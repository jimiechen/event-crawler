from typing import List, Dict, Any, Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, func
from sqlalchemy.orm import aliased
from app.models.stock_daily import StockScoreResult
from app.models.stock import StockInfo

class RankingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_previous_trading_date(self, current_date: date) -> Optional[date]:
        query = select(StockScoreResult.trade_date)\
            .where(StockScoreResult.trade_date < current_date)\
            .order_by(StockScoreResult.trade_date.desc())\
            .limit(1)
        result = await self.db.execute(query)
        return result.scalar()

    async def get_latest_score_date(self) -> Optional[date]:
        query = select(func.max(StockScoreResult.trade_date))
        result = await self.db.execute(query)
        return result.scalar()

    async def get_score_growth_ranking(self, start_date: date, end_date: date, limit: int = 20):
        # If start and end are same, try to find previous date
        if start_date == end_date:
            prev_date = await self.get_previous_trading_date(start_date)
            if not prev_date:
                # Fallback: if no previous date, just return empty list or maybe top scores
                # But requirement is "growth", so we need a base.
                return [] 
            base_date = prev_date
            target_date = end_date
        else:
            base_date = start_date
            target_date = end_date

        # Aliases for self-join
        TargetScore = aliased(StockScoreResult)
        BaseScore = aliased(StockScoreResult)

        query = select(
            TargetScore.code,
            StockInfo.name,
            TargetScore.total_score.label('end_score'),
            BaseScore.total_score.label('start_score'),
            TargetScore.total_score.label('growth'),
            TargetScore.rule_scores
        ).join(
            BaseScore, 
            and_(
                TargetScore.code == BaseScore.code,
                BaseScore.trade_date == base_date
            )
        ).outerjoin(
            StockInfo,
            TargetScore.code == StockInfo.code
        ).where(
            TargetScore.trade_date == target_date
        ).order_by(
            desc('growth')
        ).limit(limit)

        result = await self.db.execute(query)
        rows = result.all()
        
        return [
            {
                "code": row.code,
                "name": row.name,
                "score": float(row.end_score) if row.end_score is not None else 0.0,
                "growth": float(row.growth) if row.growth is not None else 0.0,
                "rule_scores": row.rule_scores,
                "date": target_date
            }
            for row in rows
        ]

    async def get_total_score_ranking(self, target_date: date, limit: int = 20):
        # Calculate start date for 250 days window
        # User requirement: Total ranking is 250 days total score (from target_date back 250 days)
        from datetime import timedelta
        # Explicitly use 250 days as requested
        start_date = target_date - timedelta(days=250)

        total_score_col = func.sum(StockScoreResult.total_score).label('total_score')

        query = select(
            StockScoreResult.code,
            StockInfo.name,
            total_score_col
        ).outerjoin(
            StockInfo,
            StockScoreResult.code == StockInfo.code
        ).where(
            and_(
                StockScoreResult.trade_date <= target_date,
                StockScoreResult.trade_date > start_date  # > start_date to include exactly 250 days? or >=? 
                                                        # "往前250天" usually means [date-250, date].
                                                        # Let's keep >= start_date.
            )
        ).group_by(
            StockScoreResult.code,
            StockInfo.name
        ).order_by(
            desc(total_score_col)
        ).limit(limit)

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "code": row.code,
                "name": row.name,
                "score": float(row.total_score) if row.total_score is not None else 0.0,
                "date": target_date
            }
            for row in rows
        ]

