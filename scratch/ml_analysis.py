# -*- coding: utf-8 -*-
"""
ハナハナ 高設定条件分析スクリプト (GPU/XGBoost, 過去7日間+長期時間減衰特徴量対応)
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
import os
import sys

# ============================================================
# 設定
# ============================================================
DB_PATH = "slot_data.db"
LAYOUT_PATH = "docs/ogiya/layout.json"
OUTPUT_PATH = "docs/ogiya/analysis_results.json"
TARGET_POSITIVE_RATE = 0.255

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
    'neg_low_and_high_diff_prev_1': '前日低設定かつ差枚大(誤爆)',
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
    'adj_avg_diff_1': '両隣平均前日差枚',
    'facing_avg_diff_1': '向かい台平均前日差枚'
}
for k, v in base_feats.items():
    FEATURE_COLS.append(k)
    FEATURE_NAMES_JP[k] = v

# イベント日翌日系フラグ
FEATURE_COLS.append('is_next_day_after_event')
FEATURE_NAMES_JP['is_next_day_after_event'] = 'イベント日翌日'
FEATURE_COLS.append('event_next_high_neg_1')
FEATURE_NAMES_JP['event_next_high_neg_1'] = 'イベント翌日・前日高設定不発'

# 過去7日間特徴量
for i in range(1, 8):
    FEATURE_COLS.append(f'prev_diff_{i}')
    FEATURE_NAMES_JP[f'prev_diff_{i}'] = f'{i}日前差枚'
    FEATURE_COLS.append(f'prev_games_{i}')
    FEATURE_NAMES_JP[f'prev_games_{i}'] = f'{i}日前ゲーム数'
    FEATURE_COLS.append(f'island_avg_prev_{i}')
    FEATURE_NAMES_JP[f'island_avg_prev_{i}'] = f'{i}日前の島平均差枚'

# 長期時間減衰集計特徴量 (1ヶ月=30日, 2ヶ月=60日, 3ヶ月=90日)
# 各ウィンドウで差枚・ゲーム数・勝率の指数減衰加重平均を計算
for _w, _label in [(30, '1ヶ月'), (60, '2ヶ月'), (90, '3ヶ月')]:
    FEATURE_COLS.append(f'ewm_diff_{_w}d')
    FEATURE_NAMES_JP[f'ewm_diff_{_w}d'] = f'時間減衰平均差枚({_label})'
    FEATURE_COLS.append(f'ewm_games_{_w}d')
    FEATURE_NAMES_JP[f'ewm_games_{_w}d'] = f'時間減衰平均G数({_label})'
    FEATURE_COLS.append(f'ewm_win_rate_{_w}d')
    FEATURE_NAMES_JP[f'ewm_win_rate_{_w}d'] = f'時間減衰勝率({_label})'
    FEATURE_COLS.append(f'cumul_{_w}d_diff')
    FEATURE_NAMES_JP[f'cumul_{_w}d_diff'] = f'累積差枚({_label})'

# 台番号・島別 長期時間減衰特徴量
for _w, _label in [(30, '1ヶ月'), (60, '2ヶ月'), (90, '3ヶ月')]:
    FEATURE_COLS.append(f'machine_ewm_diff_{_w}d')
    FEATURE_NAMES_JP[f'machine_ewm_diff_{_w}d'] = f'台別時間減衰差枚({_label})'
    FEATURE_COLS.append(f'island_ewm_diff_{_w}d')
    FEATURE_NAMES_JP[f'island_ewm_diff_{_w}d'] = f'島別時間減衰差枚({_label})'

# 月間累計差枚
FEATURE_COLS.append('machine_month_cumul_diff')
FEATURE_NAMES_JP['machine_month_cumul_diff'] = '台月間累計差枚'
FEATURE_COLS.append('store_month_cumul_diff')
FEATURE_NAMES_JP['store_month_cumul_diff'] = '店全体月間累計差枚'

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

    # イベント日翌日フラグ: 前日がイベント日(3/5/8の付く日)かどうか
    df_sorted_dates = df.sort_values('日付')
    date_is_event = df_sorted_dates.drop_duplicates('日付').set_index('日付')['is_event_day'].to_dict()
    all_dates_sorted = sorted(date_is_event.keys())
    date_idx_map = {d: i for i, d in enumerate(all_dates_sorted)}
    def _is_next_day_after_event(row_date):
        idx = date_idx_map.get(row_date, 0)
        if idx == 0:
            return 0
        prev_d = all_dates_sorted[idx - 1]
        return int(date_is_event.get(prev_d, 0))
    df['is_next_day_after_event'] = df['日付'].apply(_is_next_day_after_event)

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

    # 店全体の月間累計差枚 (その日の前日まで、月初にリセット) ─ 事前計算
    _store_daily_sum = df.groupby('日付')['最終差枚'].sum().sort_index().reset_index()
    _store_daily_sum.columns = ['日付', '_store_sum']
    _store_daily_sum['_ym'] = _store_daily_sum['日付'].dt.to_period('M')
    _store_daily_sum['store_month_cumul_diff'] = (
        _store_daily_sum.groupby('_ym')['_store_sum']
        .transform(lambda s: s.shift(1).cumsum().fillna(0))
    )
    store_month_cumul_dict = _store_daily_sum.set_index('日付')['store_month_cumul_diff'].to_dict()

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
        # 月内累計差枚の追跡用
        _machine_month = None
        _machine_month_cumul = 0.0
        
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
                # island_avg は MAX_LAG まで保存（island_ewm_diff 計算に使用）
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

            # 月内累計差枚 (前日まで)
            if _machine_month != date.month:
                _machine_month = date.month
                _machine_month_cumul = 0.0
            hist_feats[key]['machine_month_cumul_diff'] = _machine_month_cumul
            _machine_month_cumul += diffs[i]  # 今日分は翌日以降のために加算
            
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
                    
                # 同一列（向かい合う台）の前日差枚
                col_idx = layout_lookup.get(num, {}).get('col', -1)
                if col_idx >= 0 and past_date_1:
                    facing_diffs = []
                    for mn, info in layout_lookup.items():
                        if info.get('col') == col_idx and mn != num:
                            mn_int = int(mn)
                            fd = daily_machine_stats[past_date_1].get(mn_int, {}).get('diff')
                            if fd is not None:
                                facing_diffs.append(fd)
                    hist_feats[key]['facing_avg_diff_1'] = np.mean(facing_diffs) if facing_diffs else 0
                else:
                    hist_feats[key]['facing_avg_diff_1'] = 0
            else:
                for col in ['adj_left_diff_1', 'adj_right_diff_1', 'adj_avg_diff_1', 'adj_left_win_rate_3d', 'adj_right_win_rate_3d', 'island_high_ratio_3d', 'facing_avg_diff_1']:
                    hist_feats[key][col] = 0

    # 特徴量をDFにマージ
    spatial_cols = ['adj_left_diff_1', 'adj_right_diff_1', 'adj_avg_diff_1', 'adj_left_win_rate_3d', 'adj_right_win_rate_3d', 'island_high_ratio_3d', 'facing_avg_diff_1']
    store_cols = ['store_high_ratio', 'store_high_prev_3d', 'store_avg_prev_1d', 'store_avg_prev_3d', 'store_win_prev_1d', 'store_win_prev_3d']
    machine_roll_cols = ['machine_high_rate_prev_14d', 'machine_avg_diff_prev_14d']
    for col in ['cons_neg', 'cons_pos', 'prev_setting_1', 'prev_high_setting_1', 'same_wd_avg_diff', 'same_wd_win_rate'] + store_cols + machine_roll_cols + spatial_cols:
        df[col] = df.apply(lambda r: hist_feats[(r['台番号_pad'], r['日付'])].get(col, 0), axis=1)

    df = df.copy()
    for j in range(1, MAX_LAG + 1):
        df[f'prev_diff_{j}'] = df.apply(lambda r: hist_feats[(r['台番号_pad'], r['日付'])].get(f'prev_diff_{j}', 0), axis=1)
        df[f'prev_games_{j}'] = df.apply(lambda r: hist_feats[(r['台番号_pad'], r['日付'])].get(f'prev_games_{j}', 0), axis=1)
        # island_avg は全 j (1..MAX_LAG) を展開する（island_ewm_diff 計算用）
        df[f'island_avg_prev_{j}'] = df.apply(lambda r: hist_feats[(r['台番号_pad'], r['日付'])].get(f'island_avg_prev_{j}', 0), axis=1)

    # 月間累計差枚（台・店舗）をDFに反映
    df['machine_month_cumul_diff'] = df.apply(
        lambda r: hist_feats[(r['台番号_pad'], r['日付'])].get('machine_month_cumul_diff', 0), axis=1
    )
    df['store_month_cumul_diff'] = df['日付'].map(store_month_cumul_dict).fillna(0)

    # 派生特徴量
    df['neg_after_pos'] = ((df['prev_high_setting_1'] == 1) & (df['prev_diff_1'] < 0)).astype(int)
    df['neg_low_and_high_diff_prev_1'] = ((df['prev_high_setting_1'] == 0) & (df['prev_diff_1'] > 1000)).astype(int)
    df['event_next_high_neg_1'] = ((df['is_next_day_after_event'] == 1) & (df['prev_high_setting_1'] == 1) & (df['prev_diff_1'] < 0)).astype(int)
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

    # ========== 長期時間減衰集計特徴量 ==========
    # 指数減衰ウェイト: w_j = exp(-decay_rate * j), 古いほど小さいウェイト
    DECAY_RATE = 0.05  # 1日あたりの減衰率 (調整可能)
    for _window in (30, 60, 90):
        # ウェイト配列 (j=1が最新, j=_windowが最古)
        _weights = np.array([np.exp(-DECAY_RATE * j) for j in range(1, _window + 1)])
        _w_sum = _weights.sum()
        # 差枚の時間減衰加重平均
        _diff_arr = np.column_stack([
            df[f'prev_diff_{j}'].values if j <= MAX_LAG else np.zeros(len(df))
            for j in range(1, _window + 1)
        ])  # shape: (n_samples, _window)
        df[f'ewm_diff_{_window}d'] = (_diff_arr * _weights).sum(axis=1) / _w_sum
        # ゲーム数の時間減衰加重平均
        _games_arr = np.column_stack([
            df[f'prev_games_{j}'].values if j <= MAX_LAG else np.zeros(len(df))
            for j in range(1, _window + 1)
        ])
        df[f'ewm_games_{_window}d'] = (_games_arr * _weights).sum(axis=1) / _w_sum
        # 勝率の時間減衰加重平均
        _win_arr = np.column_stack([
            (df[f'prev_diff_{j}'].values > 0).astype(float) if j <= MAX_LAG else np.zeros(len(df))
            for j in range(1, _window + 1)
        ])
        df[f'ewm_win_rate_{_window}d'] = (_win_arr * _weights).sum(axis=1) / _w_sum
        # 累積差枚 (減衰なし、単純合計)
        _cumul = sum(
            df[f'prev_diff_{j}'] if j <= MAX_LAG else 0
            for j in range(1, _window + 1)
        )
        df[f'cumul_{_window}d_diff'] = _cumul

    # ========== 台番号・島別 長期時間減衰特徴量 ==========
    DECAY_RATE = 0.05
    for _window in (30, 60, 90):
        _weights = np.array([np.exp(-DECAY_RATE * j) for j in range(1, _window + 1)])
        _w_sum = _weights.sum()
        # 台別: prev_diff_j を使用 (j > MAX_LAG は 0 補完)
        _m_arr = np.column_stack([
            df[f'prev_diff_{j}'].values if j <= MAX_LAG else np.zeros(len(df))
            for j in range(1, _window + 1)
        ])
        df[f'machine_ewm_diff_{_window}d'] = (_m_arr * _weights).sum(axis=1) / _w_sum
        # 島別: island_avg_prev_j を使用 (j > MAX_LAG は 0 補完)
        _i_arr = np.column_stack([
            df[f'island_avg_prev_{j}'].values if j <= MAX_LAG else np.zeros(len(df))
            for j in range(1, _window + 1)
        ])
        df[f'island_ewm_diff_{_window}d'] = (_i_arr * _weights).sum(axis=1) / _w_sum

    base_cols = [c for c in FEATURE_COLS if c in df.columns]
    df = df.dropna(subset=base_cols)
    # Downstream TimeSeriesSplit calls assume rows are chronological.
    df = df.sort_values([df.columns[0], 'machine_num']).reset_index(drop=True)
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

    # 時系列分割に統一（StratifiedKFoldの未来リークを防止）
    n_splits = min(5, len(X) // 20)
    if n_splits < 2: n_splits = 2
    tscv_cls = TimeSeriesSplit(n_splits=n_splits)
    
    if task == 'regression':
        cv_res = cross_validate(model, X, y, cv=tscv_cls, scoring=['r2'])
        model.fit(X, y)
        importances = model.feature_importances_
        fi = [{'feature': col, 'feature_jp': FEATURE_NAMES_JP[col], 'importance': float(v)} for col, v in sorted(zip(X.columns, importances), key=lambda x: -x[1])]
        result = {'feature_importances': fi, 'n_samples': len(X)}
        result['cv_r2'] = float(np.mean(cv_res['test_r2']))
    else:
        # 手動OOFでTimeSeriesSplit対応（cross_val_predictはパーティション制約で使用不可）
        oof_prob = np.full(len(X), np.nan)
        for train_idx, val_idx in tscv_cls.split(X):
            m_clone = model.__class__(**model.get_params())
            m_clone.fit(X.iloc[train_idx], y.iloc[train_idx])
            oof_prob[val_idx] = m_clone.predict_proba(X.iloc[val_idx])[:, 1]
        
        # validationに含まれた部分のみ評価
        valid_mask = ~np.isnan(oof_prob)
        oof_valid = oof_prob[valid_mask]
        y_valid = y.values[valid_mask]
        
        # 収支ベース閾値最適化
        best_th = np.percentile(oof_valid, 100 * (1 - TARGET_POSITIVE_RATE))
        y_pred_valid = (oof_valid >= best_th).astype(int)
        
        model.fit(X, y)
        importances = model.feature_importances_
        fi = [{'feature': col, 'feature_jp': FEATURE_NAMES_JP[col], 'importance': float(v)} for col, v in sorted(zip(X.columns, importances), key=lambda x: -x[1])]
        
        result = {'feature_importances': fi, 'n_samples': len(X)}
        result['cv_accuracy'] = float(np.mean(y_pred_valid == y_valid))
        result['cv_precision'] = float(precision_score(y_valid, y_pred_valid, zero_division=0))
        result['cv_recall'] = float(recall_score(y_valid, y_pred_valid, zero_division=0))
        result['cv_f1'] = float(f1_score(y_valid, y_pred_valid, zero_division=0))
        result['threshold'] = float(best_th)
        result['positive_rate'] = float(np.mean(y_pred_valid))
        
        cm = confusion_matrix(y_valid, y_pred_valid)
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

def predict_next_day(df_feat, selected_feats=None, layout_lookup=None, use_weights=False, use_lr_plus=False):
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
                    
        # island_avg_prev を MAX_LAG まで取得（最初7日分は FEATURE_COLS 用、全体は ewm 計算用）
        _MAX_LAG_PRED = 21
        for j in range(1, _MAX_LAG_PRED + 1):
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
            
            # 向かい台の前日差枚
            num_pad = str(num).zfill(4)
            col_idx = layout_lookup.get(num_pad, {}).get('col', -1) if layout_lookup else -1
            if col_idx >= 0:
                facing_diffs = []
                for mn, info in layout_lookup.items():
                    if info.get('col') == col_idx and mn != num_pad:
                        mn_int = int(mn)
                        fd_row = df_feat[(df_feat['日付'] == last_date) & (df_feat['台番号'].astype(int) == mn_int)]
                        if not fd_row.empty:
                            facing_diffs.append(fd_row['最終差枚'].values[0])
                feat['facing_avg_diff_1'] = np.mean(facing_diffs) if facing_diffs else 0
            else:
                feat['facing_avg_diff_1'] = 0
            
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
            feat['facing_avg_diff_1'] = 0

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
    df_next['neg_low_and_high_diff_prev_1'] = ((df_next['prev_high_setting_1'] == 0) & (df_next['prev_diff_1'] > 1000)).astype(int)

    # イベント日翌日フラグ (予測日に対して)
    max_date_dom = max_date.day
    prev_is_event = 1 if str(max_date_dom)[-1] in ['3', '5', '8'] else 0
    df_next['is_next_day_after_event'] = prev_is_event

    df_next['event_next_high_neg_1'] = ((df_next['is_next_day_after_event'] == 1) & (df_next['prev_high_setting_1'] == 1) & (df_next['prev_diff_1'] < 0)).astype(int)
    df_next['momentum_1v3'] = df_next['prev_diff_1'] - df_next['prev_diff_3']
    df_next['revival_score'] = df_next['cons_neg'] * df_next['store_high_ratio']

    # 長期時間減衰集計特徴量 (予測データ用)
    _MAX_LAG = 21  # build_features と同じMAX_LAG
    _DECAY_RATE = 0.05
    for _window in (30, 60, 90):
        _weights = np.array([np.exp(-_DECAY_RATE * j) for j in range(1, _window + 1)])
        _w_sum = _weights.sum()
        _diff_arr = np.column_stack([
            df_next[f'prev_diff_{j}'].values if j <= _MAX_LAG else np.zeros(len(df_next))
            for j in range(1, _window + 1)
        ])
        df_next[f'ewm_diff_{_window}d'] = (_diff_arr * _weights).sum(axis=1) / _w_sum
        _games_arr = np.column_stack([
            df_next[f'prev_games_{j}'].values if j <= _MAX_LAG else np.zeros(len(df_next))
            for j in range(1, _window + 1)
        ])
        df_next[f'ewm_games_{_window}d'] = (_games_arr * _weights).sum(axis=1) / _w_sum
        _win_arr = np.column_stack([
            (df_next[f'prev_diff_{j}'].values > 0).astype(float) if j <= _MAX_LAG else np.zeros(len(df_next))
            for j in range(1, _window + 1)
        ])
        df_next[f'ewm_win_rate_{_window}d'] = (_win_arr * _weights).sum(axis=1) / _w_sum
        _cumul = sum(
            df_next[f'prev_diff_{j}'] if j <= _MAX_LAG else 0
            for j in range(1, _window + 1)
        )
        df_next[f'cumul_{_window}d_diff'] = _cumul

    # 台別・島別 長期時間減衰特徴量 (予測データ用)
    _DECAY_RATE2 = 0.05
    for _window in (30, 60, 90):
        _wts = np.array([np.exp(-_DECAY_RATE2 * j) for j in range(1, _window + 1)])
        _ws = _wts.sum()
        # 台別: prev_diff_j を使用
        _m2 = np.column_stack([
            df_next[f'prev_diff_{j}'].values if j <= _MAX_LAG else np.zeros(len(df_next))
            for j in range(1, _window + 1)
        ])
        df_next[f'machine_ewm_diff_{_window}d'] = (_m2 * _wts).sum(axis=1) / _ws
        # 島別: island_avg_prev_j を使用
        _i2 = np.column_stack([
            df_next[f'island_avg_prev_{j}'].values if j <= _MAX_LAG else np.zeros(len(df_next))
            for j in range(1, _window + 1)
        ])
        df_next[f'island_ewm_diff_{_window}d'] = (_i2 * _wts).sum(axis=1) / _ws

    # 月間累計差枚 (予測日 next_date に対して)
    # 機械別: max_date までの当月内差枚を合計
    next_ym = next_date.to_period('M')
    for i_m, num_m in enumerate(machines):
        m_hist_m = df_feat[df_feat['台番号'] == num_m].sort_values('日付')
        m_this_month = m_hist_m[m_hist_m['日付'].dt.to_period('M') == next_ym]
        df_next.loc[df_next.index[i_m], 'machine_month_cumul_diff'] = float(
            m_this_month['最終差枚'].sum()) if not m_this_month.empty else 0.0
    # 店全体: next_ym の当月内差枚合計 (max_date まで)
    store_this_month = df_feat[df_feat['日付'].dt.to_period('M') == next_ym]
    df_next['store_month_cumul_diff'] = float(
        store_this_month['最終差枚'].sum()) if not store_this_month.empty else 0.0
    feat_cols = [c for c in FEATURE_COLS if c in df_next.columns]

    # 回帰モデル (XGBoost) — 正則化を強化して過学習・過大評価を抑制
    X_train_reg = df_feat[feat_cols].copy()
    y_train_reg = df_feat['最終差枚'].copy()
    reg_model = XGBRegressor(n_estimators=200, max_depth=3, learning_rate=0.03,
                             reg_lambda=15, reg_alpha=5,
                             subsample=0.7, colsample_bytree=0.6,
                             min_child_weight=20,
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
        """日付ベースのtime-series fold生成（位置インデックスを返す）"""
        dates = np.array(sorted(frame['日付'].unique()))
        folds = []
        for i in range(1, n_splits + 1):
            train_end = int(len(dates) * i / (n_splits + 1))
            valid_end = int(len(dates) * (i + 1) / (n_splits + 1))
            train_dates = set(dates[:train_end])
            valid_dates = set(dates[train_end:valid_end])
            train_pos = np.where(frame['日付'].isin(train_dates))[0]
            valid_pos = np.where(frame['日付'].isin(valid_dates))[0]
            if len(train_pos) == 0 or len(valid_pos) == 0:
                continue
            if y_train_cls.iloc[train_pos].nunique() < 2 or y_train_cls.iloc[valid_pos].nunique() < 2:
                continue
            folds.append((train_pos, valid_pos))
        return folds

    def model_factories():
        from catboost import CatBoostClassifier as _CBC
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
            ),
            # CatBoost: 対称木・順序統計量処理で他と異なる帰納バイアスを持つ
            _CBC(
                iterations=250, depth=4, learning_rate=0.03,
                l2_leaf_reg=15, bootstrap_type='Bernoulli', subsample=0.8,
                auto_class_weights='Balanced',
                random_seed=42, verbose=0, task_type='GPU'
            ),
        ]

    folds = make_time_folds(df_cls)
    oof_by_model = []
    for model_template in model_factories():
        oof = np.full(len(X_train_cls), np.nan)
        for train_pos, val_pos in folds:
            model = model_template.__class__(**model_template.get_params())
            model.fit(X_train_cls.iloc[train_pos], y_train_cls.iloc[train_pos])
            oof[val_pos] = model.predict_proba(X_train_cls.iloc[val_pos])[:, 1]
        oof_by_model.append(oof)

    # LightGBM LambdaRank OOF (LTR: Learning to Rank)
    # 1日ごとのグループ内で高設定台を上位にランキングし、分類確率を補完する
    print("  [LTR] LightGBM LambdaRank OOF 計算中...")
    oof_ltr = np.full(len(X_train_cls), np.nan)
    use_ltr = False
    try:
        ltr_params = dict(
            objective="lambdarank", n_estimators=200, max_depth=4,
            learning_rate=0.03, reg_lambda=10, reg_alpha=2,
            subsample=0.8, colsample_bytree=0.75,
            min_child_samples=30, num_leaves=15,
            random_state=42, verbose=-1
        )
        for train_pos, val_pos in folds:
            tr_df_ltr = df_cls.iloc[train_pos]
            va_df_ltr = df_cls.iloc[val_pos]
            tr_groups = tr_df_ltr.groupby("日付", sort=True)["日付"].count().values
            tr_order = np.argsort(tr_df_ltr["日付"].values, kind="stable")
            va_order = np.argsort(va_df_ltr["日付"].values, kind="stable")
            ltr_m = lgb.LGBMRanker(**ltr_params)
            ltr_m.fit(X_train_cls.iloc[train_pos].iloc[tr_order],
                      y_train_cls.iloc[train_pos].values[tr_order],
                      group=tr_groups)
            ltr_scores = ltr_m.predict(X_train_cls.iloc[val_pos].iloc[va_order])
            inv_va_order = np.argsort(va_order, kind="stable")
            oof_ltr[val_pos] = ltr_scores[inv_va_order]
        ltr_valid = ~np.isnan(oof_ltr)
        ltr_vals = oof_ltr[ltr_valid]
        ltr_min, ltr_max = ltr_vals.min(), ltr_vals.max()
        if ltr_max > ltr_min:
            oof_ltr[ltr_valid] = (ltr_vals - ltr_min) / (ltr_max - ltr_min)
        oof_by_model.append(oof_ltr)
        use_ltr = True
        print("  [LTR] LambdaRank OOF 完了")
    except Exception as _e_ltr:
        print(f"  [LTR] スキップ: {_e_ltr}")

    # ===== アンサンブル 重み付け (OOF性能ベース) =====
    # 各モデルのOOFスコアをスタックして有効サンプルのマスクを作成
    oof_stack = np.vstack(oof_by_model)
    valid_mask = ~np.isnan(oof_stack).any(axis=0)
    y_eval = y_train_cls.iloc[valid_mask].reset_index(drop=True)
    df_eval = df_cls.iloc[valid_mask].reset_index(drop=True)
    eval_diffs_for_w = df_eval['最終差枚'].values

    # 各モデルのOOF性能を計算して重みを決定
    # 評価指標: 予測上位 TARGET_POSITIVE_RATE の台の平均差枚
    model_scores = []
    model_names = ['XGBoost', 'LightGBM', 'ExtraTrees', 'CatBoost']
    if use_ltr:
        model_names.append('LambdaRank')

    print("\n  [\u30a2\u30f3\u30b5\u30f3\u30d6\u30eb] \u5404\u30e2\u30c7\u30eb OOF \u6027\u80fd:")
    for m_i, (mname, m_oof) in enumerate(zip(model_names, oof_by_model)):
        m_oof_valid = m_oof[valid_mask]
        # min-max正規化して閾値を統一
        v_min, v_max = np.nanmin(m_oof_valid), np.nanmax(m_oof_valid)
        if v_max > v_min:
            m_oof_norm = (m_oof_valid - v_min) / (v_max - v_min)
        else:
            m_oof_norm = m_oof_valid
        th_top = np.percentile(m_oof_norm, 100 * (1 - TARGET_POSITIVE_RATE))
        sel = m_oof_norm >= th_top
        avg_d = float(eval_diffs_for_w[sel].mean()) if sel.sum() > 0 else 0.0
        prec_m = float(y_eval.values[sel].mean()) if sel.sum() > 0 else 0.0
        # スコア = 平均差枚（精度を考慮した莰善度）
        score_m = avg_d if avg_d > 0 else 0.0
        model_scores.append(score_m)
        print(f"    {mname}: avg_diff={avg_d:+.0f}枚  precision={prec_m:.3f}  weight_raw={score_m:.1f}")

    # 重み = スコア比例（ネガティブスコアのモデルは重み0）
    weights = np.array([max(0.0, s) for s in model_scores], dtype=float)
    weight_sum = weights.sum()
    if weight_sum <= 0:
        # 全モデルがネガなら等重みにフォールバック
        weights = np.ones(len(oof_by_model), dtype=float) / len(oof_by_model)
        weight_sum = 1.0
    else:
        weights /= weight_sum

    print(f"  [アンサンブル] 最終重み: " + ", ".join(f"{n}={w:.3f}" for n, w in zip(model_names, weights)))

    # 有効サンプル内で重み付きOOFスコアを計算
    oof_probs = np.average(oof_stack[:, valid_mask], axis=0, weights=weights)

    # ===== 全データで最終モデルをfit =====
    final_preds = []
    for model in model_factories():
        model.fit(X_train_cls, y_train_cls)
        final_preds.append(model.predict_proba(df_next_selected)[:, 1])

    # LTRも最終予測に追加
    if use_ltr:
        try:
            tr_groups_all = df_cls.groupby("日付", sort=True)["日付"].count().values
            tr_order_all = np.argsort(df_cls["日付"].values, kind="stable")
            ltr_final = lgb.LGBMRanker(**ltr_params)
            ltr_final.fit(X_train_cls.iloc[tr_order_all],
                          y_train_cls.values[tr_order_all],
                          group=tr_groups_all)
            ltr_pred_raw = ltr_final.predict(df_next_selected)
            if ltr_pred_raw.max() > ltr_pred_raw.min():
                ltr_pred = (ltr_pred_raw - ltr_pred_raw.min()) / (ltr_pred_raw.max() - ltr_pred_raw.min())
            else:
                ltr_pred = ltr_pred_raw
            final_preds.append(ltr_pred)
        except Exception as _e_ltr2:
            print(f"  [LTR] 最終予測スキップ: {_e_ltr2}")

    # 最終予測もOOF連動重みで加算
    if len(final_preds) == len(weights):
        pred_probs = np.average(np.vstack(final_preds), axis=0, weights=weights)
    else:
        # モデル数がイレギュラーなら等重みフォールバック
        pred_probs = np.mean(final_preds, axis=0)

    # 収支ベース閾値最適化: OOFデータ上で閾値を探索（リークなし）
    eval_diffs = df_eval['最終差枚'].values
    best_threshold = 0.3
    best_th_score = -np.inf
    n_eval_total = len(oof_probs)
    for th_candidate in np.arange(0.15, 0.75, 0.005):
        sel_mask = oof_probs >= th_candidate
        n_sel = int(sel_mask.sum())
        if n_sel < 3 or (n_sel / n_eval_total) < 0.10:
            continue
        avg_d = float(eval_diffs[sel_mask].mean())
        
        tp = ((y_eval.values == 1) & (sel_mask)).sum()
        fp = ((y_eval.values == 0) & (sel_mask)).sum()
        tn = ((y_eval.values == 0) & (~sel_mask)).sum()
        fn = ((y_eval.values == 1) & (~sel_mask)).sum()
        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        lr_plus = tpr / fpr if fpr > 0 else (tpr / 0.0001)
        prec = float(y_eval.values[sel_mask].mean()) if n_sel > 0 else 0
        
        if use_lr_plus:
            score = avg_d * (1.0 if lr_plus >= 1.5 else 0.5)
        else:
            score = avg_d * (1.0 if prec >= 0.20 else 0.5)
        if score > best_th_score:
            best_th_score = score
            best_threshold = float(th_candidate)

    pred_high = (oof_probs >= best_threshold).astype(int)
    best_hit_rate = precision_score(y_eval, pred_high, zero_division=0)
    best_recall = recall_score(y_eval, pred_high, zero_division=0)
    best_f1 = f1_score(y_eval, pred_high, zero_division=0)
    selected_diffs = df_eval['最終差枚'][pred_high == 1]
    best_avg_diff = float(selected_diffs.mean()) if len(selected_diffs) > 0 else 0

    # 設定別の指標を計算 (要求4)
    setting_metrics = {}
    eval_settings = df_eval['推定設定'].values
    n_pred_positive = pred_high.sum()
    k = 20
    top_k_idx = np.argsort(oof_probs)[-k:]
    # 推定設定のうち、高設定（4以上）で実際に存在する値のみ動的に抽出
    unique_high_settings = sorted([int(s) for s in np.unique(eval_settings) if not pd.isna(s) and s >= 4], reverse=True)
    for s in unique_high_settings:
        n_actual = (eval_settings == s).sum()
        n_correct = ((pred_high == 1) & (eval_settings == s)).sum()
        ppv = float(n_correct / n_pred_positive) if n_pred_positive > 0 else 0.0
        n_correct_k = (eval_settings[top_k_idx] == s).sum()
        prec_k = float(n_correct_k / k)
        rec_k = float(n_correct_k / n_actual) if n_actual > 0 else 0.0
        setting_metrics[f'setting_{s}'] = {
            'ppv': ppv,
            'precision_at_k': prec_k,
            'recall_at_k': rec_k,
            'k': k
        }

    predictions = []
    for i, num in enumerate(machines):
        feat_clean = {k: (v.item() if hasattr(v, 'item') else v) for k, v in next_X[i].items()}
        # 派生特徴量も追加
        feat_clean['neg_after_pos'] = int((feat_clean.get('prev_high_setting_1', 0) == 1) and (feat_clean.get('prev_diff_1', 0) < 0))
        feat_clean['neg_low_and_high_diff_prev_1'] = int((feat_clean.get('prev_high_setting_1', 0) == 0) and (feat_clean.get('prev_diff_1', 0) > 1000))
        feat_clean['event_next_high_neg_1'] = int((feat_clean.get('is_next_day_after_event', 0) == 1) and (feat_clean.get('prev_high_setting_1', 0) == 1) and (feat_clean.get('prev_diff_1', 0) < 0))
        feat_clean['cumul_7d_diff'] = float(sum(feat_clean.get(f'prev_diff_{j}', 0) for j in range(1, 8)))
        feat_clean['island_trend'] = float((feat_clean.get('island_avg_prev_1', 0) + feat_clean.get('island_avg_prev_2', 0) + feat_clean.get('island_avg_prev_3', 0)) / 3)
        
        # 新しく追加した空間的特徴量も追加（UI表示用）
        for sp_col in ['adj_left_diff_1', 'adj_right_diff_1', 'adj_avg_diff_1', 'island_high_ratio_3d']:
            if sp_col in df_next.columns:
                feat_clean[sp_col] = float(df_next[sp_col].iloc[i])
                
        # 期待差枚: 回帰予測を分類確率で割り引き（過大評価抑制）
        # 分類確率が高い→回帰予測を信頼、低い→全台平均に近づける
        raw_diff = float(pred_diffs[i])
        prob = float(pred_probs[i])
        overall_avg = float(y_train_reg.mean())
        adjusted_diff = prob * raw_diff + (1 - prob) * overall_avg
                
        predictions.append({
            'machine': str(num).zfill(4),
            'expected_diff': adjusted_diff,
            'expected_diff_raw': raw_diff,
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
        'setting_metrics': setting_metrics,
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
    import sys as _sys
    from ml_improvements import (select_features_by_permutation,
                                  optimize_threshold_by_profit,
                                  run_backtest, plot_backtest)

    df = load_data()
    layout = load_layout()
    lookup = build_layout_lookup(layout)
    df_feat = build_features(df, lookup)
    
    print("=== 特徴量選択 (Permutation Importance) ===")
    # 分類タスクの特徴量選択
    df_cls_sel = df_feat[df_feat['推定設定'].notna()].copy()
    df_cls_sel['高設定フラグ'] = (df_cls_sel['推定設定'] >= 4).astype(int)
    X_sel = df_cls_sel[FEATURE_COLS].replace([np.inf, -np.inf], 0).fillna(0)
    y_sel = df_cls_sel['高設定フラグ']
    
    from sklearn.ensemble import ExtraTreesClassifier
    selector_model = ExtraTreesClassifier(
        n_estimators=300, max_depth=7, min_samples_leaf=25,
        max_features=0.7, class_weight='balanced_subsample',
        random_state=42, n_jobs=-1
    )
    selected_features = select_features_by_permutation(X_sel, y_sel, selector_model)
    print(f"  選択された特徴量数: {len(selected_features)} / {len(FEATURE_COLS)}")
    print(f"  除外された特徴量: {[c for c in FEATURE_COLS if c not in selected_features]}")
    
    results = run_all_analysis(df_feat)
    # predict_next_day is called later
    results['feature_names_jp'] = FEATURE_NAMES_JP
    results['selected_features'] = selected_features
    results['n_features_original'] = len(FEATURE_COLS)
    results['n_features_selected'] = len(selected_features)
    
    # === バックテスト (新特徴量 vs 旧特徴量 の成績比較) ===
    print("\n=== バックテスト (Walk-forward) ===")
    pos_sum = y_sel.sum()
    spw = (len(y_sel) - pos_sum) / pos_sum if pos_sum > 0 else 1

    # ── 特徴量グループ定義 ──
    # GROUP_0: 前回追加分 (イベント翌日 + 全体ewm/cumul)
    GROUP_0 = (
        ['is_next_day_after_event'] +
        [f'ewm_diff_{w}d' for w in (30, 60, 90)] +
        [f'ewm_games_{w}d' for w in (30, 60, 90)] +
        [f'ewm_win_rate_{w}d' for w in (30, 60, 90)] +
        [f'cumul_{w}d_diff' for w in (30, 60, 90)]
    )
    # GROUP_A: 台番号別長期時間減衰差枚
    GROUP_A = [f'machine_ewm_diff_{w}d' for w in (30, 60, 90)]
    # GROUP_B: 島別長期時間減衰差枚
    GROUP_B = [f'island_ewm_diff_{w}d' for w in (30, 60, 90)]
    # GROUP_C: 月間累計差枚 (台・店舗全体)
    GROUP_C = ['machine_month_cumul_diff', 'store_month_cumul_diff']
    # GROUP_D: 特定条件 (イベント翌日高設定不発など)
    GROUP_D = ['event_next_high_neg_1', 'neg_low_and_high_diff_prev_1']

    ALL_NEW_FEATURES = GROUP_0 + GROUP_A + GROUP_B + GROUP_C + GROUP_D

    def _quick_oof_score(feat_cols_q, label='', use_weights=False, use_lr_plus=False):
        """軽量OOF CV で精度を高速測定 (フルバックテストより大幅に高速)"""
        import numpy as np
        from sklearn.ensemble import ExtraTreesClassifier as _ETC
        from sklearn.model_selection import TimeSeriesSplit as _TSCV
        df_q = df_cls_sel.copy()
        cols_q = [c for c in feat_cols_q if c in df_q.columns]
        X_q = df_q[cols_q].replace([np.inf, -np.inf], 0).fillna(0)
        y_q = df_q['高設定フラグ']
        settings_q = df_q['推定設定'].values
        
        n_splits = min(5, len(X_q) // 20)
        if n_splits < 2:
            return {'profit': 0, 'precision': 0, 'f1': 0, 'avg_diff': 0, 'lr_plus': 0}
            
        sample_weights = np.ones(len(y_q))
        if use_weights:
            sample_weights[settings_q == 5] = 1.5
            sample_weights[settings_q == 6] = 2.0
            
        tscv = _TSCV(n_splits=n_splits)
        oof = np.full(len(X_q), np.nan)
        mdl = _ETC(n_estimators=100, max_depth=7, min_samples_leaf=20,
                   max_features=0.7, class_weight='balanced_subsample',
                   random_state=42, n_jobs=-1)
                   
        for tr_idx, va_idx in tscv.split(X_q):
            m = _ETC(**mdl.get_params())
            m.fit(X_q.iloc[tr_idx], y_q.iloc[tr_idx], sample_weight=sample_weights[tr_idx])
            oof[va_idx] = m.predict_proba(X_q.iloc[va_idx])[:, 1]
            
        vm = ~np.isnan(oof)
        oof_v = oof[vm]; y_v = y_q.values[vm]
        diff_v = df_q['最終差枚'].values[vm]
        
        best_score = -np.inf
        best_metrics = {}
        for th in np.arange(0.15, 0.75, 0.01):
            pred_v = (oof_v >= th).astype(int)
            n_pred = pred_v.sum()
            if n_pred < 3 or (n_pred / len(pred_v)) < 0.05:
                continue
                
            tp = ((y_v == 1) & (pred_v == 1)).sum()
            fp = ((y_v == 0) & (pred_v == 1)).sum()
            tn = ((y_v == 0) & (pred_v == 0)).sum()
            fn = ((y_v == 1) & (pred_v == 0)).sum()
            
            tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
            lr_plus = tpr / fpr if fpr > 0 else (tpr / 0.0001)
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0
            f1 = 2 * prec * tpr / (prec + tpr) if (prec + tpr) > 0 else 0
            
            avg_d = float(diff_v[pred_v == 1].mean()) if n_pred > 0 else 0.0
            
            if use_lr_plus:
                score = avg_d * (1.0 if lr_plus >= 1.5 else 0.5)
            else:
                score = avg_d * (1.0 if prec >= 0.20 else 0.5)
                
            if score > best_score:
                best_score = score
                best_metrics = {'precision': float(prec), 'f1': float(f1), 'avg_diff': float(avg_d), 'lr_plus': float(lr_plus)}
                
        if not best_metrics:
            best_metrics = {'precision': 0.0, 'f1': 0.0, 'avg_diff': 0.0, 'lr_plus': 0.0}
            
        if label:
            if use_lr_plus:
                print(f"    {label}: lr+={best_metrics['lr_plus']:.2f}  avg_diff={best_metrics['avg_diff']:+.0f}枚")
            else:
                print(f"    {label}: precision={best_metrics['precision']:.3f}  f1={best_metrics['f1']:.3f}  avg_diff={best_metrics['avg_diff']:+.0f}枚")
        return best_metrics

    # ── ① アブレーション測定 ──
    print("\n=== 特徴量グループ別アブレーション測定 (軽量OOF CV) ===")
    # ベースライン: 今回追加した特徴量をすべて除外
    base_cols_abl = [c for c in selected_features if c not in ALL_NEW_FEATURES and c in df_feat.columns]
    sc_base = _quick_oof_score(base_cols_abl, 'ベースライン (今回追加なし)')

    # 各グループを個別に追加して測定
    abl_results = {}
    for gname, gcols in [('GROUP_0 (前回追加)', GROUP_0), ('GROUP_A (台別長期)', GROUP_A),
                          ('GROUP_B (島別長期)', GROUP_B), ('GROUP_C (月間累計)', GROUP_C),
                          ('GROUP_D (特定条件)', GROUP_D)]:
        test_cols = base_cols_abl + [c for c in gcols if c in df_feat.columns]
        sc = _quick_oof_score(test_cols, gname)
        abl_results[gname] = sc

    # 全グループ追加
    all_new_cols = [c for c in ALL_NEW_FEATURES if c in df_feat.columns]
    test_all_cols = base_cols_abl + all_new_cols
    sc_all = _quick_oof_score(test_all_cols, '全グループ追加')

    # ── ② 採用グループを決定 ──
    # precision が baseline 以上 かつ avg_diff が baseline 以上のグループを採用
    adopted_groups = []
    for gname, gcols in [('GROUP_0', GROUP_0), ('GROUP_A', GROUP_A),
                          ('GROUP_B', GROUP_B), ('GROUP_C', GROUP_C), ('GROUP_D', GROUP_D)]:
        sc = abl_results.get(f'{gname} (前回追加)' if gname == 'GROUP_0'
                              else f'{gname} (台別長期)' if gname == 'GROUP_A'
                              else f'{gname} (島別長期)' if gname == 'GROUP_B'
                              else f'{gname} (月間累計)' if gname == 'GROUP_C'
                              else f'{gname} (特定条件)', {})
        # キー名の揺れを吸収
        sc = next((v for k, v in abl_results.items() if gname in k), {})
        prec_ok = sc.get('precision', 0) >= sc_base.get('precision', 0) - 0.005
        diff_ok = sc.get('avg_diff', 0) >= sc_base.get('avg_diff', 0) - 50
        if prec_ok and diff_ok:
            adopted_groups.append(gcols)
            print(f"  ✅ 採用: {gname}")
        else:
            print(f"  ❌ 除外: {gname} (precision: {sc.get('precision',0):.3f} vs base {sc_base.get('precision',0):.3f})")

    adopted_new_feats = [c for g in adopted_groups for c in g]
    print(f"\n  採用された新特徴量数: {len(adopted_new_feats)}")

    # ── ③ バックテスト2段階目 (ステップワイズ特徴量探索) ──
    print("\n=== バックテスト2段階目 (ステップワイズ特徴量探索) ===")
    old_selected = [c for c in selected_features if c not in ALL_NEW_FEATURES and c in df_feat.columns]
    
    current_best_features = list(old_selected)
    current_best_score = _quick_oof_score(current_best_features).get('avg_diff', 0)
    print(f"  初期ベース(旧特徴量): {len(current_best_features)}個, スコア: {current_best_score:+.0f}枚")
    
    all_possible_features = [c for c in FEATURE_COLS if c in df_feat.columns]
    
    improved = True
    step = 0
    while improved:
        improved = False
        step += 1
        best_step_score = current_best_score
        best_step_features = None
        best_action = ""
        
        # 1つ追加をテスト
        for f in all_possible_features:
            if f not in current_best_features:
                test_feats = current_best_features + [f]
                sc = _quick_oof_score(test_feats).get('avg_diff', 0)
                if sc > best_step_score:
                    best_step_score = sc
                    best_step_features = test_feats
                    best_action = f"+ {f}"
                    
        # 1つ削除をテスト
        for f in current_best_features:
            test_feats = [c for c in current_best_features if c != f]
            if len(test_feats) < 5: continue
            sc = _quick_oof_score(test_feats).get('avg_diff', 0)
            if sc > best_step_score:
                best_step_score = sc
                best_step_features = test_feats
                best_action = f"- {f}"
                
        if best_step_features is not None and best_step_score > current_best_score:
            print(f"  Step {step}: {best_action} -> スコア更新: {best_step_score:+.0f}枚")
            current_best_features = best_step_features
            current_best_score = best_step_score
            improved = True
        else:
            print(f"  Step {step}: 改善なし。探索終了。")
            
    print(f"  探索完了: 最終特徴量 {len(current_best_features)}個, スコア: {current_best_score:+.0f}枚")
    optimal_feat_cols = current_best_features

    # --- 独立テスト (今回のみ) ---
    print("\n=== 独立テスト1: 設定の段階の重みづけ ===")
    sc_base_test = _quick_oof_score(current_best_features)
    sc_weight_test = _quick_oof_score(current_best_features, use_weights=True)
    print(f"  ベース: {sc_base_test['avg_diff']:+.0f}枚")
    print(f"  重み付(設定5=1.5, 6=2.0): {sc_weight_test['avg_diff']:+.0f}枚")
    USE_SAMPLE_WEIGHTS = False
    if sc_weight_test['avg_diff'] > sc_base_test['avg_diff']:
        print("  ✅ 性能が向上したため、設定の重みづけを採用します。")
        USE_SAMPLE_WEIGHTS = True
    else:
        print("  ❌ 性能が悪化したため、設定の重みづけは不採用とします。")

    print("\n=== 独立テスト2: 陽性尤度比(LR+)の使用 ===")
    sc_lr_test = _quick_oof_score(current_best_features, use_weights=USE_SAMPLE_WEIGHTS, use_lr_plus=True)
    base_avg_diff = sc_weight_test['avg_diff'] if USE_SAMPLE_WEIGHTS else sc_base_test['avg_diff']
    print(f"  LR+ベース: {sc_lr_test['avg_diff']:+.0f}枚")
    USE_LR_PLUS = False
    if sc_lr_test['avg_diff'] > base_avg_diff:
        print("  ✅ 性能が向上したため、陽性尤度比(LR+)を採用します。")
        USE_LR_PLUS = True
    else:
        print("  ❌ 性能が悪化したため、陽性尤度比(LR+)は不採用とします。")

    # ── ④ バックテスト: 旧セット vs 最適セット vs 採用新特徴量セット ──
    print("\n=== バックテスト (Walk-forward) ===")
    pos_sum = y_sel.sum()
    spw = (len(y_sel) - pos_sum) / pos_sum if pos_sum > 0 else 1

    def model_factories_bt(spw_val):
        from xgboost import XGBClassifier
        import lightgbm as lgb
        from catboost import CatBoostClassifier
        return [
            XGBClassifier(
                n_estimators=260, max_depth=3, learning_rate=0.02,
                reg_lambda=20, reg_alpha=2, subsample=0.8, colsample_bytree=0.75,
                gamma=1.5, min_child_weight=15, tree_method='hist',
                random_state=42, scale_pos_weight=spw_val, eval_metric='logloss'
            ),
            lgb.LGBMClassifier(
                n_estimators=260, max_depth=3, learning_rate=0.02,
                reg_lambda=25, reg_alpha=3, subsample=0.8, colsample_bytree=0.75,
                min_child_samples=100, num_leaves=10, random_state=42, verbose=-1,
                scale_pos_weight=spw_val
            ),
            ExtraTreesClassifier(
                n_estimators=500, max_depth=9, min_samples_leaf=25,
                max_features=0.7, class_weight='balanced_subsample',
                random_state=42, n_jobs=-1
            ),
            # CatBoost: 順序型特徴量を自動的に扱えるため多様性に貢献
            CatBoostClassifier(
                iterations=250, depth=4, learning_rate=0.03,
                l2_leaf_reg=15, bootstrap_type='Bernoulli', subsample=0.8,
                auto_class_weights='Balanced',
                random_seed=42, verbose=0, task_type='GPU'
            ),
        ]

    def reg_factory_bt():
        from xgboost import XGBRegressor
        return XGBRegressor(n_estimators=200, max_depth=3, learning_rate=0.03,
                            reg_lambda=15, reg_alpha=5,
                            subsample=0.7, colsample_bytree=0.6,
                            min_child_weight=20,
                            tree_method='hist', device='cuda', random_state=42)

    def _extract_bt_metrics(bt_res):
        """バックテスト結果から成績指標を抽出するヘルパー"""
        if not bt_res:
            return {'profit': 0.0, 'hit_rate': 0.0, 'tp_ratio': 0.0, 'fp_ratio': 0.0, 'daily_avg': 0.0}
        active = [r for r in bt_res if not r.get('skipped', False)]
        final = bt_res[-1]
        profit = float(final.get('cumulative_profit', 0))
        daily_avg = profit / len(active) if active else 0.0
        hit_rates = [r.get('hit_rate', 0) for r in active if 'hit_rate' in r]
        tp_ratios  = [r.get('tp_ratio', 0) for r in active if 'tp_ratio' in r]
        fp_ratios  = [r.get('fp_ratio', 0) for r in active if 'fp_ratio' in r]
        return {
            'profit':    profit,
            'daily_avg': daily_avg,
            'hit_rate':  float(np.mean(hit_rates)) if hit_rates else 0.0,
            'tp_ratio':  float(np.mean(tp_ratios)) if tp_ratios else 0.0,
            'fp_ratio':  float(np.mean(fp_ratios)) if fp_ratios else 0.0,
        }

    # 今回追加した全新特徴量 (採否に関わらずロールバック判定に使う)
    NEW_FEATURES = ALL_NEW_FEATURES


    print("  [旧特徴量セット] バックテスト中...")
    old_selected = [c for c in selected_features if c not in ALL_NEW_FEATURES]
    feat_cols_old = [c for c in old_selected if c in df_feat.columns]
    bt_old = run_backtest(df_feat, feat_cols_old, model_factories_bt, reg_factory_bt, spw, top_n=3)
    metrics_old = _extract_bt_metrics(bt_old)
    print(f"    累積収支: {metrics_old['profit']:+,.0f}枚 | "
          f"日次平均: {metrics_old['daily_avg']:+,.0f}枚 | "
          f"的中率: {metrics_old['hit_rate']:.3f}")

    print("  [後退選択・最適特徴量セット] バックテスト中...")
    feat_cols_optimal = [c for c in optimal_feat_cols if c in df_feat.columns]
    bt_opt = run_backtest(df_feat, feat_cols_optimal, model_factories_bt, reg_factory_bt, spw, top_n=3)
    metrics_opt = _extract_bt_metrics(bt_opt)
    print(f"    累積収支: {metrics_opt['profit']:+,.0f}枚 | "
          f"日次平均: {metrics_opt['daily_avg']:+,.0f}枚 | "
          f"的中率: {metrics_opt['hit_rate']:.3f}  ({len(feat_cols_optimal)}特徴量)")

    print("  [採用新特徴量セット] バックテスト中...")
    feat_cols_adopted = feat_cols_old + [c for c in adopted_new_feats if c in df_feat.columns and c in selected_features]
    bt_new = run_backtest(df_feat, feat_cols_adopted, model_factories_bt, reg_factory_bt, spw, top_n=3)
    metrics_new = _extract_bt_metrics(bt_new)
    print(f"    累積収支: {metrics_new['profit']:+,.0f}枚 | "
          f"日次平均: {metrics_new['daily_avg']:+,.0f}枚 | "
          f"的中率: {metrics_new['hit_rate']:.3f}")

    # ── ⑤ 三者比較で最良セットを採用 ──
    # 最良 = 累積収支が最も高いセット
    _candidates_bt = [
        ('old',     metrics_old['profit'], bt_old,  feat_cols_old,     'old (baseline)'),
        ('optimal', metrics_opt['profit'], bt_opt,  feat_cols_optimal, f'optimal (backward-elim {len(feat_cols_optimal)}feat)'),
        ('new',     metrics_new['profit'], bt_new,  feat_cols_adopted, 'new (adopted groups)'),
    ]
    _best = max(_candidates_bt, key=lambda x: x[1])
    _best_key, _best_profit, bt_results, feat_cols_bt, feature_set_label = _best

    print(f"\n  🏆 最良セット: [{_best_key}] 累積収支={_best_profit:+,.0f}枚")
    for _key, _profit, _, _, _label in _candidates_bt:
        _mark = '✅' if _key == _best_key else '  '
        print(f"    {_mark} {_label}: {_profit:+,.0f}枚")

    # ロールバック判定: 最良が旧セット未満(5%以上悪化)なら旧にフォールバック
    if _best_profit < metrics_old['profit'] * 0.95:
        print("  ⚠️ 全セットが旧セット比5%以上悪化 → 旧セットにロールバック")
        bt_results = bt_old
        feat_cols_bt = feat_cols_old
        feature_set_label = 'old (rollback)'
        FEATURE_COLS[:] = [c for c in FEATURE_COLS if c not in ALL_NEW_FEATURES]
    elif _best_key != 'old':
        # 最良が old でなければ FEATURE_COLS を最良セットに更新
        FEATURE_COLS[:] = [c for c in FEATURE_COLS if c in feat_cols_bt]

    results['feature_set_used'] = feature_set_label
    results['backtest_metrics_old'] = metrics_old
    results['backtest_metrics_optimal'] = metrics_opt
    results['backtest_metrics_new'] = metrics_new
    results['optimal_features'] = feat_cols_optimal
    results['ablation_results'] = {k: v for k, v in abl_results.items()}


    if bt_results:
        active_days = [r for r in bt_results if not r.get('skipped', False)]
        print(f"\n  バックテスト期間: {len(bt_results)}日")
        print(f"  稼働日数: {len(active_days)}日")
        if active_days:
            final = bt_results[-1]
            print(f"  最終累積収支: {final['cumulative_profit']:+,.0f}枚")
            print(f"  ランダム選択: {final['random_cumulative']:+,.0f}枚")
            print(f"  全台平均:     {final['avg_cumulative']:+,.0f}枚")
            avg_daily = final['cumulative_profit'] / len(active_days)
            print(f"  平均日別収支: {avg_daily:+,.0f}枚")

        # グラフ出力
        graph_path = OUTPUT_PATH.replace('.json', '_backtest.png')
        plot_backtest(bt_results, graph_path)
        print(f"  グラフ出力: {graph_path}")

        bt_summary = {
            'n_days': len(bt_results),
            'n_active_days': len(active_days),
            'final_cumulative_profit': float(bt_results[-1]['cumulative_profit']) if bt_results else 0,
            'final_random_cumulative': float(bt_results[-1]['random_cumulative']) if bt_results else 0,
            'final_avg_cumulative': float(bt_results[-1]['avg_cumulative']) if bt_results else 0,
            'daily_avg_profit': float(final['cumulative_profit'] / len(active_days)) if active_days else 0,
            'graph_path': graph_path,
            'feature_set_used': feature_set_label,
        }
        results['backtest'] = bt_summary
    
    # === 翌日予測の生成 ===
    print("\n=== 翌日予測の生成 ===")
    results['next_day_predictions'] = predict_next_day(
        df_feat, 
        selected_feats=feat_cols_optimal, 
        layout_lookup=lookup, 
        use_weights=USE_SAMPLE_WEIGHTS, 
        use_lr_plus=USE_LR_PLUS
    )

    import json
    json_str = pd.Series([results]).to_json(orient='records', force_ascii=False)
    json_str = json_str[1:-1]
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(json_str)
        
    print("\n=========================================")
    print(f"分析が完了しました！")
    print(f"結果を {OUTPUT_PATH} に出力しました。")
    print("=========================================")

    # === Github へのコミットとプッシュ ===
    print("\n=== Github へのコミットとプッシュ ===")
    import subprocess
    
    try:
        # コミット対象ファイルの追加
        subprocess.run(["git", "add", OUTPUT_PATH], check=True)
        if 'graph_path' in locals():
            subprocess.run(["git", "add", graph_path], check=True)
            
        # 変更があるか確認
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
        if status.stdout.strip():
            # コミット
            commit_msg = f"Auto-update analysis results ({pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')})"
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
            
            # プッシュ
            subprocess.run(["git", "push"], check=True)
            print("Githubへのプッシュが完了しました。")
        else:
            print("変更がないため、コミットとプッシュをスキップしました。")
    except subprocess.CalledProcessError as e:
        print(f"Git操作中にエラーが発生しました: {e}")

