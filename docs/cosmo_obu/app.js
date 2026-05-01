// ==========================================
// Configuration
// ==========================================
// コスモジャパン大府店向けキーワード（半角カタカナ）
const MACHINE_KEYWORDS = {
    hanahana: 'ハナハナ',
    juggler: 'ジャグラー'
};

let MACHINE_GROUPS = {
    hanahana: [],
    juggler: []
};

function updateMachineGroups(data) {
    const hanahanaSet = new Set();
    const jugglerSet = new Set();
    data.forEach(row => {
        const model = row['機種名'];
        if (!model) return;
        if (model.includes(MACHINE_KEYWORDS.hanahana)) hanahanaSet.add(model);
        if (model.includes(MACHINE_KEYWORDS.juggler)) jugglerSet.add(model);
    });
    MACHINE_GROUPS.hanahana = Array.from(hanahanaSet);
    MACHINE_GROUPS.juggler = Array.from(jugglerSet);
    console.log('Dynamic MACHINE_GROUPS:', MACHINE_GROUPS);
}

// コスモジャパン大府店 設定推測用 コイン持ち・確率テーブル（仮値 ※後で実際の値に修正すること）
const MACHINE_PROBS = {
    // ハナハナシリーズ
    'ドラゴンハナハナ～閃光～‐30': { 1: { big: 256, reg: 642 }, 2: { big: 246, reg: 585 }, 3: { big: 235, reg: 537 }, 4: { big: 224, reg: 489 }, 5: { big: 212, reg: 442 }, 6: { big: 199, reg: 399 } },
    'ニューキングハナハナV‐30': { 1: { big: 299, reg: 496 }, 2: { big: 291, reg: 471 }, 3: { big: 281, reg: 442 }, 4: { big: 268, reg: 409 }, 5: { big: 253, reg: 372 } },
    'スターハナハナ‐30': { 1: { big: 270, reg: 387 }, 2: { big: 262, reg: 354 }, 3: { big: 252, reg: 322 }, 4: { big: 240, reg: 293 }, 5: { big: 229, reg: 267 }, 6: { big: 218, reg: 242 } },
    // ジャグラーシリーズ
    'ウルトラミラクルジャグラー': { 1: { big: 267.5, reg: 425.6 }, 2: { big: 261.1, reg: 402.1 }, 3: { big: 256.0, reg: 350.5 }, 4: { big: 242.7, reg: 322.8 }, 5: { big: 233.2, reg: 297.9 }, 6: { big: 216.3, reg: 277.7 } },
    'ネオアイムジャグラーEX': { 1: { big: 273.1, reg: 439.8 }, 2: { big: 269.7, reg: 399.6 }, 3: { big: 269.7, reg: 331.0 }, 4: { big: 259.0, reg: 315.1 }, 5: { big: 259.0, reg: 255.0 }, 6: { big: 255.0, reg: 255.0 } },
    'ゴーゴージャグラー3': { 1: { big: 259.0, reg: 354.2 }, 2: { big: 258.0, reg: 332.7 }, 3: { big: 257.0, reg: 306.2 }, 4: { big: 254.0, reg: 268.6 }, 5: { big: 247.3, reg: 247.3 }, 6: { big: 234.9, reg: 234.9 } },
    'ジャグラーガールズ': { 1: { big: 273.1, reg: 381.0 }, 2: { big: 270.8, reg: 350.5 }, 3: { big: 260.1, reg: 316.6 }, 4: { big: 250.1, reg: 281.3 }, 5: { big: 243.6, reg: 270.8 }, 6: { big: 226.0, reg: 252.1 } },
    'ミスタージャグラー': { 1: { big: 268.6, reg: 374.5 }, 2: { big: 267.5, reg: 354.2 }, 3: { big: 260.1, reg: 331.0 }, 4: { big: 249.2, reg: 291.3 }, 5: { big: 240.9, reg: 257.0 }, 6: { big: 237.4, reg: 237.4 } },
    'ハッピージャグラーVIII': { 1: { big: 273.1, reg: 397.2 }, 2: { big: 270.8, reg: 362.1 }, 3: { big: 263.2, reg: 332.7 }, 4: { big: 254.0, reg: 300.6 }, 5: { big: 239.2, reg: 273.1 }, 6: { big: 226.0, reg: 256.0 } },
};

let rawData = [], layoutData = [], layoutLookup = {};
let currentTab = 'all', currentPeriod = '3m', currentEventFilter = 'none', currentSection = 'summary-section';
let charts = {}, activeDate = null, currentCumulFilter = 'all';
let diffThresholds = { neg1: -2000, neg2: -1000, pos1: 1000, pos2: 2000 };
// コスモ大府店はデータ分割なし（全期間使用）

const tooltip = document.createElement('div');
tooltip.className = 'custom-tooltip';
document.body.appendChild(tooltip);
document.addEventListener('mousemove', e => {
    if (tooltip.classList.contains('visible')) { tooltip.style.left = e.pageX + 15 + 'px'; tooltip.style.top = e.pageY + 15 + 'px'; }
});

// ==========================================
// Utils
// ==========================================
function normalizeNum(n) { if (n === null || n === undefined || n === '') return ''; return String(n).padStart(4, '0'); }
function percentile(arr, p) { if (!arr.length) return 0; const s = [...arr].sort((a, b) => a - b); const i = (p / 100) * (s.length - 1); const lo = Math.floor(i), hi = lo + 1, w = i % 1; if (hi >= s.length) return s[lo]; return s[lo] * (1 - w) + s[hi] * w; }
function payout(diff, g) { return g > 0 ? (((3 * g) + diff) / (3 * g) * 100) : 0; }
function formatVal(v) { if (v > 0) return `<span style="color:#38bdf8;font-weight:bold">+${Math.round(v).toLocaleString()}</span>`; if (v < 0) return `<span style="color:#ef4444;font-weight:bold">${Math.round(v).toLocaleString()}</span>`; return `<span style="color:#94a3b8;font-weight:bold">0</span>`; }
function formatPct(v) { const n = parseFloat(v); if (n >= 100) return `<span style="color:#38bdf8;font-weight:bold">${n.toFixed(2)}%</span>`; return `<span style="color:#ef4444;font-weight:bold">${n.toFixed(2)}%</span>`; }
function getPosLabel(num) { const l = layoutLookup[num]; if (!l) return '不明'; return l.pos === 0 ? '角' : l.pos === 1 ? '角2' : l.pos === 2 ? '角3' : 'その他'; }

function isSignificant(digitVals, overallAvg) {
    if (digitVals.length < 3) return false;
    const n = digitVals.length, mean = digitVals.reduce((a, b) => a + b, 0) / n;
    if (mean <= 0 || mean <= overallAvg * 1.1) return false;
    const variance = digitVals.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / (n - 1);
    if (variance === 0) return true;
    return (mean - overallAvg) / (Math.sqrt(variance) / Math.sqrt(n)) > 1.645;
}

function estimateSetting(model, games, big, reg) {
    games = Number(games) || 0; big = Number(big) || 0; reg = Number(reg) || 0;
    if (!MACHINE_PROBS[model] || games < 100) return null;
    const probs = MACHINE_PROBS[model];
    let logW = {}, maxLW = -Infinity;
    for (const [s, p] of Object.entries(probs)) {
        const pB = 1 / p.big, pR = 1 / p.reg, pN = 1 - pB - pR;
        if (pN <= 0) continue;
        const lw = big * Math.log(pB) + reg * Math.log(pR) + (games - big - reg) * Math.log(pN);
        logW[s] = lw; if (lw > maxLW) maxLW = lw;
    }
    let sum = 0, exp = {};
    for (const [s, lw] of Object.entries(logW)) { const w = Math.exp(lw - maxLW); exp[s] = w; sum += w; }
    let best = null, bestP = -1;
    for (const [s, w] of Object.entries(exp)) { const p = w / sum; if (p > bestP) { bestP = p; best = s; } }
    return { setting: parseInt(best), prob: bestP };
}

// ==========================================
// Init
// ==========================================
Chart.defaults.font.size = 14; Chart.defaults.font.weight = 'bold'; Chart.defaults.color = '#f1f5f9';

async function init() {
    setupTheme(); setupEventListeners();
    window.addEventListener('resize', () => requestAnimationFrame(applyHeatmapCellSizes));
    try {
        const [dr, lr] = await Promise.all([fetch('data.json'), fetch('layout.json')]);
        rawData = await dr.json(); layoutData = await lr.json();
        updateMachineGroups(rawData); // Build groups dynamically from data
        const maxCols = layoutData.reduce((max, r) => Math.max(max, r.length), 0);
        layoutData.forEach(r => { while (r.length < maxCols) r.push(''); });
        buildLayoutLookup();
        populateTargetModelFilter();
        updateDashboard();

    } catch (err) { console.error(err); }
}

function buildLayoutLookup() {
    layoutLookup = {};
    layoutData.forEach((row, rIdx) => {
        row.forEach((cell, cIdx) => {
            if (cell === '') return;
            const numStr = normalizeNum(cell), numVal = parseInt(numStr, 10);
            let hL = 0, hR = 0, vT = 0, vB = 0;
            for (let i = cIdx - 1; i >= 0; i--) { if (layoutData[rIdx][i] !== '') hL++; else break; }
            for (let i = cIdx + 1; i < layoutData[rIdx].length; i++) { if (layoutData[rIdx][i] !== '') hR++; else break; }
            for (let i = rIdx - 1; i >= 0; i--) { if (layoutData[i][cIdx] !== '') vT++; else break; }
            for (let i = rIdx + 1; i < layoutData.length; i++) { if (layoutData[i][cIdx] !== '') vB++; else break; }
            let dist = null, dir = 'horizontal';
            if (hL + hR > vT + vB) { dist = Math.min(hL, hR); dir = 'horizontal'; }
            else if (vT + vB > hL + hR) { dist = Math.min(vT, vB); dir = 'vertical'; }
            else if (hL + hR > 0) { dist = Math.min(hL, hR); dir = 'horizontal'; }
            else if (vT + vB > 0) { dist = Math.min(vT, vB); dir = 'vertical'; }
            else { dist = 0; }
            layoutLookup[numStr] = { row_idx: rIdx, col_idx: cIdx, pos: dist, direction: dir, islandId: '' };
        });
    });

    const rows = layoutData.length;
    const cols = layoutData[0].length;
    const visited = Array(rows).fill(0).map(() => Array(cols).fill(false));

    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            if (layoutData[r][c] !== '' && !visited[r][c]) {
                const queue = [[r, c]];
                visited[r][c] = true;
                const islandCells = [];

                while (queue.length > 0) {
                    const [currR, currC] = queue.shift();
                    const cellVal = normalizeNum(layoutData[currR][currC]);
                    const numVal = parseInt(cellVal, 10);

                    islandCells.push(cellVal);

                    const currDir = layoutLookup[cellVal].direction;
                    let neighbors = [];
                    if (currDir === 'horizontal') {
                        neighbors = [[currR, currC - 1], [currR, currC + 1]];
                    } else if (currDir === 'vertical') {
                        neighbors = [[currR - 1, currC], [currR + 1, currC]];
                    }

                    for (const [nr, nc] of neighbors) {
                        if (nr >= 0 && nr < rows && nc >= 0 && nc < cols) {
                            if (layoutData[nr][nc] !== '' && !visited[nr][nc]) {
                                const nValStr = normalizeNum(layoutData[nr][nc]);
                                const nVal = parseInt(nValStr, 10);

                                if (layoutLookup[nValStr].direction === currDir) {
                                    visited[nr][nc] = true;
                                    queue.push([nr, nc]);
                                }
                            }
                        }
                    }
                }

                if (islandCells.length > 0) {
                    islandCells.sort((a, b) => parseInt(a) - parseInt(b));
                    const startNum = parseInt(islandCells[0]), endNum = parseInt(islandCells[islandCells.length - 1]);
                    const islandName = `島 ${startNum}-${endNum}`;
                    islandCells.forEach(cell => { layoutLookup[cell].islandId = islandName; layoutLookup[cell].islandMin = startNum; });
                }
            }
        }
    }

    for (const cell of Object.keys(layoutLookup)) {
        const numVal = parseInt(cell, 10);
        if (!layoutLookup[cell].islandId) {
            layoutLookup[cell].islandId = `島 ${numVal}`; layoutLookup[cell].islandMin = numVal;
        }
    }
}

// ==========================================
// Theme & Events
// ==========================================
function setupTheme() {
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (prefersDark) {
        document.body.classList.add('dark-theme');
    } else {
        document.body.classList.remove('dark-theme');
    }

    const btn = document.getElementById('theme-btn');
    const isDark = document.body.classList.contains('dark-theme');
    updateThemeIcon(isDark);
    Chart.defaults.color = isDark ? '#94a3b8' : '#666';

    btn.addEventListener('click', () => {
        const d = document.body.classList.toggle('dark-theme');
        updateThemeIcon(d); Chart.defaults.color = d ? '#94a3b8' : '#666'; updateDashboard();
    });

    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
            if (e.matches) document.body.classList.add('dark-theme');
            else document.body.classList.remove('dark-theme');
            const d = document.body.classList.contains('dark-theme');
            updateThemeIcon(d); Chart.defaults.color = d ? '#94a3b8' : '#666'; updateDashboard();
        });
    }
}
function updateThemeIcon(isDark) {
    const svg = document.querySelector('#theme-btn svg');
    svg.innerHTML = isDark ? `<path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"></path>`
        : `<path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"></path>`;
}

