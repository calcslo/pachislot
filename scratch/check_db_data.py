import sqlite3

def check_existing_data():
    conn = sqlite3.connect("slot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT 日付, 機種名 FROM slot_data LIMIT 5;")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    conn.close()

if __name__ == "__main__":
    check_existing_data()
