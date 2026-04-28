"""
最終修正後の補間シミュレーション
"""

label_data = [
    {"val": -1500, "textOwnTY": 296.0, "ancestorTY": 20.0, "rendered": 312.0},
    {"val": -1000, "textOwnTY": 246.0, "ancestorTY": 20.0, "rendered": 262.0},
    {"val": -500,  "textOwnTY": 197.0, "ancestorTY": 20.0, "rendered": 213.0},
    {"val": 0,     "textOwnTY": 147.0, "ancestorTY": 20.0, "rendered": 163.0},
    {"val": 500,   "textOwnTY":  97.0, "ancestorTY": 20.0, "rendered": 113.0},
    {"val": 1000,  "textOwnTY":  48.0, "ancestorTY": 20.0, "rendered":  64.0},
    {"val": 1500,  "textOwnTY":  -2.0, "ancestorTY": 20.0, "rendered":  14.0},
]

graphSvgY = 40.0  # pathLastCoord.y=20 + pathTransY=20

def interpolate(labels_sorted, gY):
    p1 = p2 = None
    for i in range(len(labels_sorted)-1):
        if labels_sorted[i][0] <= gY <= labels_sorted[i+1][0]:
            p1, p2 = labels_sorted[i], labels_sorted[i+1]
            break
    if not p1:
        if gY < labels_sorted[0][0]:
            p1, p2 = labels_sorted[0], labels_sorted[1]
        else:
            p1, p2 = labels_sorted[-2], labels_sorted[-1]
    if p1[0] == p2[0]:
        return p1[1]
    ratio = (gY - p1[0]) / (p2[0] - p1[0])
    result = p1[1] + ratio * (p2[1] - p1[1])
    print(f"  p1=({p1[0]:.1f},{p1[1]}), p2=({p2[0]:.1f},{p2[1]}), ratio={ratio:.4f}")
    return round(result)

# 旧ロジック: textY(5) + textOwnTY + ancestorTY
labels_old = sorted([(5 + d["textOwnTY"] + d["ancestorTY"], d["val"]) for d in label_data])
# 新ロジック(今回の修正): totalTranslateY = textOwnTY + ancestorTY
labels_new = sorted([(d["textOwnTY"] + d["ancestorTY"], d["val"]) for d in label_data])
# 参照: rendered
labels_rendered = sorted([(d["rendered"], d["val"]) for d in label_data])

print(f"=== graphSvgY = {graphSvgY} ===\n")

print("旧ロジック (textY=5 含む):")
r_old = interpolate(labels_old, graphSvgY)
print(f"  → {r_old}枚\n")

print("修正後 (totalTranslateYのみ, textY除く):")
r_new = interpolate(labels_new, graphSvgY)
print(f"  → {r_new}枚\n")

print("rendered基準:")
r_rend = interpolate(labels_rendered, graphSvgY)
print(f"  → {r_rend}枚\n")

print("="*50)
print(f"旧ロジック: {r_old}枚")
print(f"修正後:     {r_new}枚  (差: {r_new - r_old:+d}枚)")
print(f"rendered:   {r_rend}枚  (参照値)")

print("\n=== ラベルsvgY比較 ===")
print(f"{'val':>6}  {'old(+textY)':>11}  {'new(-textY)':>11}  {'rendered':>8}")
for d in label_data:
    old_y = 5 + d["textOwnTY"] + d["ancestorTY"]
    new_y = d["textOwnTY"] + d["ancestorTY"]
    print(f"{d['val']:>6}  {old_y:>11.1f}  {new_y:>11.1f}  {d['rendered']:>8.1f}")

print(f"\n注: graphSvgY={graphSvgY}")
print(f"rendered - new: 一定差 = {label_data[0]['rendered'] - (label_data[0]['textOwnTY']+label_data[0]['ancestorTY']):.1f}px")