function setupEventListeners() {
    document.querySelectorAll('#machine-tabs .tab-btn').forEach(btn => {
        btn.addEventListener('click', e => {
            document.querySelectorAll('#machine-tabs .tab-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active'); currentTab = e.target.dataset.target; activeDate = null; updateDashboard();
        });
    });
    document.querySelectorAll('#period-tabs .tab-btn').forEach(btn => {
        btn.addEventListener('click', e => {
            document.querySelectorAll('#period-tabs .tab-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active'); currentPeriod = e.target.dataset.target; activeDate = null; updateDashboard();
        });
    });
    document.getElementById('event-filter').addEventListener('change', e => {
        currentEventFilter = e.target.value; activeDate = null; updateDashboard();
    });
    document.querySelectorAll('.main-nav .nav-btn').forEach(btn => {
        btn.addEventListener('click', e => {
            document.querySelectorAll('.main-nav .nav-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            document.querySelectorAll('.content-grid > section').forEach(s => { s.style.display = 'none'; s.classList.remove('active-section'); });
            const t = document.getElementById(e.target.dataset.section);
            t.style.display = 'block'; t.classList.add('active-section'); updateDashboard();
        });
    });
    document.getElementById('modal-close-btn').addEventListener('click', closeModal);
    document.getElementById('date-detail-modal').addEventListener('click', e => {
        if (e.target === e.currentTarget) closeModal();
    });
    // cumul filter tabs (delegated, set up after DOM ready but before first render)
    document.getElementById('cumul-filter-tabs').addEventListener('click', e => {
        const btn = e.target.closest('.tab-btn'); if (!btn) return;
        document.querySelectorAll('#cumul-filter-tabs .tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active'); currentCumulFilter = btn.dataset.target;
        renderAnalysis(getFilteredData());
    });
    // コスモ大府店は旧データトグルボタンなし
}

function openModal(date) {
    document.getElementById('date-detail-modal').style.display = 'flex';
    document.getElementById('modal-date-title').textContent = date + ' 詳細';
    document.body.classList.add('modal-open');
    renderDateDetail(date);
}
function closeModal() {
    document.getElementById('date-detail-modal').style.display = 'none';
    document.body.classList.remove('modal-open');
}

// ==========================================
// Filtering
// ==========================================
function getFilteredData() {
    if (!rawData.length) return [];
    let f = rawData;
    if (currentTab !== 'all') {
        const m = currentTab === 'hanahana' ? MACHINE_GROUPS.hanahana : MACHINE_GROUPS.juggler;
        f = f.filter(r => m.includes(r['機種名']));
    }
    if (f.length) {
        const dates = rawData.map(r => r['日付']).sort();
        const latestStr = dates[dates.length - 1];
        const latest = new Date(latestStr);
        if (currentPeriod === 'latest') { f = f.filter(r => r['日付'] === latestStr); }
        else if (currentPeriod === '3d') { const c = new Date(latest); c.setDate(c.getDate() - 2); f = f.filter(r => r['日付'] >= c.toISOString().split('T')[0]); }
        else if (currentPeriod === '7d') { const c = new Date(latest); c.setDate(c.getDate() - 6); f = f.filter(r => r['日付'] >= c.toISOString().split('T')[0]); }
        else if (currentPeriod === '1m') { const c = new Date(latest); c.setMonth(c.getMonth() - 1); f = f.filter(r => r['日付'] >= c.toISOString().split('T')[0]); }
        else if (currentPeriod === '3m') { const c = new Date(latest); c.setMonth(c.getMonth() - 3); f = f.filter(r => r['日付'] >= c.toISOString().split('T')[0]); }
    }
    if (currentEventFilter !== 'none') {
        f = f.filter(r => {
            const d = new Date(r['日付']), day = d.getDate();
            // 1の付く日: 1日, 11日, 21日, 31日
            const isEvent = (day === 1 || day === 11 || day === 21 || day === 31);
            if (currentEventFilter === '1') return isEvent;
            if (currentEventFilter === 'not1') return !isEvent;
            return true;
        });
    }
    return f;
}

function calculateDynamicThresholds(data) {
    if (!data.length) return;
    // ヒートマップで表示されるのは台ごとの期間平均であるため、しきい値も台ごとの平均分布から算出する
    const machineStats = {};
    data.forEach(d => {
        const num = d['台番号'];
        if (!machineStats[num]) machineStats[num] = { total: 0, count: 0 };
        machineStats[num].total += Number(d['最終差枚']) || 0;
        machineStats[num].count++;
    });
    const diffs = Object.values(machineStats).map(s => Math.round(s.total / s.count));

    const pos = diffs.filter(v => v > 0), neg = diffs.filter(v => v < 0);
    diffThresholds.pos1 = pos.length ? percentile(pos, 33) : 500;
    diffThresholds.pos2 = pos.length ? percentile(pos, 66) : 1000;
    diffThresholds.neg1 = neg.length ? percentile(neg, 33) : -1000;
    diffThresholds.neg2 = neg.length ? percentile(neg, 66) : -500;
    updateHeatmapLegends();
}

function enableChartPan(id, isPayout = false) {
    const canvas = document.getElementById(id);
    if (!canvas || canvas.dataset.panEnabled) return;
    canvas.dataset.panEnabled = "true";

    let isDragging = false, lastX = 0;
    const getChart = () => Chart.getChart(canvas);

    const shiftScale = (chart, shiftPixels) => {
        const scale = chart.scales.x;
        const range = scale.max - scale.min;
        const chartAreaWidth = chart.chartArea.right - chart.chartArea.left;
        if (chartAreaWidth <= 0) return;

        const valueShift = (shiftPixels / chartAreaWidth) * range;

        const vals = chart.data.datasets[0].data;
        const dataMin = vals.reduce((a, b) => Math.min(a, b), 0);
        const dataMax = vals.reduce((a, b) => Math.max(a, b), 0);

        const boundMin = isPayout ? Math.min(80, dataMin - 5) : Math.min(-2000, dataMin - 500);
        const boundMax = isPayout ? Math.max(120, dataMax + 5) : Math.max(2000, dataMax + 500);

        let newMin = scale.min - valueShift;
        let newMax = scale.max - valueShift;

        if (newMin < boundMin) { newMin = boundMin; newMax = boundMin + range; }
        if (newMax > boundMax) { newMax = boundMax; newMin = boundMax - range; }

        chart.options.scales.x.min = newMin;
        chart.options.scales.x.max = newMax;
        chart.update('none');
    };

    canvas.addEventListener('mousedown', e => { isDragging = true; lastX = e.clientX; canvas.style.cursor = 'grabbing'; });
    window.addEventListener('mouseup', () => { isDragging = false; canvas.style.cursor = 'auto'; });
    window.addEventListener('mousemove', e => { if (!isDragging) return; shiftScale(getChart(), e.clientX - lastX); lastX = e.clientX; });

    canvas.addEventListener('wheel', e => {
        if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) {
            e.preventDefault();
            shiftScale(getChart(), -e.deltaX);
        }
    }, { passive: false });

    let touchX = 0, touchY = 0, isPanning = false;
    canvas.addEventListener('touchstart', e => {
        if (e.touches.length === 1) { touchX = e.touches[0].clientX; touchY = e.touches[0].clientY; isPanning = false; }
    }, { passive: true });
    canvas.addEventListener('touchmove', e => {
        if (e.touches.length === 1) {
            const dx = e.touches[0].clientX - touchX, dy = e.touches[0].clientY - touchY;
            if (!isPanning && Math.abs(dx) > Math.abs(dy) + 5) isPanning = true;
            if (isPanning) {
                e.preventDefault();
                shiftScale(getChart(), dx);
                touchX = e.touches[0].clientX; touchY = e.touches[0].clientY;
            }
        }
    }, { passive: false });
}

function updateDashboard() {
    const f = getFilteredData(); calculateDynamicThresholds(f);
    const sec = document.querySelector('.main-nav .nav-btn.active').dataset.section;
    if (sec === 'summary-section') renderSummary(f);
    else if (sec === 'heatmap-section') renderHeatmaps(f);
    else if (sec === 'machine-section') renderMachineTab(f);
    else if (sec === 'analysis-section') renderAnalysis(f);
    else if (sec === 'target-section') {
        // Auto re-render only if results are already showing
        const res = document.getElementById('target-results');
        if (res && res.style.display !== 'none') renderTargetSupport(f);
    }
}


// ==========================================
// SUMMARY SECTION
// ==========================================
function renderSummary(data) {
    const daily = {}, monthly = {};
    data.forEach(row => {
        const date = row['日付'], month = date.substring(0, 7);
        const diff = Number(row['最終差枚']) || 0, g = Number(row['累計ゲーム']) || 0;
        const num = normalizeNum(row['台番号']), lastDigit = parseInt(num.slice(-1));
        if (!daily[date]) daily[date] = { date, diff: 0, g: 0, count: 0, digits: Array(10).fill().map(() => []) };
        daily[date].diff += diff; daily[date].g += g; daily[date].count += 1;
        if (!isNaN(lastDigit)) daily[date].digits[lastDigit].push(diff);
        if (!monthly[month]) monthly[month] = { month, diff: 0, g: 0, count: 0 };
        monthly[month].diff += diff; monthly[month].g += g; monthly[month].count += 1;
    });

    const dailyDates = Object.keys(daily).sort();
    let monthCumul = {};
    dailyDates.forEach(date => {
        const month = date.substring(0, 7);
        if (monthCumul[month] === undefined) monthCumul[month] = 0;
        monthCumul[month] += daily[date].diff;
        daily[date].cumulDiff = monthCumul[month];
    });

    const dailyArr = Object.values(daily).sort((a, b) => b.date.localeCompare(a.date));
    const dTbody = document.getElementById('summary-tbody'); dTbody.innerHTML = '';
    let chartLabels = [], chartData = [];

    dailyArr.forEach(d => {
        d.avgDiff = d.count > 0 ? Math.round(d.diff / d.count) : 0;
        d.avgG = d.count > 0 ? Math.round(d.g / d.count) : 0;
        d.payoutVal = payout(d.diff, d.g);
        let sigDigits = [];
        d.digits.forEach((vals, i) => { if (isSignificant(vals, d.avgDiff)) sigDigits.push(i); });
        d.bias = sigDigits.length ? sigDigits.join(', ') : 'なし';
        chartLabels.push(d.date); chartData.push(d.avgDiff);
        const tr = document.createElement('tr');
        if (activeDate === d.date) tr.classList.add('selected');
        tr.classList.add('clickable');
        tr.innerHTML = `<td style="text-align:left">${d.date}</td><td>${formatVal(d.diff)}</td><td>${formatVal(d.cumulDiff)}</td><td>${formatVal(d.avgDiff)}</td><td>${d.avgG.toLocaleString()}</td><td>${d.g.toLocaleString()}</td><td>${formatPct(d.payoutVal)}</td><td>${d.bias}</td>`;
        tr.addEventListener('click', () => openModal(d.date));
        dTbody.appendChild(tr);
    });

    const monthlyArr = Object.values(monthly).sort((a, b) => b.month.localeCompare(a.month));
    const mTbody = document.getElementById('monthly-tbody'); mTbody.innerHTML = '';
    monthlyArr.forEach(m => {
        const avg = m.count > 0 ? Math.round(m.diff / m.count) : 0, avgG = m.count > 0 ? Math.round(m.g / m.count) : 0;
        mTbody.innerHTML += `<tr><td>${m.month}</td><td>${formatVal(m.diff)}</td><td>${formatVal(avg)}</td><td>${avgG.toLocaleString()}</td><td>${m.g.toLocaleString()}</td><td>${formatPct(payout(m.diff, m.g))}</td></tr>`;
    });

    const ctx = document.getElementById('diff-chart');
    if (charts['daily']) charts['daily'].destroy();
    const h = Math.max(300, dailyArr.length * 28);
    ctx.parentElement.style.height = `${h}px`;
    charts['daily'] = new Chart(ctx, {
        type: 'bar', data: { labels: chartLabels, datasets: [{ data: chartData, backgroundColor: chartData.map(v => v > 0 ? 'rgba(59,130,246,0.8)' : 'rgba(239,68,68,0.8)'), borderRadius: 4 }] },
        options: {
            indexAxis: 'y', responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false }, datalabels: { display: false } },
            scales: { x: { grid: { color: 'rgba(128,128,128,0.2)' } }, y: { grid: { display: false }, ticks: { font: { size: 12 } } } }
        }
    });
}

// ==========================================
// HEATMAP SECTION
// ==========================================
const SETTING_COLORS = { 1: 'rgba(60,20,180,0.8)', 2: 'rgba(30,100,230,0.8)', 3: 'rgba(0,190,255,0.8)', 4: 'rgba(255,220,0,0.8)', 5: 'rgba(255,130,0,0.8)', 6: 'rgba(230,40,40,0.8)' };

function getHeatmapColor(v, t = diffThresholds) {
    if (v === 0) return 'transparent';
    if (v <= t.neg1) return 'rgba(60,20,180,0.8)';
    if (v <= t.neg2) return 'rgba(30,100,230,0.8)';
    if (v < 0) return 'rgba(0,190,255,0.8)';
    if (v <= t.pos1) return 'rgba(255,220,0,0.8)';
    if (v <= t.pos2) return 'rgba(255,130,0,0.8)';
    return 'rgba(230,40,40,0.8)';
}

function generateLegendHtml(t) {
    return `
        <div class="legend-item"><span class="color-box" style="background:rgba(60,20,180,0.8)"></span>${Math.round(t.neg1)}以下</div>
        <div class="legend-item"><span class="color-box" style="background:rgba(30,100,230,0.8)"></span>${Math.round(t.neg1)}〜${Math.round(t.neg2)}</div>
        <div class="legend-item"><span class="color-box" style="background:rgba(0,190,255,0.8)"></span>${Math.round(t.neg2)}〜-1</div>
        <div class="legend-item"><span class="color-box" style="background:transparent;border:1px solid #ccc"></span>0</div>
        <div class="legend-item"><span class="color-box" style="background:rgba(255,220,0,0.8)"></span>1〜${Math.round(t.pos1)}</div>
        <div class="legend-item"><span class="color-box" style="background:rgba(255,130,0,0.8)"></span>${Math.round(t.pos1)}〜${Math.round(t.pos2)}</div>
        <div class="legend-item"><span class="color-box" style="background:rgba(230,40,40,0.8)"></span>${Math.round(t.pos2)}以上</div>`;
}

function updateHeatmapLegends() {
    const lHtml = generateLegendHtml(diffThresholds);
    const dl = document.getElementById('diff-legend'); if (dl) dl.innerHTML = lHtml;
}

function buildHeatmapGrid(wrapId, cellBuilder) {
    const wrap = document.getElementById(wrapId); wrap.innerHTML = '';
    const inner = document.createElement('div');
    inner.className = 'heatmap-inner';
    // 末尾の全空行を除去して縦の空白を解消
    const trimmedData = [...layoutData];
    while (trimmedData.length > 0 && trimmedData[trimmedData.length - 1].every(c => c === '')) trimmedData.pop();
    trimmedData.forEach((row, rIdx) => {
        const rowEl = document.createElement('div'); rowEl.className = 'heatmap-row';
        row.forEach((cell, cIdx) => {
            const num = normalizeNum(cell), isEmpty = cell === '';
            const el = document.createElement('div'); el.className = `heatmap-cell${isEmpty ? ' empty' : ''}`;
            if (!isEmpty) { el.textContent = cell; cellBuilder(el, num, rIdx, cIdx); }
            rowEl.appendChild(el);
        });
        inner.appendChild(rowEl);
    });
    wrap.appendChild(inner);
    return wrap;
}

