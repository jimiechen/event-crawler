import sys
import os

# Ensure the current directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router as api_router

app = FastAPI(title="Stock Verify Server", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API
app.include_router(api_router, prefix="/api")

# Mount Static Files (Frontend)
# 修正：确保 static 目录路径是绝对路径
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(static_dir):
    print(f"Warning: Static directory not found at {static_dir}")
app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")

# 根路径重定向到 index.html (可选，如果 StaticFiles 的 html=True 没生效)
# 但通常挂载到 /static 后，访问 /static/kline.html 应该可以
# 如果用户想直接访问 /kline.html，则挂载点应该是 "/"
# 原代码是 app.mount("/", ...)，这会拦截所有非 API 请求。
# 如果 static 目录下有 kline.html，访问 /kline.html 应该能找到。
# 让我们先用绝对路径修复挂载点 "/"
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static_root")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
