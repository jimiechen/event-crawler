#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建飞书多维表格用于存储选股数据
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from datetime import date
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


def create_bitable_app(access_token: str, name: str, folder_token: str = None) -> dict:
    """
    创建多维表格应用
    
    Args:
        access_token: 访问令牌
        name: 表格名称
        folder_token: 文件夹token（可选）
        
    Returns:
        dict: 创建结果，包含 app_token 和 table_id
    """
    url = "https://open.feishu.cn/open-apis/bitable/v1/apps"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "name": name,
        "time_zone": "Asia/Shanghai"
    }
    
    if folder_token:
        data["folder_token"] = folder_token
    
    response = requests.post(url, headers=headers, json=data, timeout=30)
    result = response.json()
    
    logger.info(f"API响应: {result}")
    
    if result.get("code") == 0:
        app_data = result.get("data", {}).get("app", {})
        app_token = app_data.get("app_token")
        default_table_id = app_data.get("default_table_id")
        
        if not app_token or not default_table_id:
            logger.error(f"❌ API返回空值: app_token={app_token}, table_id={default_table_id}")
            logger.error(f"完整响应: {result}")
            return {"status": "failed", "error": "API返回空值"}
        
        logger.info(f"✅ 创建多维表格成功: {name}")
        logger.info(f"   App Token: {app_token}")
        logger.info(f"   Table ID: {default_table_id}")
        return {
            "status": "success",
            "app_token": app_token,
            "table_id": default_table_id
        }
    else:
        logger.error(f"❌ 创建多维表格失败: {result}")
        return {"status": "failed", "error": result}


def create_table_fields(access_token: str, app_token: str, table_id: str) -> bool:
    """
    创建表格字段
    
    Args:
        access_token: 访问令牌
        app_token: 应用token
        table_id: 表格ID
        
    Returns:
        bool: 是否成功
    """
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 定义字段
    fields = [
        {"field_name": "选股日期", "field_type": 5},  # 日期
        {"field_name": "股票代码", "field_type": 1},  # 文本
        {"field_name": "股票名称", "field_type": 1},  # 文本
        {"field_name": "所属板块", "field_type": 1},  # 文本
        {"field_name": "收盘价", "field_type": 2},  # 数字
        {"field_name": "开盘价", "field_type": 2},  # 数字
        {"field_name": "最高价", "field_type": 2},  # 数字
        {"field_name": "最低价", "field_type": 2},  # 数字
        {"field_name": "成交量", "field_type": 2},  # 数字
        {"field_name": "成交额", "field_type": 2},  # 数字
        {"field_name": "涨跌幅", "field_type": 2},  # 数字
        {"field_name": "量比", "field_type": 2},  # 数字
        {"field_name": "3倍量", "field_type": 7},  # 复选框
        {"field_name": "涨停", "field_type": 7},  # 复选框
        {"field_name": "60日地量", "field_type": 7},  # 复选框
        {"field_name": "30日地量", "field_type": 7},  # 复选框
        {"field_name": "20日地量", "field_type": 7},  # 复选框
        {"field_name": "10日地量", "field_type": 7},  # 复选框
        {"field_name": "5日地量", "field_type": 7},  # 复选框
        {"field_name": "批次ID", "field_type": 2},  # 数字
        {"field_name": "板块代码", "field_type": 1},  # 文本
        {"field_name": "创建时间", "field_type": 5},  # 日期
    ]
    
    success_count = 0
    for field in fields:
        try:
            response = requests.post(url, headers=headers, json=field, timeout=10)
            result = response.json()
            
            if result.get("code") == 0:
                success_count += 1
                logger.info(f"   ✅ 创建字段: {field['field_name']}")
            else:
                logger.warning(f"   ⚠️ 创建字段失败 {field['field_name']}: {result.get('msg')}")
        except Exception as e:
            logger.error(f"   ❌ 创建字段异常 {field['field_name']}: {e}")
    
    logger.info(f"字段创建完成: {success_count}/{len(fields)}")
    return success_count > 0


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🚀 创建飞书多维表格 - 选股数据存储")
    logger.info("=" * 60)
    
    # 加载环境变量
    from dotenv import load_dotenv
    env_path = r"d:\agentsTeam\.env.winbot"
    load_dotenv(env_path)
    
    app_id = os.getenv("FEISHU_APP_ID", "")
    app_secret = os.getenv("FEISHU_APP_SECRET", "")
    
    if not app_id or not app_secret:
        logger.error("❌ 飞书应用凭证未配置")
        return
    
    # 获取访问令牌
    logger.info("\n[1] 获取飞书访问令牌...")
    access_token = get_access_token(app_id, app_secret)
    if not access_token:
        return
    logger.info("✅ 获取访问令牌成功")
    
    # 创建多维表格
    logger.info("\n[2] 创建多维表格...")
    table_name = f"选股数据_{date.today().strftime('%Y%m%d')}"
    result = create_bitable_app(access_token, table_name)
    
    if result["status"] != "success":
        return
    
    app_token = result["app_token"]
    table_id = result["table_id"]
    
    # 创建字段
    logger.info("\n[3] 创建表格字段...")
    create_table_fields(access_token, app_token, table_id)
    
    # 输出配置信息
    logger.info("\n" + "=" * 60)
    logger.info("✅ 多维表格创建完成!")
    logger.info("=" * 60)
    logger.info(f"表格名称: {table_name}")
    logger.info(f"App Token: {app_token}")
    logger.info(f"Table ID: {table_id}")
    logger.info("\n请更新 .env.winbot 文件中的配置:")
    logger.info(f"FEISHU_APP_TOKEN={app_token}")
    logger.info(f"FEISHU_TABLE_ID={table_id}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
