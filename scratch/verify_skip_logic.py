import os
import sqlite3
import logging

# Copy constants and function from the modified script
DB_FILE = "slot_data.db"
MACHINE_NAME_MAP = {
    "スマート沖スロ ニューキングハナハナV": "LBﾆｭｰｷﾝｸﾞﾊﾅﾊﾅV",
    "スマート沖スロ+ニューキングハナハナV": "LBﾆｭｰｷﾝｸﾞﾊﾅﾊﾅV",
    "ゴーゴージャグラー３":               "ｺﾞｰｺﾞｰｼﾞｬｸﾞﾗｰ3",
    "ジャグラーガールズSS":               "ｼﾞｬｸﾞﾗｰｶﾞｰﾙｽﾞSS",
    "ウルトラミラクルジャグラー":         "ｳﾙﾄﾗﾐﾗｸﾙｼﾞｬｸﾞﾗｰ",
    "ミスタージャグラー":                 "ﾐｽﾀｰｼﾞｬｸﾞﾗｰ",
}

def is_data_already_scraped(date_str: str, machine_name: str) -> bool:
    if not os.path.exists(DB_FILE):
        return False
    db_machine_name = MACHINE_NAME_MAP.get(machine_name, machine_name)
    db_date_str = date_str.replace("/", "-")
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        query = "SELECT COUNT(*) FROM slot_data WHERE 日付 = ? AND 機種名 = ?"
        cursor.execute(query, (db_date_str, db_machine_name))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    # Test with known data
    # Note: I need to know the EXACT string in DB. 
    # Let's try to find the exact string for 2026-02-11
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT 機種名 FROM slot_data WHERE 日付 = '2026-02-11';")
    names = cursor.fetchall()
    print(f"Found names for 2026-02-11: {[n[0] for n in names]}")
    
    for name in names:
        db_name = name[0]
        # Find if any key in MACHINE_NAME_MAP maps to this db_name
        orig_name = next((k for k, v in MACHINE_NAME_MAP.items() if v == db_name), db_name)
        print(f"Testing check for: Date=2026/02/11, OrigName={orig_name}, DBName={db_name}")
        result = is_data_already_scraped("2026/02/11", orig_name)
        print(f"Result: {result}")
    
    conn.close()
