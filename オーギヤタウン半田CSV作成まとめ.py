from みんレポスクレイピング_オーギヤ半田_ハナハナのみ import scraping_from_minrepo
from データ整形スクレイピングみんレポオーギヤタウン半田 import seikei
from 対策版_特徴量追加_オーギヤ半田 import tokuchoryo
from モジュールまとめ_オーギヤ半田_ハナハナ import MyClass
import os

mod = MyClass()

pkl_path = scraping_from_minrepo("2025/05/24", "2025/05/25")
print("スクレイピングが完了しました。")
new_csv_path = seikei(pkl_path)
print("データ整形が完了しました。")
old_path = "rowdataオーギヤタウン半田_combined.csv"
if os.path.exists(old_path):
    combined_path = mod.combine_files(old_path, new_csv_path, old_path)
else:
    # new_csv_pathのファイルをold_pathの名前にリネーム
    os.rename(new_csv_path, old_path)
    combined_path = old_path
print("データ結合が完了しました。")
modified_csv_path = tokuchoryo(combined_path)
print("特徴量追加が完了しました。")