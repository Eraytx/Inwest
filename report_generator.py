import engine
import database
import config
import os

def generate_ai_report(user_id, report_type="daily"):
    """
    Simulates or generates an AI report based on the specific user's portfolio.
    """
    metrics = engine.calculate_portfolio(user_id)
    assets_str = ", ".join([f"{a['symbol']} ({a['amount']})" for a in metrics['assets']])
    
    report_text = f"Analist Özeti ({report_type.capitalize()}):\n"
    report_text += f"Portföyünüzün toplam değeri {metrics['total_value_try']:,.2f} TL seviyesindedir. "
    report_text += f"Bugünkü değişim %{metrics['daily_change_percent']:.2f}. "

    if metrics['assets']:
        report_text += f"Portföyünüzde öne çıkan varlıklar: {assets_str}. "
        if metrics['total_profit_percent'] > 0:
            report_text += "Genel stratejiniz kârlı görünüyor, pozisyonlarınızı korumaya devam edebilirsiniz."
        else:
            report_text += "Şu anki piyasa koşulları portföyünüz üzerinde baskı yaratıyor, destek noktalarını takip etmek faydalı olabilir."
    else:
        report_text += "Henüz portföyünüzde varlık bulunmuyor. Yatırım yaparak ilk adımı atabilirsiniz."

    database.save_report(user_id, report_type, report_text, metrics)
    return report_text
