import os
import requests
import pandas as pd
import redis
import json

# --- 1. Configuration & Constants ---
OANDA_API_URL = "https://api-fxpractice.oanda.com/v3"
OANDA_TOKEN = "ee3a5beb62067a6e36424d00d382b394-fc15159e23cbcf71a96a038f54b9c007"        
ACCOUNT_ID = "101-004-39631650-001"       
INSTRUMENT = "EUR_USD"
GRANULARITY = "H1"                         
COUNT = 100                                

# Connect to the local Docker Redis instance
r = redis.Redis(host='localhost', port=6379, password='secure_redis_password_2026', decode_responses=True)

def fetch_historical_candles():
    """
    Makes an HTTP GET request to OANDA to fetch recent candlestick data.
    Returns a pandas DataFrame for numerical processing.
    """
    headers = {
        "Authorization": f"Bearer {OANDA_TOKEN}",
        "Content-Type": "application/json"
    }
    params = {
        "granularity": GRANULARITY,
        "count": COUNT
    }
    
    url = f"{OANDA_API_URL}/instruments/{INSTRUMENT}/candles"
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Error fetching data from OANDA: {response.text}")
        return None
        
    data = response.json()
    
    # Extract only the complete candles and format them into a flat structure
    parsed_candles = []
    for candle in data.get('candles', []):
        if candle['complete']:
            parsed_candles.append({
                "time": candle['time'],
                "open": float(candle['mid']['o']),
                "high": float(candle['mid']['h']),
                "low": float(candle['mid']['l']),
                "close": float(candle['mid']['c']),
                "volume": int(candle['volume'])
            })
            
    return pd.DataFrame(parsed_candles)

def calculate_indicators(df):
    """
    Applies vector math via pandas to calculate technical indicators 
    without requiring heavy C++ compilation libraries like TA-Lib.
    """
    # Calculate 14-period Exponential Moving Average (EMA)
    df['ema_14'] = df['close'].ewm(span=14, adjust=False).mean()
    
    # Calculate 14-period Relative Strength Index (RSI)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    
    rs = gain / loss
    df['rsi_14'] = 100 - (100 / (1 + rs))
    
    return df

def stream_latest_state_to_cache(df):
    """
    Extracts the most recent calculated row and stores it in Redis 
    with a 5-minute Time-To-Live (TTL) to ensure data stays fresh.
    """
    latest_row = df.iloc[-1]
    
    market_state = {
        "instrument": INSTRUMENT,
        "time": latest_row['time'],
        "close": latest_row['close'],
        "ema_14": round(latest_row['ema_14'], 5),
        "rsi_14": round(latest_row['rsi_14'], 2)
    }
    
    r.set(f"market:{INSTRUMENT}:latest", json.dumps(market_state), ex=300)
    print(f"Successfully cached market state in Redis: {market_state}")

if __name__ == "__main__":
    print("Starting market ingestion pipeline...")
    df_candles = fetch_historical_candles()
    
    if df_candles is not None and not df_candles.empty:
        df_analyzed = calculate_indicators(df_candles)
        stream_latest_state_to_cache(df_analyzed)