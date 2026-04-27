# -*- coding: utf-8 -*-
"""
みんレポDB登録_オーギヤ半田.py

みんレポスクレイピングデータ（pickleファイル）を整形し、
slot_data.db に追加・削除するスクリプト。

使い方:
  python みんレポDB登録_オーギヤ半田.py add <pickleファイルパス>
  python みんレポDB登録_オーギヤ半田.py delete <YYYY-MM-DD> [<YYYY-MM-DD> ...]

例:
  python みんレポDB登録_オーギヤ半田.py add scraped_data_20251013_024419.pkl
  python みんレポDB登録_オーギヤ半田.py delete <開始日>~<終了日>
  python みんレポDB登録_オーギヤ半田.py delete_range <開始日> <終了日>
  python みんレポDB登録_オーギヤ半田.py delete 2025-10-10~2025-10-13
  python みんレポDB登録_オーギヤ半田.py delete_range 2025-10-10 2025-10-13
"""

import sys
import pickle
import sqlite3
import re
import numpy as np
from datetime import datetime

# ---------------------------------------------------------------
# 設定
# ---------------------------------------------------------------
DB_FILE = "slot_data.db"

# みんレポ機種名 → DB登録名のマッピング
MACHINE_NAME_MAP = {
    "スマート沖スロ ニューキングハナハナV": "LBﾆｭｰｷﾝｸﾞﾊﾅﾊﾅV",
    "スマート沖スロ+ニューキングハナハナV": "LBﾆｭｰｷﾝｸﾞﾊﾅﾊﾅV",
    "ゴーゴージャグラー３":               "ｺﾞｰｺﾞｰｼﾞｬｸﾞﾗｰ3",
    "ジャグラーガールズSS":               "ｼﾞｬｸﾞﾗｰｶﾞｰﾙｽﾞSS",
    "ウルトラミラクルジャグラー":         "ｳﾙﾄﾗﾐﾗｸﾙｼﾞｬｸﾞﾗｰ",
    "ミスタージャグラー":                 "ﾐｽﾀｰｼﾞｬｸﾞﾗｰ",
}

# 差枚計算用の機種データ（差枚計算.py から転記）
MACHINE_SAMAI_DATA = {
    "マイジャグラーV":              {"BIG": 240, "REG": 96,  "コイン持ち": 42},
    "ハナハナホウオウ〜天翔〜-30":  {"BIG": 240, "REG": 120, "コイン持ち": 36.5},
    "ハナハナホウオウ～天翔～-30":  {"BIG": 240, "REG": 120, "コイン持ち": 36.5},
    "ハナハナホウオウ?天翔?-30":   {"BIG": 240, "REG": 120, "コイン持ち": 36.5},
    "ゴーゴージャグラー3":          {"BIG": 240, "REG": 96,  "コイン持ち": 39.5},
    "ゴーゴージャグラー３":         {"BIG": 240, "REG": 96,  "コイン持ち": 39.5},
    "アイムジャグラーEX-TP":        {"BIG": 252, "REG": 96,  "コイン持ち": 40},
    "アイムジャグラーEX":           {"BIG": 252, "REG": 96,  "コイン持ち": 40},
    "SアイムジャグラーＥＸ":        {"BIG": 252, "REG": 96,  "コイン持ち": 40},
    "ネオアイムジャグラーEX":       {"BIG": 252, "REG": 96,  "コイン持ち": 40},
    "キングハナハナ-30":            {"BIG": 260, "REG": 120, "コイン持ち": 39.9},
    "ドラゴンハナハナ～閃光～‐30":  {"BIG": 252, "REG": 96,  "コイン持ち": 39.9},
    "ドラゴンハナハナ〜閃光〜‐30":  {"BIG": 252, "REG": 96,  "コイン持ち": 39.9},
    "ドラゴンハナハナ?閃光?‐30":   {"BIG": 252, "REG": 96,  "コイン持ち": 39.9},
    "ジャグラーガールズ":           {"BIG": 240, "REG": 96,  "コイン持ち": 42},
    "ジャグラーガールズSS":         {"BIG": 240, "REG": 96,  "コイン持ち": 42},
    "ウルトラミラクルジャグラー":   {"BIG": 240, "REG": 96,  "コイン持ち": 42},
    "ミスタージャグラー":           {"BIG": 240, "REG": 96,  "コイン持ち": 41},
    "ファンキージャグラー2":        {"BIG": 240, "REG": 96,  "コイン持ち": 42},
    "ファンキージャグラー２ＫＴ":   {"BIG": 240, "REG": 96,  "コイン持ち": 42},
    "スマスロ北斗の拳":             {"BIG": 110, "REG": 0,   "コイン持ち": 34.7},
    "Lスマスロ北斗の拳":            {"BIG": 110, "REG": 0,   "コイン持ち": 34.7},
    "スマート沖スロ ニューキングハナハナV": {"BIG": 312, "REG": 130, "コイン持ち": 37},
    "スマート沖スロ+ニューキングハナハナV": {"BIG": 312, "REG": 130, "コイン持ち": 37},
    # DB登録名でも引けるようにエイリアスを追加
    "LBﾆｭｰｷﾝｸﾞﾊﾅﾊﾅV":  {"BIG": 312, "REG": 130, "コイン持ち": 37},
    "ｺﾞｰｺﾞｰｼﾞｬｸﾞﾗｰ3":   {"BIG": 240, "REG": 96,  "コイン持ち": 39.5},
    "ｼﾞｬｸﾞﾗｰｶﾞｰﾙｽﾞSS":  {"BIG": 240, "REG": 96,  "コイン持ち": 42},
    "ｳﾙﾄﾗﾐﾗｸﾙｼﾞｬｸﾞﾗｰ":  {"BIG": 240, "REG": 96,  "コイン持ち": 42},
    "ﾐｽﾀｰｼﾞｬｸﾞﾗｰ":      {"BIG": 240, "REG": 96,  "コイン持ち": 41},
}


