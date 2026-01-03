import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

def verify_units():
    code = "600990"
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=10)).strftime("%Y%m%d")
    
    print(f"Fetching {code} from {start_date} to {end_date}...")
    try:
        df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="")
        if df.empty:
            print("No data returned.")
            return

        print("Columns:", df.columns.tolist())
        last_row = df.iloc[-1]
        print("\nLast Row Data:")
        print(last_row)
        
        vol = last_row['成交量']
        amt = last_row['成交额']
        
        print(f"\nVolume: {vol}")
        print(f"Amount: {amt}")
        
        # Rough check
        # Price ~ 10 RMB
        # Vol ~ 200,000 (Lots) or 20,000,000 (Shares)
        # Amt ~ 200,000,000 (Yuan)
        
        close_price = last_row['收盘']
        print(f"Close Price: {close_price}")
        
        estimated_amt_if_vol_is_lots = vol * 100 * close_price
        estimated_amt_if_vol_is_shares = vol * close_price
        
        print(f"\nIf Vol is Lots (x100): Estimated Amt = {estimated_amt_if_vol_is_lots:,.2f}")
        print(f"If Vol is Shares:      Estimated Amt = {estimated_amt_if_vol_is_shares:,.2f}")
        print(f"Actual Amount:         {amt:,.2f}")
        
        if abs(amt - estimated_amt_if_vol_is_lots) < abs(amt - estimated_amt_if_vol_is_shares):
            print("\nCONCLUSION: Volume is in LOTS (手).")
        else:
            print("\nCONCLUSION: Volume is in SHARES (股).")
            
        # Check Amount Unit
        # If Actual Amount ~ Estimated (Yuan), then Amount is in Yuan.
        # If Actual Amount ~ Estimated / 1000, then Amount is in 1000 Yuan.
        
        ratio = amt / estimated_amt_if_vol_is_lots
        print(f"Ratio (Actual Amt / Est Amt (from Lots)): {ratio:.4f}")
        
        if 0.9 < ratio < 1.1:
            print("CONCLUSION: Amount is in YUAN (元).")
        elif 0.0009 < ratio < 0.0011:
            print("CONCLUSION: Amount is in 1000 YUAN (千元).")
        else:
            print("CONCLUSION: Amount unit is UNCLEAR.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_units()
