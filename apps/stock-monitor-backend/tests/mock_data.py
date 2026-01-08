from datetime import datetime, timedelta
import pandas as pd
import numpy as np

class MockDataGenerator:
    """生成用于测试形态识别的Mock数据"""

    @staticmethod
    def create_kline(open_price, close_price, high, low, vol, date_str):
        return {
            "date": date_str,
            "open": float(open_price),
            "close": float(close_price),
            "high": float(high),
            "low": float(low),
            "volume": float(vol)
        }

    @staticmethod
    def get_bullish_engulfing_data():
        """
        生成阳包阴形态数据
        Day 1: 阴线 (Open 10.0, Close 9.5)
        Day 2: 阳线 (Open 9.4, Close 10.1) -> 完全包住Day 1实体
        """
        return [
            MockDataGenerator.create_kline(10.0, 9.5, 10.2, 9.4, 10000, "2026-01-01"),
            MockDataGenerator.create_kline(9.4, 10.1, 10.3, 9.3, 20000, "2026-01-02")
        ]

    @staticmethod
    def get_bottom_fractal_data():
        """
        生成底分型数据 (标准无包含)
        Day 1: Low 10.0, High 11.2
        Day 2: Low 9.0 (最低), High 10.0 (最低)
        Day 3: Low 9.5, High 10.8
        """
        return [
            MockDataGenerator.create_kline(11.0, 10.5, 11.2, 10.0, 10000, "2026-01-01"),
            MockDataGenerator.create_kline(10.5, 9.5, 10.0, 9.0, 15000, "2026-01-02"),
            MockDataGenerator.create_kline(9.6, 10.2, 10.8, 9.5, 20000, "2026-01-03")
        ]

    @staticmethod
    def get_inclusion_data():
        """
        生成包含关系数据 (向下的包含)
        Day 1: High 10.0, Low 9.0
        Day 2: High 9.8, Low 9.2 (被Day 1包含)
        处理后应合并为: High 9.8, Low 9.0 (向下取低低)
        """
        return [
            MockDataGenerator.create_kline(9.5, 9.2, 10.0, 9.0, 10000, "2026-01-01"),
            MockDataGenerator.create_kline(9.3, 9.6, 9.8, 9.2, 12000, "2026-01-02")
        ]
    
    @staticmethod
    def get_expma_data(length=20):
        """生成用于计算EXPMA的数据序列"""
        dates = [
            (datetime(2026, 1, 1) + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(length)
        ]
        # 构造一个上升趋势
        prices = [10.0 + i * 0.5 for i in range(length)]
        return pd.DataFrame({
            "date": dates,
            "close": prices
        })
