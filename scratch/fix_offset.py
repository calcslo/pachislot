import sqlite3

db = r'd:\PycharmProjects\pachislot\slot_data.db'
conn = sqlite3.connect(db)
c = conn.cursor()

# 影響確認
c.execute("SELECT COUNT(*), MIN(最終差枚), MAX(最終差枚) FROM slot_data WHERE 日付 >= '2026-04-22' AND 累計ゲーム > 0")
cnt, mn, mx = c.fetchone()
print(f'修正対象: {cnt}件, 差枚範囲: {mn}〜{mx}')

c.execute("SELECT COUNT(*) FROM slot_data WHERE 日付 >= '2026-04-22' AND 累計ゲーム > 0 AND 最終差枚 = 0")
zero_cnt = c.fetchone()[0]
print(f'うち差枚=0件 (解析失敗の可能性あり): {zero_cnt}件')

# 修正実行: 差枚から30を引く (累計ゲーム>0 かつ 4/22以降)
c.execute("UPDATE slot_data SET 最終差枚 = 最終差枚 - 30 WHERE 日付 >= '2026-04-22' AND 累計ゲーム > 0")
conn.commit()
print(f'修正完了: {c.rowcount}件を -30 更新')

# 検証
c.execute("SELECT COUNT(*), MIN(最終差枚), MAX(最終差枚) FROM slot_data WHERE 日付 >= '2026-04-22' AND 累計ゲーム > 0")
cnt2, mn2, mx2 = c.fetchone()
print(f'修正後: {cnt2}件, 差枚範囲: {mn2}〜{mx2}')

conn.close()
print('完了')
