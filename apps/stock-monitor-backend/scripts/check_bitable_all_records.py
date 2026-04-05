#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查飞书表格中的所有记录
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from loguru import logger
from app.services.feishu_client import FeishuClient


def check_all_records():
    """检查所有记录"""
    feishu_client = FeishuClient()
    
    access_token = feishu_client._get_access_token()
    if not access_token:
        logger.error("❌ 无法获取访问令牌")
        return
    
    logger.info(f"📊 检查飞书表格: {feishu_client.app_token} / {feishu_client.table_id}")
    
    all_records = []
    page_token = None
    page_size = 500
    
    while True:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{feishu_client.app_token}/tables/{feishu_client.table_id}/records"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        params = {"page_size": page_size}
        if page_token:
            params["page_token"] = page_token
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            result = response.json()
            
            if result.get("code") == 0:
                records = result.get("data", {}).get("items", [])
                all_records.extend(records)
                
                logger.info(f"  获取到 {len(records)} 条记录，累计 {len(all_records)} 条")
                
                has_more = result.get("data", {}).get("has_more", False)
                if not has_more:
                    break
                
                page_token = result.get("data", {}).get("page_token")
                if not page_token:
                    break
            else:
                logger.error(f"❌ 查询记录失败: {result}")
                break
                
        except Exception as e:
            logger.error(f"❌ 查询记录异常: {e}")
            break
    
    logger.info(f"\n✅ 飞书表格共有 {len(all_records)} 条记录")
    
    # 统计板块分布
    sector_count = {}
    for record in all_records:
        fields = record.get("fields", {})
        remark = fields.get("备注", "")
        
        # 从备注中提取板块名称
        if "板块:" in remark:
            sector = remark.split("板块:")[1].split(",")[0] if "," in remark else remark.split("板块:")[1]
            sector_count[sector] = sector_count.get(sector, 0) + 1
    
    logger.info(f"\n📁 板块分布（前20个）:")
    sorted_sectors = sorted(sector_count.items(), key=lambda x: x[1], reverse=True)
    for sector, count in sorted_sectors[:20]:
        logger.info(f"  - {sector}: {count} 只")
    
    if len(sorted_sectors) > 20:
        logger.info(f"  ... 还有 {len(sorted_sectors) - 20} 个板块")
    
    # 显示前10条记录详情
    logger.info(f"\n📋 前10条记录详情:")
    for idx, record in enumerate(all_records[:10], 1):
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
        
        remark = fields.get("备注", "")
        logger.info(f"  [{idx}] {stock_code} {stock_name} - {remark[:60]}")


if __name__ == "__main__":
    check_all_records()
