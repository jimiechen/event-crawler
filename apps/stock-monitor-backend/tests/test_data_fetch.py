#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据抓取功能验证测试
验证任务3.2的验收用例
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.tonghuashun_mcp_client import TongHuaShunMCPClient
from app.utils.data_deduplication import DataDeduplicationManager
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_user_stock_list():
    """测试用户股票列表抓取"""
    logger.info("开始测试用户股票列表抓取...")
    
    client = TongHuaShunMCPClient()
    
    try:
        result = await client.get_user_stock_list()
        logger.info(f"用户股票列表抓取结果: {result}")
        
        # 验收用例检查
        if result.get('success'):
            logger.info("✓ 用户股票列表抓取成功")
            logger.info(f"✓ 抓取到 {result.get('total_count', 0)} 只股票")
            return True
        else:
            logger.error(f"✗ 用户股票列表抓取失败: {result.get('error')}")
            return False
            
    except Exception as e:
        logger.error(f"✗ 用户股票列表抓取异常: {str(e)}")
        return False

async def test_stock_realtime_data():
    """测试股票实时数据抓取"""
    logger.info("开始测试股票实时数据抓取...")
    
    client = TongHuaShunMCPClient()
    
    # 测试股票代码
    test_codes = ['000001', '000002', '600000']
    
    try:
        result = await client.get_stock_realtime_data(test_codes)
        logger.info(f"股票实时数据抓取结果: {result}")
        
        # 验收用例检查
        if result.get('success'):
            logger.info("✓ 股票实时数据抓取成功")
            stock_data = result.get('stock_data', [])
            logger.info(f"✓ 抓取到 {len(stock_data)} 只股票的实时数据")
            
            # 检查数据字段
            if stock_data:
                sample = stock_data[0]
                required_fields = ['code', 'name', 'current_price', 'change_amount', 'change_percent']
                missing_fields = [field for field in required_fields if field not in sample]
                
                if not missing_fields:
                    logger.info("✓ 股票数据字段映射准确")
                    return True
                else:
                    logger.error(f"✗ 缺少必需字段: {missing_fields}")
                    return False
            else:
                logger.warning("⚠ 未获取到股票数据")
                return False
        else:
            logger.error(f"✗ 股票实时数据抓取失败: {result.get('error')}")
            return False
            
    except Exception as e:
        logger.error(f"✗ 股票实时数据抓取异常: {str(e)}")
        return False

async def test_data_deduplication():
    """测试数据去重机制"""
    logger.info("开始测试数据去重机制...")
    
    try:
        # 不使用数据库连接池，直接测试哈希算法
        dedup_manager = DataDeduplicationManager(None)
        
        # 测试数据
        test_data = {
            'code': '000001',
            'name': '平安银行',
            'current_price': 10.25,
            'change_amount': 0.15,
            'change_percent': 1.48,
            'timestamp': '2024-01-01T10:00:00'
        }
        
        # 生成哈希
        hash1 = dedup_manager._generate_hash(test_data)
        hash2 = dedup_manager._generate_hash(test_data)
        
        if hash1 == hash2:
            logger.info("✓ 数据哈希算法一致性正确")
            logger.info(f"✓ 生成的哈希值: {hash1}")
            return True
        else:
            logger.error("✗ 数据哈希算法一致性错误")
            return False
            
    except Exception as e:
        logger.error(f"✗ 数据去重测试异常: {str(e)}")
        return False

async def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("同花顺数据抓取功能验证测试")
    logger.info("任务3.2验收用例测试")
    logger.info("=" * 60)
    
    test_results = []
    
    # 测试1：用户股票列表抓取
    result1 = await test_user_stock_list()
    test_results.append(("用户股票列表抓取", result1))
    
    logger.info("-" * 40)
    
    # 测试2：股票实时数据抓取
    result2 = await test_stock_realtime_data()
    test_results.append(("股票实时数据抓取", result2))
    
    logger.info("-" * 40)
    
    # 测试3：数据去重机制
    result3 = await test_data_deduplication()
    test_results.append(("数据去重机制", result3))
    
    # 汇总结果
    logger.info("=" * 60)
    logger.info("测试结果汇总:")
    
    passed_count = 0
    for test_name, result in test_results:
        status = "✓ 通过" if result else "✗ 失败"
        logger.info(f"{test_name}: {status}")
        if result:
            passed_count += 1
    
    logger.info(f"总计: {passed_count}/{len(test_results)} 项测试通过")
    
    if passed_count == len(test_results):
        logger.info("🎉 任务3.2验收用例全部通过！")
        return True
    else:
        logger.error("❌ 部分验收用例未通过，需要修复")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)