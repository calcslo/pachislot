// Configuration
const MACHINE_GROUPS = {
    hanahana: ['LBﾆｭｰｷﾝｸﾞﾊﾅﾊﾅV'],
    juggler: ['ｺﾞｰｺﾞｰｼﾞｬｸﾞﾗｰ3', 'ｳﾙﾄﾗﾐﾗｸﾙｼﾞｬｸﾞﾗｰ', 'ｼﾞｬｸﾞﾗｰｶﾞｰﾙｽﾞSS', 'ﾐｽﾀｰｼﾞｬｸﾞﾗｰ']
};

let rawData = [];
let layoutData = [];
let currentTab = 'hanahana';
let currentPeriod = '3m';
let currentEventFilter = 'none';
let diffChart = null;
let activeDate = null; // null means all dates in period

// State Init
async function init() {
    setupTheme();
    setupEventListeners();

    try {
        const [dataRes, layoutRes] = await Promise.all([
            fetch('data.json'),
            fetch('layout.json')
        ]);
        rawData = await dataRes.json();
        layoutData = await layoutRes.json();
        
        updateDashboard();
    } catch (err) {
        console.error("Failed to load data:", err);
        document.getElementById('summary-tbody').innerHTML = `<tr><td colspan="6">データ読み込みエラー: ${err.message}</td></tr>`;
    }
}

// Theme Handling
function setupTheme() {
    const btn = document.getElementById('theme-btn');
    const isDark = document.body.classList.contains('dark-theme');
    updateThemeIcon(isDark);

    btn.addEventListener('click', () => {
        const isDarkNow = document.body.classList.toggle('dark-theme');
        updateThemeIcon(isDarkNow);
        if (diffChart) {
            diffChart.options.scales.x.grid.color = isDarkNow ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';
            diffChart.options.scales.y.grid.color = isDarkNow ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';
            diffChart.options.plugins.legend.labels.color = isDarkNow ? '#f8fafc' : '#1a1a2e';
            Chart.defaults.color = isDarkNow ? '#94a3b8' : '#666';
            diffChart.update();
        }
    });
}

function updateThemeIcon(isDark) {
    const svg = document.querySelector('#theme-btn svg');
    if (isDark) {
        svg.innerHTML = `<path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"></path>`;
    } else {
        svg.innerHTML = `<path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"></path>`;
    }
}

// Event Listeners
function setupEventListeners() {
    document.querySelectorAll('#machine-tabs .tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('#machine-tabs .tab-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentTab = e.target.dataset.target;
            activeDate = null; // reset specific date filter
            updateDashboard();
        });
    });

    document.querySelectorAll('#period-tabs .tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('#period-tabs .tab-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentPeriod = e.target.dataset.target;
            activeDate = null;
            updateDashboard();
        });
    });

    document.getElementById('event-filter').addEventListener('change', (e) => {
        currentEventFilter = e.target.value;
        activeDate = null;
        updateDashboard();
    });

    // Modal close
    document.querySelector('.close-btn').addEventListener('click', () => {
        document.getElementById('machine-modal').classList.remove('show');
    });
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('machine-modal');
        if (e.target === modal) modal.classList.remove('show');
    });
}

// Data Processing
function getFilteredData() {
    if (rawData.length === 0) return [];

    // 1. Filter by Machine Type
    let targetMachines = [];
    if (currentTab === 'hanahana') {
        targetMachines = MACHINE_GROUPS.hanahana;
    } else if (currentTab === 'juggler') {
        targetMachines = MACHINE_GROUPS.juggler;
    } else {
        targetMachines = [...MACHINE_GROUPS.hanahana, ...MACHINE_GROUPS.juggler];
    }

    let filtered = rawData.filter(row => targetMachines.includes(row['機種名']));

    // 2. Filter by Period
    if (filtered.length > 0) {
        // Find latest date in dataset
        const dates = filtered.map(r => r['日付']).sort();
        const latestDateStr = dates[dates.length - 1];
        const latestDate = new Date(latestDateStr);

        let cutoffDate = new Date(latestDate);
        if (currentPeriod === '1m') {
            cutoffDate.setMonth(cutoffDate.getMonth() - 1);
        } else if (currentPeriod === '3m') {
            cutoffDate.setMonth(cutoffDate.getMonth() - 3);
        } else {
            cutoffDate = new Date(0); // All time
        }
        
        const cutoffStr = cutoffDate.toISOString().split('T')[0];
        filtered = filtered.filter(row => row['日付'] >= cutoffStr);
    }

    // 3. Filter by Event Days
    if (currentEventFilter !== 'none') {
        filtered = filtered.filter(row => {
            const d = new Date(row['日付']);
            const dateNum = d.getDate();
            const dateStr = String(dateNum);
            
            if (currentEventFilter === '3') return dateStr.endsWith('3');
            if (currentEventFilter === '5') return dateStr.endsWith('5');
            if (currentEventFilter === '8') return dateStr.endsWith('8');
            if (currentEventFilter === '358') return dateStr.endsWith('3') || dateStr.endsWith('5') || dateStr.endsWith('8');
            return true;
        });
    }

    return filtered;
}

