import os
import pandas as pd
from loguru import logger
import glob

# Configuration
CSV_DATA_DIR = "/Volumes/MacintoshHD/data/daily"

def fix_duplicates(csv_path):
    try:
        if not os.path.exists(csv_path):
            logger.warning(f"File not found: {csv_path}")
            return False

        df = pd.read_csv(csv_path)
        
        if df.empty:
            logger.warning(f"File is empty: {csv_path}")
            return False
            
        logger.info(f"Columns in {csv_path}: {df.columns.tolist()}")

        # Handle column names
        date_col = 'trade_date'
        if 'trade_date' not in df.columns:
            if '交易日期' in df.columns:
                date_col = '交易日期'
            else:
                logger.warning(f"No date column found in {csv_path}")
                return False
            
        original_count = len(df)
        
        # Normalize trade_date
        # Some might be 20240101, some 2024-01-01, some 20240101.0
        # Convert to string first
        df[date_col] = df[date_col].astype(str)
        # Remove .0 suffix
        df[date_col] = df[date_col].str.replace(r'\.0$', '', regex=True)
        # Standardize to YYYYMMDD
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce').dt.strftime('%Y%m%d')
        
        # Drop duplicates based on trade_date (keep last)
        df.drop_duplicates(subset=[date_col], keep='last', inplace=True)
        
        # Sort
        df.sort_values(date_col, inplace=True)
        
        new_count = len(df)
        
        if new_count < original_count:
            logger.info(f"Fixed {csv_path}: Removed {original_count - new_count} duplicates.")
            df.to_csv(csv_path, index=False)
            return True
        else:
            logger.info(f"No duplicates found in {csv_path}")
            return False
            
    except Exception as e:
        logger.error(f"Error fixing {csv_path}: {e}")
        return False

def main():
    logger.info("Starting CSV duplicate fix...")
    
    # Target specific file first
    target_code = "600016"
    target_files = glob.glob(os.path.join(CSV_DATA_DIR, f"{target_code}*.csv"))
    
    for f in target_files:
        fix_duplicates(f)
        
    logger.info("Finished fixing specific target.")
    
    # Optional: Scan all (commented out for now unless requested)
    # all_files = glob.glob(os.path.join(CSV_DATA_DIR, "*.csv"))
    # for f in all_files:
    #     fix_duplicates(f)

if __name__ == "__main__":
    main()
