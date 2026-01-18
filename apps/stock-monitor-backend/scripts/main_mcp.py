"""
Trae AI MCP 协作系统主程序
提供FastAPI服务，支持GLM4.7/Gemini与DeepSeek协作
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.mcp_controller import router as mcp_router
from config.mcp_config import MCPConfig
import logging
import time

# 配置日志
logging.basicConfig(
    level=getattr(logging, MCPConfig.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(MCPConfig.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Trae AI MCP 协作系统",
    description="GLM4.7/Gemini与DeepSeek的MCP协作系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(mcp_router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Trae AI MCP 协作系统运行中",
        "version": "1.0.0",
        "endpoints": {
            "deepseek": "/mcp/deepseek/*",
            "collaboration": "/mcp/collaboration/*",
            "health": "/mcp/health"
        },
        "config": {
            "deepseek_enabled": MCPConfig.MCP_TOOLS_ENABLED["deepseek"],
            "collaboration_enabled": MCPConfig.MCP_TOOLS_ENABLED["collaboration"],
            "allowed_models": MCPConfig.ALLOWED_MODELS
        }
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "services": {
            "deepseek": MCPConfig.MCP_TOOLS_ENABLED["deepseek"],
            "collaboration": MCPConfig.MCP_TOOLS_ENABLED["collaboration"]
        }
    }


@app.on_event("startup")
async def startup_event():
    """启动事件"""
    logger.info("=" * 50)
    logger.info("Trae AI MCP 协作系统启动中...")
    logger.info("=" * 50)
    
    # 验证配置
    MCPConfig.validate()
    
    # 打印配置信息
    logger.info(f"API地址: http://{MCPConfig.API_HOST}:{MCPConfig.API_PORT}")
    logger.info(f"协作文档目录: {MCPConfig.COLLABORATION_BASE_DIR}")
    logger.info(f"允许的模型: {', '.join(MCPConfig.ALLOWED_MODELS)}")
    logger.info(f"DeepSeek已配置: {'是' if MCPConfig.DEEPSEEK_EMAIL else '否'}")
    
    logger.info("=" * 50)
    logger.info("Trae AI MCP 协作系统已启动")
    logger.info("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    logger.info("Trae AI MCP 协作系统关闭中...")
    
    # 清理资源
    from app.api.mcp_controller import deepseek_service
    if deepseek_service:
        await deepseek_service.cleanup()
    
    logger.info("Trae AI MCP 协作系统已关闭")


if __name__ == "__main__":
    # 启动服务
    uvicorn.run(
        "main:app",
        host=MCPConfig.API_HOST,
        port=MCPConfig.API_PORT,
        reload=True,
        log_level=MCPConfig.LOG_LEVEL.lower()
    )