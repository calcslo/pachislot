import sys

with open('docs/ogiya/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the old container
old_container = '''                <!-- Next Day Prediction Container -->
                <div id="ml-next-day-container" style="margin-bottom: 2rem; background: var(--card-bg); padding: 1.5rem; border-radius: 8px; border: 1px solid var(--accent-blue); display: none;">
                    <h3 style="display:flex; align-items:center; gap:0.5rem; color:var(--accent-blue); margin-bottom: 0.5rem;">
                        <span style="font-size:1.5rem;">🔮</span> 明日の狙い台予想
                    </h3>
                    <p class="section-note" style="margin-bottom:1rem;">
                        最新日の状態と過去の傾向をもとに、XGBoost (AI) が翌日の高設定確率と予想差枚を算出しました。
                    </p>
                    <div id="ml-next-day-info" style="font-weight:bold; margin-bottom:1rem; font-size:1.1rem; color: var(--text-main);">
                        <!-- Injected by JS -->
                    </div>
                    
                    <div class="table-container" style="max-height: 400px; overflow-y: auto;">
                        <table id="ml-next-day-table" style="width: 100%; border-collapse: collapse; text-align: left;">
                            <thead>
                                <tr style="background: var(--bg-main); color: var(--text-muted); font-size: 0.9rem;">
                                    <th style="padding: 10px; border-bottom: 1px solid var(--glass-border);">台番号</th>
                                    <th style="padding: 10px; border-bottom: 1px solid var(--glass-border);">高設定確率</th>
                                    <th style="padding: 10px; border-bottom: 1px solid var(--glass-border);">予想差枚</th>
                                    <th style="padding: 10px; border-bottom: 1px solid var(--glass-border);">AIが重視した主な理由 (前日状態)</th>
                                </tr>
                            </thead>
                            <tbody id="ml-next-day-tbody"></tbody>
                        </table>
                    </div>
                </div>

                <!-- ML Controls -->'''

content = content.replace(old_container, '''                <!-- ML Controls -->''')

# Insert the new section before Date Detail Modal
new_section = '''            </section>

            <!-- 7. Next Day Prediction Section -->
            <section id="next-day-prediction-section" class="data-section glass-panel" style="display:none;">
                <div class="section-header">
                    <h2>🔮 明日の狙い台予想</h2>
                    <p class="section-desc">XGBoostモデルが過去データから学習し、最新データに基づく明日の予想を算出します。</p>
                </div>
                
                <div id="ml-next-day-container" style="margin-bottom: 2rem;">
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
                </div>
            </section>

    <!-- Date Detail Modal -->'''

content = content.replace('''            </section>

    <!-- Date Detail Modal -->''', new_section)

with open('docs/ogiya/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("done")
