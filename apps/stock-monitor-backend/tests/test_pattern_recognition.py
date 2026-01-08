import pytest
import pandas as pd
from app.utils.morphology_recognition import check_bullish_engulfing, check_bottom_fractal, preprocess_kline_chan
from app.utils.technical_indicators import calculate_expma
from tests.mock_data import MockDataGenerator

class TestPatternRecognition:
    
    def test_bullish_engulfing(self):
        """测试阳包阴识别"""
        data = MockDataGenerator.get_bullish_engulfing_data()
        
        # 模拟 Day 1 和 Day 2
        k1 = data[0]
        k2 = data[1]
        
        is_pattern = check_bullish_engulfing(k1, k2)
        assert is_pattern is True, "应当识别为阳包阴"
        
        # 反例测试
        k2_fake = k2.copy()
        k2_fake['open'] = 9.6 # 高于 k1.close(9.5)，未包住
        is_pattern = check_bullish_engulfing(k1, k2_fake)
        assert is_pattern is False, "不应识别为阳包阴"

    def test_bottom_fractal(self):
        """测试底分型识别"""
        data = MockDataGenerator.get_bottom_fractal_data()
        k1, k2, k3 = data[0], data[1], data[2]
        
        is_fractal = check_bottom_fractal(k1, k2, k3)
        assert is_fractal is True, "应当识别为底分型"
        
        # 反例
        k2_fake = k2.copy()
        k2_fake['low'] = 10.1 # 高于 k1.low(10.0)
        is_fractal = check_bottom_fractal(k1, k2_fake, k3)
        assert is_fractal is False, "不应识别为底分型"

    def test_chan_inclusion_processing(self):
        """测试缠论包含关系处理"""
        # 暂未实现包含处理函数，待补充
        pass

class TestTechnicalIndicators:
    
    def test_expma_calculation(self):
        """测试EXPMA计算准确性"""
        df = MockDataGenerator.get_expma_data(20)
        # 计算 EXPMA 13
        expma_series = calculate_expma(df['close'], 13)
        
        assert len(expma_series) == 20
        assert expma_series.iloc[-1] > expma_series.iloc[0], "上升趋势中EXPMA应上升"
