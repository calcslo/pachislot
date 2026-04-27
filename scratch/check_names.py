import sqlite3

def check_names(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT 機種名 FROM slot_data;")
    names = cursor.fetchall()
    for name in names:
        print(name[0])
    conn.close()

if __name__ == "__main__":
    check_names("slot_data.db")