function renderHeatmaps(data) {
    const activeData = activeDate ? data.filter(d => d['日付'] === activeDate) : data;

    const ms = {};
    activeData.forEach(row => {
        const num = normalizeNum(row['台番号']);
        if (!ms[num]) ms[num] = { diff: 0, count: 0, big: 0, reg: 0, g: 0, model: row['機種名'] };
        ms[num].diff += Number(row['最終差枚']) || 0; ms[num].big += Number(row['BIG']) || 0;
        ms[num].reg += Number(row['REG']) || 0; ms[num].g += Number(row['累計ゲーム']) || 0; ms[num].count += 1;
    });

    // Diff heatmap
    buildHeatmapGrid('diff-heatmap-wrapper', (el, num) => {
        if (!ms[num]) { el.style.backgroundColor = 'transparent'; el.style.border = '1px solid rgba(128,128,128,0.2)'; return; }
        const st = ms[num], avg = Math.round(st.diff / st.count);
        el.style.backgroundColor = getHeatmapColor(avg);
        const t = `<div class="tooltip-title">台番号: ${num}</div><div class="tooltip-body"><div>機種: ${st.model}</div><div>位置: ${getPosLabel(num)}</div><div>平均差枚: ${formatVal(avg)}</div><div>対象日数: ${st.count}日</div></div>`;
        el.addEventListener('mouseenter', () => { tooltip.innerHTML = t; tooltip.classList.add('visible'); });
        el.addEventListener('mouseleave', () => tooltip.classList.remove('visible'));
    });

    // Setting heatmap
    buildHeatmapGrid('setting-heatmap-wrapper', (el, num) => {
        if (!ms[num]) { el.style.backgroundColor = 'transparent'; el.style.border = '1px solid rgba(128,128,128,0.2)'; return; }
        const st = ms[num];
        let sText = '';
        if (MACHINE_GROUPS.hanahana.includes(st.model) || MACHINE_GROUPS.juggler.includes(st.model)) {
            const est = estimateSetting(st.model, st.g, st.big, st.reg);
            if (est) { el.style.backgroundColor = SETTING_COLORS[est.setting] || 'transparent'; sText = `推定設定:${est.setting}(${(est.prob * 100).toFixed(1)}%)`; }
        }
        const avg = Math.round(st.diff / st.count);
        const t = `<div class="tooltip-title">台番号: ${num}</div><div class="tooltip-body"><div>機種: ${st.model}</div><div>位置: ${getPosLabel(num)}</div><div>平均差枚: ${formatVal(avg)}</div>${sText ? `<div>${sText}</div>` : ''}</div>`;
        el.addEventListener('mouseenter', () => { tooltip.innerHTML = t; tooltip.classList.add('visible'); });
        el.addEventListener('mouseleave', () => tooltip.classList.remove('visible'));
    });

    // Island avg heatmap + bar chart
    const islandStats = {};
    layoutData.forEach(row => {
        row.forEach(cell => {
            const num = normalizeNum(cell);
            if (cell !== '' && ms[num] && layoutLookup[num]) {
                const l = layoutLookup[num];
                const iId = l.islandId;
                if (!islandStats[iId]) islandStats[iId] = { total: 0, count: 0, min: l.islandMin };
                islandStats[iId].total += Math.round(ms[num].diff / ms[num].count);
                islandStats[iId].count++;
            }
        });
    });
    const islandAvgs = {};
    for (const [iId, st] of Object.entries(islandStats)) { islandAvgs[iId] = st.count > 0 ? Math.round(st.total / st.count) : 0; }

    // Calculate dynamic thresholds for islands based on individual machine averages within the group
    // This makes the scale more robust and "group-aware" especially when fewer islands are involved
    const machineAvgs = Object.values(ms).map(st => Math.round(st.diff / st.count)).filter(v => v !== 0);
    const iPos = machineAvgs.filter(v => v > 0);
    const iNeg = machineAvgs.filter(v => v < 0);
    const islandThresholds = {
        pos1: iPos.length ? percentile(iPos, 33) : 200,
        pos2: iPos.length ? percentile(iPos, 66) : 500,
        neg1: iNeg.length ? percentile(iNeg, 33) : -500,
        neg2: iNeg.length ? percentile(iNeg, 66) : -200
    };
    const rl = document.getElementById('row-legend');
    if (rl) rl.innerHTML = generateLegendHtml(islandThresholds);

    const rowWrap = document.getElementById('row-heatmap-wrapper'); rowWrap.innerHTML = '';
    const rowInner = document.createElement('div');
    rowInner.className = 'heatmap-inner';

    // 末尾の空行を削除して縦方向の不自然な空白を解消
    const trimmedLayout = [...layoutData];
    while (trimmedLayout.length > 0 && trimmedLayout[trimmedLayout.length - 1].every(c => c === '')) {
        trimmedLayout.pop();
    }

    trimmedLayout.forEach(row => {
        const rowEl = document.createElement('div'); rowEl.className = 'heatmap-row';
        row.forEach(cell => {
            const num = normalizeNum(cell);
            const isEmpty = cell === '';
            const isFiltered = !isEmpty && ms[num];
            const el = document.createElement('div'); el.className = `heatmap-cell${isEmpty ? ' empty' : ''}`;
            if (!isEmpty) {
                el.textContent = cell;
                if (!isFiltered) {
                    el.style.backgroundColor = 'transparent';
                    el.style.border = '1px solid rgba(128,128,128,0.2)';
                } else {
                    const iId = layoutLookup[num] ? layoutLookup[num].islandId : '不明';
                    el.dataset.islandId = iId;
                    const iAvg = islandAvgs[iId] || 0;
                    el.style.backgroundColor = getHeatmapColor(iAvg, islandThresholds);
                    el.addEventListener('mouseenter', () => { tooltip.innerHTML = `<div class="tooltip-title">${iId}</div><div class="tooltip-body"><div>平均差枚: ${formatVal(iAvg)}</div></div>`; tooltip.classList.add('visible'); });
                    el.addEventListener('mouseleave', () => tooltip.classList.remove('visible'));
                }
            }
            rowEl.appendChild(el);
        });
        rowInner.appendChild(rowEl);
    });
    rowWrap.appendChild(rowInner);

    // Bar chart under island heatmap
    const islandArr = Object.entries(islandStats).map(([label, st]) => ({ label, avg: islandAvgs[label], min: st.min }));
    islandArr.sort((a, b) => a.min - b.min);
    const labels = islandArr.map(r => r.label), vals = islandArr.map(r => r.avg);
    const cCtx = document.getElementById('chart-row-avg-heatmap');
    if (charts['row-heatmap']) charts['row-heatmap'].destroy();
    const h = Math.max(250, labels.length * 26);
    cCtx.parentElement.style.height = `${h}px`;
    charts['row-heatmap'] = new Chart(cCtx, {
        type: 'bar',
        data: { labels, datasets: [{ label: '島平均差枚', data: vals, backgroundColor: vals.map(v => v > 0 ? 'rgba(59,130,246,0.7)' : 'rgba(239,68,68,0.7)'), borderRadius: 4 }] },
        options: {
            indexAxis: 'y', responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false }, datalabels: { display: false } },
            scales: { x: { grid: { color: 'rgba(128,128,128,0.2)' } }, y: { grid: { display: false }, ticks: { font: { size: 12 } } } },
            onClick: (e, els) => {
                if (!els.length) return;
                const idx = els[0].index;
                const tId = islandArr[idx].label;
                const cells = document.querySelectorAll(`#row-heatmap-wrapper .heatmap-cell[data-island-id="${tId}"]`);
                if (cells.length > 0) {
                    cells[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
                    cells.forEach(c => c.classList.add('highlight-island'));
                    setTimeout(() => cells.forEach(c => c.classList.remove('highlight-island')), 2000);
                }
            }
        }
    });
    // Apply JS-computed cell sizes on mobile for accurate alignment
    requestAnimationFrame(applyHeatmapCellSizes);
    // Enable pinch zoom on heatmap wrappers (mobile)
    ['diff-heatmap-wrapper', 'setting-heatmap-wrapper', 'row-heatmap-wrapper'].forEach(id => {
        enableHeatmapPinchZoom(id);
    });
}

// ==========================================
// HEATMAP CELL AUTO-SIZING (mobile)
// ==========================================
function applyHeatmapCellSizes() {
    if (!layoutData.length) return;
    const numCols = layoutData[0].length;
    const isMobile = window.innerWidth <= 768;
    const gapWidth = isMobile ? 1 : 2; // CSSのgap設定に合わせる

    // ヒートマップタブのメインヒートマップID
    const mainIds = ['diff-heatmap-wrapper', 'setting-heatmap-wrapper', 'row-heatmap-wrapper', 'target-heatmap-wrapper'];
    const wrapIds = [...mainIds, 'modal-diff-hm', 'modal-set-hm', 'modal-streak-hm', 'modal-island-hm'];

    wrapIds.forEach(id => {
        const wrap = document.getElementById(id);
        if (!wrap || !wrap.children.length) return;

        const availW = wrap.clientWidth - 8;
        const gap = (numCols - 1) * gapWidth;
        const minCell = 16;
        const cellSize = Math.max(minCell, Math.floor((availW - gap) / numCols));

        // デフォルト設定（モバイル版やモーダル用）
        let maxCell = 44;
        let maxFont = 14;

        // PC版のメインヒートマップのみ縮小して画面に収める
        if (mainIds.includes(id) && !isMobile) {
            maxCell = 19; // PC版メインタブをコンパクトにする
            maxFont = 8;
        }

        if (cellSize >= maxCell) {
            wrap.style.setProperty('--cell-size', maxCell + 'px');
            wrap.style.setProperty('--cell-font-size', maxFont + 'px');
        } else {
            // セルが上限より小さくなる場合は、計算されたcellSizeを使用して画面に収める
            const fontSize = Math.max(4, Math.floor(cellSize * 0.4));
            wrap.style.setProperty('--cell-size', cellSize + 'px');
            wrap.style.setProperty('--cell-font-size', fontSize + 'px');
        }
    });
}

// ==========================================
// HEATMAP PINCH ZOOM (mobile)
// ==========================================
const _heatmapZoom = {}; // id -> {scale, lastDist, ticking, origW, origH, originX, originY, targetScrollX, targetScrollY}

function enableHeatmapPinchZoom(id) {
    const wrap = document.getElementById(id);
    if (!wrap || wrap.dataset.pinchEnabled) return;
    wrap.dataset.pinchEnabled = 'true';
    if (!_heatmapZoom[id]) _heatmapZoom[id] = { scale: 1, lastDist: null, ticking: false, origW: 0, origH: 0, originX: 0, originY: 0, targetScrollX: 0, targetScrollY: 0 };
    const state = _heatmapZoom[id];

    function getDist(touches) {
        const dx = touches[0].clientX - touches[1].clientX;
        const dy = touches[0].clientY - touches[1].clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }

    // ピンチ中心点をwrapper画面上の相対座標で取得
    function getMidPoint(touches) {
        const rect = wrap.getBoundingClientRect();
        const mx = (touches[0].clientX + touches[1].clientX) / 2;
        const my = (touches[0].clientY + touches[1].clientY) / 2;
        return { x: mx - rect.left, y: my - rect.top };
    }

    function updateZoom() {
        const inner = wrap.querySelector('.heatmap-inner');
        if (!inner) return;
        // 常に左上を基準に拡大することで、端が見えなくなる問題と余白問題を解決
        inner.style.transformOrigin = `0 0`;
        inner.style.transform = `scale(${state.scale})`;
        // スクロール可能領域をスケールに合わせて拡張
        if (!state.origW) {
            state.origW = inner.offsetWidth;
            state.origH = inner.offsetHeight;
        }
        inner.style.marginRight = (state.origW * (state.scale - 1)) + 'px';
        inner.style.marginBottom = (state.origH * (state.scale - 1)) + 'px';

        // margin反映後にスクロール位置を調整
        wrap.scrollLeft = state.targetScrollX;
        wrap.scrollTop = state.targetScrollY;

        state.ticking = false;
    }

    wrap.addEventListener('touchstart', e => {
        if (e.touches.length === 2) {
            state.lastDist = getDist(e.touches);
            const inner = wrap.querySelector('.heatmap-inner');
            if (inner) {
                if (!state.origW || state.origW === 0) {
                    state.origW = inner.offsetWidth;
                    state.origH = inner.offsetHeight;
                }
                const mid = getMidPoint(e.touches);
                // ピンチ中心の、オリジナルの(scale=1)時のinner上の座標を記録
                state.originX = (mid.x + wrap.scrollLeft) / state.scale;
                state.originY = (mid.y + wrap.scrollTop) / state.scale;
            }
        }
    }, { passive: true });

    wrap.addEventListener('touchmove', e => {
        if (e.touches.length === 2) {
            e.preventDefault();
            const dist = getDist(e.touches);
            if (state.lastDist && state.lastDist > 0) {
                const delta = dist / state.lastDist;
                // 最小scale=1（applyHeatmapCellSizesがfit-to-widthを保証）
                state.scale = Math.min(4, Math.max(1, state.scale * delta));

                const mid = getMidPoint(e.touches);
                state.targetScrollX = state.originX * state.scale - mid.x;
                state.targetScrollY = state.originY * state.scale - mid.y;

                if (!state.ticking) {
                    requestAnimationFrame(updateZoom);
                    state.ticking = true;
                }
            }
            state.lastDist = dist;
        }
    }, { passive: false });

    wrap.addEventListener('touchend', e => {
        if (e.touches.length < 2) state.lastDist = null;
    }, { passive: true });
}

function resetHeatmapZoom(id) {
    const wrap = document.getElementById(id);
    if (!wrap) return;
    const state = _heatmapZoom[id];
    if (state) {
        state.scale = 1;
        state.lastDist = null;
        state.origW = 0;
        state.origH = 0;
        state.targetScrollX = 0;
        state.targetScrollY = 0;
    }
    const inner = wrap.querySelector('.heatmap-inner');
    if (inner) {
        inner.style.transform = '';
        inner.style.transformOrigin = '';
        inner.style.marginRight = '';
        inner.style.marginBottom = '';
    }
}


// ==========================================
// MACHINE TAB (台番号別差枚)
// ==========================================

// 除外する機種名
const EXCLUDED_MODELS = ['ｽﾏｰﾄ沖ｽﾛ+ﾆｭｰｷﾝｸﾞﾊﾅﾊﾅV'];

function renderSplitBarChart(splitWrapperId, labelCanvasId, barCanvasId, axisCanvasId, items, opts = {}, chartKey = 'machine') {
    const step = opts.step || 500;
    const initRange = opts.initRange || 4000;
    const rowH = opts.rowH || 22; // 少し広げて視認性を向上
    const fontSize = opts.fontSize || 11;
    const labelRatio = 0.4;

    if (!items.length) return;
    const vals = items.map(i => i.avg);
    const dataMax = vals.reduce((a, b) => Math.max(a, b), 0);
    const dataMin = vals.reduce((a, b) => Math.min(a, b), 0);

    // 0点を中心（センター）にするための軸計算
    const rawMax = Math.max(initRange, Math.ceil(Math.abs(dataMax) / step) * step);
    const rawMin = Math.max(initRange, Math.ceil(Math.abs(dataMin) / step) * step);
    const absMax = Math.max(rawMax, rawMin);
    const axisMax = absMax;
    const axisMin = -absMax;

    const n = items.length;
    // 上部余白を5pxに設定
    const topPad = 5;
    const bottomPad = 10;
    const h = n * rowH + topPad + bottomPad;

    const labelCvs = document.getElementById(labelCanvasId);
    if (!labelCvs) return;
    const labelPane = labelCvs.parentElement;

    const tmpCtx = labelCvs.getContext("2d");
    tmpCtx.font = `bold ${fontSize}px Inter, Noto Sans JP, sans-serif`;
    let maxLW = 80;
    items.forEach(i => { const w = tmpCtx.measureText(i.label).width; if (w > maxLW) maxLW = w; });
    const labelCvsW = Math.ceil(maxLW) + 24;

    const dpr = window.devicePixelRatio || 1;
    labelCvs.width = labelCvsW * dpr;
    labelCvs.height = h * dpr;
    labelCvs.style.width = labelCvsW + "px";
    labelCvs.style.height = h + "px";

    const wrapper = splitWrapperId ? document.getElementById(splitWrapperId) : labelPane.parentElement.parentElement;
    const totalW = wrapper ? (wrapper.clientWidth || 600) : 600;
    const labelPaneW = Math.floor(totalW * labelRatio);
    const barPaneW = totalW - labelPaneW;

    labelPane.style.width = labelPaneW + "px";
    labelPane.style.flexShrink = "0";
    labelPane.style.overflowX = "auto";
    labelPane.style.overflowY = "hidden";
    labelPane.style.height = h + "px";

    const barCvs = document.getElementById(barCanvasId);
    if (!barCvs) return;
    const barPane = barCvs.parentElement;
    barPane.style.overflowX = "auto";
    barPane.style.overflowY = "hidden";
    barPane.style.height = h + "px";

    // Spacer for sticky header
    const spacer = wrapper ? wrapper.querySelector('.split-chart-label-spacer') : null;
    if (spacer) {
        spacer.style.width = labelPaneW + "px";
        spacer.style.height = "35px";
    }
    const axisPane = wrapper ? wrapper.querySelector('.split-chart-axis-pane') : null;
    const axisCvs = axisCanvasId ? document.getElementById(axisCanvasId) : null;
    if (axisPane) axisPane.style.height = "35px";

    const totalRange = axisMax - axisMin;
    const initTotalRange = initRange * 2;
    const scaleFactor = Math.max(1, totalRange / initTotalRange);
    const barCvsW = Math.max(barPaneW, Math.round(barPaneW * scaleFactor));
    barCvs.width = barCvsW;
    barCvs.height = h;
    barCvs.style.width = barCvsW + "px";
    barCvs.style.height = h + "px";

    if (axisCvs) {
        axisCvs.width = barCvsW;
        axisCvs.height = 35;
        axisCvs.style.width = barCvsW + "px";
        axisCvs.style.height = "30px";
    }

    const keyL = chartKey + "-labels", keyB = chartKey, keyA = chartKey + "-axis";
    if (charts[keyL]) charts[keyL].destroy();
    if (charts[keyB]) charts[keyB].destroy();
    if (charts[keyA]) charts[keyA].destroy();

    const gridColorFn = (ctx2) => {
        const v = ctx2.tick ? ctx2.tick.value : (ctx2.value ?? 0);
        const isDk = document.body.classList.contains('dark-theme');
        return (v === 0) ? (isDk ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.3)') : 'rgba(128,128,128,0.12)';
    };

    const commonOpts = {
        indexAxis: 'y', responsive: false, maintainAspectRatio: false,
        animation: false,
        layout: { padding: { top: topPad, bottom: bottomPad, left: 25, right: 25 } },
        plugins: { legend: { display: false }, datalabels: { display: false } }
    };

    const isDark = document.body.classList.contains('dark-theme');
    const labelColor = isDark ? '#e5e7eb' : '#1a1a1a';
    const stripePlugin = {
        id: 'stripePlugin',
        beforeDraw(chart) {
            const { ctx, chartArea, scales: { y } } = chart;
            if (!chartArea || !y || y.ticks.length === 0) return;
            const tickCount = y.ticks.length;
            const rowH2 = (chartArea.bottom - chartArea.top) / tickCount;
            ctx.save();
            ctx.fillStyle = document.body.classList.contains('dark-theme') ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.03)';
            for (let i = 0; i < tickCount; i++) {
                if (i % 2 === 1) {
                    ctx.fillRect(chartArea.left, chartArea.top + i * rowH2, chartArea.right - chartArea.left, rowH2);
                }
            }
            ctx.restore();
        }
    };

    // --- Label canvas setup ---
    if (charts[keyL]) { charts[keyL].destroy(); delete charts[keyL]; }
    // --- Bar chart ---
    if (charts[keyB]) charts[keyB].destroy();

    const syncPlugin = {
        id: 'syncPlugin',
        afterLayout(chart) {
            const { top, bottom } = chart.chartArea;
            if (!top || !bottom) return;
            const actualRowH = (bottom - top) / n;

            const lCtx = labelCvs.getContext('2d');
            lCtx.save();
            lCtx.scale(dpr, dpr);
            lCtx.clearRect(0, 0, labelCvsW, h);
            const stripeColor = isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.03)';
            lCtx.font = `bold ${fontSize}px Inter, "Noto Sans JP", sans-serif`;
            lCtx.textBaseline = 'middle';
            lCtx.textAlign = 'left';

            for (let i = 0; i < n; i++) {
                const y = top + i * actualRowH;
                if (i % 2 === 1) {
                    lCtx.fillStyle = stripeColor;
                    lCtx.fillRect(0, y, labelCvsW, actualRowH);
                }
                lCtx.fillStyle = labelColor;
                lCtx.fillText(items[i].label, 8, y + actualRowH / 2);
            }
            lCtx.restore();
        },
        beforeDraw(chart) {
            const { ctx, chartArea } = chart;
            if (!chartArea) return;
            const actualRowH = (chartArea.bottom - chartArea.top) / n;
            ctx.save();
            const stripeColor = isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.03)';
            for (let i = 0; i < n; i++) {
                if (i % 2 === 1) {
                    ctx.fillStyle = stripeColor;
                    ctx.fillRect(chartArea.left, chartArea.top + i * actualRowH, chartArea.right - chartArea.left, actualRowH);
                }
            }
            ctx.restore();
        }
    };

    // Blue for positive, red for negative
    const posColor = 'rgba(59,130,246,0.85)';
    const negColor = 'rgba(239,68,68,0.8)';

    charts[keyB] = new Chart(barCvs, {
        type: 'bar',
        data: {
            labels: items.map(i => i.label), datasets: [{
                label: '差枚', data: vals,
                backgroundColor: vals.map(v => v > 0 ? posColor : negColor), borderRadius: 2
            }]
        },
        options: {
            ...commonOpts,
            interaction: { mode: 'nearest', axis: 'y', intersect: false },
            plugins: {
                ...commonOpts.plugins,
                tooltip: {
                    enabled: true, animation: false,
                    position: 'nearest',
                    callbacks: { label: (ctx) => `[${items[ctx.dataIndex].num}] ${ctx.raw.toLocaleString()}枚` }
                }
            },
            scales: {
                x: {
                    display: true, min: axisMin, max: axisMax,
                    ticks: { display: !axisCvs, stepSize: step, font: { size: 9 }, color: isDark ? '#9ca3af' : '#6b7280' },
                    grid: { color: gridColorFn }
                },
                y: { display: false, grid: { display: false }, ticks: { autoSkip: false } }
            }
        },
        plugins: [syncPlugin]
    });

    if (axisCvs) {
        charts[keyA] = new Chart(axisCvs, {
            type: 'bar',
            data: { labels: items.map(i => i.label), datasets: [{ data: items.map(() => null) }] },
            options: {
                ...commonOpts,
                layout: { padding: { left: 25, right: 25, top: 0, bottom: 0 } },
                scales: {
                    x: {
                        display: true, position: 'bottom', min: axisMin, max: axisMax,
                        ticks: { stepSize: step, font: { size: 10, weight: 'bold' }, color: isDark ? '#e2e8f0' : '#1e293b' },
                        grid: { display: true, drawOnChartArea: false, drawTicks: true, tickLength: 5, color: isDark ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.4)' }
                    },
                    y: { display: false }
                }
            }
        });

        // Sync horizontal scroll
        barPane.onscroll = () => {
            axisPane.scrollLeft = barPane.scrollLeft;
        };
    }

    // Scroll bar pane so that 0 is horizontally centered
    requestAnimationFrame(() => {
        const zeroRatio = (0 - axisMin) / (axisMax - axisMin);
        const zeroX = zeroRatio * barCvsW;
        barPane.scrollLeft = Math.max(0, zeroX - barPane.clientWidth / 2);
        if (axisPane) axisPane.scrollLeft = barPane.scrollLeft;
    });
}

