#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试飞书客户端
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.feishu_client import FeishuClient, init_feishu_client


def main():
    print("\n" + "="*60)
    print("飞书客户端测试")
    print("="*60 + "\n")
    
    # 1. 初始化飞书客户端
    print("1. 初始化飞书客户端...")
    client = init_feishu_client()
    print("   OK: 飞书客户端初始化\n")
    
    # 2. 测试发送消息
    print("2. 测试发送消息...")
    result = client.send_group_message("🧪 飞书客户端测试消息\n这是一条测试消息", msg_type="text")
    print(f"   发送结果: {result}\n")
    
    # 3. 测试发送选股报告
    print("3. 测试发送选股报告...")
    from datetime import date
    test_stocks = [
        {"code": "000001.SZ", "name": "平安银行", "volume_ratio": 3.5, "change_percent": 10.0},
        {"code": "600519.SH", "name": "贵州茅台", "volume_ratio": 4.2, "change_percent": 5.5}
    ]
    
    report_result = client.send_selection_report(
        trade_date=date(2026, 3, 25),
        sector_code="3BL0325",
        selected_stocks=test_stocks
    )
    print(f"   报告结果: {report_result}\n")
    
    print("="*60)
    print("测试完成")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
