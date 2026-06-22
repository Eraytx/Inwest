import engine
import database
import config
import os
import json

PRECIOUS_METAL_LABELS = {
    "XAUUSD=X": "Altın (Ons)",
    "XAGUSD=X": "Gümüş (Ons)",
    "GC=F": "Altın Vadeli",
    "SI=F": "Gümüş Vadeli",
}


def _format_asset_line(asset):
    symbol = asset["symbol"]
    label = PRECIOUS_METAL_LABELS.get(symbol, symbol)
    ac = asset.get("asset_class", "")
    return (
        f"- **{label}** ({ac}): {asset['amount']:.4g} adet, "
        f"değer {asset['value_try']:,.2f} TL, "
        f"kâr/zarar %{asset['profit_percent']:.2f}"
    )


def _build_portfolio_context(metrics):
    lines = [
        f"Toplam değer: {metrics['total_value_try']:,.2f} TL",
        f"Toplam maliyet: {metrics['total_cost_try']:,.2f} TL",
        f"Net kâr/zarar: {metrics['total_profit_try']:,.2f} TL (%{metrics['total_profit_percent']:.2f})",
        f"Günlük değişim: %{metrics['daily_change_percent']:.2f}",
        f"USD/TRY: {metrics['usd_try_rate']:.4f}",
        "",
        "Varlıklar:",
    ]
    for asset in metrics.get("assets", []):
        lines.append(_format_asset_line(asset))
    if not metrics.get("assets"):
        lines.append("- Portföyde henüz varlık yok.")
    return "\n".join(lines)


def _generate_with_gemini(api_key, metrics, report_type):
    from google import genai

    client = genai.Client(api_key=api_key)
    context = _build_portfolio_context(metrics)
    prompt = f"""Sen deneyimli bir Türk finans analistisin. Aşağıdaki portföy verilerine dayanarak {report_type} analiz raporu yaz.

Portföy Verileri:
{context}

Raporu Türkçe yaz. Markdown formatında olsun ve şu başlıkları kullan:
## Portföy Özeti
## Varlık Dağılımı ve Performans
## Risk Değerlendirmesi
## Öneriler

Kısa, net ve yatırımcı dostu bir dil kullan. Gerçekçi ol, spekülasyon yapma.
Altın ve gümüş varsa değerli madenler perspektifinden de yorumla."""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    return response.text.strip()


def _generate_fallback_report(metrics, report_type):
    assets = metrics.get("assets", [])
    report_text = f"## Portföy Özeti ({report_type.capitalize()})\n\n"
    report_text += (
        f"Portföyünüzün toplam değeri **{metrics['total_value_try']:,.2f} TL** seviyesindedir. "
        f"Bugünkü değişim **%{metrics['daily_change_percent']:.2f}**.\n\n"
    )

    if assets:
        report_text += "## Varlık Dağılımı ve Performans\n\n"
        for asset in assets:
            report_text += _format_asset_line(asset) + "\n"
        report_text += "\n## Öneriler\n\n"
        if metrics["total_profit_percent"] > 0:
            report_text += "Genel stratejiniz kârlı görünüyor. Pozisyonlarınızı düzenli takip etmeye devam edin."
        else:
            report_text += "Piyasa koşulları portföyünüz üzerinde baskı yaratıyor. Destek seviyelerini takip etmek faydalı olabilir."
    else:
        report_text += "Henüz portföyünüzde varlık bulunmuyor. İlk işleminizi ekleyerek takibe başlayabilirsiniz."

    return report_text


def generate_ai_report(user_id, report_type="daily"):
    metrics = engine.calculate_portfolio(user_id)
    api_key = database.get_user_gemini_key(user_id) or config.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")

    if api_key:
        try:
            report_text = _generate_with_gemini(api_key, metrics, report_type)
        except Exception as e:
            print(f"Gemini API error, using fallback: {e}")
            report_text = _generate_fallback_report(metrics, report_type)
            report_text += f"\n\n*Not: AI servisi geçici olarak kullanılamadı ({e}). Şablon rapor gösteriliyor.*"
    else:
        report_text = _generate_fallback_report(metrics, report_type)
        report_text += "\n\n*Not: Gemini API anahtarı tanımlı değil. Ayarlar'dan anahtar ekleyerek gerçek AI analizi alabilirsiniz.*"

    database.save_report(user_id, report_type, report_text, metrics)
    return report_text
