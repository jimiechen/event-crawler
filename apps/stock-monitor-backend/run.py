#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用启动脚本
使用方法: python3 run.py [--reload] [--host 0.0.0.0] [--port 8000]
"""

import uvicorn
import argparse
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config.settings import get_settings

def main():
    parser = argparse.ArgumentParser(description="Stock Monitor Backend Server")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--host", help="Bind socket to this host")
    parser.add_argument("--port", type=int, help="Bind socket to this port")
    parser.add_argument("--env", help="Environment (development/production)")
    
    args = parser.parse_args()
    
    settings = get_settings()
    
    # 优先使用命令行参数，其次使用配置文件
    host = args.host or settings.host
    port = args.port or settings.port
    
    # reload设置: 命令行参数 > 配置环境 > 默认False
    reload = args.reload
    
    # 环境变量覆盖
    if args.env:
        os.environ["ENVIRONMENT"] = args.env

    print(f"🚀 Starting server on http://{host}:{port} (reload={reload})...")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=settings.log_level.lower(),
        access_log=True
    )

if __name__ == "__main__":
    main()
