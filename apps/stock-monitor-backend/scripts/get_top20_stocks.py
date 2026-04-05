#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取591只股票中符合地量+形态（高分）的前20名
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


class Top20StockSelector:
    """前20股票筛选器"""
    
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
        
        # 解析条件字段
        low_volume_5d = fields.get("5日地量", False)
        low_volume_10d = fields.get("10日地量", False)
        low_volume_20d = fields.get("20日地量", False)
        bottom_pattern = fields.get("底分型", False)
        yang_bao_yin = fields.get("阳包阴", False)
        breakout_high = fields.get("突破最高价", False)
        breakout_close = fields.get("突破收盘价", False)
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
            "score": int(score) if score else 0,
        }
    
    def get_stock_price_from_tdx(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """从通达信获取股票最新价格"""
        try:
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
    
    def check_qualified(self, parsed: Dict[str, Any]) -> bool:
        """
        检查股票是否符合条件：地量 + 形态（高分）
        条件：地量（5日/10日/20日任一）且 形态得分 >= 3
        """
        has_low_volume = parsed["low_volume_5d"] or parsed["low_volume_10d"] or parsed["low_volume_20d"]
        has_high_score = parsed["score"] >= 3
        return has_low_volume and has_high_score
    
    def send_to_feishu_group(self, message: str) -> bool:
        """发送消息到飞书群聊"""
        try:
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
        """执行筛选流程"""
        logger.info("=" * 80)
        logger.info("📊 筛选地量+形态高分股票（前20名）")
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
        logger.info("\n🔍 筛选地量+形态高分股票...")
        
        qualified_stocks = []
        
        for idx, record in enumerate(records, 1):
            parsed = self.parse_stock_record(record)
            stock_code = parsed["stock_code"]
            stock_name = parsed["stock_name"]
            
            if not stock_code:
                continue
            
            # 检查是否符合条件
            if self.check_qualified(parsed):
                # 获取最新价格
                price_data = self.get_stock_price_from_tdx(stock_code)
                
                if price_data:
                    # 构建条件描述
                    conditions = []
                    if parsed["low_volume_5d"]: conditions.append("5日地量")
                    if parsed["low_volume_10d"]: conditions.append("10日地量")
                    if parsed["low_volume_20d"]: conditions.append("20日地量")
                    if parsed["bottom_pattern"]: conditions.append("底分型")
                    if parsed["yang_bao_yin"]: conditions.append("阳包阴")
                    if parsed["breakout_high"]: conditions.append("突破最高")
                    if parsed["breakout_close"]: conditions.append("突破收盘")
                    
                    qualified_stocks.append({
                        "code": stock_code,
                        "name": stock_name,
                        "conditions": ", ".join(conditions),
                        "score": parsed["score"],
                        "price": price_data["close"],
                        "volume": price_data["volume"],
                        "time": price_data["time"],
                    })
            
            # 每处理100条显示进度
            if idx % 100 == 0:
                logger.info(f"  已处理 {idx}/{len(records)} 条记录，找到 {len(qualified_stocks)} 只符合条件的股票")
            
            time.sleep(0.03)
        
        logger.info(f"\n✅ 共找到 {len(qualified_stocks)} 只符合条件的股票（地量+高分）")
        
        if not qualified_stocks:
            logger.warning("⚠️ 没有找到符合条件的股票")
            return
        
        # 3. 按得分排序，取前20
        qualified_stocks.sort(key=lambda x: x["score"], reverse=True)
        top20 = qualified_stocks[:20]
        
        logger.info(f"\n📊 前20名股票（按得分排序）：")
        for idx, stock in enumerate(top20, 1):
            logger.info(f"  [{idx}] {stock['code']} {stock['name']}: 得分{stock['score']}, 收盘{stock['price']:.2f}, {stock['conditions']}")
        
        # 4. 构建消息
        logger.info("\n📋 构建消息...")
        
        message_lines = []
        message_lines.append("📊 **地量+形态高分股票 TOP20**")
        message_lines.append(f"📅 日期: {self.today.strftime('%Y-%m-%d')}")
        message_lines.append(f"⏰ 时间: {datetime.now().strftime('%H:%M:%S')}")
        message_lines.append(f"📈 筛选条件: 地量(5日/10日/20日) + 形态得分≥3")
        message_lines.append(f"📊 从 {len(records)} 只股票中筛选出 {len(qualified_stocks)} 只，显示前20名")
        message_lines.append("")
        message_lines.append("| 排名 | 股票代码 | 股票名称 | 收盘价 | 成交量(手) | 符合条件 | 得分 |")
        message_lines.append("|------|----------|----------|--------|------------|----------|------|")
        
        for idx, stock in enumerate(top20, 1):
            message_lines.append(f"| {idx} | {stock['code']} | {stock['name']} | {stock['price']:.2f} | {stock['volume']:.0f} | {stock['conditions']} | {stock['score']} |")
        
        message_lines.append("")
        message_lines.append("**筛选条件说明：**")
        message_lines.append("- 地量: 当日成交量 < 过去N日平均成交量 × 0.8")
        message_lines.append("- 高分: 形态得分 ≥ 3分")
        message_lines.append("- 得分计算: 地量+1分, 底分型+2分, 阳包阴+2分, 突破+3分")
        message_lines.append("")
        message_lines.append("数据来源: 通达信 | 飞书多维表格")
        
        # 5. 发送消息到飞书群聊
        message = "\n".join(message_lines)
        
        logger.info("\n📤 发送消息到飞书群聊...")
        if self.send_to_feishu_group(message):
            logger.info("✅ 完成")
        else:
            logger.error("❌ 发送失败")


def main():
    """主函数"""
    selector = Top20StockSelector()
    selector.run()


if __name__ == "__main__":
    main()
