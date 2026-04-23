def add_adjacent_mean_column(df):
    # 前日差枚の平均値を格納する新しい列を作成
    df = df.sort_values(by=['台番号', '日付'])
    df['前日差枚平均値'] = 0.0

    # グループごとに処理
    for idx in df.index:
        # 上下の行のインデックスを取得
        above_index = idx - 1 if idx > df.index.min() else None
        below_index = idx + 1 if idx < df.index.max() else None

        # 平均を計算するための値のリスト
        values = []

        # 上の行が存在し、かつ前日差枚が0でない場合
        if above_index is not None and df.at[above_index, '前日差枚'] != 0:
            values.append(df.at[above_index, '前日差枚'])

        # 下の行が存在し、かつ前日差枚が0でない場合
        if below_index is not None and df.at[below_index, '前日差枚'] != 0:
            values.append(df.at[below_index, '前日差枚'])

        # 自身の前日差枚が0でない場合
        if df.at[idx, '前日差枚'] != 0:
            values.append(df.at[idx, '前日差枚'])

        # 平均値を計算
        if values:
            df.at[idx, '前日差枚平均値'] = sum(values) / len(values)

    return df
