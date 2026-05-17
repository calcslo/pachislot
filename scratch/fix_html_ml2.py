import sys
import re

with open('docs/ogiya/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove the garbage buttons from event-filter
content = re.sub(r'(\s*<button class=\"nav-btn\" data-target=\"period-analysis-section\".*?明日の狙い台予想</button>\n\s*</div>)', r'\n            </div>', content, flags=re.DOTALL)

# 2. Put #ml-next-day-container back into #ml-analysis-section
new_next_day = '''                <!-- Next Day Prediction Container -->
                <div id="ml-next-day-container" class="glass-panel" style="margin-bottom: 2rem; border-color: var(--accent-blue); display: none;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:1rem;">
                        <div>
                            <h3 style="display:flex; align-items:center; gap:0.5rem; color:var(--accent-blue); margin-bottom: 0.5rem;">
                                AIによる高設定推測ランキング
                            </h3>
                            <p class="section-note" style="margin-bottom:1rem;">
                                最新日の状態と過去7日間の傾向をもとに、各台の翌日の高設定確率と予想差枚を算出しました。
                            </p>
                            <div id="ml-next-day-info" style="font-weight:bold; margin-bottom:1rem; font-size:1.1rem; color: var(--text-main);">
                                <!-- Injected by JS -->
                            </div>
                        </div>
                        
                        <div style="background:var(--card-bg); padding:1rem; border-radius:8px; border:1px solid rgba(16,185,129,0.3); min-width:200px;">
                            <div style="font-size:0.8rem; color:var(--text-muted); margin-bottom:0.5rem;">このモデルの過去データでの実績</div>
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.3rem;">
                                <span>的中率 (設定4以上):</span>
                                <span id="ml-next-day-hit-rate" style="font-weight:bold; color:#10b981; font-size:1.1rem;">-</span>
                            </div>
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <span>予想台の平均差枚:</span>
                                <span id="ml-next-day-avg-diff" style="font-weight:bold; color:#fbbf24; font-size:1.1rem;">-</span>
                            </div>
                            <div style="font-size:0.7rem; color:var(--text-muted); margin-top:0.3rem;">※過去のテストデータでのAI予想スコア上位群の実績値です</div>
                        </div>
                    </div>
                    
                    <div class="table-container" style="max-height: 500px; overflow-y: auto; margin-top: 1rem;">
                        <table id="ml-next-day-table" style="width: 100%; border-collapse: collapse; text-align: left;">
                            <thead>
                                <tr style="background: var(--bg-main); color: var(--text-muted); font-size: 0.9rem;">
                                    <th style="padding: 10px; border-bottom: 1px solid var(--glass-border);">ランキング</th>
                                    <th style="padding: 10px; border-bottom: 1px solid var(--glass-border);">台番号</th>
                                    <th style="padding: 10px; border-bottom: 1px solid var(--glass-border);">高設定確率</th>
                                    <th style="padding: 10px; border-bottom: 1px solid var(--glass-border);">予想差枚</th>
                                    <th style="padding: 10px; border-bottom: 1px solid var(--glass-border);">AIが重視した主な理由 (前日状態)</th>
                                </tr>
                            </thead>
                            <tbody id="ml-next-day-tbody"></tbody>
                        </table>
                    </div>
                </div>'''

content = re.sub(r'<!-- 7\. Next Day Prediction Section -->.*?</section>', '', content, flags=re.DOTALL)

# Insert the next-day container back into ml-analysis-section before ML Controls
content = content.replace('<!-- ML Controls -->', new_next_day + '\n\n                <!-- ML Controls -->')

# Also remove the rogue button from main-nav
content = re.sub(r'\s*<button class=\"nav-btn\" data-section=\"next-day-prediction-section\".*?</button>', '', content)

with open('docs/ogiya/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('HTML UI fixed.')
