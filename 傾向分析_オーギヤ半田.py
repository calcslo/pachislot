import pandas as pd
import statsmodels.api as sm
import numpy as np

pd.set_option('display.max_rows', None)  # 最大行数の制限を解除
pd.set_option('display.max_columns', None)  # 最大列数の制限を解除
pd.set_option('display.width', None)  # 行幅の制限を解除
pd.set_option('display.max_colwidth', None)  # 列の幅の制限を解除
def output_to_file(file_name, content):
    with open(file_name, 'a', encoding='utf-8') as f:
        f.write(content)
        f.write("\n")

def cal_mean(target):
    average_diff_by_machine = df.groupby(target)['予測差枚'].mean()
    print("---全体集計---")
    print(average_diff_by_machine)
    # イベント日1、2、3ごとにフィルタリングして、機種名ごとに差枚合計の平均を計算
    event_columns = ['イベント日1', 'イベント日2', 'イベント日3']

    # 結果を格納する辞書
    average_by_event = {}

    for event_col in event_columns:
        # イベント日ごとにフィルタリング
        filtered_df = df[df[event_col] == 1]

        # 機種名ごとに差枚合計の平均を計算
        average_by_event[event_col] = filtered_df.groupby(target)['予測差枚'].mean()

    # 結果表示
    for event, averages in average_by_event.items():
        print(f"--- {event} ---")
        print(averages)
        print()


df = pd.read_csv("modifiedrowdataogiyatest1.csv", encoding="utf-8")
df = df[df['機種名'].str.contains("ハナハナ")]

#機種ごとの平均差枚（各イベ日、全体）
cal_mean('機種名')
#角からの位置ごとの平均差枚（各イベ日、全体）
cal_mean('角からの位置')
#末尾（各イベ日、全体）
cal_mean('台番号末尾')
#前回、二回前、三回前差枚
cal_mean('前日設定')
cal_mean('二日前設定')
cal_mean('三日前設定')
X = df[['前日差枚', '二日前差枚', '三日前差枚']]
y = df['予測差枚']
df_clean = df.replace([np.inf, -np.inf], np.nan).dropna(subset=['前日差枚', '二日前差枚', '三日前差枚', '予測差枚'])
X_clean = df_clean[['前日差枚', '二日前差枚', '三日前差枚']]
y_clean = df_clean['予測差枚']
X_clean = sm.add_constant(X_clean)
model = sm.OLS(y_clean, X_clean).fit()
print('回帰分析の結果')
print(model.summary())
columns_to_check = ['予測差枚', '前日差枚', '二日前差枚', '三日前差枚']
correlation_matrix = df[columns_to_check].corr()
print('相関係数')
print(correlation_matrix)

#2日、3日前連続凹み
cal_mean("二日間連続凹み")
cal_mean("三日間連続凹み")

#島番号ごとの平均差枚(各イベ日、全体)
cal_mean('島番号')
#新台（各イベ日、全体）
cal_mean('新台')
#曜日
cal_mean('曜日')
#前回イベ日差枚
X = df[['前回イベント日予測差枚', '前回同イベント日1予測差枚', '前回同イベント日2予測差枚', '前回同イベント日3予測差枚']]
y = df['予測差枚']
X_clean = df_clean[['前回イベント日予測差枚', '前回同イベント日1予測差枚', '前回同イベント日2予測差枚', '前回同イベント日3予測差枚']]
y_clean = df_clean['予測差枚']
X_clean = X_clean.fillna(0)  # X_cleanの欠損値を0で埋める
y_clean = y_clean.fillna(0)  # y_cleanの欠損値を0で埋める
X_clean = sm.add_constant(X_clean)
model = sm.OLS(y_clean, X_clean).fit()
print('前回イベ日の差枚がどう影響するか回帰分析の結果')
print(model.summary())
columns_to_check = ['予測差枚','前回イベント日予測差枚', '前回同イベント日1予測差枚', '前回同イベント日2予測差枚', '前回同イベント日3予測差枚']
correlation_matrix = df[columns_to_check].corr()
print('相関係数')
print(correlation_matrix)

#前回イベ日差枚
cal_mean('前回イベント日予測設定')
cal_mean('前回同イベント日1予測設定')
cal_mean('前回同イベント日2予測設定')
cal_mean('前回同イベント日3予測設定')
X = df[['前回イベント日予測設定', '前回同イベント日1予測設定', '前回同イベント日2予測設定', '前回同イベント日3予測設定']]
y = df['予測設定']
X_clean = df_clean[['前回イベント日予測設定', '前回同イベント日1予測設定', '前回同イベント日2予測設定', '前回同イベント日3予測設定']]
y_clean = df_clean['予測設定']
X_clean = X_clean.fillna(0)  # X_cleanの欠損値を0で埋める
y_clean = y_clean.fillna(0)  # y_cleanの欠損値を0で埋める
X_clean = sm.add_constant(X_clean)
model = sm.OLS(y_clean, X_clean).fit()
print('前回イベ日の設定がどう影響するか回帰分析の結果')
print(model.summary())
columns_to_check = ['予測設定', '前回イベント日予測設定', '前回同イベント日1予測設定', '前回同イベント日2予測設定', '前回同イベント日3予測設定']
correlation_matrix = df[columns_to_check].corr()
print('相関係数')
print(correlation_matrix)