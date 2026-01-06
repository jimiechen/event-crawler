import pandas as pd
import numpy as np

def calculate_expma(series: pd.Series, span: int = 13) -> pd.Series:
    """
    计算 EXPMA (Exponential Moving Average)
    :param series: 价格序列 (pd.Series)
    :param span: 周期 (默认13)
    :return: EXPMA 序列
    """
    return series.ewm(span=span, adjust=False).mean()

def calculate_ma(series: pd.Series, window: int = 5) -> pd.Series:
    """
    计算 MA (Simple Moving Average)
    """
    return series.rolling(window=window).mean()

def calculate_volume_ratio(vol_series: pd.Series, window: int = 5) -> pd.Series:
    """
    计算量比 (当前量 / 过去N日均量)
    """
    ma_vol = vol_series.rolling(window=window).mean().shift(1) # 昨天的5日均量
    return vol_series / ma_vol
