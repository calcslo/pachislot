import sqlite3
conn = sqlite3.connect('d:/PycharmProjects/pachislot/slot_data.db')
c = conn.cursor()
c.execute("SELECT 日付, 機種名, 台番号, 累計ゲーム, 最終差枚 FROM slot_data WHERE 台番号='0942' ORDER BY 日付")
for r in c.fetchall():
    print(r)
conn.close()
