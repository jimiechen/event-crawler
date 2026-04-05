#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为飞书多维表格创建看板视图（Kanban）
支持按状态分组、待办事项、紧急重要四象限管理
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from loguru import logger
from app.services.feishu_client import FeishuClient


class KanbanViewCreator:
    """看板视图创建器"""
    
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
    
    def create_view(self, view_name: str, view_type: str = "grid", group_field: str = None, filter_conditions: list = None) -> bool:
        """
        创建视图
        
        Args:
            view_name: 视图名称
            view_type: 视图类型（grid表格/kanban看板）
            group_field: 分组字段
            filter_conditions: 过滤条件
        """
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.feishu_client.app_token}/tables/{self.feishu_client.table_id}/views"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "view_name": view_name,
            "view_type": view_type
        }
        
        if group_field:
            data["group_info"] = {
                "field_name": group_field
            }
        
        if filter_conditions:
            data["filter_info"] = {
                "conjunction": "and",
                "conditions": filter_conditions
            }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            result = response.json()
            
            if result.get("code") == 0:
                logger.info(f"  ✅ 创建视图成功: {view_name} ({view_type})")
                return True
            else:
                logger.error(f"  ❌ 创建视图失败 {view_name}: {result}")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ 创建视图异常 {view_name}: {e}")
            return False
    
    def add_status_field(self):
        """
        添加状态字段（用于看板分组）
        """
        logger.info("\n📋 添加状态字段...")
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.feishu_client.app_token}/tables/{self.feishu_client.table_id}/fields"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "field_name": "状态",
            "type": 3,  # 单选类型
            "property": {
                "options": [
                    {"name": "📥 待观察", "color": 0},
                    {"name": "🔍 观察中", "color": 1},
                    {"name": "✅ 已关注", "color": 2},
                    {"name": "❌ 已放弃", "color": 3},
                ]
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            result = response.json()
            
            if result.get("code") == 0:
                logger.info("  ✅ 添加状态字段成功")
                return True
            else:
                logger.error(f"  ❌ 添加状态字段失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ 添加状态字段异常: {e}")
            return False
    
    def add_priority_field(self):
        """
        添加优先级字段（用于紧急重要四象限）
        """
        logger.info("\n📋 添加优先级字段...")
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.feishu_client.app_token}/tables/{self.feishu_client.table_id}/fields"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "field_name": "优先级",
            "type": 3,  # 单选类型
            "property": {
                "options": [
                    {"name": "🔴 紧急重要", "color": 0},
                    {"name": "🟠 重要不紧急", "color": 1},
                    {"name": "🟡 紧急不重要", "color": 2},
                    {"name": "🟢 不紧急不重要", "color": 3},
                ]
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            result = response.json()
            
            if result.get("code") == 0:
                logger.info("  ✅ 添加优先级字段成功")
                return True
            else:
                logger.error(f"  ❌ 添加优先级字段失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ 添加优先级字段异常: {e}")
            return False
    
    def add_todo_field(self):
        """
        添加待办字段
        """
        logger.info("\n📋 添加待办字段...")
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.feishu_client.app_token}/tables/{self.feishu_client.table_id}/fields"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "field_name": "待办",
            "type": 3,  # 单选类型
            "property": {
                "options": [
                    {"name": "⬜ 待处理", "color": 0},
                    {"name": "🟨 处理中", "color": 1},
                    {"name": "✅ 已完成", "color": 2},
                ]
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            result = response.json()
            
            if result.get("code") == 0:
                logger.info("  ✅ 添加待办字段成功")
                return True
            else:
                logger.error(f"  ❌ 添加待办字段失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ 添加待办字段异常: {e}")
            return False
    
    def create_all_kanban_views(self):
        """创建所有看板视图"""
        logger.info("=" * 80)
        logger.info("📊 为飞书表格创建看板视图（Kanban）")
        logger.info("=" * 80)
        
        if not self.init():
            return
        
        # 1. 添加管理字段
        self.add_status_field()
        time.sleep(0.5)
        
        self.add_priority_field()
        time.sleep(0.5)
        
        self.add_todo_field()
        time.sleep(0.5)
        
        # 2. 创建看板视图
        views = [
            # 按状态分组的看板
            {
                "name": "📋 按状态看板",
                "type": "kanban",
                "group": "状态"
            },
            # 按优先级分组的看板（紧急重要四象限）
            {
                "name": "🔴🟠🟡🟢 紧急重要四象限",
                "type": "kanban",
                "group": "优先级"
            },
            # 按待办分组的看板
            {
                "name": "✅ 待办事项看板",
                "type": "kanban",
                "group": "待办"
            },
            # 按地量分组的看板
            {
                "name": "🔴 地量分组看板",
                "type": "kanban",
                "group": "5日地量"
            },
            # 按得分分组的看板
            {
                "name": "⭐ 按得分分组",
                "type": "kanban",
                "group": "形态得分"
            },
            # 按板块分组的看板
            {
                "name": "📁 按板块分组",
                "type": "kanban",
                "group": "备注"  # 备注中包含板块信息
            },
        ]
        
        success_count = 0
        failed_count = 0
        
        for view in views:
            logger.info(f"\n📋 创建看板视图: {view['name']}")
            if self.create_view(view["name"], view["type"], view.get("group")):
                success_count += 1
            else:
                failed_count += 1
            
            time.sleep(0.5)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"✅ 看板视图创建完成: 成功 {success_count} 个，失败 {failed_count} 个")
        logger.info(f"{'='*80}")
        
        logger.info("\n📖 使用说明:")
        logger.info("  1. 打开飞书表格，切换到看板视图")
        logger.info("  2. 在看板中拖拽卡片改变状态/优先级")
        logger.info("  3. 使用'状态'字段管理股票观察状态")
        logger.info("  4. 使用'优先级'字段进行紧急重要四象限分类")
        logger.info("  5. 使用'待办'字段跟踪处理进度")


def main():
    """主函数"""
    creator = KanbanViewCreator()
    creator.create_all_kanban_views()


if __name__ == "__main__":
    main()
