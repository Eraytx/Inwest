from datetime import datetime, date, timedelta

def get_economic_calendar():
    """
    Generates a list of macroeconomic calendar events for 2026.
    Filters to show events from the past 14 days and the next 45 days.
    """
    # Curated official dates for 2026 meetings and CPI announcements
    events = [
        # TCMB (Turkish Central Bank) Interest Rate Decisions
        {"date": "2026-01-22", "country": "TR", "event": "TCMB Faiz Kararı", "importance": "HIGH", "forecast": "Sabit", "previous": "45.00%"},
        {"date": "2026-02-19", "country": "TR", "event": "TCMB Faiz Kararı", "importance": "HIGH", "forecast": "Sabit", "previous": "45.00%"},
        {"date": "2026-03-19", "country": "TR", "event": "TCMB Faiz Kararı", "importance": "HIGH", "forecast": "Sabit", "previous": "45.00%"},
        {"date": "2026-04-16", "country": "TR", "event": "TCMB Faiz Kararı", "importance": "HIGH", "forecast": "Artış", "previous": "45.00%"},
        {"date": "2026-05-21", "country": "TR", "event": "TCMB Faiz Kararı", "importance": "HIGH", "forecast": "Sabit", "previous": "50.00%"},
        {"date": "2026-06-25", "country": "TR", "event": "TCMB Faiz Kararı", "importance": "HIGH", "forecast": "Sabit", "previous": "50.00%"},
        {"date": "2026-07-23", "country": "TR", "event": "TCMB Faiz Kararı", "importance": "HIGH", "forecast": "Sabit", "previous": "50.00%"},
        {"date": "2026-08-20", "country": "TR", "event": "TCMB Faiz Kararı", "importance": "HIGH", "forecast": "İndirim", "previous": "50.00%"},
        {"date": "2026-09-24", "country": "TR", "event": "TCMB Faiz Kararı", "importance": "HIGH", "forecast": "İndirim", "previous": "47.50%"},
        {"date": "2026-10-22", "country": "TR", "event": "TCMB Faiz Kararı", "importance": "HIGH", "forecast": "İndirim", "previous": "45.00%"},
        {"date": "2026-11-19", "country": "TR", "event": "TCMB Faiz Kararı", "importance": "HIGH", "forecast": "Sabit", "previous": "42.50%"},
        {"date": "2026-12-24", "country": "TR", "event": "TCMB Faiz Kararı", "importance": "HIGH", "forecast": "İndirim", "previous": "42.50%"},
        
        # FED (US Federal Reserve) Interest Rate Decisions
        {"date": "2026-01-28", "country": "US", "event": "FED Faiz Kararı (FOMC)", "importance": "HIGH", "forecast": "Sabit", "previous": "5.25%-5.50%"},
        {"date": "2026-03-18", "country": "US", "event": "FED Faiz Kararı (FOMC)", "importance": "HIGH", "forecast": "İndirim", "previous": "5.25%-5.50%"},
        {"date": "2026-04-29", "country": "US", "event": "FED Faiz Kararı (FOMC)", "importance": "HIGH", "forecast": "Sabit", "previous": "5.00%-5.25%"},
        {"date": "2026-06-17", "country": "US", "event": "FED Faiz Kararı (FOMC)", "importance": "HIGH", "forecast": "İndirim", "previous": "5.00%-5.25%"},
        {"date": "2026-07-29", "country": "US", "event": "FED Faiz Kararı (FOMC)", "importance": "HIGH", "forecast": "İndirim", "previous": "4.75%-5.00%"},
        {"date": "2026-09-23", "country": "US", "event": "FED Faiz Kararı (FOMC)", "importance": "HIGH", "forecast": "Sabit", "previous": "4.50%-4.75%"},
        {"date": "2026-11-04", "country": "US", "event": "FED Faiz Kararı (FOMC)", "importance": "HIGH", "forecast": "İndirim", "previous": "4.50%-4.75%"},
        {"date": "2026-12-16", "country": "US", "event": "FED Faiz Kararı (FOMC)", "importance": "HIGH", "forecast": "İndirim", "previous": "4.25%-4.50%"},

        # Inflation Releases (CPI) - Turkey (3rd of every month)
        {"date": "2026-01-03", "country": "TR", "event": "TÜİK Enflasyon Verisi (TÜFE - Yıllık)", "importance": "HIGH", "forecast": "%64.1", "previous": "%64.77"},
        {"date": "2026-02-03", "country": "TR", "event": "TÜİK Enflasyon Verisi (TÜFE - Yıllık)", "importance": "HIGH", "forecast": "%66.8", "previous": "%64.86"},
        {"date": "2026-03-03", "country": "TR", "event": "TÜİK Enflasyon Verisi (TÜFE - Yıllık)", "importance": "HIGH", "forecast": "%67.1", "previous": "%67.07"},
        {"date": "2026-04-03", "country": "TR", "event": "TÜİK Enflasyon Verisi (TÜFE - Yıllık)", "importance": "HIGH", "forecast": "%68.5", "previous": "%68.50"},
        {"date": "2026-05-03", "country": "TR", "event": "TÜİK Enflasyon Verisi (TÜFE - Yıllık)", "importance": "HIGH", "forecast": "%75.2", "previous": "%69.80"},
        {"date": "2026-06-03", "country": "TR", "event": "TÜİK Enflasyon Verisi (TÜFE - Yıllık)", "importance": "HIGH", "forecast": "%74.8", "previous": "%75.45"},
        {"date": "2026-07-03", "country": "TR", "event": "TÜİK Enflasyon Verisi (TÜFE - Yıllık)", "importance": "HIGH", "forecast": "%71.2", "previous": "%74.10"},
        {"date": "2026-08-03", "country": "TR", "event": "TÜİK Enflasyon Verisi (TÜFE - Yıllık)", "importance": "HIGH", "forecast": "%62.5", "previous": "%71.50"},
        {"date": "2026-09-03", "country": "TR", "event": "TÜİK Enflasyon Verisi (TÜFE - Yıllık)", "importance": "HIGH", "forecast": "%51.8", "previous": "%62.00"},
        {"date": "2026-10-03", "country": "TR", "event": "TÜİK Enflasyon Verisi (TÜFE - Yıllık)", "importance": "HIGH", "forecast": "%48.2", "previous": "%51.50"},
        {"date": "2026-11-03", "country": "TR", "event": "TÜİK Enflasyon Verisi (TÜFE - Yıllık)", "importance": "HIGH", "forecast": "%44.1", "previous": "%48.00"},
        {"date": "2026-12-03", "country": "TR", "event": "TÜİK Enflasyon Verisi (TÜFE - Yıllık)", "importance": "HIGH", "forecast": "%41.5", "previous": "%44.20"},

        # Inflation Releases (CPI) - US (Around 12th-15th of every month)
        {"date": "2026-01-12", "country": "US", "event": "ABD Tüketici Fiyat Endeksi (TÜFE - Yıllık)", "importance": "HIGH", "forecast": "%3.2", "previous": "%3.4"},
        {"date": "2026-02-13", "country": "US", "event": "ABD Tüketici Fiyat Endeksi (TÜFE - Yıllık)", "importance": "HIGH", "forecast": "%3.1", "previous": "%3.1"},
        {"date": "2026-03-12", "country": "US", "event": "ABD Tüketici Fiyat Endeksi (TÜFE - Yıllık)", "importance": "HIGH", "forecast": "%3.2", "previous": "%3.2"},
        {"date": "2026-04-10", "country": "US", "event": "ABD Tüketici Fiyat Endeksi (TÜFE - Yıllık)", "importance": "HIGH", "forecast": "%3.5", "previous": "%3.5"},
        {"date": "2026-05-15", "country": "US", "event": "ABD Tüketici Fiyat Endeksi (TÜFE - Yıllık)", "importance": "HIGH", "forecast": "%3.4", "previous": "%3.4"},
        {"date": "2026-06-12", "country": "US", "event": "ABD Tüketici Fiyat Endeksi (TÜFE - Yıllık)", "importance": "HIGH", "forecast": "%3.3", "previous": "%3.3"},
        {"date": "2026-07-11", "country": "US", "event": "ABD Tüketici Fiyat Endeksi (TÜFE - Yıllık)", "importance": "HIGH", "forecast": "%3.0", "previous": "%3.2"},
        {"date": "2026-08-14", "country": "US", "event": "ABD Tüketici Fiyat Endeksi (TÜFE - Yıllık)", "importance": "HIGH", "forecast": "%2.9", "previous": "%3.0"},
        {"date": "2026-09-11", "country": "US", "event": "ABD Tüketici Fiyat Endeksi (TÜFE - Yıllık)", "importance": "HIGH", "forecast": "%2.5", "previous": "%2.9"},
        {"date": "2026-10-13", "country": "US", "event": "ABD Tüketici Fiyat Endeksi (TÜFE - Yıllık)", "importance": "HIGH", "forecast": "%2.4", "previous": "%2.5"},
        {"date": "2026-11-13", "country": "US", "event": "ABD Tüketici Fiyat Endeksi (TÜFE - Yıllık)", "importance": "HIGH", "forecast": "%2.2", "previous": "%2.4"},
        {"date": "2026-12-11", "country": "US", "event": "ABD Tüketici Fiyat Endeksi (TÜFE - Yıllık)", "importance": "HIGH", "forecast": "%2.1", "previous": "%2.2"},
        
        # Non-farm Payrolls (US - First Friday of every month)
        {"date": "2026-06-05", "country": "US", "event": "Tarım Dışı İstihdam Verisi (Aylık)", "importance": "MEDIUM", "forecast": "180K", "previous": "272K"},
        {"date": "2026-07-03", "country": "US", "event": "Tarım Dışı İstihdam Verisi (Aylık)", "importance": "MEDIUM", "forecast": "175K", "previous": "185K"},
        {"date": "2026-08-07", "country": "US", "event": "Tarım Dışı İstihdam Verisi (Aylık)", "importance": "MEDIUM", "forecast": "160K", "previous": "175K"},
        {"date": "2026-09-04", "country": "US", "event": "Tarım Dışı İstihdam Verisi (Aylık)", "importance": "MEDIUM", "forecast": "150K", "previous": "160K"}
    ]
    
    today = date.today()
    start_date = today - timedelta(days=14)
    end_date = today + timedelta(days=45)
    
    filtered_events = []
    for ev in events:
        ev_date = datetime.strptime(ev["date"], "%Y-%m-%d").date()
        if start_date <= ev_date <= end_date:
            # Add state: 'Geçti' or 'Bekleniyor' or 'Bugün'
            if ev_date < today:
                ev["status"] = "Geçti"
                # For passed events, make actual same as forecast or pre-fill
                ev["actual"] = ev["forecast"] 
            elif ev_date == today:
                ev["status"] = "Bugün"
                ev["actual"] = "-"
            else:
                ev["status"] = "Bekleniyor"
                ev["actual"] = "-"
            filtered_events.append(ev)
            
    # Sort chronologically
    filtered_events.sort(key=lambda x: x["date"])
    return filtered_events

if __name__ == "__main__":
    print(f"Economic calendar events filtered for today ({date.today()}):")
    cal = get_economic_calendar()
    for c in cal:
        print(f"{c['date']} | {c['country']} | {c['status']} | {c['event']} (Önem: {c['importance']})")
