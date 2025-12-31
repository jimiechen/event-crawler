#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通达信数据服务
"""

import requests
import json
import asyncio
from datetime import date
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from ..models.stock import StockTdxRisk
from ..database import DatabaseManager

class TdxService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.base_url = "http://page3.tdx.com.cn:7615/site/pcwebcall_static/bxb/json/"

    async def fetch_stock_risk(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        抓取通达信股票风险数据
        """
        # Remove suffix if present (e.g. 000969.SZ -> 000969)
        clean_code = stock_code.split('.')[0]
        url = f"{self.base_url}{clean_code}.json"
        
        logger.info(f"Fetching TDX risk data for {stock_code} from {url}")
        
        try:
            # Run synchronous requests in executor to avoid blocking async loop
            loop = asyncio.get_event_loop()
            
            def _fetch():
                max_retries = 3
                for i in range(max_retries):
                    try:
                        # 增加超时时间，添加User-Agent，禁用代理
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                        }
                        # Explicitly bypass proxies
                        proxies = {"http": "", "https": ""}
                        resp = requests.get(url, timeout=15, headers=headers, proxies=proxies)
                        resp.encoding = 'utf-8'
                        if resp.status_code == 200:
                            return resp.json()
                    except Exception as e:
                        if i == max_retries - 1:
                            logger.error(f"Request failed after {max_retries} attempts: {e}")
                        else:
                            import time
                            time.sleep(1) # Wait 1s before retry
                return None

            data = await loop.run_in_executor(None, _fetch)
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch TDX data for {stock_code}: {e}")
            return None

    async def store_stock_risk(self, stock_code: str, stock_name: Optional[str] = None) -> Optional[StockTdxRisk]:
        """
        获取并存储股票风险数据
        """
        data = await self.fetch_stock_risk(stock_code)
        if not data:
            return None
            
        try:
            # Parse data
            total_items = data.get('total', 0)
            risk_items = data.get('num', 0)
            # Safe items = total - risk
            safe_items = total_items - risk_items
            
            # Highlight items - using length of data list as proxy for now
            highlight_items = len(data.get('data', []))
            
            # Check for existing record
            today = date.today()
            stmt = select(StockTdxRisk).where(
                StockTdxRisk.stock_code == stock_code,
                StockTdxRisk.date == today
            )
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            # Calculate score: Base 100 - Risk (Sum of trig=1 fs)
            categories = data.get('data', [])
            deduction = 0
            
            for category in categories:
                rows = category.get('rows', [])
                for row in rows:
                    try:
                        trig_val = int(row.get('trig', 0))
                        if trig_val == 1:
                            fs_val = int(row.get('fs', 0))
                            deduction += fs_val
                    except (ValueError, TypeError):
                        pass
            
            # Base score is 100
            score = 100 - deduction
            
            fetched_name = data.get('name')
            
            if existing:
                if stock_name:
                    existing.stock_name = stock_name
                elif fetched_name:
                    existing.stock_name = fetched_name
                    
                existing.total_items = total_items
                existing.risk_items = risk_items
                existing.safe_items = safe_items
                existing.highlight_items = highlight_items
                existing.raw_json = data
                existing.total_score = score
            else:
                new_record = StockTdxRisk(
                    stock_code=stock_code,
                    stock_name=stock_name or fetched_name,
                    date=today,
                    timestamp=today,
                    total_score=score,
                    total_items=total_items,
                    risk_items=risk_items,
                    safe_items=safe_items,
                    highlight_items=highlight_items,
                    raw_json=data
                )
                self.session.add(new_record)
            
            await self.session.commit()
            return existing or new_record
            
        except Exception as e:
            logger.error(f"Error storing TDX data for {stock_code}: {e}")
            await self.session.rollback()
            return None
