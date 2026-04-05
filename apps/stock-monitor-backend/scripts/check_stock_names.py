#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查飞书表格中的股票名称字段
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from loguru import logger
from app.services.feishu_client import FeishuClient


def check_stock_names():
    """检查股票名称"""
    feishu_client = FeishuClient()
    
    access_token = feishu_client._get_access_token()
    if not access_token:
        logger.error("❌ 无法获取访问令牌")
        return
    
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{feishu_client.app_token}/tables/{feishu_client.table_id}/records"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    params = {"page_size": 10}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        result = response.json()
        
        if result.get("code") == 0:
            records = result.get("data", {}).get("items", [])
            
            logger.info("📋 飞书表格前10条记录的股票信息：")
            logger.info("-" * 80)
            
            for idx, record in enumerate(records, 1):
                fields = record.get("fields", {})
                
                # 解析股票代码
                stock_code_field = fields.get("股票代码", "")
                if isinstance(stock_code_field, list) and len(stock_code_field) > 0:
                    stock_code = stock_code_field[0].get("text", "") if isinstance(stock_code_field[0], dict) else str(stock_code_field[0])
                else:
                    stock_code = str(stock_code_field) if stock_code_field else ""
                
                # 解析股票名称
                stock_name_field = fields.get("股票名称", "")
                if isinstance(stock_name_field, list) and len(stock_name_field) > 0:
                    stock_name = stock_name_field[0].get("text", "") if isinstance(stock_name_field[0], dict) else str(stock_name_field[0])
                else:
                    stock_name = str(stock_name_field) if stock_name_field else ""
                
                # 解析备注
                remark = fields.get("备注", "")
                
                logger.info(f"[{idx}] 代码: {stock_code}, 名称: {stock_name}, 备注: {remark[:50] if remark else ''}")
                
        else:
            logger.error(f"❌ 查询记录失败: {result}")
            
    except Exception as e:
        logger.error(f"❌ 查询记录异常: {e}")


if __name__ == "__main__":
    check_stock_names()
