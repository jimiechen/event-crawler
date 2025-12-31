#!/usr/bin/env python3 
# 诊断脚本：diagnose.py 
import os 
import sys 
import time 
from pathlib import Path 

# 临时禁用某些可能引起问题的模块 
os.environ["UVICORN_RELOAD"] = "1" 
os.environ["PYTHONASYNCIODEBUG"] = "1" 

# 清除可能的问题 
sys.dont_write_bytecode = True 

# 手动重新加载配置 
project_root = Path(__file__).parent 
sys.path.insert(0, str(project_root)) 

# 使用最小的uvicorn配置 
import uvicorn 
import asyncio 

# 设置事件循环策略（尝试修复某些平台的循环问题） 
if sys.platform == "win32": 
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) 
else: 
    try: 
        import uvloop 
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy()) 
        print("✅ 使用uvloop事件循环") 
    except ImportError: 
        print("⚠️  uvloop未安装，使用默认事件循环") 

print("🔍 开始诊断启动...") 
print(f"Python版本: {sys.version}") 
print(f"工作目录: {os.getcwd()}") 
print(f"项目根目录: {project_root}") 

# 最小化配置启动 
config = uvicorn.Config( 
    "app.main:app", 
    host="127.0.0.1", 
    port=8001,  # 使用不同的端口测试 
    reload=True, 
    reload_dirs=[str(project_root / "app")], 
    reload_delay=2.0,  # 较长的延迟 
    log_level="debug", 
    access_log=True, 
    loop="asyncio",  # 强制使用asyncio循环 
) 

server = uvicorn.Server(config) 

try: 
    print("🚀 启动服务器...") 
    server.run() 
except KeyboardInterrupt: 
    print("👋 中断") 
except Exception as e: 
    print(f"❌ 错误: {e}") 
    import traceback 
    traceback.print_exc()
