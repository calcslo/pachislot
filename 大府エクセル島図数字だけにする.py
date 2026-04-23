import openpyxl
import re

# ファイルパスを指定
file_path = '島図最新版.xlsx'

# Excelファイルを読み込む
wb = openpyxl.load_workbook(file_path)
ws = wb["コスモ大府"] # アクティブシートを取得

# 各セルを走査して、数字以外を削除
for row in ws.iter_rows():
    for cell in row:
        if isinstance(cell.value, str):  # 文字列の場合にのみ処理
            # 数字以外を削除する（正規表現）
            digits = ''.join(re.findall(r'\d+', cell.value))  # 数字のみ抽出
            if digits:  # 数字が存在する場合のみ
                cell.value = int(digits)  # 整数に変換
            else:
                cell.value = 0  # 数字がない場合は0に設定

# 変更を保存
wb.save('modified_島図.xlsx')