# ---------------------------------------------------------------
# 差枚計算（差枚計算.py のロジックを転用）
# ---------------------------------------------------------------
def samai_predict(b_count, r_count, total_game, machine_type):
    machine = MACHINE_SAMAI_DATA.get(machine_type)
    if machine is None:
        return 0
    coin_holding = float(machine["コイン持ち"])

    if machine_type in ("スマスロ北斗の拳", "Lスマスロ北斗の拳"):
        total_game = total_game - ((b_count - r_count) * 10)

    samai = (b_count * machine["BIG"] + r_count * machine["REG"]) - (50 * total_game / coin_holding)
    return int(round(samai))


# ---------------------------------------------------------------
# pickleデータの整形（データ整形スクレイピングみんレポオーギヤタウン半田.py を転用）
# ---------------------------------------------------------------
def flatten_list(nested_list):
    flat_list = []
    for item in nested_list:
        if isinstance(item, list):
            flat_list.extend(flatten_list(item))
        else:
            flat_list.append(item)
    return flat_list


def seikei(file_path):
    """
    pickleファイルを読み込み、整形済みのレコードリストを返す。
    各レコード: {日付, 機種名, 台番号, BONUS, BIG, REG, 累計ゲーム, 最終差枚}
    """

    def is_numeric(text):
        return bool(re.fullmatch(r'\d+', text))

    def is_date(text):
        return bool(re.fullmatch(r'\d{4}/\d{2}/\d{2}', text))

    def is_weekday(text):
        return text in {"月", "火", "水", "木", "金", "土", "日"}

    def is_fraction_or_decimal(text):
        return bool(re.fullmatch(r'\d+/\d+(\.\d+)?', text))

    def is_comma_number(text):
        return bool(re.fullmatch(r'\d{1,3}(,\d{3})+', text))

    def is_excludable(text):
        return (
            is_numeric(text)
            or is_date(text)
            or is_weekday(text)
            or is_fraction_or_decimal(text)
            or is_comma_number(text)
        )

    def clean_data(data_list, valid_interval=12):
        target_indices = [i for i, item in enumerate(data_list) if not is_excludable(item)]
        to_remove_indices = set()
        for i in range(len(target_indices)):
            curr_index = target_indices[i]
            if i + 1 < len(target_indices):
                aftr_index = target_indices[i + 1]
                segment = data_list[curr_index:aftr_index]
                weekday_count = sum(1 for item in segment if is_weekday(item))
                if aftr_index - curr_index != 12:
                    to_remove_indices.update(range(curr_index, aftr_index - 1))
                elif weekday_count >= 2:
                    to_remove_indices.update(range(curr_index, aftr_index - 1))
            else:
                remaining_elements = len(data_list) - curr_index
                if remaining_elements < 12:
                    to_remove_indices.update(range(curr_index, len(data_list)))
        return [item for i, item in enumerate(data_list) if i not in to_remove_indices]

    with open(file_path, "rb") as f:
        data_list = pickle.load(f)

    data_list = flatten_list(data_list)
    # clean_data_by_non_numeric_text は現状コメントアウトされているため適用しない
    # data_list = clean_data(data_list)

    chunk_size = 12
    num_chunks = (len(data_list) + chunk_size - 1) // chunk_size
    data_list_2d = [data_list[i * chunk_size: (i + 1) * chunk_size] for i in range(num_chunks)]
    if data_list_2d and len(data_list_2d[-1]) < chunk_size:
        data_list_2d[-1].extend([None] * (chunk_size - len(data_list_2d[-1])))

    # カラム: 日付, 曜日, 機種名, 台番号, 勝敗, G数, 出率, BB回数, RB回数, 合成確率, BB確率, RB確率
    records = []
    for row in data_list_2d:
        if len(row) < 12:
            continue
        date_raw    = row[0]   # 例: '2025/10/13'
        kishumei    = row[2]   # 機種名
        dai_no      = row[3]   # 台番号
        g_count_raw = row[5]   # G数 (例: '5458' or '5,458')
        bb_count_raw = row[7]  # BB回数
        rb_count_raw = row[8]  # RB回数

        # None チェック
        if any(v is None for v in [date_raw, kishumei, dai_no, g_count_raw, bb_count_raw, rb_count_raw]):
            print(f"  [SKIP] None値あり: {row}")
            continue

        # 日付変換: '2025/10/13' → '2025-10-13'
        try:
            date_obj = datetime.strptime(str(date_raw), "%Y/%m/%d")
            date_str = date_obj.strftime("%Y-%m-%d")
        except ValueError:
            print(f"  [SKIP] 日付変換エラー: {date_raw}")
            continue

        # 数値変換（カンマ除去）
        def to_int(val):
            return int(str(val).replace(",", ""))

        try:
            g_count  = to_int(g_count_raw)
            bb_count = to_int(bb_count_raw)
            rb_count = to_int(rb_count_raw)
        except (ValueError, TypeError) as e:
            print(f"  [SKIP] 数値変換エラー: {row} -> {e}")
            continue

        bonus = bb_count + rb_count

        # 機種名変換
        db_machine_name = MACHINE_NAME_MAP.get(kishumei, kishumei)

        # 台番号を4桁ゼロパディング（数字のみ想定）
        dai_no_str = str(dai_no).strip().zfill(4)

        # 差枚計算（元の機種名で検索、なければDB登録名で検索）
        samai = samai_predict(bb_count, rb_count, g_count, kishumei)
        if samai == 0 and kishumei != db_machine_name:
            samai = samai_predict(bb_count, rb_count, g_count, db_machine_name)

        records.append({
            "日付":       date_str,
            "機種名":     db_machine_name,
            "台番号":     dai_no_str,
            "BONUS":      bonus,
            "BIG":        bb_count,
            "REG":        rb_count,
            "累計ゲーム": g_count,
            "最終差枚":   samai,
        })

    print(f"  整形完了: {len(records)} 件")
    return records


