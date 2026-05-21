import os

filepath = 'docs/ogiya/app.js'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target1 = """        let nlReason = `<div style="margin:4px 0 8px 0; font-size:0.85rem; line-height:1.6; color:var(--text-main);">`;
        nlReason += `<strong>AIによる高設定（${prob.toFixed(1)}%）推測の根拠：</strong><ul style="margin-top:4px; padding-left:20px;">`;
        if (f.cons_neg >= 2) nlReason += `<li>現在 <b>${f.cons_neg}日連続で凹んで</b> おり、反発の期待値が高まっています。</li>`;
        if (f.neg_after_pos === 1 || f.setting_change_signal === 1) nlReason += `<li>前日に <b>高設定挙動（推定4以上）を見せながら不発（マイナス終了）</b> だったため、据え置きでの出玉が狙い目です。</li>`;
        if (f.prev_diff_1 != null) {
            if (f.prev_diff_1 > 1500) nlReason += `<li>前日は <b>+${Math.round(f.prev_diff_1)}枚</b> と非常に好調で、勢いが持続する可能性があります。</li>`;
            else if (f.prev_diff_1 < -1500) nlReason += `<li>前日は <b>${Math.round(f.prev_diff_1)}枚</b> と大きく凹んでおり、設定上げや反発の兆しがあります。</li>`;
        }
        if (f.cumul_14d_diff != null && f.cumul_14d_diff < -4000) nlReason += `<li>過去14日間の合計が <b>${Math.round(f.cumul_14d_diff)}枚</b> と大きく沈んでおり、そろそろ回収が終わるフェーズです。</li>`;
        else if (f.cumul_7d_diff != null && f.cumul_7d_diff < -2000) nlReason += `<li>過去7日間の合計が <b>${Math.round(f.cumul_7d_diff)}枚</b> のマイナスで、還元される確率が高いです。</li>`;
        if (f.island_trend != null && f.island_trend > 500) nlReason += `<li>この台が属する島全体が直近3日間で <b>平均+${Math.round(f.island_trend)}枚</b> と活気づいており、島単位での高設定投入が疑われます。</li>`;
        if (f.island_high_ratio_3d != null && f.island_high_ratio_3d > 0.4) nlReason += `<li>過去3日間の <b>同じ島の高設定比率が${(f.island_high_ratio_3d*100).toFixed(1)}%</b> と非常に高く、全台系・対象島の可能性があります。</li>`;
        if (f.store_high_ratio != null && f.store_high_ratio > 0.4) nlReason += `<li>店舗全体の高設定比率が <b>${(f.store_high_ratio*100).toFixed(1)}%</b> と高く、店舗全体のベース設定が高い状況です。</li>`;
        if (f.adj_avg_diff_1 != null && f.adj_avg_diff_1 > 1000) nlReason += `<li>前日に <b>両隣の台が平均+${Math.round(f.adj_avg_diff_1)}枚</b> と大きく出ており、並びでの高設定（塊）の可能性があります。</li>`;
        else if (f.adj_left_diff_1 != null && f.adj_left_diff_1 > 1500) nlReason += `<li>前日に <b>左隣の台が+${Math.round(f.adj_left_diff_1)}枚</b> と爆発しており、並びでの高設定（塊）の可能性があります。</li>`;
        else if (f.adj_right_diff_1 != null && f.adj_right_diff_1 > 1500) nlReason += `<li>前日に <b>右隣の台が+${Math.round(f.adj_right_diff_1)}枚</b> と爆発しており、並びでの高設定（塊）の可能性があります。</li>`;
        if (f.is_event_day === 1) nlReason += `<li>明日は <b>特定日(3,5,8の付く日)</b> のため、高設定投入率のベースが上がります。</li>`;
        if (f.position === 0) nlReason += `<li><b>角台</b> という配置的な強みがあり、見せ台として選ばれる傾向があります。</li>`;
        if (f.same_wd_avg_diff != null && f.same_wd_avg_diff > 500) nlReason += `<li>過去4週の <b>${dayStr}</b> は平均+${Math.round(f.same_wd_avg_diff)}枚と、この曜日に強い実績があります。</li>`;
        if (nlReason.indexOf('<li>') === -1) nlReason += `<li>複数の細かな指標（移動平均やボラティリティ等）が複合的に作用し、AIが高評価を与えています。</li>`;
        nlReason += `</ul></div>`;"""

