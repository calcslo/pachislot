import re

with open('docs/ogiya/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the full renderNextDayPredictions function
old_pattern = r'function renderNextDayPredictions\(predsData\) \{.*?\n\}'
new_func = r'''function renderNextDayPredictions(predsData) {
    const container = document.getElementById('ml-next-day-container');
    if (!predsData || !predsData.predictions || predsData.predictions.length === 0) {
        container.style.display = 'none';
        return;
    }
    container.style.display = 'block';

    const info = document.getElementById('ml-next-day-info');
    const eventText = predsData.is_event ? ' <span style="color:#ef4444;">(イベント日)</span>' : '';
    info.innerHTML = `予想対象日: <span style="color:#60a5fa;">${predsData.target_date}</span>${eventText}`;

    const hitRateEl = document.getElementById('ml-next-day-hit-rate');
    const avgDiffEl = document.getElementById('ml-next-day-avg-diff');
    if (hitRateEl && predsData.hit_rate != null) {
        hitRateEl.textContent = (predsData.hit_rate * 100).toFixed(1) + '%';
    }
    if (avgDiffEl && predsData.avg_diff != null) {
        const sign = predsData.avg_diff >= 0 ? '+' : '';
        avgDiffEl.textContent = sign + Math.round(predsData.avg_diff) + ' 枚';
    }

    const tbody = document.getElementById('ml-next-day-tbody');
    tbody.innerHTML = '';

    const featureNames = (mlAnalysisData && mlAnalysisData.feature_names_jp) ? mlAnalysisData.feature_names_jp : {};

    predsData.predictions.slice(0, 20).forEach((p, index) => {
        const tr = document.createElement('tr');
        tr.style.borderBottom = '1px solid var(--glass-border)';

        const prob = p.prob_high_setting * 100;
        let probColor = '#94a3b8';
        if (prob >= 50) probColor = '#ef4444';
        else if (prob >= 35) probColor = '#fbbf24';

        const diff = p.expected_diff;
        let diffColor = '#94a3b8';
        if (diff >= 1000) diffColor = '#ef4444';
        else if (diff > 0) diffColor = '#fbbf24';
        else diffColor = '#64748b';

        // ランクバッジ
        let rankBadge;
        if (index === 0) rankBadge = `<span style="display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:gold;color:#000;font-weight:bold;font-size:0.85rem;">1</span>`;
        else if (index === 1) rankBadge = `<span style="display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:silver;color:#000;font-weight:bold;font-size:0.85rem;">2</span>`;
        else if (index === 2) rankBadge = `<span style="display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:#cd7f32;color:#fff;font-weight:bold;font-size:0.85rem;">3</span>`;
        else rankBadge = `<span style="display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:rgba(59,130,246,0.2);color:var(--accent-blue);font-weight:bold;font-size:0.85rem;">${index+1}</span>`;

        const f = p.features;
        let reasons = [];
        if (f.cons_neg >= 3) reasons.push(`${f.cons_neg}日連続凹み`);
        else if (f.cons_neg >= 1) reasons.push(`${f.cons_neg}日凹み`);
        if (f.prev_diff_1 != null && f.prev_diff_1 < -1000) reasons.push(`前日${Math.round(f.prev_diff_1)}枚`);
        else if (f.prev_diff_1 != null && f.prev_diff_1 > 1000) reasons.push(`前日+${Math.round(f.prev_diff_1)}枚`);
        if (f.neg_after_pos === 1) reasons.push('前日高設定後の凹み');
        if (f.island_trend != null && f.island_trend > 500) reasons.push(`島好調(${Math.round(f.island_trend)}枚)`);
        if (f.is_event_day === 1) reasons.push('イベント日');
        if (f.position === 0) reasons.push('角台');
        if (f.cumul_7d_diff != null && f.cumul_7d_diff < -3000) reasons.push(`7日累積${Math.round(f.cumul_7d_diff)}枚`);

        let reasonHtml = reasons.slice(0, 3).map(r =>
            `<span style="background:rgba(59,130,246,0.12);border:1px solid rgba(59,130,246,0.3);padding:2px 7px;border-radius:4px;font-size:0.78rem;margin-right:3px;display:inline-block;margin-bottom:3px;white-space:nowrap;">${r}</span>`
        ).join('');
        if (!reasonHtml) reasonHtml = '<span style="color:var(--text-muted);font-size:0.78rem;">特筆なし</span>';

        const detailId = `pred-detail-${index}`;
        const detailBtn = `<button onclick="togglePredDetail('${detailId}')" style="margin-left:4px;padding:2px 8px;border-radius:4px;border:1px solid rgba(59,130,246,0.4);background:transparent;color:var(--accent-blue);font-size:0.75rem;cursor:pointer;white-space:nowrap;">詳細▼</button>`;

        let detailRows = Object.entries(f).map(([k, v]) => {
            const name = featureNames[k] || k;
            let vStr = (typeof v === 'number' && !Number.isInteger(v)) ? v.toFixed(1) : v;
            return `<tr><td style="padding:2px 8px;color:var(--text-muted);font-size:0.78rem;white-space:nowrap;">${name}</td><td style="padding:2px 8px;font-size:0.78rem;font-weight:bold;">${vStr}</td></tr>`;
        }).join('');

        tr.innerHTML = `
            <td style="padding:8px 10px;text-align:center;vertical-align:middle;">${rankBadge}</td>
            <td style="padding:8px 10px;font-weight:bold;font-size:1.05rem;vertical-align:middle;white-space:nowrap;">${p.machine}</td>
            <td style="padding:8px 10px;color:${probColor};font-weight:bold;font-size:1.05rem;vertical-align:middle;white-space:nowrap;">${prob.toFixed(1)}%</td>
            <td style="padding:8px 10px;color:${diffColor};font-weight:bold;vertical-align:middle;white-space:nowrap;">${diff >= 0 ? '+' : ''}${Math.round(diff)}枚</td>
            <td style="padding:8px 10px;vertical-align:middle;">
                <div style="display:flex;flex-wrap:wrap;align-items:center;gap:2px;">${reasonHtml}${detailBtn}</div>
                <div id="${detailId}" style="display:none;margin-top:8px;background:var(--bg-main);border-radius:6px;padding:4px;border:1px solid var(--glass-border);">
                    <table style="border-collapse:collapse;width:100%;">${detailRows}</table>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function togglePredDetail(id) {
    const el = document.getElementById(id);
    if (!el) return;
    const btn = el.previousElementSibling ? el.previousElementSibling.querySelector('button') : null;
    if (el.style.display === 'none') {
        el.style.display = 'block';
        if (btn) btn.textContent = '詳細▲';
    } else {
        el.style.display = 'none';
        if (btn) btn.textContent = '詳細▼';
    }
}'''

# Replace with regex
content = re.sub(
    r'function renderNextDayPredictions\(predsData\) \{.*?\n\}',
    new_func,
    content,
    flags=re.DOTALL
)

with open('docs/ogiya/app.js', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
