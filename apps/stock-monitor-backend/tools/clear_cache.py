#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import redis
from dotenv import load_dotenv

# 加载环境变量
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config.settings import get_settings

def clear_redis_cache():
    settings = get_settings()
    try:
        r = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=0,
            decode_responses=True
        )
        # 清除所有 baseline:* 键
        keys = r.keys("baseline:*")
        if keys:
            r.delete(*keys)
            print(f"✅ 已清除 {len(keys)} 个 Baseline 缓存")
        else:
            print("ℹ️ 没有找到 Baseline 缓存")
            
    except Exception as e:
        print(f"❌ 清除缓存失败: {e}")

if __name__ == "__main__":
    clear_redis_cache()
