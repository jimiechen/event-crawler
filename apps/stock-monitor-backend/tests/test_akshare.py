
import akshare as ak
import pandas as pd

def main():
    code = "603601"
    start_date = "20251120"
    end_date = "20251210"
    print(f"Fetching {code} from {start_date} to {end_date}...")
    try:
        df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
        if df is not None and not df.empty:
            print("Success!")
            print(df.head())
        else:
            print("Empty dataframe returned.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
