import sys
import re

with open('docs/ogiya/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update confusion matrix display
old_stats = '''    const highWrap = document.getElementById('ml-stat-high-wrap');
    if (currentMlTarget === 'classification') {
        highWrap.style.display = 'block';
        const p = periodData.n_cls > 0 ? ((periodData.n_high / periodData.n_cls) * 100).toFixed(1) : 0;
        document.getElementById('ml-stat-high').textContent = `${(periodData.n_high||0).toLocaleString()} (${p}%)`;
    } else {
        highWrap.style.display = 'none';
    }'''

new_stats = '''    const highWrap = document.getElementById('ml-stat-high-wrap');
    const confWrap = document.getElementById('ml-stat-confusion-wrap');
    if (currentMlTarget === 'classification') {
        highWrap.style.display = 'block';
        const p = periodData.n_cls > 0 ? ((periodData.n_high / periodData.n_cls) * 100).toFixed(1) : 0;
        document.getElementById('ml-stat-high').textContent = `${(periodData.n_high||0).toLocaleString()} (${p}%)`;
        
        if (res.tn_ratio !== undefined) {
            confWrap.style.display = 'block';
            document.getElementById('ml-stat-tn').textContent = (res.tn_ratio * 100).toFixed(1) + '%';
            document.getElementById('ml-stat-fp').textContent = (res.fp_ratio * 100).toFixed(1) + '%';
            document.getElementById('ml-stat-fn').textContent = (res.fn_ratio * 100).toFixed(1) + '%';
            document.getElementById('ml-stat-tp').textContent = (res.tp_ratio * 100).toFixed(1) + '%';
        } else {
            confWrap.style.display = 'none';
        }
    } else {
        highWrap.style.display = 'none';
        confWrap.style.display = 'none';
    }
    
    // Render features list
    if (globalMlResults && globalMlResults.feature_names_jp) {
        const featList = document.getElementById('ml-features-list');
        featList.innerHTML = '';
        for (const [key, name] of Object.entries(globalMlResults.feature_names_jp)) {
            const el = document.createElement('span');
            el.style.cssText = 'background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 4px; padding: 2px 8px; font-size: 0.8rem;';
            el.textContent = name;
            featList.appendChild(el);
        }
    }'''

content = content.replace(old_stats, new_stats)

# 2. Fix Tree rules formatting logic
old_tree = '''                         .replace(/<=\s*([\d\.\-]+)/, (match, p1) => {
                             let v = parseFloat(p1);
                             if (label.includes('前日差枚') || label.includes('島の前日平均')) {
                                 v = Math.round(v / 100) * 100;
                                 return ` が <span style="color:#fbbf24;">約 ${v} 枚 以下</span>`;
                             } else if (label.includes('曜日') || label.includes('連続')) {
                                 v = Math.round(v);
                                 return ` が <span style="color:#fbbf24;">${v} 以下</span>`;
                             }
                             return ` が <span style="color:#fbbf24;">${v.toFixed(1).replace('.0','')} 以下</span>`;
                         })
                         .replace(/>\s*([\d\.\-]+)/, (match, p1) => {
                             let v = parseFloat(p1);
                             if (label.includes('前日差枚') || label.includes('島の前日平均')) {
                                 v = Math.round(v / 100) * 100;
                                 return ` が <span style="color:#fbbf24;">約 ${v} 枚 より大きい</span>`;
                             } else if (label.includes('曜日') || label.includes('連続')) {
                                 v = Math.round(v);
                                 return ` が <span style="color:#fbbf24;">${v} より大きい</span>`;
                             }
                             return ` が <span style="color:#fbbf24;">${v.toFixed(1).replace('.0','')} より大きい</span>`;
                         });'''

new_tree = '''                         .replace(/<=\s*([\d\.\-]+)/, (match, p1) => {
                             let v = parseFloat(p1);
                             if (label.includes('差枚')) {
                                 v = Math.round(v / 100) * 100;
                                 return ` が <span style="color:#fbbf24;">約 ${v} 枚 以下</span>`;
                             } else if (label.includes('曜日') || label.includes('連続')) {
                                 v = Math.round(v);
                                 return ` が <span style="color:#fbbf24;">${v} 以下</span>`;
                             } else if (label.includes('ゲーム')) {
                                 v = Math.round(v / 100) * 100;
                                 return ` が <span style="color:#fbbf24;">約 ${v} G 以下</span>`;
                             }
                             return ` が <span style="color:#fbbf24;">${v.toFixed(1).replace('.0','')} 以下</span>`;
                         })
                         .replace(/>\s*([\d\.\-]+)/, (match, p1) => {
                             let v = parseFloat(p1);
                             if (label.includes('差枚')) {
                                 v = Math.round(v / 100) * 100;
                                 return ` が <span style="color:#fbbf24;">約 ${v} 枚 超過 (より大きい)</span>`;
                             } else if (label.includes('曜日') || label.includes('連続')) {
                                 v = Math.round(v);
                                 return ` が <span style="color:#fbbf24;">${v} 超過 (より大きい)</span>`;
                             } else if (label.includes('ゲーム')) {
                                 v = Math.round(v / 100) * 100;
                                 return ` が <span style="color:#fbbf24;">約 ${v} G 超過 (より大きい)</span>`;
                             }
                             return ` が <span style="color:#fbbf24;">${v.toFixed(1).replace('.0','')} 超過 (より大きい)</span>`;
                         });
                         
            // Re-apply feature names if they contain multiple numbers
            if (globalMlResults && globalMlResults.feature_names_jp) {
                for (const [key, name] of Object.entries(globalMlResults.feature_names_jp)) {
                    label = label.replace(new RegExp(key, 'g'), `<span style="color:#60a5fa; font-weight:bold;">${name}</span>`);
                }
            }'''

content = content.replace(old_tree, new_tree)

# 3. Dynamic canvas height for RF
old_rf = '''        options: {
            indexAxis: 'y',
            responsive: true,'''

new_rf = '''        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,'''
# Wait, it already has maintainAspectRatio: false. Let's set the height explicitly.
old_rf_func = '''function renderMLChartRF(fiList) {
    if (!fiList) return;
    const labels = fiList.map(f => f.feature_jp);
    const vals = fiList.map(f => f.importance);
    
    const ctx = document.getElementById('ml-chart-rf');
    if (charts['ml-rf']) charts['ml-rf'].destroy();'''

new_rf_func = '''function renderMLChartRF(fiList) {
    if (!fiList) return;
    const labels = fiList.map(f => f.feature_jp);
    const vals = fiList.map(f => f.importance);
    
    const canvas = document.getElementById('ml-chart-rf');
    const container = canvas.parentElement;
    // Calculate required height based on number of features (e.g. 25px per bar)
    const requiredHeight = Math.max(400, labels.length * 25);
    container.style.height = `${requiredHeight}px`;
    
    const ctx = canvas;
    if (charts['ml-rf']) charts['ml-rf'].destroy();'''

content = content.replace(old_rf_func, new_rf_func)

with open('docs/ogiya/app.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("app.js updated.")
