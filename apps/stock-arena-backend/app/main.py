from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Stock Arena API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CSV_DATA_PATH = os.getenv("CSV_DATA_PATH", "/Users/mac/Downloads/daily")

class StockSymbol(BaseModel):
    symbol: str
    name: str

class MarketData(BaseModel):
    symbol: str
    price: float
    oracle_price: float
    change24h: float
    volume24h: float
    percentage24h: float
    open_interest: float = 0
    funding_rate: float = 0

class KlineData(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float

def read_csv_files():
    symbols = []
    try:
        if os.path.exists(CSV_DATA_PATH):
            for filename in os.listdir(CSV_DATA_PATH):
                if filename.endswith('.csv'):
                    symbol = filename.replace('.csv', '')
                    symbols.append(StockSymbol(symbol=symbol, name=symbol))
    except Exception as e:
        print(f"Error reading CSV files: {e}")
    return symbols

def read_stock_csv(symbol: str) -> Optional[pd.DataFrame]:
    csv_path = os.path.join(CSV_DATA_PATH, f"{symbol}.csv")
    if not os.path.exists(csv_path):
        return None
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
        # Rename Chinese columns to English
        column_mapping = {
            '股票代码': 'symbol',
            '交易日期': 'timestamp',
            '开盘价': 'open',
            '最高价': 'high',
            '最低价': 'low',
            '收盘价': 'close',
            '昨收价': 'prev_close',
            '涨跌额': 'change_amount',
            '涨跌幅': 'change_percent',
            '成交量(手)': 'volume',
            '成交额(千元)': 'amount'
        }
        df = df.rename(columns=column_mapping)
        return df
    except Exception as e:
        print(f"Error reading CSV for {symbol}: {e}")
        return None

def calculate_market_data(df: pd.DataFrame, symbol: str) -> Optional[MarketData]:
    if df is None or df.empty:
        return None
    
    try:
        latest = df.iloc[-1]
        price = float(latest['close'])
        
        if len(df) >= 2:
            prev = df.iloc[-2]
            change24h = price - float(prev['close'])
            percentage24h = (change24h / float(prev['close'])) * 100 if float(prev['close']) != 0 else 0
        else:
            change24h = 0
            percentage24h = 0
        
        volume24h = float(latest['volume']) if 'volume' in latest else 0
        
        return MarketData(
            symbol=symbol,
            price=price,
            oracle_price=price,
            change24h=change24h,
            volume24h=volume24h,
            percentage24h=percentage24h
        )
    except Exception as e:
        print(f"Error calculating market data for {symbol}: {e}")
        return None

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Stock Arena API is running"}

@app.get("/api/stocks/symbols", response_model=List[StockSymbol])
async def get_stock_symbols():
    symbols = read_csv_files()
    return symbols

@app.get("/api/stocks/market", response_model=List[MarketData])
async def get_market_data(symbols: str):
    symbol_list = symbols.split(',') if symbols else []
    
    market_data_list = []
    for symbol in symbol_list:
        df = read_stock_csv(symbol)
        if df is not None:
            data = calculate_market_data(df, symbol)
            if data:
                market_data_list.append(data)
    
    return market_data_list

@app.get("/api/stocks/klines", response_model=List[KlineData])
async def get_klines(symbol: str, period: str = "1m", limit: int = 1000):
    df = read_stock_csv(symbol)
    if df is None or df.empty:
        return []
    
    try:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        if len(df) > limit:
            df = df.tail(limit)
        
        klines = []
        for _, row in df.iterrows():
            klines.append(KlineData(
                timestamp=row['timestamp'].isoformat(),
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=float(row['volume']) if 'volume' in row else 0
            ))
        
        return klines
    except Exception as e:
        print(f"Error getting klines for {symbol}: {e}")
        return []

@app.get("/api/stocks/patterns")
async def get_patterns(symbol: str):
    return {
        "symbol": symbol,
        "patterns": [],
        "message": "Pattern recognition feature coming soon"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
