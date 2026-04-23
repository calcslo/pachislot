from datetime import datetime, timedelta
#import jpholiday
import pandas as pd
from 前日差枚平均値 import add_adjacent_mean_column
from 差枚計算 import samai_predict
import tkinter as tk
from tkinter import filedialog
from 設定判別累計版 import cal_setting_short
from 推定高設定判別 import high_or_else
def tokuchoryo(file_path):
    def select_file():
        # Tkinterのルートウィンドウを作成し、非表示にします
        root = tk.Tk()
        root.withdraw()

        # ファイルダイアログを表示し、選択されたファイルのパスを取得します
        file_path = filedialog.askopenfilename()

        # 選択されたファイルの名前を取得します
        file_name = file_path.split("/")[-1]

        # 日付型を%Y/%m/%dに事前に統一する
        df = pd.read_csv(file_path, encoding="utf-8")
        #df["日付"] = df["日付"].dt.strftime('%Y/%m/%d')
        return df, file_name
    def shima_num(dai_num):
        dai_num = int(dai_num)
        if 1092 <= dai_num <= 1112:
            return 'A'
        elif 1137 <= dai_num <= 1153:
            return 'B'
        elif 1154 <= dai_num <= 1168:
            return 'C'
        elif 1169 <= dai_num <= 1183:
            return 'D'
        elif 947 <= dai_num <= 955:
            return 'E'
        elif 975 <= dai_num <= 978:
            return 'F'
        elif 979 <= dai_num <= 982:
            return 'G'
        elif 987 <= dai_num <= 998:
            return 'H'
        elif 983 <= dai_num <= 986:
            return 'I'
        elif 971 <= dai_num <= 974:
            return 'J'
        elif 962 <= dai_num <= 970:
            return 'K'
        elif 925 <= dai_num <= 931:
            return 'L'
        elif 914 <= dai_num <= 924:
            return 'M'
        elif 875 <= dai_num <= 887:
            return 'N'
        elif 859 <= dai_num <= 874:
            return 'O'
        elif 956 <= dai_num <= 961:
            return 'P'
        elif 932 <= dai_num <= 937:
            return 'Q'
        elif 904 <= dai_num <= 913:
            return 'R'
        elif 886 <= dai_num <= 897:
            return 'S'
        elif 845 <= dai_num <= 858:
            return 'T'
        elif 734 <= dai_num <= 753:
            return 'U'
        elif 714 <= dai_num <= 733:
            return 'V'
        else:
            return '-'
    def kado_num(dai_num):
        kado = [1092, 1112, 1137, 1153, 1154, 1168, 1169, 1183, 947, 955, 975, 978, 979, 982, 987, 998, 983, 986, 971, 974, 962, 970, 925, 931, 914, 924, 875, 887, 859, 874, 956, 961, 932, 937, 904, 913, 886, 897, 845, 858, 734, 753, 714, 733]
        kado2 = [1093, 1111, 1138, 1152, 1155, 1167, 1170, 1182, 948, 954, 976, 977, 980, 981, 988, 997, 984, 985, 972, 973, 963, 969, 926, 930, 915, 923, 876, 886, 860, 873, 957, 960, 933, 936, 905, 912, 887, 896, 846, 857, 735, 752, 715, 732]
        kado3 = [1094, 1110, 1139, 1151, 1156, 1166, 1171, 1181, 949, 953, 989, 996, 964, 968, 927, 929, 916, 922, 877, 885, 861, 872, 958, 959, 934, 935, 906, 911, 888, 895, 847, 856, 736, 751, 716, 731]
        if int(dai_num) in kado:
            return 1
        elif int(dai_num) in kado2:
            return 2
        elif int(dai_num) in kado3:
            return 3
        else:
            return 0

    godo_list = pd.to_datetime(['2025/03/26', '2025/02/22', '2025/01/11'])
    soutuke_list = pd.to_datetime(['2025/04/06', '2025/03/01'])

    # ファイルを選択し、データフレームとファイル名を取得します
    df = pd.read_csv(file_path, encoding="utf-8")
    # 完全一致する行をフィルタリングする
    train = df[df['機種名'].str.contains("マイジャグラーV|ハナハナホウオウ|ゴーゴージャグラー3|アイムジャグラーEX-TP|ファンキージャグラー2|ジャグラー|ハナハナ|北斗の拳")]
    train = df[df['機種名'].str.contains("ハナハナ|ジャグラー")]
    train = train.copy()
    if 'ART回数' in train.columns and 'ART確率' in train.columns:
        train = train.drop(columns=['ART回数', 'ART確率'])
    train["日付"] = pd.to_datetime(train["日付"], format='%Y/%m/%d')
    train["year"] = train["日付"].dt.year
    train["month"] = train["日付"].dt.month
    train["day"] = train["日付"].dt.day
    train["週末"] = (train["日付"].dt.weekday >= 5).astype(int)
    train["台番号末尾"] = train['台番号'].astype(str).str[-1]
    train['xのつく日'] = train['日付'].dt.day.astype(str).str[-1].astype(int)
    train['イベント日'] = train['日付'].dt.day.apply(lambda x: 1 if x % 10 in [3, 5, 8] else 0)
    #train['イベント日前日'] = train['日付'].dt.day.apply(lambda x: 1 if x % 10 in [2, 4, 7] else 0)
    #train['イベント日後日'] = train['日付'].dt.day.apply(lambda x: 1 if x % 10 in [4, 6, 9] else 0)
    train["イベント日1"] = train["日付"].dt.day.isin([3, 13, 23]).astype(int) # オーギヤ半田の場合
    train["イベント日2"] = train["日付"].dt.day.isin([5, 15, 25]).astype(int) # オーギヤ半田の場合
    train["イベント日3"] = train["日付"].dt.day.isin([8, 18, 28]).astype(int) # オーギヤ半田の場合
    train['合同営業'] = train['日付'].isin(godo_list).astype(int)
    train['総付景品'] = train['日付'].isin(soutuke_list).astype(int)
    train['島番号'] = train['台番号'].apply(shima_num)
    train['角からの位置'] = train['台番号'].apply(kado_num)
    train['G数'] = train['G数'].str.replace(',', '', regex=False).astype(int)
    train['BB回数'] = pd.to_numeric(train['BB回数'])
    train['RB回数'] = pd.to_numeric(train['RB回数'])
    train["予測差枚"] = train.apply(lambda row: samai_predict(row['BB回数'], row['RB回数'], row['G数'], row["機種名"]), axis=1)
    train = train.sort_values(by=['台番号', '日付'])

    event_shift = (
        train[train['イベント日'] == 1]
        .groupby('台番号')['予測差枚']
        .shift(1)
    )
    train.loc[train['イベント日'] == 1, '前回イベント日差枚'] = event_shift

    island_mean = (
        train.groupby(['日付', '島番号'])['予測差枚']
        .mean()
        .reset_index()
        .rename(columns={'予測差枚': '当日島平均差枚'})
    )
    island_mean_unique = island_mean.drop_duplicates(subset=['日付', '島番号'])
    train = train.merge(island_mean_unique, on=['日付', '島番号'], how='left')
    train = train.sort_values(by=['島番号', '日付'])

    event_df = train[train['イベント日'] == 1].copy()
    event_df['前回イベント日島平均差枚'] = event_df.groupby('島番号')['当日島平均差枚'].shift(1)
    event_df = event_df[['島番号', '日付', '前回イベント日島平均差枚']]
    event_df_unique = event_df.drop_duplicates(subset=['日付', '島番号'])
    train = train.merge(event_df_unique, on=['日付', '島番号'], how='left')
    train = train.sort_values(by=['台番号', '日付'])
    train['前日差枚'] = train.groupby('台番号')['予測差枚'].shift(1)
    train['前日G数'] = train.groupby('台番号')['G数'].shift(1)
    train['前日BB回数'] = train.groupby('台番号')['BB回数'].shift(1)
    train['前日RB回数'] = train.groupby('台番号')['RB回数'].shift(1)
    train['二日前差枚'] = train.groupby('台番号')['予測差枚'].shift(2)
    train['三日前差枚'] = train.groupby('台番号')['予測差枚'].shift(3)
    train['四日前差枚'] = train.groupby('台番号')['予測差枚'].shift(4)
    train['五日前差枚'] = train.groupby('台番号')['予測差枚'].shift(5)
    train['六日前差枚'] = train.groupby('台番号')['予測差枚'].shift(6)
    #train["二日間連続凹み"] = ((train["前日差枚"] < 0) & (train["二日前差枚"] < 0)).astype(int)
    #train["三日間連続凹み"] = ((train["三日前差枚"] < 0) & (train["前日差枚"] < 0) & (train["二日前差枚"] < 0)).astype(int)
    cols = ["前日差枚", "二日前差枚", "三日前差枚", "四日前差枚", "五日前差枚", "六日前差枚"]
    neg_flags = train[cols] < 0
    posi_flags = train[cols] > 0

    def count_leading_trues(row):
        count = 0
        for val in row:
            if val:
                count += 1
            else:
                break
        return count

    train["連続凹み日数"] = neg_flags.apply(count_leading_trues, axis=1)
    train["連続凸日数"] = posi_flags.apply(count_leading_trues, axis=1)
    train = train.drop(['二日前差枚', '三日前差枚', '四日前差枚', '五日前差枚', '六日前差枚'], axis=1)
    train["予測設定"] = train.apply(lambda row: cal_setting_short(row['BB回数'], row['RB回数'], row['G数'], row["機種名"]), axis=1)
    train["推定高設定"] = train.apply(lambda row: high_or_else(row['BB回数'], row['RB回数'], row['G数'], row["機種名"]), axis=1)
    def count_high_setting_neighbors(df):
        def count_neighbors(group):
            setting = group.set_index('台番号')['推定高設定']
            return group['台番号'].apply(lambda x: setting.get(x - 1, 0) + setting.get(x + 1, 0))
        df['隣台推定高設定数'] = df.groupby(['島番号', '日付']).apply(count_neighbors).reset_index(level=[0, 1], drop=True)
        return df
    train = count_high_setting_neighbors(train)
    filtered_train = train[train['イベント日'] == 1]
    filtered_train = filtered_train.sort_values(by=['台番号', '日付'])
    filtered_train['前回イベント日隣台推定高設定数'] = filtered_train.groupby('台番号')['隣台推定高設定数'].shift(1)
    cols_to_merge = ['日付', '島番号', '台番号', '前回イベント日隣台推定高設定数']
    filtered_train_sub = filtered_train[cols_to_merge]
    train = train.merge(filtered_train_sub, on=['日付', '島番号', '台番号'], how='left')

    train["前日設定"] = train.groupby("台番号")["予測設定"].shift(1)
    #train["二日前設定"] = train.groupby("台番号")["予測設定"].shift(2)
    #train["三日前設定"] = train.groupby("台番号")["予測設定"].shift(3)

    """
    train["新台"] = 0
    for idx, row in train.iterrows():
        two_weeks_ago = row['日付'] - timedelta(days=14)
        recent_rows = train[(train['台番号'] == row['台番号']) &
                            (train['日付'] >= two_weeks_ago) &
                            (train['日付'] < row['日付'])]  # 過去のデータのみ
        if not recent_rows.empty:
            different_machines = recent_rows[recent_rows['機種名'] != row['機種名']]
            if not different_machines.empty:
                train.at[idx, '新台'] = 1
    
    print(train.columns)
    
    
    grouped = train.groupby('台番号')
    # 全期間の集計
    train['全期間RB回数'] = grouped['RB回数'].transform('sum')
    train['全期間BB回数'] = grouped['BB回数'].transform('sum')
    train['全期間G数'] = grouped['G数'].transform('sum')
    train['全期間差枚'] = grouped['予測差枚'].transform('sum')
    # 一か月前の日付条件を作成
    train['一か月前'] = train['日付'] - pd.Timedelta(days=30)
    
    
    def calculate_past_month_counts(row):
        # 1ヶ月前の日付を計算
        one_month_ago = row['日付'] - timedelta(days=30)
    
        # 同じ台番号のデータを取得
        group = train[train['台番号'] == row['台番号']]
    
        # 1ヶ月前以内の日付データをフィルタリング
        recent_data = group[group['日付'] >= one_month_ago]
    
        # それぞれの合計を計算
        row['一か月RB回数'] = recent_data['RB回数'].sum()
        row['一か月BB回数'] = recent_data['BB回数'].sum()
        row['一か月G数'] = recent_data['G数'].sum()
        row['一か月差枚'] = recent_data['予測差枚'].sum()
    
        return row
    
    # applyを1回にまとめて適用
    train = train.apply(calculate_past_month_counts, axis=1)
    print("loading...")
    
    e_train1 = train[train['イベント日1'] == 1]
    e_train2 = train[train['イベント日2'] == 1]
    e_train3 = train[train['イベント日3'] == 1]
    e_grouped1 = e_train1.groupby('台番号')
    e_grouped2 = e_train2.groupby('台番号')
    e_grouped3 = e_train3.groupby('台番号')
    train['e1全期間RB回数'] = e_grouped1['RB回数'].transform('sum')
    train['e1全期間BB回数'] = e_grouped1['BB回数'].transform('sum')
    train['e1全期間G数'] = e_grouped1['G数'].transform('sum')
    train['e1全期間差枚'] = e_grouped1['予測差枚'].transform('sum')
    train['e1一か月RB回数'] = e_grouped1['一か月RB回数'].transform('sum')
    train['e1一か月BB回数'] = e_grouped1['一か月BB回数'].transform('sum')
    train['e1一か月G数'] = e_grouped1['一か月G数'].transform('sum')
    train['e1一か月差枚'] = e_grouped1['予測差枚'].transform('sum')
    train['e2全期間RB回数'] = e_grouped2['RB回数'].transform('sum')
    train['e2全期間BB回数'] = e_grouped2['BB回数'].transform('sum')
    train['e2全期間G数'] = e_grouped2['G数'].transform('sum')
    train['e2全期間差枚'] = e_grouped2['予測差枚'].transform('sum')
    train['e2一か月RB回数'] = e_grouped2['一か月RB回数'].transform('sum')
    train['e2一か月BB回数'] = e_grouped2['一か月BB回数'].transform('sum')
    train['e2一か月G数'] = e_grouped2['一か月G数'].transform('sum')
    train['e2一か月差枚'] = e_grouped2['予測差枚'].transform('sum')
    train['e3全期間RB回数'] = e_grouped3['RB回数'].transform('sum')
    train['e3全期間BB回数'] = e_grouped3['BB回数'].transform('sum')
    train['e3全期間G数'] = e_grouped3['G数'].transform('sum')
    train['e3全期間差枚'] = e_grouped3['予測差枚'].transform('sum')
    train['e3一か月RB回数'] = e_grouped3['一か月RB回数'].transform('sum')
    train['e3一か月BB回数'] = e_grouped3['一か月BB回数'].transform('sum')
    train['e3一か月G数'] = e_grouped3['一か月G数'].transform('sum')
    train['e3一か月差枚'] = e_grouped3['予測差枚'].transform('sum')
    
    n_train = train[train['イベント日'] == 0]
    n_grouped = n_train.groupby('台番号')
    train['n全期間BB回数'] = n_grouped['BB回数'].transform('sum')
    train['n全期間RB回数'] = n_grouped['RB回数'].transform('sum')
    train['n全期間G数'] = n_grouped['G数'].transform('sum')
    train['n全期間差枚'] = n_grouped['予測差枚'].transform('sum')
    train['n一か月RB回数'] = n_grouped['一か月RB回数'].transform('sum')
    train['n一か月BB回数'] = n_grouped['一か月BB回数'].transform('sum')
    train['n一か月G数'] = n_grouped['一か月G数'].transform('sum')
    train['n一か月差枚'] = n_grouped['予測差枚'].transform('sum')
    
    train["全期間予測設定"] = train.apply(lambda row: cal_setting_short(row['全期間BB回数'], row['全期間RB回数'], row['全期間G数'], row["機種名"]), axis=1)
    train["一か月予測設定"] = train.apply(lambda row: cal_setting_short(row['一か月BB回数'], row['一か月RB回数'], row['一か月G数'], row["機種名"]) if row['日付'] >= row['一か月前'] else None, axis=1)
    train["e1全期間予測設定"] = train.apply(lambda row: cal_setting_short(row['e1全期間BB回数'], row['e1全期間RB回数'], row['e1全期間G数'], row["機種名"]) if row['日付'].day in [3, 13, 23] else None, axis=1)
    train["e1一か月予測設定"] = train.apply(lambda row: cal_setting_short(row['e1一か月BB回数'], row['e1一か月RB回数'], row['e1一か月G数'], row["機種名"]) if row['日付'] >= row['一か月前'] and row['日付'].day in [3, 13, 23] else None, axis=1)
    train["e2全期間予測設定"] = train.apply(lambda row: cal_setting_short(row['e2全期間BB回数'], row['e2全期間RB回数'], row['e2全期間G数'], row["機種名"]) if row['日付'].day in [5, 15, 25] else None, axis=1)
    train["e2一か月予測設定"] = train.apply(lambda row: cal_setting_short(row['e2一か月BB回数'], row['e2一か月RB回数'], row['e2一か月G数'], row["機種名"]) if row['日付'] >= row['一か月前'] and row['日付'].day in [5, 15, 25] else None, axis=1)
    train["e3全期間予測設定"] = train.apply(lambda row: cal_setting_short(row['e3全期間BB回数'], row['e3全期間RB回数'], row['e3全期間G数'], row["機種名"]) if row['日付'].day in [8, 18, 28] else None, axis=1)
    train["e3一か月予測設定"] = train.apply(lambda row: cal_setting_short(row['e3一か月BB回数'], row['e3一か月RB回数'], row['e3一か月G数'], row["機種名"]) if row['日付'] >= row['一か月前'] and row['日付'].day in [8, 18, 28] else None, axis=1)
    train["n全期間予測設定"] = train.apply(lambda row: cal_setting_short(row['n全期間BB回数'], row['n全期間RB回数'], row['n全期間G数'], row["機種名"]) if row['日付'].day not in [3, 5, 8, 13, 15, 18, 23, 25, 28] else None, axis=1)
    train["n一か月予測設定"] = train.apply(lambda row: cal_setting_short(row['n一か月BB回数'], row['n一か月RB回数'], row['n一か月G数'], row["機種名"]) if row['日付'] >= row['一か月前'] and row['日付'].day not in [3, 5, 8, 13, 15, 18, 23, 25, 28] else None, axis=1)
    train.drop(columns=['一か月前'], inplace=True)
    """
    train = pd.DataFrame(train)
    output_path = "3monthsrowdataオーギヤタウン半田.csv"
    train.to_csv(output_path, encoding="utf-8", index=False)
    return output_path
tokuchoryo("rowdataオーギヤタウン半田20251013.csv")