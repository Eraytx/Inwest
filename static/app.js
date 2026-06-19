// App Globals
let historyChart = null;

// DOM Elements
const elUsdRate = document.getElementById('usd-rate-value');
const elTotalValue = document.getElementById('stat-total-value');
const elTotalCost = document.getElementById('stat-total-cost');
const elNetProfit = document.getElementById('stat-net-profit');
const elProfitPercent = document.getElementById('stat-profit-percent');
const elDailyChange = document.getElementById('stat-daily-change');
const elProfitIconBox = document.getElementById('profit-icon-box');

const elHoldingsList = document.getElementById('holdings-list');
const elNewsList = document.getElementById('news-list');
const elAiReportBody = document.getElementById('ai-report-body');
const elReportDateBadge = document.getElementById('report-date-badge');

const formTransaction = document.getElementById('transaction-form');
const btnGenerateReport = document.getElementById('btn-generate-report');

const toast = document.getElementById('toast');
const toastMessage = document.getElementById('toast-message');

// Toast Notification Helper
function showToast(message, type = 'success') {
    toastMessage.textContent = message;
    
    // Icon switching based on type
    const icon = toast.querySelector('.toast-icon');
    if (type === 'error') {
        icon.className = 'fa-solid fa-circle-exclamation toast-icon';
        toast.style.borderColor = 'var(--accent-down)';
    } else {
        icon.className = 'fa-solid fa-circle-check toast-icon';
        toast.style.borderColor = 'var(--primary)';
    }
    
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, 4000);
}

// Fetch dashboard data and populate DOM
async function fetchDashboard() {
    try {
        const response = await fetch('/api/dashboard');
        if (!response.ok) throw new Error('API request failed');
        const data = await response.json();
        
        updateMetrics(data.metrics);
        renderChart(data.history);
        renderHoldings(data.metrics.assets);
        renderReports(data.reports);
        renderNews(data.news);
        
    } catch (error) {
        console.error('Error fetching dashboard:', error);
        showToast('Veriler yüklenirken hata oluştu!', 'error');
    }
}

// Update core dashboard metric boxes
function updateMetrics(metrics) {
    // 1. USD rate
    elUsdRate.textContent = metrics.usd_try_rate ? metrics.usd_try_rate.toFixed(4) : '0.00';
    
    // 2. Total values
    elTotalValue.textContent = formatCurrency(metrics.total_value_try, 'TRY');
    elTotalCost.textContent = formatCurrency(metrics.total_cost_try, 'TRY');
    
    // 3. Profit / Loss
    const profitVal = metrics.total_profit_try;
    const profitPct = metrics.total_profit_percent;
    
    elNetProfit.textContent = formatCurrency(profitVal, 'TRY');
    elProfitPercent.textContent = `${profitVal >= 0 ? '+' : ''}${profitPct.toFixed(2)}%`;
    
    // Apply positive/negative classes to Profit/Loss
    if (profitVal >= 0) {
        elNetProfit.className = 'change-up';
        elProfitPercent.className = 'stat-trend change-up';
        elProfitIconBox.className = 'stat-icon-wrapper profit-icon change-up';
        elProfitIconBox.innerHTML = '<i class="fa-solid fa-arrow-trend-up"></i>';
    } else {
        elNetProfit.className = 'change-down';
        elProfitPercent.className = 'stat-trend change-down';
        elProfitIconBox.className = 'stat-icon-wrapper profit-icon change-down';
        elProfitIconBox.innerHTML = '<i class="fa-solid fa-arrow-trend-down"></i>';
    }
    
    // 4. Daily performance
    const dailyPct = metrics.daily_change_percent;
    elDailyChange.innerHTML = `
        <i class="fa-solid ${dailyPct >= 0 ? 'fa-caret-up' : 'fa-caret-down'}"></i> 
        ${dailyPct >= 0 ? '+' : ''}${dailyPct.toFixed(2)}% (Bugün)
    `;
    elDailyChange.className = `stat-trend ${dailyPct >= 0 ? 'change-up' : 'change-down'}`;
}

