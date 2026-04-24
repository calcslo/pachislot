// Configuration
const MACHINE_GROUPS = {
    hanahana: ['LBﾆｭｰｷﾝｸﾞﾊﾅﾊﾅV'],
    juggler: ['ｺﾞｰｺﾞｰｼﾞｬｸﾞﾗｰ3', 'ｳﾙﾄﾗﾐﾗｸﾙｼﾞｬｸﾞﾗｰ', 'ｼﾞｬｸﾞﾗｰｶﾞｰﾙｽﾞSS', 'ﾐｽﾀｰｼﾞｬｸﾞﾗｰ']
};

const MACHINE_PROBS = {
    'LBﾆｭｰｷﾝｸﾞﾊﾅﾊﾅV': {
        1: { big: 299, reg: 496 },
        2: { big: 291, reg: 471 },
        3: { big: 281, reg: 442 },
        4: { big: 268, reg: 409 },
        5: { big: 253, reg: 372 }
    },
    'ｺﾞｰｺﾞｰｼﾞｬｸﾞﾗｰ3': {
        1: { big: 259.0, reg: 354.2 },
        2: { big: 258.0, reg: 332.7 },
        3: { big: 257.0, reg: 306.2 },
        4: { big: 254.0, reg: 268.6 },
        5: { big: 247.3, reg: 247.3 },
        6: { big: 234.9, reg: 234.9 }
    },
    'ｳﾙﾄﾗﾐﾗｸﾙｼﾞｬｸﾞﾗｰ': {
        1: { big: 267.5, reg: 425.6 },
        2: { big: 261.1, reg: 402.1 },
        3: { big: 256.0, reg: 350.5 },
        4: { big: 242.7, reg: 322.8 },
        5: { big: 233.2, reg: 297.9 },
        6: { big: 216.3, reg: 277.7 }
    },
    'ｼﾞｬｸﾞﾗｰｶﾞｰﾙｽﾞSS': {
        1: { big: 273.1, reg: 381.0 },
        2: { big: 270.8, reg: 350.5 },
        3: { big: 260.1, reg: 316.6 },
        4: { big: 250.1, reg: 281.3 },
        5: { big: 243.6, reg: 270.8 },
        6: { big: 226.0, reg: 252.1 }
    },
    'ﾐｽﾀｰｼﾞｬｸﾞﾗｰ': {
        1: { big: 268.6, reg: 374.5 },
        2: { big: 267.5, reg: 354.2 },
        3: { big: 260.1, reg: 331.0 },
        4: { big: 249.2, reg: 291.3 },
        5: { big: 240.9, reg: 257.0 },
        6: { big: 237.4, reg: 237.4 }
    }
};

let rawData = [];
let layoutData = [];
let layoutLookup = {};
let currentTab = 'all';
let currentPeriod = '3m';
let currentEventFilter = 'none';
let currentSection = 'summary-section';
let charts = {};
let activeDate = null;
let diffThresholds = { neg1: -2000, neg2: -1000, pos1: 1000, pos2: 2000 };

// Global Tooltip
const tooltip = document.createElement('div');
tooltip.className = 'custom-tooltip';
document.body.appendChild(tooltip);
document.addEventListener('mousemove', (e) => {
    if (tooltip.classList.contains('visible')) {
        tooltip.style.left = e.pageX + 15 + 'px';
        tooltip.style.top = e.pageY + 15 + 'px';
    }
});

// ==========================================
// Stats & Utils
// ==========================================

function normalizeNum(n) {
    if (n === null || n === undefined || n === '') return '';
    return String(n).padStart(4, '0');
}

function percentile(arr, p) {
    if (arr.length === 0) return 0;
    const sorted = [...arr].sort((a, b) => a - b);
    const index = (p / 100) * (sorted.length - 1);
    const lower = Math.floor(index);
    const upper = lower + 1;
    const weight = index % 1;
    if (upper >= sorted.length) return sorted[lower];
    return sorted[lower] * (1 - weight) + sorted[upper] * weight;
}

// Student's T-Test for ending digit
function isSignificant(digitVals, overallAvg, overallValues) {
    if (digitVals.length < 3) return false;
    const n = digitVals.length;
    const mean = digitVals.reduce((a,b)=>a+b, 0) / n;
    
    if (mean <= 0) return false; // Not positive
    if (mean <= overallAvg * 1.1) return false; // Simple ratio check
    
    // Variance
    const variance = digitVals.reduce((a,b)=>a+Math.pow(b-mean,2), 0) / (n - 1);
    if (variance === 0) return true;
    const std = Math.sqrt(variance);
    const t = (mean - overallAvg) / (std / Math.sqrt(n));
    
    return t > 1.645; // Approx 95% confidence (one-tailed)
}

