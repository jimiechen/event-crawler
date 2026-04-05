#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查飞书多维表格数据
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import date
from loguru import logger

async def check_bitable():
    """检查飞书多维表格数据"""
    
    logger.info("=" * 60)
    logger.info("🔍 检查飞书多维表格数据")
    logger.info("=" * 60)
    
    # 加载环境变量
    from dotenv import load_dotenv
    env_path = r"d:\agentsTeam\.env.winbot"
    load_dotenv(env_path)
    
    # 旧表格配置
    old_app_token = "CsBlwtWU6igB1bkkwp1c28TAn5f"
    old_table_id = "tblCQA1vS1Tx59Q4"
    
    # 新表格配置
    new_app_token = "SRK2bKXmmaWBcVsLds5cWjahnpc"
    new_table_id = "tblp8ByhFU5YUsZP"
    
    app_id = os.getenv("FEISHU_APP_ID", "")
    app_secret = os.getenv("FEISHU_APP_SECRET", "")
    
    logger.info(f"飞书应用ID: {app_id[:10]}...")
    
    try:
        import requests
        import time
        
        # 1. 获取访问令牌
        logger.info("\n[1] 获取飞书访问令牌...")
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json"}
        data = {
            "app_id": app_id,
            "app_secret": app_secret
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        result = response.json()
        
        if result.get("code") != 0:
            logger.error(f"❌ 获取访问令牌失败: {result}")
            return
        
        access_token = result.get("tenant_access_token")
        logger.info("✅ 获取访问令牌成功")
        
        # 2. 查询旧表格数据
        logger.info(f"\n[2] 查询旧表格数据...")
        logger.info(f"   App Token: {old_app_token}")
        logger.info(f"   Table ID: {old_table_id}")
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{old_app_token}/tables/{old_table_id}/records"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        params = {
            "page_size": 100
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        result = response.json()
        
        if result.get("code") == 0:
            records = result.get("data", {}).get("items", [])
            total = result.get("data", {}).get("total", 0)
            logger.info(f"✅ 旧表格查询成功")
            logger.info(f"   总记录数: {total}")
            logger.info(f"   返回记录数: {len(records)}")
            
            if records:
                logger.info("\n   最近10条记录:")
                for i, record in enumerate(records[:10], 1):
                    fields = record.get("fields", {})
                    stock_code = fields.get("股票代码", "N/A")
                    stock_name = fields.get("股票名称", "N/A")
                    trade_date = fields.get("交易日期", "N/A")
                    logger.info(f"   {i}. {stock_code} {stock_name} - {trade_date}")
        else:
            logger.error(f"❌ 旧表格查询失败: {result}")
        
        # 3. 查询新表格数据
        logger.info(f"\n[3] 查询新表格数据...")
        logger.info(f"   App Token: {new_app_token}")
        logger.info(f"   Table ID: {new_table_id}")
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{new_app_token}/tables/{new_table_id}/records"
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        result = response.json()
        
        if result.get("code") == 0:
            records = result.get("data", {}).get("items", [])
            total = result.get("data", {}).get("total", 0)
            logger.info(f"✅ 新表格查询成功")
            logger.info(f"   总记录数: {total}")
            logger.info(f"   返回记录数: {len(records)}")
            
            if records:
                logger.info("\n   最近10条记录:")
                for i, record in enumerate(records[:10], 1):
                    fields = record.get("fields", {})
                    stock_code = fields.get("股票代码", "N/A")
                    stock_name = fields.get("股票名称", "N/A")
                    trade_date = fields.get("交易日期", "N/A")
                    logger.info(f"   {i}. {stock_code} {stock_name} - {trade_date}")
        else:
            logger.error(f"❌ 新表格查询失败: {result}")
        
    except Exception as e:
        logger.error(f"❌ 检查失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    logger.info("\n" + "=" * 60)
    logger.info("🔍 检查完成")
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(check_bitable())
