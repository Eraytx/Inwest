import yfinance as yf
from datetime import datetime, date
import database

def get_usd_try_rate():
    """Fetches the current USD/TRY exchange rate from Yahoo Finance."""
    try:
        ticker = yf.Ticker("USDTRY=X")
        # Try to get the latest close or current price
        history = ticker.history(period="1d")
        if not history.empty:
            return float(history["Close"].iloc[-1])
    except Exception as e:
        print(f"Error fetching USD/TRY rate: {e}")
    # Fallback rate if yfinance fails
    return 32.50

def get_asset_price(symbol, asset_class):
    """
    Fetches the current price for a symbol using yfinance.
    Returns: (price, currency)
    """
    symbol = symbol.upper().strip()
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period="1d")
        if not history.empty:
            price = float(history["Close"].iloc[-1])
            # Infer currency
            if asset_class.upper() == "BIST" or symbol.endswith(".IS"):
                currency = "TRY"
            elif "USD" in symbol or asset_class.upper() == "CRYPTO":
                currency = "USD"
            else:
                currency = "USD"
            return price, currency
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
    
    return None, None

def calculate_portfolio():
    """
    Fetches assets, retrieves current market prices, converts currencies,
    calculates portfolio statistics, and records daily history snapshot.
    Returns: a detailed metrics dictionary.
    """
    assets = database.get_assets()
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
        
        # Fallback if fetching fails
        if current_price is None:
            current_price = avg_price
            currency = "TRY" if asset_class == "BIST" else "USD"
            
        # Cost and Value calculations in original currency
        cost_orig = amount * avg_price
        value_orig = amount * current_price
        
        # Convert to TRY for overall totals
        if currency == "USD":
            cost_try = cost_orig * usd_try
            value_try = value_orig * usd_try
            current_price_try = current_price * usd_try
            avg_price_try = avg_price * usd_try
        else:
            cost_try = cost_orig
            value_try = value_orig
            current_price_try = current_price
            avg_price_try = avg_price
            
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
            "profit_percent": profit_percent,
            "avg_price_try": avg_price_try,
            "current_price_try": current_price_try
        })
        
    # Calculate overall stats
    total_profit_try = total_value_try - total_cost_try
    total_profit_percent = (total_profit_try / total_cost_try * 100.0) if total_cost_try > 0 else 0.0
    
    # Calculate daily change percent by comparing with the last history entry
    history = database.get_portfolio_history(limit=1)
    if history:
        prev_value = history[0]["total_value"]
        daily_change_percent = ((total_value_try - prev_value) / prev_value * 100.0) if prev_value > 0 else 0.0
    else:
        daily_change_percent = 0.0
        
    # Save daily history snapshot
    today_str = date.today().isoformat()
    database.save_portfolio_history(
        date=today_str,
        total_value=total_value_try,
        total_cost=total_cost_try,
        daily_change_percent=daily_change_percent
    )
    
    metrics = {
        "date": today_str,
        "usd_try_rate": usd_try,
        "total_cost_try": total_cost_try,
        "total_value_try": total_value_try,
        "total_profit_try": total_profit_try,
        "total_profit_percent": total_profit_percent,
        "daily_change_percent": daily_change_percent,
        "assets": asset_details
    }
    
    return metrics

if __name__ == "__main__":
    # Test execution
    print("Testing portfolio calculation...")
    usd_rate = get_usd_try_rate()
    print(f"Current USD/TRY rate: {usd_rate}")
    froto_price, froto_curr = get_asset_price("FROTO.IS", "BIST")
    print(f"FROTO.IS Price: {froto_price} {froto_curr}")
    btc_price, btc_curr = get_asset_price("BTC-USD", "Crypto")
    print(f"BTC-USD Price: {btc_price} {btc_curr}")
