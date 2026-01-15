"""
A-Share Signal Definitions
Mapping common A-Share technical signals to Arena signal definitions.
"""

ASHARE_SIGNALS = [
    {
        "signal_name": "3倍量",
        "description": "当日成交量是昨日的 3 倍以上，显示资金强势介入",
        "trigger_condition": "volume > prev_volume * 3",
        "enabled": True
    },
    {
        "signal_name": "60日地量",
        "description": "过去 60 个交易日内的最低成交量，通常意味着抛压衰竭",
        "trigger_condition": "volume == min(volume_60d)",
        "enabled": True
    },
    {
        "signal_name": "价格双重突破",
        "description": "收盘价同时突破近期关键压力位（如20日均线和前高）",
        "trigger_condition": "close > resistance_1 AND close > resistance_2",
        "enabled": True
    },
    {
        "signal_name": "平台突破",
        "description": "突破长期横盘整理平台，开启上涨空间",
        "trigger_condition": "close > platform_high",
        "enabled": True
    },
    {
        "signal_name": "底分型",
        "description": "缠论底分型形态，潜在的底部反转信号",
        "trigger_condition": "pattern == 'bottom_fractal'",
        "enabled": True
    },
    {
        "signal_name": "阳包阴",
        "description": "阳线实体完全包裹昨日阴线，强势反转信号",
        "trigger_condition": "pattern == 'bullish_engulfing'",
        "enabled": True
    },
    {
        "signal_name": "放量上涨",
        "description": "价格上涨配合成交量放大，量价配合理想",
        "trigger_condition": "close > prev_close AND volume > ma_volume_5",
        "enabled": True
    },
    {
        "signal_name": "缩量回调",
        "description": "价格回调但成交量萎缩，主力未出逃",
        "trigger_condition": "close < prev_close AND volume < prev_volume",
        "enabled": True
    }
]
