from typing import List, Dict, Any, Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, func
from sqlalchemy.orm import aliased
from app.models.stock_daily import StockScoreResult, StockDaily
from app.models.stock import StockInfo
from .volume_analysis_service import VolumeAnalysisService

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
        """
        Calculate ranking based on total score of anomalies over the last 250 days.
        Uses Pandas for efficient calculation of Limit Up, Volume Multiples, and Low Volume.
        """
        import pandas as pd
        import numpy as np
        from datetime import timedelta
        
        # 1. Determine Date Range
        # We need 250 days for scoring, plus 60 days buffer for Low Volume calculation
        start_date = target_date - timedelta(days=250)
        data_start_date = start_date - timedelta(days=100) # Buffer
        
        # 2. Fetch Data (Active Stocks Only to optimize)
        stmt = select(
            StockDaily.code, 
            StockDaily.trade_date, 
            StockDaily.close, 
            StockDaily.vol,
            StockInfo.name
        ).join(
            StockInfo, StockDaily.code == StockInfo.code
        ).where(
            and_(
                StockInfo.is_active == True,
                StockDaily.trade_date >= data_start_date,
                StockDaily.trade_date <= target_date
            )
        )
        
        result = await self.db.execute(stmt)
        # Convert to list of dicts for DataFrame
        data = [
            {
                "code": row.code, 
                "trade_date": row.trade_date, 
                "close": float(row.close or 0), 
                "vol": float(row.vol or 0),
                "name": row.name
            } 
            for row in result
        ]
        
        if not data:
            return []
            
        df = pd.DataFrame(data)
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df = df.sort_values(['code', 'trade_date'])
        
        # 3. Calculate Scores using Service
        scores = VolumeAnalysisService.calculate_scores_batch(df, group_col='code')
        df['score'] = scores
            
        # 4. Filter Date Range and Sum
        # Target Range: [start_date, target_date]
        # Optimize date comparison
        start_ts = pd.Timestamp(start_date)
        end_ts = pd.Timestamp(target_date)
        mask_date = (df['trade_date'] >= start_ts) & (df['trade_date'] <= end_ts)
        df_final = df[mask_date]
        
        # Group by code to get total score
        ranking = df_final.groupby(['code', 'name'])['score'].sum().reset_index()
        ranking = ranking.sort_values('score', ascending=False).head(limit)
        
        return [
            {
                "code": row['code'],
                "name": row['name'],
                "score": float(row['score']),
                "date": target_date
            }
            for _, row in ranking.iterrows()
        ]

