import sqlite3
import sys

def check_names(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT 機種名 FROM slot_data;")
    names = cursor.fetchall()
    for name in names:
        try:
            # If the DB has Shift-JIS encoded bytes stored as TEXT (unlikely but possible if legacy)
            # or if the terminal is just misinterpreting UTF-8.
            # Most likely the DB is UTF-8 but the terminal is Shift-JIS.
            print(f"Name: {name[0]}")
        except:
            print(f"Error printing name: {repr(name[0])}")
    conn.close()

if __name__ == "__main__":
    # Force UTF-8 output if possible, but let's just use repr to be safe.
    conn = sqlite3.connect("slot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT 機種名 FROM slot_data;")
    names = cursor.fetchall()
    for name in names:
        print(repr(name[0]))
    conn.close()