// Render historical line chart
function renderChart(history) {
    if (!history || history.length === 0) return;
    
    const labels = history.map(item => item.date);
    const dataValues = history.map(item => item.total_value);
    
    const ctx = document.getElementById('historyChart').getContext('2d');
    
    // Destroy previous chart instance if exists
    if (historyChart) {
        historyChart.destroy();
    }
    
    // Gradient fill setup
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(138, 43, 226, 0.45)');
    gradient.addColorStop(1, 'rgba(138, 43, 226, 0.0)');
    
    historyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Portföy Değeri (TL)',
                data: dataValues,
                borderColor: '#a855f7',
                borderWidth: 3,
                pointBackgroundColor: '#22d3ee',
                pointBorderColor: '#0f172a',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6,
                fill: true,
                backgroundColor: gradient,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    titleColor: '#f8fafc',
                    bodyColor: '#22d3ee',
                    borderColor: 'rgba(168, 85, 247, 0.3)',
                    borderWidth: 1,
                    displayColors: false,
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            return `Değer: ${context.parsed.y.toLocaleString('tr-TR', {minimumFractionDigits: 2})} TL`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8', font: { size: 10 } }
                },
                y: {
                    grid: { color: 'rgba(148, 163, 184, 0.07)' },
                    ticks: {
                        color: '#94a3b8',
                        font: { size: 10 },
                        callback: function(value) {
                            return value.toLocaleString('tr-TR') + ' TL';
                        }
                    }
                }
            }
        }
    });
}

// Populate current holdings list table
function renderHoldings(assets) {
    elHoldingsList.innerHTML = '';
    
    if (!assets || assets.length === 0) {
        elHoldingsList.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; color: var(--text-muted); padding: 2rem;">
                    Portföyünüzde henüz hiç varlık bulunmamaktadır. İşlem kaydı girerek başlayın!
                </td>
            </tr>
        `;
        return;
    }
    
    assets.forEach(asset => {
        const profitClass = asset.profit_try >= 0 ? 'change-up' : 'change-down';
        
        let badgeClass = 'badge-crypto';
        if (asset.asset_class === 'BIST') {
            badgeClass = 'badge-bist';
        } else if (asset.asset_class === 'US_Stocks' || asset.asset_class === 'US_STOCKS' || asset.asset_class === 'US') {
            badgeClass = 'badge-us_stocks';
        }
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${asset.symbol}</strong></td>
            <td>
                <span class="badge-class ${badgeClass}">
                    ${asset.asset_class}
                </span>
            </td>
            <td>${asset.amount.toLocaleString('tr-TR', { maximumFractionDigits: 6 })}</td>
            <td>${asset.avg_price.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ${asset.currency}</td>
            <td>${asset.current_price.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ${asset.currency}</td>
            <td>${asset.cost_try.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} TL</td>
            <td><strong>${asset.value_try.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} TL</strong></td>
            <td class="${profitClass}">
                ${asset.profit_try >= 0 ? '+' : ''}${asset.profit_try.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} TL 
                (${asset.profit_try >= 0 ? '+' : ''}${asset.profit_percent.toFixed(2)}%)
            </td>
        `;
        elHoldingsList.appendChild(row);
    });
}