# ---------------------------------------------------------------
# DBテーブル作成（存在しない場合のみ）
# ---------------------------------------------------------------
def ensure_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS slot_data (
            日付       TEXT NOT NULL,
            機種名     TEXT NOT NULL,
            台番号     TEXT NOT NULL,
            BONUS      INTEGER,
            BIG        INTEGER,
            REG        INTEGER,
            累計ゲーム INTEGER,
            最終差枚   INTEGER,
            PRIMARY KEY (日付, 機種名, 台番号)
        )
    """)
    conn.commit()


# ---------------------------------------------------------------
# 追加処理
# ---------------------------------------------------------------
def add_records(pickle_path):
    print(f"[ADD] pickleファイル読み込み: {pickle_path}")
    records = seikei(pickle_path)
    if not records:
        print("  追加するレコードがありません。")
        return

    conn = sqlite3.connect(DB_FILE)
    ensure_table(conn)

    inserted = 0
    updated  = 0
    skipped  = 0

    for r in records:
        # 既存チェック（PRIMARY KEY）
        cur = conn.execute(
            "SELECT COUNT(*) FROM slot_data WHERE 日付=? AND 機種名=? AND 台番号=?",
            (r["日付"], r["機種名"], r["台番号"])
        )
        exists = cur.fetchone()[0]

        if exists:
            # 上書き更新
            conn.execute("""
                UPDATE slot_data
                SET BONUS=?, BIG=?, REG=?, 累計ゲーム=?, 最終差枚=?
                WHERE 日付=? AND 機種名=? AND 台番号=?
            """, (
                r["BONUS"], r["BIG"], r["REG"], r["累計ゲーム"], r["最終差枚"],
                r["日付"], r["機種名"], r["台番号"]
            ))
            updated += 1
        else:
            conn.execute("""
                INSERT INTO slot_data (日付, 機種名, 台番号, BONUS, BIG, REG, 累計ゲーム, 最終差枚)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r["日付"], r["機種名"], r["台番号"],
                r["BONUS"], r["BIG"], r["REG"], r["累計ゲーム"], r["最終差枚"]
            ))
            inserted += 1

    conn.commit()
    conn.close()

    print(f"  [完了] 新規追加: {inserted} 件 / 更新: {updated} 件 / スキップ: {skipped} 件")


