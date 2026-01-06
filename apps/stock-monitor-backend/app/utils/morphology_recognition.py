from typing import Dict, Any

def check_bullish_engulfing(k2: Dict[str, Any], k3: Dict[str, Any]) -> bool:
    """
    识别阳包阴形态 (2日)
    k2: 昨天
    k3: 今天
    条件:
    1. 昨天是阴线 (Open > Close)
    2. 今天是阳线 (Close > Open)
    3. 今天实体包裹昨天实体 (Open <= 昨天Close 且 Close >= 昨天Open)
    """
    try:
        prev_open = float(k2['open'])
        prev_close = float(k2['close'])
        curr_open = float(k3['open'])
        curr_close = float(k3['close'])
        
        is_prev_bear = prev_close < prev_open
        is_curr_bull = curr_close > curr_open
        
        # 宽松包裹：包含实体部分即可
        is_engulfing = (curr_open <= prev_close) and (curr_close >= prev_open)
        
        # 严格包裹：包含最高最低 (可选)
        # is_engulfing_strict = (curr_low <= prev_low) and (curr_high >= prev_high)
        
        return is_prev_bear and is_curr_bull and is_engulfing
    except (KeyError, ValueError):
        return False

def check_bottom_fractal(k1: Dict[str, Any], k2: Dict[str, Any], k3: Dict[str, Any]) -> bool:
    """
    识别底分型 (3日)
    k1: 前天
    k2: 昨天 (中间)
    k3: 今天
    条件:
    1. 中间K线低点最低 (Low2 < Low1 且 Low2 < Low3)
    2. 中间K线高点最低 (High2 < High1 且 High2 < High3)
    """
    try:
        l1, h1 = float(k1['low']), float(k1['high'])
        l2, h2 = float(k2['low']), float(k2['high'])
        l3, h3 = float(k3['low']), float(k3['high'])
        
        is_lowest_low = (l2 < l1) and (l2 < l3)
        is_lowest_high = (h2 < h1) and (h2 < h3)
        
        return is_lowest_low and is_lowest_high
    except (KeyError, ValueError):
        return False

def check_shooting_star(k: Dict[str, Any]) -> bool:
    """
    识别冲高回落 (1日) / 射击之星
    条件:
    1. 上影线较长 (Upper Shadow > 2 * Body)
    2. 实体较小
    3. 下影线较短
    """
    try:
        open_p = float(k['open'])
        close_p = float(k['close'])
        high_p = float(k['high'])
        low_p = float(k['low'])
        
        body = abs(close_p - open_p)
        upper_shadow = high_p - max(open_p, close_p)
        lower_shadow = min(open_p, close_p) - low_p
        
        # 避免除以零
        if body == 0:
            return upper_shadow > 0
            
        # 条件判断
        long_upper = upper_shadow > (2 * body)
        short_lower = lower_shadow < body # 下影线小于实体
        
        return long_upper and short_lower
    except (KeyError, ValueError):
        return False
