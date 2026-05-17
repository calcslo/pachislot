import sys

with open('scratch/ml_analysis.py', 'r', encoding='utf-8') as f:
    content = f.read()

# We will completely overwrite ml_analysis.py
new_content = """# -*- coding: utf-8 -*-
\"\"\"
ハナハナ 高設定条件分析スクリプト (GPU/XGBoost, 過去7日間対応)
\"\"\"
import sqlite3
import json
import math
import numpy as np
import pandas as pd
from datetime import datetime
from collections import defaultdict

from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier, export_text
from xgboost import XGBRegressor, XGBClassifier
from sklearn.model_selection import TimeSeriesSplit, cross_validate
from sklearn.metrics import (mean_squared_error, r2_score,
                             precision_score, recall_score, f1_score,
                             accuracy_score, confusion_matrix)
from mlxtend.frequent_patterns import apriori, association_rules

# ============================================================
# 設定
# ============================================================
DB_PATH = "slot_data.db"
LAYOUT_PATH = "docs/ogiya/layout.json"
OUTPUT_PATH = "docs/ogiya/analysis_results.json"

MACHINE_PROBS = {
    'LBﾆｭｰｷﾝｸﾞﾊﾅﾊﾅV': {
        1: {'big': 299, 'reg': 496},
        2: {'big': 291, 'reg': 471},
        3: {'big': 281, 'reg': 442},
        4: {'big': 268, 'reg': 409},
        5: {'big': 253, 'reg': 372},
    }
}

PERIOD_LABELS = {
    'all':     '全日',
    'day3':    '3の付く日',
    'day5':    '5の付く日',
    'day8':    '8の付く日',
    'event':   'イベント日(3・5・8)',
    'nonevent':'イベント日以外',
}

# 動的に構築する
FEATURE_COLS = []
FEATURE_NAMES_JP = {}

# 基本特徴量
base_feats = {
    'tail_digit': '台番号末尾',
    'weekday': '曜日',
    'position': '角からの位置',
    'cons_neg': '連続凹み日数',
    'cons_pos': '連続凸日数',
    'is_event_day': 'イベント日',
    'day_of_month': '月内日付',
    'island_id_num': '所属島ID(数値化)',
    'prev_setting_1': '前日設定',
    'prev_high_setting_1': '前日高設定(4以上)'
}
for k, v in base_feats.items():
    FEATURE_COLS.append(k)
    FEATURE_NAMES_JP[k] = v

# 過去7日間特徴量
for i in range(1, 8):
    FEATURE_COLS.append(f'prev_diff_{i}')
    FEATURE_NAMES_JP[f'prev_diff_{i}'] = f'{i}日前差枚'
    FEATURE_COLS.append(f'prev_games_{i}')
    FEATURE_NAMES_JP[f'prev_games_{i}'] = f'{i}日前ゲーム数'
    FEATURE_COLS.append(f'island_avg_prev_{i}')
    FEATURE_NAMES_JP[f'island_avg_prev_{i}'] = f'{i}日前の島平均差枚'

def estimate_setting(model, games, big, reg):
    games, big, reg = int(games or 0), int(big or 0), int(reg or 0)
    if model not in MACHINE_PROBS or games < 100:
        return None
    probs = MACHINE_PROBS[model]
    log_w, max_lw = {}, -math.inf
    for s, p in probs.items():
        pB = 1 / p['big']
        pR = 1 / p['reg']
        pN = 1 - pB - pR
        if pN <= 0: continue
        lw = big * math.log(pB) + reg * math.log(pR) + (games - big - reg) * math.log(pN)
        log_w[s] = lw
        if lw > max_lw: max_lw = lw
    total = sum(math.exp(lw - max_lw) for lw in log_w.values())
    best, best_p = None, -1
    for s, lw in log_w.items():
        p = math.exp(lw - max_lw) / total
        if p > best_p:
            best_p, best = p, s
    return int(best) if best is not None else None

def build_layout_lookup(layout_data):
    rows = len(layout_data)
    cols = len(layout_data[0]) if rows > 0 else 0
    lookup = {}
    for r in range(rows):
        for c in range(cols):
            cell = layout_data[r][c]
            if cell == '' or cell is None: continue
            num = str(cell).zfill(4)
            hL = hR = vT = vB = 0
            for i in range(c - 1, -1, -1):
                if layout_data[r][i] != '' and layout_data[r][i] is not None: hL += 1
                else: break
            for i in range(c + 1, cols):
                if layout_data[r][i] != '' and layout_data[r][i] is not None: hR += 1
                else: break
            for i in range(r - 1, -1, -1):
                if layout_data[i][c] != '' and layout_data[i][c] is not None: vT += 1
                else: break
            for i in range(r + 1, rows):
                if layout_data[i][c] != '' and layout_data[i][c] is not None: vB += 1
                else: break
            num_val = int(num)
            if (987 <= num_val <= 998) or (1370 <= num_val <= 1385):
                dist = None
                direction = 'circle'
            elif hL + hR >= vT + vB:
                dist = min(hL, hR)
                direction = 'horizontal'
            else:
                dist = min(vT, vB)
                direction = 'vertical'
            lookup[num] = {'pos': dist, 'direction': direction, 'island_id': '', 'row': r, 'col': c}

    visited = [[False] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            cell = layout_data[r][c]
            if (cell == '' or cell is None) or visited[r][c]: continue
            num = str(cell).zfill(4)
            num_val = int(num)
            if (987 <= num_val <= 998) or (1370 <= num_val <= 1385): continue
            queue = [(r, c)]
            visited[r][c] = True
            island_cells = []
            while queue:
                cr, cc = queue.pop(0)
                cv = str(layout_data[cr][cc]).zfill(4)
                cv_val = int(cv)
                if (987 <= cv_val <= 998) or (1370 <= cv_val <= 1385): continue
                island_cells.append(cv)
                direction = lookup.get(cv, {}).get('direction', 'horizontal')
                if direction == 'horizontal':
                    neighbors = [(cr, cc - 1), (cr, cc + 1)]
                else:
                    neighbors = [(cr - 1, cc), (cr + 1, cc)]
                for nr, nc in neighbors:
                    if 0 <= nr < rows and 0 <= nc < cols and not visited[nr][nc]:
                        nc_cell = layout_data[nr][nc]
                        if nc_cell == '' or nc_cell is None: continue
                        nc_num = str(nc_cell).zfill(4)
                        if (987 <= int(nc_num) <= 998) or (1370 <= int(nc_num) <= 1385): continue
                        if lookup.get(nc_num, {}).get('direction') == direction:
                            visited[nr][nc] = True
                            queue.append((nr, nc))
            if island_cells:
                island_cells.sort(key=lambda x: int(x))
                island_id = f"{int(island_cells[0])}-{int(island_cells[-1])}"
                for nc in island_cells:
                    if nc in lookup:
                        lookup[nc]['island_id'] = island_id
    return lookup

def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM slot_data WHERE 機種名 LIKE '%ﾊﾅﾊﾅ%'", conn)
    conn.close()
    return df

def load_layout():
    with open(LAYOUT_PATH, encoding='utf-8') as f:
        return json.load(f)

def build_features(df, layout_lookup):
    df = df.copy()
    df['日付'] = pd.to_datetime(df['日付'])
    df['台番号_pad'] = df['台番号'].astype(str).str.zfill(4)
    df['推定設定'] = df.apply(lambda r: estimate_setting(r['機種名'], r['累計ゲーム'], r['BIG'], r['REG']), axis=1)

    df['position'] = df['台番号_pad'].apply(lambda x: layout_lookup.get(x, {}).get('pos', -1))
    df['position'] = df['position'].apply(lambda x: x if x in [0, 1, 2] else 3)
    df['island_id'] = df['台番号_pad'].apply(lambda x: layout_lookup.get(x, {}).get('island_id', ''))
    
    island_ids_unique = list(df['island_id'].unique())
    df['island_id_num'] = df['island_id'].apply(lambda x: island_ids_unique.index(x) if x in island_ids_unique else -1)

    df['tail_digit'] = df['台番号_pad'].apply(lambda x: int(x[-1]))
    df['weekday'] = df['日付'].dt.weekday
    df['day_of_month'] = df['日付'].dt.day
    df['is_event_day'] = df['day_of_month'].apply(lambda d: 1 if str(d).endswith(('3', '5', '8')) else 0)

    # 全日付一覧
    all_dates = sorted(df['日付'].unique())
    date_to_idx = {d: i for i, d in enumerate(all_dates)}

    # 島ごとの日別平均を事前計算
    island_daily_avg = df.groupby(['日付', 'island_id'])['最終差枚'].mean().to_dict()

    df_sorted = df.sort_values(['台番号_pad', '日付']).reset_index(drop=True)
    
    # 7日分の履歴を格納する辞書
    hist_feats = defaultdict(dict)
    
    for num, grp in df_sorted.groupby('台番号_pad'):
        grp = grp.sort_values('日付')
        diffs = grp['最終差枚'].tolist()
        settings = grp['推定設定'].tolist()
        games = grp['累計ゲーム'].tolist()
        dates = grp['日付'].tolist()
        island = grp['island_id'].iloc[0]

        cons_neg = 0
        cons_pos = 0
        
        # 過去7日間情報を保持するリスト
        # idxは日付順。歯抜けがある場合でも「その台の直近稼働日基準」とするか「暦日基準」にするか。
        # データリーク防止および正確な分析のため「暦日基準」で1日〜7日前を取得する。
        # ただし、データが存在しない日は0や-1とする。
        
        # 日付をキーにしたディクショナリを作成
        m_data = {d: {'diff': df, 'set': st, 'game': gm} for d, df, st, gm in zip(dates, diffs, settings, games)}
        
        for i, date in enumerate(dates):
            date_idx = date_to_idx[date]
            key = (num, date)
            
            # 連勝連敗の計算 (前日までの稼働日ベース)
            if i > 0:
                prev_diff = diffs[i-1]
                if prev_diff < 0:
                    cons_neg += 1
                    cons_pos = 0
                elif prev_diff > 0:
                    cons_pos += 1
                    cons_neg = 0
                else:
                    cons_neg = 0
                    cons_pos = 0
            
            hist_feats[key]['cons_neg'] = min(cons_neg, 6) # 0〜6以上
            hist_feats[key]['cons_pos'] = min(cons_pos, 6) # 0〜6以上
            
            # 1〜7日前の情報を取得
            for j in range(1, 8):
                if date_idx - j >= 0:
                    past_date = all_dates[date_idx - j]
                else:
                    past_date = None
                    
                if past_date and past_date in m_data:
                    pd_diff = m_data[past_date]['diff']
                    pd_game = m_data[past_date]['game']
                    pd_set = m_data[past_date]['set'] if pd.notna(m_data[past_date]['set']) else -1
                else:
                    pd_diff = 0
                    pd_game = 0
                    pd_set = -1
                
                if past_date:
                    i_avg = island_daily_avg.get((past_date, island), 0)
                else:
                    i_avg = 0
                
                hist_feats[key][f'prev_diff_{j}'] = pd_diff
                hist_feats[key][f'prev_games_{j}'] = pd_game
                hist_feats[key][f'island_avg_prev_{j}'] = i_avg
                
                if j == 1:
                    hist_feats[key]['prev_setting_1'] = pd_set
                    hist_feats[key]['prev_high_setting_1'] = 1 if pd_set >= 4 else 0

    # 特徴量をDFにマージ
    for col in ['cons_neg', 'cons_pos', 'prev_setting_1', 'prev_high_setting_1']:
        df[col] = df.apply(lambda r: hist_feats[(r['台番号_pad'], r['日付'])][col], axis=1)
        
    for j in range(1, 8):
        df[f'prev_diff_{j}'] = df.apply(lambda r: hist_feats[(r['台番号_pad'], r['日付'])][f'prev_diff_{j}'], axis=1)
        df[f'prev_games_{j}'] = df.apply(lambda r: hist_feats[(r['台番号_pad'], r['日付'])][f'prev_games_{j}'], axis=1)
        df[f'island_avg_prev_{j}'] = df.apply(lambda r: hist_feats[(r['台番号_pad'], r['日付'])][f'island_avg_prev_{j}'], axis=1)

    df = df.dropna(subset=FEATURE_COLS)
    return df

def filter_period(df, period_key):
    if period_key == 'all': return df
    elif period_key == 'day3': return df[df['day_of_month'].astype(str).str.endswith('3')]
    elif period_key == 'day5': return df[df['day_of_month'].astype(str).str.endswith('5')]
    elif period_key == 'day8': return df[df['day_of_month'].astype(str).str.endswith('8')]
    elif period_key == 'event': return df[df['is_event_day'] == 1]
    elif period_key == 'nonevent': return df[df['is_event_day'] == 0]
    return df

def analyze_decision_tree(X, y, task='regression'):
    if len(X) < 20: return {'error': 'サンプル数不足'}
    model = DecisionTreeRegressor(max_depth=4, min_samples_leaf=5, random_state=42) if task == 'regression' else DecisionTreeClassifier(max_depth=4, min_samples_leaf=5, random_state=42)
    model.fit(X, y)
    rules = export_text(model, feature_names=list(X.columns))
    return {'tree_rules': rules, 'n_samples': len(X)}

def analyze_feature_importance(X, y, task='regression'):
    if len(X) < 20: return {'error': 'サンプル数不足'}
    
    if task == 'regression':
        model = XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, tree_method='hist', device='cuda', random_state=42)
        scoring = ['r2']
    else:
        pos_sum = y.sum()
        spw = (len(y) - pos_sum) / pos_sum if pos_sum > 0 else 1
        model = XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, tree_method='hist', device='cuda', scale_pos_weight=spw, random_state=42)
        scoring = ['accuracy', 'precision', 'recall', 'f1']

    tscv = TimeSeriesSplit(n_splits=min(5, len(X) // 20))
    cv_res = cross_validate(model, X, y, cv=tscv, scoring=scoring)
    model.fit(X, y)
    importances = model.feature_importances_
    fi = [{'feature': col, 'feature_jp': FEATURE_NAMES_JP[col], 'importance': float(v)} for col, v in sorted(zip(X.columns, importances), key=lambda x: -x[1])]
    
    result = {'feature_importances': fi, 'n_samples': len(X)}
    if task == 'regression':
        result['cv_r2'] = float(np.mean(cv_res['test_r2']))
    else:
        result['cv_accuracy'] = float(np.mean(cv_res['test_accuracy']))
        result['cv_precision'] = float(np.mean(cv_res['test_precision']))
        result['cv_recall'] = float(np.mean(cv_res['test_recall']))
        result['cv_f1'] = float(np.mean(cv_res['test_f1']))
        y_pred = model.predict(X)
        cm = confusion_matrix(y, y_pred)
        result['confusion_matrix'] = cm.tolist()
        
        # Calculate TN, FP, FN, TP ratios
        tn, fp, fn, tp = cm.ravel()
        total = tn + fp + fn + tp
        result['tn_ratio'] = float(tn / total)
        result['fp_ratio'] = float(fp / total)
        result['fn_ratio'] = float(fn / total)
        result['tp_ratio'] = float(tp / total)
    return result

def analyze_association(df_period, task='regression'):
    if len(df_period) < 20: return {'error': 'サンプル数不足'}
    df = df_period.copy()
    bins_map = {}
    
    for v in range(10): bins_map[f'末尾={v}'] = (df['tail_digit'] == v).values
    day_names = ['月', '火', '水', '木', '金', '土', '日']
    for v in range(7): bins_map[f'曜日={day_names[v]}'] = (df['weekday'] == v).values
    pos_names = {0: '角', 1: '角2', 2: '角3', 3: 'その他'}
    for v, name in pos_names.items(): bins_map[f'位置={name}'] = (df['position'] == v).values

    for v in range(7):
        bins_map[f'連続凹み={v}日'] = (df['cons_neg'] == v).values
        bins_map[f'連続凸={v}日'] = (df['cons_pos'] == v).values

    # 1〜7日前の差枚を離散化
    import math
    prev_diff_bins = [
        (-math.inf, -2000, "<-2000枚"), (-2000, -1000, "-2000〜-1000枚"), 
        (-1000, -500, "-1000〜-500枚"), (-500, 0, "-500〜0枚"),
        (0, 500, "0〜500枚"), (500, 1000, "500〜1000枚"), 
        (1000, 2000, "1000〜2000枚"), (2000, math.inf, ">2000枚")
    ]
    for j in range(1, 8):
        for lo, hi, label in prev_diff_bins:
            bins_map[f'{j}日前差枚={label}'] = ((df[f'prev_diff_{j}'] > lo) & (df[f'prev_diff_{j}'] <= hi)).values

    bins_map['前日設定=不明'] = (df['prev_setting_1'] == -1).values
    for v in range(1, 6): bins_map[f'前日設定={v}'] = (df['prev_setting_1'] == v).values
    bins_map['前日高設定=あり'] = (df['prev_high_setting_1'] == 1).values
    bins_map['前日高設定=なし'] = (df['prev_high_setting_1'] == 0).values

    bins_map['イベント日=あり'] = (df['is_event_day'] == 1).values
    bins_map['イベント日=なし'] = (df['is_event_day'] == 0).values

    if task == 'regression':
        diff_bins = [(-math.inf, -1000, "<-1000枚"), (-1000, 0, "-1000〜0枚"), (0, 1000, "0〜1000枚"), (1000, 2000, "1000〜2000枚"), (2000, math.inf, ">2000枚")]
        target_labels = []
        for lo, hi, label in diff_bins:
            t_label = f'当日差枚={label}'
            bins_map[t_label] = ((df['最終差枚'] > lo) & (df['最終差枚'] <= hi)).values
            target_labels.append(t_label)
    else:
        bins_map['当日設定=高(4-5)'] = (df['高設定フラグ'] == 1).values
        bins_map['当日設定=低(1-3)'] = (df['高設定フラグ'] == 0).values
        target_labels = ['当日設定=高(4-5)', '当日設定=低(1-3)']

    assoc_df = pd.DataFrame(bins_map)
    try:
        freq = apriori(assoc_df, min_support=0.03, use_colnames=True, max_len=4)
        if freq.empty: return {'error': '頻出アイテムなし'}
        rules = association_rules(freq, metric='lift', min_threshold=1.1)
        rules = rules[rules['consequents'].apply(lambda cs: all(t in target_labels for t in cs) and len(cs) > 0) & 
                      rules['antecedents'].apply(lambda as_: all(t not in target_labels for t in as_) and len(as_) > 0)]
        rules = rules.sort_values('lift', ascending=False)
        top_rules = []
        for _, row in rules.head(50).iterrows(): # Show top 50
            top_rules.append({
                'antecedents': list(row['antecedents']), 'consequents': list(row['consequents']),
                'support': float(row['support']), 'confidence': float(row['confidence']), 'lift': float(row['lift']),
            })
        return {'rules': top_rules, 'n_samples': len(df), 'n_rules': len(rules)}
    except Exception as e:
        return {'error': str(e)}

def predict_next_day(df_feat):
    max_date = df_feat['日付'].max()
    next_date = max_date + pd.Timedelta(days=1)
    
    day_of_month = next_date.day
    weekday = next_date.weekday()
    is_event = 1 if str(day_of_month)[-1] in ['3', '5', '8'] else 0
    machine_nums = df_feat['台番号'].unique()
    
    next_X = []
    machines = []
    
    for num in machine_nums:
        m_hist = df_feat[df_feat['台番号'] == num].sort_values('日付')
        if m_hist.empty: continue
        last_row = m_hist.iloc[-1]
        
        # Build features for "tomorrow" based on history
        # We need to extract the past 7 days relative to next_date.
        feat = {
            'tail_digit': last_row['tail_digit'],
            'weekday': weekday,
            'position': last_row['position'],
            'is_event_day': is_event,
            'day_of_month': day_of_month,
            'island_id_num': last_row['island_id_num']
        }
        
        # Calculate cons_neg and cons_pos exactly at max_date ending
        cons_neg = int(last_row['cons_neg'])
        cons_pos = int(last_row['cons_pos'])
        if last_row['日付'] == max_date:
            last_diff = float(last_row['最終差枚'])
            if last_diff < 0:
                cons_neg += 1
                cons_pos = 0
            elif last_diff > 0:
                cons_pos += 1
                cons_neg = 0
            else:
                cons_neg = 0; cons_pos = 0
                
        feat['cons_neg'] = min(cons_neg, 6)
        feat['cons_pos'] = min(cons_pos, 6)
        
        # Build 1 to 7 days past info
        # We simulate what the script does: prev_diff_1 is max_date, prev_diff_2 is max_date - 1, etc.
        all_dates = sorted(df_feat['日付'].unique())
        date_to_idx = {d: i for i, d in enumerate(all_dates)}
        max_idx = len(all_dates) # Next day is max_idx
        
        for j in range(1, 8):
            target_idx = max_idx - j
            if target_idx >= 0 and target_idx < len(all_dates):
                target_date = all_dates[target_idx]
                r_hist = m_hist[m_hist['日付'] == target_date]
                if not r_hist.empty:
                    feat[f'prev_diff_{j}'] = r_hist['最終差枚'].values[0]
                    feat[f'prev_games_{j}'] = r_hist['累計ゲーム'].values[0]
                    feat[f'island_avg_prev_{j}'] = r_hist[f'island_avg_prev_{1}'].values[0] # wait, island avg is tricky.
                    if j == 1:
                        feat['prev_setting_1'] = r_hist['推定設定'].values[0] if pd.notna(r_hist['推定設定'].values[0]) else -1
                        feat['prev_high_setting_1'] = 1 if feat['prev_setting_1'] >= 4 else 0
                else:
                    feat[f'prev_diff_{j}'] = 0
                    feat[f'prev_games_{j}'] = 0
                    feat[f'island_avg_prev_{j}'] = 0
                    if j == 1:
                        feat['prev_setting_1'] = -1
                        feat['prev_high_setting_1'] = 0
            else:
                feat[f'prev_diff_{j}'] = 0
                feat[f'prev_games_{j}'] = 0
                feat[f'island_avg_prev_{j}'] = 0
                if j == 1:
                    feat['prev_setting_1'] = -1
                    feat['prev_high_setting_1'] = 0
                    
        # For island_avg_prev, we must pull the exact island average for that day.
        for j in range(1, 8):
            target_idx = max_idx - j
            if target_idx >= 0 and target_idx < len(all_dates):
                target_date = all_dates[target_idx]
                island_id = last_row['island_id']
                island_df = df_feat[(df_feat['日付'] == target_date) & (df_feat['island_id'] == island_id)]
                avg = island_df['最終差枚'].mean() if not island_df.empty else 0
                feat[f'island_avg_prev_{j}'] = avg
                
        next_X.append(feat)
        machines.append(num)
        
    df_next = pd.DataFrame(next_X)
    X_train_reg = df_feat[FEATURE_COLS].copy()
    y_train_reg = df_feat['最終差枚'].copy()
    reg_model = XGBRegressor(n_estimators=200, max_depth=5, learning_rate=0.05, tree_method='hist', device='cuda', random_state=42)
    reg_model.fit(X_train_reg, y_train_reg)
    pred_diffs = reg_model.predict(df_next[FEATURE_COLS])
    
    df_cls = df_feat[df_feat['推定設定'].notna()].copy()
    df_cls['高設定フラグ'] = (df_cls['推定設定'] >= 4).astype(int)
    X_train_cls = df_cls[FEATURE_COLS].copy()
    y_train_cls = df_cls['高設定フラグ'].copy()
    pos_sum = y_train_cls.sum()
    spw = (len(y_train_cls) - pos_sum) / pos_sum if pos_sum > 0 else 1
    cls_model = XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.05, tree_method='hist', device='cuda', scale_pos_weight=spw, random_state=42)
    cls_model.fit(X_train_cls, y_train_cls)
    pred_probs = cls_model.predict_proba(df_next[FEATURE_COLS])[:, 1]
    
    predictions = []
    for i, num in enumerate(machines):
        feat_clean = {k: v.item() if hasattr(v, 'item') else v for k, v in next_X[i].items()}
        predictions.append({
            'machine': str(num).zfill(4),
            'expected_diff': float(pred_diffs[i]),
            'prob_high_setting': float(pred_probs[i]),
            'features': feat_clean
        })
    predictions.sort(key=lambda x: x['prob_high_setting'], reverse=True)
    return {'target_date': next_date.strftime('%Y-%m-%d'), 'is_event': is_event == 1, 'predictions': predictions[:30]}

def run_all_analysis(df_feat):
    results = {}
    for period_key, period_label in PERIOD_LABELS.items():
        df_p = filter_period(df_feat, period_key)
        results[period_key] = {'label': period_label, 'n_total': int(len(df_p))}
        X_reg = df_p[FEATURE_COLS].copy()
        y_reg = df_p['最終差枚'].copy()
        results[period_key]['regression_tree'] = analyze_decision_tree(X_reg, y_reg, 'regression')
        results[period_key]['regression_rf'] = analyze_feature_importance(X_reg, y_reg, 'regression')
        results[period_key]['regression_assoc'] = analyze_association(df_p, 'regression')
        df_cls = df_p[df_p['推定設定'].notna()].copy()
        df_cls['高設定フラグ'] = (df_cls['推定設定'] >= 4).astype(int)
        if len(df_cls) >= 20 and df_cls['高設定フラグ'].sum() >= 5:
            X_cls = df_cls[FEATURE_COLS].copy()
            y_cls = df_cls['高設定フラグ'].copy()
            results[period_key]['cls_tree'] = analyze_decision_tree(X_cls, y_cls, 'classification')
            results[period_key]['cls_rf'] = analyze_feature_importance(X_cls, y_cls, 'classification')
            results[period_key]['cls_assoc'] = analyze_association(df_cls, 'classification')
        else:
            msg = {'error': 'サンプル不足'}
            results[period_key]['cls_tree'] = results[period_key]['cls_rf'] = results[period_key]['cls_assoc'] = msg
        results[period_key]['n_cls'] = int(len(df_cls))
        results[period_key]['n_high'] = int(df_cls['高設定フラグ'].sum())
    return results

if __name__ == '__main__':
    df = load_data()
    layout = load_layout()
    lookup = build_layout_lookup(layout)
    df_feat = build_features(df, lookup)
    results = run_all_analysis(df_feat)
    results['next_day_predictions'] = predict_next_day(df_feat)
    results['feature_names_jp'] = FEATURE_NAMES_JP
    import json
    json_str = pd.Series([results]).to_json(orient='records', force_ascii=False)
    json_str = json_str[1:-1]
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(json_str)
"""

with open('scratch/ml_analysis.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
