import sys

with open('docs/ogiya/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix metrics
old_metrics = '''    // Metrics
    const mLabel = document.getElementById('ml-stat-metric-label');
    const mVal = document.getElementById('ml-stat-metric-val');
    const mDesc = document.getElementById('ml-stat-metric-desc');
    if (currentMlTarget === 'regression') {
        mLabel.textContent = '決定係数 (R²)';
        mVal.textContent = (res.regression_rf && res.regression_rf.cv_r2 !== undefined) ? res.regression_rf.cv_r2.toFixed(4) : '-';
        if (mDesc) mDesc.textContent = '1に近いほど予測精度が高く、0以下は「平均で予測した方がマシ」な状態（新しい発見がない）を示します。';
    } else {
        mLabel.textContent = 'F1スコア (精度)';
        mVal.textContent = (res.cls_rf && res.cls_rf.cv_f1 !== undefined) ? res.cls_rf.cv_f1.toFixed(4) : '-';
        if (mDesc) mDesc.textContent = '1に近いほど「高設定を正確に見抜けている」ことを示します。';
    }'''

new_metrics = '''    // Metrics
    const mLabel = document.getElementById('ml-stat-metric-label');
    const mVal = document.getElementById('ml-stat-metric-val');
    const mDesc = document.getElementById('ml-stat-metric-desc');
    if (currentMlTarget === 'regression') {
        mLabel.textContent = '決定係数 (R²)';
        mVal.textContent = (periodData.regression_rf && periodData.regression_rf.cv_r2 !== undefined) ? periodData.regression_rf.cv_r2.toFixed(4) : '-';
        if (mDesc) mDesc.textContent = '1に近いほど予測精度が高く、0以下は「平均で予測した方がマシ」な状態（新しい発見がない）を示します。';
    } else {
        mLabel.textContent = 'F1スコア (精度)';
        mVal.textContent = (periodData.cls_rf && periodData.cls_rf.cv_f1 !== undefined) ? periodData.cls_rf.cv_f1.toFixed(4) : '-';
        if (mDesc) mDesc.textContent = '1に近いほど「高設定を正確に見抜けている」ことを示します。';
    }'''

content = content.replace(old_metrics, new_metrics)

# Fix confusion matrix wrap
old_conf = '''    const confWrap = document.getElementById('ml-stat-confusion-wrap');
    if (currentMlTarget === 'classification') {
        highWrap.style.display = 'block';
        const p = periodData.n_cls > 0 ? ((periodData.n_high / periodData.n_cls) * 100).toFixed(1) : 0;
        document.getElementById('ml-stat-high').textContent = `${(periodData.n_high||0).toLocaleString()} (${p}%)`;
        
        if (res.cls_rf && res.cls_rf.tn_ratio !== undefined) {
            confWrap.style.display = 'block';
            document.getElementById('ml-stat-tn').textContent = (res.cls_rf.tn_ratio * 100).toFixed(1) + '%';
            document.getElementById('ml-stat-fp').textContent = (res.cls_rf.fp_ratio * 100).toFixed(1) + '%';
            document.getElementById('ml-stat-fn').textContent = (res.cls_rf.fn_ratio * 100).toFixed(1) + '%';
            document.getElementById('ml-stat-tp').textContent = (res.cls_rf.tp_ratio * 100).toFixed(1) + '%';
        } else {
            confWrap.style.display = 'none';
        }
    } else {'''

new_conf = '''    const confWrap = document.getElementById('ml-stat-confusion-wrap');
    if (currentMlTarget === 'classification') {
        highWrap.style.display = 'block';
        const p = periodData.n_cls > 0 ? ((periodData.n_high / periodData.n_cls) * 100).toFixed(1) : 0;
        document.getElementById('ml-stat-high').textContent = `${(periodData.n_high||0).toLocaleString()} (${p}%)`;
        
        if (periodData.cls_rf && periodData.cls_rf.tn_ratio !== undefined) {
            confWrap.style.display = 'block';
            document.getElementById('ml-stat-tn').textContent = (periodData.cls_rf.tn_ratio * 100).toFixed(1) + '%';
            document.getElementById('ml-stat-fp').textContent = (periodData.cls_rf.fp_ratio * 100).toFixed(1) + '%';
            document.getElementById('ml-stat-fn').textContent = (periodData.cls_rf.fn_ratio * 100).toFixed(1) + '%';
            document.getElementById('ml-stat-tp').textContent = (periodData.cls_rf.tp_ratio * 100).toFixed(1) + '%';
        } else {
            confWrap.style.display = 'none';
        }
    } else {'''

content = content.replace(old_conf, new_conf)

with open('docs/ogiya/app.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("done")
