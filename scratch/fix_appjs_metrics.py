import sys

with open('docs/ogiya/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

old_metrics = '''    // Metrics
    const mLabel = document.getElementById('ml-stat-metric-label');
    const mVal = document.getElementById('ml-stat-metric-val');
    const mDesc = document.getElementById('ml-stat-metric-desc');
    if (currentMlTarget === 'regression') {
        mLabel.textContent = '決定係数 (R²)';
        mVal.textContent = res.cv_r2 !== undefined ? res.cv_r2.toFixed(4) : '-';
        if (mDesc) mDesc.textContent = '1に近いほど予測精度が高く、0以下は「平均で予測した方がマシ」な状態（新しい発見がない）を示します。';
    } else {
        mLabel.textContent = 'F1スコア (精度)';
        mVal.textContent = res.cv_f1 !== undefined ? res.cv_f1.toFixed(4) : '-';
        if (mDesc) mDesc.textContent = '1に近いほど「高設定を正確に見抜けている」ことを示します。';
    }'''

new_metrics = '''    // Metrics
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

content = content.replace(old_metrics, new_metrics)

with open('docs/ogiya/app.js', 'w', encoding='utf-8') as f:
    f.write(content)
print("app.js metrics fixed.")
