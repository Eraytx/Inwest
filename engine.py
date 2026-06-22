import yfinance as yf
from datetime import date
import database

# 1 Troy Ounce = 31.1034768 Grams
OUNCE_TO_GRAM = 31.1034768

def get_usd_try_rate():
    """Fetches the latest USD/TRY exchange rate."""
    for sym in ["USDTRY=X", "TRY=X"]:
        try:
            ticker = yf.Ticker(sym)
            # Try fast_info first (most recent)
            if hasattr(ticker, 'fast_info') and 'last_price' in ticker.fast_info:
                return float(ticker.fast_info['last_price'])
            # Fallback to history
            history = ticker.history(period="1d")
            if not history.empty:
                return float(history["Close"].iloc[-1])
        except Exception as e:
            print(f"Error fetching USD/TRY rate from {sym}: {e}")
    return 34.50 # Hard fallback

def get_asset_price(symbol, asset_class, usd_rate):
    """
    Fetches the current price for a symbol.
    Returns: (price, currency)
    """
    symbol = symbol.upper().strip()
    ac = asset_class.upper()

    try:
        # Special handling for Gold/Silver Gram calculation (TRY)
        if ac in ["GOLD", "SILVER"] or symbol in ["XAUUSD=X", "XAGUSD=X"]:
            target_symbol = symbol if "=" in symbol else ("XAUUSD=X" if ac == "GOLD" else "XAGUSD=X")

            # Try to get the Ounce price in USD
            ticker = yf.Ticker(target_symbol)
            ounce_price_usd = None

            if hasattr(ticker, 'fast_info') and 'last_price' in ticker.fast_info:
                ounce_price_usd = float(ticker.fast_info['last_price'])

            if ounce_price_usd is None:
                history = ticker.history(period="5d")
                if not history.empty:
                    ounce_price_usd = float(history["Close"].iloc[-1])

            if ounce_price_usd:
                # Convert Ounce USD -> Gram TRY
                gram_price_try = (ounce_price_usd * usd_rate) / OUNCE_TO_GRAM
                print(f"Calculated Gram price for {target_symbol}: {gram_price_try} TL")
                return gram_price_try, "TRY"

        # Standard Assets (BIST, Crypto, US Stocks)
        ticker = yf.Ticker(symbol)
        current_price = None

        if hasattr(ticker, 'fast_info') and 'last_price' in ticker.fast_info:
            current_price = float(ticker.fast_info['last_price'])

        if current_price is None:
            history = ticker.history(period="5d")
            if not history.empty:
                current_price = float(history["Close"].iloc[-1])

        if current_price:
            # Resolve currency
            if ac == "BIST" or symbol.endswith(".IS"):
                currency = "TRY"
            else:
                currency = "USD"
            return current_price, currency

    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")

    return None, None

def _display_name(symbol, asset_class):
    ac = asset_class.upper()
    if ac == "GOLD" or symbol == "XAUUSD=X":
        return "Gram Altın"
    if ac == "SILVER" or symbol == "XAGUSD=X":
        return "Gram Gümüş"
    if symbol.endswith(".IS"):
        return symbol.replace(".IS", "")
    if symbol.endswith("-USD"):
        return symbol.replace("-USD", "")
    return symbol

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

        current_price, currency = get_asset_price(symbol, asset_class, usd_try)

        if current_price is None:
            current_price = avg_price
            # Default currency resolution if fetch fails
            ac = asset_class.upper()
            currency = "TRY" if (ac in ["BIST", "GOLD", "SILVER"] or symbol.endswith(".IS")) else "USD"

        # Cost and Value calculations
        if currency == "TRY":
            cost_try = amount * avg_price
            value_try = amount * current_price
        else:
            # USD Assets
            cost_try = (amount * avg_price) * usd_try
            value_try = (amount * current_price) * usd_try

        profit_try = value_try - cost_try
        profit_percent = (profit_try / cost_try * 100.0) if cost_try > 0 else 0.0

        total_cost_try += cost_try
        total_value_try += value_try

        asset_details.append({
            "symbol": symbol,
            "display_name": _display_name(symbol, asset_class),
            "asset_class": asset_class,
            "amount": amount,
            "avg_price": avg_price,
            "current_price": current_price,
            "currency": currency,
            "cost_try": cost_try,
            "value_try": value_try,
            "profit_try": profit_try,
            "profit_percent": profit_percent,
        })

    total_profit_try = total_value_try - total_cost_try
    total_profit_percent = (total_profit_try / total_cost_try * 100.0) if total_cost_try > 0 else 0.0

    history = database.get_portfolio_history(user_id, limit=2)
    if len(history) >= 2:
        prev_value = history[-2]["total_value"]
        daily_change_percent = ((total_value_try - prev_value) / prev_value * 100.0) if prev_value > 0 else 0.0
    elif history:
        prev_value = history[-1]["total_value"]
        daily_change_percent = ((total_value_try - prev_value) / prev_value * 100.0) if prev_value > 0 else 0.0
    else:
        daily_change_percent = 0.0

    today_str = date.today().isoformat()
    database.save_portfolio_history(user_id, today_str, total_value_try, total_cost_try, daily_change_percent)

    for detail in asset_details:
        detail["allocation_percent"] = (
            (detail["value_try"] / total_value_try * 100.0) if total_value_try > 0 else 0.0
        )

    return {
        "date": today_str,
        "usd_try_rate": usd_try,
        "total_cost_try": total_cost_try,
        "total_value_try": total_value_try,
        "total_profit_try": total_profit_try,
        "total_profit_percent": total_profit_percent,
        "daily_change_percent": daily_change_percent,
        "assets": asset_details,
    }
