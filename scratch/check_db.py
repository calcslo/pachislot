import sqlite3

conn = sqlite3.connect('slot_data.db')
cur = conn.cursor()

# ハナハナ機種名確認
cur.execute("SELECT DISTINCT 機種名 FROM slot_data WHERE 機種名 LIKE '%ハナハナ%' LIMIT 30")
models = cur.fetchall()
print('ハナハナ機種名:')
for m in models:
    print(m)

# 全機種名確認
cur.execute("SELECT DISTINCT 機種名 FROM slot_data LIMIT 50")
all_models = cur.fetchall()
print('\n全機種名（最大50）:')
for m in all_models:
    print(m)

# データ件数確認
cur.execute("SELECT COUNT(*) FROM slot_data WHERE 機種名 LIKE '%ハナハナ%'")
count = cur.fetchone()
print(f'\nハナハナデータ件数: {count[0]}')

# データ日付範囲
cur.execute("SELECT MIN(日付), MAX(日付) FROM slot_data")
date_range = cur.fetchone()
print(f'日付範囲: {date_range}')

# 台番号の例
cur.execute("SELECT DISTINCT 台番号 FROM slot_data WHERE 機種名 LIKE '%ハナハナ%' LIMIT 20")
machines = cur.fetchall()
print('\nハナハナ台番号例:')
for m in machines:
    print(m)

# 推定設定のカラムがあるか確認
cur.execute("PRAGMA table_info(slot_data)")
cols = cur.fetchall()
print('\nslot_dataカラム詳細:')
for c in cols:
    print(c)

conn.close()
