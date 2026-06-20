import yfinance as yf
from datetime import datetime, date
import database

def get_usd_try_rate():
    try:
        ticker = yf.Ticker("USDTRY=X")
        history = ticker.history(period="1d")
        if not history.empty:
            return float(history["Close"].iloc[-1])
    except Exception as e:
        print(f"Error fetching USD/TRY rate: {e}")
    return 34.50 # Fallback

def get_asset_price(symbol, asset_class):
    symbol = symbol.upper().strip()
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period="1d")
        if not history.empty:
            price = float(history["Close"].iloc[-1])
            if asset_class.upper() == "BIST" or symbol.endswith(".IS"):
                currency = "TRY"
            else:
                currency = "USD"
            return price, currency
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
    return None, None

def calculate_portfolio(user_id):
    assets = database.get_assets(user_id)
    usd_try = get_usd_try_rate()
    total_cost_try = 0.0
    total_value_try = 0.0
    asset_details = []
    
    for asset in assets:
        symbol = asset["symbol"]
        asset_class = asset["asset_class"]
        amount = asset["amount"]
        avg_price = asset["avg_price"]
        current_price, currency = get_asset_price(symbol, asset_class)
        if current_price is None:
            current_price = avg_price
            currency = "TRY" if asset_class == "BIST" else "USD"
            
        cost_orig = amount * avg_price
        value_orig = amount * current_price
        
        if currency == "USD":
            cost_try = cost_orig * usd_try
            value_try = value_orig * usd_try
        else:
            cost_try = cost_orig
            value_try = value_orig

        profit_try = value_try - cost_try
        profit_percent = (profit_try / cost_try * 100.0) if cost_try > 0 else 0.0
        total_cost_try += cost_try
        total_value_try += value_try
        
        asset_details.append({
            "symbol": symbol,
            "asset_class": asset_class,
            "amount": amount,
            "avg_price": avg_price,
            "current_price": current_price,
            "currency": currency,
            "cost_try": cost_try,
            "value_try": value_try,
            "profit_try": profit_try,
            "profit_percent": profit_percent
        })
        
    total_profit_try = total_value_try - total_cost_try
    total_profit_percent = (total_profit_try / total_cost_try * 100.0) if total_cost_try > 0 else 0.0
    
    history = database.get_portfolio_history(user_id, limit=1)
    if history:
        prev_value = history[0]["total_value"]
        daily_change_percent = ((total_value_try - prev_value) / prev_value * 100.0) if prev_value > 0 else 0.0
    else:
        daily_change_percent = 0.0
        
    today_str = date.today().isoformat()
    database.save_portfolio_history(user_id, today_str, total_value_try, total_cost_try, daily_change_percent)
    
    return {
        "date": today_str,
        "usd_try_rate": usd_try,
        "total_cost_try": total_cost_try,
        "total_value_try": total_value_try,
        "total_profit_try": total_profit_try,
        "total_profit_percent": total_profit_percent,
        "daily_change_percent": daily_change_percent,
        "assets": asset_details
    }
