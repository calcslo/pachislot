import re

with open('docs/ogiya/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update formatTreeRules to handle categories
old_format = r'''            // Then do value replacement based on translated Japanese strings
            label = label.replace(/<=\s*([\d\.\-]+)/, (match, p1) => \{
                             let v = parseFloat\(p1\);
                             if \(label.includes\('差枚'\)\) \{
                                 v = Math.round\(v / 100\) \* 100;
                                 return ` が <span style="color:#fbbf24;">約 \$\{v\} 枚 以下</span>`;
                             \} else if \(label.includes\('曜日'\) \|\| label.includes\('連続'\) \|\| label.includes\('設定'\)\) \{
                                 v = Math.round\(v\);
                                 return ` が <span style="color:#fbbf24;">\$\{v\} 以下</span>`;
                             \} else if \(label.includes\('ゲーム'\)\) \{
                                 v = Math.round\(v / 100\) \* 100;
                                 return ` が <span style="color:#fbbf24;">約 \$\{v\} G 以下</span>`;
                             \}
                             return ` が <span style="color:#fbbf24;">約 \$\{v\} 以下</span>`;
                         \}\);
            
            label = label.replace(/>\s*([\d\.\-]+)/, (match, p1) => \{
                             let v = parseFloat\(p1\);
                             if \(label.includes\('差枚'\)\) \{
                                 v = Math.round\(v / 100\) \* 100;
                                 return ` が <span style="color:#fbbf24;">約 \$\{v\} 枚 超過</span>`;
                             \} else if \(label.includes\('曜日'\) \|\| label.includes\('連続'\) \|\| label.includes\('設定'\)\) \{
                                 v = Math.round\(v\);
                                 return ` が <span style="color:#fbbf24;">\$\{v\} 超過</span>`;
                             \} else if \(label.includes\('ゲーム'\)\) \{
                                 v = Math.round\(v / 100\) \* 100;
                                 return ` が <span style="color:#fbbf24;">約 \$\{v\} G 超過</span>`;
                             \}
                             return ` が <span style="color:#fbbf24;">約 \$\{v\} 超過</span>`;
                         \}\);'''

new_format = r'''            // Then do value replacement based on translated Japanese strings
            if (label.includes('曜日')) {
                const dayNames = ['月', '火', '水', '木', '金', '土', '日'];
                label = label.replace(/<=\s*([\d\.\-]+)/, (m, p1) => {
                    let v = Math.floor(parseFloat(p1));
                    if (v < 0) v = 0; if (v > 6) v = 6;
                    const days = dayNames.slice(0, v + 1).join('・');
                    return ` が <span style="color:#fbbf24;">${days}曜日</span>`;
                });
                label = label.replace(/>\s*([\d\.\-]+)/, (m, p1) => {
                    let v = Math.floor(parseFloat(p1));
                    if (v < 0) v = 0; if (v > 6) v = 6;
                    const days = dayNames.slice(v + 1).join('・');
                    return ` が <span style="color:#fbbf24;">${days}曜日</span>`;
                });
            } else if (label.includes('所属島ID')) {
                label = label.replace(/<=\s*([\d\.\-]+)/, (m, p1) => {
                    return ` が <span style="color:#fbbf24;">${Math.floor(parseFloat(p1))} グループ以下</span>`;
                });
                label = label.replace(/>\s*([\d\.\-]+)/, (m, p1) => {
                    return ` が <span style="color:#fbbf24;">${Math.floor(parseFloat(p1))} グループより大きい</span>`;
                });
            } else if (label.includes('角からの位置')) {
                const posNames = ['角', '角2', '角3', 'その他(内側)'];
                label = label.replace(/<=\s*([\d\.\-]+)/, (m, p1) => {
                    let v = Math.floor(parseFloat(p1));
                    if (v < 0) v = 0; if (v > 3) v = 3;
                    const pos = posNames.slice(0, v + 1).join('・');
                    return ` が <span style="color:#fbbf24;">${pos}</span>`;
                });
                label = label.replace(/>\s*([\d\.\-]+)/, (m, p1) => {
                    let v = Math.floor(parseFloat(p1));
                    if (v < 0) v = 0; if (v > 3) v = 3;
                    const pos = posNames.slice(v + 1).join('・');
                    return ` が <span style="color:#fbbf24;">${pos}</span>`;
                });
            } else {
                label = label.replace(/<=\s*([\d\.\-]+)/, (match, p1) => {
                     let v = parseFloat(p1);
                     if (label.includes('差枚')) {
                         v = Math.round(v / 100) * 100;
                         return ` が <span style="color:#fbbf24;">約 ${v} 枚 以下</span>`;
                     } else if (label.includes('連続') || label.includes('設定')) {
                         v = Math.round(v);
                         return ` が <span style="color:#fbbf24;">${v} 以下</span>`;
                     } else if (label.includes('ゲーム')) {
                         v = Math.round(v / 100) * 100;
                         return ` が <span style="color:#fbbf24;">約 ${v} G 以下</span>`;
                     }
                     return ` が <span style="color:#fbbf24;">約 ${Math.round(v)} 以下</span>`;
                 });
                
                label = label.replace(/>\s*([\d\.\-]+)/, (match, p1) => {
                     let v = parseFloat(p1);
                     if (label.includes('差枚')) {
                         v = Math.round(v / 100) * 100;
                         return ` が <span style="color:#fbbf24;">約 ${v} 枚 超過</span>`;
                     } else if (label.includes('連続') || label.includes('設定')) {
                         v = Math.round(v);
                         return ` が <span style="color:#fbbf24;">${v} 超過</span>`;
                     } else if (label.includes('ゲーム')) {
                         v = Math.round(v / 100) * 100;
                         return ` が <span style="color:#fbbf24;">約 ${v} G 超過</span>`;
                     }
                     return ` が <span style="color:#fbbf24;">約 ${Math.round(v)} 超過</span>`;
                 });
            }'''

# 2. Update renderNextDayPredictions for Natural Language detail explanation
old_detail = r'''        let detailRows = Object.entries\(f\).map\(\(\[k, v\]\) => \{
            const name = featureNames\[k\] \|\| k;
            let vStr = \(typeof v === 'number' && !Number.isInteger\(v\)\) \? v.toFixed\(1\) : v;
            return `<tr><td style="padding:2px 8px;color:var\(--text-muted\);font-size:0.78rem;white-space:nowrap;">\$\{name\}</td><td style="padding:2px 8px;font-size:0.78rem;font-weight:bold;">\$\{vStr\}</td></tr>`;
        \}\).join\(''\);

        tr.innerHTML = `
            <td style="padding:8px 10px;text-align:center;vertical-align:middle;">\$\{rankBadge\}</td>
            <td style="padding:8px 10px;font-weight:bold;font-size:1.05rem;vertical-align:middle;white-space:nowrap;">\$\{p.machine\}</td>
            <td style="padding:8px 10px;color:\$\{probColor\};font-weight:bold;font-size:1.05rem;vertical-align:middle;white-space:nowrap;">\$\{prob.toFixed\(1\)\}%</td>
            <td style="padding:8px 10px;color:\$\{diffColor\};font-weight:bold;vertical-align:middle;white-space:nowrap;">\$\{diff >= 0 \? '\+' : ''\}\$\{Math.round\(diff\)\}枚</td>
            <td style="padding:8px 10px;vertical-align:middle;">
                <div style="display:flex;flex-wrap:wrap;align-items:center;gap:2px;">\$\{reasonHtml\}\$\{detailBtn\}</div>
                <div id="\$\{detailId\}" style="display:none;margin-top:8px;background:var\(--bg-main\);border-radius:6px;padding:4px;border:1px solid var\(--glass-border\);">
                    <table style="border-collapse:collapse;width:100%;">\$\{detailRows\}</table>
                </div>
            </td>
        `;'''

new_detail = r'''        const dayNames = ['月', '火', '水', '木', '金', '土', '日'];
        const dayStr = dayNames[f.weekday] ? dayNames[f.weekday] + '曜' : '';
        const posNames = ['角', '角2', '角3', 'その他(内側)'];
        const posStr = posNames[f.position] || '';
        
        let nlReason = `<p style="margin:4px 0 8px 0; font-size:0.85rem; line-height:1.4;">`;
        nlReason += `この台が高設定（確率${prob.toFixed(1)}%）と推測された主な理由です：<br>`;
        if (f.cons_neg >= 2) nlReason += `・現在 <b>${f.cons_neg}日連続で凹んで</b> います。<br>`;
        if (f.neg_after_pos === 1) nlReason += `・前日は <b>高設定挙動（推定4以上）でしたが不発（マイナス終了）</b> でした。<br>`;
        if (f.prev_diff_1 != null) {
            if (f.prev_diff_1 > 1000) nlReason += `・前日は <b>+${Math.round(f.prev_diff_1)}枚</b> と好調に出ています。<br>`;
            else if (f.prev_diff_1 < -1000) nlReason += `・前日は <b>${Math.round(f.prev_diff_1)}枚</b> と大きく凹んでいます。<br>`;
        }
        if (f.cumul_7d_diff != null && f.cumul_7d_diff < -3000) nlReason += `・過去7日間の合計が <b>${Math.round(f.cumul_7d_diff)}枚</b> と沈んでおり、反発が期待されます。<br>`;
        if (f.island_trend != null && f.island_trend > 500) nlReason += `・この台が属する島全体が、直近3日間 <b>平均+${Math.round(f.island_trend)}枚</b> と活気づいています。<br>`;
        if (f.is_event_day === 1) nlReason += `・明日は <b>イベント日(3,5,8の付く日)</b> のため、ベース設定の底上げが見込めます。<br>`;
        if (f.position === 0) nlReason += `・<b>角台</b> という配置的な強みがあります。<br>`;
        if (dayStr) nlReason += `・明日の <b>${dayStr}</b> の傾向に合致しています。<br>`;
        nlReason += `</p>`;
        
        let detailRows = Object.entries(f).map(([k, v]) => {
            const name = featureNames[k] || k;
            let vStr = v;
            if (k === 'weekday') vStr = dayNames[v] || v;
            else if (k === 'position') vStr = posNames[v] || v;
            else if (typeof v === 'number' && !Number.isInteger(v)) vStr = v.toFixed(1);
            return `<tr><td style="padding:2px 8px;color:var(--text-muted);font-size:0.75rem;white-space:nowrap;border-bottom:1px solid rgba(255,255,255,0.02);">${name}</td><td style="padding:2px 8px;font-size:0.75rem;font-weight:bold;border-bottom:1px solid rgba(255,255,255,0.02);">${vStr}</td></tr>`;
        }).join('');

        tr.innerHTML = `
            <td style="padding:8px 10px;text-align:center;vertical-align:middle;">${rankBadge}</td>
            <td style="padding:8px 10px;font-weight:bold;font-size:1.05rem;vertical-align:middle;white-space:nowrap;">${p.machine}</td>
            <td style="padding:8px 10px;color:${probColor};font-weight:bold;font-size:1.05rem;vertical-align:middle;white-space:nowrap;">${prob.toFixed(1)}%</td>
            <td style="padding:8px 10px;color:${diffColor};font-weight:bold;vertical-align:middle;white-space:nowrap;">${diff >= 0 ? '+' : ''}${Math.round(diff)}枚</td>
            <td style="padding:8px 10px;vertical-align:middle;">
                <div style="display:flex;flex-wrap:wrap;align-items:center;gap:2px;">${reasonHtml}${detailBtn}</div>
                <div id="${detailId}" style="display:none;margin-top:8px;background:var(--bg-main);border-radius:6px;padding:8px;border:1px solid var(--glass-border);">
                    ${nlReason}
                    <div style="font-size:0.75rem;color:var(--text-muted);margin-bottom:4px;border-top:1px dashed var(--glass-border);padding-top:4px;">▼ AIが読み込んだデータ</div>
                    <div style="max-height:150px;overflow-y:auto;">
                        <table style="border-collapse:collapse;width:100%;">${detailRows}</table>
                    </div>
                </div>
            </td>
        `;'''

content = re.sub(old_format, new_format, content, flags=re.DOTALL)
content = re.sub(old_detail, new_detail, content, flags=re.DOTALL)

with open('docs/ogiya/app.js', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated app.js")
