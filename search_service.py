import urllib.parse
import urllib.request
import json

PRECIOUS_METAL_SYMBOLS = {
    "GOLD": [
        {"symbol": "XAUUSD=X", "name": "Altın (Spot / Ons)", "type": "CURRENCY"},
        {"symbol": "GC=F", "name": "Altın Vadeli İşlem", "type": "FUTURE"},
    ],
    "SILVER": [
        {"symbol": "XAGUSD=X", "name": "Gümüş (Spot / Ons)", "type": "CURRENCY"},
        {"symbol": "SI=F", "name": "Gümüş Vadeli İşlem", "type": "FUTURE"},
    ],
}


def _precious_metal_results(query, asset_class):
    ac = asset_class.upper()
    if ac not in PRECIOUS_METAL_SYMBOLS:
        return []
    options = PRECIOUS_METAL_SYMBOLS[ac]
    q = query.strip().lower()
    if not q:
        return options
    return [
        item for item in options
        if q in item["symbol"].lower() or q in item["name"].lower()
    ]


def search_symbols(query, asset_class=None):
    if asset_class and asset_class.upper() in PRECIOUS_METAL_SYMBOLS:
        return _precious_metal_results(query, asset_class)

    if not query or len(query.strip()) < 1:
        return []

    query_clean = query.strip()
    search_queries = [query_clean]
    if asset_class and asset_class.upper() == "BIST" and not query_clean.upper().endswith(".IS"):
        search_queries.insert(0, f"{query_clean}.IS")

    all_results = []
    seen_symbols = set()

    for q_text in search_queries:
        query_encoded = urllib.parse.quote(q_text)
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query_encoded}"

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))

            for q in data.get("quotes", []):
                symbol = q.get("symbol", "").upper()
                if symbol in seen_symbols:
                    continue

                name = q.get("shortname") or q.get("longname") or symbol
                quote_type = q.get("quoteType", "")

                keep = True
                if asset_class:
                    ac_upper = asset_class.upper()
                    if ac_upper == "BIST":
                        if not symbol.endswith(".IS") and quote_type != "EQUITY":
                            keep = False
                    elif ac_upper in ["US_STOCKS", "US"]:
                        if quote_type not in ["EQUITY", "ETF"]:
                            keep = False
                    elif ac_upper == "CRYPTO":
                        if quote_type != "CRYPTO" and "-USD" not in symbol:
                            keep = False

                if keep:
                    seen_symbols.add(symbol)
                    all_results.append({"symbol": symbol, "name": name, "type": quote_type})

            if len(all_results) >= 10:
                break
        except Exception as e:
            print(f"Error searching symbols for {q_text}: {e}")

    return all_results[:15]
