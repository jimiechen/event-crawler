import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta, date
from decimal import Decimal
from sqlalchemy import text, select
from typing import List, Dict, Any

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.dirname(current_dir) # apps/stock-monitor-backend
sys.path.append(backend_root)

print("Start imports")
try:
    print("Importing app.database...")
    from app.database import DatabaseManager
    print("app.database imported")

    print("Importing app.crawler.wencai_crawler...")
    from app.crawler.wencai_crawler import WencaiCrawler
    print("app.crawler.wencai_crawler imported")
    
except Exception as e:
    print(f"Error: {e}")
