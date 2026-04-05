#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从飞书表格读取所有股票，筛选符合地量、倍量、形态条件的股票，发送到飞书群聊
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


class StockPriceSender:
    """股票价格发送器"""
    
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
        """
        从飞书表格读取所有股票记录
        """
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
        
        # 解析条件字段
        low_volume_5d = fields.get("5日地量", False)
        low_volume_10d = fields.get("10日地量", False)
        low_volume_20d = fields.get("20日地量", False)
        bottom_pattern = fields.get("底分型", False)
        yang_bao_yin = fields.get("阳包阴", False)
        breakout_high = fields.get("突破最高价", False)
        breakout_close = fields.get("突破收盘价", False)
        triple_volume = fields.get("3倍量确认", False)
        score = fields.get("形态得分", 0)
        
        return {
            "record_id": record_id,
            "stock_code": stock_code,
            "stock_name": stock_name,
            "low_volume_5d": bool(low_volume_5d) if low_volume_5d else False,
            "low_volume_10d": bool(low_volume_10d) if low_volume_10d else False,
            "low_volume_20d": bool(low_volume_20d) if low_volume_20d else False,
            "bottom_pattern": bool(bottom_pattern) if bottom_pattern else False,
            "yang_bao_yin": bool(yang_bao_yin) if yang_bao_yin else False,
            "breakout_high": bool(breakout_high) if breakout_high else False,
            "breakout_close": bool(breakout_close) if breakout_close else False,
            "triple_volume": bool(triple_volume) if triple_volume else False,
            "score": int(score) if score else 0,
        }
    
    def get_stock_price_from_tdx(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        从通达信获取股票最新价格
        """
        try:
            # 转换股票代码格式
            if stock_code.startswith('6'):
                stock_code_full = f"{stock_code}.SH"
            else:
                stock_code_full = f"{stock_code}.SZ"
            
            data_dict = self.tdx_client.get_market_data(
                field_list=['Open', 'High', 'Low', 'Close', 'Volume', 'Amount'],
                stock_list=[stock_code_full],
                period='1d',
                count=1,
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
            
            # 成交量转换为手
            volume = float(volume) / 100 if volume is not None else 0
            
            return {
                'date': str(latest_date_idx),
                'time': datetime.now().strftime('%H:%M:%S'),
                'open': float(open_val) if open_val is not None else 0,
                'high': float(high_val) if high_val is not None else 0,
                'low': float(low_val) if low_val is not None else 0,
                'close': float(close_val) if close_val is not None else 0,
                'volume': volume,
            }
            
        except Exception as e:
            logger.error(f"❌ 获取 {stock_code} 价格失败: {e}")
            return None
    
    def check_conditions(self, parsed: Dict[str, Any]) -> Dict[str, bool]:
        """
        检查股票是否符合各种条件
        
        Returns:
            Dict: 各条件是否符合
        """
        return {
            "地量": parsed["low_volume_5d"] or parsed["low_volume_10d"] or parsed["low_volume_20d"],
            "倍量": parsed["triple_volume"],
            "底分型": parsed["bottom_pattern"],
            "阳包阴": parsed["yang_bao_yin"],
            "突破": parsed["breakout_high"] or parsed["breakout_close"],
            "高分": parsed["score"] >= 3,
        }
    
    def send_to_feishu_group(self, message: str) -> bool:
        """
        使用飞书CLI发送消息到群聊
        """
        try:
            # 使用feishu_client发送消息
            result = self.feishu_client.send_group_message(message)
            if result:
                logger.info("✅ 消息发送成功")
                return True
            else:
                logger.error("❌ 消息发送失败")
                return False
        except Exception as e:
            logger.error(f"❌ 发送消息异常: {e}")
            return False
    
    def run(self):
        """执行发送流程"""
        logger.info("=" * 80)
        logger.info("📊 筛选符合条件的股票并发送到飞书群聊")
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
        
        # 2. 筛选符合条件的股票
        logger.info("\n🔍 筛选符合条件的股票...")
        
        qualified_stocks = []
        
        for idx, record in enumerate(records, 1):
            parsed = self.parse_stock_record(record)
            stock_code = parsed["stock_code"]
            stock_name = parsed["stock_name"]
            
            if not stock_code:
                continue
            
            # 检查条件
            conditions = self.check_conditions(parsed)
            
            # 如果符合任一条件，则加入列表
            if any(conditions.values()):
                # 获取最新价格
                price_data = self.get_stock_price_from_tdx(stock_code)
                
                if price_data:
                    qualified_stocks.append({
                        "code": stock_code,
                        "name": stock_name,
                        "conditions": conditions,
                        "score": parsed["score"],
                        "price": price_data["close"],
                        "volume": price_data["volume"],
                        "time": price_data["time"],
                    })
                    
                    condition_str = ", ".join([k for k, v in conditions.items() if v])
                    logger.info(f"  [{len(qualified_stocks)}] {stock_code} {stock_name}: {condition_str}, 得分{parsed['score']}")
            
            # 每处理50条显示进度
            if idx % 50 == 0:
                logger.info(f"  已处理 {idx}/{len(records)} 条记录，找到 {len(qualified_stocks)} 只符合条件的股票")
            
            time.sleep(0.05)
        
        logger.info(f"\n✅ 共找到 {len(qualified_stocks)} 只符合条件的股票")
        
        if not qualified_stocks:
            logger.warning("⚠️ 没有找到符合条件的股票")
            return
        
        # 3. 构建消息
        logger.info("\n📋 构建消息...")
        
        message_lines = []
        message_lines.append("📊 **股票筛选播报**")
        message_lines.append(f"📅 日期: {self.today.strftime('%Y-%m-%d')}")
        message_lines.append(f"⏰ 时间: {datetime.now().strftime('%H:%M:%S')}")
        message_lines.append(f"📈 筛选结果: 共 {len(qualified_stocks)} 只股票符合条件")
        message_lines.append("")
        message_lines.append("| 序号 | 股票代码 | 股票名称 | 收盘价 | 成交量(手) | 符合条件 | 得分 |")
        message_lines.append("|------|----------|----------|--------|------------|----------|------|")
        
        for idx, stock in enumerate(qualified_stocks[:50], 1):  # 最多显示50只
            condition_str = ", ".join([k for k, v in stock["conditions"].items() if v])
            message_lines.append(f"| {idx} | {stock['code']} | {stock['name']} | {stock['price']:.2f} | {stock['volume']:.0f} | {condition_str} | {stock['score']} |")
        
        if len(qualified_stocks) > 50:
            message_lines.append(f"| ... | ... | ... | ... | ... | ... | ... |")
            message_lines.append(f"| - | - | - | - | - | 还有 {len(qualified_stocks) - 50} 只 | - |")
        
        message_lines.append("")
        message_lines.append("**筛选条件说明：**")
        message_lines.append("- 地量: 5日/10日/20日地量")
        message_lines.append("- 倍量: 3倍量确认")
        message_lines.append("- 底分型: 出现底分型形态")
        message_lines.append("- 阳包阴: 出现阳包阴形态")
        message_lines.append("- 突破: 突破最高价或收盘价")
        message_lines.append("- 高分: 形态得分≥3")
        message_lines.append("")
        message_lines.append("数据来源: 通达信 | 飞书多维表格")
        
        # 4. 发送消息到飞书群聊
        message = "\n".join(message_lines)
        
        logger.info("\n📤 发送消息到飞书群聊...")
        if self.send_to_feishu_group(message):
            logger.info("✅ 完成")
        else:
            logger.error("❌ 发送失败")


def main():
    """主函数"""
    sender = StockPriceSender()
    sender.run()


if __name__ == "__main__":
    main()
