import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

def fetch_portfolio_news(assets, limit=5):
    """
    Fetches news headlines from Google News RSS for the symbols in the portfolio.
    """
    if not assets:
        return []
        
    # Extract clean symbols (e.g., FROTO.IS -> FROTO, BTC-USD -> BTC or Bitcoin)
    keywords = []
    for asset in assets:
        symbol = asset["symbol"]
        if symbol.endswith(".IS"):
            clean_symbol = symbol.replace(".IS", "")
            keywords.append(f'"{clean_symbol}"')
        elif "-" in symbol:
            clean_symbol = symbol.split("-")[0]
            keywords.append(f'"{clean_symbol}"')
        else:
            keywords.append(f'"{symbol}"')
            
    # Combine keywords with OR operator
    query_str = " OR ".join(keywords)
    # Search for turkish news regarding these symbols
    query_encoded = urllib.parse.quote(f"({query_str}) (hisse OR kripto OR ekonomi OR borsa)")
    url = f"https://news.google.com/rss/search?q={query_encoded}&hl=tr&gl=TR&ceid=TR:tr"
    
    news_items = []
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        
        # Google News RSS path: channel/item
        for item in root.findall(".//item")[:limit]:
            title = item.find("title").text if item.find("title") is not None else ""
            link = item.find("link").text if item.find("link") is not None else ""
            pub_date_str = item.find("pubDate").text if item.find("pubDate") is not None else ""
            source = item.find("source").text if item.find("source") is not None else "Haber Kaynağı"
            
            # Format title (remove source suffix if present, e.g. "Title - Hürriyet" -> "Title")
            if " - " in title:
                title = " - ".join(title.split(" - ")[:-1])
                
            news_items.append({
                "title": title,
                "link": link,
                "source": source,
                "published": pub_date_str
            })
    except Exception as e:
        print(f"Error fetching portfolio news: {e}")
        # Fallback news list if offline or rate-limited
        news_items = [
            {
                "title": "Borsa İstanbul BIST 100 endeksi günü yükselişle kapattı.",
                "link": "https://www.kap.org.tr",
                "source": "KAP",
                "published": datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
            }
        ]
        
    return news_items

if __name__ == "__main__":
    # Test news service
    test_assets = [{"symbol": "FROTO.IS"}, {"symbol": "BTC-USD"}]
    print("Fetching news for test assets...")
    news = fetch_portfolio_news(test_assets)
    for idx, item in enumerate(news):
        print(f"{idx+1}. [{item['source']}] {item['title']} ({item['published']})")
        print(f"   URL: {item['link']}")
