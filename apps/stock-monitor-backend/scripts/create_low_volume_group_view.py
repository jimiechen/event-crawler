#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建按地量分组的视图
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from loguru import logger
from app.services.feishu_client import FeishuClient


class LowVolumeGroupViewCreator:
    """地量分组视图创建器"""
    
    def __init__(self):
        self.feishu_client = FeishuClient()
        self.access_token = None
        
    def init(self):
        """初始化"""
        self.access_token = self.feishu_client._get_access_token()
        if not self.access_token:
            logger.error("❌ 无法获取访问令牌")
            return False
        logger.info("✅ 飞书客户端初始化成功")
        return True
    
    def create_view(self, view_name: str, group_field: str = None, sorts: list = None) -> bool:
        """创建视图"""
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.feishu_client.app_token}/tables/{self.feishu_client.table_id}/views"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "view_name": view_name,
            "view_type": "grid"
        }
        
        if group_field:
            data["group_info"] = {
                "field_name": group_field
            }
        
        if sorts:
            data["sort_info"] = sorts
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            result = response.json()
            
            if result.get("code") == 0:
                logger.info(f"  ✅ 创建视图成功: {view_name}")
                return True
            else:
                logger.error(f"  ❌ 创建视图失败 {view_name}: {result}")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ 创建视图异常 {view_name}: {e}")
            return False
    
    def create_all_views(self):
        """创建所有地量分组视图"""
        logger.info("=" * 80)
        logger.info("📊 创建按地量分组的视图")
        logger.info("=" * 80)
        
        if not self.init():
            return
        
        views = [
            {
                "name": "🔴 按5日地量分组",
                "group": "5日地量",
                "sort": [{"field_name": "形态得分", "desc": True}]
            },
            {
                "name": "🔴 按10日地量分组",
                "group": "10日地量",
                "sort": [{"field_name": "形态得分", "desc": True}]
            },
            {
                "name": "🔴 按20日地量分组",
                "group": "20日地量",
                "sort": [{"field_name": "形态得分", "desc": True}]
            },
            {
                "name": "📁 按板块分组",
                "group": "备注",
                "sort": [{"field_name": "形态得分", "desc": True}]
            },
        ]
        
        success_count = 0
        failed_count = 0
        
        for view in views:
            logger.info(f"\n📋 创建视图: {view['name']}")
            if self.create_view(view["name"], view.get("group"), view.get("sort")):
                success_count += 1
            else:
                failed_count += 1
            
            time.sleep(0.5)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"✅ 视图创建完成: 成功 {success_count} 个，失败 {failed_count} 个")
        logger.info(f"{'='*80}")


def main():
    """主函数"""
    creator = LowVolumeGroupViewCreator()
    creator.create_all_views()


if __name__ == "__main__":
    main()
