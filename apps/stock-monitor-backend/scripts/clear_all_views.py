#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清空飞书多维表格的所有视图
只保留默认的"选股记录"视图
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from loguru import logger
from app.services.feishu_client import FeishuClient


class ViewCleaner:
    """视图清理器"""
    
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
    
    def get_all_views(self) -> list:
        """获取所有视图"""
        logger.info("📋 获取所有视图列表...")
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.feishu_client.app_token}/tables/{self.feishu_client.table_id}/views"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        all_views = []
        page_token = None
        
        while True:
            params = {}
            if page_token:
                params["page_token"] = page_token
            
            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)
                result = response.json()
                
                if result.get("code") == 0:
                    views = result.get("data", {}).get("items", [])
                    all_views.extend(views)
                    
                    has_more = result.get("data", {}).get("has_more", False)
                    if not has_more:
                        break
                    
                    page_token = result.get("data", {}).get("page_token")
                else:
                    logger.error(f"❌ 获取视图列表失败: {result}")
                    break
                    
            except Exception as e:
                logger.error(f"❌ 获取视图列表异常: {e}")
                break
        
        logger.info(f"✅ 共找到 {len(all_views)} 个视图")
        return all_views
    
    def delete_view(self, view_id: str, view_name: str) -> bool:
        """删除视图"""
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.feishu_client.app_token}/tables/{self.feishu_client.table_id}/views/{view_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.delete(url, headers=headers, timeout=30)
            result = response.json()
            
            if result.get("code") == 0:
                logger.info(f"  ✅ 删除视图: {view_name}")
                return True
            else:
                logger.error(f"  ❌ 删除视图失败 {view_name}: {result}")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ 删除视图异常 {view_name}: {e}")
            return False
    
    def clear_all_views(self):
        """清空所有视图，只保留默认视图"""
        logger.info("=" * 80)
        logger.info("🗑️ 清空所有视图，只保留默认视图")
        logger.info("=" * 80)
        
        if not self.init():
            return
        
        # 获取所有视图
        views = self.get_all_views()
        if not views:
            logger.info("⚠️ 没有找到视图")
            return
        
        # 保留的视图名称（默认视图）
        keep_views = ["选股记录", "Grid", "表格", "默认", "Default"]
        
        deleted_count = 0
        failed_count = 0
        skipped_count = 0
        
        for view in views:
            view_id = view.get("view_id", "")
            view_name = view.get("view_name", "")
            
            # 检查是否是默认视图
            is_default = any(keep in view_name for keep in keep_views)
            
            if is_default:
                logger.info(f"  ⏭️ 跳过默认视图: {view_name}")
                skipped_count += 1
                continue
            
            # 删除视图
            if self.delete_view(view_id, view_name):
                deleted_count += 1
            else:
                failed_count += 1
            
            time.sleep(0.3)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"✅ 视图清理完成:")
        logger.info(f"  删除: {deleted_count} 个")
        logger.info(f"  保留: {skipped_count} 个")
        logger.info(f"  失败: {failed_count} 个")
        logger.info(f"{'='*80}")


def main():
    """主函数"""
    cleaner = ViewCleaner()
    cleaner.clear_all_views()


if __name__ == "__main__":
    main()
