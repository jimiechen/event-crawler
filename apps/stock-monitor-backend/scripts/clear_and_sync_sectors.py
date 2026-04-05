#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清空飞书多维表格，然后重新同步通达信自定义板块
只同步板块内的股票（约500多只），不是全量同步
"""

import sys
import os
import time
from datetime import date
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

import pandas as pd
import requests
from loguru import logger


class ClearAndSyncSectors:
    """清空并同步板块"""
    
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
    
    def clear_all_records(self) -> bool:
        """清空飞书多维表格所有记录"""
        logger.info("\n🗑️ 开始清空飞书多维表格...")
        
        access_token = self.feishu_client._get_access_token()
        if not access_token:
            logger.error("❌ 无法获取访问令牌")
            return False
        
        # 获取所有记录ID
        all_record_ids = []
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
                    for record in records:
                        all_record_ids.append(record.get("record_id"))
                    
                    logger.info(f"  获取到 {len(records)} 条记录，累计 {len(all_record_ids)} 条")
                    
                    has_more = result.get("data", {}).get("has_more", False)
                    if not has_more:
                        break
                    
                    page_token = result.get("data", {}).get("page_token")
                    if not page_token:
                        break
                else:
                    logger.error(f"❌ 查询记录失败: {result}")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ 查询记录异常: {e}")
                return False
        
        logger.info(f"\n  共找到 {len(all_record_ids)} 条记录需要删除")
        
        # 批量删除记录
        deleted_count = 0
        failed_count = 0
        batch_size = 100  # 飞书API限制每次最多删除100条
        
        for i in range(0, len(all_record_ids), batch_size):
            batch = all_record_ids[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(all_record_ids) + batch_size - 1) // batch_size
            
            logger.info(f"  删除第 {batch_num}/{total_batches} 批，{len(batch)} 条记录...")
            
            # 使用批量删除API
            url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.feishu_client.app_token}/tables/{self.feishu_client.table_id}/records/batch_delete"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            data = {"records": batch}
            
            try:
                response = requests.post(url, headers=headers, json=data, timeout=30)
                result = response.json()
                
                if result.get("code") == 0:
                    deleted_count += len(batch)
                    logger.info(f"    ✅ 删除成功: {len(batch)} 条")
                else:
                    failed_count += len(batch)
                    logger.error(f"    ❌ 删除失败: {result}")
                    
            except Exception as e:
                failed_count += len(batch)
                logger.error(f"    ❌ 删除异常: {e}")
            
            time.sleep(0.5)
        
        logger.info(f"\n✅ 清空完成: 成功 {deleted_count} 条，失败 {failed_count} 条")
        return failed_count == 0
    
    def get_user_sectors(self) -> List[Dict[str, str]]:
        """获取通达信用户自定义板块列表"""
        try:
            sectors = self.tdx_client.get_user_sector()
            logger.info(f"✅ 获取到 {len(sectors)} 个自定义板块")
            return sectors
        except Exception as e:
            logger.error(f"❌ 获取板块列表失败: {e}")
            return []
    
    def get_stocks_in_sector(self, sector_code: str) -> List[str]:
        """获取板块内的股票列表"""
        stocks = []
        
        # 方法1: 尝试API获取
        try:
            stocks = self.tdx_client.get_stock_list_in_sector(sector_code)
            if stocks and len(stocks) > 0:
                return stocks
        except Exception as e:
            pass
        
        # 方法2: 直接读取板块文件
        try:
            block_file = rf"C:\new_tdx_test\T0002\blocknew\{sector_code}.blk"
            if os.path.exists(block_file):
                with open(block_file, 'r', encoding='gbk', errors='ignore') as f:
                    lines = f.readlines()
                
                for line in lines:
                    code = line.strip()
                    if not code:
                        continue
                    
                    if code.startswith('1'):
                        stock_code = f"{code[1:]}.SH"
                    elif code.startswith('0'):
                        stock_code = f"{code[1:]}.SZ"
                    else:
                        continue
                    
                    stocks.append(stock_code)
                
                if stocks:
                    return stocks
        except Exception as e:
            pass
        
        return []
    
    def get_stock_data(self, stock_code_full: str) -> Optional[Dict[str, Any]]:
        """获取股票数据"""
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
            
            # 计算地量
            volume_series = data_dict.get('Volume')[stock_code_full] if data_dict.get('Volume') is not None else None
            low_volume_flags = self.calculate_low_volume_flags(volume_series)
            
            # 计算形态
            df_data = {
                'Open': data_dict.get('Open')[stock_code_full] if data_dict.get('Open') is not None else None,
                'High': data_dict.get('High')[stock_code_full] if data_dict.get('High') is not None else None,
                'Low': data_dict.get('Low')[stock_code_full] if data_dict.get('Low') is not None else None,
                'Close': close_df[stock_code_full],
                'Volume': data_dict.get('Volume')[stock_code_full] if data_dict.get('Volume') is not None else None,
            }
            df = pd.DataFrame(df_data)
            df.index = close_df.index
            df['Volume'] = df['Volume'] / 100
            
            pattern_flags = self.calculate_pattern_flags(df)
            
            return {
                'open': float(open_val) if open_val is not None else 0,
                'high': float(high_val) if high_val is not None else 0,
                'low': float(low_val) if low_val is not None else 0,
                'close': float(close_val) if close_val is not None else 0,
                'volume': volume,
                'date': latest_date_idx,
                'low_volume_flags': low_volume_flags,
                'pattern_flags': pattern_flags
            }
            
        except Exception as e:
            logger.error(f"❌ 获取 {stock_code_full} 数据失败: {e}")
            return None
    
    def calculate_low_volume_flags(self, volume_series) -> Dict[str, bool]:
        """
        计算地量标志
        地量定义：当天成交量是N天内最低成交量（含当天）
        """
        if volume_series is None or len(volume_series) < 2:
            return {"5日地量": False, "10日地量": False, "20日地量": False, "30日地量": False, "60日地量": False}
        
        volumes = volume_series.tolist()
        latest_volume = volumes[-1]  # 当天成交量（股）
        result = {}
        
        for days, name in [(5, "5日地量"), (10, "10日地量"), (20, "20日地量"), (30, "30日地量"), (60, "60日地量")]:
            if len(volumes) >= days:
                # 取最近N天（含当天）
                recent_volumes = volumes[-days:]
                # 当天成交量是否是N天内最低
                result[name] = latest_volume <= min(recent_volumes)
            else:
                result[name] = False
        
        return result
    
    def calculate_pattern_flags(self, df) -> Dict[str, bool]:
        """计算形态标志"""
        if df is None or len(df) < 3:
            return {"底分型": False, "阳包阴": False}
        
        result = {}
        
        low_2days_ago = df['Low'].iloc[-3]
        low_1day_ago = df['Low'].iloc[-2]
        low_today = df['Low'].iloc[-1]
        result["底分型"] = bool(low_1day_ago < low_2days_ago and low_1day_ago < low_today)
        
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
    
    def build_bitable_record(self, 
                             stock_code: str,
                             stock_name: str,
                             sector_name: str,
                             data: Dict[str, Any]) -> Dict[str, Any]:
        """构建飞书表格记录"""
        import time
        
        date_timestamp = int(time.mktime(self.today.timetuple())) * 1000
        low_volume_flags = data.get('low_volume_flags', {})
        pattern_flags = data.get('pattern_flags', {})
        
        score = 0
        if low_volume_flags.get("5日地量"): score += 1
        if low_volume_flags.get("10日地量"): score += 1
        if low_volume_flags.get("20日地量"): score += 1
        if pattern_flags.get("底分型"): score += 2
        if pattern_flags.get("阳包阴"): score += 2
        
        return {
            "股票代码": stock_code,
            "股票名称": stock_name,
            "入池日期": date_timestamp,
            "入池开盘价": float(data.get('open', 0)),
            "入池收盘价": float(data.get('close', 0)),
            "入池最高价": float(data.get('high', 0)),
            "最新日期": self.today.strftime('%Y-%m-%d'),
            "最新收盘价": float(data.get('close', 0)),
            "最新成交量": float(data.get('volume', 0)),
            "成交量": float(data.get('volume', 0)),
            "3倍量确认": True,
            "5日地量": bool(low_volume_flags.get("5日地量", False)),
            "10日地量": bool(low_volume_flags.get("10日地量", False)),
            "20日地量": bool(low_volume_flags.get("20日地量", False)),
            "30日地量": bool(low_volume_flags.get("30日地量", False)),
            "60日地量": bool(low_volume_flags.get("60日地量", False)),
            "突破最高价": False,
            "突破收盘价": False,
            "突破告警": False,
            "底分型": bool(pattern_flags.get("底分型", False)),
            "阳包阴": bool(pattern_flags.get("阳包阴", False)),
            "形态得分": int(score),
            "备注": f"板块:{sector_name}, 收盘:{data.get('close', 0):.2f}, 得分:{score}"
        }
    
    def get_stock_name_from_tdx(self, stock_code_full: str) -> str:
        """从通达信获取股票名称"""
        try:
            # 使用get_stock_info获取股票名称
            info = self.tdx_client.get_stock_info(stock_code_full)
            if info and isinstance(info, dict):
                name = info.get('Name', '')
                if name:
                    return name
        except Exception as e:
            logger.debug(f"获取股票名称失败 {stock_code_full}: {e}")
        
        # 如果失败，返回代码
        return stock_code_full.split('.')[0] if '.' in stock_code_full else stock_code_full
    
    def sync_sector(self, sector_code: str, sector_name: str) -> List[Dict[str, Any]]:
        """同步单个板块，返回记录列表"""
        logger.info(f"  📁 处理板块: {sector_name} ({sector_code})")
        
        stocks = self.get_stocks_in_sector(sector_code)
        if not stocks:
            logger.warning(f"    ⚠️ 板块为空")
            return []
        
        records = []
        
        for i, stock_code_full in enumerate(stocks, 1):
            try:
                code = stock_code_full.split('.')[0] if '.' in stock_code_full else stock_code_full
                
                # 获取股票数据
                data = self.get_stock_data(stock_code_full)
                
                # 获取股票名称
                stock_name = self.get_stock_name_from_tdx(stock_code_full)
                
                if data:
                    record = self.build_bitable_record(code, stock_name, sector_name, data)
                    records.append(record)
                    logger.info(f"    [{i}/{len(stocks)}] {code} {stock_name}: 收盘{data['close']:.2f}")
                else:
                    logger.warning(f"    [{i}/{len(stocks)}] {code}: 无法获取数据")
                    
            except Exception as e:
                logger.error(f"    [{i}/{len(stocks)}] {code}: 处理失败 {e}")
                continue
        
        logger.info(f"    ✅ 板块 {sector_name} 共 {len(records)} 条记录")
        return records
    
    def add_records_to_bitable(self, records: List[Dict[str, Any]]) -> bool:
        """批量添加记录到飞书表格"""
        if not records:
            return True
        
        logger.info(f"\n📤 添加 {len(records)} 条记录到飞书表格...")
        
        result = self.feishu_client.add_records_to_bitable(records)
        
        if result.get("status") == "success":
            logger.info(f"✅ 添加成功: {len(records)} 条记录")
            return True
        else:
            logger.error(f"❌ 添加失败: {result}")
            return False
    
    def run(self, sector_filter: Optional[str] = None):
        """执行清空并同步"""
        logger.info("=" * 80)
        logger.info("🗑️ 清空并重新同步通达信板块到飞书多维表格")
        logger.info("=" * 80)
        logger.info(f"📅 同步日期: {self.today}")
        if sector_filter:
            logger.info(f"🔍 板块过滤: {sector_filter}")
        logger.info("")
        
        # 初始化
        try:
            self.init_tdx()
            self.init_feishu()
        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            return
        
        # 1. 清空表格
        if not self.clear_all_records():
            logger.warning("⚠️ 清空表格失败，继续同步...")
        
        logger.info("\n" + "=" * 80)
        
        # 2. 获取板块列表
        sectors = self.get_user_sectors()
        if not sectors:
            logger.warning("⚠️ 没有获取到板块")
            return
        
        # 过滤板块
        if sector_filter:
            sectors = [s for s in sectors if sector_filter.lower() in s.get('Name', '').lower()]
            logger.info(f"🔍 过滤后剩余 {len(sectors)} 个板块")
        
        # 3. 收集所有记录
        all_records = []
        
        for sector in sectors:
            sector_code = sector.get('Code', '')
            sector_name = sector.get('Name', '')
            
            if not sector_code or not sector_name:
                continue
            
            records = self.sync_sector(sector_code, sector_name)
            all_records.extend(records)
            
            time.sleep(0.5)
        
        logger.info(f"\n📊 共收集 {len(all_records)} 条记录")
        
        # 4. 批量添加到飞书表格
        if all_records:
            self.add_records_to_bitable(all_records)
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ 同步完成")
        logger.info("=" * 80)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='清空并同步通达信板块到飞书多维表格')
    parser.add_argument('--filter', '-f', type=str, help='板块过滤条件（模糊匹配）')
    
    args = parser.parse_args()
    
    sync = ClearAndSyncSectors()
    sync.run(sector_filter=args.filter)


if __name__ == "__main__":
    main()
