#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第二阶段：更新最新数据并计算形态
- 获取今天（2026-04-03）的最新价格和成交量
- 计算地量（今天是否是N天内最低）
- 计算形态（底分型、阳包阴）
- 比较最新价与入池价
"""

import sys
import os
import time
from datetime import date, datetime
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

import pandas as pd
import requests
from loguru import logger


class LatestDataUpdater:
    """最新数据更新器"""
    
    def __init__(self):
        self.tdx_client = None
        self.feishu_client = None
        self.today = date(2026, 4, 3)
        
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
    
    def get_all_stocks_from_bitable(self) -> List[Dict[str, Any]]:
        """从飞书表格读取所有股票记录"""
        logger.info("📥 从飞书表格读取所有股票记录...")
        
        access_token = self.feishu_client._get_access_token()
        if not access_token:
            logger.error("❌ 无法获取访问令牌")
            return []
        
        all_records = []
        page_token = None
        page_size = 500
        
        while True:
            url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.feishu_client.app_token}/tables/{self.feishu_client.table_id}/records"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            params = {"page_size": page_size}
            if page_token:
                params["page_token"] = page_token
            
            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)
                result = response.json()
                
                if result.get("code") == 0:
                    records = result.get("data", {}).get("items", [])
                    all_records.extend(records)
                    
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
        
        logger.info(f"✅ 共获取到 {len(all_records)} 条记录")
        return all_records
    
    def parse_stock_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """解析股票记录"""
        fields = record.get("fields", {})
        record_id = record.get("record_id", "")
        
        # 解析股票代码
        stock_code_field = fields.get("股票代码", "")
        if isinstance(stock_code_field, list) and len(stock_code_field) > 0:
            stock_code = stock_code_field[0].get("text", "") if isinstance(stock_code_field[0], dict) else str(stock_code_field[0])
        else:
            stock_code = str(stock_code_field) if stock_code_field else ""
        
        # 解析股票名称
        stock_name_field = fields.get("股票名称", "")
        if isinstance(stock_name_field, list) and len(stock_name_field) > 0:
            stock_name = stock_name_field[0].get("text", "") if isinstance(stock_name_field[0], dict) else str(stock_name_field[0])
        else:
            stock_name = str(stock_name_field) if stock_name_field else ""
        
        # 解析入池数据
        pool_high = fields.get("入池最高价", 0)
        pool_close = fields.get("入池收盘价", 0)
        
        return {
            "record_id": record_id,
            "stock_code": stock_code,
            "stock_name": stock_name,
            "pool_high": float(pool_high) if pool_high else 0,
            "pool_close": float(pool_close) if pool_close else 0,
        }
    
    def get_stock_data(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """获取股票今天数据和60天历史数据"""
        try:
            if stock_code.startswith('6'):
                stock_code_full = f"{stock_code}.SH"
            else:
                stock_code_full = f"{stock_code}.SZ"
            
            # 获取60天历史数据
            data_dict = self.tdx_client.get_market_data(
                field_list=['Open', 'High', 'Low', 'Close', 'Volume'],
                stock_list=[stock_code_full],
                period='1d',
                count=60,
                dividend_type='front',
                fill_data=True
            )
            
            close_df = data_dict.get('Close')
            if close_df is None or close_df.empty:
                return None
            
            # 获取今天数据
            latest_date_idx = close_df.index[-1]
            today_close = close_df.loc[latest_date_idx, stock_code_full]
            today_open = data_dict.get('Open').loc[latest_date_idx, stock_code_full] if data_dict.get('Open') is not None else None
            today_high = data_dict.get('High').loc[latest_date_idx, stock_code_full] if data_dict.get('High') is not None else None
            today_low = data_dict.get('Low').loc[latest_date_idx, stock_code_full] if data_dict.get('Low') is not None else None
            today_volume = data_dict.get('Volume').loc[latest_date_idx, stock_code_full] if data_dict.get('Volume') is not None else None
            
            today_volume = float(today_volume) / 100 if today_volume is not None else 0
            
            # 构建DataFrame用于形态计算
            df_data = {
                'Open': data_dict.get('Open')[stock_code_full] if data_dict.get('Open') is not None else None,
                'High': data_dict.get('High')[stock_code_full] if data_dict.get('High') is not None else None,
                'Low': data_dict.get('Low')[stock_code_full] if data_dict.get('Low') is not None else None,
                'Close': close_df[stock_code_full],
                'Volume': data_dict.get('Volume')[stock_code_full] if data_dict.get('Volume') is not None else None,
            }
            df = pd.DataFrame(df_data)
            df.index = close_df.index
            df['Volume'] = df['Volume'] / 100  # 转换为手
            
            # 计算地量
            volume_series = df['Volume']
            low_volume_flags = self.calculate_low_volume_flags(volume_series)
            
            # 计算形态
            pattern_flags = self.calculate_pattern_flags(df)
            
            return {
                'today_close': float(today_close) if today_close is not None else 0,
                'today_open': float(today_open) if today_open is not None else 0,
                'today_high': float(today_high) if today_high is not None else 0,
                'today_low': float(today_low) if today_low is not None else 0,
                'today_volume': today_volume,
                'low_volume_flags': low_volume_flags,
                'pattern_flags': pattern_flags,
            }
            
        except Exception as e:
            logger.error(f"❌ 获取 {stock_code} 数据失败: {e}")
            return None
    
    def calculate_low_volume_flags(self, volume_series) -> Dict[str, bool]:
        """
        计算地量标志
        地量定义：当天成交量是N天内最低成交量（含当天）
        """
        if volume_series is None or len(volume_series) < 5:
            return {"5日地量": False, "10日地量": False, "20日地量": False, "30日地量": False, "60日地量": False}
        
        volumes = volume_series.tolist()
        today_volume = volumes[-1]
        result = {}
        
        for days, name in [(5, "5日地量"), (10, "10日地量"), (20, "20日地量"), (30, "30日地量"), (60, "60日地量")]:
            if len(volumes) >= days:
                recent_volumes = volumes[-days:]
                result[name] = today_volume <= min(recent_volumes)
            else:
                result[name] = False
        
        return result
    
    def calculate_pattern_flags(self, df) -> Dict[str, bool]:
        """计算形态标志"""
        if df is None or len(df) < 3:
            return {"底分型": False, "阳包阴": False}
        
        result = {}
        
        # 底分型判断：昨天是最低点，今天开始反弹
        low_2days_ago = df['Low'].iloc[-3]
        low_1day_ago = df['Low'].iloc[-2]
        low_today = df['Low'].iloc[-1]
        result["底分型"] = bool(low_1day_ago < low_2days_ago and low_1day_ago < low_today)
        
        # 阳包阴判断
        if len(df) >= 2:
            open_yesterday = df['Open'].iloc[-2]
            close_yesterday = df['Close'].iloc[-2]
            open_today = df['Open'].iloc[-1]
            close_today = df['Close'].iloc[-1]
            
            yesterday_yin = close_yesterday < open_yesterday
            today_yang = close_today > open_today
            result["阳包阴"] = bool(yesterday_yin and today_yang and open_today <= close_yesterday and close_today >= open_yesterday)
        else:
            result["阳包阴"] = False
        
        return result
    
    def calculate_score(self, low_volume_flags: Dict[str, bool], pattern_flags: Dict[str, bool]) -> int:
        """计算形态得分"""
        score = 0
        if low_volume_flags.get("5日地量"): score += 1
        if low_volume_flags.get("10日地量"): score += 1
        if low_volume_flags.get("20日地量"): score += 1
        if pattern_flags.get("底分型"): score += 2
        if pattern_flags.get("阳包阴"): score += 2
        return score
    
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
        """执行更新流程"""
        logger.info("=" * 80)
        logger.info("📊 第二阶段：更新最新数据并计算形态")
        logger.info("=" * 80)
        
        # 初始化
        try:
            self.init_tdx()
            self.init_feishu()
        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            return
        
        # 1. 从飞书表格读取所有股票
        records = self.get_all_stocks_from_bitable()
        if not records:
            logger.warning("⚠️ 没有获取到股票记录")
            return
        
        # 2. 更新每只股票
        logger.info(f"\n📈 开始更新 {len(records)} 只股票...")
        
        success_count = 0
        failed_count = 0
        
        for idx, record in enumerate(records, 1):
            parsed = self.parse_stock_record(record)
            stock_code = parsed["stock_code"]
            stock_name = parsed["stock_name"]
            record_id = parsed["record_id"]
            
            if not stock_code:
                continue
            
            # 获取今天数据和历史数据
            data = self.get_stock_data(stock_code)
            
            if data:
                # 计算突破
                breakout_high = data['today_close'] > parsed["pool_high"] if parsed["pool_high"] > 0 else False
                breakout_close = data['today_close'] > parsed["pool_close"] if parsed["pool_close"] > 0 else False
                
                # 计算得分
                score = self.calculate_score(data['low_volume_flags'], data['pattern_flags'])
                
                # 构建更新字段
                update_fields = {
                    "最新日期": self.today.strftime('%Y-%m-%d'),
                    "最新收盘价": data['today_close'],
                    "最新成交量": data['today_volume'],
                    "5日地量": data['low_volume_flags']["5日地量"],
                    "10日地量": data['low_volume_flags']["10日地量"],
                    "20日地量": data['low_volume_flags']["20日地量"],
                    "30日地量": data['low_volume_flags']["30日地量"],
                    "60日地量": data['low_volume_flags']["60日地量"],
                    "底分型": data['pattern_flags']["底分型"],
                    "阳包阴": data['pattern_flags']["阳包阴"],
                    "突破最高价": breakout_high,
                    "突破收盘价": breakout_close,
                    "形态得分": score,
                }
                
                # 更新记录
                if self.update_record_in_bitable(record_id, update_fields):
                    success_count += 1
                    if idx % 50 == 0:
                        logger.info(f"  [{idx}/{len(records)}] {stock_code} {stock_name}: 收盘{data['today_close']:.2f}, 得分{score}")
                else:
                    failed_count += 1
            else:
                logger.warning(f"  [{idx}/{len(records)}] {stock_code}: 无法获取数据")
            
            time.sleep(0.05)
        
        logger.info(f"\n✅ 更新完成: 成功 {success_count} 条，失败 {failed_count} 条")
        logger.info("=" * 80)


def main():
    """主函数"""
    updater = LatestDataUpdater()
    updater.run()


if __name__ == "__main__":
    main()
