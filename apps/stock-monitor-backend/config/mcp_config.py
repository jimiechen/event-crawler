"""
MCP配置管理
"""
import os
from dotenv import load_dotenv

load_dotenv()


class MCPConfig:
    """MCP配置"""
    
    # DeepSeek配置
    DEEPSEEK_EMAIL = os.getenv("DEEPSEEK_EMAIL", "")
    DEEPSEEK_PASSWORD = os.getenv("DEEPSEEK_PASSWORD", "")
    
    # API配置
    API_HOST = os.getenv("MCP_API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("MCP_API_PORT", "56666"))
    
    # 文档配置
    COLLABORATION_BASE_DIR = os.getenv("COLLABORATION_DIR", "collaboration_docs")
    
    # MCP工具配置
    MCP_TOOLS_ENABLED = {
        "deepseek": os.getenv("MCP_DEEPSEEK_ENABLED", "true").lower() == "true",
        "collaboration": os.getenv("MCP_COLLABORATION_ENABLED", "true").lower() == "true",
        "code_analysis": os.getenv("MCP_CODE_ANALYSIS_ENABLED", "true").lower() == "true"
    }
    
    # 安全配置
    API_KEY = os.getenv("MCP_API_KEY", "")
    ALLOWED_MODELS = os.getenv("ALLOWED_MODELS", "GLM4.7,Gemini,DeepSeek").split(",")
    
    # 数据库配置
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./collaboration.db")
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "mcp_collaboration.log")
    
    # 超时配置
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "120"))
    RESPONSE_TIMEOUT = int(os.getenv("RESPONSE_TIMEOUT", "60"))
    
    # 备份配置
    BACKUP_COUNT = int(os.getenv("BACKUP_COUNT", "10"))
    BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
    
    @classmethod
    def validate(cls):
        """验证配置"""
        warnings = []
        
        if not cls.DEEPSEEK_EMAIL or not cls.DEEPSEEK_PASSWORD:
            warnings.append("DeepSeek登录凭证未设置，部分功能将不可用")
        
        if not cls.API_KEY:
            warnings.append("API密钥未设置，生产环境建议设置")
        
        if cls.API_PORT < 1024 or cls.API_PORT > 65535:
            warnings.append(f"API端口 {cls.API_PORT} 不在有效范围内(1024-65535)")
        
        if warnings:
            print("⚠️  配置警告:")
            for warning in warnings:
                print(f"  - {warning}")
        else:
            print("✅ 配置验证通过")
    
    @classmethod
    def get_deepseek_credentials(cls) -> dict:
        """获取DeepSeek凭证"""
        return {
            "email": cls.DEEPSEEK_EMAIL,
            "password": cls.DEEPSEEK_PASSWORD
        }
    
    @classmethod
    def is_model_allowed(cls, model_name: str) -> bool:
        """检查模型是否被允许"""
        return model_name in cls.ALLOWED_MODELS
    
    @classmethod
    def get_database_url(cls) -> str:
        """获取数据库URL"""
        return cls.DATABASE_URL