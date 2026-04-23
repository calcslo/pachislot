import sqlite3
import json
import random
from datetime import datetime, timedelta
import argparse
import sys

DB_FILE = 'slot_data.db'
LAYOUT_FILE = 'docs/layout.json'
DUMMY_MARKER_BONUS = 9999 # ダミーデータの目印としてBONUS回数を9999に設定する

def get_valid_machines():
    try:
        with open(LAYOUT_FILE, 'r', encoding='utf-8') as f:
            layout = json.load(f)
        machines = [str(cell) for row in layout for cell in row if cell != '']
        return machines
    except Exception as e:
        print(f"Error reading layout.json: {e}")
        return []

def delete_dummy_data():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(f"DELETE FROM slot_data WHERE BONUS = {DUMMY_MARKER_BONUS}")
    deleted = c.rowcount
    conn.commit()
    conn.close()
    print(f"ダミーデータを {deleted} 件削除しました。")

def generate_dummy_data():
    machines = get_valid_machines()
    if not machines:
        print("有効な台番号が見つかりませんでした。")
        return

    # 適当に機種を割り当てる
    hanahana_model = 'LBﾆｭｰｷﾝｸﾞﾊﾅﾊﾅV'
    juggler_model = 'ｺﾞｰｺﾞｰｼﾞｬｸﾞﾗｰ3'
    
    hanahana_machines = machines[:len(machines)//2]
    juggler_machines = machines[len(machines)//2:]

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    today = datetime.now()
    records = []

    print("ダミーデータを生成中...")
    for i in range(90): # 過去90日分
        current_date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        
        # ハナハナのダミーデータ
        for m in hanahana_machines:
            # 稼働していない日もある想定 (80%の確率で稼働)
            if random.random() > 0.2:
                diff = int(random.gauss(0, 1500)) # 平均0、標準偏差1500の正規分布
                games = random.randint(1000, 8000)
                records.append((current_date, hanahana_model, m, DUMMY_MARKER_BONUS, 0, 0, games, diff))
                
        # ジャグラーのダミーデータ
        for m in juggler_machines:
            if random.random() > 0.2:
                diff = int(random.gauss(0, 1200))
                games = random.randint(1000, 8000)
                records.append((current_date, juggler_model, m, DUMMY_MARKER_BONUS, 0, 0, games, diff))

    try:
        c.executemany('''
            INSERT OR REPLACE INTO slot_data 
            (日付, 機種名, 台番号, BONUS, BIG, REG, 累計ゲーム, 最終差枚) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', records)
        conn.commit()
        print(f"ダミーデータを {len(records)} 件追加しました！")
        print(f"※ 目印として全ダミーデータの BONUS カラムを {DUMMY_MARKER_BONUS} に設定しています。")
        print("※ 削除する場合は 'python generate_dummy_data.py --delete' を実行してください。")
    except Exception as e:
        print(f"エラー: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--delete", action="store_true", help="ダミーデータを削除する")
    args = parser.parse_args()

    if args.delete:
        delete_dummy_data()
    else:
        generate_dummy_data()