function estimateSetting(model, games, big, reg) {
    games = Number(games) || 0;
    big = Number(big) || 0;
    reg = Number(reg) || 0;
    if (!MACHINE_PROBS[model] || games < 100) return null;
    const probs = MACHINE_PROBS[model];
    let logWeights = {};
    let maxLogW = -Infinity;
    
    for (const [setting, p] of Object.entries(probs)) {
        const pB = 1 / p.big;
        const pR = 1 / p.reg;
        const pN = 1 - pB - pR;
        if (pN <= 0) continue;
        
        const logW = big * Math.log(pB) + reg * Math.log(pR) + (games - big - reg) * Math.log(pN);
        logWeights[setting] = logW;
        if (logW > maxLogW) maxLogW = logW;
    }
    
    let sumWeights = 0;
    let expWeights = {};
    for (const [setting, logW] of Object.entries(logWeights)) {
        const w = Math.exp(logW - maxLogW);
        expWeights[setting] = w;
        sumWeights += w;
    }
    
    let bestSetting = null;
    let bestProb = -1;
    for (const [setting, w] of Object.entries(expWeights)) {
        const prob = w / sumWeights;
        if (prob > bestProb) {
            bestProb = prob;
            bestSetting = setting;
        }
    }
    
    return {
        setting: parseInt(bestSetting),
        prob: bestProb
    };
}

// ==========================================
// Initialization
// ==========================================

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
        
        buildLayoutLookup();
        updateDashboard();
    } catch (err) {
        console.error("Failed to load data:", err);
        document.getElementById('summary-tbody').innerHTML = `<tr><td colspan="7">データ読み込みエラー: ${err.message}</td></tr>`;
    }
}

function buildLayoutLookup() {
    layoutLookup = {};
    layoutData.forEach((row, rIdx) => {
        row.forEach((cell, cIdx) => {
            if (cell !== '') {
                const numStr = normalizeNum(cell);
                const numVal = parseInt(numStr, 10);
                
                let hLeft = 0, hRight = 0, vTop = 0, vBottom = 0;
                for(let i=cIdx-1; i>=0; i--) { if(layoutData[rIdx][i] && layoutData[rIdx][i] !== '') hLeft++; else break; }
                for(let i=cIdx+1; i<layoutData[rIdx].length; i++) { if(layoutData[rIdx][i] && layoutData[rIdx][i] !== '') hRight++; else break; }
                for(let i=rIdx-1; i>=0; i--) { if(layoutData[i][cIdx] && layoutData[i][cIdx] !== '') vTop++; else break; }
                for(let i=rIdx+1; i<layoutData.length; i++) { if(layoutData[i][cIdx] && layoutData[i][cIdx] !== '') vBottom++; else break; }

                let dist = null;
                let dir = 'horizontal';

                if ((numVal >= 992 && numVal <= 998) || (numVal >= 1370 && numVal <= 1385)) {
                    dist = null; // Circular island
                } else {
                    const isHorizontal = (hLeft + hRight) > 0;
                    const isVertical = (vTop + vBottom) > 0;

                    if (hLeft + hRight > vTop + vBottom) {
                        dist = Math.min(hLeft, hRight);
                        dir = 'horizontal';
                    } else if (vTop + vBottom > hLeft + hRight) {
                        dist = Math.min(vTop, vBottom);
                        dir = 'vertical';
                    } else if (isHorizontal) {
                        dist = Math.min(hLeft, hRight);
                        dir = 'horizontal';
                    } else if (isVertical) {
                        dist = Math.min(vTop, vBottom);
                        dir = 'vertical';
                    } else {
                        dist = 0; // standalone
                    }
                }
                
                layoutLookup[numStr] = {
                    row_idx: rIdx,
                    col_idx: cIdx,
                    pos: dist,
                    direction: dir
                };
            }
        });
    });
}

// ==========================================
// UI / Events
// ==========================================

