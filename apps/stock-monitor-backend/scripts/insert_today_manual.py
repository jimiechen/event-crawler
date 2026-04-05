#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动插入今天选股数据到飞书表格
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("📊 手动插入今天(0402)选股数据到飞书表格")
    logger.info("=" * 60)
    
    from app.services.feishu_client import FeishuClient
    
    # 初始化飞书客户端
    feishu_client = FeishuClient()
    
    # 今天日期
    trade_date = "2026-04-02"
    date_timestamp = int(time.mktime(time.strptime(trade_date, "%Y-%m-%d"))) * 1000
    
    # 今天的3只选股结果
    records = [
        {
            "股票代码": "600644",
            "股票名称": "乐山电力",
            "入池日期": date_timestamp,
            "入池开盘价": 6.35,
            "入池收盘价": 6.81,
            "入池最高价": 6.81,
            "成交量": 34128488.0,
            "3倍量确认": True,
            "5日地量": False,
            "10日地量": False,
            "20日地量": False,
            "30日地量": False,
            "60日地量": False,
            "备注": "量比: 3.45, 涨幅: 10.01%, 板块: 3BL260402"
        },
        {
            "股票代码": "603798",
            "股票名称": "康普顿",
            "入池日期": date_timestamp,
            "入池开盘价": 9.70,
            "入池收盘价": 10.23,
            "入池最高价": 10.23,
            "成交量": 7374984.0,
            "3倍量确认": True,
            "5日地量": False,
            "10日地量": False,
            "20日地量": False,
            "30日地量": False,
            "60日地量": False,
            "备注": "量比: 3.06, 涨幅: 10.00%, 板块: 3BL260402"
        },
        {
            "股票代码": "920230",
            "股票名称": "林泰新材",
            "入池日期": date_timestamp,
            "入池开盘价": 52.00,
            "入池收盘价": 60.50,
            "入池最高价": 60.50,
            "成交量": 1124900.0,
            "3倍量确认": True,
            "5日地量": False,
            "10日地量": False,
            "20日地量": False,
            "30日地量": False,
            "60日地量": False,
            "备注": "量比: 7.95, 涨幅: 29.98%, 板块: 3BL260402"
        }
    ]
    
    logger.info(f"准备插入 {len(records)} 条记录...")
    for i, r in enumerate(records, 1):
        logger.info(f"{i}. {r['股票代码']} {r['股票名称']} 收盘价:{r['入池收盘价']}")
    
    # 批量插入
    result = feishu_client.add_records_to_bitable(records)
    
    logger.info(f"\n📊 插入结果: {result}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ 操作完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
