#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书CLI风格的多维表格管理工具
使用飞书OpenAPI实现类似CLI的功能
"""

import sys
import os
import json
import requests
from datetime import date
from typing import Dict, Any, List, Optional
from loguru import logger

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class FeishuCLIManager:
    """飞书CLI风格管理器"""
    
    def __init__(self):
        """初始化"""
        from dotenv import load_dotenv
        env_path = r"d:\agentsTeam\.env.winbot"
        load_dotenv(env_path)
        
        self.app_id = os.getenv("FEISHU_APP_ID", "")
        self.app_secret = os.getenv("FEISHU_APP_SECRET", "")
        self.access_token = None
        
    def auth_login(self) -> bool:
        """登录获取访问令牌"""
        logger.info("🔐 登录飞书...")
        
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json"}
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            result = response.json()
            
            if result.get("code") == 0:
                self.access_token = result.get("tenant_access_token")
                logger.info("✅ 登录成功")
                return True
            else:
                logger.error(f"❌ 登录失败: {result}")
                return False
        except Exception as e:
            logger.error(f"❌ 登录异常: {e}")
            return False
    
    def base_create(self, name: str, folder_token: str = None) -> Optional[str]:
        """
        创建多维表格（类似 lark-cli base create）
        
        Args:
            name: 表格名称
            folder_token: 文件夹token
            
        Returns:
            str: 创建的表格app_token
        """
        logger.info(f"📊 创建多维表格: {name}")
        
        if not self.access_token:
            if not self.auth_login():
                return None
        
        url = "https://open.feishu.cn/open-apis/bitable/v1/apps"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "name": name,
            "time_zone": "Asia/Shanghai"
        }
        
        if folder_token:
            data["folder_token"] = folder_token
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            result = response.json()
            
            if result.get("code") == 0:
                app_data = result.get("data", {}).get("app", {})
                app_token = app_data.get("app_token")
                table_id = app_data.get("default_table_id")
                
                logger.info(f"✅ 创建成功")
                logger.info(f"   App Token: {app_token}")
                logger.info(f"   Table ID: {table_id}")
                
                return app_token
            else:
                logger.error(f"❌ 创建失败: {result}")
                return None
        except Exception as e:
            logger.error(f"❌ 创建异常: {e}")
            return None
    
    def base_list(self) -> List[Dict]:
        """
        列出所有多维表格（类似 lark-cli base list）
        
        Returns:
            List[Dict]: 表格列表
        """
        logger.info("📋 列出多维表格...")
        
        if not self.access_token:
            if not self.auth_login():
                return []
        
        url = "https://open.feishu.cn/open-apis/bitable/v1/apps"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            result = response.json()
            
            if result.get("code") == 0:
                apps = result.get("data", {}).get("items", [])
                logger.info(f"✅ 找到 {len(apps)} 个表格")
                
                for app in apps:
                    logger.info(f"   - {app.get('name')} ({app.get('app_token')})")
                
                return apps
            else:
                logger.error(f"❌ 查询失败: {result}")
                return []
        except Exception as e:
            logger.error(f"❌ 查询异常: {e}")
            return []
    
    def base_field_create(self, app_token: str, table_id: str, field_name: str, field_type: int) -> bool:
        """
        创建字段（类似 lark-cli base field create）
        
        Args:
            app_token: 应用token
            table_id: 表格ID
            field_name: 字段名称
            field_type: 字段类型 (1=文本, 2=数字, 3=单选, 5=日期, 7=复选框)
            
        Returns:
            bool: 是否成功
        """
        logger.info(f"➕ 创建字段: {field_name}")
        
        if not self.access_token:
            if not self.auth_login():
                return False
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "field_name": field_name,
            "field_type": field_type
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            result = response.json()
            
            if result.get("code") == 0:
                logger.info(f"✅ 字段创建成功: {field_name}")
                return True
            else:
                logger.warning(f"⚠️ 字段创建失败: {result.get('msg')}")
                return False
        except Exception as e:
            logger.error(f"❌ 字段创建异常: {e}")
            return False
    
    def base_record_create(self, app_token: str, table_id: str, fields: Dict[str, Any]) -> bool:
        """
        创建记录（类似 lark-cli base record create）
        
        Args:
            app_token: 应用token
            table_id: 表格ID
            fields: 字段数据
            
        Returns:
            bool: 是否成功
        """
        if not self.access_token:
            if not self.auth_login():
                return False
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {"fields": fields}
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            result = response.json()
            
            if result.get("code") == 0:
                return True
            else:
                logger.warning(f"⚠️ 记录创建失败: {result.get('msg')}")
                return False
        except Exception as e:
            logger.error(f"❌ 记录创建异常: {e}")
            return False
    
    def base_record_batch_create(self, app_token: str, table_id: str, records: List[Dict[str, Any]]) -> Dict:
        """
        批量创建记录（类似 lark-cli base record batch-create）
        
        Args:
            app_token: 应用token
            table_id: 表格ID
            records: 记录列表
            
        Returns:
            Dict: 创建结果
        """
        logger.info(f"📝 批量创建 {len(records)} 条记录...")
        
        if not self.access_token:
            if not self.auth_login():
                return {"status": "failed", "error": "auth failed"}
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {"records": [{"fields": r} for r in records]}
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            result = response.json()
            
            if result.get("code") == 0:
                created = len(result.get("data", {}).get("records", []))
                logger.info(f"✅ 批量创建成功: {created}/{len(records)} 条")
                return {"status": "success", "created": created}
            else:
                logger.error(f"❌ 批量创建失败: {result}")
                return {"status": "failed", "error": result}
        except Exception as e:
            logger.error(f"❌ 批量创建异常: {e}")
            return {"status": "failed", "error": str(e)}
    
    def base_record_list(self, app_token: str, table_id: str, page_size: int = 100) -> List[Dict]:
        """
        列出记录（类似 lark-cli base record list）
        
        Args:
            app_token: 应用token
            table_id: 表格ID
            page_size: 每页数量
            
        Returns:
            List[Dict]: 记录列表
        """
        logger.info("📋 列出记录...")
        
        if not self.access_token:
            if not self.auth_login():
                return []
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        params = {"page_size": page_size}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            result = response.json()
            
            if result.get("code") == 0:
                records = result.get("data", {}).get("items", [])
                total = result.get("data", {}).get("total", 0)
                logger.info(f"✅ 找到 {total} 条记录")
                return records
            else:
                logger.error(f"❌ 查询失败: {result}")
                return []
        except Exception as e:
            logger.error(f"❌ 查询异常: {e}")
            return []


def main():
    """主函数 - 演示CLI风格操作"""
    logger.info("=" * 60)
    logger.info("🚀 飞书CLI风格管理工具")
    logger.info("=" * 60)
    
    cli = FeishuCLIManager()
    
    # 1. 登录
    if not cli.auth_login():
        return
    
    # 2. 列出所有表格
    logger.info("\n📊 列出所有多维表格:")
    apps = cli.base_list()
    
    # 3. 创建新表格（选股数据）
    logger.info("\n📊 创建新的选股数据表格:")
    table_name = f"选股数据_{date.today().strftime('%Y%m%d')}"
    app_token = cli.base_create(table_name)
    
    if app_token:
        # 获取默认表格ID
        logger.info("\n📋 获取表格信息...")
        # 新创建的表格默认table_id需要从app信息中获取
        # 这里简化处理，实际使用时需要查询
        
        logger.info(f"✅ 表格创建成功: {table_name}")
        logger.info(f"   App Token: {app_token}")
        logger.info(f"   访问链接: https://ua1ubozww7s.feishu.cn/base/{app_token}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ 操作完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
