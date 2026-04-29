import pickle

with open('scraping_data.pkl', 'rb') as f:
    data = pickle.load(f)

d = data['0269']
starts = d['履歴_スタート']
shubetu = d['履歴_種別']
dedamas = d['履歴_出玉']

print("=== マーカー位置 ===")
for i, t in enumerate(shubetu):
    if '最終' in str(t):
        print(f"  [{i}] {t} = {starts[i]}")

# 今日のデータ (マーカー[78]以降, [156]未満)
today_data = list(zip(
    [str(s) for s in starts[79:156]],
    [str(t) for t in shubetu[79:156]],
    [str(v) for v in dedamas[79:156]]
))

heso_sum = sum(int(s) for s, t, v in today_data if t == '大当' and s.isdigit())
st_sum   = sum(int(s) for s, t, v in today_data if t == '確変' and s.isdigit())
dedama_sum = sum(int(v) for s, t, v in today_data if v.isdigit())

print("\n=== 今日のデータ集計 ===")
print(f"ヘソスタート合計 (大当): {heso_sum}")
print(f"確変スタート合計 (確変): {st_sum}")
print(f"ヘソ+確変スタート合計: {heso_sum + st_sum}")
print(f"出玉合計: {dedama_sum}")

print("\n=== サイトの集計値 ===")
print(f"累計スタート: {d['累計スタート']}")
print(f"最終スタート: {d['最終スタート']}")
print(f"グラフ差玉: {d['最終差玉']}")

final_diff = d['最終差玉']
investment = dedama_sum - final_diff
print(f"\n投資玉 (出玉-差玉): {investment}")

cumstart = d['累計スタート']
if investment > 0:
    k1 = heso_sum * 250 / investment
    k2 = cumstart * 250 / investment
    k3 = (heso_sum + st_sum) * 250 / investment
    print(f"\n回転率パターン:")
    print(f"  ヘソのみ / 投資: {k1:.1f}")
    print(f"  累計スタート / 投資: {k2:.1f}")
    print(f"  ヘソ+確変 / 投資: {k3:.1f}")

# 「26」になる場合の投資玉を逆算
for nomal in [heso_sum, cumstart, heso_sum + st_sum]:
    inv_for_26 = nomal * 250 / 26
    diff_for_26 = dedama_sum - inv_for_26
    print(f"\nnomal={nomal} で回転率=26 → 必要な投資玉={inv_for_26:.0f}, 差玉={diff_for_26:.0f}")

# 昨日のデータ
print("\n=== 昨日のデータ集計 ===")
yesterday_data = list(zip(
    [str(s) for s in starts[1:78]],
    [str(t) for t in shubetu[1:78]],
    [str(v) for v in dedamas[1:78]]
))
y_heso = sum(int(s) for s, t, v in yesterday_data if t == '大当' and s.isdigit())
y_st = sum(int(s) for s, t, v in yesterday_data if t == '確変' and s.isdigit())
y_dedama = sum(int(v) for s, t, v in yesterday_data if v.isdigit())
print(f"ヘソ+確変スタート合計: {y_heso + y_st}")
print(f"出玉合計: {y_dedama}")
print(f"(今日と同一か: {y_heso+y_st == heso_sum+st_sum and y_dedama == dedama_sum})")