# ---------------------------------------------------------------
# 削除処理
# ---------------------------------------------------------------
def delete_records(date_args):
    """
    指定された日付（YYYY-MM-DD）のみんレポデータをDBから削除する。
    みんレポ由来の機種名（MACHINE_NAME_MAP の値）に絞って削除。
    """
    for arg in date_args:
        if "~" in arg:
            # 期間指定: YYYY-MM-DD~YYYY-MM-DD
            parts = arg.split("~")
            if len(parts) == 2:
                delete_records_range(parts[0], parts[1])
            else:
                print(f"  [ERROR] 期間指定の形式が不正です（開始日~終了日）: {arg}")
        else:
            # 単一日の削除（従来通り）
            _delete_single_date(arg)

def _delete_single_date(date_str):
    """単一日の削除処理（内部用）"""
    minrepo_machines = list(MACHINE_NAME_MAP.values())
    placeholders = ",".join(["?"] * len(minrepo_machines))

    conn = sqlite3.connect(DB_FILE)
    ensure_table(conn)

    # 日付フォーマット統一（YYYY/MM/DD → YYYY-MM-DD）
    date_str = date_str.replace("/", "-")
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print(f"  [ERROR] 日付フォーマット不正（YYYY-MM-DD で指定してください）: {date_str}")
        conn.close()
        return

    cur = conn.execute(
        f"SELECT COUNT(*) FROM slot_data WHERE 日付=? AND 機種名 IN ({placeholders})",
        [date_str] + minrepo_machines
    )
    count = cur.fetchone()[0]

    conn.execute(
        f"DELETE FROM slot_data WHERE 日付=? AND 機種名 IN ({placeholders})",
        [date_str] + minrepo_machines
    )
    conn.commit()
    conn.close()
    print(f"  [DELETE] {date_str}: {count} 件削除")


def delete_records_range(start_date, end_date):
    """
    指定された期間（start_date ～ end_date）のみんレポデータをDBから削除する。
    """
    minrepo_machines = list(MACHINE_NAME_MAP.values())
    placeholders = ",".join(["?"] * len(minrepo_machines))
    conn = sqlite3.connect(DB_FILE)
    ensure_table(conn)
    # 日付フォーマット統一
    start_date = start_date.replace("/", "-")
    end_date = end_date.replace("/", "-")
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        print(f"  [ERROR] 日付フォーマット不正（YYYY-MM-DD で指定してください）: {start_date}, {end_date}")
        conn.close()
        return
    cur = conn.execute(
        f"SELECT COUNT(*) FROM slot_data WHERE 日付 BETWEEN ? AND ? AND 機種名 IN ({placeholders})",
        [start_date, end_date] + minrepo_machines
    )
    count = cur.fetchone()[0]
    conn.execute(
        f"DELETE FROM slot_data WHERE 日付 BETWEEN ? AND ? AND 機種名 IN ({placeholders})",
        [start_date, end_date] + minrepo_machines
    )
    conn.commit()
    conn.close()
    print(f"  [DELETE] {start_date} ～ {end_date}: {count} 件削除")
    print(f"  [完了] 合計 {count} 件削除しました。")


# ---------------------------------------------------------------
# エントリポイント
# ---------------------------------------------------------------
def print_usage():
    print(__doc__)


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "add":
        if len(sys.argv) < 3:
            print("使い方: python みんレポDB登録_オーギヤ半田.py add <pickleファイルパス>")
            sys.exit(1)
        pickle_path = sys.argv[2]
        add_records(pickle_path)

    elif command == "delete":
        if len(sys.argv) < 3:
            print("使い方: python みんレポDB登録_オーギヤ半田.py delete <YYYY-MM-DD> [<YYYY-MM-DD> ...]")
            print("        python みんレポDB登録_オーギヤ半田.py delete <開始日>~<終了日>")
            sys.exit(1)
        date_args = sys.argv[2:]
        delete_records(date_args)

    elif command == "delete_range":
        if len(sys.argv) < 4:
            print("使い方: python みんレポDB登録_オーギヤ半田.py delete_range <開始日> <終了日>")
            sys.exit(1)
        start_date = sys.argv[2]
        end_date = sys.argv[3]
        delete_records_range(start_date, end_date)


    else:
        print(f"不明なコマンド: {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