function aggregateByDate(data) {
    const summary = {};
    
    data.forEach(row => {
        const date = row['日付'];
        if (!summary[date]) {
            summary[date] = { 
                date: date, 
                totalDiff: 0, 
                totalG: 0, 
                machineCount: 0,
                digits: Array(10).fill().map(() => ({ total: 0, count: 0 }))
            };
        }
        
        const diff = Number(row['最終差枚']) || 0;
        const g = Number(row['累計ゲーム']) || 0;
        const machineNum = String(row['台番号']);
        const lastDigit = parseInt(machineNum.slice(-1));

        summary[date].totalDiff += diff;
        summary[date].totalG += g;
        summary[date].machineCount += 1;
        
        if (!isNaN(lastDigit)) {
            summary[date].digits[lastDigit].total += diff;
            summary[date].digits[lastDigit].count += 1;
        }
    });

    const result = Object.values(summary).map(day => {
        day.avgDiff = day.machineCount > 0 ? Math.round(day.totalDiff / day.machineCount) : 0;
        // Payout rate: (3 * Total G + Total Diff) / (3 * Total G) * 100
        const outCoins = (3 * day.totalG) + day.totalDiff;
        const inCoins = 3 * day.totalG;
        day.payout = inCoins > 0 ? (outCoins / inCoins * 100).toFixed(2) : 0;

        // Ends-with bias (末尾寄せ) calculation
        let significantDigits = [];
        day.digits.forEach((d, idx) => {
            if (d.count > 0) {
                const avg = d.total / d.count;
                // Heuristic: Average > 500 AND Average is 500 higher than overall average
                if (avg > 500 && avg > day.avgDiff + 500) {
                    significantDigits.push(idx);
                }
            }
        });
        day.bias = significantDigits.length > 0 ? significantDigits.join(', ') : 'なし';

        return day;
    });

    // Sort descending by date
    return result.sort((a, b) => b.date.localeCompare(a.date));
}

// Rendering
function updateDashboard() {
    const filteredData = getFilteredData();
    const dailyData = aggregateByDate(filteredData);
    
    renderTable(dailyData);
    renderChart(dailyData);
    renderHeatmap(filteredData, activeDate);
    
    document.getElementById('heatmap-date-label').innerText = activeDate ? activeDate : '全期間平均';
}

function formatVal(val) {
    if (val > 0) return `<span class="val-pos">+${val.toLocaleString()}</span>`;
    if (val < 0) return `<span class="val-neg">${val.toLocaleString()}</span>`;
    return `<span class="val-zero">0</span>`;
}

function renderTable(dailyData) {
    const tbody = document.getElementById('summary-tbody');
    tbody.innerHTML = '';

    if (dailyData.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6">データがありません</td></tr>`;
        return;
    }

    dailyData.forEach(day => {
        const tr = document.createElement('tr');
        if (activeDate === day.date) tr.classList.add('selected');
        
        tr.innerHTML = `
            <td>${day.date}</td>
            <td>${formatVal(day.totalDiff)}</td>
            <td>${formatVal(day.avgDiff)}</td>
            <td>${day.totalG.toLocaleString()}</td>
            <td>${day.payout}%</td>
            <td>${day.bias}</td>
        `;
        
        tr.addEventListener('click', () => {
            if (activeDate === day.date) {
                activeDate = null; // toggle off
                document.querySelectorAll('#summary-tbody tr').forEach(r => r.classList.remove('selected'));
            } else {
                activeDate = day.date;
                document.querySelectorAll('#summary-tbody tr').forEach(r => r.classList.remove('selected'));
                tr.classList.add('selected');
            }
            // Update heatmap for specific date
            renderHeatmap(getFilteredData(), activeDate);
            document.getElementById('heatmap-date-label').innerText = activeDate ? activeDate : '全期間平均';
        });

        tbody.appendChild(tr);
    });
}