// Render generated AI reports (Markdown parsed dynamically)
function renderReports(reports) {
    if (!reports || reports.length === 0) {
        elReportDateBadge.textContent = 'Henüz hiç rapor oluşturulmadı';
        elAiReportBody.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: var(--text-muted);">
                <i class="fa-solid fa-wand-magic-sparkles" style="font-size: 2rem; margin-bottom: 1rem; color: var(--primary);"></i>
                <p>Henüz analiz raporu oluşturulmamış.</p>
                <p style="font-size: 0.85rem; margin-top: 5px;">Yukarıdaki "AI Raporu Üret" butonuna basarak ilk raporunuzu oluşturabilirsiniz.</p>
            </div>
        `;
        return;
    }
    
    const latest = reports[0];
    
    // Parse timestamp
    const date = new Date(latest.generated_at);
    const dateFormatted = date.toLocaleString('tr-TR', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
    
    elReportDateBadge.textContent = `Son Güncelleme: ${dateFormatted}`;
    
    // Use marked library to parse AI Markdown text to HTML safely
    elAiReportBody.innerHTML = marked.parse(latest.report_text);
}

// Populate Google News listings
function renderNews(news) {
    elNewsList.innerHTML = '';
    
    if (!news || news.length === 0) {
        elNewsList.innerHTML = `
            <div style="color: var(--text-muted); padding: 1rem; text-align: center; font-size: 0.85rem;">
                Takip listesindeki varlıklar için son haber bulunamadı.
            </div>
        `;
        return;
    }
    
    news.forEach(item => {
        const date = new Date(item.published);
        const dateFormatted = isNaN(date.getTime()) ? item.published : date.toLocaleDateString('tr-TR', {
            day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'
        });
        
        const newsEl = document.createElement('div');
        newsEl.className = 'news-item';
        newsEl.innerHTML = `
            <div class="news-meta">
                <span class="news-source">${item.source}</span>
                <span class="news-time">${dateFormatted}</span>
            </div>
            <a href="${item.link}" target="_blank" class="news-title">
                ${item.title}
            </a>
        `;
        elNewsList.appendChild(newsEl);
    });
}

// Form Submission logic
formTransaction.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const txData = {
        symbol: document.getElementById('tx-symbol').value.toUpperCase().trim(),
        asset_class: document.getElementById('tx-asset-class').value,
        type: document.getElementById('tx-type').value,
        amount: parseFloat(document.getElementById('tx-amount').value),
        price: parseFloat(document.getElementById('tx-price').value)
    };
    
    try {
        const response = await fetch('/api/transactions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(txData)
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'İşlem kaydedilemedi');
        }
        
        showToast('İşleminiz başarıyla kaydedildi!');
        formTransaction.reset();
        
        // Refresh dashboard numbers & transactions list
        fetchDashboard();
        fetchTransactions();
        
    } catch (error) {
        showToast(error.message, 'error');
    }
});

// AI Report manual trigger click handler
btnGenerateReport.addEventListener('click', async () => {
    // Show spinner & loading state
    btnGenerateReport.disabled = true;
    const originalContent = btnGenerateReport.innerHTML;
    btnGenerateReport.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>Analiz ediliyor...</span>';
    
    elAiReportBody.innerHTML = `
        <div class="report-loading">
            <i class="fa-solid fa-brain-circuit fa-spin" style="font-size: 2.2rem; color: var(--primary); animation: pulse 1s infinite;"></i>
            <span>Yapay Zeka Portföyünüzü Analiz Ediyor, Lütfen Bekleyin...</span>
        </div>
    `;
    
    try {
        const response = await fetch('/api/reports/generate', { method: 'POST' });
        if (!response.ok) throw new Error('Rapor oluşturulamadı');
        const data = await response.json();
        
        showToast('Yapay Zeka Raporu başarıyla üretildi!');
        
        // Refresh dashboard to display new report & updated prices
        await fetchDashboard();
        
    } catch (error) {
        showToast(error.message, 'error');
        elAiReportBody.innerHTML = `
            <div style="color: var(--accent-down); text-align: center; padding: 2rem;">
                <i class="fa-solid fa-triangle-exclamation" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                <p>Rapor üretilirken bir hata oluştu.</p>
                <button onclick="fetchDashboard()" class="btn btn-secondary" style="margin-top: 10px;">Yeniden Dene</button>
            </div>
        `;
    } finally {
        btnGenerateReport.disabled = false;
        btnGenerateReport.innerHTML = originalContent;
    }
});

// Autocomplete Symbol Suggestions
const elSymbolInput = document.getElementById('tx-symbol');
const elSuggestionsBox = document.getElementById('autocomplete-suggestions');
const elAssetClassSelect = document.getElementById('tx-asset-class');
let autocompleteTimeout = null;

if (elSymbolInput) {
    elSymbolInput.addEventListener('input', () => {
        clearTimeout(autocompleteTimeout);
        const query = elSymbolInput.value.trim();
        const assetClass = elAssetClassSelect.value;
        
        if (query.length < 1) {
            elSuggestionsBox.style.display = 'none';
            return;
        }
        
        autocompleteTimeout = setTimeout(async () => {
            try {
                const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&type=${assetClass}`);
                if (!response.ok) return;
                const suggestions = await response.json();
                
                if (suggestions.length === 0) {
                    elSuggestionsBox.style.display = 'none';
                    return;
                }
                
                elSuggestionsBox.innerHTML = '';
                suggestions.forEach(item => {
                    const itemEl = document.createElement('div');
                    itemEl.className = 'suggestion-item';
                    itemEl.innerHTML = `
                        <span class="suggestion-symbol">${item.symbol}</span>
                        <span class="suggestion-name">${item.name}</span>
                    `;
                    itemEl.addEventListener('click', () => {
                        elSymbolInput.value = item.symbol;
                        elSuggestionsBox.style.display = 'none';
                    });
                    elSuggestionsBox.appendChild(itemEl);
                });
                elSuggestionsBox.style.display = 'block';
            } catch (err) {
                console.error('Autocomplete error:', err);
            }
        }, 250);
    });

    // Close suggestions when clicking outside
    document.addEventListener('click', (e) => {
        if (e.target !== elSymbolInput && e.target !== elSuggestionsBox) {
            elSuggestionsBox.style.display = 'none';
        }
    });
}

