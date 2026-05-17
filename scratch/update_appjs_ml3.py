import sys
import re

with open('docs/ogiya/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

old_tree_block = '''        } else {
            // Translate conditions
            let label = content;
            label = label.replace(/is_event_day\s*<=\s*0\.50/, '<span style="color:#60a5fa; font-weight:bold;">イベント日</span> が <span style="color:#fbbf24;">ない(0)</span>')
                         .replace(/is_event_day\s*>\s*0\.50/, '<span style="color:#60a5fa; font-weight:bold;">イベント日</span> が <span style="color:#fbbf24;">ある(1)</span>')
                         
                         .replace(/weekday\s*<=\s*4\.50/, '<span style="color:#60a5fa; font-weight:bold;">曜日</span> が <span style="color:#fbbf24;">平日 (月〜金)</span>')
                         .replace(/weekday\s*>\s*4\.50/, '<span style="color:#60a5fa; font-weight:bold;">曜日</span> が <span style="color:#fbbf24;">週末 (土日)</span>')
                         .replace(/weekday\s*<=\s*2\.50/, '<span style="color:#60a5fa; font-weight:bold;">曜日</span> が <span style="color:#fbbf24;">週前半 (月〜水)</span>')
                         .replace(/weekday\s*>\s*2\.50/, '<span style="color:#60a5fa; font-weight:bold;">曜日</span> が <span style="color:#fbbf24;">週後半 (木〜日)</span>')
                         
                         .replace(/prev_setting\s*<=\s*0\.00/, '<span style="color:#60a5fa; font-weight:bold;">前日推定設定</span> が <span style="color:#fbbf24;">不明(0以下)</span>')
                         .replace(/prev_setting\s*>\s*0\.00/, '<span style="color:#60a5fa; font-weight:bold;">前日推定設定</span> が <span style="color:#fbbf24;">推測可能(1以上)</span>')
                         
                         .replace(/cons_pos/, '<span style="color:#60a5fa; font-weight:bold;">連続凸日数</span>')
                         .replace(/cons_neg/, '<span style="color:#60a5fa; font-weight:bold;">連続凹み日数</span>')
                         .replace(/prev_diff/, '<span style="color:#60a5fa; font-weight:bold;">前日差枚</span>')
                         .replace(/island_avg_prev/, '<span style="color:#60a5fa; font-weight:bold;">島の前日平均差枚</span>')
                         .replace(/tail_digit/, '<span style="color:#60a5fa; font-weight:bold;">台番号末尾</span>')
                         .replace(/day_of_month/, '<span style="color:#60a5fa; font-weight:bold;">月内日付(〇日)</span>')
                         .replace(/position/, '<span style="color:#60a5fa; font-weight:bold;">角からの位置</span>')
                         
                         .replace(/<=\s*([\d\.\-]+)/, (match, p1) => {
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

new_tree_block = '''        } else {
            // Translate conditions
            let label = content;
            
            // First, translate feature names dynamically
            if (globalMlResults && globalMlResults.feature_names_jp) {
                // Sort keys by length descending to prevent partial replacements (e.g. prev_diff_10 before prev_diff_1)
                const sortedKeys = Object.keys(globalMlResults.feature_names_jp).sort((a, b) => b.length - a.length);
                for (const key of sortedKeys) {
                    const name = globalMlResults.feature_names_jp[key];
                    label = label.replace(new RegExp(key, 'g'), name);
                }
            }
            
            // Then do value replacement based on translated Japanese strings
            label = label.replace(/<=\s*([\d\.\-]+)/, (match, p1) => {
                             let v = parseFloat(p1);
                             if (label.includes('差枚')) {
                                 v = Math.round(v / 100) * 100;
                                 return ` が <span style="color:#fbbf24;">約 ${v} 枚 以下</span>`;
                             } else if (label.includes('曜日') || label.includes('連続') || label.includes('設定')) {
                                 v = Math.round(v);
                                 return ` が <span style="color:#fbbf24;">${v} 以下</span>`;
                             } else if (label.includes('ゲーム')) {
                                 v = Math.round(v / 100) * 100;
                                 return ` が <span style="color:#fbbf24;">約 ${v} G 以下</span>`;
                             } else if (label.includes('イベント')) {
                                 return ` が <span style="color:#fbbf24;">ない(0)</span>`;
                             }
                             return ` が <span style="color:#fbbf24;">${v.toFixed(1).replace('.0','')} 以下</span>`;
                         })
                         .replace(/>\s*([\d\.\-]+)/, (match, p1) => {
                             let v = parseFloat(p1);
                             if (label.includes('差枚')) {
                                 v = Math.round(v / 100) * 100;
                                 return ` が <span style="color:#fbbf24;">約 ${v} 枚 超過</span>`;
                             } else if (label.includes('曜日') || label.includes('連続') || label.includes('設定')) {
                                 v = Math.round(v);
                                 return ` が <span style="color:#fbbf24;">${v} 超過</span>`;
                             } else if (label.includes('ゲーム')) {
                                 v = Math.round(v / 100) * 100;
                                 return ` が <span style="color:#fbbf24;">約 ${v} G 超過</span>`;
                             } else if (label.includes('イベント')) {
                                 return ` が <span style="color:#fbbf24;">ある(1)</span>`;
                             }
                             return ` が <span style="color:#fbbf24;">${v.toFixed(1).replace('.0','')} 超過</span>`;
                         });
                         
            // Wrap the feature name part with bold blue span (everything before ' が ')
            if (label.includes(' が ')) {
                const parts = label.split(' が ');
                label = `<span style="color:#60a5fa; font-weight:bold;">${parts[0]}</span> が ${parts.slice(1).join(' が ')}`;
            }'''

if old_tree_block not in content:
    old_tree_block = old_tree_block.replace('\n', '\r\n')
    new_tree_block = new_tree_block.replace('\n', '\r\n')
    if old_tree_block not in content:
        print("Target block not found!")
        sys.exit(1)

content = content.replace(old_tree_block, new_tree_block)

with open('docs/ogiya/app.js', 'w', encoding='utf-8') as f:
    f.write(content)
print("app.js updated.")
