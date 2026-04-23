from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider, Button
from Discordファイルアップロードbot import Discord_file_upload
plt.rcParams["font.family"] = "MS Gothic"  # Windows用


def plot_border_diff_chart(csv_file):
    # CSVデータの読み込み
    image_files = []
    df = pd.read_csv(csv_file, encoding="utf-8")
    df["日付"] = pd.to_datetime(df["日付"], errors='coerce')
    date = "2025-02-28"
    # df = df[df["日付"] == pd.to_datetime(date)]
    # 数値データのみ変換（エラー時 NaN にする）
    numeric_cols = ["ボーダー差分", "最小ボーダー差分", "最大ボーダー差分", "総回転数"]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')

    # 台番号ごとにデータを集計し、平均を計算
    df_grouped_machine = df.groupby("機種名")[numeric_cols].mean().reset_index()
    df_grouped_number = df.groupby("台番号")[numeric_cols].mean().reset_index()
    number_to_machine = df.groupby("台番号")["機種名"].apply(lambda x: ", ".join(x.unique())).to_dict()

    def save_data_in_batches(graph, categories, border_diff, min_border_diff, max_border_diff, batch_size=50):
        total_categories = len(categories)
        num_batches = (total_categories + batch_size - 1) // batch_size  # 必要なバッチ数を計算

        today_str = datetime.today().strftime("%Y-%m-%d")  # 実行日の日付を取得

        for batch in range(num_batches):
            start = batch * batch_size
            end = min(start + batch_size, total_categories)

            fig, ax = plt.subplots(figsize=(10, 8))
            plt.subplots_adjust(left=0.2, right=0.99, bottom=0.1, top=0.9)

            visible_categories = categories[start:end]
            visible_border_diff = border_diff[start:end]
            visible_min_border_diff = min_border_diff[start:end]
            visible_max_border_diff = max_border_diff[start:end]

            y_positions = np.arange(len(visible_categories))
            colors = np.where(visible_border_diff >= 0, 'blue', 'red')

            # 背景に交互の色を付ける
            for i in range(len(y_positions)):
                if i % 2 == 0:
                    ax.axhspan(i - 0.5, i + 0.5, facecolor='lightgray', alpha=0.3)

            ax.barh(y_positions, visible_border_diff, color=colors, align='center')

            ax.set_yticks(y_positions)
            ax.set_yticklabels(visible_categories)
            for i, tick in enumerate(ax.get_yticklabels()):
                if visible_border_diff.iloc[i] >= 0:
                    tick.set_color('blue')

            for i, (min_val, max_val) in enumerate(zip(visible_min_border_diff, visible_max_border_diff)):
                ax.plot([min_val, max_val], [y_positions[i], y_positions[i]], color='black', linewidth=2)
                ax.plot([min_val, min_val], [y_positions[i] - 0.2, y_positions[i] + 0.2], color='black', linewidth=2)
                ax.plot([max_val, max_val], [y_positions[i] - 0.2, y_positions[i] + 0.2], color='black', linewidth=2)

            ax.set_xlabel("ボーダー差分")
            ax.set_title(f"ボーダー差分の横棒グラフ (Batch {batch + 1})")

            # ファイル名を日付付きで保存
            filename = r"C:\Users\mikih\PycharmProjects\pythonProject\graph_log\\" + graph + "border_diff_chart_" + today_str + "_batch_" + str(
                batch + 1) + ".png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"Saved: {filename}")  # 保存完了メッセージを表示
            plt.close(fig)  # メモリ節約のために図を閉じる
            image_files.append(filename)

    def plot_grouped_data(graph, df_grouped, title):
        if df_grouped.columns[0] == "台番号":
            categories = df_grouped[df_grouped.columns[0]].map(number_to_machine) + \
                         " (" + df_grouped[df_grouped.columns[0]].astype(str) + ") - " + \
                         df_grouped["総回転数"].astype(int).astype(str) + "回転"
        else:
            categories = df_grouped[df_grouped.columns[0]]  # 横軸ラベル（台番号 or 機種名）
        border_diff = df_grouped["ボーダー差分"]
        min_border_diff = df_grouped["最小ボーダー差分"]
        max_border_diff = df_grouped["最大ボーダー差分"]

        # グラフを保存する関数を呼び出す
        save_data_in_batches(graph, categories, border_diff, min_border_diff, max_border_diff)

    # 台番号ごとのグラフ
    plot_grouped_data("kakudai", df_grouped_number, "ボーダー差分の横棒グラフと範囲線（台番号ごとの平均）")

    # 機種名ごとのグラフ
    plot_grouped_data("kishu", df_grouped_machine, "ボーダー差分の横棒グラフと範囲線（機種名ごとの平均）")
    try:
        Discord_file_upload(image_files)
    except Exception as e:
        print(e)


# 使用例
#csv_file = "today_P_sadamadataオーギヤ半田.csv"  # CSVファイルのパスを指定
#plot_border_diff_chart(csv_file)
