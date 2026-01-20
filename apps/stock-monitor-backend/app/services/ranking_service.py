from typing import List, Dict, Any, Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, func
from sqlalchemy.orm import aliased
from app.models.stock_daily import StockScoreResult, StockDaily
from app.models.stock import StockInfo, WencaiStock
from app.database import db_manager
from .volume_analysis_service import VolumeAnalysisService
from loguru import logger

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

    async def has_scores_for_date(self, target_date: date) -> bool:
        """
        Check if there are any VALID score results for the target date.
        Valid means we have records AND at least one record has non-zero accumulated_score.
        This prevents the system from getting stuck with 0-score records (bug state).
        """
        # 1. Check if any records exist
        query_count = select(func.count(StockScoreResult.id)).where(StockScoreResult.trade_date == target_date)
        res_count = await self.db.execute(query_count)
        count = res_count.scalar()
        
        if count == 0:
            return False
            
        # 2. Check if we have any non-zero accumulated scores
        # If all scores are 0, it implies a calculation bug or incomplete state, so we return False to trigger recalc.
        query_valid = select(func.count(StockScoreResult.id)).where(
            StockScoreResult.trade_date == target_date,
            StockScoreResult.accumulated_score != 0
        )
        res_valid = await self.db.execute(query_valid)
        valid_count = res_valid.scalar()
        
        return valid_count > 0

    async def get_score_growth_ranking(self, start_date: date, end_date: date, limit: int = 20, pool_type: Optional[str] = None):
        """
        Calculate ranking based on score growth (sum of daily scores) between start_date and end_date.
        Growth = Sum(daily_score) in range.
        # ALWAYS uses WencaiStock pool.
        """
        # Calculate growth as Sum(daily_score) in range
        
        conditions = [
            StockScoreResult.trade_date >= start_date,
            StockScoreResult.trade_date <= end_date
        ]
        
        # Use WencaiStock table exclusively
        # Use LEFT JOIN to include stocks with 0 growth (null sum becomes 0)
        stmt = select(
            WencaiStock.stock_code.label('code'),
            func.coalesce(func.sum(StockScoreResult.daily_score), 0).label('growth'),
        ).outerjoin(
            StockScoreResult, and_(
                WencaiStock.stock_code == StockScoreResult.code,
                *conditions
            )
        ).group_by(
            WencaiStock.stock_code
        ).order_by(
            desc('growth')
        ).limit(limit)
        
        result = await self.db.execute(stmt)
        growth_rows = result.all()
        
        if not growth_rows:
            return []
            
        # Fetch details (name, latest rule_scores) for these codes
        codes = [row.code for row in growth_rows]
        
        # Get Stock Names from WencaiStock
        names_query = select(WencaiStock.stock_code, WencaiStock.stock_name).where(WencaiStock.stock_code.in_(codes))
        names_res = await self.db.execute(names_query)
        names_map = {r.stock_code: r.stock_name for r in names_res.all()}
        
        # Get Latest Details (from end_date or latest available in range)
        # To simplify, we try to get the record on end_date
        details_query = select(
            StockScoreResult.code,
            StockScoreResult.rule_scores,
            StockScoreResult.accumulated_score,
            StockScoreResult.ranking
        ).where(
            StockScoreResult.code.in_(codes),
            StockScoreResult.trade_date == end_date
        )
        details_res = await self.db.execute(details_query)
        details_map = {r.code: r for r in details_res.all()}

        # Get Previous Rankings for Rank Change Calculation
        previous_date = await self.get_previous_trading_date(end_date)
        prev_rankings_map = {}
        if previous_date:
            prev_rank_query = select(
                StockScoreResult.code,
                StockScoreResult.ranking
            ).where(
                StockScoreResult.code.in_(codes),
                StockScoreResult.trade_date == previous_date
            )
            prev_rank_res = await self.db.execute(prev_rank_query)
            prev_rankings_map = {r.code: r.ranking for r in prev_rank_res.all()}
        
        ranking_data = []
        for row in growth_rows:
            code = row.code
            growth = float(row.growth or 0)
            name = names_map.get(code, code)
            
            detail = details_map.get(code)
            rule_scores = detail.rule_scores if detail else {}
            # Fallback for accumulated_score if detail is missing
            accumulated_score = float(detail.accumulated_score) if detail and detail.accumulated_score is not None else 0.0
            
            # Rank Change Calculation
            current_rank = detail.ranking if detail else None
            prev_rank = prev_rankings_map.get(code)
            
            rank_change = 0
            if current_rank is not None and prev_rank is not None:
                # Positive change means rank improved (smaller number is better)
                # e.g. Prev 5, Curr 1 -> Change +4
                rank_change = prev_rank - current_rank
            elif current_rank is not None and prev_rank is None:
                # New entry
                rank_change = 9999 # Special value for "New"
            
            # Base/Dynamic Split (Currently assuming Base=0, Dynamic=Daily Score)
            # In single-day mode, growth == daily_score
            base_score = 0.0
            dynamic_score = growth
            
            ranking_data.append({
                "code": code,
                "name": name,
                "growth": growth,
                "score": accumulated_score, # Total Accumulated Score
                "base_score": base_score,
                "dynamic_score": dynamic_score,
                "rank_change": rank_change,
                "rule_scores": rule_scores,
                "date": end_date
            })
            
        return ranking_data

    async def get_total_score_ranking(self, target_date: date, limit: int = 20):
        """
        Calculate ranking based on accumulated_score (Latest available snapshot).
        Finds the latest score record for each stock on or before target_date.
        Compatible with MySQL 5.7 (No Window Functions).
        """
        from datetime import timedelta
        
        # 3. 使用 Max-Date 子查询获取每个股票在 target_date 之前(含)的最新一条记录
        # Strategy:
        # 1. Subquery: Find MAX(trade_date) for each code where trade_date <= target_date
        # 2. Join StockScoreResult on (code, trade_date) == (code, max_date)
        
        # Subquery: Get latest date per stock
        latest_dates_subquery = select(
            StockScoreResult.code,
            func.max(StockScoreResult.trade_date).label('max_date')
        ).where(
            StockScoreResult.trade_date <= target_date
        ).group_by(
            StockScoreResult.code
        ).subquery()
        
        stmt = select(
            WencaiStock.stock_code.label('code'),
            WencaiStock.stock_name,
            StockScoreResult.accumulated_score.label('total_score')
        ).join(
            latest_dates_subquery, 
            WencaiStock.stock_code == latest_dates_subquery.c.code
        ).join(
            StockScoreResult, and_(
                StockScoreResult.code == latest_dates_subquery.c.code,
                StockScoreResult.trade_date == latest_dates_subquery.c.max_date
            )
        ).order_by(
            desc('total_score')
        ).limit(limit)
        
        result = await self.db.execute(stmt)
        rows = result.all()
        
        if not rows:
            return []
            
        ranking_data = []
        for idx, row in enumerate(rows):
            code = row.code
            total_score = float(row.total_score or 0)
            ranking = idx + 1
            
            ranking_data.append({
                "code": code,
                "name": row.stock_name,
                "score": total_score,
                "rank": ranking
            })
            
        return ranking_data

