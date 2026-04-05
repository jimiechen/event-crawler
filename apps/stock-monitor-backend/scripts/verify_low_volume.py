#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校验地量判断是否正确
随机选取标记为5日地量、10日地量的股票进行验证
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

import requests
import pandas as pd
from datetime import date
from loguru import logger
from app.services.feishu_client import FeishuClient


def get_random_low_volume_stocks():
    """从飞书表格获取标记为5日地量或10日地量的股票"""
    feishu_client = FeishuClient()
    
    access_token = feishu_client._get_access_token()
    if not access_token:
        logger.error("❌ 无法获取访问令牌")
        return []
    
    # 查询标记为5日地量或10日地量的股票
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{feishu_client.app_token}/tables/{feishu_client.table_id}/records/search"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 构建过滤条件：5日地量 = true OR 10日地量 = true
    filter_data = {
        "conjunction": "or",
        "conditions": [
            {
                "field_name": "5日地量",
                "operator": "is",
                "value": ["true"]
            },
            {
                "field_name": "10日地量",
                "operator": "is",
                "value": ["true"]
            }
        ]
    }
    
    data = {
        "page_size": 20,
        "filter": filter_data
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        result = response.json()
        
        if result.get("code") == 0:
            records = result.get("data", {}).get("items", [])
            logger.info(f"✅ 找到 {len(records)} 只标记为地量的股票")
            return records
        else:
            logger.error(f"❌ 查询失败: {result}")
            return []
            
    except Exception as e:
        logger.error(f"❌ 查询异常: {e}")
        return []


def parse_stock_info(record):
    """解析股票信息"""
    fields = record.get("fields", {})
    
    stock_code_field = fields.get("股票代码", "")
    if isinstance(stock_code_field, list) and len(stock_code_field) > 0:
        stock_code = stock_code_field[0].get("text", "") if isinstance(stock_code_field[0], dict) else str(stock_code_field[0])
    else:
        stock_code = str(stock_code_field) if stock_code_field else ""
    
    stock_name_field = fields.get("股票名称", "")
    if isinstance(stock_name_field, list) and len(stock_name_field) > 0:
        stock_name = stock_name_field[0].get("text", "") if isinstance(stock_name_field[0], dict) else str(stock_name_field[0])
    else:
        stock_name = str(stock_name_field) if stock_name_field else ""
    
    low_5d = fields.get("5日地量", False)
    low_10d = fields.get("10日地量", False)
    low_20d = fields.get("20日地量", False)
    
    return {
        "code": stock_code,
        "name": stock_name,
        "low_5d": bool(low_5d) if low_5d else False,
        "low_10d": bool(low_10d) if low_10d else False,
        "low_20d": bool(low_20d) if low_20d else False,
    }


def verify_low_volume_calculation(stock_code, stock_name):
    """
    从通达信获取数据，重新计算地量判断
    """
    from tqcenter import tq
    
    # 初始化通达信
    tq.initialize(__file__)
    
    # 转换股票代码格式
    if stock_code.startswith('6'):
        stock_code_full = f"{stock_code}.SH"
    else:
        stock_code_full = f"{stock_code}.SZ"
    
    logger.info(f"\n📊 校验股票: {stock_code} {stock_name}")
    logger.info(f"  通达信代码: {stock_code_full}")
    
    # 获取15天数据（用于计算5日和10日地量）
    try:
        data_dict = tq.get_market_data(
            field_list=['Volume'],
            stock_list=[stock_code_full],
            period='1d',
            count=15,
            dividend_type='front',
            fill_data=True
        )
        
        volume_series = data_dict.get('Volume')
        if volume_series is None or volume_series.empty:
            logger.error(f"  ❌ 无法获取成交量数据")
            return None
        
        # 获取最近11天的成交量（用于计算10日地量）
        volumes = volume_series[stock_code_full].tolist()[-11:]  # 取最近11天
        
        if len(volumes) < 6:
            logger.error(f"  ❌ 数据不足，只有 {len(volumes)} 天")
            return None
        
        # 转换为手
        volumes_hand = [v / 100 for v in volumes]
        
        latest_volume = volumes_hand[-1]
        
        logger.info(f"\n  最近11天成交量（手）:")
        for i, vol in enumerate(volumes_hand):
            day_label = "今天" if i == len(volumes_hand) - 1 else f"-{len(volumes_hand)-1-i}天"
            logger.info(f"    {day_label}: {vol:.0f} 手")
        
        # 计算5日地量：当天成交量是否是5天内最低
        if len(volumes_hand) >= 5:
            recent_5_volumes = volumes_hand[-5:]  # 最近5天（含今天）
            min_5 = min(recent_5_volumes)
            is_5d_low = latest_volume <= min_5
            logger.info(f"\n  5日地量计算:")
            logger.info(f"    最近5天成交量: {[f'{v:.0f}' for v in recent_5_volumes]}")
            logger.info(f"    5天内最低: {min_5:.0f} 手")
            logger.info(f"    今天成交量: {latest_volume:.0f} 手")
            logger.info(f"    是否地量（今天是最低）: {is_5d_low}")
        else:
            is_5d_low = None
        
        # 计算10日地量：当天成交量是否是10天内最低
        if len(volumes_hand) >= 10:
            recent_10_volumes = volumes_hand[-10:]  # 最近10天（含今天）
            min_10 = min(recent_10_volumes)
            is_10d_low = latest_volume <= min_10
            logger.info(f"\n  10日地量计算:")
            logger.info(f"    最近10天成交量: {[f'{v:.0f}' for v in recent_10_volumes]}")
            logger.info(f"    10天内最低: {min_10:.0f} 手")
            logger.info(f"    今天成交量: {latest_volume:.0f} 手")
            logger.info(f"    是否地量（今天是最低）: {is_10d_low}")
        else:
            is_10d_low = None
        
        return {
            "is_5d_low": is_5d_low,
            "is_10d_low": is_10d_low,
        }
        
    except Exception as e:
        logger.error(f"  ❌ 获取数据失败: {e}")
        return None


def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("🔍 校验地量判断是否正确")
    logger.info("=" * 80)
    
    # 1. 获取标记为地量的股票
    records = get_random_low_volume_stocks()
    if not records:
        logger.warning("⚠️ 没有找到标记为地量的股票")
        return
    
    # 2. 随机选择前3只进行校验
    import random
    sample_records = records[:3]  # 取前3只
    
    logger.info(f"\n📋 将校验 {len(sample_records)} 只股票")
    
    # 3. 逐个校验
    for idx, record in enumerate(sample_records, 1):
        stock_info = parse_stock_info(record)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"📊 校验第 {idx}/{len(sample_records)} 只股票")
        logger.info(f"{'='*80}")
        logger.info(f"股票代码: {stock_info['code']}")
        logger.info(f"股票名称: {stock_info['name']}")
        logger.info(f"飞书记录 - 5日地量: {stock_info['low_5d']}, 10日地量: {stock_info['low_10d']}, 20日地量: {stock_info['low_20d']}")
        
        # 从通达信获取数据重新计算
        result = verify_low_volume_calculation(stock_info['code'], stock_info['name'])
        
        if result:
            logger.info(f"\n📊 校验结果:")
            if result['is_5d_low'] is not None:
                match_5d = result['is_5d_low'] == stock_info['low_5d']
                status_5d = "✅ 正确" if match_5d else "❌ 错误"
                logger.info(f"  5日地量: 飞书记录={stock_info['low_5d']}, 实际计算={result['is_5d_low']} {status_5d}")
            
            if result['is_10d_low'] is not None:
                match_10d = result['is_10d_low'] == stock_info['low_10d']
                status_10d = "✅ 正确" if match_10d else "❌ 错误"
                logger.info(f"  10日地量: 飞书记录={stock_info['low_10d']}, 实际计算={result['is_10d_low']} {status_10d}")
    
    logger.info(f"\n{'='*80}")
    logger.info("✅ 校验完成")
    logger.info(f"{'='*80}")


if __name__ == "__main__":
    main()
