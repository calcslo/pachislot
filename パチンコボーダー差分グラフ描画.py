import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider, Button

plt.rcParams["font.family"] = "MS Gothic"  # Windows用

def plot_border_diff_chart(csv_file):
    # CSVデータの読み込み
    df = pd.read_csv(csv_file, encoding="utf-8")
    df["日付"] = pd.to_datetime(df["日付"], errors='coerce')
    date = "2025-02-28"
    #df = df[df["日付"] == pd.to_datetime(date)]
    # 数値データのみ変換（エラー時 NaN にする）
    numeric_cols = ["ボーダー差分", "最小ボーダー差分", "最大ボーダー差分"]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')

    # 台番号ごとにデータを集計し、平均を計算
    df_grouped_machine = df.groupby("機種名")[numeric_cols].mean().reset_index()
    df_grouped_number = df.groupby("台番号")[numeric_cols].mean().reset_index()
    number_to_machine = df.groupby("台番号")["機種名"].apply(lambda x: ", ".join(x.unique())).to_dict()

    def plot_grouped_data(df_grouped, title):
        if df_grouped.columns[0] == "台番号":
            categories = df_grouped[df_grouped.columns[0]].map(number_to_machine) + " (" + df_grouped[
                df_grouped.columns[0]].astype(str) + ")"
        else:
            categories = df_grouped[df_grouped.columns[0]]  # 横軸ラベル（台番号 or 機種名）
        border_diff = df_grouped["ボーダー差分"]
        min_border_diff = df_grouped["最小ボーダー差分"]
        max_border_diff = df_grouped["最大ボーダー差分"]
        max_display = 50  # 一度に表示する最大の台番号数
        num_categories = len(categories)

        # グラフの初期設定
        fig, ax = plt.subplots(figsize=(10, 8))
        plt.subplots_adjust(left=0.2, right=0.99, bottom=0.1, top=0.9)
        start = 0
        end = min(start + max_display, num_categories)

        def update():
            ax.clear()

            visible_categories = categories[start:end]
            visible_border_diff = border_diff[start:end]
            visible_min_border_diff = min_border_diff[start:end]
            visible_max_border_diff = max_border_diff[start:end]

            y_positions = np.arange(len(visible_categories))
            colors = np.where(visible_border_diff >= 0, 'blue', 'red')

            # 背景に交互の色を付ける
            for i in range(len(y_positions)):
                if i % 2 == 0:
                    ax.axhspan(i - 0.5, i + 0.5, facecolor='lightgray', alpha=0.3)  # 偶数行の背景色

            ax.barh(y_positions, visible_border_diff, color=colors, align='center')


            ax.set_yticks(y_positions)
            ax.set_yticklabels(visible_categories)
            for i, tick in enumerate(ax.get_yticklabels()):
                if visible_border_diff.iloc[i] >= 0:
                    tick.set_color('blue')  # 青色に変更

            for i, (min_val, max_val) in enumerate(zip(visible_min_border_diff, visible_max_border_diff)):
                ax.plot([min_val, max_val], [y_positions[i], y_positions[i]], color='black', linewidth=2)
                ax.plot([min_val, min_val], [y_positions[i] - 0.2, y_positions[i] + 0.2], color='black', linewidth=2)
                ax.plot([max_val, max_val], [y_positions[i] - 0.2, y_positions[i] + 0.2], color='black', linewidth=2)

            ax.set_xlabel("ボーダー差分")
            ax.set_title(title)
            plt.draw()

        def next_page(event):
            nonlocal start, end
            if end < num_categories:
                start += max_display
                end = min(start + max_display, num_categories)
                btn_next.ax.set_facecolor((0.7, 0.8, 1, 1)) # クリックされた時の色を固定
                update()
                btn_next.ax.set_facecolor((0.2, 0.6, 1, 0.5)) # 元の色に戻す

        def previous_page(event):
            nonlocal start, end
            if start > 0:
                start -= max_display
                end = start + max_display
                btn_prev.ax.set_facecolor((0.7, 0.8, 1, 1)) # クリックされた時の色を固定
                update()
                btn_prev.ax.set_facecolor((0.2, 0.6, 1, 0.5)) # 元の色に戻す

        # ボタンの作成
        ax_next = plt.axes([0.85, 0.005, 0.1, 0.03])  # "次へ"ボタンの位置
        ax_prev = plt.axes([0.75, 0.005, 0.1, 0.03])  # "前へ"ボタンの位置

        btn_next = Button(ax_next, '次へ')
        btn_prev = Button(ax_prev, '前へ')
        btn_next.ax.set_facecolor((0.2, 0.6, 1, 0.5))  # 半透明の青色
        btn_prev.ax.set_facecolor((0.2, 0.6, 1, 0.5))  # 半透明の青色
        # ボタンにイベントを設定
        btn_next.on_clicked(next_page)
        btn_prev.on_clicked(previous_page)

        update()
        plt.show()

    # 台番号ごとのグラフ
    plot_grouped_data(df_grouped_number, "ボーダー差分の横棒グラフと範囲線（台番号ごとの平均）")

    # 機種名ごとのグラフ
    plot_grouped_data(df_grouped_machine, "ボーダー差分の横棒グラフと範囲線（機種名ごとの平均）")


# 使用例
csv_file = "today_P_sadamadataオーギヤ半田.csv"  # CSVファイルのパスを指定
plot_border_diff_chart(csv_file)
