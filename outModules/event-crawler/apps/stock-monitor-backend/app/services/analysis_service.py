from typing import List, Dict
import pandas as pd


def analyze_volume_price_relationship(
    daily: List[Dict],
    window_size: int = 60
) -> List[Dict]:
    if not daily:
        return []
    df = pd.DataFrame(daily)
    df['close_prev'] = df['close'].shift(1)
    df['price_change_pct'] = (df['close'] - df['close_prev']) / df['close_prev'] * 100
    df['volume_prev'] = df['volume'].shift(1)
    df['volume_change_pct'] = (df['volume'] - df['volume_prev']) / df['volume_prev'] * 100
    df['vol_ma5'] = df['volume'].rolling(5, min_periods=1).mean()
    df['vol_ma10'] = df['volume'].rolling(10, min_periods=1).mean()
    def _pos(i):
        start = max(0, i - window_size + 1)
        win = df.iloc[start:i+1]
        c = df.iloc[i]['close']
        mn = win['close'].min()
        mx = win['close'].max()
        if mx == mn:
            return '中位'
        ratio = (c - mn) / (mx - mn)
        if ratio >= 0.66:
            return '高位'
        if ratio <= 0.33:
            return '低位'
        return '中位'
    df['position_label'] = [
        _pos(i) for i in range(len(df))
    ]
    def _vol_status(i):
        v = df.iloc[i]['volume']
        ma = df.iloc[i]['vol_ma5']
        if pd.isna(v) or pd.isna(ma):
            return '平量'
        if v >= ma * 1.2:
            return '放量'
        if v <= ma * 0.8:
            return '缩量'
        return '平量'
    df['volume_status'] = [
        _vol_status(i) for i in range(len(df))
    ]
    def _price_status(i):
        pct = df.iloc[i]['price_change_pct']
        if pd.isna(pct) or abs(pct) < 0.1:
            return '平盘'
        return '上涨' if pct > 0 else '下跌'
    df['price_status'] = [
        _price_status(i) for i in range(len(df))
    ]
    def _pattern(i):
        return f"{df.iloc[i]['volume_status']}{df.iloc[i]['price_status']}"
    df['volume_price_pattern'] = [
        _pattern(i) for i in range(len(df))
    ]
    def _hint(i):
        pos = df.iloc[i]['position_label']
        pat = df.iloc[i]['volume_price_pattern']
        if pos == '高位' and pat == '放量上涨':
            return '减仓/观望'
        if pos == '低位' and pat == '放量上涨':
            return '跟进?'
        if pat == '放量上涨':
            return '加仓'
        if pos == '高位' and pat == '放量下跌':
            return '卖出'
        if pat == '放量下跌':
            return '卖出'
        if pat == '缩量上涨':
            return '持有/谨慎'
        if pat == '缩量下跌':
            return '等待'
        return '观望'
    df['vp_action_hint'] = [
        _hint(i) for i in range(len(df))
    ]
    out: List[Dict] = []
    for _, row in df.iterrows():
        out.append({
            'trade_date': row['trade_date'],
            'open': row.get('open'),
            'high': row.get('high'),
            'low': row.get('low'),
            'close': row.get('close'),
            'volume': row.get('volume'),
            'amount': row.get('amount'),
            'price_change_pct': float(row['price_change_pct']) if pd.notna(row['price_change_pct']) else None,
            'volume_change_pct': float(row['volume_change_pct']) if pd.notna(row['volume_change_pct']) else None,
            'vol_ma5': float(row['vol_ma5']) if pd.notna(row['vol_ma5']) else None,
            'vol_ma10': float(row['vol_ma10']) if pd.notna(row['vol_ma10']) else None,
            'position_label': row['position_label'],
            'volume_status': row['volume_status'],
            'price_status': row['price_status'],
            'volume_price_pattern': row['volume_price_pattern'],
            'vp_action_hint': row['vp_action_hint'],
        })
    return out


