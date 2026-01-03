#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用启动脚本
"""

import os
import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import uvicorn
from app.config.settings import get_settings
from app.config.logging import setup_logging
from loguru import logger


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="同花顺股票监控系统")
    parser.add_argument(
        "--env",
        choices=["development", "production", "testing"],
        default="development",
        help="运行环境"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="服务器主机地址"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="服务器端口"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="工作进程数（仅生产环境）"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="启用热重载（仅开发环境）"
    )
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error", "critical"],
        default="info",
        help="日志级别"
    )
    
    args = parser.parse_args()
    
    # 设置环境变量
    os.environ["ENVIRONMENT"] = args.env
    os.environ["HOST"] = args.host
    os.environ["PORT"] = str(args.port)
    os.environ["WORKERS"] = str(args.workers)
    os.environ["LOG_LEVEL"] = args.log_level.upper()
    
    # 初始化配置和日志
    settings = get_settings()
    setup_logging()
    
    logger.info(f"🚀 启动{settings.app_name}")
    logger.info(f"📍 环境: {settings.environment}")
    logger.info(f"🌐 地址: http://{settings.host}:{settings.port}")
    logger.info(f"📊 日志级别: {settings.log_level}")
    
    # 配置Uvicorn启动参数
    uvicorn_config = {
        "app": "app.main:app",
        "host": args.host,
        "port": args.port,
        "log_level": args.log_level.lower(),
        "access_log": True,
    }

    if settings.is_production():
        logger.info("🏭 生产模式启动...")
        uvicorn_config.update({
            "workers": args.workers,
            "reload": False,
        })
    else:
        logger.info("🛠️ 开发模式启动...")
        # 开发模式下配置热重载
        reload_dirs = [str(project_root / "app")]
        uvicorn_config.update({
            "reload": True,
            "reload_dirs": reload_dirs,
            "reload_delay": 0.25,
        })
        # 如果命令行指定了reload参数，覆盖配置
        if args.reload:
            uvicorn_config["reload"] = True

    try:
        uvicorn.run(**uvicorn_config)
    except KeyboardInterrupt:
        logger.info("👋 用户中断，正在关闭服务器...")
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()