function renderMachineTab(data) {
    // Build per-machine history to find latest model per machine number
    const machineModels = {};
    data.forEach(row => {
        const num = normalizeNum(row['台番号']), model = row['機種名'], date = row['日付'];
        // 除外機種をスキップ
        if (EXCLUDED_MODELS.includes(model)) return;
        if (!machineModels[num]) machineModels[num] = { latestDate: '', latestModel: '', entries: {} };
        if (date > machineModels[num].latestDate) { machineModels[num].latestDate = date; machineModels[num].latestModel = model; }
        const key = model;
        if (!machineModels[num].entries[key]) machineModels[num].entries[key] = { diff: 0, g: 0, count: 0, latestDate: '' };
        machineModels[num].entries[key].diff += Number(row['最終差枚']) || 0;
        machineModels[num].entries[key].g += Number(row['累計ゲーム']) || 0;
        machineModels[num].entries[key].count += 1;
        if (date > machineModels[num].entries[key].latestDate) machineModels[num].entries[key].latestDate = date;
    });

    const items = [];
    for (const [num, info] of Object.entries(machineModels)) {
        for (const [model, st] of Object.entries(info.entries)) {
            const isLatest = model === info.latestModel;
            const label = isLatest ? `[ ${num} ] ${model}` : `[ ${num} ] (${model})`;
            const avg = st.count > 0 ? st.diff / st.count : 0;
            items.push({ label, avg, isLatest, num });
        }
    }
    items.sort((a, b) => parseInt(a.num) - parseInt(b.num));

    renderSplitBarChart('machine-split-wrapper', 'machine-labels-canvas', 'chart-machine-diff', 'machine-axis-canvas', items,
        { step: 500, initRange: 4000, rowH: 18, fontSize: 11, labelWidthMax: 260 });
}

// ==========================================
// ANALYSIS SECTION
// ==========================================
function drawDotChart(id, labels, vals, label, extraOpts = {}) {
    const ctx = document.getElementById(id); if (!ctx) return;
    const h = Math.max(150, labels.length * 16 + 40);
    ctx.style.height = `${h}px`; ctx.parentElement.style.height = `${h}px`;
    ctx.parentElement.style.minWidth = '0px';

    if (charts[id]) charts[id].destroy();
    const maxDev = vals.reduce((max, v) => Math.max(max, Math.abs(v - 100)), 2);

    const scales = {
        x: { grid: { color: (ctx) => { if (ctx.tick.value === 100) return 'rgba(255,255,255,0.3)'; return 'rgba(128,128,128,0.2)'; } }, min: 100 - maxDev, max: 100 + maxDev, title: { display: true, text: label } },
        y: { grid: { display: false }, ticks: { font: { size: 12 }, autoSkip: false } }
    };

    if (extraOpts.dynamicWidth) {
        scales.x.min = 90;
        scales.x.max = 110;
    }

    charts[id] = new Chart(ctx, {
        type: 'line',
        data: { labels, datasets: [{ label, data: vals, backgroundColor: vals.map(v => v >= 100 ? 'rgba(59,130,246,0.9)' : 'rgba(239,68,68,0.9)'), borderColor: 'transparent', pointRadius: 6, pointHoverRadius: 8, showLine: false }] },
        options: {
            indexAxis: 'y', responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false }, datalabels: { display: false } },
            scales: scales
        }
    });
    if (extraOpts.dynamicWidth) enableChartPan(id, true);
}

function drawBar(id, labels, vals, label, extraOpts = {}) {
    const ctx = document.getElementById(id); if (!ctx) return;
    const h = Math.max(150, labels.length * 16 + 40);
    ctx.style.height = `${h}px`;
    ctx.parentElement.style.height = `${h}px`;
    ctx.parentElement.style.minWidth = '0px';

    if (charts[id]) charts[id].destroy();

    const scales = { x: { grid: { color: 'rgba(128,128,128,0.2)' } }, y: { grid: { display: false }, ticks: { font: { size: 12 }, autoSkip: false } } };
    if (extraOpts.dynamicWidth) {
        scales.x.min = -2000;
        scales.x.max = 2000;
    }
    if (extraOpts.optExtras && extraOpts.optExtras.scales) {
        Object.assign(scales.x, extraOpts.optExtras.scales.x || {});
        Object.assign(scales.y, extraOpts.optExtras.scales.y || {});
    }

    charts[id] = new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets: [{ label, data: vals, backgroundColor: vals.map(v => v > 0 ? 'rgba(59,130,246,0.7)' : 'rgba(239,68,68,0.7)'), borderRadius: 4, ...(extraOpts.datasetExtras || {}) }] },
        options: {
            indexAxis: 'y', responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false }, datalabels: { display: false } },
            scales: scales,
            ...(extraOpts.optExtras || {})
        }
    });
    if (extraOpts.dynamicWidth) enableChartPan(id, false);
}

function computeCumulDiffByDate(allRawData) {
    // Per machine, compute monthly cumulative diff up to (but not including) each date
    // Returns map: date -> { prevMonthCumul: X, diff: Y, g: Z, count: N }
    const byMachine = {};
    allRawData.forEach(row => {
        const num = normalizeNum(row['台番号']);
        if (!byMachine[num]) byMachine[num] = [];
        byMachine[num].push({ date: row['日付'], diff: Number(row['最終差枚']) || 0, g: Number(row['累計ゲーム']) || 0 });
    });

    // For each date, gather how many machines' prev cumul we know
    // We'll aggregate per-day: median/mean of prev cumulative diff
    const dailyCumul = {};// date -> [{prevCumul, diff, g}]

    for (const [num, hist] of Object.entries(byMachine)) {
        hist.sort((a, b) => a.date.localeCompare(b.date));
        let monthCumul = {};// month -> cumulative up to prev day
        let prevDate = null, prevMonth = null, runCumul = 0;

        hist.forEach(entry => {
            const month = entry.date.substring(0, 7);
            if (month !== prevMonth) { runCumul = 0; prevMonth = month; }// reset on new month
            // prevCumul = cumulative BEFORE this date's diff is added
            if (!dailyCumul[entry.date]) dailyCumul[entry.date] = [];
            dailyCumul[entry.date].push({ prevCumul: runCumul, diff: entry.diff, g: entry.g });
            runCumul += entry.diff;
        });
    }
    return dailyCumul;
}

function getBucket(v, step, min, max) {
    if (v <= min) return `${min}以下`;
    if (v >= max) return `${max}以上`;
    const b = Math.floor((v - min) / step) * step + min;
    return `${b}〜${b + step}`;
}

function renderAnalysis(data) {
    const digits = Array(10).fill().map(() => ({ diff: 0, g: 0, c: 0 }));
    const ndays = Array(10).fill().map(() => ({ diff: 0, g: 0, c: 0 }));
    const wdNames = ['日', '月', '火', '水', '木', '金', '土'];
    const wdays = Array(7).fill().map(() => ({ diff: 0, g: 0, c: 0 }));
    const models = {};
    const positions = { '角': { diff: 0, c: 0 }, '角2': { diff: 0, c: 0 }, '角3': { diff: 0, c: 0 }, 'その他': { diff: 0, c: 0 } };
    const mHistory = {};
    const dayOfMonth = Array(32).fill().map(() => ({ diff: 0, g: 0, c: 0 }));// index=day 1-31

    data.forEach(row => {
        const d = row['日付'], diff = Number(row['最終差枚']) || 0, g = Number(row['累計ゲーム']) || 0;
        const num = normalizeNum(row['台番号']), model = row['機種名'];
        const digit = parseInt(num.slice(-1));
        if (!isNaN(digit)) { digits[digit].diff += diff; digits[digit].g += g; digits[digit].c++; }
        const dayStr = d.split('-')[2], nday = parseInt(dayStr.slice(-1));
        ndays[nday].diff += diff; ndays[nday].g += g; ndays[nday].c++;
        const wd = new Date(d).getDay(); wdays[wd].diff += diff; wdays[wd].g += g; wdays[wd].c++;
        if (!models[model]) models[model] = { diff: 0, g: 0, c: 0 };
        models[model].diff += diff; models[model].g += g; models[model].c++;
        const loc = layoutLookup[num];
        if (loc) {
            const pk = loc.pos === 0 ? '角' : loc.pos === 1 ? '角2' : loc.pos === 2 ? '角3' : 'その他';
            positions[pk].diff += diff; positions[pk].c++;
        }
        if (!mHistory[num]) mHistory[num] = [];
        mHistory[num].push({ ...row, diff, g });
        // Day of month
        const dom = parseInt(d.split('-')[2], 10);
        if (dom >= 1 && dom <= 31) { dayOfMonth[dom].diff += diff; dayOfMonth[dom].g += g; dayOfMonth[dom].c++; }
    });

    const buildCD = obj => { let labels = [], dDiff = [], dPayout = []; for (const [k, v] of Object.entries(obj)) { if (v.c === 0) continue; labels.push(k); dDiff.push(v.diff / v.c); dPayout.push(payout(v.diff, v.g)); } return { labels, dDiff, dPayout }; };

    drawBar('chart-digit', buildCD(digits).labels, buildCD(digits).dDiff, '平均差枚');
    drawBar('chart-nday', buildCD(ndays).labels, buildCD(ndays).dDiff, '平均差枚');
    const wdOrder = [1, 2, 3, 4, 5, 6, 0];
    const ordW = wdOrder.map(i => ({ ...wdays[i], name: wdNames[i] }));
    drawBar('chart-weekday', ordW.filter(w => w.c > 0).map(w => w.name), ordW.filter(w => w.c > 0).map(w => w.diff / w.c), '平均差枚');
    drawBar('chart-position', buildCD(positions).labels, buildCD(positions).dDiff, '平均差枚');
    drawBar('chart-model', buildCD(models).labels, buildCD(models).dDiff, '平均差枚', { dynamicWidth: true });

    // Day of month (1-31) bar charts
    const domLabels = [], domDiff = [], domPayout = [];
    for (let i = 1; i <= 31; i++) { if (dayOfMonth[i].c > 0) { domLabels.push(`${i}日`); domDiff.push(dayOfMonth[i].diff / dayOfMonth[i].c); domPayout.push(payout(dayOfMonth[i].diff, dayOfMonth[i].g)); } }
    drawBar('chart-dayofmonth-diff', domLabels, domDiff, '平均差枚');
    drawDotChart('chart-dayofmonth-payout', domLabels, domPayout, '出率(%)');

    // Consecutive & Neighbor analysis
    const consNeg = Array(7).fill().map(() => ({ diff: 0, c: 0 }));
    const consPos = Array(7).fill().map(() => ({ diff: 0, c: 0 }));
    const neiDiffBuckets = { '<-4000': { diff: 0, c: 0 }, '-4000~-2001': { diff: 0, c: 0 }, '-2000~-1': { diff: 0, c: 0 }, '0~2000': { diff: 0, c: 0 }, '2001~4000': { diff: 0, c: 0 }, '>4000': { diff: 0, c: 0 } };
    const neiSetBuckets = { 1: { diff: 0, c: 0 }, 2: { diff: 0, c: 0 }, 3: { diff: 0, c: 0 }, 4: { diff: 0, c: 0 }, 5: { diff: 0, c: 0 }, 6: { diff: 0, c: 0 } };
    const bothDiffBuckets = { '<-4000': { diff: 0, c: 0 }, '-4000~-2001': { diff: 0, c: 0 }, '-2000~-1': { diff: 0, c: 0 }, '0~2000': { diff: 0, c: 0 }, '2001~4000': { diff: 0, c: 0 }, '>4000': { diff: 0, c: 0 } };
    const bothSetBuckets = { '456': { diff: 0, c: 0 }, 'Others': { diff: 0, c: 0 } };
    const gBucket = d => { if (d <= -4001) return '<-4000'; if (d <= -2001) return '-4000~-2001'; if (d < 0) return '-2000~-1'; if (d <= 2000) return '0~2000'; if (d <= 4000) return '2001~4000'; return '>4000'; };

    const matrix = {};
    for (const [m, hist] of Object.entries(mHistory)) {
        hist.forEach(r => { if (!matrix[r['日付']]) matrix[r['日付']] = {}; matrix[r['日付']][m] = r; });
    }
    for (const [m, hist] of Object.entries(mHistory)) {
        hist.sort((a, b) => a['日付'].localeCompare(b['日付']));
        let negS = 0, posS = 0;
        for (const row of hist) {
            const diff = row.diff, g = Number(row['累計ゲーム']) || 0;
            if (g === 0) continue;
            consNeg[Math.min(negS, 6)].diff += diff; consNeg[Math.min(negS, 6)].c++;
            consPos[Math.min(posS, 6)].diff += diff; consPos[Math.min(posS, 6)].c++;
            if (diff < 0) { negS++; posS = 0; } else if (diff > 0) { posS++; negS = 0; } else { negS = 0; posS = 0; }
            const loc = layoutLookup[m];
            if (loc) {
                const dmap = matrix[row['日付']];
                let lM = null, rM = null;
                layoutData[loc.row_idx].forEach(c => { if (c === '') return; const nc = normalizeNum(c); const cl = layoutLookup[nc]; if (cl && cl.col_idx === loc.col_idx - 1) lM = nc; if (cl && cl.col_idx === loc.col_idx + 1) rM = nc; });
                const rL = lM ? dmap[lM] : null, rR = rM ? dmap[rM] : null;
                const cSet = r => { if (!r) return null; const e = estimateSetting(r['機種名'], r['累計ゲーム'] || 0, r['BIG'] || 0, r['REG'] || 0); return e ? e.setting : null; };
                const mySet = cSet(row);
                [rL, rR].forEach(nR => {
                    if (!nR) return;
                    neiDiffBuckets[gBucket(nR.diff)].diff += diff; neiDiffBuckets[gBucket(nR.diff)].c++;
                    const nSet = cSet(nR); if (nSet && mySet) { neiSetBuckets[nSet].diff += mySet; neiSetBuckets[nSet].c++; }
                });
                if (rL && rR) {
                    const lb = gBucket(rL.diff), rb = gBucket(rR.diff); if (lb === rb) { bothDiffBuckets[lb].diff += diff; bothDiffBuckets[lb].c++; }
                    const ls = cSet(rL), rs = cSet(rR); if (mySet && ls && rs) { if (ls >= 4 && rs >= 4) { bothSetBuckets['456'].diff += mySet; bothSetBuckets['456'].c++; } else { bothSetBuckets['Others'].diff += mySet; bothSetBuckets['Others'].c++; } }
                }
            }
        }
    }
    drawBar('chart-cons-neg', ['0日', '1日', '2日', '3日', '4日', '5日', '6日以上'], consNeg.map(v => v.c ? v.diff / v.c : 0), '翌日平均差枚');
    drawBar('chart-cons-pos', ['0日', '1日', '2日', '3日', '4日', '5日', '6日以上'], consPos.map(v => v.c ? v.diff / v.c : 0), '翌日平均差枚');
    drawBar('chart-neighbor-diff', buildCD(neiDiffBuckets).labels, buildCD(neiDiffBuckets).dDiff, '平均差枚');
    drawBar('chart-neighbor-setting', buildCD(neiSetBuckets).labels, buildCD(neiSetBuckets).dDiff, '自台平均設定');
    drawBar('chart-both-neighbor-diff', buildCD(bothDiffBuckets).labels, buildCD(bothDiffBuckets).dDiff, '平均差枚');
    drawBar('chart-both-neighbor-setting', buildCD(bothSetBuckets).labels, buildCD(bothSetBuckets).dDiff, '自台平均設定');

    // Monthly cumulative analysis
    renderCumulAnalysis(data);
}

