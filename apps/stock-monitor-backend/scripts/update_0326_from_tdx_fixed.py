#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从通达信获取0326股票最新数据并更新多维表格（修复版）
"""

import sys
import os
import time
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

from loguru import logger


def get_stock_data_from_tdx(tdx_client, stock_code_full, target_date):
    """
    从通达信获取单只股票数据（修复版）
    
    Args:
        tdx_client: 通达信客户端
        stock_code_full: 完整股票代码（如 002361.SZ）
        target_date: 目标日期
        
    Returns:
        dict: 股票数据
    """
    try:
        # 获取日线数据 - 返回的是dict，每个字段对应一个DataFrame
        data_dict = tdx_client.get_market_data(
            field_list=['Open', 'High', 'Low', 'Close', 'Volume', 'Amount'],
            stock_list=[stock_code_full],
            period='1d',
            count=1,
            dividend_type='front',
            fill_data=True
        )
        
        # 调试信息
        logger.debug(f"数据类型: {type(data_dict)}")
        logger.debug(f"数据键: {data_dict.keys() if isinstance(data_dict, dict) else 'N/A'}")
        
        # 获取Close数据的DataFrame
        close_df = data_dict.get('Close')
        if close_df is None or close_df.empty:
            logger.warning(f"未找到Close数据")
            return None
        
        logger.debug(f"close_df类型: {type(close_df)}")
        logger.debug(f"close_df形状: {close_df.shape}")
        logger.debug(f"close_df列: {close_df.columns.tolist()}")
        logger.debug(f"close_df索引: {close_df.index.tolist()}")
        
        # 通达信返回的DataFrame: index是日期，columns是股票代码
        # 例如: close_df.loc['2026-03-20', '000001.SZ'] = 10.77
        
        if stock_code_full not in close_df.columns:
            logger.warning(f"股票 {stock_code_full} 不在返回数据中")
            return None
        
        # 获取最新日期 (index)
        latest_date_idx = close_df.index[-1]
        logger.debug(f"最新日期索引: {latest_date_idx}")
        
        # 从各个字段的DataFrame中获取数据
        close_val = close_df.loc[latest_date_idx, stock_code_full]
        
        open_df = data_dict.get('Open')
        high_df = data_dict.get('High')
        low_df = data_dict.get('Low')
        volume_df = data_dict.get('Volume')
        amount_df = data_dict.get('Amount')
        
        open_val = open_df.loc[latest_date_idx, stock_code_full] if open_df is not None else None
        high_val = high_df.loc[latest_date_idx, stock_code_full] if high_df is not None else None
        low_val = low_df.loc[latest_date_idx, stock_code_full] if low_df is not None else None
        volume = volume_df.loc[latest_date_idx, stock_code_full] if volume_df is not None else None
        amount = amount_df.loc[latest_date_idx, stock_code_full] if amount_df is not None else None
        
        # 单位转换:
        # - 成交量: 通达信(股) → 手, 除以100
        # - 成交额: 通达信(元) → 千元, 除以1000
        if volume is not None:
            volume = float(volume) / 100  # 股 → 手
        
        if amount is not None:
            amount = float(amount) / 1000  # 元 → 千元
        
        return {
            'open': float(open_val) if open_val is not None else 0,
            'high': float(high_val) if high_val is not None else 0,
            'low': float(low_val) if low_val is not None else 0,
            'close': float(close_val) if close_val is not None else 0,
            'volume': volume if volume is not None else 0,
            'amount': amount if amount is not None else 0,
            'date': latest_date_idx
        }
        
    except Exception as e:
        logger.error(f"获取 {stock_code_full} 数据失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("📊 从通达信获取0326股票最新数据（修复版）")
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
    
    logger.info(f"\n📅 获取日期: {today}")
    logger.info(f"📈 股票数量: {len(stocks_0326)}")
    
    # 准备更新记录
    records = []
    
    for stock in stocks_0326:
        code = stock['code']
        name = stock['name']
        stock_code_full = f"{code}.{stock['exchange']}"
        
        logger.info(f"\n📈 获取 {code} {name}...")
        
        # 从通达信获取数据
        data = get_stock_data_from_tdx(tq, stock_code_full, today)
        
        if data:
            logger.info(f"   开盘: {data['open']}")
            logger.info(f"   收盘: {data['close']}")
            logger.info(f"   最高: {data['high']}")
            logger.info(f"   最低: {data['low']}")
            logger.info(f"   成交量: {data['volume']}")
            logger.info(f"   成交额: {data['amount']}")
            
            # 构建记录
            record = {
                "股票代码": code,
                "股票名称": name,
                "最新日期": "2026-04-02",
                "最新收盘价": data['close'],
                "最新成交量": data['volume'],
                "备注": f"更新于0402, 开盘:{data['open']}, 最高:{data['high']}, 最低:{data['low']}, 成交额:{data['amount']}"
            }
            records.append(record)
        else:
            logger.warning(f"   ⚠️ 未获取到数据")
    
    # 更新飞书表格
    if records:
        logger.info(f"\n📤 更新 {len(records)} 只股票到飞书表格...")
        
        from app.services.feishu_client import FeishuClient
        feishu_client = FeishuClient()
        
        result = feishu_client.add_records_to_bitable(records)
        logger.info(f"📊 更新结果: {result}")
    else:
        logger.warning("⚠️ 没有记录需要更新")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ 操作完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