function setupTheme() {
    const btn = document.getElementById('theme-btn');
    const isDark = document.body.classList.contains('dark-theme');
    updateThemeIcon(isDark);

    btn.addEventListener('click', () => {
        const isDarkNow = document.body.classList.toggle('dark-theme');
        updateThemeIcon(isDarkNow);
        Chart.defaults.color = isDarkNow ? '#94a3b8' : '#666';
        updateDashboard();
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

function setupEventListeners() {
    // Tabs
    document.querySelectorAll('#machine-tabs .tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('#machine-tabs .tab-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentTab = e.target.dataset.target;
            activeDate = null;
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

    // Main Sections Nav
    document.querySelectorAll('.main-nav .nav-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.main-nav .nav-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            const targetId = e.target.dataset.section;
            document.querySelectorAll('.content-grid > section').forEach(sec => {
                sec.style.display = 'none';
                sec.classList.remove('active-section');
            });
            const tSec = document.getElementById(targetId);
            tSec.style.display = 'block';
            tSec.classList.add('active-section');
            updateDashboard();
        });
    });

    // Modal
    document.querySelector('.close-btn').addEventListener('click', () => {
        document.getElementById('machine-modal').classList.remove('show');
    });
    window.addEventListener('click', (e) => {
        if (e.target === document.getElementById('machine-modal')) {
            document.getElementById('machine-modal').classList.remove('show');
        }
    });

    // Drag-to-scroll for heatmaps and tables
    const dragScrollElements = ['.heatmap-wrapper', '.table-container'];
    dragScrollElements.forEach(selector => {
        document.querySelectorAll(selector).forEach(el => setupDragScroll(el));
    });
}

function setupDragScroll(el) {
    let isDown = false;
    let startX;
    let scrollLeft;

    el.addEventListener('mousedown', (e) => {
        isDown = true;
        el.classList.add('active-dragging');
        startX = e.pageX - el.offsetLeft;
        scrollLeft = el.scrollLeft;
    });
    el.addEventListener('mouseleave', () => {
        isDown = false;
        el.classList.remove('active-dragging');
    });
    el.addEventListener('mouseup', () => {
        isDown = false;
        el.classList.remove('active-dragging');
    });
    el.addEventListener('mousemove', (e) => {
        if (!isDown) return;
        e.preventDefault();
        const x = e.pageX - el.offsetLeft;
        const walk = (x - startX) * 2;
        el.scrollLeft = scrollLeft - walk;
    });
}

// ==========================================
// Data Filtering
// ==========================================

function getFilteredData() {
    if (rawData.length === 0) return [];

    let filtered = rawData;

    // 1. Machine
    if (currentTab !== 'all') {
        const targetMachines = currentTab === 'hanahana' ? MACHINE_GROUPS.hanahana : MACHINE_GROUPS.juggler;
        filtered = filtered.filter(row => targetMachines.includes(row['機種名']));
    }

    // 2. Period
    if (filtered.length > 0) {
        const dates = filtered.map(r => r['日付']).sort();
        const latestDate = new Date(dates[dates.length - 1]);
        
        let cutoffDate = new Date(latestDate);
        if (currentPeriod === '1m') cutoffDate.setMonth(cutoffDate.getMonth() - 1);
        else if (currentPeriod === '3m') cutoffDate.setMonth(cutoffDate.getMonth() - 3);
        else cutoffDate = new Date(0);
        
        const cutoffStr = cutoffDate.toISOString().split('T')[0];
        filtered = filtered.filter(row => row['日付'] >= cutoffStr);
    }

    // 3. Event
    if (currentEventFilter !== 'none') {
        filtered = filtered.filter(row => {
            const d = new Date(row['日付']);
            const str = String(d.getDate());
            if (currentEventFilter === '3') return str.endsWith('3');
            if (currentEventFilter === '5') return str.endsWith('5');
            if (currentEventFilter === '8') return str.endsWith('8');
            if (currentEventFilter === '358') return str.endsWith('3') || str.endsWith('5') || str.endsWith('8');
            return true;
        });
    }

    return filtered;
}

function calculateDynamicThresholds(data) {
    const diffs = data.map(d => Number(d['最終差枚']) || 0);
    const pos = diffs.filter(v => v > 0);
    const neg = diffs.filter(v => v < 0);
    
    diffThresholds.pos1 = pos.length > 0 ? percentile(pos, 33) : 1000;
    diffThresholds.pos2 = pos.length > 0 ? percentile(pos, 66) : 2000;
    diffThresholds.neg1 = neg.length > 0 ? percentile(neg, 33) : -2000; // bottom 33% (most negative)
    diffThresholds.neg2 = neg.length > 0 ? percentile(neg, 66) : -1000; // middle 33%
}

// ==========================================
// Dashboard Update
// ==========================================

function updateDashboard() {
    const filteredData = getFilteredData();
    calculateDynamicThresholds(filteredData);

    const activeSection = document.querySelector('.main-nav .nav-btn.active').dataset.section;
    
    if (activeSection === 'summary-section') {
        renderSummary(filteredData);
    } else if (activeSection === 'heatmap-section') {
        renderHeatmaps(filteredData);
    } else if (activeSection === 'analysis-section') {
        renderAnalysis(filteredData);
    }
}

// ==========================================
// SUMMARY SECTION
// ==========================================

function formatVal(val) {
    if (val > 0) return `<span class="val-pos">+${val.toLocaleString()}</span>`;
    if (val < 0) return `<span class="val-neg">${val.toLocaleString()}</span>`;
    return `<span class="val-zero">0</span>`;
}

function formatPayout(val) {
    const num = parseFloat(val);
    if (num >= 100) return `<span class="val-pos">${val}%</span>`;
    if (num > 0) return `<span class="val-neg">${val}%</span>`;
    return `<span class="val-zero">${val}%</span>`;
}

function renderSummary(data) {
    // Group by Date and Month
    const daily = {};
    const monthly = {};

    data.forEach(row => {
        const date = row['日付'];
        const month = date.substring(0, 7);
        const diff = Number(row['最終差枚']) || 0;
        const g = Number(row['累計ゲーム']) || 0;
        const numStr = normalizeNum(row['台番号']);
        const lastDigit = parseInt(numStr.slice(-1));

        if (!daily[date]) daily[date] = { date, diff: 0, g: 0, count: 0, digits: Array(10).fill().map(()=>[]) };
        daily[date].diff += diff;
        daily[date].g += g;
        daily[date].count += 1;
        if (!isNaN(lastDigit)) daily[date].digits[lastDigit].push(diff);

        if (!monthly[month]) monthly[month] = { month, diff: 0, g: 0, count: 0 };
        monthly[month].diff += diff;
        monthly[month].g += g;
        monthly[month].count += 1;
    });

    // Daily Table & Chart
    const dailyArr = Object.values(daily).sort((a,b)=>b.date.localeCompare(a.date));
    const dTbody = document.getElementById('summary-tbody');
    dTbody.innerHTML = '';
    
    let chartLabels = [];
    let chartData = [];

    dailyArr.forEach(d => {
        d.avgDiff = d.count > 0 ? Math.round(d.diff / d.count) : 0;
        d.avgG = d.count > 0 ? Math.round(d.g / d.count) : 0;
        d.payout = d.g > 0 ? (((3 * d.g) + d.diff) / (3 * d.g) * 100).toFixed(2) : 0;
        
        let sigDigits = [];
        d.digits.forEach((vals, i) => {
            if (isSignificant(vals, d.avgDiff, data)) sigDigits.push(i);
        });
        d.bias = sigDigits.length > 0 ? sigDigits.join(', ') : 'なし';

        chartLabels.push(d.date);
        chartData.push(d.avgDiff);

        const tr = document.createElement('tr');
        if (activeDate === d.date) tr.classList.add('selected');
        tr.innerHTML = `
            <td>${d.date}</td>
            <td>${formatVal(d.diff)}</td>
            <td>${formatVal(d.avgDiff)}</td>
            <td>${d.avgG.toLocaleString()}</td>
            <td>${d.g.toLocaleString()}</td>
            <td>${formatPayout(d.payout)}</td>
            <td>${d.bias}</td>
        `;
        tr.addEventListener('click', () => {
            activeDate = activeDate === d.date ? null : d.date;
            updateDashboard();
        });
        dTbody.appendChild(tr);
    });

    // Monthly Table
    const monthlyArr = Object.values(monthly).sort((a,b)=>b.month.localeCompare(a.month));
    const mTbody = document.getElementById('monthly-tbody');
    mTbody.innerHTML = '';
    monthlyArr.forEach(m => {
        const avgDiff = m.count > 0 ? Math.round(m.diff / m.count) : 0;
        const avgG = m.count > 0 ? Math.round(m.g / m.count) : 0;
        const payout = m.g > 0 ? (((3 * m.g) + m.diff) / (3 * m.g) * 100).toFixed(2) : 0;
        mTbody.innerHTML += `
            <tr>
                <td>${m.month}</td>
                <td>${formatVal(m.diff)}</td>
                <td>${formatVal(avgDiff)}</td>
                <td>${avgG.toLocaleString()}</td>
                <td>${m.g.toLocaleString()}</td>
                <td>${formatPayout(payout)}</td>
            </tr>
        `;
    });

    // Chart Update
    const ctx = document.getElementById('diff-chart');
    if (charts['daily']) charts['daily'].destroy();
    
    // adjust height
    const containerHeight = Math.max(400, dailyArr.length * 35);
    ctx.parentElement.style.height = `${containerHeight}px`;

    charts['daily'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: chartLabels,
            datasets: [{
                data: chartData,
                backgroundColor: chartData.map(v => v > 0 ? 'rgba(59, 130, 246, 0.8)' : 'rgba(239, 68, 68, 0.8)'),
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { color: 'rgba(128,128,128,0.2)' } },
                y: { grid: { display: false } }
            }
        }
    });
}

