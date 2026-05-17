import sys

with open('docs/ogiya/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

old_func = '''function renderNextDayPredictions(predsData) {
    const container = document.getElementById('ml-next-day-container');
    if (!predsData || !predsData.predictions || predsData.predictions.length === 0) {
        container.style.display = 'none';
        return;
    }
    container.style.display = 'block';
    
    const info = document.getElementById('ml-next-day-info');
    const eventText = predsData.is_event ? ' <span style="color:#ef4444;">(イベント日)</span>' : '';
    info.innerHTML = `予想対象日: <span style="color:#60a5fa;">${predsData.target_date}</span>${eventText}`;
    
    const tbody = document.getElementById('ml-next-day-tbody');
    tbody.innerHTML = '';
    
    predsData.predictions.slice(0, 15).forEach(p => {
        const tr = document.createElement('tr');
        tr.style.borderBottom = '1px solid var(--glass-border)';
        
        // Probability formatting
        const prob = p.prob_high_setting * 100;
        let probColor = '#94a3b8';
        if (prob >= 50) probColor = '#ef4444';
        else if (prob >= 30) probColor = '#fbbf24';
        
        // Diff formatting
        const diff = p.expected_diff;
        let diffColor = '#94a3b8';
        if (diff >= 1000) diffColor = '#ef4444';
        else if (diff > 0) diffColor = '#fbbf24';
        else if (diff < 0) diffColor = '#64748b';
        
        // Features (Reasons)
        let reasons = [];
        if (p.features.prev_diff < 0) reasons.push(`前日差枚がマイナス (${Math.round(p.features.prev_diff)}枚)`);
        else if (p.features.prev_diff > 1000) reasons.push(`前日好調 (${Math.round(p.features.prev_diff)}枚)`);
        
        if (p.features.cons_neg >= 2) reasons.push(`${p.features.cons_neg}日連続凹み`);
        if (p.features.island_avg_prev > 500) reasons.push(`所属島が前日好調`);
        if (p.features.is_event_day === 1) reasons.push(`明日はイベント日`);
        
        let reasonHtml = reasons.map(r => `<span style="background:var(--bg-main); padding:2px 6px; border-radius:4px; font-size:0.8rem; margin-right:4px; display:inline-block; margin-bottom:4px;">${r}</span>`).join('');
        if (!reasonHtml) reasonHtml = '<span style="color:var(--text-muted); font-size:0.8rem;">特筆すべき特徴なし</span>';
        
        tr.innerHTML = `
            <td style="padding: 10px; font-weight: bold;">${p.machine}</td>
            <td style="padding: 10px; color: ${probColor}; font-weight: bold;">${prob.toFixed(1)}%</td>
            <td style="padding: 10px; color: ${diffColor}; font-weight: bold;">${Math.round(diff)} 枚</td>
            <td style="padding: 10px;">${reasonHtml}</td>
        `;
        tbody.appendChild(tr);
    });
}'''

new_func = '''function renderNextDayPredictions(predsData) {
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
    if (hitRateEl && predsData.hit_rate !== undefined) {
        hitRateEl.textContent = (predsData.hit_rate * 100).toFixed(1) + '%';
    }
    const avgDiffEl = document.getElementById('ml-next-day-avg-diff');
    if (avgDiffEl && predsData.avg_diff !== undefined) {
        avgDiffEl.textContent = Math.round(predsData.avg_diff) + ' 枚';
    }
    
    const tbody = document.getElementById('ml-next-day-tbody');
    tbody.innerHTML = '';
    
    predsData.predictions.slice(0, 15).forEach((p, index) => {
        const tr = document.createElement('tr');
        tr.style.borderBottom = '1px solid var(--glass-border)';
        
        // Probability formatting
        const prob = p.prob_high_setting * 100;
        let probColor = '#94a3b8';
        if (prob >= 50) probColor = '#ef4444';
        else if (prob >= 30) probColor = '#fbbf24';
        
        // Diff formatting
        const diff = p.expected_diff;
        let diffColor = '#94a3b8';
        if (diff >= 1000) diffColor = '#ef4444';
        else if (diff > 0) diffColor = '#fbbf24';
        else if (diff < 0) diffColor = '#64748b';
        
        // Features (Reasons)
        let reasons = [];
        if (p.features.prev_diff_1 < 0) reasons.push(`前日差枚がマイナス (${Math.round(p.features.prev_diff_1)}枚)`);
        else if (p.features.prev_diff_1 > 1000) reasons.push(`前日好調 (${Math.round(p.features.prev_diff_1)}枚)`);
        
        if (p.features.cons_neg >= 2) reasons.push(`${p.features.cons_neg}日連続凹み`);
        if (p.features.island_avg_prev_1 > 500) reasons.push(`所属島が前日好調`);
        if (p.features.is_event_day === 1) reasons.push(`明日はイベント日`);
        if (p.features.position === 0) reasons.push(`角台`);
        if (p.features.position === 1) reasons.push(`角2`);
        if (p.features.position === 2) reasons.push(`角3`);
        
        let reasonHtml = reasons.map(r => `<span style="background:var(--bg-main); padding:2px 6px; border-radius:4px; font-size:0.8rem; margin-right:4px; display:inline-block; margin-bottom:4px;">${r}</span>`).join('');
        if (!reasonHtml) reasonHtml = '<span style="color:var(--text-muted); font-size:0.8rem;">特筆すべき特徴なし</span>';
        
        let rankHtml = `<span style="display:inline-block; width:24px; height:24px; line-height:24px; text-align:center; border-radius:50%; background:rgba(59,130,246,0.2); color:var(--accent-blue); font-weight:bold;">${index+1}</span>`;
        if (index === 0) rankHtml = `<span style="display:inline-block; width:24px; height:24px; line-height:24px; text-align:center; border-radius:50%; background:gold; color:#000; font-weight:bold;">1</span>`;
        if (index === 1) rankHtml = `<span style="display:inline-block; width:24px; height:24px; line-height:24px; text-align:center; border-radius:50%; background:silver; color:#000; font-weight:bold;">2</span>`;
        if (index === 2) rankHtml = `<span style="display:inline-block; width:24px; height:24px; line-height:24px; text-align:center; border-radius:50%; background:#cd7f32; color:#fff; font-weight:bold;">3</span>`;

        tr.innerHTML = `
            <td style="padding: 10px; text-align: center;">${rankHtml}</td>
            <td style="padding: 10px; font-weight: bold; font-size: 1.1rem;">${p.machine}</td>
            <td style="padding: 10px; color: ${probColor}; font-weight: bold;">${prob.toFixed(1)}%</td>
            <td style="padding: 10px; color: ${diffColor}; font-weight: bold;">${Math.round(diff)} 枚</td>
            <td style="padding: 10px;">${reasonHtml}</td>
        `;
        tbody.appendChild(tr);
    });
}'''

content = content.replace(old_func, new_func)

with open('docs/ogiya/app.js', 'w', encoding='utf-8') as f:
    f.write(content)
print("app.js updated.")