// Economic Calendar loading
const elCalendarList = document.getElementById('calendar-list');

async function fetchCalendar() {
    if (!elCalendarList) return;
    try {
        const response = await fetch('/api/calendar');
        if (!response.ok) throw new Error('Calendar fetch failed');
        const data = await response.json();
        renderCalendar(data);
    } catch (err) {
        console.error('Error fetching calendar:', err);
        elCalendarList.innerHTML = `<div style="color: var(--text-muted); font-size: 0.85rem; padding: 1rem;">Takvim yüklenemedi.</div>`;
    }
}

function renderCalendar(events) {
    elCalendarList.innerHTML = '';
    if (!events || events.length === 0) {
        elCalendarList.innerHTML = `<div style="color: var(--text-muted); font-size: 0.85rem; padding: 1rem;">Takvimde yakın zamanda açıklanacak veri yok.</div>`;
        return;
    }
    
    events.forEach(item => {
        const date = new Date(item.date);
        const dateFormatted = date.toLocaleDateString('tr-TR', { day: '2-digit', month: 'short', year: 'numeric' });
        
        let badgeClass = item.country === 'TR' ? 'badge-tr' : 'badge-us';
        let statusClass = 'status-pending';
        if (item.status === 'Geçti') statusClass = 'status-passed';
        else if (item.status === 'Bugün') statusClass = 'status-today';
        
        const itemEl = document.createElement('div');
        itemEl.className = 'calendar-item';
        itemEl.innerHTML = `
            <div class="calendar-meta">
                <span class="calendar-badge ${badgeClass}">${item.country}</span>
                <span class="calendar-status ${statusClass}">${item.status === 'Bugün' ? '🔴 Bugün' : item.status}</span>
            </div>
            <div class="calendar-event">${item.event}</div>
            <div class="calendar-values">
                <span>Beklenen: <strong>${item.forecast}</strong></span>
                <span>Önceki: <strong>${item.previous}</strong></span>
                ${item.status === 'Geçti' ? `<span>Açıklanan: <strong>${item.actual}</strong></span>` : ''}
            </div>
            <div style="font-size: 0.7rem; color: var(--text-muted); text-align: right; width:100%">${dateFormatted}</div>
        `;
        elCalendarList.appendChild(itemEl);
    });
}

// Transaction History loading
const elTransactionsList = document.getElementById('transactions-list');

