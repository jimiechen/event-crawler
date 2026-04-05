#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从通达信获取0326股票最新数据并更新多维表格
"""

import sys
import os
import time
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

from loguru import logger


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("📊 从通达信获取0326股票最新数据")
    logger.info("=" * 60)
    
    # 初始化通达信
    from tqcenter import tq
    logger.info("[初始化] 连接通达信...")
    tq.initialize(__file__)
    logger.info("✅ 通达信连接成功")
    
    # 0326选股的9只股票
    stocks_0326 = [
        {"code": "002361", "name": "神剑股份", "exchange": "SZ"},
        {"code": "002902", "name": "铭普光磁", "exchange": "SZ"},
        {"code": "605555", "name": "德昌股份", "exchange": "SH"},
        {"code": "000965", "name": "天保基建", "exchange": "SZ"},
        {"code": "000722", "name": "湖南发展", "exchange": "SZ"},
        {"code": "001367", "name": "海森药业", "exchange": "SZ"},
        {"code": "603601", "name": "再升科技", "exchange": "SH"},
        {"code": "002705", "name": "新宝股份", "exchange": "SZ"},
        {"code": "000927", "name": "中国铁物", "exchange": "SZ"},
    ]
    
    today = date(2026, 4, 3)
    date_timestamp = int(time.mktime(today.timetuple())) * 1000
    
    logger.info(f"\n📅 获取日期: {today}")
    logger.info(f"📈 股票数量: {len(stocks_0326)}")
    
    # 获取股票数据
    stock_list = [f"{s['code']}.{s['exchange']}" for s in stocks_0326]
    
    logger.info(f"\n🔍 从通达信获取数据...")
    try:
        # 获取日线数据
        df = tq.get_market_data(
            field_list=['Open', 'High', 'Low', 'Close', 'Volume', 'Amount'],
            stock_list=stock_list,
            period='1d',
            count=1,
            dividend_type='front',
            fill_data=True
        )
        
        logger.info(f"✅ 获取到数据")
        
        # 准备更新记录
        records = []
        for stock in stocks_0326:
            code = stock['code']
            name = stock['name']
            
            try:
                # 从DataFrame获取数据
                stock_code_full = f"{code}.{stock['exchange']}"
                
                # 通达信返回的数据格式: df[field][stock_code][date]
                open_price = float(df['Open'].loc[stock_code_full].iloc[-1])
                high_price = float(df['High'].loc[stock_code_full].iloc[-1])
                low_price = float(df['Low'].loc[stock_code_full].iloc[-1])
                close_price = float(df['Close'].loc[stock_code_full].iloc[-1])
                volume = float(df['Volume'].loc[stock_code_full].iloc[-1])
                amount = float(df['Amount'].loc[stock_code_full].iloc[-1])
                
                logger.info(f"\n📈 {code} {name}")
                logger.info(f"   开盘: {open_price}")
                logger.info(f"   收盘: {close_price}")
                logger.info(f"   最高: {high_price}")
                logger.info(f"   最低: {low_price}")
                logger.info(f"   成交量: {volume}")
                logger.info(f"   成交额: {amount}")
                
                # 构建记录
                record = {
                    "股票代码": code,
                    "股票名称": name,
                    "最新日期": "2026-04-02",
                    "最新收盘价": close_price,
                    "最新成交量": volume,
                    "备注": f"更新于0402, 开盘:{open_price}, 最高:{high_price}, 最低:{low_price}, 成交额:{amount}"
                }
                records.append(record)
                
            except Exception as e:
                logger.error(f"   ❌ 获取数据失败: {e}")
        
        # 更新飞书表格
        if records:
            logger.info(f"\n📤 更新 {len(records)} 只股票到飞书表格...")
            
            from app.services.feishu_client import FeishuClient
            feishu_client = FeishuClient()
            
            result = feishu_client.add_records_to_bitable(records)
            logger.info(f"📊 更新结果: {result}")
        
    except Exception as e:
        logger.error(f"❌ 获取数据异常: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ 操作完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
