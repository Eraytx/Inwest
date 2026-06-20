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

    # Heuristic for BIST: if searching for BIST and query doesn't have .IS,
    # try adding it to search if it looks like a ticker.
    search_queries = [query_clean]
    if asset_class and asset_class.upper() == "BIST" and not query_clean.upper().endswith(".IS"):
        search_queries.insert(0, f"{query_clean}.IS") # Prioritize with .IS

    all_results = []
    seen_symbols = set()

    for q_text in search_queries:
        query_encoded = urllib.parse.quote(q_text)
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
            
            for q in quotes:
                symbol = q.get("symbol", "").upper()
                if symbol in seen_symbols:
                    continue

                name = q.get("shortname") or q.get("longname") or symbol
                quote_type = q.get("quoteType", "")

                # Apply asset class filtering heuristics
                keep = True
                if asset_class:
                    ac_upper = asset_class.upper()
                    if ac_upper == "BIST":
                        # If BIST, we strongly prefer .IS but allow matching without if it's EQUITY
                        if not symbol.endswith(".IS") and quote_type != "EQUITY":
                            keep = False
                    elif ac_upper in ["US_STOCKS", "US"]:
                        is_us_stock = quote_type in ["EQUITY", "ETF"]
                        if not is_us_stock:
                            keep = False
                    elif ac_upper == "CRYPTO":
                        if quote_type != "CRYPTO" and "-USD" not in symbol:
                            keep = False

                if keep:
                    seen_symbols.add(symbol)
                    all_results.append({
                        "symbol": symbol,
                        "name": name,
                        "type": quote_type
                    })

            if len(all_results) >= 10:
                break
        except Exception as e:
            print(f"Error searching symbols for {q_text}: {e}")

    return all_results[:15]

if __name__ == "__main__":
    print("Testing BIST search for 'froto'...")
    res1 = search_symbols("froto", "BIST")
    for r in res1:
        print(r)
