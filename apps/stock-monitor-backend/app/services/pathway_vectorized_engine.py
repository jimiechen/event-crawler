
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.tag_management import StockTagInfo

class PathwayVectorizedEngine:
    """
    High-performance Vectorized Pathway Engine
    Uses Pandas for batch calculation of indicators and tags.
    """

    def __init__(self, db_session: AsyncSession = None):
        self.db_session = db_session
        self.tag_scores_map = {}

    async def _ensure_tag_scores(self):
        """Load tag scores from DB"""
        if self.tag_scores_map:
            return

        if self.db_session:
            try:
                stmt = select(StockTagInfo).where(StockTagInfo.tag_type == 'calculation')
                result = await self.db_session.execute(stmt)
                tags = result.scalars().all()
                self.tag_scores_map = {tag.name: float(tag.score) for tag in tags}
                logger.info(f"Loaded {len(self.tag_scores_map)} tag scores")
            except Exception as e:
                logger.error(f"Failed to load tag scores: {e}")
        
        # Default fallbacks if DB load fails or not provided
        defaults = {
            '3倍量': 300, '2倍量': 200, '涨停': 100, '阳包阴': 100, 
            '底分型': 100, '冲高回落': -50, '60日地量': 600, 
            '30日地量': 300, 'EXPMA13上方': 50, '地量比率': 100
        }
        for k, v in defaults.items():
            if k not in self.tag_scores_map:
                self.tag_scores_map[k] = v

    def calculate_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate tags and scores for the entire DataFrame at once.
        df must have index as datetime (trade_date) or strictly sorted by date.
        df columns: open, close, high, low, vol
        """
        # Ensure sorted
        df = df.sort_values('trade_date').copy()
        
        # 1. Pre-calculate indicators
        # Volume Ratio
        df['vol_prev'] = df['vol'].shift(1)
        df['vol_ratio'] = np.where(df['vol_prev'] > 0, df['vol'] / df['vol_prev'], 0)
        
        # Price Change
        df['close_prev'] = df['close'].shift(1)
        df['pct_chg'] = np.where(df['close_prev'] > 0, (df['close'] - df['close_prev']) / df['close_prev'], 0)
        
        # EXPMA 13
        df['expma13'] = df['close'].ewm(span=13, adjust=False).mean()
        
        # Ground Volume (Low Volume)
        # Rolling min volume for N days (excluding today)
        # Shift 1 to exclude today from the window, then rolling min
        vol_shifted = df['vol'].shift(1)
        df['min_vol_60'] = vol_shifted.rolling(window=60).min()
        df['min_vol_30'] = vol_shifted.rolling(window=30).min()
        
        # 2. Vectorized Tag Logic
        
        # Initialize Score and Tags columns
        df['daily_score'] = 0.0
        df['tags'] = [[] for _ in range(len(df))] # List of strings
        
        def add_tag(condition, tag_name):
            score = self.tag_scores_map.get(tag_name, 0)
            # Add score
            df.loc[condition, 'daily_score'] += score
            # Add tag name (This is slow in Pandas, but acceptable for strings)
            # A faster way is to join at the end, but let's try apply for now or list comprehension
            # Optimization: Use boolean masks to build a list of tags per row?
            # Actually, modifying object column in pandas is slow. 
            # Let's collect booleans first.
            return condition

        # --- Volume Tags ---
        mask_vol_3x = df['vol_ratio'] >= 2.8
        mask_vol_2x = (df['vol_ratio'] >= 2.0) & (df['vol_ratio'] < 2.8)
        
        # --- Price Tags ---
        mask_limit_up = df['pct_chg'] > 0.095
        
        # --- Pattern Tags ---
        # Bullish Engulfing: Yesterday Open > Close (Green/Down), Today Close > Open (Red/Up), 
        # Today Open < Yesterday Close, Today Close > Yesterday Open
        # Note: A-share colors: Red=Up, Green=Down. 
        # Logic: Yesterday Black (Close < Open), Today Red (Close > Open).
        # Body covers yesterday.
        df['open_prev'] = df['open'].shift(1)
        df['high_prev'] = df['high'].shift(1)
        df['low_prev'] = df['low'].shift(1)
        
        mask_bullish_engulfing = (
            (df['close_prev'] < df['open_prev']) & # Yesterday down
            (df['close'] > df['open']) &           # Today up
            (df['open'] < df['close_prev']) &      # Open lower than yest close
            (df['close'] > df['open_prev'])        # Close higher than yest open
        )
        
        # Bottom Fractal (底分型): Low of yesterday is lowest among prev, yesterday, today
        df['low_prev_2'] = df['low'].shift(2)
        mask_bottom_fractal = (
            (df['low_prev'] < df['low_prev_2']) &
            (df['low_prev'] < df['low'])
        )
        # Note: Fractal is usually confirmed on the 3rd candle (today). 
        # The pattern occurred "yesterday" but is confirmed "today".
        # If we tag "today", it means "Bottom Fractal Confirmed".
        
        # EXPMA Support
        mask_expma_up = df['close'] > df['expma13']
        
        # Ground Volume
        mask_land_vol_60 = (df['vol'] < df['min_vol_60']) & (df['vol'] > 0)
        # If 60 triggered, usually don't trigger 30.
        mask_land_vol_30 = (df['vol'] < df['min_vol_30']) & (df['vol'] > 0) & (~mask_land_vol_60)
        
        # --- Apply Scores & Tags ---
        # We can iterate and append
        tag_masks = [
            ('3倍量', mask_vol_3x),
            ('2倍量', mask_vol_2x),
            ('涨停', mask_limit_up),
            ('阳包阴', mask_bullish_engulfing),
            ('底分型', mask_bottom_fractal),
            ('EXPMA13上方', mask_expma_up),
            ('60日地量', mask_land_vol_60),
            ('30日地量', mask_land_vol_30)
        ]
        
        # Apply Scores
        for name, mask in tag_masks:
            score = self.tag_scores_map.get(name, 0)
            df.loc[mask, 'daily_score'] += score
            
        # Apply Tags (String Construction)
        # Vectorized string concatenation
        df['tags_str'] = 'basic_info' # Start with basic
        
        for name, mask in tag_masks:
            # If mask is true, append ",name"
            # np.where(mask, ',name', '')
            df['tags_str'] += np.where(mask, f',{name}', '')
            
        # 3. Rolling Cumulative Score (250 days)
        # Sum of 'daily_score' over last 250 rows
        df['total_score'] = df['daily_score'].rolling(window=250, min_periods=1).sum()
        
        return df[['trade_date', 'close', 'vol', 'daily_score', 'total_score', 'tags_str']]

