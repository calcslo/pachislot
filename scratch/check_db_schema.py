import sqlite3

def check_schema(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables: {tables}")
    
    for table in tables:
        table_name = table[0]
        print(f"\nSchema for table: {table_name}")
        cursor.execute(f"PRAGMA table_info({table_name});")
        info = cursor.fetchall()
        for col in info:
            print(col)
            
    conn.close()

if __name__ == "__main__":
    check_schema("slot_data.db")
