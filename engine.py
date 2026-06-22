import yfinance as yf
from datetime import date
import database

# 1 Troy Ounce = 31.1034768 Grams
OUNCE_TO_GRAM = 31.1034768

PRECIOUS_METAL_SYMBOLS = {"XAUUSD=X", "XAGUSD=X", "GC=F", "SI=F"}


def get_usd_try_rate():
    try:
        ticker = yf.Ticker("USDTRY=X")
        history = ticker.history(period="1d")
        if not history.empty:
            return float(history["Close"].iloc[-1])
    except Exception as e:
        print(f"Error fetching USD/TRY rate: {e}")
    return 34.50


def _resolve_currency(symbol, asset_class):
    ac = asset_class.upper()
    # GOLD and SILVER assets are entered and tracked in TRY (Gram price)
    if ac in ("GOLD", "SILVER"):
        return "TRY"
    if ac == "BIST" or symbol.endswith(".IS"):
        return "TRY"
    return "USD"


def get_asset_price(symbol, asset_class, usd_rate):
    """
    Fetches the current price for a symbol.
    Returns: (price, currency)
    """
    symbol = symbol.upper().strip()
    ac = asset_class.upper()

    try:
        # Special handling for Gold/Silver Gram calculation
        if ac in ["GOLD", "SILVER"] or symbol in ["XAUUSD=X", "XAGUSD=X"]:
            target_symbol = symbol if "=" in symbol else ("XAUUSD=X" if ac == "GOLD" else "XAGUSD=X")
            ticker = yf.Ticker(target_symbol)
            history = ticker.history(period="5d")
            if not history.empty:
                ounce_price_usd = float(history["Close"].iloc[-1])
                # Convert Ounce USD -> Gram TRY
                gram_price_try = (ounce_price_usd * usd_rate) / OUNCE_TO_GRAM
                return gram_price_try, "TRY"

        ticker = yf.Ticker(symbol)
        history = ticker.history(period="5d")
        if not history.empty:
            price = float(history["Close"].iloc[-1])
            currency = _resolve_currency(symbol, asset_class)
            return price, currency
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
            currency = _resolve_currency(symbol, asset_class)

        # Cost and Value calculations
        # GOLD and SILVER assets are already handled as Gram TRY in this logic
        if currency == "TRY":
            cost_try = amount * avg_price
            value_try = amount * current_price
        else:
            # USD Assets (US Stocks, Crypto) - entered in USD, shown in TRY
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
