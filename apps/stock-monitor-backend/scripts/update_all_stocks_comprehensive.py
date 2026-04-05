#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面更新飞书多维表格所有股票数据
- 更新最新日期、收盘价、成交量
- 计算地量判断（5/10/20/30/60日）
- 计算形态判断（突破最高价、突破收盘价、底分型、阳包阴）
- 支持批量更新所有记录（解决9条限制）
"""

import sys
import os
import time
from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, r"C:\new_tdx_test\PYPlugins\user")

import pandas as pd
from loguru import logger


class ComprehensiveStockUpdater:
    """全面股票数据更新器"""
    
    def __init__(self):
        self.tdx_client = None
        self.feishu_client = None
        self.today = date(2026, 4, 3)
        self.today_timestamp = int(time.mktime(self.today.timetuple())) * 1000
        
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
    
    def get_all_records_from_bitable(self) -> List[Dict[str, Any]]:
        """
        从飞书多维表格获取所有记录
        处理分页，获取全部记录
        """
        logger.info("📥 从飞书多维表格获取所有记录...")
        
        access_token = self.feishu_client._get_access_token()
        if not access_token:
            logger.error("❌ 无法获取访问令牌")
            return []
        
        import requests
        
        all_records = []
        page_token = None
        page_size = 500  # 每页最大500条
        
        while True:
            url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.feishu_client.app_token}/tables/{self.feishu_client.table_id}/records/search"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "page_size": page_size
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
                    
                    # 检查是否有更多数据
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
        
        logger.info(f"✅ 共获取 {len(all_records)} 条记录")
        return all_records
    
    def get_stock_history_data(self, stock_code_full: str, days: int = 60) -> Optional[Any]:
        """
        从通达信获取股票历史数据
        
        Args:
            stock_code_full: 完整股票代码（如 002361.SZ）
            days: 获取天数
            
        Returns:
            DataFrame: 包含历史数据的DataFrame，或None
        """
        try:
            import pandas as pd
            
            # 获取日线数据
            data_dict = self.tdx_client.get_market_data(
                field_list=['Open', 'High', 'Low', 'Close', 'Volume', 'Amount'],
                stock_list=[stock_code_full],
                period='1d',
                count=days,
                dividend_type='front',
                fill_data=True
            )
            
            # 构建DataFrame
            close_df = data_dict.get('Close')
            if close_df is None or close_df.empty:
                return None
            
            # 构建完整DataFrame
            df_data = {
                'Open': data_dict.get('Open')[stock_code_full] if data_dict.get('Open') is not None else None,
                'High': data_dict.get('High')[stock_code_full] if data_dict.get('High') is not None else None,
                'Low': data_dict.get('Low')[stock_code_full] if data_dict.get('Low') is not None else None,
                'Close': close_df[stock_code_full],
                'Volume': data_dict.get('Volume')[stock_code_full] if data_dict.get('Volume') is not None else None,
                'Amount': data_dict.get('Amount')[stock_code_full] if data_dict.get('Amount') is not None else None,
            }
            
            df = pd.DataFrame(df_data)
            df.index = close_df.index
            
            # 单位转换
            df['Volume'] = df['Volume'] / 100  # 股 → 手
            df['Amount'] = df['Amount'] / 1000  # 元 → 千元
            
            return df
            
        except Exception as e:
            logger.error(f"❌ 获取 {stock_code_full} 历史数据失败: {e}")
            return None
    
    def calculate_low_volume_flags(self, volumes: List[float]) -> Dict[str, bool]:
        """
        计算地量标志
        
        地量定义：当日成交量 < 过去N日平均成交量 * 0.8
        
        Args:
            volumes: 成交量列表（从旧到新）
            
        Returns:
            Dict: 各周期地量标志
        """
        if not volumes or len(volumes) < 2:
            return {
                "5日地量": False,
                "10日地量": False,
                "20日地量": False,
                "30日地量": False,
                "60日地量": False
            }
        
        latest_volume = volumes[-1]
        result = {}
        
        for days, name in [
            (5, "5日地量"),
            (10, "10日地量"),
            (20, "20日地量"),
            (30, "30日地量"),
            (60, "60日地量")
        ]:
            if len(volumes) >= days + 1:  # 需要N日历史+当日
                # 取过去N日（不含当日）
                past_volumes = volumes[-(days+1):-1]
                avg_volume = sum(past_volumes) / len(past_volumes)
                result[name] = latest_volume < avg_volume * 0.8
            else:
                result[name] = False
        
        return result
    
    def calculate_pattern_flags(self, df: Any) -> Dict[str, Any]:
        """
        计算形态标志
        
        Args:
            df: 股票历史数据DataFrame
            
        Returns:
            Dict: 形态判断结果
        """
        if df is None or len(df) < 3:
            return {
                "底分型": False,
                "阳包阴": False
            }
        
        result = {}
        
        # 底分型判断
        # 定义：中间K线的最低点低于左右两根K线的最低点
        if len(df) >= 3:
            low_2days_ago = df['Low'].iloc[-3]
            low_1day_ago = df['Low'].iloc[-2]
            low_today = df['Low'].iloc[-1]
            
            # 底分型：昨天是最低点，今天开始反弹
            result["底分型"] = low_1day_ago < low_2days_ago and low_1day_ago < low_today
        else:
            result["底分型"] = False
        
        # 阳包阴判断
        # 定义：今日阳线完全包含昨日阴线（开盘价低于昨日收盘价，收盘价高于昨日开盘价）
        if len(df) >= 2:
            open_yesterday = df['Open'].iloc[-2]
            close_yesterday = df['Close'].iloc[-2]
            open_today = df['Open'].iloc[-1]
            close_today = df['Close'].iloc[-1]
            
            # 昨日是阴线（收盘 < 开盘），今日是阳线（收盘 > 开盘）
            yesterday_yin = close_yesterday < open_yesterday
            today_yang = close_today > open_today
            
            # 阳包阴：今日阳线实体包含昨日阴线实体
            result["阳包阴"] = yesterday_yin and today_yang and \
                              open_today <= close_yesterday and close_today >= open_yesterday
        else:
            result["阳包阴"] = False
        
        return result
    
    def calculate_breakout_flags(self, 
                                  latest_close: float,
                                  pool_high: float,
                                  pool_close: float) -> Dict[str, Any]:
        """
        计算突破标志
        
        Args:
            latest_close: 最新收盘价
            pool_high: 入池最高价
            pool_close: 入池收盘价
            
        Returns:
            Dict: 突破判断结果
        """
        result = {}
        
        # 突破最高价：最新收盘价 > 入池最高价
        result["突破最高价"] = latest_close > pool_high if pool_high > 0 else False
        
        # 突破收盘价：最新收盘价 > 入池收盘价
        result["突破收盘价"] = latest_close > pool_close if pool_close > 0 else False
        
        # 突破告警：突破最高价且涨幅超过3%
        if pool_close > 0:
            change_pct = (latest_close - pool_close) / pool_close * 100
            result["突破告警"] = result["突破最高价"] and change_pct > 3
        else:
            result["突破告警"] = False
        
        return result
    
    def parse_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析飞书记录，提取关键字段
        飞书文本字段返回的是列表格式，需要取第一个元素
        """
        fields = record.get("fields", {})
        record_id = record.get("record_id", "")
        
        # 解析股票代码（文本字段返回列表）
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
        pool_date = fields.get("入池日期", None)
        pool_open = fields.get("入池开盘价", 0)
        pool_close = fields.get("入池收盘价", 0)
        pool_high = fields.get("入池最高价", 0)
        
        # 如果入池数据为空，尝试从其他字段获取
        if pool_close == 0:
            pool_close = fields.get("收盘价", 0)
        if pool_high == 0:
            pool_high = fields.get("最高价", 0)
        
        return {
            "record_id": record_id,
            "stock_code": stock_code,
            "stock_name": stock_name,
            "pool_date": pool_date,
            "pool_open": float(pool_open) if pool_open else 0,
            "pool_close": float(pool_close) if pool_close else 0,
            "pool_high": float(pool_high) if pool_high else 0,
            "fields": fields
        }
    
    def build_update_record(self, 
                           parsed: Dict[str, Any],
                           df: Any) -> Optional[Dict[str, Any]]:
        """
        构建更新记录
        
        Args:
            parsed: 解析后的记录数据
            df: 股票历史数据
            
        Returns:
            Dict: 更新记录，或None
        """
        if df is None or len(df) == 0:
            return None
        
        # 获取最新数据
        latest_close = float(df['Close'].iloc[-1])
        latest_volume = float(df['Volume'].iloc[-1])
        latest_high = float(df['High'].iloc[-1])
        latest_low = float(df['Low'].iloc[-1])
        latest_open = float(df['Open'].iloc[-1])
        
        # 获取历史成交量列表
        volumes = df['Volume'].tolist()
        
        # 计算地量标志
        low_volume_flags = self.calculate_low_volume_flags(volumes)
        
        # 计算形态标志
        pattern_flags = self.calculate_pattern_flags(df)
        
        # 计算突破标志
        breakout_flags = self.calculate_breakout_flags(
            latest_close,
            parsed["pool_high"],
            parsed["pool_close"]
        )
        
        # 计算形态得分
        score = 0
        if low_volume_flags["5日地量"]:
            score += 1
        if low_volume_flags["10日地量"]:
            score += 1
        if low_volume_flags["20日地量"]:
            score += 1
        if pattern_flags["底分型"]:
            score += 2
        if pattern_flags["阳包阴"]:
            score += 2
        if breakout_flags["突破最高价"]:
            score += 3
        if breakout_flags["突破收盘价"]:
            score += 1
        
        # 构建更新记录（将numpy类型转换为Python原生类型）
        def to_bool(val):
            """转换为Python原生bool"""
            return bool(val) if val is not None else False
        
        def to_float(val):
            """转换为Python原生float"""
            return float(val) if val is not None else 0.0
        
        # 最新日期字段是文本类型，不是日期类型，需要格式化为字符串
        date_str = self.today.strftime('%Y-%m-%d')
        
        update_record = {
            "record_id": parsed["record_id"],
            "fields": {
                "最新日期": date_str,  # 文本格式日期
                "最新收盘价": to_float(latest_close),
                "最新成交量": to_float(latest_volume),
                "5日地量": to_bool(low_volume_flags["5日地量"]),
                "10日地量": to_bool(low_volume_flags["10日地量"]),
                "20日地量": to_bool(low_volume_flags["20日地量"]),
                "30日地量": to_bool(low_volume_flags["30日地量"]),
                "60日地量": to_bool(low_volume_flags["60日地量"]),
                "突破最高价": to_bool(breakout_flags["突破最高价"]),
                "突破收盘价": to_bool(breakout_flags["突破收盘价"]),
                "突破告警": to_bool(breakout_flags["突破告警"]),
                "底分型": to_bool(pattern_flags["底分型"]),
                "阳包阴": to_bool(pattern_flags["阳包阴"]),
                "形态得分": int(score),
                "备注": f"更新于{self.today.strftime('%m%d')}, 收盘:{to_float(latest_close):.2f}, 最高:{to_float(latest_high):.2f}, 最低:{to_float(latest_low):.2f}, 得分:{int(score)}"
            }
        }
        
        return update_record
    
    def update_record_in_bitable(self, record_id: str, fields: Dict[str, Any]) -> bool:
        """
        更新单条记录到飞书多维表格
        
        Args:
            record_id: 记录ID
            fields: 字段数据
            
        Returns:
            bool: 是否成功
        """
        access_token = self.feishu_client._get_access_token()
        if not access_token:
            return False
        
        import requests
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.feishu_client.app_token}/tables/{self.feishu_client.table_id}/records/{record_id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "fields": fields
        }
        
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
    
    def update_records_batch(self, records: List[Dict[str, Any]], batch_size: int = 9) -> Dict[str, int]:
        """
        批量更新记录
        
        飞书API限制：batch_update 一次最多9条记录
        所以需要分批处理
        
        Args:
            records: 记录列表
            batch_size: 每批大小（默认9，飞书限制）
            
        Returns:
            Dict: 统计结果
        """
        total = len(records)
        success_count = 0
        failed_count = 0
        
        logger.info(f"📝 开始批量更新 {total} 条记录，每批 {batch_size} 条...")
        
        for i in range(0, total, batch_size):
            batch = records[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size
            
            logger.info(f"  处理第 {batch_num}/{total_batches} 批，{len(batch)} 条记录...")
            
            for record in batch:
                record_id = record["record_id"]
                fields = record["fields"]
                
                if self.update_record_in_bitable(record_id, fields):
                    success_count += 1
                    logger.debug(f"    ✅ 更新成功: {record_id}")
                else:
                    failed_count += 1
                    logger.warning(f"    ❌ 更新失败: {record_id}")
                
                # 添加短暂延迟，避免API限流
                time.sleep(0.1)
            
            # 每批之间添加延迟
            if i + batch_size < total:
                time.sleep(0.5)
        
        return {
            "total": total,
            "success": success_count,
            "failed": failed_count
        }
    
    def run(self):
        """执行全面更新"""
        logger.info("=" * 80)
        logger.info("📊 全面更新飞书多维表格股票数据")
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
        
        # 获取所有记录
        records = self.get_all_records_from_bitable()
        if not records:
            logger.warning("⚠️ 没有获取到记录")
            return
        
        # 准备更新数据
        update_records = []
        
        logger.info(f"\n📈 开始处理 {len(records)} 只股票...")
        logger.info("")
        
        for idx, record in enumerate(records, 1):
            parsed = self.parse_record(record)
            stock_code = parsed["stock_code"]
            stock_name = parsed["stock_name"]
            
            if not stock_code:
                logger.warning(f"  [{idx}/{len(records)}] 跳过：股票代码为空")
                continue
            
            # 转换股票代码格式
            if stock_code.startswith('6'):
                stock_code_full = f"{stock_code}.SH"
            else:
                stock_code_full = f"{stock_code}.SZ"
            
            logger.info(f"  [{idx}/{len(records)}] 处理 {stock_code} {stock_name}...")
            
            # 获取历史数据
            df = self.get_stock_history_data(stock_code_full, days=60)
            
            if df is None:
                logger.warning(f"    ⚠️ 无法获取数据")
                continue
            
            # 构建更新记录
            update_record = self.build_update_record(parsed, df)
            
            if update_record:
                update_records.append(update_record)
                flags = update_record["fields"]
                logger.info(f"    ✅ 收盘:{flags['最新收盘价']:.2f}, 5日地量:{flags['5日地量']}, 突破最高:{flags['突破最高价']}, 底分型:{flags['底分型']}, 得分:{flags['形态得分']}")
            else:
                logger.warning(f"    ⚠️ 无法构建更新记录")
        
        logger.info("")
        logger.info(f"📊 共准备 {len(update_records)} 条更新记录")
        logger.info("")
        
        # 批量更新
        if update_records:
            result = self.update_records_batch(update_records, batch_size=9)
            
            logger.info("")
            logger.info("=" * 80)
            logger.info("📊 更新结果统计")
            logger.info("=" * 80)
            logger.info(f"  总计: {result['total']}")
            logger.info(f"  成功: {result['success']}")
            logger.info(f"  失败: {result['failed']}")
            logger.info("=" * 80)
        else:
            logger.warning("⚠️ 没有需要更新的记录")


def main():
    """主函数"""
    updater = ComprehensiveStockUpdater()
    updater.run()


if __name__ == "__main__":
    main()
