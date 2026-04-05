#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看标准飞书多维表格字段结构
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from loguru import logger


def get_access_token(app_id: str, app_secret: str) -> str:
    """获取飞书访问令牌"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    
    response = requests.post(url, headers=headers, json=data, timeout=10)
    result = response.json()
    
    if result.get("code") == 0:
        return result.get("tenant_access_token")
    else:
        logger.error(f"获取访问令牌失败: {result}")
        return None


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🔍 查看标准飞书多维表格字段结构")
    logger.info("=" * 60)
    
    # 加载环境变量
    from dotenv import load_dotenv
    env_path = r"d:\agentsTeam\.env.winbot"
    load_dotenv(env_path)
    
    app_id = os.getenv("FEISHU_APP_ID", "")
    app_secret = os.getenv("FEISHU_APP_SECRET", "")
    
    # 标准表格
    standard_app_token = "SRK2bKXmmaWBcVsLds5cWjahnpc"
    standard_table_id = "tblp8ByhFU5YUsZP"
    
    logger.info(f"标准表格 App Token: {standard_app_token}")
    logger.info(f"标准表格 Table ID: {standard_table_id}")
    
    # 获取访问令牌
    access_token = get_access_token(app_id, app_secret)
    if not access_token:
        return
    
    # 查询表格字段
    logger.info("\n[1] 查询标准表格字段...")
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{standard_app_token}/tables/{standard_table_id}/fields"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers, timeout=30)
    result = response.json()
    
    if result.get("code") == 0:
        fields = result.get("data", {}).get("items", [])
        logger.info(f"✅ 找到 {len(fields)} 个字段:")
        for field in fields:
            field_name = field.get("field_name")
            field_type = field.get("type")
            field_id = field.get("field_id")
            logger.info(f"   - {field_name} (类型: {field_type}, ID: {field_id})")
    else:
        logger.error(f"❌ 查询字段失败: {result}")
    
    # 查询表格记录
    logger.info("\n[2] 查询标准表格记录...")
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{standard_app_token}/tables/{standard_table_id}/records"
    params = {"page_size": 5}
    
    response = requests.get(url, headers=headers, params=params, timeout=30)
    result = response.json()
    
    if result.get("code") == 0:
        records = result.get("data", {}).get("items", [])
        total = result.get("data", {}).get("total", 0)
        logger.info(f"✅ 找到 {total} 条记录")
        
        if records:
            logger.info("\n   记录示例:")
            for i, record in enumerate(records[:3], 1):
                fields = record.get("fields", {})
                logger.info(f"   {i}. {fields}")
    else:
        logger.error(f"❌ 查询记录失败: {result}")
    
    logger.info("\n" + "=" * 60)
    logger.info("🔍 检查完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
