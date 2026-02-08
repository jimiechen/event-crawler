#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI分析提示词模板
用于股票截图识别
"""

# 天龙博弈日K线图提示词
SANLONG_KLINE_PROMPT = """
请详细分析这张约牛天龙博弈的日K线截图，提取以下信息：

## 1. 基础股票信息
- 股票代码和名称（右上角）
- 当前价格
- 涨跌幅(%)
- 所属行业/板块

## 2. 三龙聚首指标（重点）
查看截图下方的"三龙聚首"区域，有4个警戒灯：
- 趋势警戒: 0或1（红色为1，灰色/绿色为0）
- 量能警戒: 0或1
- 中期警戒: 0或1
- 短期警戒: 0或1
- 亮灯总数: 0-4
- 是否全红警戒: true/false

## 3. K/D信号识别（重点）
查看K线图上的信号标记：
- K信号: 蓝色"K"字母图标
- D信号: 黄色小房子图标
统计：
- 今天（最右侧K线）是否有K信号？true/false
- 今天（最右侧K线）是否有D信号？true/false
- 整个图表中K信号的总数量
- 整个图表中D信号的总数量

## 4. 价格和成交量
- 当前价格
- 涨跌幅(%)
- 成交量(VOL数值)
- MAVOL1和MAVOL2数值

## 5. 形态识别
- 是否识别到"天龙博弈"或"天量博弈"形态
- 当前趋势描述

请以JSON格式返回：
{
    "stock_code": "股票代码如002165",
    "stock_name": "股票名称如红宝丽",
    "industry": "所属行业如化学制品",
    "price": 14.36,
    "change_percent": 4.82,
    "volume": 2073900,
    
    "sanlong": {
        "trend_alert": 1,
        "volume_alert": 1,
        "mid_alert": 1,
        "short_alert": 1,
        "alert_count": 4,
        "all_red": true
    },
    
    "kd_signals": {
        "has_k_signal_today": false,
        "has_d_signal_today": false,
        "k_signal_count": 3,
        "d_signal_count": 4
    },
    
    "pattern": "天龙博弈",
    "pattern_confidence": 0.92,
    "analysis_text": "详细分析描述"
}
"""

# 分时图提示词
FENXI_PROMPT = """
请分析这张股票分时图截图，提取以下信息：

## 1. 基础信息
- 股票代码和名称
- 当前价格
- 涨跌幅(%)

## 2. 主力控盘数据（重点）
查看顶部的控盘数据：
- 主力买入占比(%)
- 主力卖出占比(%)
- 散户买入占比(%)
- 散户卖出占比(%)

## 3. 分时特征
- 早盘/午盘/尾盘的主力买卖信号
- 价格与均价的关系
- 成交量分布特征

请以JSON格式返回：
{
    "stock_code": "股票代码",
    "stock_name": "股票名称",
    "price": 当前价格,
    "change_percent": 涨跌幅,
    
    "main_force": {
        "main_force_buy_ratio": 63.32,
        "main_force_sell_ratio": 36.68,
        "retail_buy_ratio": 0.00,
        "retail_sell_ratio": 0.00
    },
    
    "analysis_text": "分时图分析描述"
}
"""

# 普通K线图提示词
KLINE_PROMPT = """
请分析这张股票K线图截图，提取以下信息：
- 股票代码和名称
- 当前价格
- 涨跌幅
- 成交量
- K线形态特征
- 技术指标信号

请以JSON格式返回相关数据。
"""


def get_prompt(screenshot_type: str) -> str:
    """根据截图类型获取提示词"""
    prompts = {
        "tlby": SANLONG_KLINE_PROMPT,
        "sanlong": SANLONG_KLINE_PROMPT,
        "fenxi": FENXI_PROMPT,
        "kline": KLINE_PROMPT
    }
    return prompts.get(screenshot_type, SANLONG_KLINE_PROMPT)
