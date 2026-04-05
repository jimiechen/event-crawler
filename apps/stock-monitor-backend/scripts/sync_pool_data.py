#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第一阶段：同步入池数据到飞书表格
- 从通达信自定义板块获取股票
- 从板块名称解析入池日期
- 获取入池日期当天的开盘价、最高价、收盘价、成交量
"""

import sys
import os
import time
import re
from datetime import date, datetime
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

import requests
from loguru import logger


class PoolDataSync:
    """入池数据同步器"""
    
    def __init__(self):
        self.tdx_client = None
        self.feishu_client = None
        
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
        
        logger.info(f"\n  共找到 {len(all_record_ids)} 条记录需要删除")
        
        deleted_count = 0
        failed_count = 0
        batch_size = 100
        
        for i in range(0, len(all_record_ids), batch_size):
            batch = all_record_ids[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(all_record_ids) + batch_size - 1) // batch_size
            
            logger.info(f"  删除第 {batch_num}/{total_batches} 批，{len(batch)} 条记录...")
            
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
                else:
                    failed_count += len(batch)
                    
            except Exception as e:
                failed_count += len(batch)
            
            time.sleep(0.3)
        
        logger.info(f"\n✅ 清空完成: 成功 {deleted_count} 条，失败 {failed_count} 条")
        return failed_count == 0
    
    def parse_date_from_sector_name(self, sector_name: str) -> Optional[date]:
        """
        从板块名称解析日期
        格式：中文前缀 + YYMMDD（如 "三倍量涨停260203" → 2026-02-03）
        """
        # 匹配末尾的6位数字（YYMMDD）
        match = re.search(r'(\d{6})$', sector_name)
        if match:
            date_str = match.group(1)
            try:
                # YYMMDD → 20YY-MM-DD
                year = 2000 + int(date_str[0:2])
                month = int(date_str[2:4])
                day = int(date_str[4:6])
                return date(year, month, day)
            except ValueError:
                return None
        return None
    
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
        
        try:
            stocks = self.tdx_client.get_stock_list_in_sector(sector_code)
            if stocks and len(stocks) > 0:
                return stocks
        except:
            pass
        
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
        except:
            pass
        
        return []
    
    def get_stock_name_from_tdx(self, stock_code_full: str) -> str:
        """从通达信获取股票名称"""
        try:
            info = self.tdx_client.get_stock_info(stock_code_full)
            if info and isinstance(info, dict):
                name = info.get('Name', '')
                if name:
                    return name
        except:
            pass
        return stock_code_full.split('.')[0] if '.' in stock_code_full else stock_code_full
    
    def get_pool_day_data(self, stock_code_full: str, pool_date: date) -> Optional[Dict[str, Any]]:
        """
        获取入池日期当天的数据
        
        Args:
            stock_code_full: 完整股票代码（如 000001.SZ）
            pool_date: 入池日期
            
        Returns:
            Dict: 入池当天的开盘价、最高价、收盘价、成交量
        """
        try:
            # 获取足够的历史数据（确保包含入池日期）
            # 从入池日期到今天的天数
            days_needed = (date(2026, 4, 3) - pool_date).days + 10
            
            data_dict = self.tdx_client.get_market_data(
                field_list=['Open', 'High', 'Low', 'Close', 'Volume'],
                stock_list=[stock_code_full],
                period='1d',
                count=days_needed,
                dividend_type='front',
                fill_data=True
            )
            
            close_df = data_dict.get('Close')
            if close_df is None or close_df.empty:
                return None
            
            # 找到入池日期对应的数据
            pool_date_str = pool_date.strftime('%Y-%m-%d')
            
            if pool_date_str in close_df.index:
                open_val = data_dict.get('Open').loc[pool_date_str, stock_code_full] if data_dict.get('Open') is not None else None
                high_val = data_dict.get('High').loc[pool_date_str, stock_code_full] if data_dict.get('High') is not None else None
                low_val = data_dict.get('Low').loc[pool_date_str, stock_code_full] if data_dict.get('Low') is not None else None
                close_val = close_df.loc[pool_date_str, stock_code_full]
                volume = data_dict.get('Volume').loc[pool_date_str, stock_code_full] if data_dict.get('Volume') is not None else None
                
                # 成交量转换为手
                volume = float(volume) / 100 if volume is not None else 0
                
                return {
                    'open': float(open_val) if open_val is not None else 0,
                    'high': float(high_val) if high_val is not None else 0,
                    'low': float(low_val) if low_val is not None else 0,
                    'close': float(close_val) if close_val is not None else 0,
                    'volume': volume,
                }
            else:
                logger.warning(f"  未找到 {stock_code_full} 在 {pool_date} 的数据")
                return None
                
        except Exception as e:
            logger.error(f"❌ 获取 {stock_code_full} 入池数据失败: {e}")
            return None
    
    def build_bitable_record(self, 
                             stock_code: str,
                             stock_name: str,
                             sector_name: str,
                             pool_date: date,
                             data: Dict[str, Any]) -> Dict[str, Any]:
        """构建飞书表格记录（仅入池数据）"""
        import time
        
        # 入池日期转为时间戳
        date_timestamp = int(time.mktime(pool_date.timetuple())) * 1000
        
        return {
            "股票代码": stock_code,
            "股票名称": stock_name,
            "入池日期": date_timestamp,
            "入池开盘价": float(data.get('open', 0)),
            "入池最高价": float(data.get('high', 0)),
            "入池收盘价": float(data.get('close', 0)),
            "成交量": float(data.get('volume', 0)),  # 使用现有字段
            "备注": f"板块:{sector_name},入池日期:{pool_date.strftime('%Y%m%d')}",
        }
    
    def sync_sector(self, sector_code: str, sector_name: str) -> List[Dict[str, Any]]:
        """同步单个板块"""
        # 解析入池日期
        pool_date = self.parse_date_from_sector_name(sector_name)
        if not pool_date:
            logger.warning(f"  ⚠️ 无法从板块名称解析日期: {sector_name}")
            return []
        
        logger.info(f"  📁 处理板块: {sector_name} ({sector_code}) - 入池日期: {pool_date}")
        
        stocks = self.get_stocks_in_sector(sector_code)
        if not stocks:
            logger.warning(f"    ⚠️ 板块为空")
            return []
        
        records = []
        
        for i, stock_code_full in enumerate(stocks, 1):
            try:
                code = stock_code_full.split('.')[0] if '.' in stock_code_full else stock_code_full
                
                # 获取股票名称
                stock_name = self.get_stock_name_from_tdx(stock_code_full)
                
                # 获取入池日期当天的数据
                data = self.get_pool_day_data(stock_code_full, pool_date)
                
                if data:
                    record = self.build_bitable_record(code, stock_name, sector_name, pool_date, data)
                    records.append(record)
                    logger.info(f"    [{i}/{len(stocks)}] {code} {stock_name}: 入池收盘{data['close']:.2f}, 日期{pool_date}")
                else:
                    logger.warning(f"    [{i}/{len(stocks)}] {code}: 无法获取入池数据")
                    
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
        """执行同步"""
        logger.info("=" * 80)
        logger.info("🗑️ 第一阶段：同步入池数据到飞书表格")
        logger.info("=" * 80)
        
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
            
            time.sleep(0.3)
        
        logger.info(f"\n📊 共收集 {len(all_records)} 条记录")
        
        # 4. 批量添加到飞书表格
        if all_records:
            self.add_records_to_bitable(all_records)
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ 第一阶段完成：入池数据同步完成")
        logger.info("=" * 80)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='同步入池数据到飞书表格')
    parser.add_argument('--filter', '-f', type=str, help='板块过滤条件（模糊匹配）')
    
    args = parser.parse_args()
    
    sync = PoolDataSync()
    sync.run(sector_filter=args.filter)


if __name__ == "__main__":
    main()
