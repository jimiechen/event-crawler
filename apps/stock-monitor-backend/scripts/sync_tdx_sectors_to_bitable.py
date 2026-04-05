#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
读取通达信自定义板块，同步板块内的所有股票到飞书多维表格
按照板块名称区分
"""

import sys
import os
import time
from datetime import date, datetime
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

import pandas as pd
from loguru import logger


class TdxSectorSync:
    """通达信板块同步器"""
    
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
    
    def get_user_sectors(self) -> List[Dict[str, str]]:
        """
        获取通达信用户自定义板块列表
        
        Returns:
            List[Dict]: 板块列表，每个板块包含 Code 和 Name
        """
        try:
            sectors = self.tdx_client.get_user_sector()
            logger.info(f"✅ 获取到 {len(sectors)} 个自定义板块")
            for sector in sectors:
                logger.info(f"  - {sector.get('Code')}: {sector.get('Name')}")
            return sectors
        except Exception as e:
            logger.error(f"❌ 获取板块列表失败: {e}")
            return []
    
    def get_stocks_in_sector(self, sector_code: str) -> List[str]:
        """
        获取板块内的股票列表
        首先尝试API获取，如果失败则直接读取板块文件
        
        Args:
            sector_code: 板块代码
            
        Returns:
            List[str]: 股票代码列表（通达信格式）
        """
        stocks = []
        
        # 方法1: 尝试API获取
        try:
            stocks = self.tdx_client.get_stock_list_in_sector(sector_code)
            if stocks and len(stocks) > 0:
                logger.info(f"  板块 {sector_code} 包含 {len(stocks)} 只股票 (API)")
                return stocks
        except Exception as e:
            logger.debug(f"API获取板块股票失败: {e}")
        
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
                    
                    # 转换格式
                    if code.startswith('1'):
                        # 沪市
                        stock_code = f"{code[1:]}.SH"
                    elif code.startswith('0'):
                        # 深市
                        stock_code = f"{code[1:]}.SZ"
                    else:
                        continue
                    
                    stocks.append(stock_code)
                
                if stocks:
                    logger.info(f"  板块 {sector_code} 包含 {len(stocks)} 只股票 (文件)")
                    return stocks
            else:
                logger.debug(f"板块文件不存在: {block_file}")
        except Exception as e:
            logger.debug(f"读取板块文件失败: {e}")
        
        logger.warning(f"  板块 {sector_code} 没有股票")
        return []
    
    def get_stock_name(self, stock_code: str) -> str:
        """
        获取股票名称
        
        Args:
            stock_code: 股票代码（如 000001.SZ）
            
        Returns:
            str: 股票名称
        """
        try:
            info = self.tdx_client.get_more_info(stock_code)
            if info and len(info) > 0:
                return info[0].get('Name', stock_code)
        except Exception as e:
            logger.warning(f"获取股票名称失败 {stock_code}: {e}")
        return stock_code
    
    def get_stock_data(self, stock_code_full: str) -> Optional[Dict[str, Any]]:
        """
        获取股票最新数据
        
        Args:
            stock_code_full: 完整股票代码（如 000001.SZ）
            
        Returns:
            Dict: 股票数据，包含价格、成交量等
        """
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
            
            # 获取最新日期和数据
            latest_date_idx = close_df.index[-1]
            
            close_val = close_df.loc[latest_date_idx, stock_code_full]
            open_val = data_dict.get('Open').loc[latest_date_idx, stock_code_full] if data_dict.get('Open') is not None else None
            high_val = data_dict.get('High').loc[latest_date_idx, stock_code_full] if data_dict.get('High') is not None else None
            low_val = data_dict.get('Low').loc[latest_date_idx, stock_code_full] if data_dict.get('Low') is not None else None
            volume = data_dict.get('Volume').loc[latest_date_idx, stock_code_full] if data_dict.get('Volume') is not None else None
            amount = data_dict.get('Amount').loc[latest_date_idx, stock_code_full] if data_dict.get('Amount') is not None else None
            
            # 单位转换
            volume = float(volume) / 100 if volume is not None else 0  # 股 → 手
            amount = float(amount) / 1000 if amount is not None else 0  # 元 → 千元
            
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
                'amount': amount,
                'date': latest_date_idx,
                'low_volume_flags': low_volume_flags,
                'pattern_flags': pattern_flags
            }
            
        except Exception as e:
            logger.error(f"❌ 获取 {stock_code_full} 数据失败: {e}")
            return None
    
    def calculate_low_volume_flags(self, volume_series) -> Dict[str, bool]:
        """计算地量标志"""
        if volume_series is None or len(volume_series) < 2:
            return {"5日地量": False, "10日地量": False, "20日地量": False, "30日地量": False, "60日地量": False}
        
        volumes = volume_series.tolist()
        latest_volume = volumes[-1] / 100  # 转换为手
        result = {}
        
        for days, name in [(5, "5日地量"), (10, "10日地量"), (20, "20日地量"), (30, "30日地量"), (60, "60日地量")]:
            if len(volumes) >= days + 1:
                past_volumes = [v / 100 for v in volumes[-(days+1):-1]]  # 转换为手
                avg_volume = sum(past_volumes) / len(past_volumes)
                result[name] = latest_volume < avg_volume * 0.8
            else:
                result[name] = False
        
        return result
    
    def calculate_pattern_flags(self, df) -> Dict[str, bool]:
        """计算形态标志"""
        if df is None or len(df) < 3:
            return {"底分型": False, "阳包阴": False}
        
        result = {}
        
        # 底分型判断
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
    
    def build_bitable_record(self, 
                             stock_code: str,
                             stock_name: str,
                             sector_name: str,
                             data: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建飞书表格记录
        
        Args:
            stock_code: 股票代码（纯数字）
            stock_name: 股票名称
            sector_name: 板块名称
            data: 股票数据
            
        Returns:
            Dict: 飞书表格记录
        """
        import time
        
        date_timestamp = int(time.mktime(self.today.timetuple())) * 1000
        low_volume_flags = data.get('low_volume_flags', {})
        pattern_flags = data.get('pattern_flags', {})
        
        # 计算形态得分
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
            "突破最高价": False,  # 首次入池，无突破判断
            "突破收盘价": False,
            "突破告警": False,
            "底分型": bool(pattern_flags.get("底分型", False)),
            "阳包阴": bool(pattern_flags.get("阳包阴", False)),
            "形态得分": int(score),
            "备注": f"板块:{sector_name}, 收盘:{data.get('close', 0):.2f}, 得分:{score}"
        }
    
    def sync_sector_to_bitable(self, sector_code: str, sector_name: str) -> Dict[str, int]:
        """
        同步单个板块到飞书表格
        
        Args:
            sector_code: 板块代码
            sector_name: 板块名称
            
        Returns:
            Dict: 同步统计
        """
        logger.info(f"\n📁 同步板块: {sector_name} ({sector_code})")
        
        # 获取板块内股票
        stocks = self.get_stocks_in_sector(sector_code)
        if not stocks:
            logger.warning(f"  板块 {sector_name} 没有股票")
            return {"total": 0, "success": 0, "failed": 0}
        
        # 准备记录
        records = []
        
        for i, stock_code_full in enumerate(stocks, 1):
            try:
                # 提取纯代码
                code = stock_code_full.split('.')[0] if '.' in stock_code_full else stock_code_full
                
                logger.info(f"  [{i}/{len(stocks)}] 处理 {code}...")
                
                # 获取股票名称
                stock_name = self.get_stock_name(stock_code_full)
                
                # 获取股票数据
                data = self.get_stock_data(stock_code_full)
                
                if data:
                    # 构建记录
                    record = self.build_bitable_record(code, stock_name, sector_name, data)
                    records.append(record)
                    logger.info(f"    ✅ {stock_name}: 收盘{data['close']:.2f}")
                else:
                    logger.warning(f"    ⚠️ 无法获取数据")
                    
            except Exception as e:
                logger.error(f"    ❌ 处理失败: {e}")
                continue
        
        # 批量添加到飞书表格
        if records:
            logger.info(f"\n  📤 添加 {len(records)} 条记录到飞书表格...")
            result = self.feishu_client.add_records_to_bitable(records)
            
            if result.get("status") == "success":
                logger.info(f"  ✅ 同步成功: {len(records)} 条记录")
                return {"total": len(records), "success": len(records), "failed": 0}
            else:
                logger.error(f"  ❌ 同步失败: {result}")
                return {"total": len(records), "success": 0, "failed": len(records)}
        else:
            logger.warning(f"  ⚠️ 没有记录需要同步")
            return {"total": 0, "success": 0, "failed": 0}
    
    def run(self, sector_filter: Optional[str] = None):
        """
        执行同步
        
        Args:
            sector_filter: 板块过滤条件（可选，支持模糊匹配）
        """
        logger.info("=" * 80)
        logger.info("📊 通达信板块同步到飞书多维表格")
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
        
        # 获取板块列表
        sectors = self.get_user_sectors()
        if not sectors:
            logger.warning("⚠️ 没有获取到板块")
            return
        
        # 过滤板块
        if sector_filter:
            sectors = [s for s in sectors if sector_filter.lower() in s.get('Name', '').lower()]
            logger.info(f"🔍 过滤后剩余 {len(sectors)} 个板块")
        
        # 同步每个板块
        total_stats = {"total": 0, "success": 0, "failed": 0}
        
        for sector in sectors:
            sector_code = sector.get('Code', '')
            sector_name = sector.get('Name', '')
            
            if not sector_code or not sector_name:
                continue
            
            # 同步板块
            stats = self.sync_sector_to_bitable(sector_code, sector_name)
            
            total_stats["total"] += stats["total"]
            total_stats["success"] += stats["success"]
            total_stats["failed"] += stats["failed"]
            
            # 板块间延迟
            time.sleep(1)
        
        # 汇总
        logger.info("\n" + "=" * 80)
        logger.info("📊 同步完成汇总")
        logger.info("=" * 80)
        logger.info(f"  总计: {total_stats['total']}")
        logger.info(f"  成功: {total_stats['success']}")
        logger.info(f"  失败: {total_stats['failed']}")
        logger.info("=" * 80)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='同步通达信板块到飞书多维表格')
    parser.add_argument('--filter', '-f', type=str, help='板块过滤条件（模糊匹配）')
    
    args = parser.parse_args()
    
    sync = TdxSectorSync()
    sync.run(sector_filter=args.filter)


if __name__ == "__main__":
    main()