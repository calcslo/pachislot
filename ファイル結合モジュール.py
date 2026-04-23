import pandas as pd

def load_files(old_path, new_path, file_name):

    # file1の拡張子をチェックして読み込み方を決定
    df1 = pd.read_csv(old_path)
    df2 = pd.read_csv(new_path)


    # df1とdf2を縦に結合する
    df_combined = pd.concat([df1, df2], axis=0).drop_duplicates()

    # ファイルを保存する
    df_combined.to_csv(file_name, index=False)

    print("縦に結合されたファイルが保存されました:", file_name)
