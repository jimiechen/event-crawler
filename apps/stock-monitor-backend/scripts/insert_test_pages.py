#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插入测试页面到数据库
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db_session
from app.models.test_page import TestPage
from sqlalchemy import text


async def insert_test_pages():
    """插入测试页面"""
    db_gen = get_db_session()
    db = await db_gen.__anext__()
    
    try:
        test_pages = [
            {
                "name": "同花顺个股页面",
                "url": "https://stockpage.10jqka.com.cn/000795/",
                "platform": "tonghuashun",
                "description": "同花顺个股资金流向查询页面，用于测试同花顺登录状态和数据抓取"
            },
            {
                "name": "问财搜索结果页面",
                "url": "https://www.iwencai.com/unifiedwap/result?w=2026%E5%B9%B401%E6%9C%8813%E6%97%A5%E6%88%90%E4%BA%A4%E9%87%8F%E6%98%AF2026%E5%B9%B401%E6%9C%8812%E6%97%A5%E6%88%90%E4%BA%A4%E9%87%8F%E7%9A%842.8%E5%80%8D%E4%BB%A5%E4%B8%8A%EF%BC%8C%E9%9D%9E%E5%8C%97%E4%BA%A4%20%E9%9D%9E%E5%88%9B%E4%B8%9A%E7%89%88%EF%BC%8C%E9%9D%9E%E7%A7%91%E5%88%9B%E7%89%88%EF%BC%8C%E9%9D%9EST%EF%BC%8C%E6%A6%82%E5%BF%B5%20%E8%A1%8C%E4%B8%9A%EF%BC%8C2026%E5%B9%B401%E6%9C%8812%E6%97%A5%E5%92%8C2026%E5%B9%B401%E6%9C%8813%E6%97%A5%E6%B6%A8%E5%B9%85%E4%BD%8E%E4%BA%8E13%25%20%20%E6%94%B6%E7%9B%98%E4%BB%B7%E4%BD%8E%E4%BA%8E25",
                "platform": "wencai",
                "description": "问财搜索结果页面，用于测试问财登录状态和数据抓取"
            },
            {
                "name": "同花顺自选股页面",
                "url": "https://t.10jqka.com.cn/newcircle/user/userPersonal/?from=finance&tab=zx",
                "platform": "tonghuashun",
                "description": "同花顺自选股页面，用于测试同花顺登录状态和数据抓取"
            }
        ]
        
        for page_data in test_pages:
            existing = await db.execute(
                text(f"SELECT id FROM test_pages WHERE url = '{page_data['url']}'")
            )
            if existing.fetchone():
                print(f"测试页面已存在: {page_data['name']}")
                continue
            
            test_page = TestPage(
                name=page_data["name"],
                url=page_data["url"],
                platform=page_data["platform"],
                description=page_data["description"],
                is_active=True
            )
            db.add(test_page)
            print(f"插入测试页面: {page_data['name']}")
        
        await db.commit()
        print(f"\n✅ 成功插入 {len(test_pages)} 个测试页面")
    
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(insert_test_pages())