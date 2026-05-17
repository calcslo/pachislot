import sys

with open('docs/ogiya/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

old_stats = '''        if (res.tn_ratio !== undefined) {
            confWrap.style.display = 'block';
            document.getElementById('ml-stat-tn').textContent = (res.tn_ratio * 100).toFixed(1) + '%';
            document.getElementById('ml-stat-fp').textContent = (res.fp_ratio * 100).toFixed(1) + '%';
            document.getElementById('ml-stat-fn').textContent = (res.fn_ratio * 100).toFixed(1) + '%';
            document.getElementById('ml-stat-tp').textContent = (res.tp_ratio * 100).toFixed(1) + '%';
        } else {
            confWrap.style.display = 'none';
        }'''

new_stats = '''        if (res.cls_rf && res.cls_rf.tn_ratio !== undefined) {
            confWrap.style.display = 'block';
            document.getElementById('ml-stat-tn').textContent = (res.cls_rf.tn_ratio * 100).toFixed(1) + '%';
            document.getElementById('ml-stat-fp').textContent = (res.cls_rf.fp_ratio * 100).toFixed(1) + '%';
            document.getElementById('ml-stat-fn').textContent = (res.cls_rf.fn_ratio * 100).toFixed(1) + '%';
            document.getElementById('ml-stat-tp').textContent = (res.cls_rf.tp_ratio * 100).toFixed(1) + '%';
        } else {
            confWrap.style.display = 'none';
        }'''

content = content.replace(old_stats, new_stats)

with open('docs/ogiya/app.js', 'w', encoding='utf-8') as f:
    f.write(content)
