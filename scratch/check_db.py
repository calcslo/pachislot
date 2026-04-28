import sqlite3

db_path = 'd:/PycharmProjects/pachislot/slot_data.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

# 0942番台を確認
print("=== 台番号 0942 の全データ ===")
c.execute("""
    SELECT 日付, 機種名, 台番号, 累計ゲーム, 最終差枚
    FROM slot_data 
    WHERE 台番号 = '0942'
    ORDER BY 日付
""")
for row in c.fetchall():
    print(row)

# 4/26の 差枚=1000 付近のデータを確認
print("\n=== 4/26: 差枚が800〜1200のデータ ===")
c.execute("""
    SELECT 日付, 機種名, 台番号, 累計ゲーム, 最終差枚
    FROM slot_data 
    WHERE 日付 = '2026-04-26' AND 最終差枚 BETWEEN 800 AND 1200
    ORDER BY 最終差枚 DESC
""")
for row in c.fetchall():
    print(row)

conn.close()
