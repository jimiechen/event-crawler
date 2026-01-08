
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.dirname(current_dir)
sys.path.append(backend_root)

print("Importing DatabaseManager...")
from app.database import DatabaseManager
print("DatabaseManager imported")

print("Importing WencaiCrawler...")
try:
    from app.crawler.wencai_crawler import WencaiCrawler
    print("WencaiCrawler imported successfully")
except Exception as e:
    print(f"Error importing WencaiCrawler: {e}")
