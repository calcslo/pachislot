# -*- coding: utf-8 -*-
"""
ハナハナ 高設定条件分析スクリプト (GPU/XGBoost, 過去7日間対応)
"""
import sqlite3
import json
import math
import numpy as np
import pandas as pd
from datetime import datetime
from collections import defaultdict

from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier, export_text
from xgboost import XGBRegressor, XGBClassifier
import lightgbm as lgb
from catboost import CatBoostClassifier
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
TARGET_POSITIVE_RATE = 0.255

MACHINE_PROBS = {
    'LBﾆｭｰｷﾝｸﾞﾊﾅﾊﾅV': {
        1: {'big': 319, 'reg': 619},
        2: {'big': 299, 'reg': 510},
        3: {'big': 282, 'reg': 469},
        4: {'big': 265, 'reg': 387},
        5: {'big': 248, 'reg': 325},
        6: {'big': 230, 'reg': 273},
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
    'machine_num': '台番号',
    'tail_digit': '台番号末尾',
    'weekday': '曜日',
    'weekday_sin': '曜日周期(sin)',
    'weekday_cos': '曜日周期(cos)',
    'position': '角からの位置',
    'cons_neg': '連続凹み日数',
    'cons_pos': '連続凸日数',
    'is_event_day': 'イベント日',
    'day_of_month': '月内日付',
    'day_sin': '月内日付周期(sin)',
    'day_cos': '月内日付周期(cos)',
    'day_last_digit': '日付末尾',
    'is_same_tail_as_day': '台末尾と日付末尾が一致',
    'is_tail_3_5_8': '台末尾が3/5/8',
    'island_id_num': '所属島ID(数値化)',
    'prev_setting_1': '前日設定',
    'prev_high_setting_1': '前日高設定(4以上)',
    'neg_after_pos': '前日高設定後凹み(0/1)',
    'cumul_7d_diff': '過去7日累積差枚',
    'cumul_14d_diff': '過去14日累積差枚',
    'cumul_21d_diff': '過去21日累積差枚',
    'island_trend': '島の直近傾向(3日平均差枚)',
    'win_rate_7d': '直近7日間勝率',
    'win_rate_14d': '直近14日間勝率',
    'volatility_7d': '直近7日間差枚ボラティリティ',
    'avg_games_7d': '直近7日間平均G数',
    'island_avg_7d': '島平均差枚(過去7日)',
    'ewm_diff_7d': '指数平滑移動平均(7日)',
    'setting_change_signal': '設定変更シグナル(前日高設定大凹み)',
    'momentum_1v3': 'モメンタム(前日vs3日前)',
    'revival_score': '復活期待度スコア',
    'same_wd_avg_diff': '同曜日平均差枚(過去4週)',
    'same_wd_win_rate': '同曜日勝率(過去4週)',
    'layout_row': '島図の行',
    'layout_col': '島図の列',
    'island_size': '同一島の台数',
    'island_pos_ratio': '島内位置比率',
    'store_high_ratio': '店舗全体高設定比率(前日)',
    'store_avg_prev_1d': '店舗平均差枚(前日)',
    'store_win_prev_1d': '店舗勝率(前日)',
    'store_high_prev_3d': '店舗高設定比率(過去3日)',
    'store_avg_prev_3d': '店舗平均差枚(過去3日)',
    'store_win_prev_3d': '店舗勝率(過去3日)',
    'tail_high_prev_3d': '同末尾高設定率(過去3日)',
    'tail_high_prev_7d': '同末尾高設定率(過去7日)',
    'tail_high_prev_14d': '同末尾高設定率(過去14日)',
    'tail_avg_prev_3d': '同末尾平均差枚(過去3日)',
    'tail_avg_prev_7d': '同末尾平均差枚(過去7日)',
    'tail_avg_prev_14d': '同末尾平均差枚(過去14日)',
    'tail_win_prev_3d': '同末尾勝率(過去3日)',
    'tail_win_prev_7d': '同末尾勝率(過去7日)',
    'tail_win_prev_14d': '同末尾勝率(過去14日)',
    'tail_event_high_prev_3d': '同末尾×特定日高設定率(過去3日)',
    'tail_event_high_prev_7d': '同末尾×特定日高設定率(過去7日)',
    'tail_event_high_prev_14d': '同末尾×特定日高設定率(過去14日)',
    'tail_event_avg_prev_3d': '同末尾×特定日平均差枚(過去3日)',
    'tail_event_avg_prev_7d': '同末尾×特定日平均差枚(過去7日)',
    'tail_event_avg_prev_14d': '同末尾×特定日平均差枚(過去14日)',
    'tail_event_win_prev_3d': '同末尾×特定日勝率(過去3日)',
    'tail_event_win_prev_7d': '同末尾×特定日勝率(過去7日)',
    'tail_event_win_prev_14d': '同末尾×特定日勝率(過去14日)',
    'machine_high_rate_prev_14d': '自台高設定率(過去14稼働日)',
    'machine_avg_diff_prev_14d': '自台平均差枚(過去14稼働日)',
    'island_high_ratio_3d': '自島高設定比率(過去3日)',
    'adj_left_diff_1': '左隣前日差枚',
    'adj_right_diff_1': '右隣前日差枚',
    'adj_left_win_rate_3d': '左隣過去3日勝率',
    'adj_right_win_rate_3d': '右隣過去3日勝率',
    'adj_avg_diff_1': '両隣平均前日差枚'
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
    df['layout_row'] = df['台番号_pad'].apply(lambda x: layout_lookup.get(x, {}).get('row', -1))
    df['layout_col'] = df['台番号_pad'].apply(lambda x: layout_lookup.get(x, {}).get('col', -1))
    
    island_ids_unique = list(df['island_id'].unique())
    df['island_id_num'] = df['island_id'].apply(lambda x: island_ids_unique.index(x) if x in island_ids_unique else -1)
    df['island_size'] = df.groupby('island_id')['台番号'].transform('nunique').fillna(0)
    df['island_pos_ratio'] = df['position'] / df['island_size'].clip(lower=1)

    df['machine_num'] = df['台番号'].astype(int)
    df['tail_digit'] = df['台番号_pad'].apply(lambda x: int(x[-1]))
    df['weekday'] = df['日付'].dt.weekday
    df['day_of_month'] = df['日付'].dt.day
    df['is_event_day'] = df['day_of_month'].apply(lambda d: 1 if str(d).endswith(('3', '5', '8')) else 0)
    df['weekday_sin'] = np.sin(2 * np.pi * df['weekday'] / 7)
    df['weekday_cos'] = np.cos(2 * np.pi * df['weekday'] / 7)
    df['day_sin'] = np.sin(2 * np.pi * df['day_of_month'] / 31)
    df['day_cos'] = np.cos(2 * np.pi * df['day_of_month'] / 31)
    df['day_last_digit'] = df['day_of_month'] % 10
    df['is_same_tail_as_day'] = (df['tail_digit'] == df['day_last_digit']).astype(int)
    df['is_tail_3_5_8'] = df['tail_digit'].isin([3, 5, 8]).astype(int)

    # 全日付一覧
    all_dates = sorted(df['日付'].unique())
    date_to_idx = {d: i for i, d in enumerate(all_dates)}

    # 島ごとの日別平均を事前計算
    island_daily_avg = df.groupby(['日付', 'island_id'])['最終差枚'].mean().to_dict()
    
    # 店舗全体の設定比率（日別）
    date_high_ratio = {}
    for date, grp in df[df['推定設定'].notna()].groupby('日付'):
        date_high_ratio[date] = float((grp['推定設定'] >= 4).mean())

    # 店舗全体の日別傾向。学習時も予測時も前日以前だけを使う。
    date_avg_diff = df.groupby('日付')['最終差枚'].mean().to_dict()
    date_win_rate = df.groupby('日付')['最終差枚'].apply(lambda s: float((s > 0).mean())).to_dict()

    def prev_date_mean(values, date_idx, window):
        prev_dates = all_dates[max(0, date_idx - window):date_idx]
        vals = [values.get(d, 0.0) for d in prev_dates]
        return float(np.mean(vals)) if vals else 0.0

    def add_group_rolling_features(base_df, group_cols, prefix, windows=(3, 7, 14)):
        daily = (
            base_df.groupby(['日付'] + group_cols)
            .agg(
                high=('推定設定', lambda s: float((s.dropna() >= 4).mean()) if len(s.dropna()) > 0 else 0.0),
                avg=('最終差枚', 'mean'),
                win=('最終差枚', lambda s: float((s > 0).mean()))
            )
            .reset_index()
            .sort_values(group_cols + ['日付'])
        )
        gen_cols = []
        for w in windows:
            for metric in ['high', 'avg', 'win']:
                col = f'{prefix}_{metric}_prev_{w}d'
                gen_cols.append(col)
                daily[col] = daily.groupby(group_cols)[metric].transform(
                    lambda s, window=w: s.shift(1).rolling(window, min_periods=1).mean()
                )
        return base_df.merge(daily[['日付'] + group_cols + gen_cols], on=['日付'] + group_cols, how='left'), gen_cols

    df, tail_cols = add_group_rolling_features(df, ['tail_digit'], 'tail')
    df, tail_event_cols = add_group_rolling_features(df, ['tail_digit', 'is_event_day'], 'tail_event')
    for col in tail_cols + tail_event_cols:
        df[col] = df[col].fillna(0)
        
    # 島ごとの設定比率（日別）
    island_date_high_ratio = {}
    for (date, island_id), grp in df[df['推定設定'].notna()].groupby(['日付', 'island_id']):
        island_date_high_ratio[(date, island_id)] = float((grp['推定設定'] >= 4).mean())

    # 全台の日別データ辞書 (両隣の特徴量計算用)
    daily_machine_stats = defaultdict(dict)
    for date, m_num, diff, st in zip(df['日付'], df['台番号'].astype(int), df['最終差枚'], df['推定設定']):
        daily_machine_stats[date][m_num] = {'diff': diff, 'set': st}

    df_sorted = df.sort_values(['台番号_pad', '日付']).reset_index(drop=True)
    
    MAX_LAG = 21
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
        
        m_data = {d: {'diff': df_, 'set': st, 'game': gm} for d, df_, st, gm in zip(dates, diffs, settings, games)}
        
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
            
            # 1〜MAX_LAG日前の情報を取得
            for j in range(1, MAX_LAG + 1):
                past_date = all_dates[date_idx - j] if date_idx - j >= 0 else None
                    
                if past_date and past_date in m_data:
                    pd_diff = m_data[past_date]['diff']
                    pd_game = m_data[past_date]['game']
                    pd_set = m_data[past_date]['set'] if pd.notna(m_data[past_date]['set']) else -1
                else:
                    pd_diff = 0
                    pd_game = 0
                    pd_set = -1
                
                i_avg = island_daily_avg.get((past_date, island), 0) if past_date else 0
                
                hist_feats[key][f'prev_diff_{j}'] = pd_diff
                hist_feats[key][f'prev_games_{j}'] = pd_game
                if j <= 7:
                    hist_feats[key][f'island_avg_prev_{j}'] = i_avg
                
                if j == 1:
                    hist_feats[key]['prev_setting_1'] = pd_set
                    hist_feats[key]['prev_high_setting_1'] = 1 if pd_set >= 4 else 0

            # 同曜日の過去パターン（直近4週）
            same_wd_diffs = []
            for w in range(1, 5):
                past_wd_date = all_dates[date_idx - w*7] if date_idx - w*7 >= 0 else None
                if past_wd_date and past_wd_date in m_data:
                    same_wd_diffs.append(m_data[past_wd_date]['diff'])
            hist_feats[key]['same_wd_avg_diff'] = np.mean(same_wd_diffs) if same_wd_diffs else 0
            hist_feats[key]['same_wd_win_rate'] = sum(1 for x in same_wd_diffs if x > 0) / len(same_wd_diffs) if same_wd_diffs else 0
            
            # 店舗全体の傾向。現在日の答えを混ぜないため、前日以前だけを参照する。
            hist_feats[key]['store_high_ratio'] = prev_date_mean(date_high_ratio, date_idx, 1)
            hist_feats[key]['store_high_prev_3d'] = prev_date_mean(date_high_ratio, date_idx, 3)
            hist_feats[key]['store_avg_prev_1d'] = prev_date_mean(date_avg_diff, date_idx, 1)
            hist_feats[key]['store_avg_prev_3d'] = prev_date_mean(date_avg_diff, date_idx, 3)
            hist_feats[key]['store_win_prev_1d'] = prev_date_mean(date_win_rate, date_idx, 1)
            hist_feats[key]['store_win_prev_3d'] = prev_date_mean(date_win_rate, date_idx, 3)
            prev_highs = [1 if pd.notna(s) and s >= 4 else 0 for s in settings[max(0, i - 14):i]]
            prev_diffs_14 = diffs[max(0, i - 14):i]
            hist_feats[key]['machine_high_rate_prev_14d'] = float(np.mean(prev_highs)) if prev_highs else 0.0
            hist_feats[key]['machine_avg_diff_prev_14d'] = float(np.mean(prev_diffs_14)) if prev_diffs_14 else 0.0
            
            # 空間的特徴量
            past_date_1 = all_dates[date_idx - 1] if date_idx - 1 >= 0 else None
            m_num_int = int(num)
            if past_date_1:
                hist_feats[key]['adj_left_diff_1'] = daily_machine_stats[past_date_1].get(m_num_int - 1, {}).get('diff', 0)
                hist_feats[key]['adj_right_diff_1'] = daily_machine_stats[past_date_1].get(m_num_int + 1, {}).get('diff', 0)
                hist_feats[key]['adj_avg_diff_1'] = (hist_feats[key]['adj_left_diff_1'] + hist_feats[key]['adj_right_diff_1']) / 2
                
                left_wins, right_wins, left_count, right_count = 0, 0, 0, 0
                island_high_ratios = []
                for k in range(1, 4):
                    p_date = all_dates[date_idx - k] if date_idx - k >= 0 else None
                    if p_date:
                        ld = daily_machine_stats[p_date].get(m_num_int - 1, {}).get('diff')
                        rd = daily_machine_stats[p_date].get(m_num_int + 1, {}).get('diff')
                        if ld is not None:
                            left_wins += 1 if ld > 0 else 0
                            left_count += 1
                        if rd is not None:
                            right_wins += 1 if rd > 0 else 0
                            right_count += 1
                        island_high_ratios.append(island_date_high_ratio.get((p_date, island), 0))
                
                hist_feats[key]['adj_left_win_rate_3d'] = left_wins / left_count if left_count > 0 else 0
                hist_feats[key]['adj_right_win_rate_3d'] = right_wins / right_count if right_count > 0 else 0
                hist_feats[key]['island_high_ratio_3d'] = np.mean(island_high_ratios) if island_high_ratios else 0
            else:
                for col in ['adj_left_diff_1', 'adj_right_diff_1', 'adj_avg_diff_1', 'adj_left_win_rate_3d', 'adj_right_win_rate_3d', 'island_high_ratio_3d']:
                    hist_feats[key][col] = 0

    # 特徴量をDFにマージ
    spatial_cols = ['adj_left_diff_1', 'adj_right_diff_1', 'adj_avg_diff_1', 'adj_left_win_rate_3d', 'adj_right_win_rate_3d', 'island_high_ratio_3d']
    store_cols = ['store_high_ratio', 'store_high_prev_3d', 'store_avg_prev_1d', 'store_avg_prev_3d', 'store_win_prev_1d', 'store_win_prev_3d']
    machine_roll_cols = ['machine_high_rate_prev_14d', 'machine_avg_diff_prev_14d']
    for col in ['cons_neg', 'cons_pos', 'prev_setting_1', 'prev_high_setting_1', 'same_wd_avg_diff', 'same_wd_win_rate'] + store_cols + machine_roll_cols + spatial_cols:
        df[col] = df.apply(lambda r: hist_feats[(r['台番号_pad'], r['日付'])].get(col, 0), axis=1)

    df = df.copy()
    for j in range(1, MAX_LAG + 1):
        df[f'prev_diff_{j}'] = df.apply(lambda r: hist_feats[(r['台番号_pad'], r['日付'])].get(f'prev_diff_{j}', 0), axis=1)
        df[f'prev_games_{j}'] = df.apply(lambda r: hist_feats[(r['台番号_pad'], r['日付'])].get(f'prev_games_{j}', 0), axis=1)
        if j <= 7:
            df[f'island_avg_prev_{j}'] = df.apply(lambda r: hist_feats[(r['台番号_pad'], r['日付'])].get(f'island_avg_prev_{j}', 0), axis=1)

    # 派生特徴量
    df['neg_after_pos'] = ((df['prev_high_setting_1'] == 1) & (df['prev_diff_1'] < 0)).astype(int)
    df['cumul_7d_diff'] = sum(df[f'prev_diff_{j}'] for j in range(1, 8))
    df['cumul_14d_diff'] = sum(df[f'prev_diff_{j}'] for j in range(1, 15))
    df['cumul_21d_diff'] = sum(df[f'prev_diff_{j}'] for j in range(1, 22))
    df['island_trend'] = (df['island_avg_prev_1'] + df['island_avg_prev_2'] + df['island_avg_prev_3']) / 3
    df['win_rate_7d'] = sum((df[f'prev_diff_{j}'] > 0).astype(int) for j in range(1, 8)) / 7.0
    df['win_rate_14d'] = sum((df[f'prev_diff_{j}'] > 0).astype(int) for j in range(1, 15)) / 14.0
    df['volatility_7d'] = df[[f'prev_diff_{j}' for j in range(1, 8)]].std(axis=1).fillna(0)
    df['avg_games_7d'] = df[[f'prev_games_{j}' for j in range(1, 8)]].mean(axis=1)
    df['island_avg_7d'] = sum(df[f'island_avg_prev_{j}'] for j in range(1, 8)) / 7.0
    
    # EWM（指数加重移動平均）
    diff_cols_7 = [f'prev_diff_{j}' for j in range(1, 8)]
    df['ewm_diff_7d'] = df[diff_cols_7].apply(lambda row: pd.Series(row.values).ewm(span=3).mean().iloc[-1] if len(row.values) > 0 else 0, axis=1)
    
    # 設定変更検出（前日設定4以上→今日凹み）
    df['setting_change_signal'] = ((df['prev_setting_1'] >= 4) & (df['prev_diff_1'] < -500)).astype(int)
    
    # 直近 momentum（前日差枚 vs 3日前差枚）
    df['momentum_1v3'] = df['prev_diff_1'] - df['prev_diff_3']
    
    # 台の「復活確率」（連続凹み日数 × 店舗全体の設定比率）
    df['revival_score'] = df['cons_neg'] * df['store_high_ratio']

    base_cols = [c for c in FEATURE_COLS if c in df.columns]
    df = df.dropna(subset=base_cols)
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
        # 強めの正則化を入れて過学習・負のR2を抑制
        model = XGBRegressor(n_estimators=100, max_depth=3, learning_rate=0.05, 
                             reg_lambda=10, reg_alpha=5, subsample=0.8,
                             tree_method='hist', device='cuda', random_state=42)
        scoring = ['r2']
    else:
        from sklearn.ensemble import ExtraTreesClassifier
        model = ExtraTreesClassifier(
            n_estimators=500, max_depth=9, min_samples_leaf=25,
            max_features=0.7, class_weight='balanced_subsample',
            random_state=42, n_jobs=-1
        )
        scoring = ['accuracy', 'precision', 'recall', 'f1']

    if task == 'regression':
        tscv = TimeSeriesSplit(n_splits=min(5, len(X) // 20))
        cv_res = cross_validate(model, X, y, cv=tscv, scoring=scoring)
        model.fit(X, y)
        importances = model.feature_importances_
        fi = [{'feature': col, 'feature_jp': FEATURE_NAMES_JP[col], 'importance': float(v)} for col, v in sorted(zip(X.columns, importances), key=lambda x: -x[1])]
        result = {'feature_importances': fi, 'n_samples': len(X)}
        result['cv_r2'] = float(np.mean(cv_res['test_r2']))
    else:
        from sklearn.model_selection import StratifiedKFold, cross_val_predict
        n_splits = min(5, int(y.sum()), int(len(y) - y.sum()))
        if n_splits < 2: n_splits = 2
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        
        oof_prob = cross_val_predict(model, X, y, cv=skf, method='predict_proba')[:, 1]
        
        # 評価用閾値: FPを抑えつつ見逃しを減らすため、上位25.5%を候補化する。
        best_th = np.percentile(oof_prob, 100 * (1 - TARGET_POSITIVE_RATE))
        y_pred = (oof_prob >= best_th).astype(int)
        
        model.fit(X, y)
        importances = model.feature_importances_
        fi = [{'feature': col, 'feature_jp': FEATURE_NAMES_JP[col], 'importance': float(v)} for col, v in sorted(zip(X.columns, importances), key=lambda x: -x[1])]
        
        result = {'feature_importances': fi, 'n_samples': len(X)}
        result['cv_accuracy'] = float(np.mean(y_pred == y))
        result['cv_precision'] = float(precision_score(y, y_pred, zero_division=0))
        result['cv_recall'] = float(recall_score(y, y_pred, zero_division=0))
        result['cv_f1'] = float(f1_score(y, y_pred, zero_division=0))
        result['threshold'] = float(best_th)
        result['positive_rate'] = float(np.mean(y_pred))
        
        cm = confusion_matrix(y, y_pred)
        result['confusion_matrix'] = cm.tolist()
        
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
    all_dates = sorted(df_feat['日付'].unique())
    max_idx = len(all_dates) # Next day is max_idx
    store_daily = df_feat.groupby('日付').agg(
        avg_diff=('最終差枚', 'mean'),
        win_rate=('最終差枚', lambda s: float((s > 0).mean())),
        high_ratio=('推定設定', lambda s: float((s.dropna() >= 4).mean()) if len(s.dropna()) > 0 else 0.0)
    ).reindex(all_dates).fillna(0)

    def recent_store_mean(col, window):
        vals = store_daily[col].iloc[max(0, max_idx - window):max_idx]
        return float(vals.mean()) if len(vals) > 0 else 0.0

    def recent_group_stats(mask, window):
        grp = df_feat[mask].copy()
        if grp.empty:
            return {'high': 0.0, 'avg': 0.0, 'win': 0.0}
        daily = grp.groupby('日付').agg(
            high=('推定設定', lambda s: float((s.dropna() >= 4).mean()) if len(s.dropna()) > 0 else 0.0),
            avg=('最終差枚', 'mean'),
            win=('最終差枚', lambda s: float((s > 0).mean()))
        ).sort_index()
        recent = daily.tail(window)
        if recent.empty:
            return {'high': 0.0, 'avg': 0.0, 'win': 0.0}
        return {
            'high': float(recent['high'].mean()),
            'avg': float(recent['avg'].mean()),
            'win': float(recent['win'].mean()),
        }
    
    next_X = []
    machines = []
    
    for num in machine_nums:
        m_hist = df_feat[df_feat['台番号'] == num].sort_values('日付')
        if m_hist.empty: continue
        last_row = m_hist.iloc[-1]
        
        # Build features for "tomorrow" based on history
        # We need to extract the past MAX_LAG days relative to next_date.
        MAX_LAG = 21
        feat = {
            'machine_num': int(num),
            'tail_digit': last_row['tail_digit'],
            'weekday': weekday,
            'position': last_row['position'],
            'is_event_day': is_event,
            'day_of_month': day_of_month,
            'weekday_sin': np.sin(2 * np.pi * weekday / 7),
            'weekday_cos': np.cos(2 * np.pi * weekday / 7),
            'day_sin': np.sin(2 * np.pi * day_of_month / 31),
            'day_cos': np.cos(2 * np.pi * day_of_month / 31),
            'day_last_digit': day_of_month % 10,
            'island_id_num': last_row['island_id_num'],
            'layout_row': last_row.get('layout_row', -1),
            'layout_col': last_row.get('layout_col', -1),
            'island_size': last_row.get('island_size', 0),
            'island_pos_ratio': last_row.get('island_pos_ratio', 0)
        }
        feat['is_same_tail_as_day'] = 1 if int(feat['tail_digit']) == int(feat['day_last_digit']) else 0
        feat['is_tail_3_5_8'] = 1 if int(feat['tail_digit']) in [3, 5, 8] else 0
        
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
        m_recent_14 = m_hist.tail(14)
        if not m_recent_14.empty:
            feat['machine_high_rate_prev_14d'] = float((m_recent_14['推定設定'].dropna() >= 4).mean()) if m_recent_14['推定設定'].notna().any() else 0.0
            feat['machine_avg_diff_prev_14d'] = float(m_recent_14['最終差枚'].mean())
        else:
            feat['machine_high_rate_prev_14d'] = 0.0
            feat['machine_avg_diff_prev_14d'] = 0.0

        for w in [3, 7, 14]:
            tail_stats = recent_group_stats(df_feat['tail_digit'] == feat['tail_digit'], w)
            tail_event_stats = recent_group_stats(
                (df_feat['tail_digit'] == feat['tail_digit']) & (df_feat['is_event_day'] == is_event), w
            )
            for metric in ['high', 'avg', 'win']:
                feat[f'tail_{metric}_prev_{w}d'] = tail_stats[metric]
                feat[f'tail_event_{metric}_prev_{w}d'] = tail_event_stats[metric]
        
        # Build 1 to MAX_LAG days past info
        m_hist_dict = m_hist.set_index('日付').to_dict('index')
        
        same_wd_diffs = []
        for j in range(1, MAX_LAG + 1):
            target_idx = max_idx - j
            if target_idx >= 0 and target_idx < len(all_dates):
                target_date = all_dates[target_idx]
                r_hist = m_hist_dict.get(target_date)
                if r_hist:
                    feat[f'prev_diff_{j}'] = r_hist['最終差枚']
                    feat[f'prev_games_{j}'] = r_hist['累計ゲーム']
                    if j == 1:
                        feat['prev_setting_1'] = r_hist['推定設定'] if pd.notna(r_hist['推定設定']) else -1
                        feat['prev_high_setting_1'] = 1 if feat['prev_setting_1'] >= 4 else 0
                else:
                    feat[f'prev_diff_{j}'] = 0
                    feat[f'prev_games_{j}'] = 0
                    if j == 1:
                        feat['prev_setting_1'] = -1
                        feat['prev_high_setting_1'] = 0
            else:
                feat[f'prev_diff_{j}'] = 0
                feat[f'prev_games_{j}'] = 0
                if j == 1:
                    feat['prev_setting_1'] = -1
                    feat['prev_high_setting_1'] = 0
                    
            if j % 7 == 0 and j <= 28:
                # same weekday diffs
                if target_idx >= 0 and target_idx < len(all_dates):
                    target_date = all_dates[target_idx]
                    r_hist = m_hist_dict.get(target_date)
                    if r_hist:
                        same_wd_diffs.append(r_hist['最終差枚'])
        
        feat['same_wd_avg_diff'] = np.mean(same_wd_diffs) if same_wd_diffs else 0
        feat['same_wd_win_rate'] = sum(1 for x in same_wd_diffs if x > 0) / len(same_wd_diffs) if same_wd_diffs else 0
                    
        # For island_avg_prev, we must pull the exact island average for that day.
        for j in range(1, 8):
            target_idx = max_idx - j
            if target_idx >= 0 and target_idx < len(all_dates):
                target_date = all_dates[target_idx]
                island_id = last_row['island_id']
                island_df = df_feat[(df_feat['日付'] == target_date) & (df_feat['island_id'] == island_id)]
                avg = island_df['最終差枚'].mean() if not island_df.empty else 0
                feat[f'island_avg_prev_{j}'] = avg
            else:
                feat[f'island_avg_prev_{j}'] = 0
                
        # Store high ratio & Spatial Features
        m_num_int = int(num)
        if max_idx - 1 >= 0:
            last_date = all_dates[max_idx - 1]
            ld_df = df_feat[(df_feat['日付'] == last_date) & df_feat['推定設定'].notna()]
            feat['store_high_ratio'] = float((ld_df['推定設定'] >= 4).mean()) if not ld_df.empty else 0.0
            feat['store_high_prev_3d'] = recent_store_mean('high_ratio', 3)
            feat['store_avg_prev_1d'] = recent_store_mean('avg_diff', 1)
            feat['store_avg_prev_3d'] = recent_store_mean('avg_diff', 3)
            feat['store_win_prev_1d'] = recent_store_mean('win_rate', 1)
            feat['store_win_prev_3d'] = recent_store_mean('win_rate', 3)
            
            # 空間的特徴量 (1日前)
            left_1 = df_feat[(df_feat['日付'] == last_date) & (df_feat['台番号'].astype(int) == m_num_int - 1)]
            right_1 = df_feat[(df_feat['日付'] == last_date) & (df_feat['台番号'].astype(int) == m_num_int + 1)]
            feat['adj_left_diff_1'] = left_1['最終差枚'].values[0] if not left_1.empty else 0
            feat['adj_right_diff_1'] = right_1['最終差枚'].values[0] if not right_1.empty else 0
            feat['adj_avg_diff_1'] = (feat['adj_left_diff_1'] + feat['adj_right_diff_1']) / 2
            
            left_wins, right_wins, left_count, right_count = 0, 0, 0, 0
            island_high_ratios = []
            for k in range(1, 4):
                if max_idx - k >= 0:
                    p_date = all_dates[max_idx - k]
                    left_k = df_feat[(df_feat['日付'] == p_date) & (df_feat['台番号'].astype(int) == m_num_int - 1)]
                    right_k = df_feat[(df_feat['日付'] == p_date) & (df_feat['台番号'].astype(int) == m_num_int + 1)]
                    
                    if not left_k.empty:
                        left_wins += 1 if left_k['最終差枚'].values[0] > 0 else 0
                        left_count += 1
                    if not right_k.empty:
                        right_wins += 1 if right_k['最終差枚'].values[0] > 0 else 0
                        right_count += 1
                        
                    island_df_k = df_feat[(df_feat['日付'] == p_date) & (df_feat['island_id'] == last_row['island_id']) & df_feat['推定設定'].notna()]
                    if not island_df_k.empty:
                        island_high_ratios.append(float((island_df_k['推定設定'] >= 4).mean()))
                        
            feat['adj_left_win_rate_3d'] = left_wins / left_count if left_count > 0 else 0
            feat['adj_right_win_rate_3d'] = right_wins / right_count if right_count > 0 else 0
            feat['island_high_ratio_3d'] = np.mean(island_high_ratios) if island_high_ratios else 0
            
        else:
            feat['store_high_ratio'] = 0.0
            feat['store_high_prev_3d'] = 0.0
            feat['store_avg_prev_1d'] = 0.0
            feat['store_avg_prev_3d'] = 0.0
            feat['store_win_prev_1d'] = 0.0
            feat['store_win_prev_3d'] = 0.0
            feat['adj_left_diff_1'] = 0
            feat['adj_right_diff_1'] = 0
            feat['adj_avg_diff_1'] = 0
            feat['adj_left_win_rate_3d'] = 0
            feat['adj_right_win_rate_3d'] = 0
            feat['island_high_ratio_3d'] = 0

        next_X.append(feat)
        machines.append(num)
        
    df_next = pd.DataFrame(next_X)
    
    # 派生特徴量を予測データにも追加
    df_next['neg_after_pos'] = ((df_next['prev_high_setting_1'] == 1) & (df_next['prev_diff_1'] < 0)).astype(int)
    df_next['cumul_7d_diff'] = sum(df_next[f'prev_diff_{j}'] for j in range(1, 8))
    df_next['cumul_14d_diff'] = sum(df_next[f'prev_diff_{j}'] for j in range(1, 15))
    df_next['cumul_21d_diff'] = sum(df_next[f'prev_diff_{j}'] for j in range(1, 22))
    df_next['island_trend'] = (df_next['island_avg_prev_1'] + df_next['island_avg_prev_2'] + df_next['island_avg_prev_3']) / 3
    df_next['win_rate_7d'] = sum((df_next[f'prev_diff_{j}'] > 0).astype(int) for j in range(1, 8)) / 7.0
    df_next['win_rate_14d'] = sum((df_next[f'prev_diff_{j}'] > 0).astype(int) for j in range(1, 15)) / 14.0
    df_next['volatility_7d'] = df_next[[f'prev_diff_{j}' for j in range(1, 8)]].std(axis=1).fillna(0)
    df_next['avg_games_7d'] = df_next[[f'prev_games_{j}' for j in range(1, 8)]].mean(axis=1)
    df_next['island_avg_7d'] = sum(df_next[f'island_avg_prev_{j}'] for j in range(1, 8)) / 7.0
    
    diff_cols_7 = [f'prev_diff_{j}' for j in range(1, 8)]
    df_next['ewm_diff_7d'] = df_next[diff_cols_7].apply(lambda row: pd.Series(row.values).ewm(span=3).mean().iloc[-1] if len(row.values) > 0 else 0, axis=1)
    df_next['setting_change_signal'] = ((df_next['prev_setting_1'] >= 4) & (df_next['prev_diff_1'] < -500)).astype(int)
    df_next['momentum_1v3'] = df_next['prev_diff_1'] - df_next['prev_diff_3']
    df_next['revival_score'] = df_next['cons_neg'] * df_next['store_high_ratio']

    feat_cols = [c for c in FEATURE_COLS if c in df_next.columns]

    # 回帰モデル (XGBoost)
    X_train_reg = df_feat[feat_cols].copy()
    y_train_reg = df_feat['最終差枚'].copy()
    reg_model = XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.05,
                             subsample=0.8, colsample_bytree=0.8,
                             tree_method='hist', device='cuda', random_state=42)
    reg_model.fit(X_train_reg, y_train_reg)
    pred_diffs = reg_model.predict(df_next[feat_cols])

    # 分類モデル
    df_cls = df_feat[df_feat['推定設定'].notna()].copy()
    df_cls['高設定フラグ'] = (df_cls['推定設定'] >= 4).astype(int)
    X_train_cls = df_cls[feat_cols].copy()
    y_train_cls = df_cls['高設定フラグ'].copy()
    pos_sum = y_train_cls.sum()
    spw = (len(y_train_cls) - pos_sum) / pos_sum if pos_sum > 0 else 1
    
    cat_cols_present = [c for c in ['weekday', 'position', 'tail_digit', 'island_id_num'] if c in feat_cols]
    for c in cat_cols_present:
        X_train_cls[c] = X_train_cls[c].astype(int)
        df_next[c] = df_next[c].astype(int)

    X_train_cls = X_train_cls.reset_index(drop=True).replace([np.inf, -np.inf], 0).fillna(0)
    y_train_cls = y_train_cls.reset_index(drop=True)
    df_cls = df_cls.reset_index(drop=True)
    df_next_selected = df_next[feat_cols].replace([np.inf, -np.inf], 0).fillna(0)

    from sklearn.ensemble import ExtraTreesClassifier

    def make_time_folds(frame, n_splits=5):
        dates = np.array(sorted(frame['日付'].unique()))
        folds = []
        for i in range(1, n_splits + 1):
            train_end = int(len(dates) * i / (n_splits + 1))
            valid_end = int(len(dates) * (i + 1) / (n_splits + 1))
            train_dates = dates[:train_end]
            valid_dates = dates[train_end:valid_end]
            train_idx = frame.index[frame['日付'].isin(train_dates)].to_numpy()
            valid_idx = frame.index[frame['日付'].isin(valid_dates)].to_numpy()
            if len(train_idx) == 0 or len(valid_idx) == 0:
                continue
            if y_train_cls.iloc[train_idx].nunique() < 2 or y_train_cls.iloc[valid_idx].nunique() < 2:
                continue
            folds.append((train_idx, valid_idx))
        return folds

    def model_factories():
        return [
            XGBClassifier(
                n_estimators=260, max_depth=3, learning_rate=0.02,
                reg_lambda=20, reg_alpha=2, subsample=0.8, colsample_bytree=0.75,
                gamma=1.5, min_child_weight=15, tree_method='hist',
                random_state=42, scale_pos_weight=spw, eval_metric='logloss'
            ),
            lgb.LGBMClassifier(
                n_estimators=260, max_depth=3, learning_rate=0.02,
                reg_lambda=25, reg_alpha=3, subsample=0.8, colsample_bytree=0.75,
                min_child_samples=100, num_leaves=10, random_state=42, verbose=-1,
                scale_pos_weight=spw
            ),
            ExtraTreesClassifier(
                n_estimators=500, max_depth=9, min_samples_leaf=25,
                max_features=0.7, class_weight='balanced_subsample',
                random_state=42, n_jobs=-1
            )
        ]

    folds = make_time_folds(df_cls)
    oof_by_model = []
    for model_template in model_factories():
        oof = np.full(len(X_train_cls), np.nan)
        for train_idx, val_idx in folds:
            model = model_template.__class__(**model_template.get_params())
            model.fit(X_train_cls.iloc[train_idx], y_train_cls.iloc[train_idx])
            oof[val_idx] = model.predict_proba(X_train_cls.iloc[val_idx])[:, 1]
        oof_by_model.append(oof)

    oof_stack = np.vstack(oof_by_model)
    valid_mask = ~np.isnan(oof_stack).any(axis=0)
    oof_probs = np.mean(oof_stack[:, valid_mask], axis=0)
    y_eval = y_train_cls.iloc[valid_mask].reset_index(drop=True)
    df_eval = df_cls.iloc[valid_mask].reset_index(drop=True)

    final_preds = []
    for model in model_factories():
        model.fit(X_train_cls, y_train_cls)
        final_preds.append(model.predict_proba(df_next_selected)[:, 1])
    pred_probs = np.mean(final_preds, axis=0)

    # 評価用閾値: FPを抑えつつ見逃しを減らすため、上位25.5%を候補化する。
    best_threshold = np.percentile(oof_probs, 100 * (1 - TARGET_POSITIVE_RATE))
    pred_high = (oof_probs >= best_threshold).astype(int)
    
    best_hit_rate = precision_score(y_eval, pred_high, zero_division=0)
    best_recall = recall_score(y_eval, pred_high, zero_division=0)
    best_f1 = f1_score(y_eval, pred_high, zero_division=0)
    selected_diffs = df_eval['最終差枚'][pred_high == 1]
    best_avg_diff = selected_diffs.mean() if len(selected_diffs) > 0 else 0

    predictions = []
    for i, num in enumerate(machines):
        feat_clean = {k: (v.item() if hasattr(v, 'item') else v) for k, v in next_X[i].items()}
        # 派生特徴量も追加
        feat_clean['neg_after_pos'] = int((feat_clean.get('prev_high_setting_1', 0) == 1) and (feat_clean.get('prev_diff_1', 0) < 0))
        feat_clean['cumul_7d_diff'] = float(sum(feat_clean.get(f'prev_diff_{j}', 0) for j in range(1, 8)))
        feat_clean['island_trend'] = float((feat_clean.get('island_avg_prev_1', 0) + feat_clean.get('island_avg_prev_2', 0) + feat_clean.get('island_avg_prev_3', 0)) / 3)
        
        # 新しく追加した空間的特徴量も追加（UI表示用）
        for sp_col in ['adj_left_diff_1', 'adj_right_diff_1', 'adj_avg_diff_1', 'island_high_ratio_3d']:
            if sp_col in df_next.columns:
                feat_clean[sp_col] = float(df_next[sp_col].iloc[i])
                
        predictions.append({
            'machine': str(num).zfill(4),
            'expected_diff': float(pred_diffs[i]),
            'prob_high_setting': float(pred_probs[i]),
            'features': feat_clean
        })
        
    predictions.sort(key=lambda x: x['prob_high_setting'], reverse=True)
    return {
        'target_date': next_date.strftime('%Y-%m-%d'),
        'is_event': is_event == 1,
        'hit_rate': float(best_hit_rate),
        'recall': float(best_recall),
        'f1': float(best_f1),
        'threshold': float(best_threshold),
        'positive_rate': float(np.mean(pred_high)),
        'avg_diff': float(best_avg_diff),
        'predictions': predictions[:30]
    }

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
        
    print("=========================================")
    print(f"分析が完了しました！")
    print(f"結果を {OUTPUT_PATH} に出力しました。")
    print("=========================================")
