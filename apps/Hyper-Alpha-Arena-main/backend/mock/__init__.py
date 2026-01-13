"""
Mock API模块 - 完全独立，不依赖任何原有代码

这个模块提供所有API接口的Mock实现，用于开发和测试。
所有Mock数据存储在内存中，重启后重置。
"""
from .mock_routes import router as mock_router

__all__ = ['mock_router']
