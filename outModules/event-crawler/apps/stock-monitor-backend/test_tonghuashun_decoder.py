#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试同花顺数据解码器
验证字段映射和数据转换功能
"""

import sys
import os
import asyncio
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.tonghuashun_data_decoder import TonghuashunDataDecoder, decode_tonghuashun_data


def test_decoder():
    """测试解码器功能"""
    print("🧪 开始测试同花顺数据解码器...")
    
    # 测试数据 - 用户提供的原始数据
    test_raw_data = {
        "hs": {
            "300466": {
                "6": "9.65",
                "7": "9.61", 
                "8": "9.67",
                "9": "9.40",
                "10": "9.40",
                "13": "7199100.00",
                "19": "68172919.00",
                "199112": "-2.591",
                "264648": "-0.250",
                "526792": "2.798",
                "1968584": "1.604",
                "2034120": "",
                "3541450": "5033981100.000",
                "name": "赛摩智能"
            }
        }
    }
    
    print(f"📥 原始数据: {test_raw_data}")
    
    # 创建解码器实例
    decoder = TonghuashunDataDecoder()
    
    # 测试字段映射
    print("\n📋 字段映射配置:")
    field_mapping = decoder.get_field_mapping()
    for field_id, field_name in field_mapping.items():
        print(f"  {field_id} -> {field_name}")
    
    # 测试单只股票解码
    print("\n🔍 测试单只股票解码...")
    stock_raw_data = test_raw_data["hs"]["300466"]
    decoded_stock = decoder.decode_stock_data(stock_raw_data)
    
    print("✅ 解码结果:")
    for field, value in decoded_stock.items():
        print(f"  {field}: {value}")
    
    # 测试批量解码
    print("\n🔍 测试批量解码...")
    batch_result = decoder.decode_batch_data(test_raw_data)
    
    print(f"✅ 批量解码结果:")
    print(f"  成功: {batch_result['success']}")
    print(f"  总数: {batch_result['total_count']}")
    print(f"  失败: {batch_result['failed_count']}")
    print(f"  错误: {batch_result['errors']}")
    
    if batch_result['decoded_stocks']:
        for stock_code, stock_data in batch_result['decoded_stocks'].items():
            print(f"\n📊 股票 {stock_code} ({stock_data.get('stock_name', 'N/A')}):")
            print(f"  当前价格: {stock_data.get('current_price', 'N/A')}")
            print(f"  涨跌幅: {stock_data.get('change_percent', 'N/A')}%")
            print(f"  涨跌额: {stock_data.get('change_amount', 'N/A')}")
            print(f"  成交量: {stock_data.get('volume', 'N/A')}")
            print(f"  成交额: {stock_data.get('turnover', 'N/A')}")
            print(f"  最高价: {stock_data.get('high_price', 'N/A')}")
            print(f"  最低价: {stock_data.get('low_price', 'N/A')}")
            print(f"  开盘价: {stock_data.get('open_price', 'N/A')}")
            print(f"  昨收价: {stock_data.get('prev_close', 'N/A')}")
            print(f"  换手率: {stock_data.get('turnover_rate', 'N/A')}%")
            print(f"  振幅: {stock_data.get('amplitude', 'N/A')}%")
            print(f"  市盈率: {stock_data.get('pe_ratio', 'N/A')}")
            print(f"  总市值: {stock_data.get('market_cap', 'N/A')}")
    
    # 测试数据验证
    print("\n🔍 测试数据验证...")
    if batch_result['decoded_stocks']:
        for stock_code, stock_data in batch_result['decoded_stocks'].items():
            is_valid = decoder.validate_decoded_data(stock_data)
            print(f"  股票 {stock_code} 数据验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    
    # 测试便捷函数
    print("\n🔍 测试便捷函数...")
    convenience_result = decode_tonghuashun_data(test_raw_data)
    print(f"  便捷函数结果: 成功={convenience_result['success']}, 总数={convenience_result['total_count']}")
    
    print("\n🎉 测试完成！")


async def test_stock_service_integration():
    """测试与StockService的集成"""
    print("\n🔗 测试与StockService的集成...")
    
    try:
        from app.database.database import get_async_session
        from app.services.stock_service import StockService
        
        # 测试数据
        test_raw_data = {
            "hs": {
                "300466": {
                    "6": "9.65",
                    "7": "9.61", 
                    "8": "9.67",
                    "9": "9.40",
                    "10": "9.40",
                    "13": "7199100.00",
                    "19": "68172919.00",
                    "199112": "-2.591",
                    "264648": "-0.250",
                    "526792": "2.798",
                    "1968584": "1.604",
                    "2034120": "",
                    "3541450": "5033981100.000",
                    "name": "赛摩智能"
                }
            }
        }
        
        # 获取数据库会话
        async with get_async_session() as session:
            stock_service = StockService(session)
            
            # 测试处理同花顺原始数据
            result = await stock_service.process_tonghuashun_raw_data(test_raw_data)
            
            print(f"✅ StockService集成测试结果:")
            print(f"  成功: {result['success']}")
            print(f"  处理数量: {result.get('processed_count', 0)}")
            print(f"  失败数量: {result.get('failed_count', 0)}")
            print(f"  解码总数: {result.get('total_decoded', 0)}")
            print(f"  错误: {result.get('errors', [])}")
            
    except Exception as e:
        print(f"❌ StockService集成测试失败: {e}")
        print("💡 提示: 请确保数据库服务正在运行")


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 同花顺数据解码器测试")
    print("=" * 60)
    
    # 基础解码器测试
    test_decoder()
    
    # 集成测试
    try:
        asyncio.run(test_stock_service_integration())
    except Exception as e:
        print(f"⚠️ 集成测试跳过: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()