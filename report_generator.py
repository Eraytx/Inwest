import config
import database
import news_service
import json
from datetime import datetime

def generate_report_prompt(metrics, news):
    """
    Constructs the prompt for the LLM detailing portfolio performance and news.
    """
    # Format asset details
    asset_breakdown_str = ""
    for asset in metrics["assets"]:
        asset_breakdown_str += (
            f"- **{asset['symbol']}** ({asset['asset_class']}):\n"
            f"  * Miktar: {asset['amount']:.4f}\n"
            f"  * Ortalama Maliyet: {asset['avg_price']:.2f} {asset['currency']}\n"
            f"  * Güncel Fiyat: {asset['current_price']:.2f} {asset['currency']}\n"
            f"  * Toplam Maliyet (TL): {asset['cost_try']:.2f} TL\n"
            f"  * Güncel Değer (TL): {asset['value_try']:.2f} TL\n"
            f"  * Kâr/Zarar: {asset['profit_try']:.2f} TL ({asset['profit_percent']:.2f}%)\n\n"
        )
        
    # Format news details
    news_str = ""
    if news:
        for idx, item in enumerate(news):
            news_str += f"{idx+1}. [{item['source']}] {item['title']}\n"
    else:
        news_str = "Portföydeki varlıklar hakkında son 24 saatte kritik bir haber bulunmamaktadır.\n"

    # Construct the instruction
    prompt = f"""
Sen deneyimli bir finans analisti ve portföy yöneticisisin. 
Aşağıda verilen portföy performans verilerini ve son haberleri analiz ederek Türkçe dilinde profesyonel, samimi, anlaşılır ve yorum içeren bir günlük/haftalık finans raporu oluştur.

Rapor Formatı:
1. **Genel Durum**: Portföyün toplam değeri, toplam kâr/zararı, toplam maliyeti ve günlük performansını (% ve TL olarak) özetle.
2. **Performans Analizi (Öne Çıkanlar)**: 
   - En çok kazandıran varlık hangisi?
   - En çok kaybettiren varlık hangisi?
   - Genel BIST / Kripto dağılımı nasıl?
3. **Haberler & Beklentiler**: Sağlanan haber başlıklarını ve piyasa durumunu dikkate alarak portföydeki varlıkları etkileyebilecek faktörleri yorumla.
4. **Gelecek Stratejisi & Tavsiyeler**: Portföyün dengelenmesi (rebalancing) veya izlenmesi gereken kritik seviyeler hakkında genel, yatırım tavsiyesi olmayan analist yorumları yap.

Analiz edilecek veriler:
- Rapor Tarihi: {metrics['date']}
- Güncel USD/TRY Kuru: {metrics['usd_try_rate']:.4f}
- Toplam Maliyet: {metrics['total_cost_try']:.2f} TL
- Toplam Güncel Değer: {metrics['total_value_try']:.2f} TL
- Toplam Net Kâr/Zarar: {metrics['total_profit_try']:.2f} TL ({metrics['total_profit_percent']:.2f}%)
- Günlük Değişim Yüzdesi: {metrics['daily_change_percent']:.2f}%

Varlık Kırılımları:
{asset_breakdown_str}

Gündemdeki Haber Başlıkları:
{news_str}

Lütfen raporu Markdown formatında hazırla ve gereksiz teknik terimlerden kaçınıp okuyucuyu bilgilendirici bir tonda yaz.
"""
    return prompt

