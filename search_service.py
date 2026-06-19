import urllib.parse
import urllib.request
import json

def search_symbols(query, asset_class=None):
    """
    Queries Yahoo Finance's autocomplete search API.
    Optionally filters results based on asset class.
    """
    if not query or len(query.strip()) < 1:
        return []
        
    query_clean = query.strip()
    query_encoded = urllib.parse.quote(query_clean)
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query_encoded}"
    
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            raw_data = response.read().decode('utf-8')
            data = json.loads(raw_data)
            
        quotes = data.get("quotes", [])
        results = []
        
        for q in quotes:
            symbol = q.get("symbol", "").upper()
            name = q.get("shortname") or q.get("longname") or symbol
            quote_type = q.get("quoteType", "")
            
            # Apply asset class filtering heuristics
            if asset_class:
                ac_upper = asset_class.upper()
                if ac_upper == "BIST":
                    if not symbol.endswith(".IS"):
                        # If query is short, also search without suffix but we only suggest with .IS for BIST trades
                        continue
                elif ac_upper in ["US_STOCKS", "US"]:
                    # US Equities: quoteType must be EQUITY or ETF, and symbol should not contain non-US suffixes
                    is_us_stock = quote_type in ["EQUITY", "ETF"]
                    if is_us_stock:
                        parts = symbol.split(".")
                        if len(parts) > 1:
                            suffix = parts[-1]
                            if suffix not in ["A", "B", "K"]:
                                continue
                    else:
                        continue
                elif ac_upper == "CRYPTO":
                    if quote_type != "CRYPTO" and "-USD" not in symbol:
                        continue
                        
            results.append({
                "symbol": symbol,
                "name": name,
                "type": quote_type
            })
            
        return results
    except Exception as e:
        print(f"Error searching symbols: {e}")
        return []

if __name__ == "__main__":
    print("Testing BIST search for 'FR'...")
    res1 = search_symbols("FR", "BIST")
    for r in res1:
        print(r)
    print("\nTesting Crypto search for 'BTC'...")
    res2 = search_symbols("BTC", "Crypto")
    for r in res2:
        print(r)
