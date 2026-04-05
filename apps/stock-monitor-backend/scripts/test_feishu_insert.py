#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试飞书表格数据插入
"""

import sys
import os
import time
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🧪 测试飞书表格数据插入")
    logger.info("=" * 60)
    
    from app.services.feishu_client import FeishuClient
    
    # 初始化飞书客户端
    feishu_client = FeishuClient()
    
    # 今天的选股结果（3只）
    trade_date = date(2026, 4, 3)
    selected_stocks = [
        {
            "stock_code": "600644.SH",
            "stock_name": "乐山电力",
            "volume_ratio": 3.45,
            "change_percent": 10.01
        },
        {
            "stock_code": "603798.SH",
            "stock_name": "康普顿",
            "volume_ratio": 3.06,
            "change_percent": 10.00
        },
        {
            "stock_code": "920230.BJ",
            "stock_name": "林泰新材",
            "volume_ratio": 7.95,
            "change_percent": 29.98
        }
    ]
    
    sector_code = "3BL260402"
    
    # 构建记录
    records = []
    for s in selected_stocks:
        stock_info = f"{s.get('stock_code', '')} {s.get('stock_name', '')} 量比:{round(s.get('volume_ratio', 0), 2)} 涨幅:{round(s.get('change_percent', 0), 2)}% 板块:{sector_code} 日期:{trade_date}"
        # 日期需要转换为Unix时间戳（毫秒）
        date_timestamp = int(time.mktime(trade_date.timetuple())) * 1000
        record = {
            "文本": stock_info,
            "日期": date_timestamp
        }
        records.append(record)
        logger.info(f"准备插入: {stock_info}")
    
    # 批量插入
    logger.info(f"\n📤 批量插入 {len(records)} 条记录...")
    result = feishu_client.add_records_to_bitable(records)
    
    logger.info(f"\n📊 插入结果: {result}")
    
    logger.info("\n" + "=" * 60)
    logger.info("🧪 测试完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
