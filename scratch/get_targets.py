import sqlite3
db = r'd:\PycharmProjects\pachislot\slot_data.db'
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("""
    SELECT 日付, 機種名, 台番号, 累計ゲーム, 最終差枚
    FROM slot_data
    WHERE 日付 >= date('now', '-3 days')
      AND 累計ゲーム >= 2000
      AND abs(最終差枚) >= 1000
    ORDER BY abs(最終差枚) DESC LIMIT 10
""")
for r in c.fetchall():
    print(r)
conn.close()
