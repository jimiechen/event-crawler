"""
Mock API服务器 - 完全独立，不依赖数据库

这是一个独立的FastAPI服务器，只提供Mock接口，不需要数据库。
用于开发和测试。
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from mock.mock_routes import router as mock_router

app = FastAPI(
    title="Hyper Alpha Arena Mock API",
    version="0.5.0",
    description="Mock API for Hyper Alpha Arena - No database required"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mock_router)


@app.middleware("http")
async def redirect_api_to_mock(request: Request, call_next):
    """将所有 /api/ 请求重定向到 /api/mock/"""
    path = request.url.path
    if path.startswith("/api/") and not path.startswith("/api/mock"):
        new_path = path.replace("/api/", "/api/mock/", 1)
        request.scope["path"] = new_path
        request.scope["route_path"] = new_path
    return await call_next(request)

@app.get("/")
async def root():
    return {
        "message": "Hyper Alpha Arena Mock API",
        "version": "0.5.0",
        "status": "running",
        "mock_mode": True
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "mock_mode": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mock_server:app", host="0.0.0.0", port=8803, reload=True)
