#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为飞书多维表格创建仪表盘
数据可视化和统计展示
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from loguru import logger
from app.services.feishu_client import FeishuClient


class BitableDashboardCreator:
    """飞书表格仪表盘创建器"""
    
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
    
    def create_dashboard(self, dashboard_name: str, config: dict) -> bool:
        """
        创建仪表盘
        
        Args:
            dashboard_name: 仪表盘名称
            config: 仪表盘配置
        """
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.feishu_client.app_token}/dashboards"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "name": dashboard_name,
            "config": config
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            result = response.json()
            
            if result.get("code") == 0:
                logger.info(f"  ✅ 创建仪表盘成功: {dashboard_name}")
                return True
            else:
                logger.error(f"  ❌ 创建仪表盘失败 {dashboard_name}: {result}")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ 创建仪表盘异常 {dashboard_name}: {e}")
            return False
    
    def get_table_stats(self) -> dict:
        """获取表格统计数据"""
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.feishu_client.app_token}/tables/{self.feishu_client.table_id}/records/search"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # 获取所有记录统计
        stats = {
            "total": 0,
            "low_volume_5d": 0,
            "low_volume_10d": 0,
            "low_volume_20d": 0,
            "bottom_pattern": 0,
            "yang_bao_yin": 0,
            "breakout_high": 0,
            "breakout_close": 0,
            "high_score_3": 0,
            "high_score_5": 0,
        }
        
        page_token = None
        page_size = 500
        
        while True:
            data = {"page_size": page_size}
            if page_token:
                data["page_token"] = page_token
            
            try:
                response = requests.post(url, headers=headers, json=data, timeout=30)
                result = response.json()
                
                if result.get("code") == 0:
                    records = result.get("data", {}).get("items", [])
                    
                    for record in records:
                        fields = record.get("fields", {})
                        stats["total"] += 1
                        
                        if fields.get("5日地量"): stats["low_volume_5d"] += 1
                        if fields.get("10日地量"): stats["low_volume_10d"] += 1
                        if fields.get("20日地量"): stats["low_volume_20d"] += 1
                        if fields.get("底分型"): stats["bottom_pattern"] += 1
                        if fields.get("阳包阴"): stats["yang_bao_yin"] += 1
                        if fields.get("突破最高价"): stats["breakout_high"] += 1
                        if fields.get("突破收盘价"): stats["breakout_close"] += 1
                        
                        score = fields.get("形态得分", 0)
                        if score and int(score) >= 3: stats["high_score_3"] += 1
                        if score and int(score) >= 5: stats["high_score_5"] += 1
                    
                    has_more = result.get("data", {}).get("has_more", False)
                    if not has_more:
                        break
                    
                    page_token = result.get("data", {}).get("page_token")
                else:
                    break
                    
            except Exception as e:
                logger.error(f"❌ 获取统计数据异常: {e}")
                break
        
        return stats
    
    def create_all_dashboards(self):
        """创建所有仪表盘"""
        logger.info("=" * 80)
        logger.info("📊 为飞书表格创建仪表盘")
        logger.info("=" * 80)
        
        if not self.init():
            return
        
        # 获取统计数据
        logger.info("\n📈 获取表格统计数据...")
        stats = self.get_table_stats()
        
        logger.info(f"\n  总股票数: {stats['total']}")
        logger.info(f"  5日地量: {stats['low_volume_5d']} ({stats['low_volume_5d']/stats['total']*100:.1f}%)")
        logger.info(f"  10日地量: {stats['low_volume_10d']} ({stats['low_volume_10d']/stats['total']*100:.1f}%)")
        logger.info(f"  20日地量: {stats['low_volume_20d']} ({stats['low_volume_20d']/stats['total']*100:.1f}%)")
        logger.info(f"  底分型: {stats['bottom_pattern']}")
        logger.info(f"  阳包阴: {stats['yang_bao_yin']}")
        logger.info(f"  突破入池最高: {stats['breakout_high']}")
        logger.info(f"  突破入池收盘: {stats['breakout_close']}")
        logger.info(f"  高分(≥3分): {stats['high_score_3']}")
        logger.info(f"  高分(≥5分): {stats['high_score_5']}")
        
        # 创建仪表盘配置
        dashboards = [
            {
                "name": "📊 股票数据总览",
                "config": {
                    "widgets": [
                        {
                            "type": "stat",
                            "title": "总股票数",
                            "value": stats['total'],
                            "icon": "stock"
                        },
                        {
                            "type": "stat",
                            "title": "5日地量",
                            "value": stats['low_volume_5d'],
                            "percent": round(stats['low_volume_5d']/stats['total']*100, 1) if stats['total'] > 0 else 0
                        },
                        {
                            "type": "stat",
                            "title": "10日地量",
                            "value": stats['low_volume_10d'],
                            "percent": round(stats['low_volume_10d']/stats['total']*100, 1) if stats['total'] > 0 else 0
                        },
                        {
                            "type": "stat",
                            "title": "20日地量",
                            "value": stats['low_volume_20d'],
                            "percent": round(stats['low_volume_20d']/stats['total']*100, 1) if stats['total'] > 0 else 0
                        },
                    ]
                }
            },
            {
                "name": "📈 形态分析仪表盘",
                "config": {
                    "widgets": [
                        {
                            "type": "pie",
                            "title": "形态分布",
                            "data": [
                                {"name": "底分型", "value": stats['bottom_pattern']},
                                {"name": "阳包阴", "value": stats['yang_bao_yin']},
                                {"name": "其他", "value": stats['total'] - stats['bottom_pattern'] - stats['yang_bao_yin']}
                            ]
                        },
                        {
                            "type": "bar",
                            "title": "地量统计",
                            "data": [
                                {"name": "5日地量", "value": stats['low_volume_5d']},
                                {"name": "10日地量", "value": stats['low_volume_10d']},
                                {"name": "20日地量", "value": stats['low_volume_20d']},
                            ]
                        },
                    ]
                }
            },
            {
                "name": "🚀 突破分析仪表盘",
                "config": {
                    "widgets": [
                        {
                            "type": "stat",
                            "title": "突破入池最高",
                            "value": stats['breakout_high'],
                            "trend": "up"
                        },
                        {
                            "type": "stat",
                            "title": "突破入池收盘",
                            "value": stats['breakout_close'],
                            "trend": "up"
                        },
                        {
                            "type": "progress",
                            "title": "突破率",
                            "value": stats['breakout_high'],
                            "total": stats['total'],
                            "percent": round(stats['breakout_high']/stats['total']*100, 1) if stats['total'] > 0 else 0
                        },
                    ]
                }
            },
            {
                "name": "⭐ 高分股票仪表盘",
                "config": {
                    "widgets": [
                        {
                            "type": "stat",
                            "title": "高分股票(≥3分)",
                            "value": stats['high_score_3'],
                            "color": "orange"
                        },
                        {
                            "type": "stat",
                            "title": "高分股票(≥5分)",
                            "value": stats['high_score_5'],
                            "color": "red"
                        },
                        {
                            "type": "gauge",
                            "title": "高分率",
                            "value": round(stats['high_score_3']/stats['total']*100, 1) if stats['total'] > 0 else 0,
                            "max": 100
                        },
                    ]
                }
            },
        ]
        
        success_count = 0
        failed_count = 0
        
        for dashboard in dashboards:
            logger.info(f"\n📋 创建仪表盘: {dashboard['name']}")
            if self.create_dashboard(dashboard["name"], dashboard["config"]):
                success_count += 1
            else:
                failed_count += 1
            
            time.sleep(0.5)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"✅ 仪表盘创建完成: 成功 {success_count} 个，失败 {failed_count} 个")
        logger.info(f"{'='*80}")


def main():
    """主函数"""
    creator = BitableDashboardCreator()
    creator.create_all_dashboards()


if __name__ == "__main__":
    main()
