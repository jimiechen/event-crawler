#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实盘监控工具 (Live Monitor)
用于实时监控系统各组件健康状态
"""

import sys
import time
import json
import requests
import datetime
import os
from typing import Dict, Any

# 配置
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001/api/v1")
REFRESH_INTERVAL = 5  # 秒

# ANSI 颜色
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_health_status() -> Dict[str, Any]:
    try:
        response = requests.get(f"{API_BASE_URL}/health/detailed", timeout=3)
        if response.status_code == 200:
            return response.json().get("data", {})
        else:
            return {"status": "error", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def print_status(health_data: Dict[str, Any]):
    clear_screen()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"{Colors.HEADER}{Colors.BOLD}=== 股票实时监控系统状态板 ==={Colors.ENDC}")
    print(f"时间: {now}")
    print(f"API地址: {API_BASE_URL}")
    print("-" * 50)
    
    # 总体状态
    status = health_data.get("status", "unknown")
    color = Colors.GREEN if status == "healthy" else Colors.FAIL
    if status == "degraded": color = Colors.WARNING
    
    print(f"系统整体状态: {color}{status.upper()}{Colors.ENDC}")
    print("-" * 50)
    
    if status == "error":
        print(f"{Colors.FAIL}连接失败: {health_data.get('error')}{Colors.ENDC}")
        return

    # 组件检查
    checks = health_data.get("checks", {})
    
    # Database
    db = checks.get("database", {})
    db_status = db.get("status", "unknown")
    db_color = Colors.GREEN if db_status == "healthy" else Colors.FAIL
    print(f"数据库 (MySQL): {db_color}{db_status.upper()}{Colors.ENDC} ({db.get('response_time', 0):.4f}s)")
    if db_status != "healthy":
        print(f"  错误: {db.get('error')}")

    # Redis
    redis = checks.get("redis", {})
    redis_status = redis.get("status", "unknown")
    redis_color = Colors.GREEN if redis_status == "healthy" else Colors.FAIL
    print(f"缓存 (Redis): {redis_color}{redis_status.upper()}{Colors.ENDC} ({redis.get('response_time', 0):.4f}s)")
    if redis_status != "healthy":
        print(f"  错误: {redis.get('error')}")

    # Services
    print("-" * 30)
    stock_svc = checks.get("stock_service", {})
    print(f"股票服务: {Colors.GREEN}{stock_svc.get('status', 'unknown').upper()}{Colors.ENDC} (总股票数: {stock_svc.get('stock_count', 'N/A')})")
    
    dedup_svc = checks.get("dedup_service", {})
    print(f"去重服务: {Colors.GREEN}{dedup_svc.get('status', 'unknown').upper()}{Colors.ENDC} (日志数: {dedup_svc.get('total_logs', 'N/A')})")

    # Chrome Extension Hint
    print("-" * 50)
    print(f"{Colors.BLUE}提示: 请确保Chrome扩展已连接并显示绿色状态图标{Colors.ENDC}")
    print(f"{Colors.BLUE}提示: 使用 Ctrl+C 退出监控{Colors.ENDC}")

def main():
    print("正在启动监控...")
    try:
        while True:
            health_data = get_health_status()
            print_status(health_data)
            time.sleep(REFRESH_INTERVAL)
    except KeyboardInterrupt:
        print("\n监控已停止")
        sys.exit(0)

if __name__ == "__main__":
    main()
