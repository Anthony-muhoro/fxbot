import redis
import json
import time

# --- 1. Connection Configuration ---
r = redis.Redis(host='localhost', port=6379, password='secure_redis_password_2026', decode_responses=True)
INSTRUMENT = "EUR_USD"

def check_strategy_signals():
    """
    Retrieves the latest market data from Redis cache and evaluates
    it against predefined risk and entry criteria.
    """
    state_json = r.get(f"market:{INSTRUMENT}:latest")
    
    if not state_json:
        print("No market state found in cache. Awaiting ingestion tick...")
        return

    market_state = json.loads(state_json)
    rsi = market_state.get("rsi_14")
    close_price = market_state.get("close")
    
    print(f"Analyzing {INSTRUMENT} | Price: {close_price} | RSI: {rsi}")

    # --- 2. Execution Logic ---
    # Condition A: Market is Oversold (Trigger BUY)
    if rsi <= 30:
        signal_payload = {
            "instrument": INSTRUMENT,
            "side": "BUY",
            "units": "1000", 
            "reason": f"RSI indicates oversold condition at {rsi}"
        }
        r.publish("trading_signals", json.dumps(signal_payload))
        print(f"SIGNAL SENT: Published BUY execution event.")

    # Condition B: Market is Overbought (Trigger SELL)
    elif rsi >= 70:
        signal_payload = {
            "instrument": INSTRUMENT,
            "side": "SELL",
            "units": "1000",
            "reason": f"RSI indicates overbought condition at {rsi}"
        }
        r.publish("trading_signals", json.dumps(signal_payload))
        print(f"SIGNAL SENT: Published SELL execution event.")
        
    else:
        print("Market conditions neutral. No execution criteria met.")

if __name__ == "__main__":
    print("Launching Python Decision Engine Loop...")
    
    # 3. Continuous Evaluation Loop
    try:
        while True:
            check_strategy_signals()
            time.sleep(5) 
    except KeyboardInterrupt:
        print("Decision engine shut down by user.")