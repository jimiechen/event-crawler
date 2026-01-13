"""
Redis缓存服务
用于缓存baseline数据，减少数据库查询
"""
import redis
import logging
from typing import Optional, Dict, Any
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

class RedisCacheService:
    """Redis缓存服务"""
    
    def __init__(self):
        settings = get_settings()
        self.client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=0,
            decode_responses=True
        )
    
    def get_baseline(self, code: str) -> Optional[Dict[str, Any]]:
        """
        从Redis获取baseline缓存
        
        Args:
            code: 股票代码
        
        Returns:
            baseline数据字典，如果不存在返回None
        """
        try:
            cache_key = f"baseline:{code}"
            cached_data = self.client.hgetall(cache_key)
            
            if cached_data:
                logger.debug(f"✅ 从Redis缓存读取baseline: {code}")
                return cached_data
            
            return None
        except Exception as e:
            logger.error(f"读取Redis缓存失败: {e}")
            return None
    
    def set_baseline(self, code: str, baseline_data: Dict[str, Any], expire_seconds: int = 3600):
        """
        设置baseline缓存
        
        Args:
            code: 股票代码
            baseline_data: baseline数据字典
            expire_seconds: 过期时间（秒），默认1小时
        """
        try:
            cache_key = f"baseline:{code}"
            self.client.hset(cache_key, mapping=baseline_data)
            self.client.expire(cache_key, expire_seconds)
            logger.debug(f"💾 baseline数据已缓存: {code}")
        except Exception as e:
            logger.error(f"写入Redis缓存失败: {e}")
    
    def delete_baseline(self, code: str):
        """
        删除baseline缓存
        
        Args:
            code: 股票代码
        """
        try:
            cache_key = f"baseline:{code}"
            self.client.delete(cache_key)
            logger.debug(f"🗑️ baseline缓存已删除: {code}")
        except Exception as e:
            logger.error(f"删除Redis缓存失败: {e}")
    
    def ping(self) -> bool:
        """测试Redis连接"""
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            return False

# 全局单例
redis_cache_service = RedisCacheService()