def generate_simulated_report(metrics, news):
    """
    Generates a high-quality simulated report when no API key is available.
    """
    best_asset = None
    worst_asset = None
    bist_val = 0.0
    crypto_val = 0.0
    
    for asset in metrics["assets"]:
        if asset["asset_class"] == "BIST":
            bist_val += asset["value_try"]
        else:
            crypto_val += asset["value_try"]
            
        if best_asset is None or asset["profit_percent"] > best_asset["profit_percent"]:
            best_asset = asset
        if worst_asset is None or asset["profit_percent"] < worst_asset["profit_percent"]:
            worst_asset = asset

    total_val = metrics["total_value_try"]
    bist_pct = (bist_val / total_val * 100) if total_val > 0 else 0
    crypto_pct = (crypto_val / total_val * 100) if total_val > 0 else 0

    best_str = f"**{best_asset['symbol']}** (%{best_asset['profit_percent']:.1f})" if best_asset else "Yok"
    worst_str = f"**{worst_asset['symbol']}** (%{worst_asset['profit_percent']:.1f})" if worst_asset else "Yok"

    sim_text = f"""
# 📋 Portföy Performans ve Analiz Raporu (Simüle Edilmiş)

> ⚠️ **Not**: API Anahtarı (Gemini veya Claude) yapılandırılmadığı için bu rapor yerel analitik motoru tarafından şablon bazlı simüle edilerek üretilmiştir.

---

## 1. Genel Durum
Portföyünüzün bugünkü toplam değeri **{metrics['total_value_try']:,.2f} TL** seviyesindedir. 
- **Toplam Yatırım Maliyeti**: {metrics['total_cost_try']:,.2f} TL
- **Net Kâr/Zarar Durumu**: {metrics['total_profit_try']:,.2f} TL ({metrics['total_profit_percent']:.2f}%)
- **Günlük Performans**: {metrics['daily_change_percent']:.2f}%

Mevcut durumda USD/TRY kuru **{metrics['usd_try_rate']:.4f}** olarak hesaplamalara yansıtılmıştır.

---

## 2. Performans Analizi (Öne Çıkanlar)
- 🚀 **En İyi Performans**: {best_str} ile gerçekleşti. Bu varlıktaki pozisyonunuz portföy kârlılığını yukarı taşımaktadır.
- 📉 **Zayıf Performans**: {worst_str} ile izlendi. Bu varlıktaki ortalama maliyetinizi ve piyasa eğilimini kontrol etmek faydalı olabilir.
- 📊 **Portföy Dağılımı**:
  - BIST (Hisse): %{bist_pct:.1f}
  - Kripto Para: %{crypto_pct:.1f}

---

## 3. Haberler & Beklentiler
Piyasadaki son gelişmelere baktığımızda aşağıdaki haberler dikkat çekiyor:
"""
    for idx, item in enumerate(news[:3]):
        sim_text += f"\n- **{item['source']}**: {item['title']} ([Habere Git]({item['link']}))"
        
    sim_text += f"""

Bu haber akışı, özellikle döviz bazlı varlıklar (kripto para) ve Borsa İstanbul hisseleriniz üzerinde hacim hareketliliğine yol açabilir.

---

## 4. Gelecek Stratejisi & Tavsiyeler
- **Varlık Dağılımı**: BIST ve Kripto dağılımınız dengeli duruyor. Risk iştahınıza göre bu oranı korumak veya kâr realizasyonuna gitmek düşünülebilir.
- **Kripto Varlıkları**: Kripto pozisyonunuz doğrudan küresel dolar likiditesi ve Fed faiz beklentilerinden etkilenmektedir. Fed haberlerini yakından izlemeniz önerilir.
- **BIST Hisseleri**: Enflasyonist süreçte KAP haberleri ve bilançolar hisse bazlı hareketleri ayrıştırabilir.
"""
    return sim_text

def generate_ai_report(report_type="daily"):
    """
    Orchestrates the report generation: fetches metrics and news, prompts LLM,
    and saves the generated text into database.
    """
    import engine
    
    # 1. Fetch current metrics
    try:
        metrics = engine.calculate_portfolio()
    except Exception as e:
        print(f"Error calculating portfolio metrics for report: {e}")
        return None
        
    # 2. Fetch recent news
    news = news_service.fetch_portfolio_news(metrics["assets"])
    
    # 3. Create prompt
    prompt = generate_report_prompt(metrics, news)
    
    report_text = ""
    # 4. Hit LLM API
    if config.GEMINI_API_KEY:
        print("Generating report using Gemini API...")
        try:
            from google import genai
            client = genai.Client(api_key=config.GEMINI_API_KEY)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            report_text = response.text
        except Exception as e:
            print(f"Gemini API generation failed: {e}")
            
    elif config.ANTHROPIC_API_KEY:
        print("Generating report using Anthropic Claude API...")
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            report_text = message.content[0].text
        except Exception as e:
            print(f"Anthropic API generation failed: {e}")
            
    # Fallback to simulated if all else fails or keys are missing
    if not report_text:
        print("No API keys configured or API failed. Using local simulated report generator.")
        report_text = generate_simulated_report(metrics, news)
        
    # 5. Save report to DB
    database.save_report(report_type, report_text, metrics)
    return report_text

if __name__ == "__main__":
    print("Testing report generation...")
    # Add dummy assets to DB if empty
    assets = database.get_assets()
    if not assets:
        print("No assets in DB. Creating dummy assets for testing report generator...")
        database.add_transaction("FROTO.IS", "BIST", "BUY", 10, 900.0)
        database.add_transaction("BTC-USD", "Crypto", "BUY", 0.05, 65000.0)
        
    report = generate_ai_report("daily")
    print("\n--- GENERATED REPORT ---")
    try:
        print(report)
    except UnicodeEncodeError:
        # Fallback print for consoles that do not support unicode/emojis
        print(report.encode('utf-8', errors='ignore').decode('cp1254', errors='ignore'))