// ==========================================
// HEATMAPS SECTION
// ==========================================

function getHeatmapColor(val) {
    if (val === 0) return 'transparent';
    if (val <= diffThresholds.neg1) return 'rgba(60, 20, 180, 0.8)'; // Bluish Purple
    if (val <= diffThresholds.neg2) return 'rgba(30, 100, 230, 0.8)'; // Blue
    if (val < 0) return 'rgba(0, 190, 255, 0.8)'; // Vivid Light Blue
    if (val <= diffThresholds.pos1) return 'rgba(255, 220, 0, 0.8)'; // Vivid Yellow
    if (val <= diffThresholds.pos2) return 'rgba(255, 130, 0, 0.8)'; // Orange
    return 'rgba(230, 40, 40, 0.8)'; // Red
}

function updateHeatmapLegends() {
    const lHtml = `
        <div class="legend-item"><span class="color-box" style="background-color: rgba(60, 20, 180, 0.8);"></span>${Math.round(diffThresholds.neg1)}以下 (下位33%)</div>
        <div class="legend-item"><span class="color-box" style="background-color: rgba(30, 100, 230, 0.8);"></span>${Math.round(diffThresholds.neg1)} ~ ${Math.round(diffThresholds.neg2)} (中位)</div>
        <div class="legend-item"><span class="color-box" style="background-color: rgba(0, 190, 255, 0.8);"></span>${Math.round(diffThresholds.neg2)} ~ -1 (上位33%)</div>
        <div class="legend-item"><span class="color-box" style="background-color: transparent; border: 1px solid #ccc;"></span>0 (無色)</div>
        <div class="legend-item"><span class="color-box" style="background-color: rgba(255, 220, 0, 0.8);"></span>1 ~ ${Math.round(diffThresholds.pos1)} (下位33%)</div>
        <div class="legend-item"><span class="color-box" style="background-color: rgba(255, 130, 0, 0.8);"></span>${Math.round(diffThresholds.pos1)} ~ ${Math.round(diffThresholds.pos2)} (中位)</div>
        <div class="legend-item"><span class="color-box" style="background-color: rgba(230, 40, 40, 0.8);"></span>${Math.round(diffThresholds.pos2)}以上 (上位33%)</div>
    `;
    document.getElementById('diff-legend').innerHTML = lHtml;
    document.getElementById('row-legend').innerHTML = lHtml;
}

