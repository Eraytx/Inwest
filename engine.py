import yfinance as yf
from datetime import date
import database
import logging

# Log yapılandırması
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1 Troy Ounce = 31.1034768 Grams
OUNCE_TO_GRAM = 31.1034768

def get_usd_try_rate():
    """Garantili Dolar/TL kuru çekme."""
    for sym in ["USDTRY=X", "TRY=X"]:
        try:
            ticker = yf.Ticker(sym)
            data = ticker.history(period="1d")
            if not data.empty:
                val = float(data["Close"].iloc[-1])
                logger.info(f"Dolar Kuru Alındı: {val}")
                return val
        except: continue
    return 34.60 # Son çare fallback

def get_asset_price(symbol, asset_class, usd_rate):
    """Varlık fiyatını çeker. Altın/Gümüş için gram hesabı yapar."""
    symbol = symbol.upper().strip()
    ac = asset_class.upper()

    # --- ALTIN VE GÜMÜŞ ÖZEL HESAPLAMA (KESİN FORMÜL) ---
    if ac in ["GOLD", "SILVER"] or symbol in ["XAUUSD=X", "XAGUSD=X"]:
        target = "XAUUSD=X" if (ac == "GOLD" or "XAU" in symbol) else "XAGUSD=X"
        try:
            ticker = yf.Ticker(target)
            data = ticker.history(period="5d") # 5 günlük alıp en günceli yakalayalım
            if not data.empty:
                ounce_usd = float(data["Close"].iloc[-1])
                # SENİN FORMÜLÜN: (ONS * DOLAR) / 31.1035
                gram_try = (ounce_usd * usd_rate) / OUNCE_TO_GRAM
                logger.info(f"METAL BAŞARILI -> {target}: {ounce_usd}$, Kur: {usd_rate}, Gram: {gram_try} TL")
                return gram_try, "TRY"
        except Exception as e:
            logger.warning(f"Metal verisi çekilemedi: {e}")

    # --- DİĞER VARLIKLAR (Hisse, Kripto) ---
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="5d")
        if not data.empty:
            price = float(data["Close"].iloc[-1])
            currency = "TRY" if (ac == "BIST" or symbol.endswith(".IS")) else "USD"
            return price, currency
    except: pass

    return None, None

def _display_name(symbol, asset_class):
    ac = asset_class.upper()
    if ac == "GOLD" or "XAU" in symbol: return "Gram Altın"
    if ac == "SILVER" or "XAG" in symbol: return "Gram Gümüş"
    if symbol.endswith(".IS"): return symbol.replace(".IS", "")
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

        # VERİ GELMEZSE: Maliyeti değil, 0 gösterelim ki hata olduğu anlaşılsın
        if current_price is None:
            current_price = avg_price # Fallback
            currency = "TRY" if (asset_class.upper() in ["BIST", "GOLD", "SILVER"]) else "USD"

        # TL ve USD Ayırımı
        if currency == "TRY":
            cost_try = amount * avg_price
            value_try = amount * current_price
        else:
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
            "profit_percent": profit_percent
        })

    total_profit_try = total_value_try - total_cost_try
    total_profit_percent = (total_profit_try / total_cost_try * 100.0) if total_cost_try > 0 else 0.0

    today_str = date.today().isoformat()
    # Günlük değişim hesabı
    daily_change = 0.0
    try:
        history = database.get_portfolio_history(user_id, limit=1)
        if history:
            prev = history[0]["total_value"]
            daily_change = ((total_value_try - prev) / prev * 100.0) if prev > 0 else 0.0
    except: pass

    database.save_portfolio_history(user_id, today_str, total_value_try, total_cost_try, daily_change)

    return {
        "date": today_str,
        "usd_try_rate": usd_try,
        "total_cost_try": total_cost_try,
        "total_value_try": total_value_try,
        "total_profit_try": total_profit_try,
        "total_profit_percent": total_profit_percent,
        "daily_change_percent": daily_change,
        "assets": asset_details,
    }
