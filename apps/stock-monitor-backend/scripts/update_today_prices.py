#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新今天日期的所有股票收盘价和成交量
只更新最新日期为今天的记录
"""

import sys
import os
import time
from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

import pandas as pd
import requests
from loguru import logger


class TodayPriceUpdater:
    """今日价格更新器"""
    
    def __init__(self):
        self.tdx_client = None
        self.feishu_client = None
        self.today = date(2026, 4, 3)
        self.today_str = self.today.strftime('%Y-%m-%d')
        
    def init_tdx(self):
        """初始化通达信连接"""
        from tqcenter import tq
        logger.info("[初始化] 连接通达信...")
        tq.initialize(__file__)
        self.tdx_client = tq
        logger.info("✅ 通达信连接成功")
        return tq
    
    def init_feishu(self):
        """初始化飞书客户端"""
        from app.services.feishu_client import FeishuClient
        self.feishu_client = FeishuClient()
        logger.info("✅ 飞书客户端初始化成功")
        return self.feishu_client
    
    def get_today_records_from_bitable(self) -> List[Dict[str, Any]]:
        """
        从飞书多维表格获取今天日期的记录
        使用过滤条件减少数据量
        """
        logger.info(f"📥 从飞书多维表格获取今天({self.today_str})的记录...")
        
        access_token = self.feishu_client._get_access_token()
        if not access_token:
            logger.error("❌ 无法获取访问令牌")
            return []
        
        all_records = []
        page_token = None
        page_size = 500
        
        # 构建过滤条件：最新日期等于今天
        filter_data = {
            "conjunction": "and",
            "conditions": [
                {
                    "field_name": "最新日期",
                    "operator": "is",
                    "value": [self.today_str]
                }
            ]
        }
        
        while True:
            url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.feishu_client.app_token}/tables/{self.feishu_client.table_id}/records/search"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "page_size": page_size,
                "filter": filter_data
            }
            if page_token:
                data["page_token"] = page_token
            
            try:
                response = requests.post(url, headers=headers, json=data, timeout=30)
                result = response.json()
                
                if result.get("code") == 0:
                    records = result.get("data", {}).get("items", [])
                    all_records.extend(records)
                    
                    logger.info(f"  获取到 {len(records)} 条记录，累计 {len(all_records)} 条")
                    
                    has_more = result.get("data", {}).get("has_more", False)
                    if not has_more:
                        break
                    
                    page_token = result.get("data", {}).get("page_token")
                    if not page_token:
                        break
                else:
                    logger.error(f"❌ 查询记录失败: {result}")
                    break
                    
            except Exception as e:
                logger.error(f"❌ 查询记录异常: {e}")
                break
        
        logger.info(f"✅ 共获取 {len(all_records)} 条今天日期的记录")
        return all_records
    
    def get_stock_data(self, stock_code_full: str) -> Optional[Dict[str, Any]]:
        """获取股票最新数据"""
        try:
            data_dict = self.tdx_client.get_market_data(
                field_list=['Open', 'High', 'Low', 'Close', 'Volume', 'Amount'],
                stock_list=[stock_code_full],
                period='1d',
                count=60,
                dividend_type='front',
                fill_data=True
            )
            
            close_df = data_dict.get('Close')
            if close_df is None or close_df.empty:
                return None
            
            latest_date_idx = close_df.index[-1]
            
            close_val = close_df.loc[latest_date_idx, stock_code_full]
            open_val = data_dict.get('Open').loc[latest_date_idx, stock_code_full] if data_dict.get('Open') is not None else None
            high_val = data_dict.get('High').loc[latest_date_idx, stock_code_full] if data_dict.get('High') is not None else None
            low_val = data_dict.get('Low').loc[latest_date_idx, stock_code_full] if data_dict.get('Low') is not None else None
            volume = data_dict.get('Volume').loc[latest_date_idx, stock_code_full] if data_dict.get('Volume') is not None else None
            
            volume = float(volume) / 100 if volume is not None else 0
            
            return {
                'open': float(open_val) if open_val is not None else 0,
                'high': float(high_val) if high_val is not None else 0,
                'low': float(low_val) if low_val is not None else 0,
                'close': float(close_val) if close_val is not None else 0,
                'volume': volume,
            }
            
        except Exception as e:
            logger.error(f"❌ 获取 {stock_code_full} 数据失败: {e}")
            return None
    
    def parse_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """解析飞书记录"""
        fields = record.get("fields", {})
        record_id = record.get("record_id", "")
        
        stock_code_field = fields.get("股票代码", "")
        if isinstance(stock_code_field, list) and len(stock_code_field) > 0:
            stock_code = stock_code_field[0].get("text", "") if isinstance(stock_code_field[0], dict) else str(stock_code_field[0])
        else:
            stock_code = str(stock_code_field) if stock_code_field else ""
        
        stock_name_field = fields.get("股票名称", "")
        if isinstance(stock_name_field, list) and len(stock_name_field) > 0:
            stock_name = stock_name_field[0].get("text", "") if isinstance(stock_name_field[0], dict) else str(stock_name_field[0])
        else:
            stock_name = str(stock_name_field) if stock_name_field else ""
        
        return {
            "record_id": record_id,
            "stock_code": stock_code,
            "stock_name": stock_name,
        }
    
    def update_record_in_bitable(self, record_id: str, fields: Dict[str, Any]) -> bool:
        """更新单条记录"""
        access_token = self.feishu_client._get_access_token()
        if not access_token:
            return False
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.feishu_client.app_token}/tables/{self.feishu_client.table_id}/records/{record_id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        data = {"fields": fields}
        
        try:
            response = requests.put(url, headers=headers, json=data, timeout=30)
            result = response.json()
            
            if result.get("code") == 0:
                return True
            else:
                logger.error(f"❌ 更新记录 {record_id} 失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 更新记录 {record_id} 异常: {e}")
            return False
    
    def run(self):
        """执行更新"""
        logger.info("=" * 80)
        logger.info("📊 更新今天日期的股票收盘价和成交量")
        logger.info("=" * 80)
        logger.info(f"📅 更新日期: {self.today}")
        logger.info("")
        
        # 初始化
        try:
            self.init_tdx()
            self.init_feishu()
        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            return
        
        # 获取今天日期的记录
        records = self.get_today_records_from_bitable()
        if not records:
            logger.warning("⚠️ 没有找到今天日期的记录")
            return
        
        # 更新记录
        logger.info(f"\n📈 开始更新 {len(records)} 只股票...")
        logger.info("")
        
        success_count = 0
        failed_count = 0
        
        for idx, record in enumerate(records, 1):
            parsed = self.parse_record(record)
            stock_code = parsed["stock_code"]
            stock_name = parsed["stock_name"]
            record_id = parsed["record_id"]
            
            if not stock_code:
                logger.warning(f"  [{idx}/{len(records)}] 跳过：股票代码为空")
                continue
            
            # 转换股票代码格式
            if stock_code.startswith('6'):
                stock_code_full = f"{stock_code}.SH"
            else:
                stock_code_full = f"{stock_code}.SZ"
            
            logger.info(f"  [{idx}/{len(records)}] 更新 {stock_code} {stock_name}...")
            
            # 获取最新数据
            data = self.get_stock_data(stock_code_full)
            
            if data:
                # 构建更新字段
                update_fields = {
                    "最新收盘价": float(data['close']),
                    "最新成交量": float(data['volume']),
                    "备注": f"更新于{self.today.strftime('%m%d')}, 收盘:{data['close']:.2f}, 成交量:{data['volume']:.0f}手"
                }
                
                # 更新记录
                if self.update_record_in_bitable(record_id, update_fields):
                    success_count += 1
                    logger.info(f"    ✅ 收盘:{data['close']:.2f}, 成交量:{data['volume']:.0f}手")
                else:
                    failed_count += 1
                    logger.warning(f"    ❌ 更新失败")
            else:
                logger.warning(f"    ⚠️ 无法获取数据")
            
            # 添加延迟避免API限流
            time.sleep(0.1)
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("📊 更新结果统计")
        logger.info("=" * 80)
        logger.info(f"  总计: {len(records)}")
        logger.info(f"  成功: {success_count}")
        logger.info(f"  失败: {failed_count}")
        logger.info("=" * 80)


def main():
    """主函数"""
    updater = TodayPriceUpdater()
    updater.run()


if __name__ == "__main__":
    main()