function renderHeatmaps(data) {
    let activeData = activeDate ? data.filter(d => d['日付'] === activeDate) : data;
    updateHeatmapLegends();

    const machineStats = {};
    activeData.forEach(row => {
        const num = normalizeNum(row['台番号']);
        if (!machineStats[num]) machineStats[num] = { diff: 0, count: 0, big: 0, reg: 0, g: 0, model: row['機種名'] };
        machineStats[num].diff += Number(row['最終差枚']) || 0;
        machineStats[num].big += Number(row['BIG']) || 0;
        machineStats[num].reg += Number(row['REG']) || 0;
        machineStats[num].g += Number(row['累計ゲーム']) || 0;
        machineStats[num].count += 1;
    });

    // 1. Diff Heatmap
    const diffWrap = document.getElementById('diff-heatmap-wrapper');
    diffWrap.innerHTML = '';
    
    // 2. Setting Heatmap
    const setWrap = document.getElementById('setting-heatmap-wrapper');
    setWrap.innerHTML = '';

    // 3. Row Avg Heatmap
    const rowWrap = document.getElementById('row-heatmap-wrapper');
    rowWrap.innerHTML = '';

    const rowAverages = [];

    layoutData.forEach((row, rIdx) => {
        // Build elements for all 3
        const rDiff = document.createElement('div'); rDiff.className = 'heatmap-row';
        const rSet = document.createElement('div'); rSet.className = 'heatmap-row';
        const rRowAvg = document.createElement('div'); rRowAvg.className = 'heatmap-row';

        let rowTotalDiff = 0, rowMCount = 0;

        row.forEach(cell => {
            const num = normalizeNum(cell);
            const isEmp = cell === '';
            
            // Diff Cell
            const cDiff = document.createElement('div'); cDiff.className = `heatmap-cell ${isEmp?'empty':''}`;
            // Set Cell
            const cSet = document.createElement('div'); cSet.className = `heatmap-cell ${isEmp?'empty':''}`;
            // Row Cell
            const cRowAvg = document.createElement('div'); cRowAvg.className = `heatmap-cell ${isEmp?'empty':''}`;

            if (!isEmp) {
                cDiff.innerText = cell; cSet.innerText = cell; cRowAvg.innerText = cell;
                
                if (machineStats[num]) {
                    const st = machineStats[num];
                    const avgDiff = Math.round(st.diff / st.count);
                    cDiff.style.backgroundColor = getHeatmapColor(avgDiff);
                    
                    rowTotalDiff += avgDiff;
                    rowMCount += 1;

                    // Setting
                    let sText = '';
                    const isTarget = MACHINE_GROUPS.hanahana.includes(st.model) || MACHINE_GROUPS.juggler.includes(st.model);
                    if (isTarget) {
                        const est = estimateSetting(st.model, st.g, st.big, st.reg);
                        if (est) {
                            const cols = {1:'rgba(60,20,180,0.8)', 2:'rgba(30,100,230,0.8)', 3:'rgba(0,190,255,0.8)', 4:'rgba(255,220,0,0.8)', 5:'rgba(255,130,0,0.8)', 6:'rgba(230,40,40,0.8)'};
                            cSet.style.backgroundColor = cols[est.setting] || 'transparent';
                            sText = `<div class="tooltip-body"><div>推定設定: ${est.setting} (信頼度: ${(est.prob*100).toFixed(1)}%)</div></div>`;
                        }
                    }

                    // Tooltips
                    const posStr = layoutLookup[num] 
                        ? (layoutLookup[num].pos === 0 ? '角' : layoutLookup[num].pos === 1 ? '角2' : layoutLookup[num].pos === 2 ? '角3' : layoutLookup[num].pos === null ? '円形島' : 'その他')
                        : '不明';
                    
                    const tText = `
                        <div class="tooltip-title">台番号: ${num}</div>
                        <div class="tooltip-body">
                            <div>機種: ${st.model}</div>
                            <div>位置: ${posStr}</div>
                            <div>平均差枚: ${formatVal(avgDiff)}</div>
                            <div>対象日数: ${st.count}日</div>
                        </div>
                    `;
                    
                    cDiff.addEventListener('mouseenter', () => { tooltip.innerHTML = tText; tooltip.classList.add('visible'); });
                    cDiff.addEventListener('mouseleave', () => { tooltip.classList.remove('visible'); });
                    
                    cSet.addEventListener('mouseenter', () => { tooltip.innerHTML = tText + sText; tooltip.classList.add('visible'); });
                    cSet.addEventListener('mouseleave', () => { tooltip.classList.remove('visible'); });
                } else {
                    [cDiff, cSet, cRowAvg].forEach(c => {
                        c.style.backgroundColor = 'transparent';
                        c.style.border = '1px solid rgba(128,128,128,0.2)';
                    });
                }
            }
            rDiff.appendChild(cDiff);
            rSet.appendChild(cSet);
            rRowAvg.appendChild(cRowAvg);
        });

        const rAvg = rowMCount > 0 ? Math.round(rowTotalDiff / rowMCount) : 0;
        rowAverages.push(rAvg);

        // Apply row average color
        Array.from(rRowAvg.children).forEach(c => {
            if (!c.classList.contains('empty') && c.style.backgroundColor !== 'transparent') {
                c.style.backgroundColor = getHeatmapColor(rAvg);
                const rText = `
                    <div class="tooltip-title">列: Row ${rIdx + 1}</div>
                    <div class="tooltip-body"><div>平均差枚: ${formatVal(rAvg)}</div></div>
                `;
                c.addEventListener('mouseenter', () => { tooltip.innerHTML = rText; tooltip.classList.add('visible'); });
                c.addEventListener('mouseleave', () => { tooltip.classList.remove('visible'); });
            }
        });

        diffWrap.appendChild(rDiff);
        setWrap.appendChild(rSet);
        rowWrap.appendChild(rRowAvg);
    });
}

