import pandas as pd
import numpy as np
import datetime
import re
import pickle
from datetime import datetime

def seikei(file_path):#はじめはARTもカウントしていたが、途中でなくなるパターンに対応。差枚なしVER
    def flatten_list(nested_list):
        flat_list = []
        for item in nested_list:
            if isinstance(item, list):
                flat_list.extend(flatten_list(item))  # 内側のリストをフラット化
            else:
                flat_list.append(item)
        return flat_list


    def clean_data_by_non_numeric_text(data_list, valid_interval=12):
        """
        リスト内の「数字」「日付」「曜日」以外のテキストを見つけ、その前後の要素を削除します。

        Args:
            data_list (list): 処理対象のリスト。
            valid_interval (int): 前後削除する要素の間隔（デフォルトは12）。

        Returns:
            list: クリーンアップ後のリスト。
        """

        # 数字を判定する関数
        def is_numeric(text):
            return bool(re.fullmatch(r'\d+', text))

        # 日付を判定する関数
        def is_date(text):
            return bool(re.fullmatch(r'\d{4}/\d{2}/\d{2}', text))

        # 曜日を判定する関数
        def is_weekday(text):
            weekdays = {"月", "火", "水", "木", "金", "土", "日"}
            return text in weekdays
            # 分数または小数（例: 1/219.1）

        def is_fraction_or_decimal(text):
            return bool(re.fullmatch(r'\d+/\d+(\.\d+)?', text))

            # カンマ付きの数字（例: 3,456）

        def is_comma_number(text):
            return bool(re.fullmatch(r'\d{1,3}(,\d{3})+', text))

            # 排除対象を判定
        def is_excludable(text):
            return (
                    is_numeric(text) or
                    is_date(text) or
                    is_weekday(text) or
                    is_fraction_or_decimal(text) or
                    is_comma_number(text)
            )
        # 「排除対象以外」を抽出
        target_indices = [
            i for i, item in enumerate(data_list)
            if not is_excludable(item)
        ]
        print(target_indices)

        # 削除対象のインデックスを特定
        to_remove_indices = set()
        for i in range(len(target_indices)):
            curr_index = target_indices[i]
            # 次の要素が存在する場合
            if i + 1 < len(target_indices):
                aftr_index = target_indices[i + 1]
                segment = data_list[curr_index:aftr_index]
                weekday_count = sum(1 for item in segment if is_weekday(item))

                # 間隔が12でない場合
                if aftr_index - curr_index != 12:
                    to_remove_indices.update(range(curr_index, aftr_index - 1))
                elif weekday_count >= 2:
                    # 範囲全体を削除対象に追加
                    to_remove_indices.update(range(curr_index, aftr_index - 1))

            else:
                # 次の要素が存在しない場合
                remaining_elements = len(data_list) - curr_index
                if remaining_elements < 12:  # 後ろに11個未満しか要素がない
                    to_remove_indices.update(range(curr_index, len(data_list)))

            # 削除対象を取り除いて新しいリストを作成
        cleaned_list = [item for i, item in enumerate(data_list) if i not in to_remove_indices]

        return cleaned_list


    if file_path:
        # 選択されたファイルを開いて読み込む
        with open(file_path, 'rb') as f:
            data_list = pickle.load(f)
    # リストをフラット化
    data_list = flatten_list(data_list)
    #data_list = clean_data_by_non_numeric_text(data_list)
    print(data_list)
    #store_name = input("店名を入力して下さい：")
    store_name = "オーギヤタウン半田"
    # データをチャンクごとに分割して二次元配列にreshape
    chunk_size = 12  # 1行あたりの列数
    num_chunks = (len(data_list) + chunk_size - 1) // chunk_size  # 切り上げ

    # パディングを行ってチャンクのサイズを揃える
    data_list_2d = [data_list[i * chunk_size: (i + 1) * chunk_size] for i in range(num_chunks)]

    # 最後のチャンクが満たない場合、パディング
    if len(data_list_2d[-1]) < chunk_size:
        data_list_2d[-1].extend([None] * (chunk_size - len(data_list_2d[-1])))

    # NumPy 配列に変換する
    data_array = np.array(data_list_2d, dtype=object)

    print(data_array)

    # Pandas DataFrameに変換してカラム名を設定
    column_names = ["日付", "曜日", "機種名", "台番号", "勝敗", "G数", "出率", "BB回数", "RB回数", "合成確率", "BB確率", "RB確率"]
    df = pd.DataFrame(data_array, columns=column_names)
    df = df.fillna('')
    df = df.drop(['出率', '勝敗'], axis=1)
    dt_now = datetime.now()
    output_path = f"rowdata{store_name + dt_now.strftime('%Y%m%d')}.csv"

    # CSVファイルに書き出し
    df.to_csv(output_path, index=False, encoding="utf-8_sig")
    return output_path
#seikei("scraped_data_20251013_024419.pkl")