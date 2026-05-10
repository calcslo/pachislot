import random
import matplotlib.pyplot as plt
import numpy as np
import matplotlib

# 日本語フォントの設定（Windows用：MS Gothicを使用）
matplotlib.rc('font', family='MS Gothic')

def simulate_pachinko_advanced(target_machine, days=30, spins_per_day=2000, 
                                rotation_rate=20, initial_budget=200000, iterations=1000):
    """
    パチンコ収支シミュレーション（複数回試行対応版）
    """
    # 機種スペック（ボーダーは4円・等価計算の理論値）
    machines = {
        "e東京喰種": {
            "ts": 399.9, "rush_rate": 0.51, "continuation": 0.75, 
            "payout_avg": 1500, "border": 17.5
        },
        "P沖海6LTP": {
            "ts": 319.7, "rush_rate": 0.50, "continuation": 0.80, 
            "payout_avg": 1500, "border": 16.8
        },
        "Pエヴァ17未来": {
            "ts": 319.7, "rush_rate": 0.70, "continuation": 0.81, 
            "payout_avg": 1500, "border": 17.0
        }
    }

    if target_machine not in machines:
        print(f"エラー: 機種 '{target_machine}' が見つかりません。")
        return

    spec = machines[target_machine]
    ball_price = 4
    ts = spec["ts"]
    rush_rate = spec["rush_rate"]
    continuation = spec["continuation"]
    payout_avg = spec["payout_avg"]

    all_histories = []
    bankruptcy_days = []
    final_profits = []

    print(f"シミュレーション実行中... ({iterations}試行)")

    for _ in range(iterations):
        purse = initial_budget
        history = [0] # 収支の履歴 (0から開始)
        is_bankrupt = False
        
        for d in range(days):
            if is_bankrupt:
                history.append(history[-1])
                continue

            day_invested = 0
            day_payout = 0
            
            for _ in range(spins_per_day):
                cost = (1000 / rotation_rate)
                if purse < cost:
                    is_bankrupt = True
                    bankruptcy_days.append(d + 1)
                    break
                
                purse -= cost
                day_invested += cost
                
                # 当たり判定
                if random.random() < (1 / ts):
                    win = payout_avg
                    # RUSH判定
                    if random.random() < rush_rate:
                        while random.random() < continuation:
                            win += payout_avg
                    
                    purse += win * ball_price
                    day_payout += win * ball_price
            
            # その日の終わりの累計収支を記録
            history.append(purse - initial_budget)
        
        final_profits.append(purse - initial_budget)
        all_histories.append(history)

    # 統計計算
    all_histories = np.array(all_histories)
    mean_history = np.mean(all_histories, axis=0)
    p25 = np.percentile(all_histories, 2.5, axis=0)
    p975 = np.percentile(all_histories, 97.5, axis=0)
    
    bankruptcy_rate = (len(bankruptcy_days) / iterations) * 100
    avg_bankruptcy_day = np.mean(bankruptcy_days) if bankruptcy_days else 0

    # グラフ描画
    plt.figure(figsize=(12, 7))
    days_range = np.arange(days + 1)
    
    # 95%分布（背景）
    plt.fill_between(days_range, p25, p975, color='gray', alpha=0.2, label='95%分布範囲 (上位2.5%～下位2.5%)')
    
    # 個別のサンプル（視覚化のために数本表示）
    for i in range(min(10, iterations)):
        plt.plot(days_range, all_histories[i], alpha=0.15, linewidth=0.8, color='green')

    # 期待収支（平均）
    plt.plot(days_range, mean_history, color='blue', linewidth=2.5, label='期待収支 (全試行平均)')
    
    # 補助線
    plt.axhline(0, color='black', linestyle='-', linewidth=1)
    plt.axhline(-initial_budget, color='red', linestyle='--', linewidth=1.5, label='破産ライン')
    
    # 装飾
    plt.title(f"【{target_machine}】収支推移シミュレーション ({days}日間 / {iterations}試行)", fontsize=14)
    plt.xlabel("経過日数", fontsize=12)
    plt.ylabel("累計収支 (円)", fontsize=12)
    plt.legend(loc='upper left')
    plt.grid(True, which='both', linestyle='--', alpha=0.5)
    
    # 統計情報の表示
    stats_text = (
        f"最終期待収支: {mean_history[-1]:,.0f} 円\n"
        f"上位2.5%境界: {p975[-1]:,.0f} 円\n"
        f"下位2.5%境界: {p25[-1]:,.0f} 円\n"
        f"破産確率: {bankruptcy_rate:.1f} %\n"
    )
    if bankruptcy_days:
        stats_text += f"平均破産日数: {avg_bankruptcy_day:.1f} 日"
    
    plt.gca().text(0.02, 0.65, stats_text, transform=plt.gca().transAxes, 
                   verticalalignment='top', fontsize=11,
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))

    plt.tight_layout()
    graph_filename = "pachinko_simulation.png"
    plt.savefig(graph_filename)
    print(f"\nグラフを {graph_filename} に保存しました。")

    # コンソール出力
    border_diff = rotation_rate - spec["border"]
    print(f"\n--- 【{target_machine}】 シミュレーション結果 ---")
    print(f"設定回転率: {rotation_rate}回/1k (ボーダー比: {border_diff:+.1f})")
    print(f"初期軍資金: {initial_budget:,} 円 / 試行回数: {iterations:,}")
    print("-" * 40)
    print(f"最終期待収支: {mean_history[-1]:,.0f} 円")
    print(f"収支分布 (95%範囲): {p25[-1]:,.0f} ～ {p975[-1]:,.0f} 円")
    print(f"破産確率: {bankruptcy_rate:.1f} %")
    if bankruptcy_days:
        print(f"平均破産日数: {avg_bankruptcy_day:.1f} 日")
    print(f"勝率 (プラス収支): {(len([x for x in final_profits if x > 0]) / iterations) * 100:.1f} %")
    print("-" * 40)

# --- 実行設定 ---
if __name__ == "__main__":
    simulate_pachinko_advanced(
        target_machine="Pエヴァ17未来", 
        days=30,               # シミュレーション期間
        spins_per_day=1500,      # 1日の回転数
        rotation_rate=19,      # 回転率 (1kあたり)
        initial_budget=200000,  # 初期軍資金
        iterations=2000        # 統計精度向上のための試行回数
    )