#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加目标页面到数据库
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.crawler import CrawlerTarget
from app.config.settings import get_settings

async def add_targets():
    """添加目标页面到数据库"""
    
    # 创建数据库连接
    settings = get_settings()
    DATABASE_URL = settings.database_url
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # 目标页面列表
    targets = [
        {
            "platform": "tonghuashun",
            "name": "同花顺股票页面",
            "url": "https://stockpage.10jqka.com.cn/000795/",
            "target_type": "url",
            "is_active": True
        },
        {
            "platform": "wencai",
            "name": "问财搜索-成交量倍增",
            "url": "https://www.iwencai.com/unifiedwap/result?w=2026年01月13日成交量是2026年01月12日成交量的2.8倍以上，非北交 非创业版，非科创版，非ST，概念 行业，2026年01月12日和2026年01月13日涨幅低于13%  收盘价低于25",
            "target_type": "url",
            "is_active": True
        },
        {
            "platform": "tonghuashun",
            "name": "同花顺自选股页面",
            "url": "https://t.10jqka.com.cn/newcircle/user/userPersonal/?from=finance&tab=zx",
            "target_type": "url",
            "is_active": True
        }
    ]
    
    async with async_session_maker() as session:
        for target_data in targets:
            # 检查是否已存在
            from sqlalchemy import select
            stmt = select(CrawlerTarget).where(
                CrawlerTarget.url == target_data["url"]
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"✅ 目标页面已存在: {target_data['name']}")
                continue
            
            # 创建新目标
            new_target = CrawlerTarget(**target_data)
            session.add(new_target)
            await session.commit()
            await session.refresh(new_target)
            print(f"✅ 成功添加目标页面: {target_data['name']} (ID: {new_target.id})")
    
    print(f"\n🎉 所有目标页面添加完成！")
    
    # 关闭数据库连接
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(add_targets())
