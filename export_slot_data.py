import sqlite3
import pandas as pd
import json
import os

DB_FILE = 'slot_data.db'
EXCEL_FILE = 'オーギヤ半田島図.xlsx'
DOCS_DIR = 'docs'

def export_data():
    os.makedirs(DOCS_DIR, exist_ok=True)
    
    # 1. Export DB to JSON
    print(f"Reading from {DB_FILE}...")
    if not os.path.exists(DB_FILE):
        print(f"Warning: {DB_FILE} does not exist. Creating empty data.json.")
        data = []
    else:
        conn = sqlite3.connect(DB_FILE)
        # Select all data
        query = "SELECT 日付, 機種名, 台番号, BONUS, BIG, REG, 累計ゲーム, 最終差枚 FROM slot_data"
        try:
            df = pd.read_sql_query(query, conn)
            data = df.to_dict(orient='records')
            print(f"Extracted {len(data)} records from DB.")
        except Exception as e:
            print(f"Error reading from DB: {e}")
            data = []
        finally:
            conn.close()
            
    with open(os.path.join(DOCS_DIR, 'data.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Saved data.json")

    # 2. Export Excel layout to JSON
    print(f"Reading layout from {EXCEL_FILE}...")
    if not os.path.exists(EXCEL_FILE):
        print(f"Warning: {EXCEL_FILE} does not exist. Creating empty layout.json.")
        layout = []
    else:
        try:
            df_excel = pd.read_excel(EXCEL_FILE, header=None)
            # Fill NaNs with empty string and convert to list of lists
            layout = df_excel.fillna('').values.tolist()
            # Clean up floats to ints for machine numbers
            for i in range(len(layout)):
                for j in range(len(layout[i])):
                    val = layout[i][j]
                    if isinstance(val, float) and val.is_integer():
                        layout[i][j] = int(val)
                    elif isinstance(val, (int, float)):
                        layout[i][j] = int(val)
            print(f"Extracted layout with {len(layout)} rows.")
        except Exception as e:
            print(f"Error reading Excel layout: {e}")
            layout = []
            
    with open(os.path.join(DOCS_DIR, 'layout.json'), 'w', encoding='utf-8') as f:
        json.dump(layout, f, ensure_ascii=False, indent=2)
    print("Saved layout.json")

if __name__ == "__main__":
    export_data()
    print("Export complete!")
