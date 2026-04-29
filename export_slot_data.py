import sqlite3
import json
import os

DB_FILE = 'slot_data.db'
EXCEL_FILE = 'オーギヤ半田島図.xlsx'
DOCS_DIR = 'docs'

def export_data():
    os.makedirs(DOCS_DIR, exist_ok=True)

    # 1. Export DB to JSON (pandas不要版)
    print(f"Reading from {DB_FILE}...")
    if not os.path.exists(DB_FILE):
        print(f"Warning: {DB_FILE} does not exist. Creating empty data.json.")
        data = []
    else:
        try:
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT 日付, 機種名, 台番号, BONUS, BIG, REG, 累計ゲーム, 最終差枚 FROM slot_data")
            data = [dict(row) for row in c.fetchall()]
            print(f"Extracted {len(data)} records from DB.")
        except Exception as e:
            print(f"Error reading from DB: {e}")
            data = []
        finally:
            conn.close()

    with open(os.path.join(DOCS_DIR, 'data.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    print("Saved data.json")

    # 2. Export Excel layout to JSON (openpyxl使用、なければスキップ)
    print(f"Reading layout from {EXCEL_FILE}...")
    if not os.path.exists(EXCEL_FILE):
        print(f"Warning: {EXCEL_FILE} does not exist. Skipping layout.json update.")
    else:
        try:
            import openpyxl
            wb = openpyxl.load_workbook(EXCEL_FILE, data_only=True)
            ws = wb.active
            layout = []
            for row in ws.iter_rows(values_only=True):
                r = []
                for val in row:
                    if val is None:
                        r.append('')
                    elif isinstance(val, float) and val.is_integer():
                        r.append(int(val))
                    elif isinstance(val, (int, float)):
                        r.append(int(val))
                    else:
                        r.append(str(val))
                layout.append(r)
            print(f"Extracted layout with {len(layout)} rows.")
            with open(os.path.join(DOCS_DIR, 'layout.json'), 'w', encoding='utf-8') as f:
                json.dump(layout, f, ensure_ascii=False)
            print("Saved layout.json")
        except ImportError:
            print("openpyxl not found. Skipping layout.json update.")
        except Exception as e:
            print(f"Error reading Excel layout: {e}")

if __name__ == "__main__":
    export_data()
    print("Export complete!")
