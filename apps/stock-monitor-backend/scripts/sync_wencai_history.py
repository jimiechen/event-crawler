
import asyncio
import os
import sys
import glob
import pandas as pd
from datetime import datetime
from loguru import logger

# Add project root to path
sys.path.append(os.getcwd())

from app.database import db_manager
from app.services.wencai_service import WencaiService

async def sync_history():
    print("Starting Wencai history sync...")
    
    # Initialize DB
    async with db_manager.get_session() as session:
        service = WencaiService(session)
        
        # Find all CSV files
        data_dir = "/Users/mac/StudioProjects/open-citycloud/projects/event-crawler/data/wencai"
        pattern = os.path.join(data_dir, "wencai_*.csv")
        files = glob.glob(pattern)
        files.sort()
        
        print(f"Found {len(files)} files to process.")
        
        for file_path in files:
            try:
                # Extract date from filename: wencai_20251128.csv
                filename = os.path.basename(file_path)
                date_str = filename.replace("wencai_", "").replace(".csv", "")
                target_date = datetime.strptime(date_str, "%Y%m%d").date()
                
                print(f"Processing {target_date} from {filename}...")
                
                # Read CSV
                df = pd.read_csv(file_path)
                
                # Convert to list of dicts
                stocks = []
                for _, row in df.iterrows():
                    # Map CSV columns to service expected keys
                    stock_data = {
                        "stock_code": str(row['stock_code']).zfill(6), # Ensure 6 digits
                        "stock_name": row['stock_name'],
                        "latest_price": row.get('current_price'),
                        "change_percent": row.get('price_change_percent'),
                        "date": target_date
                    }
                    stocks.append(stock_data)
                
                if stocks:
                    print(f"  Saving {len(stocks)} stocks...")
                    await service.save_stocks(stocks)
                    print(f"  Done for {target_date}")
                else:
                    print(f"  No stocks found in {filename}")
                    
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                # Continue to next file
                continue
                
    print("Sync finished.")

if __name__ == "__main__":
    asyncio.run(sync_history())
