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
    average_diff_by_machine = df.groupby(target)['差枚'].mean()
    print("---全体集計---")
    print(average_diff_by_machine)
    # イベント日1、2、3ごとにフィルタリングして、機種名ごとに差枚合計の平均を計算
    event_columns = ['イベント日']

    # 結果を格納する辞書
    average_by_event = {}

    for event_col in event_columns:
        # イベント日ごとにフィルタリング
        filtered_df = df[df[event_col] == 1]

        # 機種名ごとに差枚合計の平均を計算
        average_by_event[event_col] = filtered_df.groupby(target)['差枚'].mean()

    # 結果表示
    for event, averages in average_by_event.items():
        print(f"--- {event} ---")
        print(averages)
        print()


df = pd.read_csv("modifiedrowdataコスモ大府.csv", encoding="utf-8")
#機種ごとの平均差枚（各イベ日、全体）
cal_mean('機種名')
#角からの位置ごとの平均差枚（各イベ日、全体）
cal_mean('角からの位置')
#末尾（各イベ日、全体）
cal_mean('台番号末尾')
#前回、二回前、三回前差枚
#cal_mean('前日差枚')
#cal_mean('二日前差枚')
#cal_mean('三日前差枚')
X = df[['前日差枚', '二日前差枚', '三日前差枚']]
y = df['差枚']
df_clean = df.replace([np.inf, -np.inf], np.nan).dropna(subset=['前日差枚', '二日前差枚', '三日前差枚', '差枚'])
X_clean = df_clean[['前日差枚', '二日前差枚', '三日前差枚']]
y_clean = df_clean['差枚']
X_clean = sm.add_constant(X_clean)
model = sm.OLS(y_clean, X_clean).fit()
print('回帰分析の結果')
print(model.summary())
columns_to_check = ['差枚', '前日差枚', '二日前差枚', '三日前差枚']
correlation_matrix = df[columns_to_check].corr()
print('相関係数')
print(correlation_matrix)
#2日、3日前連続凹み
cal_mean("二日間連続凹み")
cal_mean("三日間連続凹み")
#演者ごとの全体平均差枚、機種ごとの平均差枚
average_diff_by_machine1 = df.groupby(['来店演者1', "機種名"])['差枚'].mean()
average_diff_by_machine2 = df.groupby(['来店演者2', "機種名"])['差枚'].mean()
average_diff_by_machine3 = df.groupby(['来店演者3', "機種名"])['差枚'].mean()
print("---全体集計---")
print(average_diff_by_machine1)
print(average_diff_by_machine2)
print(average_diff_by_machine3)
output_to_file('output1.txt', "---全体集計---")
output_to_file('output1.txt', str(average_diff_by_machine1))
output_to_file('output1.txt', str(average_diff_by_machine2))
output_to_file('output1.txt', str(average_diff_by_machine3))
average_diff_by_machine1 = df.groupby(['取材1', "機種名"])['差枚'].mean()
average_diff_by_machine2 = df.groupby(['取材2', "機種名"])['差枚'].mean()
average_diff_by_machine3 = df.groupby(['取材3', "機種名"])['差枚'].mean()
print("---全体集計---")
print(average_diff_by_machine1)
print(average_diff_by_machine2)
print(average_diff_by_machine3)
output_to_file('output1.txt', "---全体集計---")
output_to_file('output1.txt', str(average_diff_by_machine1))
output_to_file('output1.txt', str(average_diff_by_machine2))
output_to_file('output1.txt', str(average_diff_by_machine3))
average_diff_by_machine1 = df.groupby(['景品1', "機種名"])['差枚'].mean()
average_diff_by_machine2 = df.groupby(['景品2', "機種名"])['差枚'].mean()
average_diff_by_machine3 = df.groupby(['景品3', "機種名"])['差枚'].mean()
print("---全体集計---")
print(average_diff_by_machine1)
print(average_diff_by_machine2)
print(average_diff_by_machine3)
output_to_file('output1.txt', "---全体集計---")
output_to_file('output1.txt', str(average_diff_by_machine1))
output_to_file('output1.txt', str(average_diff_by_machine2))
output_to_file('output1.txt', str(average_diff_by_machine3))

# イベント日1、2、3ごとにフィルタリングして、機種名ごとに差枚合計の平均を計算
event_columns = ['イベント日']

# 結果を格納する辞書
average_by_event = {}

for event_col in event_columns:
    # イベント日ごとにフィルタリング
    filtered_df = df[df[event_col] == 1]

    # 機種名ごとに差枚合計の平均を計算
    average_by_event[event_col] = filtered_df.groupby(['来店演者1', "機種名"])['差枚'].mean()

for event, averages in average_by_event.items():
    output_to_file('output1.txt', f"--- {event} ---")
    output_to_file('output1.txt', str(averages))
    output_to_file('output1.txt', "")  # 空行を追加して区切る
# 結果表示
for event, averages in average_by_event.items():
    print(f"--- {event} ---")
    print(averages)
    print()

#島番号ごとの平均差枚(各イベ日、全体)
cal_mean('島番号')
#新台（各イベ日、全体）
cal_mean('新台')
#曜日
cal_mean('曜日')
#前回イベ日差枚
