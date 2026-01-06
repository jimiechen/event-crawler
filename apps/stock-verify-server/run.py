import os
import sys
import uvicorn

# 确保当前目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # 配置 Uvicorn 参数
    # 注意：这里假设 main.py 在当前目录下
    uvicorn_config = {
        "app": "main:app",
        "host": "0.0.0.0",
        "port": 8001,
        "log_level": "info",
        "access_log": True,
        "reload": True,
        # 监控当前目录
        "reload_dirs": [os.path.dirname(os.path.abspath(__file__))],
    }

    print(f"🚀 Starting Stock Verify Server on port 8001...")
    print(f"🔧 Config: {uvicorn_config}")
    
    uvicorn.run(**uvicorn_config)