// ==========================================
// ANALYSIS SECTION (Charts)
// ==========================================

function renderAnalysis(data) {
    // We need to aggregate data across various dimensions
    
    // 1. Ending Digit
    const digits = Array(10).fill().map(()=>({diff:0, g:0, c:0}));
    // 2. n-Day
    const ndays = Array(10).fill().map(()=>({diff:0, g:0, c:0}));
    // 3. Weekday
    const wdNames = ['日','月','火','水','木','金','土'];
    const wdays = Array(7).fill().map(()=>({diff:0, g:0, c:0}));
    // 4. Model
    const models = {};
    // 5. Position
    const positions = {'角':{diff:0,c:0}, '角2':{diff:0,c:0}, '角3':{diff:0,c:0}, 'その他':{diff:0,c:0}};
    // 6. Row Avg (aggregate by date and row, then avg across dates)
    const rowDiffs = {}; 
    
    // Grouping for Consecutive Days and Neighbors requires sorting by date per machine
    const mHistory = {};

    data.forEach(row => {
        const d = row['日付'];
        const diff = Number(row['最終差枚']) || 0;
        const g = Number(row['累計ゲーム']) || 0;
        const num = normalizeNum(row['台番号']);
        const model = row['機種名'];
        
        // Digit
        const digit = parseInt(num.slice(-1));
        if (!isNaN(digit)) { digits[digit].diff += diff; digits[digit].g += g; digits[digit].c++; }
        
        // nDay
        const dayStr = d.split('-')[2];
        const nday = parseInt(dayStr.slice(-1));
        ndays[nday].diff += diff; ndays[nday].g += g; ndays[nday].c++;

        // Weekday
        const wday = new Date(d).getDay();
        wdays[wday].diff += diff; wdays[wday].g += g; wdays[wday].c++;

        // Model
        if (!models[model]) models[model] = {diff:0, g:0, c:0};
        models[model].diff += diff; models[model].g += g; models[model].c++;

        // Layout based metrics
        const loc = layoutLookup[num];
        if (loc) {
            let pKey = loc.pos === 0 ? '角' : loc.pos === 1 ? '角2' : loc.pos === 2 ? '角3' : 'その他';
            positions[pKey].diff += diff; positions[pKey].c++;

            const rKey = `Row ${loc.row_idx + 1}`;
            if (!rowDiffs[rKey]) rowDiffs[rKey] = {diff:0, c:0};
            rowDiffs[rKey].diff += diff; rowDiffs[rKey].c++;
        }

        // History
        if (!mHistory[num]) mHistory[num] = [];
        mHistory[num].push({...row, diff, g});
    });

    // Chart Helpers
    const buildChartData = (aggObj) => {
        let labels=[], dDiff=[], dPayout=[];
        for (let [k, v] of Object.entries(aggObj)) {
            if (v.c === 0) continue;
            labels.push(k);
            dDiff.push(v.diff / v.c);
            dPayout.push(v.g > 0 ? (((3*v.g)+v.diff)/(3*v.g)*100) : 0);
        }
        return {labels, dDiff, dPayout};
    };

    const drawBarChart = (id, labels, dataArr, label) => {
        const ctx = document.getElementById(id);
        const parent = ctx.parentElement;
        const height = Math.max(300, labels.length * 30);
        parent.style.height = `${height}px`;

        if (charts[id]) charts[id].destroy();
        charts[id] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{ label: label, data: dataArr, backgroundColor: dataArr.map(v=>v>0?'rgba(59,130,246,0.7)':'rgba(239,68,68,0.7)') }]
            },
            options: { 
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                onClick: (e, elements) => {
                    if (id === 'chart-row-avg-heatmap' && elements.length > 0) {
                        const index = elements[0].index;
                        const rowWrap = document.getElementById('row-heatmap-wrapper');
                        const targetRow = rowWrap.children[index];
                        if (targetRow) {
                            targetRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            targetRow.classList.add('highlight-row');
                            setTimeout(() => targetRow.classList.remove('highlight-row'), 2000);
                        }
                    }
                }
            }
        });
    };

    drawBarChart('chart-digit', buildChartData(digits).labels, buildChartData(digits).dDiff, '平均差枚');
    drawBarChart('chart-nday', buildChartData(ndays).labels, buildChartData(ndays).dDiff, '平均差枚');
    
    const wdOrder = [1, 2, 3, 4, 5, 6, 0]; // Mon to Sun
    const orderedWdays = wdOrder.map(idx => ({...wdays[idx], name: wdNames[idx]}));
    drawBarChart('chart-weekday', buildChartData(orderedWdays).labels, buildChartData(orderedWdays).dDiff, '平均差枚');
    
    const mData = buildChartData(models);
    drawBarChart('chart-model', mData.labels, mData.dDiff, '平均差枚');

    const rData = buildChartData(rowDiffs);
    drawBarChart('chart-row-avg', rData.labels, rData.dDiff, '列平均差枚');
    drawBarChart('chart-row-avg-heatmap', rData.labels, rData.dDiff, '列平均差枚');

    const pData = buildChartData(positions);
    drawBarChart('chart-position', pData.labels, pData.dDiff, '平均差枚');

    // Consecutive Analysis & Neighbors
    const consNeg = Array(7).fill().map(()=>({diff:0, c:0}));
    const consPos = Array(7).fill().map(()=>({diff:0, c:0}));
    
    // Single Neighbor (Diff -> Avg Diff)
    const neiDiffBuckets = {'<-4000':{diff:0,c:0}, '-4000~-2001':{diff:0,c:0}, '-2000~-1':{diff:0,c:0}, '0~2000':{diff:0,c:0}, '2001~4000':{diff:0,c:0}, '>4000':{diff:0,c:0}};
    // Single Neighbor Setting -> Avg Setting
    const neiSetBuckets = {1:{diff:0,c:0}, 2:{diff:0,c:0}, 3:{diff:0,c:0}, 4:{diff:0,c:0}, 5:{diff:0,c:0}, 6:{diff:0,c:0}};
    
    // Both Neighbors Diff
    const bothDiffBuckets = {'<-4000':{diff:0,c:0}, '-4000~-2001':{diff:0,c:0}, '-2000~-1':{diff:0,c:0}, '0~2000':{diff:0,c:0}, '2001~4000':{diff:0,c:0}, '>4000':{diff:0,c:0}};
    const bothSetBuckets = {'456':{diff:0,c:0}, 'Others':{diff:0,c:0}};

    const getBucket = (d) => {
        if(d <= -4001) return '<-4000'; if(d <= -2001) return '-4000~-2001';
        if(d < 0) return '-2000~-1'; if(d <= 2000) return '0~2000';
        if(d <= 4000) return '2001~4000'; return '>4000';
    };

    // Prepare Date-Machine matrix for neighbor lookups
    const matrix = {};
    for (const [m, hist] of Object.entries(mHistory)) {
        const normM = normalizeNum(m);
        hist.forEach(r => {
            if(!matrix[r['日付']]) matrix[r['日付']] = {};
            matrix[r['日付']][normM] = r;
        });
    }

    for (const [m, hist] of Object.entries(mHistory)) {
        hist.sort((a,b)=>a['日付'].localeCompare(b['日付']));
        let negStreak = 0, posStreak = 0;
        
        for (let i = 0; i < hist.length; i++) {
            const row = hist[i];
            const diff = row.diff;
            const g = Number(row['累計ゲーム']) || 0;

            if (g === 0) continue; // Skip non-played days for streaks

            // Consecutive
            const nIdx = Math.min(negStreak, 6);
            const pIdx = Math.min(posStreak, 6);
            consNeg[nIdx].diff += diff; consNeg[nIdx].c++;
            consPos[pIdx].diff += diff; consPos[pIdx].c++;

            if (diff < 0) { negStreak++; posStreak = 0; }
            else if (diff > 0) { posStreak++; negStreak = 0; }
            else { negStreak=0; posStreak=0; }

            // Neighbors
            const loc = layoutLookup[m];
            if (loc) {
                const dateMap = matrix[row['日付']];
                let leftM = null, rightM = null;
                layoutData[loc.row_idx].forEach(c => {
                    if (c !== '') {
                        const normC = normalizeNum(c);
                        const cloc = layoutLookup[normC];
                        if (cloc && cloc.col_idx === loc.col_idx - 1) leftM = normC;
                        if (cloc && cloc.col_idx === loc.col_idx + 1) rightM = normC;
                    }
                });

                const rLeft = leftM ? dateMap[leftM] : null;
                const rRight = rightM ? dateMap[rightM] : null;

                const calcSet = (r) => {
                    if(!r) return null;
                    const e = estimateSetting(r['機種名'], r['累計ゲーム']||0, r['BIG']||0, r['REG']||0);
                    return e ? e.setting : null;
                };

                const mySet = calcSet(row);

                // Single Neighbor (Treat left and right as independent samples)
                [rLeft, rRight].forEach(nR => {
                    if (nR) {
                        neiDiffBuckets[getBucket(nR.diff)].diff += diff;
                        neiDiffBuckets[getBucket(nR.diff)].c++;

                        const nSet = calcSet(nR);
                        if (nSet && mySet) {
                            neiSetBuckets[nSet].diff += mySet;
                            neiSetBuckets[nSet].c++;
                        }
                    }
                });

                // Both Neighbors
                if (rLeft && rRight) {
                    const lB = getBucket(rLeft.diff);
                    const rB = getBucket(rRight.diff);
                    if (lB === rB) {
                        bothDiffBuckets[lB].diff += diff;
                        bothDiffBuckets[lB].c++;
                    }

                    const ls = calcSet(rLeft);
                    const rs = calcSet(rRight);
                    if (mySet && ls && rs) {
                        if (ls >= 4 && rs >= 4) { bothSetBuckets['456'].diff += mySet; bothSetBuckets['456'].c++; }
                        else { bothSetBuckets['Others'].diff += mySet; bothSetBuckets['Others'].c++; }
                    }
                }
            }
        }
    }

    drawBarChart('chart-cons-neg', ['0日','1日','2日','3日','4日','5日','6日以上'], consNeg.map(v=>v.c?v.diff/v.c:0), '翌日平均差枚');
    drawBarChart('chart-cons-pos', ['0日','1日','2日','3日','4日','5日','6日以上'], consPos.map(v=>v.c?v.diff/v.c:0), '翌日平均差枚');

    const nbDiffData = buildChartData(neiDiffBuckets);
    drawBarChart('chart-neighbor-diff', nbDiffData.labels, nbDiffData.dDiff, '平均差枚');

    const nbSetData = buildChartData(neiSetBuckets);
    drawBarChart('chart-neighbor-setting', nbSetData.labels, nbSetData.dDiff, '自台平均設定');

    const bothDiffData = buildChartData(bothDiffBuckets);
    drawBarChart('chart-both-neighbor-diff', bothDiffData.labels, bothDiffData.dDiff, '平均差枚');

    const bothSetData = buildChartData(bothSetBuckets);
    drawBarChart('chart-both-neighbor-setting', bothSetData.labels, bothSetData.dDiff, '自台平均設定');
}

document.addEventListener('DOMContentLoaded', init);
