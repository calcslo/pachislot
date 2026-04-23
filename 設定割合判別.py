import pandas as pd
from scipy import stats
import math

from 設定判別改 import cal_setting
list = [0.0002, 0.295, 0.5067, 0.07, 0.0179, 0.0011]
df = pd.read_csv("train.csv", encoding="shift-jis")  # "your_file.csv"は適切なファイルパスに置き換えてください

df = df[(df['機種名'] == 'マイジャグラーV') | (df['機種名'] == 'ハナハナホウオウ～天翔～-30') | (df['機種名'] == 'ゴーゴージャグラー3') | (df['機種名'] == 'アイムジャグラーEX-TP') \
                    | (df['機種名'] == 'ファンキージャグラー2')
                    ]
df['予測設定'] = df.apply(lambda row: cal_setting(row["BB回数"], row['RB回数'], row['G数'], row["機種名"], list)[2], axis=1)
"""
# "設定"列の値の割合を計算する
setting_counts = df["予測設定"].value_counts(normalize=True)

# 結果を表示する
print("設定の割合:")
for setting, count in setting_counts.items():
    print(f"設定 {setting}: {count:.2%}")
"""
import matplotlib.pyplot as plt

# 階級の範囲を定義
class_ranges = [(0.5, 1.4), (1.5, 2.4), (2.5, 3.4), (3.5, 4.4), (4.5, 5.4), (5.5, 6.4)]

# 各階級のデータ数をカウント
class_counts = [((df['予測設定'] >= class_range[0]) & (df['予測設定'] < class_range[1])).sum() for class_range in class_ranges]

# 全体のデータ数で割って割合を計算
total_count = df.shape[0]
class_ratios = [count / total_count for count in class_counts]

# 棒グラフを作成
plt.bar(range(1, len(class_ranges) + 1), class_ratios, tick_label=[f"{class_range[0]}-{class_range[1]}" for class_range in class_ranges])
plt.xlabel('階級')
plt.ylabel('割合')
plt.title('平均設定の階級ごとの割合')
# 数字で設定の割合も表示
for i, class_ratio in enumerate(class_ratios):
    plt.text(i + 1, class_ratio, f"{class_ratio:.2%}", ha='center', va='bottom')

plt.show()