async function fetchTransactions() {
    if (!elTransactionsList) return;
    try {
        const response = await fetch('/api/transactions');
        if (!response.ok) throw new Error('Transactions fetch failed');
        const data = await response.json();
        renderTransactions(data);
    } catch (err) {
        console.error('Error fetching transactions:', err);
        elTransactionsList.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--text-muted);">İşlemler yüklenemedi.</td></tr>`;
    }
}

function renderTransactions(txs) {
    elTransactionsList.innerHTML = '';
    if (!txs || txs.length === 0) {
        elTransactionsList.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--text-muted);padding:1.5rem;">İşlem geçmişiniz bulunmamaktadır.</td></tr>`;
        return;
    }
    
    txs.forEach(tx => {
        const date = new Date(tx.timestamp);
        const dateFormatted = date.toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
        const isBuy = tx.type.toUpperCase() === 'BUY';
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${dateFormatted}</td>
            <td><strong>${tx.symbol}</strong></td>
            <td><span class="badge-class ${isBuy ? 'badge-bist' : 'badge-crypto'}">${isBuy ? 'AL' : 'SAT'}</span></td>
            <td>${tx.amount.toLocaleString('tr-TR', { maximumFractionDigits: 6 })}</td>
            <td>${tx.price.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} TL</td>
            <td>
                <button class="btn-delete" onclick="deleteTransaction(${tx.id})" title="Sil">
                    <i class="fa-solid fa-trash-can"></i>
                </button>
            </td>
        `;
        elTransactionsList.appendChild(row);
    });
}

async function deleteTransaction(id) {
    if (!confirm('Bu işlemi silmek istediğinize emin misiniz? Pozisyonlarınız ve kâr oranlarınız baştan hesaplanacaktır.')) return;
    
    try {
        const response = await fetch(`/api/transactions/${id}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('Silme işlemi başarısız');
        
        showToast('İşlem silindi ve portföy yeniden hesaplandı!');
        
        // Refresh everything
        fetchDashboard();
        fetchTransactions();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// Expose deleteTransaction to global scope for button onclick attributes
window.deleteTransaction = deleteTransaction;

// Helper: format currencies elegantly
function formatCurrency(amount, currency = 'TRY') {
    if (currency === 'USD') {
        return amount.toLocaleString('tr-TR', { style: 'currency', currency: 'USD' });
    }
    return amount.toLocaleString('tr-TR', { style: 'currency', currency: 'TRY' });
}

// Settings API Key managers
const elApiKeyInput = document.getElementById('settings-api-key');
const btnSaveApiKey = document.getElementById('btn-save-api-key');

async function fetchSettings() {
    if (!elApiKeyInput) return;
    try {
        const response = await fetch('/api/settings');
        if (!response.ok) return;
        const data = await response.json();
        if (data.has_key) {
            elApiKeyInput.value = '';
            elApiKeyInput.placeholder = `Tanımlı: ${data.gemini_api_key}`;
        } else {
            elApiKeyInput.value = '';
            elApiKeyInput.placeholder = 'Anahtar yok (Simülasyon Aktif)';
        }
    } catch (err) {
        console.error('Error fetching settings:', err);
    }
}

if (btnSaveApiKey) {
    btnSaveApiKey.addEventListener('click', async () => {
        const keyVal = elApiKeyInput.value.trim();
        if (!keyVal) {
            showToast('Lütfen geçerli bir API anahtarı girin!', 'error');
            return;
        }
        
        btnSaveApiKey.disabled = true;
        btnSaveApiKey.textContent = 'Kaydediliyor...';
        
        try {
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ gemini_api_key: keyVal })
            });
            
            if (!response.ok) throw new Error('API Key kaydedilemedi');
            
            showToast('Gemini API Anahtarı başarıyla kaydedildi!');
            await fetchSettings();
        } catch (err) {
            showToast(err.message, 'error');
        } finally {
            btnSaveApiKey.disabled = false;
            btnSaveApiKey.textContent = 'Kaydet';
        }
    });
}

// Initial Bootstrapping
document.addEventListener('DOMContentLoaded', () => {
    fetchDashboard();
    fetchCalendar();
    fetchTransactions();
    fetchSettings();
});