replacement1 = """        let reasons = [];
        if (f.cons_neg >= 2) reasons.push(`現在 <b>${f.cons_neg}日連続で凹んで</b> おり、反発の期待値が高まっています。`);
        if (f.neg_after_pos === 1 || f.setting_change_signal === 1) reasons.push(`前日に <b>高設定挙動（推定4以上）を見せながら不発（マイナス終了）</b> だったため、据え置きでの出玉が狙い目です。`);
        if (f.prev_diff_1 != null) {
            if (f.prev_diff_1 > 1500) reasons.push(`前日は <b>+${Math.round(f.prev_diff_1)}枚</b> と非常に好調で、勢いが持続する可能性があります。`);
            else if (f.prev_diff_1 < -1500) reasons.push(`前日は <b>${Math.round(f.prev_diff_1)}枚</b> と大きく凹んでおり、設定上げや反発の兆しがあります。`);
        }
        if (f.cumul_14d_diff != null && f.cumul_14d_diff < -4000) reasons.push(`過去14日間の合計が <b>${Math.round(f.cumul_14d_diff)}枚</b> と大きく沈んでおり、そろそろ回収が終わるフェーズです。`);
        else if (f.cumul_7d_diff != null && f.cumul_7d_diff < -2000) reasons.push(`過去7日間の合計が <b>${Math.round(f.cumul_7d_diff)}枚</b> のマイナスで、還元される確率が高いです。`);
        if (f.island_trend != null && f.island_trend > 500) reasons.push(`この台が属する島全体が直近3日間で <b>平均+${Math.round(f.island_trend)}枚</b> と活気づいており、島単位での高設定投入が疑われます。`);
        if (f.island_high_ratio_3d != null && f.island_high_ratio_3d > 0.4) reasons.push(`過去3日間の <b>同じ島の高設定比率が${(f.island_high_ratio_3d*100).toFixed(1)}%</b> と非常に高く、全台系・対象島の可能性があります。`);
        if (f.store_high_ratio != null && f.store_high_ratio > 0.4) reasons.push(`店舗全体の高設定比率が <b>${(f.store_high_ratio*100).toFixed(1)}%</b> と高く、店舗全体のベース設定が高い状況です。`);
        if (f.adj_avg_diff_1 != null && f.adj_avg_diff_1 > 1000) reasons.push(`前日に <b>両隣の台が平均+${Math.round(f.adj_avg_diff_1)}枚</b> と大きく出ており、並びでの高設定（塊）の可能性があります。`);
        else if (f.adj_left_diff_1 != null && f.adj_left_diff_1 > 1500) reasons.push(`前日に <b>左隣の台が+${Math.round(f.adj_left_diff_1)}枚</b> と爆発しており、並びでの高設定（塊）の可能性があります。`);
        else if (f.adj_right_diff_1 != null && f.adj_right_diff_1 > 1500) reasons.push(`前日に <b>右隣の台が+${Math.round(f.adj_right_diff_1)}枚</b> と爆発しており、並びでの高設定（塊）の可能性があります。`);
        if (f.is_event_day === 1) reasons.push(`明日は <b>特定日(3,5,8の付く日)</b> のため、高設定投入率のベースが上がります。`);
        if (f.position === 0) reasons.push(`<b>角台</b> という配置的な強みがあり、見せ台として選ばれる傾向があります。`);
        if (f.same_wd_avg_diff != null && f.same_wd_avg_diff > 500) reasons.push(`過去4週の <b>${dayStr}</b> は平均+${Math.round(f.same_wd_avg_diff)}枚と、この曜日に強い実績があります。`);
        if (reasons.length === 0) reasons.push(`複数の細かな指標（移動平均やボラティリティ等）が複合的に作用し、AIが高評価を与えています。`);

        const reasonToggleId = `pred-reason-more-${index}`;
        let nlReason = `<div style="margin:4px 0 8px 0; font-size:0.85rem; line-height:1.6; color:var(--text-main);">`;
        nlReason += `<strong>AIによる高設定（${prob.toFixed(1)}%）推測の根拠：</strong><ul style="margin-top:4px; padding-left:20px;">`;
        if (reasons.length > 0) nlReason += `<li>${reasons[0]}</li>`;
        if (reasons.length > 1) {
            nlReason += `<div id="${reasonToggleId}" style="display:none;">`;
            for (let i = 1; i < reasons.length; i++) nlReason += `<li>${reasons[i]}</li>`;
            nlReason += `</div>`;
        }
        nlReason += `</ul></div>`;"""

