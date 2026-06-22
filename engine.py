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
    """Dolar/TL kurunu çekmek için çoklu kaynak dener."""
    for sym in ["USDTRY=X", "TRY=X", "TRYUSD=X"]:
        try:
            ticker = yf.Ticker(sym)
            data = ticker.history(period="1d")
            if not data.empty:
                val = float(data["Close"].iloc[-1])
                if sym == "TRYUSD=X": val = 1.0 / val
                logger.info(f"Dolar Kuru Başarıyla Alındı: {val}")
                return val
        except: continue
    return 34.65 # Son çare fallback

def get_asset_price(symbol, asset_class, usd_rate):
    """Varlık fiyatını çeker. Altın/Gümüş için gram hesabı yapar."""
    symbol = symbol.upper().strip()
    ac = asset_class.upper()

    # --- ALTIN VE GÜMÜŞ ÖZEL HESAPLAMA ---
    if ac in ["GOLD", "SILVER"] or any(s in symbol for s in ["XAU", "XAG"]):
        # Altın için öncelik XAUUSD=X, yedek GC=F
        # Gümüş için öncelik XAGUSD=X, yedek SI=F
        is_gold = (ac == "GOLD" or "XAU" in symbol)
        search_list = ["XAUUSD=X", "GC=F"] if is_gold else ["XAGUSD=X", "SI=F"]

        for target in search_list:
            try:
                ticker = yf.Ticker(target)
                data = ticker.history(period="3d")
                if not data.empty:
                    ounce_usd = float(data["Close"].iloc[-1])
                    # KESİN FORMÜL: (ONS * DOLAR) / 31.1035
                    gram_try = (ounce_usd * usd_rate) / OUNCE_TO_GRAM
                    logger.info(f"HESAPLAMA BAŞARILI -> {target}: {ounce_usd}$, Kur: {usd_rate}, Sonuç: {gram_try} TL/Gram")
                    return gram_try, "TRY"
            except Exception as e:
                logger.warning(f"{target} için veri çekilemedi: {e}")

        logger.error(f"KRİTİK: {ac} fiyatı hiçbir kaynaktan alınamadı!")
        return None, "TRY"

    # --- DİĞER VARLIKLAR (Hisse, Kripto) ---
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="3d")
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

        # Fiyat çekilemezse maliyeti göstermek yerine NULL bırakıyoruz ki hata anlaşılsın
        if current_price is None:
            logger.warning(f"Fiyat çekilemedi: {symbol}. Fallback uygulanıyor.")
            current_price = avg_price # Geçici olarak maliyeti göster
            ac = asset_class.upper()
            currency = "TRY" if (ac in ["BIST", "GOLD", "SILVER"]) else "USD"

        # Hesaplama mantığı
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
            "profit_percent": profit_percent,
        })

    total_profit_try = total_value_try - total_cost_try
    total_profit_percent = (total_profit_try / total_cost_try * 100.0) if total_cost_try > 0 else 0.0

    today_str = date.today().isoformat()
    history = database.get_portfolio_history(user_id, limit=1)
    daily_change = 0.0
    if history:
        prev = history[0]["total_value"]
        daily_change = ((total_value_try - prev) / prev * 100.0) if prev > 0 else 0.0

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
