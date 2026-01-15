#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Realhead 爬虫字段映射
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.crawler.realhead_crawler import RealheadCrawler

# 测试数据
test_data = {
    "unknown_items": {
        "10": "10.33",
        "7": "10.24",
        "8": "10.34",
        "9": "10.22",
        "6": "10.22",
        "13": "8938300.00",
        "19": "92204113.00",
        "1968584": "0.788",
        "5": "000795",
        "name": "英洛华",
        "199112": "1.08"
    }
}

# 创建爬虫实例
crawler = RealheadCrawler(None)

# 测试字段转换
print("=== 原始数据 ===")
print(test_data)

print("\n=== 转换后数据 ===")
converted = crawler.convert_fields(test_data)
print(converted)

print("\n=== 字段映射 ===")
print(f"stock_code: {converted.get('stock_code')}")
print(f"stock_name: {converted.get('stock_name')}")
print(f"current_price: {converted.get('current_price')}")
print(f"open_price: {converted.get('open_price')}")
print(f"high_price: {converted.get('high_price')}")
print(f"low_price: {converted.get('low_price')}")
print(f"prev_close: {converted.get('prev_close')}")
print(f"volume: {converted.get('volume')}")
print(f"turnover: {converted.get('turnover')}")
print(f"turnover_rate: {converted.get('turnover_rate')}")
print(f"change_percent: {converted.get('change_percent')}")