target2 = """            <td style="padding:8px 10px;vertical-align:top;border-bottom: 1px solid var(--glass-border);">
                ${nlReason}
                <div style="margin-top:4px;">
                    <button onclick="togglePredDetail('${detailId}')" style="padding:4px 12px;border-radius:4px;border:1px solid rgba(16,185,129,0.5);background:rgba(16,185,129,0.1);color:#10b981;font-size:0.8rem;cursor:pointer;transition:all 0.2s;font-weight:bold;">
                        AIが読み込んだ詳細数値データを見る
                    </button>
                </div>
                <div id="${detailId}" style="display:none;margin-top:10px;background:var(--bg-main);border-radius:6px;padding:8px;border:1px solid var(--glass-border);">
                    <div style="max-height:200px;overflow-y:auto;">
                        <table style="border-collapse:collapse;width:100%;">${detailRows}</table>
                    </div>
                </div>
            </td>"""

replacement2 = """            <td style="padding:8px 10px;vertical-align:top;border-bottom: 1px solid var(--glass-border);">
                ${nlReason}
                <div style="margin-top:4px; display:flex; gap:8px; flex-wrap:wrap;">
                    ${reasons.length > 1 ? `<button onclick="togglePredDetail('${reasonToggleId}', this)" style="padding:4px 12px;border-radius:4px;border:1px solid rgba(96,165,250,0.5);background:rgba(96,165,250,0.1);color:#60a5fa;font-size:0.8rem;cursor:pointer;transition:all 0.2s;font-weight:bold;">他の理由も見る ▼</button>` : ''}
                    <button onclick="togglePredDetail('${detailId}', this)" style="padding:4px 12px;border-radius:4px;border:1px solid rgba(16,185,129,0.5);background:rgba(16,185,129,0.1);color:#10b981;font-size:0.8rem;cursor:pointer;transition:all 0.2s;font-weight:bold;">
                        数値データを見る ▼
                    </button>
                </div>
                <div id="${detailId}" style="display:none;margin-top:10px;background:var(--bg-main);border-radius:6px;padding:8px;border:1px solid var(--glass-border);">
                    <div style="max-height:200px;overflow-y:auto;">
                        <table style="border-collapse:collapse;width:100%;">${detailRows}</table>
                    </div>
                </div>
            </td>"""

target3 = """function togglePredDetail(id) {
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
}"""

replacement3 = """function togglePredDetail(id, btnEl) {
    const el = document.getElementById(id);
    if (!el) return;
    if (!btnEl && el.previousElementSibling) {
        btnEl = el.previousElementSibling.querySelector('button');
    }
    if (el.style.display === 'none') {
        el.style.display = 'block';
        if (btnEl) {
            if (btnEl.textContent.includes('他の理由')) btnEl.textContent = '他の理由を隠す ▲';
            else btnEl.textContent = '数値データを隠す ▲';
        }
    } else {
        el.style.display = 'none';
        if (btnEl) {
            if (btnEl.textContent.includes('他の理由')) btnEl.textContent = '他の理由も見る ▼';
            else btnEl.textContent = '数値データを見る ▼';
        }
    }
}"""

def do_replace(tgt, rep):
    global content
    if tgt in content:
        content = content.replace(tgt, rep)
        return True
    elif tgt.replace('\\n', '\\r\\n') in content:
        content = content.replace(tgt.replace('\\n', '\\r\\n'), rep.replace('\\n', '\\r\\n'))
        return True
    return False

c1 = do_replace(target1, replacement1)
c2 = do_replace(target2, replacement2)
c3 = do_replace(target3, replacement3)

print('Replace status:', c1, c2, c3)

if c1 and c2 and c3:
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Successfully updated file.')
else:
    print('Failed to replace one or more targets.')
