"""
DBデータ補正・削除スクリプト

【根拠】
SVG調査結果（0845台 2026-04-28）:
- ラベルの textOwnTY 間隔: 約50px per 500枚
- text.y = 5px（フォントベースライン固定オフセット）
- 過大評価量 = 5px × (total_range_枚 / 298px)
- total_range = 2 × scale_half（±スケール）
- scale_half ≈ ceil(|最終差枚| / 500) × 500

結果: 補正量 = round(5 × 2 × scale_half / 298)
     常に差枚から引く（正負問わず）

4/26,4/27,4/28 → 削除（修正後コードで再スクレイピング）
4/22-4/25      → 補正
"""
import sqlite3
import math

DB_PATH = 'd:/PycharmProjects/pachislot/slot_data.db'
PIXEL_RANGE = 298  # amchartsグラフの総ピクセル高さ（実測値）
OFFSET_PX = 5      # text.yの固定オフセット（実測値）

def estimate_scale_half(sasarai: int) -> int:
    """最終差枚から推定Y軸スケール半幅を計算（500刻み切り上げ）"""
    if sasarai == 0:
        return 0
    return max(500, math.ceil(abs(sasarai) / 500) * 500)

def calc_correction(scale_half: int) -> int:
    """スケール半幅から補正量を計算"""
    if scale_half == 0:
        return 0
    total_range = 2 * scale_half
    return round(OFFSET_PX * total_range / PIXEL_RANGE)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# =============================================
# 1. 4/26, 4/27, 4/28 のデータを削除
# =============================================
print("=== 1. 4/26〜4/28 データ削除 ===")
for d in ['2026-04-26', '2026-04-27', '2026-04-28']:
    c.execute("SELECT COUNT(*) FROM slot_data WHERE 日付=?", (d,))
    cnt = c.fetchone()[0]
    c.execute("DELETE FROM slot_data WHERE 日付=?", (d,))
    print(f"  {d}: {cnt}件 削除")

conn.commit()

# =============================================
# 2. 4/22〜4/25 のデータを補正
# =============================================
print("\n=== 2. 4/22〜4/25 データ補正 ===")
c.execute("""
    SELECT 日付, 機種名, 台番号, 累計ゲーム, 最終差枚
    FROM slot_data
    WHERE 日付 BETWEEN '2026-04-22' AND '2026-04-25'
      AND 累計ゲーム > 0
    ORDER BY 日付, 機種名, 台番号
""")
rows = c.fetchall()
print(f"補正対象: {len(rows)}件")

correction_stats = {}
updated = 0
skipped_zero = 0

for 日付, 機種名, 台番号, ゲーム, 差枚 in rows:
    scale_half = estimate_scale_half(差枚)
    correction = calc_correction(scale_half)

    if correction == 0:
        skipped_zero += 1
        continue

    new_差枚 = 差枚 - correction  # 常に引く

    # 統計
    key = scale_half
    if key not in correction_stats:
        correction_stats[key] = {'count': 0, 'correction': correction}
    correction_stats[key]['count'] += 1

    c.execute("""
        UPDATE slot_data
        SET 最終差枚 = ?
        WHERE 日付=? AND 機種名=? AND 台番号=?
    """, (new_差枚, 日付, 機種名, 台番号))
    updated += 1

conn.commit()

print(f"更新: {updated}件, スキップ(差枚=0): {skipped_zero}件")
print("\n--- スケール別補正量 ---")
print(f"  {'スケール':>8}  {'補正量':>6}  {'件数':>5}")
for scale_half, info in sorted(correction_stats.items()):
    print(f"  ±{scale_half:>5}枚  {info['correction']:>5}枚  {info['count']:>5}件")

# 補正後の統計確認
print("\n=== 3. 補正後確認 ===")
c.execute("SELECT 日付, COUNT(*), MIN(最終差枚), MAX(最終差枚), AVG(最終差枚) FROM slot_data WHERE 日付 BETWEEN '2026-04-22' AND '2026-04-25' GROUP BY 日付")
for row in c.fetchall():
    print(f"  {row[0]}: {row[1]}件, min={row[2]}, max={row[3]}, avg={row[4]:.0f}")

# 0942番台の確認
print("\n--- 0942番台（補正後） ---")
c.execute("SELECT 日付, 累計ゲーム, 最終差枚 FROM slot_data WHERE 台番号='0942' ORDER BY 日付")
for row in c.fetchall():
    print(f"  {row}")

conn.close()
print("\n完了")
