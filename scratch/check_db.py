import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('slot_data.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Tables:', cur.fetchall())
cur.execute("PRAGMA table_info(slot_data)")
cols = cur.fetchall()
print('Columns:')
for c in cols:
    print(' ', c)
cur.execute("SELECT * FROM slot_data LIMIT 5")
rows = cur.fetchall()
print('Sample rows:')
for r in rows:
    print(' ', r)
conn.close()
