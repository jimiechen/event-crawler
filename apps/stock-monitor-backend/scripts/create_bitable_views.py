#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为飞书多维表格创建多个视图
方便快速查看地量、形态、突破、积分、排名等数据
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from loguru import logger
from app.services.feishu_client import FeishuClient


class BitableViewCreator:
    """飞书表格视图创建器"""
    
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
    
    def create_view(self, view_name: str, filter_conditions: list = None, sorts: list = None) -> bool:
        """
        创建视图
        
        Args:
            view_name: 视图名称
            filter_conditions: 过滤条件列表
            sorts: 排序规则列表
        """
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.feishu_client.app_token}/tables/{self.feishu_client.table_id}/views"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "view_name": view_name,
            "view_type": "grid"  # 表格视图
        }
        
        if filter_conditions:
            data["filter_info"] = {
                "conjunction": "and",
                "conditions": filter_conditions
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
        """创建所有视图"""
        logger.info("=" * 80)
        logger.info("📊 为飞书表格创建多个视图")
        logger.info("=" * 80)
        
        if not self.init():
            return
        
        views = [
            # 1. 地量股票视图
            {
                "name": "🔴 地量股票 (5日)",
                "filter": [
                    {
                        "field_name": "5日地量",
                        "operator": "is",
                        "value": ["true"]
                    }
                ],
                "sort": [
                    {"field_name": "形态得分", "desc": True}
                ]
            },
            {
                "name": "🔴 地量股票 (10日)",
                "filter": [
                    {
                        "field_name": "10日地量",
                        "operator": "is",
                        "value": ["true"]
                    }
                ],
                "sort": [
                    {"field_name": "形态得分", "desc": True}
                ]
            },
            {
                "name": "🔴 地量股票 (20日)",
                "filter": [
                    {
                        "field_name": "20日地量",
                        "operator": "is",
                        "value": ["true"]
                    }
                ],
                "sort": [
                    {"field_name": "形态得分", "desc": True}
                ]
            },
            
            # 2. 形态股票视图
            {
                "name": "📈 底分型股票",
                "filter": [
                    {
                        "field_name": "底分型",
                        "operator": "is",
                        "value": ["true"]
                    }
                ],
                "sort": [
                    {"field_name": "形态得分", "desc": True}
                ]
            },
            {
                "name": "📈 阳包阴股票",
                "filter": [
                    {
                        "field_name": "阳包阴",
                        "operator": "is",
                        "value": ["true"]
                    }
                ],
                "sort": [
                    {"field_name": "形态得分", "desc": True}
                ]
            },
            
            # 3. 突破股票视图
            {
                "name": "🚀 突破入池最高",
                "filter": [
                    {
                        "field_name": "突破最高价",
                        "operator": "is",
                        "value": ["true"]
                    }
                ],
                "sort": [
                    {"field_name": "最新收盘价", "desc": True}
                ]
            },
            {
                "name": "🚀 突破入池收盘",
                "filter": [
                    {
                        "field_name": "突破收盘价",
                        "operator": "is",
                        "value": ["true"]
                    }
                ],
                "sort": [
                    {"field_name": "最新收盘价", "desc": True}
                ]
            },
            
            # 4. 高分股票视图
            {
                "name": "⭐ 高分股票 (≥3分)",
                "filter": [
                    {
                        "field_name": "形态得分",
                        "operator": "isGreaterEqual",
                        "value": ["3"]
                    }
                ],
                "sort": [
                    {"field_name": "形态得分", "desc": True}
                ]
            },
            {
                "name": "⭐⭐ 高分股票 (≥5分)",
                "filter": [
                    {
                        "field_name": "形态得分",
                        "operator": "isGreaterEqual",
                        "value": ["5"]
                    }
                ],
                "sort": [
                    {"field_name": "形态得分", "desc": True}
                ]
            },
            
            # 5. 综合优质股票视图
            {
                "name": "💎 地量+底分型",
                "filter": [
                    {
                        "field_name": "5日地量",
                        "operator": "is",
                        "value": ["true"]
                    },
                    {
                        "field_name": "底分型",
                        "operator": "is",
                        "value": ["true"]
                    }
                ],
                "sort": [
                    {"field_name": "形态得分", "desc": True}
                ]
            },
            {
                "name": "💎 地量+阳包阴",
                "filter": [
                    {
                        "field_name": "5日地量",
                        "operator": "is",
                        "value": ["true"]
                    },
                    {
                        "field_name": "阳包阴",
                        "operator": "is",
                        "value": ["true"]
                    }
                ],
                "sort": [
                    {"field_name": "形态得分", "desc": True}
                ]
            },
            {
                "name": "💎 地量+突破",
                "filter": [
                    {
                        "field_name": "5日地量",
                        "operator": "is",
                        "value": ["true"]
                    },
                    {
                        "field_name": "突破最高价",
                        "operator": "is",
                        "value": ["true"]
                    }
                ],
                "sort": [
                    {"field_name": "形态得分", "desc": True}
                ]
            },
            
            # 6. 按板块查看
            {
                "name": "📁 按板块查看",
                "filter": [],
                "sort": [
                    {"field_name": "备注", "desc": False}
                ]
            },
            
            # 7. 按入池日期查看
            {
                "name": "📅 按入池日期查看",
                "filter": [],
                "sort": [
                    {"field_name": "入池日期", "desc": True}
                ]
            },
        ]
        
        success_count = 0
        failed_count = 0
        
        for view in views:
            logger.info(f"\n📋 创建视图: {view['name']}")
            if self.create_view(view["name"], view.get("filter"), view.get("sort")):
                success_count += 1
            else:
                failed_count += 1
            
            time.sleep(0.5)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"✅ 视图创建完成: 成功 {success_count} 个，失败 {failed_count} 个")
        logger.info(f"{'='*80}")


def main():
    """主函数"""
    creator = BitableViewCreator()
    creator.create_all_views()


if __name__ == "__main__":
    main()
