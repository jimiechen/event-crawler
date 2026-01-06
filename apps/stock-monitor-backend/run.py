import os
import sys
import uvicorn

# 确保当前目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 尝试导入 settings，如果失败则使用默认值
try:
    from app.config.settings import get_settings
    settings = get_settings()
    PORT = settings.port
    WORKERS = settings.workers
    LOG_LEVEL = settings.log_level.lower()
    IS_PROD = settings.is_production()
except ImportError:
    print("Warning: Could not import settings, using defaults")
    PORT = 8000
    WORKERS = 1
    LOG_LEVEL = "info"
    IS_PROD = False

if __name__ == "__main__":
    # 配置 Uvicorn 参数
    uvicorn_config = {
        "app": "app.main:app",
        "host": "0.0.0.0",
        "port": PORT,
        "log_level": LOG_LEVEL,
        "access_log": True,
    }

    if IS_PROD:
        uvicorn_config.update({
            "workers": WORKERS,
            "reload": False,
        })
    else:
        # 开发环境配置 reload
        # 监控 app 目录的变化
        reload_dirs = [os.path.join(os.path.dirname(os.path.abspath(__file__)), "app")]
        uvicorn_config.update({
            "reload": True,
            "reload_dirs": reload_dirs,
        })

    print(f"🚀 Starting Stock Monitor Backend on port {PORT}...")
    print(f"🔧 Config: {uvicorn_config}")
    
    # 使用 sys.executable 启动 uvicorn 以确保使用相同的 python 环境
    # 但 uvicorn.run 在代码中直接调用通常更好，除非为了规避某些 import 问题
    uvicorn.run(**uvicorn_config)