def calculate_morphology(daily: List[Dict], window_size: int = 60) -> List[Dict]:
    if not daily:
        return []
    df = pd.DataFrame(daily)
    df['body'] = (df['close'] - df['open']).abs()
    df['range'] = (df['high'] - df['low']).abs()
    df['body_pct'] = (df['body'] / df['range']).fillna(0) * 100
    df['upper_shadow_pct'] = ((df['high'] - df[['open','close']].max(axis=1)) / df['range']).fillna(0) * 100
    df['lower_shadow_pct'] = ((df[['open','close']].min(axis=1) - df['low']) / df['range']).fillna(0) * 100
    def _pos(i):
        start = max(0, i - window_size + 1)
        win = df.iloc[start:i+1]
        c = df.iloc[i]['close']
        mn = win['close'].min()
        mx = win['close'].max()
        if mx == mn:
            return '中位'
        r = (c - mn) / (mx - mn)
        if r >= 0.66:
            return '高位'
        if r <= 0.33:
            return '低位'
        return '中位'
    df['position_label'] = [ _pos(i) for i in range(len(df)) ]
    df['close_prev'] = df['close'].shift(1)
    df['price_change_pct'] = (df['close'] - df['close_prev']) / df['close_prev'] * 100
    df['vol_ma5'] = df['volume'].rolling(5, min_periods=1).mean()
    def _vol_status(i):
        v = df.iloc[i]['volume']
        ma = df.iloc[i]['vol_ma5']
        if pd.isna(v) or pd.isna(ma):
            return '平量'
        if v >= ma * 1.2:
            return '放量'
        if v <= ma * 0.8:
            return '缩量'
        return '平量'
    df['volume_status'] = [ _vol_status(i) for i in range(len(df)) ]
    def _price_status(i):
        p = df.iloc[i]['price_change_pct']
        if pd.isna(p) or abs(p) < 0.1:
            return '平盘'
        return '上涨' if p > 0 else '下跌'
    df['price_status'] = [ _price_status(i) for i in range(len(df)) ]
    out: List[Dict] = []
    for _, row in df.iterrows():
        out.append({
            'trade_date': row['trade_date'],
            'price_change_pct': float(row['price_change_pct']) if pd.notna(row['price_change_pct']) else None,
            'body_pct': float(row['body_pct']) if pd.notna(row['body_pct']) else None,
            'upper_shadow_pct': float(row['upper_shadow_pct']) if pd.notna(row['upper_shadow_pct']) else None,
            'lower_shadow_pct': float(row['lower_shadow_pct']) if pd.notna(row['lower_shadow_pct']) else None,
            'position_label': row['position_label'],
            'volume_status': row['volume_status'],
            'price_status': row['price_status'],
        })
    return out


def find_three_day_patterns(daily: List[Dict]) -> List[Dict]:
    if not daily:
        return []
    df = pd.DataFrame(daily)
    df['close_prev'] = df['close'].shift(1)
    df['chg'] = df['close'] - df['close_prev']
    patterns: List[Dict] = []
    for i in range(2, len(df)):
        win = df.iloc[i-2:i+1]
        up_days = (win['chg'] > 0).sum()
        down_days = (win['chg'] < 0).sum()
        if down_days >= 3:
            patterns.append({'trade_date': win.iloc[-1]['trade_date'], 'description': '三日下跌', 'pattern_name': 'three_day_down'})
        elif up_days >= 3:
            patterns.append({'trade_date': win.iloc[-1]['trade_date'], 'description': '三日上涨', 'pattern_name': 'three_day_up'})
        else:
            highs = win['high']; lows = win['low']
            if highs.iloc[1] >= highs.iloc[0] and highs.iloc[1] >= highs.iloc[2]:
                patterns.append({'trade_date': win.iloc[-1]['trade_date'], 'description': '三日顶分形', 'pattern_name': 'three_day_top_fractal'})
            if lows.iloc[1] <= lows.iloc[0] and lows.iloc[1] <= lows.iloc[2]:
                patterns.append({'trade_date': win.iloc[-1]['trade_date'], 'description': '三日底分形', 'pattern_name': 'three_day_bottom_fractal'})
    return patterns


def analyze_rules(daily: List[Dict]) -> List[Dict]:
    if not daily:
        return []
    df = pd.DataFrame(daily)
    df['body'] = (df['close'] - df['open']).abs()
    df['range'] = (df['high'] - df['low']).abs()
    df['body_pct'] = (df['body'] / df['range']).fillna(0) * 100
    df['vol_ma5'] = df['volume'].rolling(5, min_periods=1).mean()
    logs: List[Dict] = []
    for i in range(len(df)):
        vol = df.iloc[i]['volume']
        ma5 = df.iloc[i]['vol_ma5']
        body_pct = df.iloc[i]['body_pct']
        cond_high_vol_small_body = (pd.notna(vol) and pd.notna(ma5) and vol >= ma5 * 1.5) and (body_pct <= 30)
        if cond_high_vol_small_body:
            logs.append({
                'trade_date': df.iloc[i]['trade_date'],
                'rule_number': 1,
                'rule_content': '量大实体小，多数有人跑',
                'vp_action_hint': '减仓/观望',
                'details': { 'body_pct': float(body_pct) if pd.notna(body_pct) else None, 'vol_ma5': float(ma5) if pd.notna(ma5) else None, 'volume': float(vol) if pd.notna(vol) else None }
            })
    return logs