// ==========================================
// CUMULATIVE MONTHLY ANALYSIS
// ==========================================
function renderCumulAnalysis(data) {
    // 1. Group data by date to get daily total diff and total g
    const daily = {};
    data.forEach(row => {
        const date = row['日付'];
        const diff = Number(row['最終差枚']) || 0;
        const g = Number(row['累計ゲーム']) || 0;
        if (!daily[date]) daily[date] = { date, diff: 0, g: 0, count: 0 };
        daily[date].diff += diff;
        daily[date].g += g;
        daily[date].count += 1;
    });

    const dailyDates = Object.keys(daily).sort();

    // 2. Compute cumulative up to PREVIOUS day for each date
    const cumulPoints = [];
    let prevMonth = null;
    let runCumul = 0;

    dailyDates.forEach(date => {
        const month = date.substring(0, 7);
        if (month !== prevMonth) {
            runCumul = 0; // reset on new month
            prevMonth = month;
        }

        const dayNum = parseInt(date.split('-')[2], 10);
        const lastDayOfMonth = new Date(parseInt(month.split('-')[0]), parseInt(month.split('-')[1]), 0).getDate();
        const isFirstWeek = dayNum <= 7;
        const isLastWeek = dayNum >= lastDayOfMonth - 6;

        cumulPoints.push({
            date: date,
            prevCumul: runCumul,
            diff: daily[date].diff,
            g: daily[date].g,
            isFirstWeek,
            isLastWeek,
            dayNum
        });

        // Add this day's diff for the NEXT day's prevCumul
        runCumul += daily[date].diff;
    });

    // Apply cumul filter
    let pts = cumulPoints;
    if (currentCumulFilter === 'first_week') pts = pts.filter(p => p.isFirstWeek);
    else if (currentCumulFilter === 'last_week') pts = pts.filter(p => p.isLastWeek);

    // (棒グラフ削除済み — 散布図のみ残す)

    // Scatter plot: prevCumul(x) vs diff(y) with regression line
    const scatterData = pts.map(p => ({ x: p.prevCumul, y: p.diff, date: p.date }));
    // Linear regression
    const n = pts.length;
    if (n > 1) {
        const sumX = pts.reduce((a, p) => a + p.prevCumul, 0), sumY = pts.reduce((a, p) => a + p.diff, 0);
        const sumXY = pts.reduce((a, p) => a + p.prevCumul * p.diff, 0), sumX2 = pts.reduce((a, p) => a + p.prevCumul ** 2, 0);
        const denominator = (n * sumX2 - sumX ** 2);
        const slope = denominator === 0 ? 0 : (n * sumXY - sumX * sumY) / denominator;
        const intercept = (sumY - slope * sumX) / n;
        const meanY = sumY / n;
        const ssRes = pts.reduce((a, p) => a + (p.diff - (slope * p.prevCumul + intercept)) ** 2, 0);
        const ssTot = pts.reduce((a, p) => a + (p.diff - meanY) ** 2, 0);
        const r2 = ssTot > 0 ? 1 - ssRes / ssTot : 0;
        const r = Math.sign(slope) * Math.sqrt(Math.abs(r2));
        const xVals = pts.map(p => p.prevCumul);
        const xMin = xVals.reduce((a, b) => Math.min(a, b), xVals[0] || 0);
        const xMax = xVals.reduce((a, b) => Math.max(a, b), xVals[0] || 0);
        const regLine = [{ x: xMin, y: slope * xMin + intercept }, { x: xMax, y: slope * xMax + intercept }];

        const sCtx = document.getElementById('chart-cumul-scatter');
        if (charts['cumul-scatter']) charts['cumul-scatter'].destroy();
        charts['cumul-scatter'] = new Chart(sCtx, {
            data: {
                datasets: [
                    { type: 'scatter', label: '各日', data: scatterData, backgroundColor: 'rgba(99,179,237,0.8)', pointRadius: 5 },
                    { type: 'line', label: `回帰直線 (r=${r.toFixed(3)}, slope=${slope.toFixed(4)})`, data: regLine, borderColor: 'rgba(248,113,113,0.9)', backgroundColor: 'transparent', pointRadius: 0, borderWidth: 2 }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: {
                    legend: { display: true, labels: { font: { size: 13 }, color: '#f1f5f9' } }, datalabels: { display: false },
                    tooltip: { callbacks: { label: ctx => ctx.datasetIndex === 0 ? `${ctx.raw.date} | 累積差枚:${ctx.parsed.x.toLocaleString()} / 当日差枚:${ctx.parsed.y.toLocaleString()}` : ctx.dataset.label } }
                },
                scales: {
                    x: { title: { display: true, text: '前日までの月累積差枚', font: { size: 13 } }, grid: { color: 'rgba(128,128,128,0.2)' } },
                    y: { title: { display: true, text: '当日差枚', font: { size: 13 } }, grid: { color: 'rgba(128,128,128,0.2)' } }
                }
            }
        });
    }
    renderGameCountAnalysis();
}

// ==========================================
// DATE DETAIL MODAL
// ==========================================
function renderDateDetail(date) {
    const body = document.getElementById('modal-body'); body.innerHTML = '';
    const dayData = rawData.filter(r => r['日付'] === date);

    // Compute consecutive streaks per machine UP TO this date
    const streakMap = {};
    const allDates = [...new Set(rawData.map(r => r['日付']))].sort();
    const dateIdx = allDates.indexOf(date);
    rawData.forEach(row => {
        const num = normalizeNum(row['台番号']);
        if (!streakMap[num]) streakMap[num] = { neg: 0, pos: 0 };
    });
    // Build per-machine date-sorted history up to (not including) target date
    const mHist = {};
    rawData.filter(r => r['日付'] < date).forEach(row => {
        const num = normalizeNum(row['台番号']);
        if (!mHist[num]) mHist[num] = [];
        mHist[num].push({ date: row['日付'], diff: Number(row['最終差枚']) || 0 });
    });
    for (const [num, hist] of Object.entries(mHist)) {
        hist.sort((a, b) => a.date.localeCompare(b.date));
        let neg = 0, pos = 0;
        hist.forEach(e => { if (e.diff < 0) { neg++; pos = 0; } else if (e.diff > 0) { pos++; neg = 0; } else { neg = 0; pos = 0; } });
        streakMap[num] = { neg, pos };
    }

    // ---- Section: Heatmaps ----
    const hmSec = document.createElement('div'); hmSec.className = 'modal-section';
    hmSec.innerHTML = `<h3>差枚・設定ヒートマップ (${date})</h3>`;
    const ms = {};
    dayData.forEach(row => {
        const num = normalizeNum(row['台番号']);
        if (!ms[num]) ms[num] = { diff: 0, count: 0, big: 0, reg: 0, g: 0, model: row['機種名'] };
        ms[num].diff += Number(row['最終差枚']) || 0; ms[num].big += Number(row['BIG']) || 0;
        ms[num].reg += Number(row['REG']) || 0; ms[num].g += Number(row['累計ゲーム']) || 0; ms[num].count += 1;
    });

    // Diff heatmap for this date
    const diffWrapId = 'modal-diff-hm', setWrapId = 'modal-set-hm', streakWrapId = 'modal-streak-hm', islandWrapId = 'modal-island-hm';
    hmSec.innerHTML += `
        <div style="margin-bottom:0.5rem"><strong>差枚ヒートマップ</strong></div>
        <div class="heatmap-legend" style="font-size:0.85rem;gap:0.5rem;margin-bottom:0.5rem" id="modal-diff-legend"></div>
        <div class="heatmap-wrapper" id="${diffWrapId}" style="margin-bottom:1rem"></div>
        <div style="margin-bottom:0.5rem"><strong>推定設定ヒートマップ</strong></div>
        <div class="heatmap-legend" style="font-size:0.85rem;gap:0.5rem;margin-bottom:0.5rem">
            <div class="legend-item"><span class="color-box" style="background:rgba(60,20,180,0.8)"></span>設定1</div>
            <div class="legend-item"><span class="color-box" style="background:rgba(30,100,230,0.8)"></span>設定2</div>
            <div class="legend-item"><span class="color-box" style="background:rgba(0,190,255,0.8)"></span>設定3</div>
            <div class="legend-item"><span class="color-box" style="background:rgba(255,220,0,0.8)"></span>設定4</div>
            <div class="legend-item"><span class="color-box" style="background:rgba(255,130,0,0.8)"></span>設定5</div>
            <div class="legend-item"><span class="color-box" style="background:rgba(230,40,40,0.8)"></span>設定6</div>
        </div>
        <div class="heatmap-wrapper" id="${setWrapId}" style="margin-bottom:1rem"></div>
        <div style="margin-bottom:0.5rem"><strong>島平均差枚ヒートマップ</strong></div>
        <div class="heatmap-legend" style="font-size:0.85rem;gap:0.5rem;margin-bottom:0.5rem" id="modal-island-legend"></div>
        <div class="heatmap-wrapper" id="${islandWrapId}" style="margin-bottom:1rem"></div>
        <div style="margin-bottom:0.5rem"><strong>連続凹み・凸日数ヒートマップ</strong>
          <span style="font-size:0.8rem;color:var(--text-muted);margin-left:0.5rem">（青=凹み継続、赤=凸継続）</span>
        </div>
        <div class="heatmap-legend" style="font-size:0.85rem;gap:0.5rem;margin-bottom:0.5rem">
          <div class="legend-item"><span class="color-box" style="background:rgba(0,190,255,0.5)"></span>凹み1日</div>
          <div class="legend-item"><span class="color-box" style="background:rgba(30,100,230,0.7)"></span>凹み2日</div>
          <div class="legend-item"><span class="color-box" style="background:rgba(60,20,180,0.85)"></span>凹み3日以上</div>
          <div class="legend-item"><span class="color-box" style="background:rgba(255,220,0,0.5)"></span>凸1日</div>
          <div class="legend-item"><span class="color-box" style="background:rgba(255,130,0,0.7)"></span>凸2日</div>
          <div class="legend-item"><span class="color-box" style="background:rgba(230,40,40,0.85)"></span>凸3日以上</div>
        </div>
        <div class="heatmap-wrapper" id="${streakWrapId}"></div>`;
    body.appendChild(hmSec);

    // Build heatmaps after injecting HTML
    setTimeout(() => {
        // Dynamic thresholds from today's data
        const dayDiffs = Object.values(ms).map(s => Math.round(s.diff / s.count));
        const dayPos = dayDiffs.filter(v => v > 0), dayNeg = dayDiffs.filter(v => v < 0);
        const localT = {
            pos1: dayPos.length ? percentile(dayPos, 33) : 1000,
            pos2: dayPos.length ? percentile(dayPos, 66) : 2000,
            neg1: dayNeg.length ? percentile(dayNeg, 33) : -2000,
            neg2: dayNeg.length ? percentile(dayNeg, 66) : -1000
        };
        const lEl = document.getElementById('modal-diff-legend');
        if (lEl) lEl.innerHTML = generateLegendHtml(localT);
        // Diff heatmap
        buildModalHeatmap(diffWrapId, (el, num) => {
            if (!ms[num]) { el.style.background = 'transparent'; el.style.border = '1px solid rgba(128,128,128,0.2)'; return; }
            const st = ms[num], avg = Math.round(st.diff / st.count);
            el.style.backgroundColor = getHeatmapColor(avg, localT);
            const t = `<div class="tooltip-title">台番号: ${num}</div><div class="tooltip-body"><div>機種: ${st.model}</div><div>位置: ${getPosLabel(num)}</div><div>差枚: ${formatVal(avg)}</div></div>`;
            el.addEventListener('mouseenter', () => { tooltip.innerHTML = t; tooltip.classList.add('visible'); });
            el.addEventListener('mouseleave', () => tooltip.classList.remove('visible'));
        });
        // Setting heatmap
        buildModalHeatmap(setWrapId, (el, num) => {
            if (!ms[num]) { el.style.background = 'transparent'; el.style.border = '1px solid rgba(128,128,128,0.2)'; return; }
            const st = ms[num]; let sText = '';
            if (MACHINE_GROUPS.hanahana.includes(st.model) || MACHINE_GROUPS.juggler.includes(st.model)) {
                const est = estimateSetting(st.model, st.g, st.big, st.reg);
                if (est) { el.style.backgroundColor = SETTING_COLORS[est.setting]; sText = `推定設定:${est.setting}(${(est.prob * 100).toFixed(1)}%)`; }
            }
            const t = `<div class="tooltip-title">台番号: ${num}</div><div class="tooltip-body"><div>機種: ${st.model}</div><div>位置: ${getPosLabel(num)}</div>${sText ? `<div>${sText}</div>` : ''}</div>`;
            el.addEventListener('mouseenter', () => { tooltip.innerHTML = t; tooltip.classList.add('visible'); });
            el.addEventListener('mouseleave', () => tooltip.classList.remove('visible'));
        });
        // Island avg heatmap
        const iSt2 = {};
        layoutData.forEach(row => row.forEach(cell => {
            const num = normalizeNum(cell);
            if (cell !== '' && ms[num] && layoutLookup[num]) {
                const iId = layoutLookup[num].islandId;
                if (!iSt2[iId]) iSt2[iId] = { total: 0, count: 0 };
                iSt2[iId].total += Math.round(ms[num].diff / ms[num].count); iSt2[iId].count++;
            }
        }));
        const iAvg2 = {};
        for (const [k, v] of Object.entries(iSt2)) iAvg2[k] = v.count > 0 ? Math.round(v.total / v.count) : 0;
        const iVals = Object.values(iAvg2).filter(v => v !== 0);
        const iP = iVals.filter(v => v > 0), iN = iVals.filter(v => v < 0);
        const iT2 = { pos1: iP.length ? percentile(iP, 33) : 200, pos2: iP.length ? percentile(iP, 66) : 500, neg1: iN.length ? percentile(iN, 33) : -500, neg2: iN.length ? percentile(iN, 66) : -200 };
        const ilEl = document.getElementById('modal-island-legend');
        if (ilEl) ilEl.innerHTML = generateLegendHtml(iT2);
        buildModalHeatmap(islandWrapId, (el, num) => {
            const iId = layoutLookup[num] ? layoutLookup[num].islandId : null;
            const ia = iId ? (iAvg2[iId] || 0) : 0;
            el.style.backgroundColor = getHeatmapColor(ia, iT2);
            const t = `<div class="tooltip-title">${iId || num}</div><div class="tooltip-body"><div>島平均差枚: ${formatVal(ia)}</div></div>`;
            el.addEventListener('mouseenter', () => { tooltip.innerHTML = t; tooltip.classList.add('visible'); });
            el.addEventListener('mouseleave', () => tooltip.classList.remove('visible'));
        });
        // Streak heatmap
        buildModalHeatmap(streakWrapId, (el, num) => {
            const sk = streakMap[num] || { neg: 0, pos: 0 };
            el.classList.add('streak-cell'); let streakText = '';
            if (sk.neg > 0) { const lvl = sk.neg >= 3 ? 3 : sk.neg; el.style.backgroundColor = ['', 'rgba(0,190,255,0.5)', 'rgba(30,100,230,0.7)', 'rgba(60,20,180,0.85)'][lvl]; streakText = `凹${sk.neg}日`; }
            else if (sk.pos > 0) { const lvl = sk.pos >= 3 ? 3 : sk.pos; el.style.backgroundColor = ['', 'rgba(255,220,0,0.5)', 'rgba(255,130,0,0.7)', 'rgba(230,40,40,0.85)'][lvl]; streakText = `凸${sk.pos}日`; }
            if (streakText) {
                el.textContent = `${num}\n${streakText}`;
                const m = ms[num] ? ms[num].model : '不明';
                const t = `<div class="tooltip-title">台番号: ${num}</div><div class="tooltip-body"><div>機種: ${m}</div><div>位置: ${getPosLabel(num)}</div><div>継続: ${streakText}</div></div>`;
                el.addEventListener('mouseenter', () => { tooltip.innerHTML = t; tooltip.classList.add('visible'); });
                el.addEventListener('mouseleave', () => tooltip.classList.remove('visible'));
            }
        });
    }, 50);

    // ---- Section: Machine summary ----
    const mSec = document.createElement('div'); mSec.className = 'modal-section';
    mSec.innerHTML = '<h3>機種別データ（平均差枚降順）</h3>';
    const modelStats = {};
    dayData.forEach(row => {
        const m = row['機種名'], diff = Number(row['最終差枚']) || 0, g = Number(row['累計ゲーム']) || 0;
        if (!modelStats[m]) modelStats[m] = { diff: 0, g: 0, c: 0, win: 0 };
        modelStats[m].diff += diff; modelStats[m].g += g; modelStats[m].c++;
        if (diff > 0) modelStats[m].win++;
    });
    let mHtml = '<div class="table-container"><table class="modal-compact-table"><thead><tr><th>機種名</th><th>台数</th><th>平均差枚</th><th>平均G数</th><th>勝率</th></tr></thead><tbody>';
    Object.entries(modelStats).sort((a, b) => b[1].diff / b[1].c - a[1].diff / a[1].c).forEach(([m, st]) => {
        const avg = Math.round(st.diff / st.c), avgG = Math.round(st.g / st.c);
        mHtml += `<tr><td style="text-align:left">${m}</td><td>${st.c}</td><td>${formatVal(avg)}</td><td>${avgG.toLocaleString()}</td><td>${(st.win / st.c * 100).toFixed(1)}%</td></tr>`;
    });
    mHtml += '</tbody></table></div>';
    mSec.innerHTML += mHtml; body.appendChild(mSec);

    // ---- Section: Ending digit summary ----
    const dSec = document.createElement('div'); dSec.className = 'modal-section';
    dSec.innerHTML = '<h3>末尾別データ</h3>';
    const digitStats = Array(10).fill().map(() => ({ diff: 0, g: 0, c: 0, win: 0 }));
    dayData.forEach(row => {
        const num = normalizeNum(row['台番号']), d = parseInt(num.slice(-1));
        if (isNaN(d)) return;
        const diff = Number(row['最終差枚']) || 0, g = Number(row['累計ゲーム']) || 0;
        digitStats[d].diff += diff; digitStats[d].g += g; digitStats[d].c++; if (diff > 0) digitStats[d].win++;
    });
    let dHtml = '<div class="table-container"><table class="modal-compact-table"><thead><tr><th>末尾</th><th>台数</th><th>平均差枚</th><th>平均G数</th><th>出率</th><th>勝率</th></tr></thead><tbody>';
    digitStats.forEach((st, i) => {
        if (st.c === 0) return;
        const avg = Math.round(st.diff / st.c), avgG = Math.round(st.g / st.c);
        dHtml += `<tr><td>${i}</td><td>${st.c}</td><td>${formatVal(avg)}</td><td>${avgG.toLocaleString()}</td><td>${formatPct(payout(st.diff, st.g))}</td><td>${(st.win / st.c * 100).toFixed(1)}%</td></tr>`;
    });
    dHtml += '</tbody></table></div>';
    dSec.innerHTML += dHtml; body.appendChild(dSec);

    // ---- Section: Per-machine bar chart (split: labels fixed, bars scroll) ----
    const cSec = document.createElement('div'); cSec.className = 'modal-section';
    cSec.innerHTML = '<h3>台番号別 差枚棒グラフ</h3>';
    const splitW = document.createElement('div'); splitW.className = 'split-chart-wrapper';
    splitW.innerHTML = `
        <div class="split-chart-body">
            <div class="split-chart-labels">
                <canvas id="modal-machine-labels"></canvas>
            </div>
            <div class="split-chart-bars">
                <canvas id="modal-machine-chart"></canvas>
            </div>
        </div>
        <div class="split-chart-footer">
            <div class="split-chart-label-spacer"></div>
            <div class="split-chart-axis-pane">
                <canvas id="modal-machine-axis"></canvas>
            </div>
        </div>
    `;
    cSec.appendChild(splitW); body.appendChild(cSec);

    setTimeout(() => {
        const items = [];
        dayData.forEach(row => {
            const num = normalizeNum(row['台番号']), diff = Number(row['最終差枚']) || 0;
            items.push({ label: `[ ${num} ] ${row['機種名']}`, avg: diff, num });
        });
        items.sort((a, b) => parseInt(a.num) - parseInt(b.num));
        if (charts['modal-machine']) charts['modal-machine'].destroy();
        if (charts['modal-machine-labels']) charts['modal-machine-labels'].destroy();
        if (charts['modal-machine-axis']) charts['modal-machine-axis'].destroy();
        renderSplitBarChart('', 'modal-machine-labels', 'modal-machine-chart', 'modal-machine-axis', items,
            { step: 2000, initRange: 4000, rowH: 20, fontSize: 11, labelWidthMax: 280 });
    }, 100);
}

function buildModalHeatmap(wrapId, cellBuilder) {
    const wrap = document.getElementById(wrapId); if (!wrap) return; wrap.innerHTML = '';
    const inner = document.createElement('div');
    inner.className = 'heatmap-inner';
    layoutData.forEach(row => {
        const rowEl = document.createElement('div'); rowEl.className = 'heatmap-row';
        row.forEach(cell => {
            const isEmpty = cell === '';
            const el = document.createElement('div'); el.className = `heatmap-cell${isEmpty ? ' empty' : ''}`;
            if (!isEmpty) { el.textContent = cell; cellBuilder(el, normalizeNum(cell)); }
            rowEl.appendChild(el);
        });
        inner.appendChild(rowEl);
    });
    wrap.appendChild(inner);
    // セルサイズをモバイルに合わせて自動調整してからピンチズーム有効化
    requestAnimationFrame(() => {
        applyHeatmapCellSizes();
        // pinchEnabledをリセットして再初期化可能にする
        delete wrap.dataset.pinchEnabled;
        if (_heatmapZoom[wrapId]) {
            _heatmapZoom[wrapId].scale = 1;
            _heatmapZoom[wrapId].origW = 0;
            _heatmapZoom[wrapId].origH = 0;
        }
        enableHeatmapPinchZoom(wrapId);
    });
}

// ==========================================
// TARGET SUPPORT TOOL
// ==========================================

/**
 * Compute consecutive neg/pos streaks for every machine AS OF the latest date in rawData.
 * This intentionally ignores period/tab filters.
 */
function computeLatestStreaks() {
    const streaks = {};// num -> {neg, pos}
    const byMachine = {};
    rawData.forEach(row => {
        const num = normalizeNum(row['台番号']);
        if (!byMachine[num]) byMachine[num] = [];
        byMachine[num].push({ date: row['日付'], diff: Number(row['最終差枚']) || 0 });
    });
    for (const [num, hist] of Object.entries(byMachine)) {
        hist.sort((a, b) => a.date.localeCompare(b.date));
        let neg = 0, pos = 0;
        hist.forEach(e => {
            if (e.diff < 0) { neg++; pos = 0; }
            else if (e.diff > 0) { pos++; neg = 0; }
            else { neg = 0; pos = 0; }
        });
        streaks[num] = { neg, pos };
    }
    return streaks;
}

/**
 * Get the latest date record per machine from rawData (for hover info).
 */
function getLatestRecords() {
    const latest = {};// num -> row
    rawData.forEach(row => {
        const num = normalizeNum(row['台番号']);
        if (!latest[num] || row['日付'] > latest[num]['日付']) latest[num] = row;
    });
    return latest;
}

/**
 * Compute island avg diff from filteredData.
 */
function computeIslandAvgFromFiltered(filteredData) {
    const islandTotal = {}, islandCount = {};
    const machineAvg = computeMachineAvgFromFiltered(filteredData);
    for (const [num, avg] of Object.entries(machineAvg)) {
        const l = layoutLookup[num];
        if (!l) continue;
        const iId = l.islandId;
        if (!islandTotal[iId]) { islandTotal[iId] = 0; islandCount[iId] = 0; }
        islandTotal[iId] += avg; islandCount[iId]++;
    }
    const result = {};
    for (const iId of Object.keys(islandTotal)) {
        result[iId] = islandCount[iId] > 0 ? islandTotal[iId] / islandCount[iId] : 0;
    }
    return result;
}

/**
 * Compute per-machine avg diff from filteredData.
 */
function computeMachineAvgFromFiltered(filteredData) {
    const ms = {};
    filteredData.forEach(row => {
        const num = normalizeNum(row['台番号']);
        if (!ms[num]) ms[num] = { diff: 0, count: 0 };
        ms[num].diff += Number(row['最終差枚']) || 0; ms[num].count++;
    });
    const result = {};
    for (const [num, st] of Object.entries(ms)) {
        result[num] = st.count > 0 ? st.diff / st.count : 0;
    }
    return result;
}

/**
 * Compute per-model avg diff from filteredData.
 */
function computeModelAvgFromFiltered(filteredData) {
    const ms = {};
    filteredData.forEach(row => {
        const model = row['機種名'];
        if (!model) return;
        if (!ms[model]) ms[model] = { diff: 0, count: 0 };
        ms[model].diff += Number(row['最終差枚']) || 0; ms[model].count++;
    });
    const result = {};
    for (const [model, st] of Object.entries(ms)) {
        result[model] = st.count > 0 ? st.diff / st.count : 0;
    }
    return result;
}

/**
 * Determine position category (0=角,1=角2,2=角3,'other')
 */
function getPosCategory(num) {
    const l = layoutLookup[num];
    if (!l) return null;
    if (l.pos === 0) return 0;
    if (l.pos === 1) return 1;
    if (l.pos === 2) return 2;
    return 'other';
}

/**
 * Get condition colors for N total conditions (gradient blue->red).
 * Returns array of length N+1: index 0=無色, index N=赤
 */
function getConditionColors(n) {
    if (n === 0) return ['transparent'];
    const palettes = [
        // 1 condition
        ['transparent', 'rgba(220,60,60,0.85)'],
        // 2 conditions
        ['transparent', 'rgba(59,130,246,0.85)', 'rgba(220,60,60,0.85)'],
        // 3 conditions
        ['transparent', 'rgba(59,130,246,0.85)', 'rgba(255,165,0,0.85)', 'rgba(220,60,60,0.85)'],
        // 4 conditions
        ['transparent', 'rgba(59,130,246,0.85)', 'rgba(0,190,255,0.85)', 'rgba(255,165,0,0.85)', 'rgba(220,60,60,0.85)'],
        // 5 conditions
        ['transparent', 'rgba(59,130,246,0.85)', 'rgba(0,190,255,0.85)', 'rgba(60,200,100,0.85)', 'rgba(255,165,0,0.85)', 'rgba(220,60,60,0.85)'],
        // 6 conditions
        ['transparent', 'rgba(100,100,230,0.85)', 'rgba(59,130,246,0.85)', 'rgba(0,190,255,0.85)', 'rgba(60,200,100,0.85)', 'rgba(255,165,0,0.85)', 'rgba(220,60,60,0.85)'],
    ];
    return palettes[Math.min(n, 6) - 1] || palettes[palettes.length - 1];
}

function setupPrioLimit() {
    const chks = document.querySelectorAll('.prio-chk');
    chks.forEach(c => {
        c.addEventListener('change', () => {
            const checked = [...chks].filter(x => x.checked);
            if (checked.length > 2) c.checked = false;
        });
    });
}

function setupCondBadges() {
    const pairs = [
        ['cond-cons-neg-enabled', 'cond-cons-neg-badge', 'cond-card-cons-neg'],
        ['cond-cons-pos-enabled', 'cond-cons-pos-badge', 'cond-card-cons-pos'],
        ['cond-position-enabled', 'cond-position-badge', 'cond-card-position'],
        ['cond-digit-enabled', 'cond-digit-badge', 'cond-card-digit'],
        ['cond-island-avg-enabled', 'cond-island-avg-badge', 'cond-card-island-avg'],
        ['cond-machine-avg-enabled', 'cond-machine-avg-badge', 'cond-card-machine-avg'],
        ['cond-model-avg-enabled', 'cond-model-avg-badge', 'cond-card-model-avg'],
        ['cond-past-game-enabled', 'cond-past-game-badge', 'cond-card-past-game'],
    ];
    pairs.forEach(([cbId, badgeId, cardId]) => {
        const cb = document.getElementById(cbId);
        const badge = document.getElementById(badgeId);
        const card = document.getElementById(cardId);
        if (!cb || !badge || !card) return;

        cb.addEventListener('change', () => {
            if (cb.checked) {
                badge.textContent = 'ON'; badge.style.background = 'rgba(34,197,94,0.8)';
                card.classList.add('cond-active');
            } else {
                badge.textContent = 'OFF'; badge.style.background = 'rgba(100,100,120,0.5)';
                card.classList.remove('cond-active');
            }
        });
        // Initial sync
        if (cb.checked) {
            badge.textContent = 'ON'; badge.style.background = 'rgba(34,197,94,0.8)';
            card.classList.add('cond-active');
        }
    });
}

function setupTargetSearchBtn() {
    const btn = document.getElementById('target-search-btn');
    if (!btn) return;
    btn.addEventListener('click', () => {
        const fd = getFilteredData();
        renderTargetSupport(fd);
    });
}

function setupMobilePopupClose() {
    const closeBtn = document.getElementById('target-mobile-close');
    if (closeBtn) closeBtn.addEventListener('click', () => {
        document.getElementById('target-mobile-popup').style.display = 'none';
        document.body.classList.remove('modal-open');
    });
    document.getElementById('target-mobile-popup').addEventListener('click', e => {
        if (e.target === e.currentTarget) {
            e.currentTarget.style.display = 'none';
            document.body.classList.remove('modal-open');
        }
    });
}

/**
 * Main render function for target support tool.
 */
function renderTargetSupport(filteredData) {
    // 1. Compute latest streaks (ignores filter)
    const streaks = computeLatestStreaks();
    // 2. Compute machine/island/model avgs from filtered data
    const machineAvg = computeMachineAvgFromFiltered(filteredData);
    const islandAvg = computeIslandAvgFromFiltered(filteredData);
    const modelAvg = computeModelAvgFromFiltered(filteredData);
    // 3. Get latest records for hover info
    const latestRec = getLatestRecords();
    const latestDate = Object.values(latestRec).map(r => r['日付']).sort().slice(-1)[0] || '';
    const now = new Date();
    const todayDate = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;

    // 4. Read conditions
    const conds = {
        consNeg: {
            enabled: document.getElementById('cond-cons-neg-enabled').checked,
            vals: [...document.querySelectorAll('.cons-neg-chk:checked')].map(c => parseInt(c.value))
        },
        consPos: {
            enabled: document.getElementById('cond-cons-pos-enabled').checked,
            vals: [...document.querySelectorAll('.cons-pos-chk:checked')].map(c => parseInt(c.value))
        },
        position: {
            enabled: document.getElementById('cond-position-enabled').checked,
            vals: [...document.querySelectorAll('.pos-chk:checked')].map(c => c.value === 'other' ? 'other' : parseInt(c.value))
        },
        digit: {
            enabled: document.getElementById('cond-digit-enabled').checked,
            vals: [...document.querySelectorAll('.digit-chk:checked')].map(c => parseInt(c.value))
        },
        // 差枚系条件：有効／no threshold, sort-only
        islandAvg: {
            enabled: document.getElementById('cond-island-avg-enabled').checked
        },
        machineAvg: {
            enabled: document.getElementById('cond-machine-avg-enabled').checked
        },
        modelAvg: {
            enabled: document.getElementById('cond-model-avg-enabled').checked
        },
        pastGame: {
            enabled: document.getElementById('cond-past-game-enabled').checked,
            logic: document.querySelector('input[name="past-game-logic"]:checked')?.value || 'or',
            periods: [...document.querySelectorAll('.past-game-period-row')].map(row => {
                const pVal = parseInt(row.dataset.period);
                return {
                    period: pVal,
                    enabled: row.querySelector('.period-chk').checked,
                    ranges: [...row.querySelectorAll('.range-chk:checked')].map(c => parseInt(c.value))
                };
            }).filter(p => p.enabled)
        }
    };

    // Active conditions (enabled)
    const activeConds = Object.entries(conds).filter(([, c]) => c.enabled).map(([k]) => k);
    const totalConds = activeConds.length;

    // Priority conditions
    const prioConds = [...document.querySelectorAll('.prio-chk:checked')].map(c => c.value);
    // diff priority
    const diffPriority = document.querySelector('input[name="diff-priority"]:checked')?.value || 'machine';
    
    // Sort by match count checkbox
    const sortByMatchCount = document.getElementById('sort-by-match-count')?.checked;

    // Has diff conditions?
    const hasDiffConds = conds.machineAvg.enabled || conds.islandAvg.enabled;

    // Get selected models
    const selectedModels = [...document.querySelectorAll('#target-model-filter-list input:checked')].map(c => c.value);

    // 5. Evaluate each machine in layoutLookup
    const condKeyMap = { consNeg: 'cons-neg', consPos: 'cons-pos', position: 'position', digit: 'digit', islandAvg: 'island-avg', machineAvg: 'machine-avg', modelAvg: 'model-avg', pastGame: 'past-game' };
    const machines = [];
    const allDates = [...new Set(rawData.map(r => r['日付']))].sort();
    const dateIdxMap = {};
    allDates.forEach((d, i) => dateIdxMap[d] = i);
    const mHist = {};
    rawData.forEach(row => {
        const num = normalizeNum(row['台番号']);
        if (!mHist[num]) mHist[num] = {};
        mHist[num][row['日付']] = Number(row['累計ゲーム']) || 0;
    });

    for (const num of Object.keys(layoutLookup)) {
        const numVal = parseInt(num);
        // Skip circular islands
        if ((numVal >= 987 && numVal <= 998) || (numVal >= 1370 && numVal <= 1385)) continue;

        const rec = latestRec[num] || null;
        const model = rec ? rec['機種名'] : (layoutLookup[num] ? layoutLookup[num].model : null);

        if (selectedModels.length > 0 && (!model || !selectedModels.includes(model))) {
            continue;
        }

        const sk = streaks[num] || { neg: 0, pos: 0 };
        const mAvg = machineAvg[num] ?? null;
        const l = layoutLookup[num];
        const iId = l ? l.islandId : '';
        const iAvg = islandAvg[iId] ?? null;
        const posVal = getPosCategory(num);
        const digit = parseInt(num.slice(-1));

        // Evaluate each active condition
        let prioMatch = 0, otherMatch = 0;
        const matchedConds = [];

        const checkCond = (key, passes) => {
            if (!conds[key].enabled) return;
            const prioKey = condKeyMap[key];
            if (passes) {
                matchedConds.push(key);
                if (prioConds.includes(prioKey)) prioMatch++;
                else otherMatch++;
            }
        };

        checkCond('consNeg', conds.consNeg.vals.length === 0 || conds.consNeg.vals.some(v => v === 7 ? sk.neg >= 7 : sk.neg === v));
        checkCond('consPos', conds.consPos.vals.length === 0 || conds.consPos.vals.some(v => v === 7 ? sk.pos >= 7 : sk.pos === v));
        checkCond('position', conds.position.vals.length === 0 || conds.position.vals.includes(posVal));
        checkCond('digit', conds.digit.vals.length === 0 || conds.digit.vals.includes(digit));
        // 差枚系：データがあれば常に「合致」（フィルタなし、ソートのみ）
        checkCond('islandAvg', iAvg !== null);
        checkCond('machineAvg', mAvg !== null);
        checkCond('modelAvg', modelAvg[model] !== undefined);

        // Past Game Count Average (Independent Periods)
        let pastGameMatch = false;
        let displayAvg = null;
        if (conds.pastGame.enabled && conds.pastGame.periods.length > 0) {
            const latestIdx = dateIdxMap[latestDate];
            if (latestIdx !== undefined) {
                const results = [];
                for (const pCond of conds.pastGame.periods) {
                    let sumG = 0, countG = 0;
                    for (let i = 0; i < pCond.period; i++) {
                        const idx = latestIdx - i;
                        if (idx >= 0) {
                            const d = allDates[idx];
                            const g = mHist[num] ? mHist[num][d] : undefined;
                            if (g !== undefined) { sumG += g; countG++; }
                        }
                    }
                    const avgG = countG > 0 ? sumG / countG : 0;
                    if (displayAvg === null) displayAvg = avgG;

                    let bucket = 0;
                    if (avgG > 10000) bucket = 10;
                    else if (avgG > 0) bucket = Math.floor((avgG - 1) / 1000);
                    
                    results.push(pCond.ranges.length === 0 || pCond.ranges.includes(bucket));
                }
                if (conds.pastGame.logic === 'and') {
                    pastGameMatch = results.every(r => r === true);
                } else {
                    pastGameMatch = results.some(r => r === true);
                }
            }
        }
        checkCond('pastGame', pastGameMatch);

        const totalMatch = prioMatch + otherMatch;

        machines.push({
            num, sk, mAvg, iAvg, posVal, digit, avgG: displayAvg,
            prioMatch, otherMatch, totalMatch, matchedConds,
            rec: latestRec[num] || null
        });
    }

    // 6. Sort (ranking)
    machines.sort((a, b) => {
        const aD1 = diffPriority === 'machine' ? (a.mAvg ?? -Infinity) : (diffPriority === 'island' ? (a.iAvg ?? -Infinity) : (modelAvg[a.rec?.['機種名']] ?? -Infinity));
        const bD1 = diffPriority === 'machine' ? (b.mAvg ?? -Infinity) : (diffPriority === 'island' ? (b.iAvg ?? -Infinity) : (modelAvg[b.rec?.['機種名']] ?? -Infinity));
        const aD2 = diffPriority === 'machine' ? (a.iAvg ?? -Infinity) : (a.mAvg ?? -Infinity);
        const bD2 = diffPriority === 'machine' ? (b.iAvg ?? -Infinity) : (b.mAvg ?? -Infinity);

        // If 'sort-by-match-count' is enabled, total match count is the absolute primary key
        if (sortByMatchCount) {
            if (b.totalMatch !== a.totalMatch) return b.totalMatch - a.totalMatch;
        }

        // Primary: if diff conditions exist, sort by diff values first
        if (!sortByMatchCount && (hasDiffConds || conds.modelAvg.enabled)) {
            if (bD1 !== aD1) return bD1 - aD1;
            if (bD2 !== aD2) return bD2 - aD2;
        }

        // Then prio match count desc, then other match count desc
        if (b.prioMatch !== a.prioMatch) return b.prioMatch - a.prioMatch;
        if (b.otherMatch !== a.otherMatch) return b.otherMatch - a.otherMatch;

        // If diff conditions were NOT primary (OFF), use diffs as tiebreaker
        // OR if sortByMatchCount was true, diffs can act as tiebreaker after match counts
        if (sortByMatchCount || !hasDiffConds) {
            if (bD1 !== aD1) return bD1 - aD1;
            if (bD2 !== aD2) return bD2 - aD2;
        }

        return parseInt(a.num) - parseInt(b.num);
    });

    // 7. Build color map
    const colors = getConditionColors(totalConds);
    const colorMap = {};// num -> color
    machines.forEach(m => {
        colorMap[m.num] = colors[Math.min(m.totalMatch, colors.length - 1)];
    });

    // 8. Render legend
    const legendEl = document.getElementById('target-legend');
    legendEl.innerHTML = '';
    for (let i = 0; i <= totalConds; i++) {
        const item = document.createElement('div'); item.className = 'legend-item';
        const box = document.createElement('span'); box.className = 'color-box';
        box.style.background = colors[i] || 'transparent';
        if (!colors[i] || colors[i] === 'transparent') box.style.border = '1px solid #ccc';
        item.appendChild(box);
        const txt = document.createElement('span');
        txt.textContent = i === 0 ? '0条件合致（無色）' : `${i}条件合致`;
        item.appendChild(txt);
        legendEl.appendChild(item);
    }

    // 9. Render ranking list (top 30)
    const rankEl = document.getElementById('target-ranking-list'); rankEl.innerHTML = '';
    const top30 = machines.filter(m => m.totalMatch > 0).slice(0, 30);
    if (top30.length === 0) {
        rankEl.innerHTML = '<p style="color:var(--text-muted);padding:1rem;">条件に合致する台がありませんでした。条件を緩めてみてください。</p>';
    } else {
        const tbl = document.createElement('table');
        tbl.innerHTML = `<thead><tr>
            <th>順位</th><th>台番号</th><th>機種</th><th>合致数</th>
            ${activeConds.includes('consNeg') ? '<th>連続凹み</th>' : ''}
            ${activeConds.includes('consPos') ? '<th>連続凸</th>' : ''}
            ${activeConds.includes('machineAvg') ? '<th>台平均差枚</th>' : ''}
            ${activeConds.includes('islandAvg') ? '<th>島平均差枚</th>' : ''}
            ${activeConds.includes('modelAvg') ? '<th>機種平均差枚</th>' : ''}
            ${activeConds.includes('pastGame') ? '<th>過去G平均</th>' : ''}
            ${activeConds.includes('position') ? '<th>位置</th>' : ''}
        </tr></thead>`;
        const tbody = document.createElement('tbody');
        top30.forEach((m, i) => {
            const model = m.rec ? m.rec['機種名'] : '-';
            const tr = document.createElement('tr');
            tr.style.borderLeft = `4px solid ${colorMap[m.num] === 'transparent' ? '#444' : colorMap[m.num]}`;
            tr.classList.add('clickable');
            
            const mc = m.matchedConds;
            const mAvgVal = m.mAvg !== null ? Math.round(m.mAvg) : null;
            const iAvgVal = m.iAvg !== null ? Math.round(m.iAvg) : null;
            const modAvgVal = modelAvg[model] !== undefined ? Math.round(modelAvg[model]) : null;

            tr.innerHTML = `
                <td>${i + 1}</td>
                <td style="font-weight:bold">${parseInt(m.num)}</td>
                <td style="text-align:left;font-size:0.85em">${model}</td>
                <td><span style="background:${colorMap[m.num] === 'transparent' ? '#444' : colorMap[m.num]};padding:2px 8px;border-radius:10px;font-weight:bold">${m.totalMatch}/${totalConds}</span></td>
                ${activeConds.includes('consNeg') ? `<td style="${mc.includes('consNeg') ? 'background:rgba(255,215,0,0.15);font-weight:bold;' : ''}">${m.sk.neg > 0 ? `凹${m.sk.neg}日` : '–'}</td>` : ''}
                ${activeConds.includes('consPos') ? `<td style="${mc.includes('consPos') ? 'background:rgba(255,215,0,0.15);font-weight:bold;' : ''}">${m.sk.pos > 0 ? `凸${m.sk.pos}日` : '–'}</td>` : ''}
                ${activeConds.includes('machineAvg') ? `<td style="${mc.includes('machineAvg') ? 'background:rgba(255,215,0,0.15);font-weight:bold;' : ''}">${mAvgVal !== null ? formatVal(mAvgVal) : '–'}</td>` : ''}
                ${activeConds.includes('islandAvg') ? `<td style="${mc.includes('islandAvg') ? 'background:rgba(255,215,0,0.15);font-weight:bold;' : ''}">${iAvgVal !== null ? formatVal(iAvgVal) : '–'}</td>` : ''}
                ${activeConds.includes('modelAvg') ? `<td style="${mc.includes('modelAvg') ? 'background:rgba(255,215,0,0.15);font-weight:bold;' : ''}">${modAvgVal !== null ? formatVal(modAvgVal) : '–'}</td>` : ''}
                ${activeConds.includes('pastGame') ? `<td style="${mc.includes('pastGame') ? 'background:rgba(255,215,0,0.15);font-weight:bold;' : ''}">${m.avgG !== null && m.avgG !== undefined ? `${Math.round(m.avgG).toLocaleString()}G` : '–'}</td>` : ''}
                ${activeConds.includes('position') ? `<td style="${mc.includes('position') ? 'background:rgba(255,215,0,0.15);font-weight:bold;' : ''}">${getPosLabel(m.num)}</td>` : ''}
            `;

            // --- 修正後のクリックイベント処理 ---
            tr.addEventListener('click', () => {
                const cell = document.querySelector(`#target-heatmap-wrapper .heatmap-cell[data-num="${m.num}"]`);
                if (cell) {
                    // 他のハイライトを解除
                    document.querySelectorAll('#target-heatmap-wrapper .highlight-machine').forEach(c => {
                        c.classList.remove('highlight-machine');
                    });
                    
                    // ハイライト用クラスを追加 (!importantがあるためインラインスタイルより優先される)
                    cell.classList.add('highlight-machine');
                    
                    // スムーズスクロール
                    cell.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
                    
                    // 強制再描画（アニメーションを即時開始させるため）
                    void cell.offsetWidth;
                }
            });

            tbody.appendChild(tr);
        });
        tbl.appendChild(tbody);
        rankEl.appendChild(tbl);
    }

    // 10. Render island heatmap
    const wrap = document.getElementById('target-heatmap-wrapper'); wrap.innerHTML = '';
    const inner = document.createElement('div');
    inner.className = 'heatmap-inner';
    const isMobile = window.innerWidth < 768;

    layoutData.forEach(row => {
        const rowEl = document.createElement('div'); rowEl.className = 'heatmap-row';
        row.forEach(cell => {
            const isEmpty = cell === '';
            const el = document.createElement('div'); el.className = `heatmap-cell${isEmpty ? ' empty' : ''}`;
            if (!isEmpty) {
                const num = normalizeNum(cell);
                el.dataset.num = num; // Add data-num for easy lookup
                const m = machines.find(x => x.num === num);
                const color = colorMap[num] || 'transparent';
                el.style.backgroundColor = color;
                if (!m || m.totalMatch === 0) {
                    el.style.border = '1px solid rgba(128,128,128,0.2)';
                } else {
                    el.style.border = `2px solid ${color}`;
                    el.style.boxShadow = `0 0 6px ${color}`;
                }
                el.textContent = cell;

                // Build info for tooltip/popup
                const rec = m ? m.rec : null;
                const latestDiff = rec ? Number(rec['最終差枚']) || 0 : null;
                const latestG = rec ? Number(rec['累計ゲーム']) || 0 : null;
                const latestBig = rec ? Number(rec['BIG']) || 0 : null;
                const latestReg = rec ? Number(rec['REG']) || 0 : null;
                const model = rec ? rec['機種名'] : '不明';
                const sk = m ? m.sk : { neg: 0, pos: 0 };

                let estTxt = '';
                if (rec && (MACHINE_GROUPS.hanahana.includes(model) || MACHINE_GROUPS.juggler.includes(model))) {
                    const est = estimateSetting(model, latestG, latestBig, latestReg);
                    if (est) estTxt = `推定設定:${est.setting}（${(est.prob * 100).toFixed(1)}%）`;
                }
                const bigProb = latestG && latestBig ? `1/${Math.round(latestG / latestBig)}` : '–';
                const regProb = latestG && latestReg ? `1/${Math.round(latestG / latestReg)}` : '–';
                const synProb = latestG && (latestBig + latestReg) ? `1/${Math.round(latestG / (latestBig + latestReg))}` : '–';
                const streakTxt = sk.neg > 0 ? `凹み${sk.neg}日連続` : sk.pos > 0 ? `凸${sk.pos}日連続` : 'なし';
                const mAvgTxt = m && m.mAvg !== null ? `${Math.round(m.mAvg).toLocaleString()}枚` : '–';
                const iAvgTxt = m && m.iAvg !== null ? `${Math.round(m.iAvg).toLocaleString()}枚` : '–';
                const pastGAvgTxt = m && m.avgG !== null && m.avgG !== undefined ? `${Math.round(m.avgG).toLocaleString()}G` : '–';
                const dataUrl = `https://cosmojapan.pt.teramoba2.com/obu/standgraph/?rack_no=${parseInt(num)}&dai_hall_id=2648&target_date=${todayDate}`;

                const matchStr = m ? m.matchedConds.map(k => ({ consNeg: '連続凹み', consPos: '連続凸', position: '角位置', digit: '台末尾', islandAvg: '島平均差枚', machineAvg: '台平均差枚', pastGame: '過去G数平均' }[k] || k)).join('・') : '–';

                if (isMobile) {
                    // Mobile: tap to show popup
                    el.addEventListener('click', e => {
                        e.stopPropagation();
                        const pop = document.getElementById('target-mobile-popup');
                        const cont = document.getElementById('target-mobile-content');
                        const link = document.getElementById('target-mobile-link');
                        cont.innerHTML = `
                            <div class="tm-title">台番号 ${parseInt(num)} <span class="tm-model">${model}</span></div>
                            <div class="tm-badge" style="background:${color === 'transparent' ? '#444' : color}">${m ? m.totalMatch : 0}/${totalConds} 条件合致</div>
                            <div class="tm-row"><span>最新日差枚</span><span>${latestDiff !== null ? formatVal(latestDiff) : '–'}</span></div>
                            <div class="tm-row"><span>推定設定</span><span>${estTxt || '–'}</span></div>
                            <div class="tm-row"><span>BIG確率</span><span>${bigProb}</span></div>
                            <div class="tm-row"><span>REG確率</span><span>${regProb}</span></div>
                            <div class="tm-row"><span>合成確率</span><span>${synProb}</span></div>
                            <div class="tm-row"><span>総G数</span><span>${latestG !== null ? latestG.toLocaleString() : '–'}</span></div>
                            <div class="tm-row"><span>連続凹み/凸</span><span>${streakTxt}</span></div>
                            <div class="tm-row"><span>台平均差枚</span><span>${mAvgTxt}</span></div>
                            <div class="tm-row"><span>島平均差枚</span><span>${iAvgTxt}</span></div>
                            <div class="tm-row"><span>過去G数平均</span><span>${pastGAvgTxt}</span></div>
                            <div class="tm-row"><span>合致条件</span><span>${matchStr}</span></div>
                        `;
                        link.href = dataUrl;
                        pop.style.display = 'flex';
                        document.body.classList.add('modal-open');
                    });
                } else {
                    // PC: hover tooltip
                    const tipHtml = `
                        <div class="tooltip-title">台番号: ${parseInt(num)} ${model}</div>
                        <div class="tooltip-body">
                            <div><b>${m ? m.totalMatch : 0}/${totalConds} 条件合致</b>${matchStr ? ` (${matchStr})` : ''}  </div>
                            <div>最新日差枚: ${latestDiff !== null ? formatVal(latestDiff) : '–'}</div>
                            ${estTxt ? `<div>${estTxt}</div>` : ''}
                            <div>BIG: ${bigProb} / REG: ${regProb} / 合成: ${synProb}</div>
                            <div>総G数: ${latestG !== null ? latestG.toLocaleString() : '–'}</div>
                            <div>連続: ${streakTxt}</div>
                            <div>台平均: ${mAvgTxt} / 島平均: ${iAvgTxt}</div>
                            <div>過去G平均: ${pastGAvgTxt}</div>
                            <div style="margin-top:4px;font-size:0.85em;color:#93c5fd">クリックでデータサイトへ</div>
                        </div>`;
                    el.addEventListener('mouseenter', () => { tooltip.innerHTML = tipHtml; tooltip.classList.add('visible'); });
                    el.addEventListener('mouseleave', () => tooltip.classList.remove('visible'));
                    el.style.cursor = 'pointer';
                    el.addEventListener('click', () => window.open(dataUrl, '_blank'));
                }
            }
            rowEl.appendChild(el);
        });
        inner.appendChild(rowEl);
    });
    wrap.appendChild(inner);
    enableHeatmapPinchZoom('target-heatmap-wrapper');
    applyHeatmapCellSizes();

    document.getElementById('target-results').style.display = 'block';
}

function populateTargetModelFilter() {
    const filterContainer = document.getElementById('target-model-filter-list');
    if (!filterContainer) return;
    const models = new Set(rawData.map(r => r['機種名']).filter(Boolean));
    const sortedModels = Array.from(models).sort();

    filterContainer.innerHTML = '';
    sortedModels.forEach(m => {
        const lbl = document.createElement('label');
        lbl.innerHTML = `<input type="checkbox" value="${m}"> ${m}`;
        filterContainer.appendChild(lbl);
    });

    filterContainer.querySelectorAll('input').forEach(chk => {
        chk.addEventListener('change', () => {
            saveTargetConditions();
            const res = document.getElementById('target-results');
            if (res && res.style.display !== 'none') renderTargetSupport(getFilteredData());
        });
    });

    // Apply saved models if any
    if (window._savedModels) {
        filterContainer.querySelectorAll('input').forEach(chk => {
            if (window._savedModels.includes(chk.value)) chk.checked = true;
        });
        delete window._savedModels;
    }
}

function setupTargetSection() {
    setupPrioLimit();
    setupCondBadges();
    setupTargetSearchBtn();
    setupMobilePopupClose();

    document.getElementById('btn-model-filter-all')?.addEventListener('click', () => {
        const chks = document.querySelectorAll('#target-model-filter-list input[type="checkbox"]');
        let changed = false;
        chks.forEach(c => { if (!c.checked) { c.checked = true; changed = true; } });
        if (changed) {
            saveTargetConditions();
            const res = document.getElementById('target-results');
            if (res && res.style.display !== 'none') renderTargetSupport(getFilteredData());
        }
    });

    document.getElementById('btn-model-filter-clear')?.addEventListener('click', () => {
        const chks = document.querySelectorAll('#target-model-filter-list input[type="checkbox"]');
        let changed = false;
        chks.forEach(c => { if (c.checked) { c.checked = false; changed = true; } });
        if (changed) {
            saveTargetConditions();
            const res = document.getElementById('target-results');
            if (res && res.style.display !== 'none') renderTargetSupport(getFilteredData());
        }
    });

    // Event listeners for Past Game Count condition
    document.querySelectorAll('.period-chk, .range-chk, #cond-past-game-enabled, input[name="past-game-logic"]').forEach(el => {
        el.addEventListener('change', () => {
            saveTargetConditions();
            const res = document.getElementById('target-results');
            if (res && res.style.display !== 'none') renderTargetSupport(getFilteredData());
        });
    });
    // 機種平均のリスナーも追加
    document.getElementById('cond-model-avg-enabled').addEventListener('change', () => {
        saveTargetConditions();
        const res = document.getElementById('target-results');
        if (res && res.style.display !== 'none') renderTargetSupport(getFilteredData());
    });
    
    document.querySelectorAll('.period-all-btn').forEach(btn => {
        btn.addEventListener('click', e => {
            const row = e.target.closest('.past-game-period-row');
            row.querySelectorAll('.range-chk').forEach(c => c.checked = true);
            row.querySelector('.period-chk').checked = true;
            saveTargetConditions();
            const res = document.getElementById('target-results');
            if (res && res.style.display !== 'none') renderTargetSupport(getFilteredData());
        });
    });

    document.querySelectorAll('.period-clear-btn').forEach(btn => {
        btn.addEventListener('click', e => {
            const row = e.target.closest('.past-game-period-row');
            row.querySelectorAll('.range-chk').forEach(c => c.checked = false);
            row.querySelector('.period-chk').checked = false;
            saveTargetConditions();
            const res = document.getElementById('target-results');
            if (res && res.style.display !== 'none') renderTargetSupport(getFilteredData());
        });
    });
    
    // Add listeners for other conditions
    const otherSelectors = [
        '#cond-cons-neg-enabled', '#cond-cons-pos-enabled', '#cond-position-enabled', '#cond-digit-enabled',
        '#cond-island-avg-enabled', '#cond-machine-avg-enabled', '#sort-by-match-count',
        '.cons-neg-chk', '.cons-pos-chk', '.pos-chk', '.digit-chk',
        '.prio-chk', 'input[name="diff-priority"]'
    ];
    document.querySelectorAll(otherSelectors.join(',')).forEach(el => {
        el.addEventListener('change', saveTargetConditions);
    });

    loadTargetConditions();
}

function saveTargetConditions() {
    const config = {
        enabled: {
            consNeg: document.getElementById('cond-cons-neg-enabled').checked,
            consPos: document.getElementById('cond-cons-pos-enabled').checked,
            position: document.getElementById('cond-position-enabled').checked,
            digit: document.getElementById('cond-digit-enabled').checked,
            islandAvg: document.getElementById('cond-island-avg-enabled').checked,
            machineAvg: document.getElementById('cond-machine-avg-enabled').checked,
            modelAvg: document.getElementById('cond-model-avg-enabled').checked,
            pastGame: document.getElementById('cond-past-game-enabled').checked,
        },
        vals: {
            consNeg: [...document.querySelectorAll('.cons-neg-chk:checked')].map(c => c.value),
            consPos: [...document.querySelectorAll('.cons-pos-chk:checked')].map(c => c.value),
            position: [...document.querySelectorAll('.pos-chk:checked')].map(c => c.value),
            digit: [...document.querySelectorAll('.digit-chk:checked')].map(c => c.value),
            pastGameLogic: document.querySelector('input[name="past-game-logic"]:checked')?.value || 'or',
            diffPriority: document.querySelector('input[name="diff-priority"]:checked')?.value || 'machine',
            sortByMatchCount: document.getElementById('sort-by-match-count')?.checked,
            prioConds: [...document.querySelectorAll('.prio-chk:checked')].map(c => c.value),
            models: [...document.querySelectorAll('#target-model-filter-list input:checked')].map(c => c.value)
        },
        pastGame: [...document.querySelectorAll('.past-game-period-row')].map(row => ({
            period: row.dataset.period,
            enabled: row.querySelector('.period-chk').checked,
            ranges: [...row.querySelectorAll('.range-chk:checked')].map(c => c.value)
        }))
    };
    localStorage.setItem('target_support_config', JSON.stringify(config));
}

function loadTargetConditions() {
    const data = localStorage.getItem('target_support_config');
    if (!data) return;
    try {
        const config = JSON.parse(data);
        // Value checkboxes
        const setChecks = (selector, vals) => {
            if (!vals) return;
            document.querySelectorAll(selector).forEach(c => {
                c.checked = vals.includes(c.value);
            });
        };
        setChecks('.cons-neg-chk', config.vals.consNeg);
        setChecks('.cons-pos-chk', config.vals.consPos);
        setChecks('.pos-chk', config.vals.position);
        setChecks('.digit-chk', config.vals.digit);
        setChecks('.prio-chk', config.vals.prioConds);

        // Radios
        if (config.vals.pastGameLogic) {
            const r = document.querySelector(`input[name="past-game-logic"][value="${config.vals.pastGameLogic}"]`);
            if (r) r.checked = true;
        }
        if (config.vals.diffPriority) {
            const r = document.querySelector(`input[name="diff-priority"][value="${config.vals.diffPriority}"]`);
            if (r) r.checked = true;
        }
        
        if (config.vals.sortByMatchCount !== undefined) {
            const cb = document.getElementById('sort-by-match-count');
            if (cb) cb.checked = config.vals.sortByMatchCount;
        }

        // Past game rows
        if (config.pastGame) {
            config.pastGame.forEach(item => {
                const row = document.querySelector(`.past-game-period-row[data-period="${item.period}"]`);
                if (row) {
                    const pchk = row.querySelector('.period-chk');
                    if (pchk) pchk.checked = item.enabled;
                    row.querySelectorAll('.range-chk').forEach(c => {
                        c.checked = item.ranges.includes(c.value);
                    });
                }
            });
        }

        // Enabled checkboxes (dispatch change events last so saveTargetConditions gets correct state)
        const idMap = {
            consNeg: 'cond-cons-neg-enabled', consPos: 'cond-cons-pos-enabled', position: 'cond-position-enabled',
            digit: 'cond-digit-enabled', islandAvg: 'cond-island-avg-enabled', machineAvg: 'cond-machine-avg-enabled',
            modelAvg: 'cond-model-avg-enabled', pastGame: 'cond-past-game-enabled'
        };
        for (const [key, id] of Object.entries(idMap)) {
            const el = document.getElementById(id);
            if (el && config.enabled[key] !== undefined) {
                el.checked = config.enabled[key];
                el.dispatchEvent(new Event('change')); // Trigger badge update & save
            }
        }

        // Models (populated later, so we need a way to apply this after population)
        window._savedModels = config.vals.models;

    } catch (e) { console.error('Failed to load config', e); }
}

document.addEventListener('DOMContentLoaded', () => {
    init();
    setupTargetSection();
    setupGameCountPeriodTabs();
});

function setupGameCountPeriodTabs() {
    document.getElementById('game-count-period-tabs')?.addEventListener('click', e => {
        if (e.target.classList.contains('tab-btn')) {
            document.querySelectorAll('#game-count-period-tabs .tab-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            renderGameCountAnalysis();
        }
    });
}

function renderGameCountAnalysis() {
    const periodBtn = document.querySelector('#game-count-period-tabs .tab-btn.active');
    const period = parseInt(periodBtn ? periodBtn.dataset.period : '1');

    const allDates = [...new Set(rawData.map(r => r['日付']))].sort();
    if (allDates.length < 2) return;

    const dateIdxMap = {};
    allDates.forEach((d, i) => dateIdxMap[d] = i);

    const mHist = {};
    rawData.forEach(row => {
        const num = normalizeNum(row['台番号']);
        if (!mHist[num]) mHist[num] = {};
        mHist[num][row['日付']] = Number(row['累計ゲーム']) || 0;
    });

    const targetData = getFilteredData();
    const buckets = {};

    targetData.forEach(row => {
        const num = normalizeNum(row['台番号']);
        const targetDate = row['日付'];
        const targetDiff = Number(row['最終差枚']) || 0;

        const currentIdx = dateIdxMap[targetDate];
        if (currentIdx === undefined) return;

        let sumG = 0;
        let countG = 0;

        for (let i = 1; i <= period; i++) {
            const prevIdx = currentIdx - i;
            if (prevIdx >= 0) {
                const prevDate = allDates[prevIdx];
                const g = mHist[num][prevDate];
                if (g !== undefined) {
                    sumG += g;
                    countG++;
                }
            }
        }

        if (countG > 0) {
            const avgG = sumG / countG;
            const bucketIdx = Math.floor(avgG / 1000);
            if (!buckets[bucketIdx]) buckets[bucketIdx] = { diffSum: 0, count: 0 };
            buckets[bucketIdx].diffSum += targetDiff;
            buckets[bucketIdx].count++;
        }
    });

    const labels = [], values = [];
    Object.keys(buckets).sort((a, b) => parseInt(a) - parseInt(b)).forEach(idx => {
        const b = buckets[idx];
        if (b.count < 1) return;
        labels.push(`${idx * 1000}-${(parseInt(idx) + 1) * 1000}G`);
        values.push(Math.round(b.diffSum / b.count));
    });

    const posColor = 'rgba(59,130,246,0.8)';
    const negColor = 'rgba(239,68,68,0.8)';

    drawBar('chart-game-count-diff', labels, values, '平均差枚', {
        datasetExtras: {
            backgroundColor: values.map(v => v > 0 ? posColor : negColor)
        }
    });
}


