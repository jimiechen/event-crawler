#!/usr/bin/env python3 
# -*- coding: utf-8 -*- 
""" 
增强版应用启动脚本 - 解决热重载卡死问题 
""" 

import os 
import sys 
import argparse 
import signal 
import time 
import subprocess 
from pathlib import Path 
from loguru import logger 

# 添加项目根目录到Python路径 
project_root = Path(__file__).parent 
sys.path.insert(0, str(project_root)) 


def start_with_reload(args): 
    """使用子进程启动，自己管理热重载""" 
    from watchdog.observers import Observer 
    from watchdog.events import FileSystemEventHandler 
    
    class RestartHandler(FileSystemEventHandler): 
        def __init__(self, callback): 
            self.callback = callback 
            self.last_event = 0 
            
        def on_modified(self, event): 
            if not event.is_directory and event.src_path.endswith('.py'): 
                current_time = time.time() 
                # 防抖动：1秒内只触发一次 
                if current_time - self.last_event > 1: 
                    self.last_event = current_time 
                    logger.info(f"📝 检测到文件变更: {event.src_path}") 
                    self.callback() 
    
    process = None 
    
    def start_server(): 
        nonlocal process 
        cmd = [ 
            sys.executable, "-c", 
            f"""
import uvicorn
import sys
sys.path.insert(0, "{str(project_root)}")
uvicorn.run(
    "app.main:app",
    host="{args.host}",
    port={args.port},
    log_level="{args.log_level}",
    access_log=True,
    workers=1
)
            """ 
        ] 
        return subprocess.Popen(cmd) 
    
    def restart_server(): 
        nonlocal process 
        if process: 
            logger.info("🔄 重启服务器...") 
            process.terminate() 
            process.wait(timeout=5) 
        process = start_server() 
    
    # 首次启动 
    process = start_server() 
    
    # 设置文件监控 
    event_handler = RestartHandler(restart_server) 
    observer = Observer() 
    
    # 监控app目录 
    app_dir = str(project_root / "app") 
    observer.schedule(event_handler, app_dir, recursive=True) 
    observer.start() 
    
    try: 
        while True: 
            time.sleep(1) 
            # 检查子进程是否还活着 
            if process and process.poll() is not None: 
                logger.error(f"❌ 服务器进程意外退出，退出码: {process.returncode}") 
                break 
    except KeyboardInterrupt: 
        logger.info("👋 收到中断信号，正在关闭...") 
    finally: 
        observer.stop() 
        observer.join() 
        if process: 
            process.terminate() 
            process.wait() 


def start_without_reload(args): 
    """不使用热重载直接启动""" 
    import uvicorn 
    
    uvicorn.run( 
        "app.main:app", 
        host=args.host, 
        port=args.port, 
        log_level=args.log_level, 
        workers=args.workers if args.env == "production" else 1, 
    ) 


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
    parser.add_argument( 
        "--simple-reload", 
        action="store_true", 
        help="使用简单的进程重启（替代uvicorn reload）" 
    ) 
    
    args = parser.parse_args() 
    
    # 设置环境变量 
    os.environ["ENVIRONMENT"] = args.env 
    
    # 初始化日志 
    from app.config.logging import setup_logging 
    setup_logging() 
    
    logger.info(f"🚀 启动同花顺股票监控系统") 
    logger.info(f"📍 环境: {args.env}") 
    logger.info(f"🌐 地址: http://{args.host}:{args.port}") 
    logger.info(f"📊 日志级别: {args.log_level}") 
    
    try: 
        if args.env == "production": 
            logger.info("🏭 生产模式启动...") 
            start_without_reload(args) 
        else: 
            if args.reload: 
                if args.simple_reload: 
                    logger.info("🔧 使用简单热重载模式...") 
                    start_with_reload(args) 
                else: 
                    logger.info("🔧 使用Uvicorn热重载模式...") 
                    # 尝试使用uvicorn的直接调用 
                    subprocess.run([ 
                        sys.executable, "-m", "uvicorn", 
                        "app.main:app", 
                        "--host", args.host, 
                        "--port", str(args.port), 
                        "--log-level", args.log_level, 
                        "--reload", 
                        "--reload-dir", "app", 
                        "--reload-delay", "1.0" 
                    ]) 
            else: 
                logger.info("⚡ 开发模式（无热重载）...") 
                start_without_reload(args) 
                
    except KeyboardInterrupt: 
        logger.info("👋 用户中断，正在关闭服务器...") 
    except Exception as e: 
        logger.error(f"❌ 服务器启动失败: {e}") 
        import traceback 
        traceback.print_exc() 
        sys.exit(1) 


if __name__ == "__main__": 
    main()
