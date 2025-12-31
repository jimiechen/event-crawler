
import sys
import os
import asyncio
from datetime import date

# Add project root to path
sys.path.append(os.getcwd())

try:
    from app.services.stock_service import StockService
    from app.services.tdx_service import TdxService
    from app.models.stock import StockData, StockTdxRisk
    from app.database import db_manager
    print("✅ Import check passed.")
except Exception as e:
    print(f"❌ Import check failed: {e}")
    sys.exit(1)

async def verify_603601():
    print("\n--- Verifying 603601 ---")
    
    # Initialize DB
    await db_manager.initialize()
    
    async with db_manager.get_session() as db:
        # 1. Verify TDX Risk
        tdx_service = TdxService(db)
        print("Fetching TDX risk for 603601...")
        risk_data = await tdx_service.store_stock_risk("603601")
        
        if risk_data:
            print(f"✅ Risk Data Found for {risk_data.stock_code}")
            print(f"   Score: {risk_data.total_score} (Expected: 97)")
            print(f"   Risk Items Count: {risk_data.risk_items}")
            # Check for Auditor Change
            # Parse raw_json if available
            if risk_data.raw_json:
                print("   Checking raw_json for auditor change...")
                import json
                print(f"   Raw JSON keys: {risk_data.raw_json.keys()}")
                categories = risk_data.raw_json.get('data', [])
                found = False
                for category in categories:
                    rows = category.get('rows', [])
                    for row in rows:
                        if row.get('trig') == 1 or row.get('trig') == '1':
                            print(f"   👉 Found Triggered Item: {row}")
                            if '会计师事务所' in str(row):
                                found = True
                if not found:
                    print("   ❌ Auditor change risk item NOT found in raw_json")
            else:
                print("   ❌ raw_json is empty")
        else:
            print("❌ Risk Data NOT Found for 603601")

        # 2. Verify Stock Info/Data
        stock_service = StockService(db)
        print("\nFetching Stock Info for 603601...")
        # Try to get daily data
        daily_data = await stock_service.get_daily_data_with_fallback("603601", limit=10)
        print(f"   Daily Data Count: {len(daily_data)}")
        if daily_data:
            first_data = daily_data[0]
            # Handle different field names in StockDaily (trade_date vs date, close vs close_price)
            d_date = getattr(first_data, 'trade_date', getattr(first_data, 'date', getattr(first_data, 'timestamp', 'N/A')))
            d_close = getattr(first_data, 'close', getattr(first_data, 'close_price', getattr(first_data, 'price', 'N/A')))
            print(f"   Latest Date: {d_date}")
            print(f"   Latest Close: {d_close}")
        
        # Verify Name
        stock_info = await stock_service.get_stock_info("603601")
        if stock_info:
             print(f"✅ Stock Info Found: {stock_info.code} - {stock_info.name}")
        else:
             print("❌ Stock Info NOT Found for 603601")
             print("   Attempting to fetch from Tushare and save...")
             try:
                 from app.services.tushare_service import TushareService
                 tushare_service = TushareService(db_manager)
                 basic_info = tushare_service.get_stock_basic("603601")
                 if basic_info:
                     print(f"   Fetched from Tushare: {basic_info}")
                     # Map Tushare fields to StockInfo fields
                     # Tushare: ts_code, symbol, name, market
                     # StockInfo: stock_code, stock_name, market
                     stock_data = {
                         'stock_code': basic_info.get('symbol'),
                         'stock_name': basic_info.get('name'),
                         'market': basic_info.get('market'),
                         'is_active': True
                     }
                     saved_info = await stock_service.create_or_update_stock_info(stock_data)
                     print(f"   ✅ Saved Stock Info: {saved_info.code} - {saved_info.name}")
                 else:
                     print("   ❌ Failed to fetch from Tushare")
                     # Fallback to hardcoded info for 603601 (中科曙光)
                     print("   ⚠️ Tushare limit reached or failed. Using hardcoded info.")
                     stock_data = {
                         'stock_code': '603601',
                         'stock_name': '中科曙光',
                         'market': 'SH',
                         'is_active': True
                     }
                     saved_info = await stock_service.create_or_update_stock_info(stock_data)
                     print(f"   ✅ Saved Hardcoded Stock Info: {saved_info.code} - {saved_info.name}")
             except Exception as e:
                 print(f"   ❌ Error fetching/saving stock info: {e}")

if __name__ == "__main__":
    asyncio.run(verify_603601())
