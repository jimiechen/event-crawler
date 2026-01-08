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

def preprocess_kline_chan(k_lines: list) -> list:
    """
    缠论K线包含关系处理
    规则:
    1. 趋势判断：若 High_curr > High_prev 且 Low_curr > Low_prev -> 向上趋势 (暂时简化处理，不判断分型方向)
       或者简单使用前两根K线的方向
    
    简化版包含处理 (仅处理包含，不严格区分向上/向下趋势，默认向上或向下合并):
    - 包含定义: (High_curr <= High_prev and Low_curr >= Low_prev) 或 (High_curr >= High_prev and Low_curr <= Low_prev)
    - 这里的定义是：后一根在前一根范围内，或者前一根在后一根范围内（非标准定义，标准是后包前或前包后）
    - 标准缠论包含: 
        如果是相邻两根K线，gk和gk+1
        凡是 High_k+1 >= High_k 且 Low_k+1 <= Low_k (反了？)
        
        正确定义:
        包含关系指两根K线的高低点关系。
        若 High_k+1 <= High_k 且 Low_k+1 >= Low_k，则 k+1 包含在 k 中。
        若 High_k+1 >= High_k 且 Low_k+1 <= Low_k，则 k 包含在 k+1 中（这种情况通常不处理，因为是后包前？不对，缠论只处理后一根在范围内的）。
        
        修正：缠论只处理“当前根被前一根包含”的情况？
        不，是两根K线存在包含关系。
        
        我们采用标准处理：
        1. 从左向右处理
        2. 若第 i 根和第 i+1 根存在包含关系（一根的高低点完全在另一根范围内）
        3. 需要根据“趋势”决定合并方式：
           - 向上趋势：High = max(H1, H2), Low = max(L1, L2)
           - 向下趋势：High = min(H1, H2), Low = min(L1, L2)
           
    为简化实现，我们这里暂时假设：
    - 如果第一根K线是阳线，假设向上趋势
    - 如果第一根K线是阴线，假设向下趋势
    """
    if len(k_lines) < 2:
        return k_lines
        
    result = [k_lines[0]]
    
    for i in range(1, len(k_lines)):
        curr = k_lines[i]
        prev = result[-1]
        
        h_curr, l_curr = float(curr['high']), float(curr['low'])
        h_prev, l_prev = float(prev['high']), float(prev['low'])
        
        # 检查包含关系
        is_curr_inside_prev = (h_curr <= h_prev) and (l_curr >= l_prev)
        is_prev_inside_curr = (h_curr >= h_prev) and (l_curr <= l_prev)
        
        if is_curr_inside_prev or is_prev_inside_curr:
            # 存在包含，进行合并
            # 简单策略：根据前一根的颜色判断趋势 (这是一个启发式近似，非严格缠论)
            # 严格缠论需要看分型，这里简化
            prev_open = float(prev['open'])
            prev_close = float(prev['close'])
            is_up = prev_close >= prev_open
            
            new_k = curr.copy()
            if is_up:
                # 向上: 取高高，低高
                new_k['high'] = max(h_curr, h_prev)
                new_k['low'] = max(l_curr, l_prev)
            else:
                # 向下: 取高低，低低
                new_k['high'] = min(h_curr, h_prev)
                new_k['low'] = min(l_curr, l_prev)
            
            # 更新当前K线为合并后的K线，并替换结果列表中的最后一个
            # 注意：如果前一个是被合并的，应该替换前一个？
            # 缠论是合并后作为新的第i根，去和第i+2根比较
            # 所以这里应该替换 result[-1]
            result[-1] = new_k
        else:
            result.append(curr)
            
    return result
