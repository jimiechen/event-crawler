#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看飞书多维表格完整字段结构
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
    logger.info("=" * 80)
    logger.info("🔍 查看飞书多维表格完整字段结构")
    logger.info("=" * 80)
    
    # 加载环境变量
    from dotenv import load_dotenv
    env_path = r"d:\agentsTeam\.env.winbot"
    load_dotenv(env_path)
    
    app_id = os.getenv("FEISHU_APP_ID", "")
    app_secret = os.getenv("FEISHU_APP_SECRET", "")
    app_token = os.getenv("FEISHU_APP_TOKEN", "")
    table_id = os.getenv("FEISHU_TABLE_ID", "")
    
    logger.info(f"标准表格 App Token: {app_token}")
    logger.info(f"标准表格 Table ID: {table_id}")
    
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
        logger.info("\n" + "-" * 80)
        logger.info(f"{'序号':<6}{'字段名':<20}{'类型':<15}{'ID':<30}")
        logger.info("-" * 80)
        
        field_type_map = {
            1: "文本",
            2: "数字", 
            3: "单选",
            4: "多选",
            5: "日期",
            7: "复选框",
            11: "人员",
            13: "电话号码",
            15: "超链接",
            17: "附件",
            18: "关联",
            20: "公式",
            21: "双向关联",
            22: "地理位置",
            1001: "创建时间",
            1002: "最后更新时间",
            1003: "创建人",
            1004: "最后更新人"
        }
        
        for i, field in enumerate(fields, 1):
            field_name = field.get("field_name", "")
            field_type = field.get("type", 0)
            field_id = field.get("field_id", "")
            type_name = field_type_map.get(field_type, f"类型{field_type}")
            
            logger.info(f"{i:<6}{field_name:<20}{type_name:<15}{field_id:<30}")
        
        logger.info("-" * 80)
        
        # 分类显示字段
        logger.info("\n[字段分类]")
        
        # 基础信息字段
        basic_fields = [f for f in fields if f.get("field_name") in ["股票代码", "股票名称", "入池日期"]]
        logger.info(f"\n📋 基础信息字段 ({len(basic_fields)}个):")
        for f in basic_fields:
            logger.info(f"   - {f.get('field_name')}")
        
        # 入池数据字段
        pool_fields = [f for f in fields if "入池" in f.get("field_name", "") and f.get("field_name") != "入池日期"]
        logger.info(f"\n📊 入池数据字段 ({len(pool_fields)}个):")
        for f in pool_fields:
            logger.info(f"   - {f.get('field_name')}")
        
        # 最新数据字段
        latest_fields = [f for f in fields if "最新" in f.get("field_name", "")]
        logger.info(f"\n📈 最新数据字段 ({len(latest_fields)}个):")
        for f in latest_fields:
            logger.info(f"   - {f.get('field_name')}")
        
        # 地量字段
        low_vol_fields = [f for f in fields if "地量" in f.get("field_name", "")]
        logger.info(f"\n📉 地量字段 ({len(low_vol_fields)}个):")
        for f in low_vol_fields:
            logger.info(f"   - {f.get('field_name')}")
        
        # 形态字段
        pattern_fields = [f for f in fields if any(kw in f.get("field_name", "") for kw in ["突破", "阳包阴", "底分型", "收盘价", "告警"])]
        logger.info(f"\n🔍 形态字段 ({len(pattern_fields)}个):")
        for f in pattern_fields:
            logger.info(f"   - {f.get('field_name')}")
        
        # 其他字段
        other_fields = [f for f in fields if f.get("field_name") not in 
                       ["股票代码", "股票名称", "入池日期"] + 
                       [f.get("field_name") for f in pool_fields] + 
                       [f.get("field_name") for f in latest_fields] + 
                       [f.get("field_name") for f in low_vol_fields] + 
                       [f.get("field_name") for f in pattern_fields]]
        logger.info(f"\n📝 其他字段 ({len(other_fields)}个):")
        for f in other_fields:
            logger.info(f"   - {f.get('field_name')}")
        
    else:
        logger.error(f"❌ 查询字段失败: {result}")
    
    # 查询表格记录数
    logger.info("\n[2] 查询表格记录...")
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    params = {"page_size": 1}
    
    response = requests.get(url, headers=headers, params=params, timeout=30)
    result = response.json()
    
    if result.get("code") == 0:
        total = result.get("data", {}).get("total", 0)
        logger.info(f"✅ 表格共有 {total} 条记录")
        
        # 显示一条示例记录
        records = result.get("data", {}).get("items", [])
        if records:
            logger.info("\n[示例记录]:")
            fields = records[0].get("fields", {})
            for key, value in fields.items():
                logger.info(f"   {key}: {value}")
    else:
        logger.error(f"❌ 查询记录失败: {result}")
    
    logger.info("\n" + "=" * 80)
    logger.info("🔍 检查完成")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