function renderChart(dailyData) {
    const ctx = document.getElementById('diff-chart').getContext('2d');
    
    // Use same order as table (newest at top)
    const chartData = [...dailyData];
    
    const labels = chartData.map(d => d.date);
    const data = chartData.map(d => d.avgDiff);
    
    const colors = data.map(val => val > 0 ? 'rgba(59, 130, 246, 0.8)' : 'rgba(239, 68, 68, 0.8)');

    if (diffChart) {
        diffChart.destroy();
    }

    // Expand chart and table wrapper dynamically based on number of dates
    const wrapper = document.querySelector('.table-chart-wrapper');
    const containerHeight = Math.max(400, chartData.length * 35);
    wrapper.style.height = `${containerHeight}px`;

    Chart.defaults.color = document.body.classList.contains('dark-theme') ? '#94a3b8' : '#666';

    diffChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '平均差枚 (Avg Diff)',
                data: data,
                backgroundColor: colors,
                borderWidth: 0,
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y', // Horizontal
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: { display: true, text: '平均差枚' },
                    grid: { color: document.body.classList.contains('dark-theme') ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' }
                },
                y: {
                    grid: { display: false }
                }
            },
            plugins: {
                legend: { display: false },
                datalabels: {
                    color: '#fff',
                    anchor: 'end',
                    align: (context) => context.dataset.data[context.dataIndex] > 0 ? 'left' : 'right',
                    formatter: (val) => val > 0 ? '+' + val : val,
                    font: { weight: 'bold', size: 10 }
                }
            }
        },
        plugins: [ChartDataLabels]
    });
}

function getHeatmapColor(val) {
    if (val <= -2000) return 'rgba(128,0,128,0.7)'; // Purple
    if (val <= -1000) return 'rgba(0,0,255,0.7)';   // Blue
    if (val < 0) return 'rgba(173,216,230,0.7)';    // Light blue
    if (val === 0) return 'transparent';
    if (val <= 999) return 'rgba(255,255,0,0.7)';   // Yellow
    if (val <= 1999) return 'rgba(255,165,0,0.7)';  // Orange
    return 'rgba(255,0,0,0.7)';                     // Red
}

function renderHeatmap(filteredData, specificDate = null) {
    const wrapper = document.getElementById('heatmap-wrapper');
    wrapper.innerHTML = '';

    if (layoutData.length === 0) {
        wrapper.innerHTML = '<div>レイアウトデータがありません</div>';
        return;
    }

    // Calculate avg diff for each machine
    const machineStats = {};
    
    let activeData = filteredData;
    if (specificDate) {
        activeData = filteredData.filter(d => d['日付'] === specificDate);
    }

    activeData.forEach(row => {
        const num = String(row['台番号']);
        if (!machineStats[num]) {
            machineStats[num] = { total: 0, count: 0, model: row['機種名'] };
        }
        machineStats[num].total += Number(row['最終差枚']) || 0;
        machineStats[num].count += 1;
    });

    layoutData.forEach(row => {
        const rowDiv = document.createElement('div');
        rowDiv.className = 'heatmap-row';
        
        row.forEach(cell => {
            const cellDiv = document.createElement('div');
            cellDiv.className = 'heatmap-cell';
            
            if (cell === '') {
                cellDiv.classList.add('empty');
            } else {
                const machineNum = String(cell);
                cellDiv.innerText = machineNum;
                
                if (machineStats[machineNum]) {
                    const avg = Math.round(machineStats[machineNum].total / machineStats[machineNum].count);
                    cellDiv.style.backgroundColor = getHeatmapColor(avg);
                    
                    cellDiv.addEventListener('click', () => {
                        showModal(machineNum, machineStats[machineNum].model, avg, machineStats[machineNum].count);
                    });
                } else {
                    cellDiv.style.backgroundColor = 'transparent';
                    cellDiv.style.border = '1px solid rgba(128,128,128,0.2)';
                    cellDiv.style.color = 'var(--text-muted)';
                }
            }
            rowDiv.appendChild(cellDiv);
        });
        wrapper.appendChild(rowDiv);
    });
}

function showModal(machineNum, model, avg, count) {
    document.getElementById('modal-title').innerText = `台番号: ${machineNum}`;
    document.getElementById('modal-body').innerHTML = `
        <p><strong>機種:</strong> ${model}</p>
        <p><strong>対象日数:</strong> ${count}日</p>
        <p><strong>平均差枚:</strong> ${formatVal(avg)}</p>
    `;
    document.getElementById('machine-modal').classList.add('show');
}

// Bootstrap
document.addEventListener('DOMContentLoaded', init);
