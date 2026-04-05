#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查飞书多维表格字段结构
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
    logger.info("🔍 检查飞书多维表格字段结构")
    logger.info("=" * 60)
    
    # 加载环境变量
    from dotenv import load_dotenv
    env_path = r"d:\agentsTeam\.env.winbot"
    load_dotenv(env_path)
    
    app_id = os.getenv("FEISHU_APP_ID", "")
    app_secret = os.getenv("FEISHU_APP_SECRET", "")
    app_token = os.getenv("FEISHU_APP_TOKEN", "")
    table_id = os.getenv("FEISHU_TABLE_ID", "")
    
    logger.info(f"App Token: {app_token}")
    logger.info(f"Table ID: {table_id}")
    
    # 获取访问令牌
    access_token = get_access_token(app_id, app_secret)
    if not access_token:
        return
    
    # 查询表格字段
    logger.info("\n[1] 查询表格字段...")
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
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
            logger.info(f"   - {field_name} (类型: {field_type})")
    else:
        logger.error(f"❌ 查询字段失败: {result}")
    
    # 查询表格记录
    logger.info("\n[2] 查询表格记录...")
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    params = {"page_size": 10}
    
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
