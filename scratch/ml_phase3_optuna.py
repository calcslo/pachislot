"""
フェーズ3: Optuna + LightGBM + 高度特徴量エンジニアリング
- 10日〜21日前の特徴量追加
- 移動平均・EWM特徴量
- 同曜日パターン（過去n週の同曜日成績）
- 設定変更検出フラグ
- LightGBM + Optuna ハイパーパラメータ探索
- XGBoost + LightGBM アンサンブル
"""
import pandas as pd
import numpy as np
import json, sqlite3, math, warnings
from collections import defaultdict
import xgboost as xgb
import lightgbm as lgb
import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import f1_score, precision_score, recall_score
warnings.filterwarnings('ignore')

# ─── データ読み込み ───────────────────────────
with open('docs/ogiya/layout.json', 'r', encoding='utf-8') as f:
    layout_data = json.load(f)

conn = sqlite3.connect('slot_data.db')
raw_df = pd.read_sql_query("SELECT * FROM slot_data WHERE 機種名 LIKE '%ﾊﾅﾊﾅ%'", conn)
conn.close()

MACHINE_PROBS = {
    'LBﾆｭｰｷﾝｸﾞﾊﾅﾊﾅV': {
        1: {'big': 319, 'reg': 619}, 2: {'big': 299, 'reg': 510},
        3: {'big': 282, 'reg': 469}, 4: {'big': 265, 'reg': 387},
        5: {'big': 248, 'reg': 325}, 6: {'big': 230, 'reg': 273},
    }
}

def estimate_setting(model, games, big, reg):
    try: games, big, reg = int(games or 0), int(big or 0), int(reg or 0)
    except: return None
    if model not in MACHINE_PROBS or games < 100: return None
    probs = MACHINE_PROBS[model]
    log_w, max_lw = {}, -math.inf
    for s, p in probs.items():
        pB, pR = 1/p['big'], 1/p['reg']
        pN = 1 - pB - pR
        if pN <= 0: continue
        lw = big*math.log(pB) + reg*math.log(pR) + (games-big-reg)*math.log(pN)
        log_w[s] = lw
        if lw > max_lw: max_lw = lw
    total = sum(math.exp(lw-max_lw) for lw in log_w.values())
    best, best_p = None, -1
    for s, lw in log_w.items():
        p = math.exp(lw-max_lw)/total
        if p > best_p: best_p, best = p, s
    return int(best) if best is not None else None

def build_layout_lookup(layout_data):
    rows, cols = len(layout_data), len(layout_data[0]) if layout_data else 0
    lookup = {}
    for r in range(rows):
        for c in range(cols):
            cell = layout_data[r][c]
            if cell in ('', None): continue
            num = str(cell).zfill(4)
            hL=hR=vT=vB=0
            for i in range(c-1,-1,-1):
                if layout_data[r][i] not in ('',None): hL+=1
                else: break
            for i in range(c+1,cols):
                if layout_data[r][i] not in ('',None): hR+=1
                else: break
            for i in range(r-1,-1,-1):
                if layout_data[i][c] not in ('',None): vT+=1
                else: break
            for i in range(r+1,rows):
                if layout_data[i][c] not in ('',None): vB+=1
                else: break
            nv = int(num)
            if (987<=nv<=998) or (1370<=nv<=1385): dist,direction=None,'circle'
            elif hL+hR>=vT+vB: dist,direction=min(hL,hR),'horizontal'
            else: dist,direction=min(vT,vB),'vertical'
            lookup[num]={'pos':dist,'direction':direction,'island_id':'','row':r,'col':c}
    visited=[[False]*cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            cell=layout_data[r][c]
            if cell in ('',None) or visited[r][c]: continue
            q=[(r,c)]; visited[r][c]=True; ic=[]
            d=lookup.get(str(cell).zfill(4),{}).get('direction')
            while q:
                cr,cc=q.pop(0)
                cv=str(layout_data[cr][cc]).zfill(4)
                cvv=int(cv)
                if (987<=cvv<=998) or (1370<=cvv<=1385): continue
                ic.append(cv)
                d=lookup.get(cv,{}).get('direction','horizontal')
                nb=[(cr,cc-1),(cr,cc+1)] if d=='horizontal' else [(cr-1,cc),(cr+1,cc)]
                for nr,nc in nb:
                    if 0<=nr<rows and 0<=nc<cols and not visited[nr][nc]:
                        ncc=layout_data[nr][nc]
                        if ncc in ('',None): continue
                        ncn=str(ncc).zfill(4)
                        if (987<=int(ncn)<=998) or (1370<=int(ncn)<=1385): continue
                        if lookup.get(ncn,{}).get('direction')==d:
                            visited[nr][nc]=True; q.append((nr,nc))
            if ic:
                ic.sort(key=lambda x:int(x))
                iid=f"{int(ic[0])}-{int(ic[-1])}"
                for nc in ic:
                    if nc in lookup: lookup[nc]['island_id']=iid
    return lookup

print("データ構築中...")
layout_lookup = build_layout_lookup(layout_data)
df = raw_df.copy()
df['日付'] = pd.to_datetime(df['日付'])
df['台番号_pad'] = df['台番号'].astype(str).str.zfill(4)
df['最終差枚'] = pd.to_numeric(df['最終差枚'], errors='coerce').fillna(0)
df['累計ゲーム'] = pd.to_numeric(df['累計ゲーム'], errors='coerce').fillna(0)
df['BIG'] = pd.to_numeric(df['BIG'], errors='coerce').fillna(0)
df['REG'] = pd.to_numeric(df['REG'], errors='coerce').fillna(0)
df['推定設定'] = df.apply(lambda r: estimate_setting(r['機種名'], r['累計ゲーム'], r['BIG'], r['REG']), axis=1)
df['position'] = df['台番号_pad'].apply(lambda x: layout_lookup.get(x,{}).get('pos',-1))
df['position'] = df['position'].apply(lambda x: x if x in [0,1,2] else 3)
df['island_id'] = df['台番号_pad'].apply(lambda x: layout_lookup.get(x,{}).get('island_id',''))
iids = list(df['island_id'].unique())
df['island_id_num'] = df['island_id'].apply(lambda x: iids.index(x) if x in iids else -1)
df['machine_num'] = df['台番号'].astype(int)
df['tail_digit'] = df['台番号_pad'].apply(lambda x: int(x[-1]))
df['weekday'] = df['日付'].dt.weekday
df['day_of_month'] = df['日付'].dt.day
df['is_event_day'] = df['day_of_month'].apply(lambda d: 1 if str(d).endswith(('3','5','8')) else 0)

all_dates = sorted(df['日付'].unique())
date_to_idx = {d:i for i,d in enumerate(all_dates)}
island_daily_avg = df.groupby(['日付','island_id'])['最終差枚'].mean().to_dict()

# 店舗全体の設定比率（日別）
date_high_ratio = {}
for date, grp in df[df['推定設定'].notna()].groupby('日付'):
    date_high_ratio[date] = float((grp['推定設定'] >= 4).mean())

print("特徴量を構築中...")
df_sorted = df.sort_values(['台番号_pad','日付']).reset_index(drop=True)
hist_feats = defaultdict(dict)

# ラグ数を21日まで拡張
MAX_LAG = 21

for num, grp in df_sorted.groupby('台番号_pad'):
    grp = grp.sort_values('日付')
    diffs = grp['最終差枚'].tolist()
    settings = grp['推定設定'].tolist()
    games = grp['累計ゲーム'].tolist()
    dates = grp['日付'].tolist()
    island = grp['island_id'].iloc[0]
    m_data = {d:{'diff':df_,'set':st,'game':gm} for d,df_,st,gm in zip(dates,diffs,settings,games)}
    cons_neg=0; cons_pos=0

    for i, date in enumerate(dates):
        date_idx = date_to_idx[date]; key=(num,date)
        if i > 0:
            p_=diffs[i-1]
            if p_<0: cons_neg+=1; cons_pos=0
            elif p_>0: cons_pos+=1; cons_neg=0
            else: cons_neg=0; cons_pos=0
        hist_feats[key]['cons_neg'] = min(cons_neg,6)
        hist_feats[key]['cons_pos'] = min(cons_pos,6)

        # ラグ特徴量（最大21日前）
        for j in range(1, MAX_LAG+1):
            past_date = all_dates[date_idx-j] if date_idx-j>=0 else None
            if past_date and past_date in m_data:
                pd_diff=m_data[past_date]['diff']; pd_game=m_data[past_date]['game']
                pd_set=m_data[past_date]['set'] if pd.notna(m_data[past_date]['set']) else -1
            else:
                pd_diff=0; pd_game=0; pd_set=-1
            i_avg=island_daily_avg.get((past_date,island),0) if past_date else 0
            hist_feats[key][f'prev_diff_{j}']=pd_diff
            hist_feats[key][f'prev_games_{j}']=pd_game
            hist_feats[key][f'island_avg_prev_{j}']=i_avg
            if j==1:
                hist_feats[key]['prev_setting_1']=pd_set
                hist_feats[key]['prev_high_setting_1']=1 if pd_set>=4 else 0

        # 同曜日の過去パターン（直近4週）
        same_wd_diffs = []
        for w in range(1,5):
            past_wd_date = all_dates[date_idx - w*7] if date_idx-w*7>=0 else None
            if past_wd_date and past_wd_date in m_data:
                same_wd_diffs.append(m_data[past_wd_date]['diff'])
        hist_feats[key]['same_wd_avg_diff'] = np.mean(same_wd_diffs) if same_wd_diffs else 0
        hist_feats[key]['same_wd_win_rate'] = sum(1 for x in same_wd_diffs if x>0)/len(same_wd_diffs) if same_wd_diffs else 0

        # 店舗全体の設定比率
        hist_feats[key]['store_high_ratio'] = date_high_ratio.get(date, 0.0)

print("特徴量をDFにマージ中...")
for col in ['cons_neg','cons_pos','prev_setting_1','prev_high_setting_1','same_wd_avg_diff','same_wd_win_rate','store_high_ratio']:
    df[col] = df.apply(lambda r: hist_feats[(r['台番号_pad'],r['日付'])].get(col,0), axis=1)
for j in range(1, MAX_LAG+1):
    df[f'prev_diff_{j}'] = df.apply(lambda r: hist_feats[(r['台番号_pad'],r['日付'])].get(f'prev_diff_{j}',0), axis=1)
    df[f'prev_games_{j}'] = df.apply(lambda r: hist_feats[(r['台番号_pad'],r['日付'])].get(f'prev_games_{j}',0), axis=1)
    if j <= 7:
        df[f'island_avg_prev_{j}'] = df.apply(lambda r: hist_feats[(r['台番号_pad'],r['日付'])].get(f'island_avg_prev_{j}',0), axis=1)

# 派生特徴量
df['neg_after_pos'] = ((df['prev_high_setting_1']==1)&(df['prev_diff_1']<0)).astype(int)
df['cumul_7d_diff'] = sum(df[f'prev_diff_{j}'] for j in range(1,8))
df['cumul_14d_diff'] = sum(df[f'prev_diff_{j}'] for j in range(1,15))
df['cumul_21d_diff'] = sum(df[f'prev_diff_{j}'] for j in range(1,22))
df['island_trend'] = (df['island_avg_prev_1']+df['island_avg_prev_2']+df['island_avg_prev_3'])/3
df['win_rate_7d'] = sum((df[f'prev_diff_{j}']>0).astype(int) for j in range(1,8))/7.0
df['win_rate_14d'] = sum((df[f'prev_diff_{j}']>0).astype(int) for j in range(1,15))/14.0
df['volatility_7d'] = df[[f'prev_diff_{j}' for j in range(1,8)]].std(axis=1).fillna(0)
df['avg_games_7d'] = df[[f'prev_games_{j}' for j in range(1,8)]].mean(axis=1)
df['island_avg_7d'] = sum(df[f'island_avg_prev_{j}'] for j in range(1,8))/7.0
# EWM（指数加重移動平均）
diff_cols_7 = [f'prev_diff_{j}' for j in range(1,8)]
df['ewm_diff_7d'] = df[diff_cols_7].apply(lambda row: pd.Series(row.values).ewm(span=3).mean().iloc[-1], axis=1)
# 設定変更検出（前日設定4以上→今日凹み）
df['setting_change_signal'] = ((df['prev_setting_1']>=4)&(df['prev_diff_1']<-500)).astype(int)
# 直近 momentum（前日差枚 vs 3日前差枚）
df['momentum_1v3'] = df['prev_diff_1'] - df['prev_diff_3']
# 台の「復活確率」（連続凹み日数 × 店舗全体の設定比率）
df['revival_score'] = df['cons_neg'] * df['store_high_ratio']

FEAT_COLS = [
    'machine_num','tail_digit','weekday','position','is_event_day','day_of_month','island_id_num',
    'cons_neg','cons_pos','prev_setting_1','prev_high_setting_1',
    'neg_after_pos','cumul_7d_diff','cumul_14d_diff','cumul_21d_diff',
    'island_trend','win_rate_7d','win_rate_14d','volatility_7d','avg_games_7d',
    'island_avg_7d','ewm_diff_7d','setting_change_signal','momentum_1v3',
    'revival_score','same_wd_avg_diff','same_wd_win_rate','store_high_ratio',
] + [f'prev_diff_{j}' for j in range(1,8)] + [f'prev_games_{j}' for j in range(1,8)] + [f'island_avg_prev_{j}' for j in range(1,8)]

df4 = df[df['推定設定'].notna()].copy()
df4['label'] = (df4['推定設定']>=4).astype(int)
X = df4[[c for c in FEAT_COLS if c in df4.columns]]
y = df4['label']
spw = (len(y)-y.sum())/y.sum() if y.sum()>0 else 1
print(f"データ: {len(y)}件, 高設定率: {y.mean():.3f}, 特徴量数: {len(X.columns)}")

CV = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# ─── Optuna: XGBoost 最適化 ───────────────────
print("\n【Optuna: XGBoost最適化中（50試行）...】")
def xgb_objective(trial):
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 200, 800),
        'max_depth': trial.suggest_int('max_depth', 2, 6),
        'learning_rate': trial.suggest_float('learning_rate', 0.005, 0.1, log=True),
        'reg_lambda': trial.suggest_float('reg_lambda', 1, 30),
        'reg_alpha': trial.suggest_float('reg_alpha', 0, 20),
        'subsample': trial.suggest_float('subsample', 0.5, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
        'gamma': trial.suggest_float('gamma', 0, 5),
        'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
        'tree_method': 'hist', 'device': 'cuda', 'scale_pos_weight': spw, 'random_state': 42
    }
    model = xgb.XGBClassifier(**params)
    proba = cross_val_predict(model, X, y, cv=CV, method='predict_proba')[:,1]
    # 閾値0.45でのF1を最大化
    preds = (proba >= 0.45).astype(int)
    return f1_score(y, preds, zero_division=0)

xgb_study = optuna.create_study(direction='maximize')
xgb_study.optimize(xgb_objective, n_trials=50, show_progress_bar=True)
best_xgb_params = {**xgb_study.best_params, 'tree_method':'hist','device':'cuda','scale_pos_weight':spw,'random_state':42}
print(f"XGBoost最良F1 (thr=0.45): {xgb_study.best_value:.4f}")
print(f"XGBoost最良パラメータ: {xgb_study.best_params}")

# ─── Optuna: LightGBM 最適化 ───────────────────
print("\n【Optuna: LightGBM最適化中（50試行）...】")
def lgb_objective(trial):
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 200, 800),
        'max_depth': trial.suggest_int('max_depth', 2, 8),
        'learning_rate': trial.suggest_float('learning_rate', 0.005, 0.1, log=True),
        'reg_lambda': trial.suggest_float('reg_lambda', 1, 30),
        'reg_alpha': trial.suggest_float('reg_alpha', 0, 20),
        'subsample': trial.suggest_float('subsample', 0.5, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
        'min_child_samples': trial.suggest_int('min_child_samples', 5, 50),
        'num_leaves': trial.suggest_int('num_leaves', 15, 63),
        'scale_pos_weight': spw, 'random_state': 42, 'verbose': -1
    }
    model = lgb.LGBMClassifier(**params)
    proba = cross_val_predict(model, X, y, cv=CV, method='predict_proba')[:,1]
    preds = (proba >= 0.45).astype(int)
    return f1_score(y, preds, zero_division=0)

lgb_study = optuna.create_study(direction='maximize')
lgb_study.optimize(lgb_objective, n_trials=50, show_progress_bar=True)
best_lgb_params = {**lgb_study.best_params, 'scale_pos_weight':spw,'random_state':42,'verbose':-1}
print(f"LightGBM最良F1 (thr=0.45): {lgb_study.best_value:.4f}")
print(f"LightGBM最良パラメータ: {lgb_study.best_params}")

# ─── 最良パラメータで OOF 予測 ───────────────────
print("\n【最良パラメータでOOF評価...】")
xgb_best = xgb.XGBClassifier(**best_xgb_params)
xgb_proba = cross_val_predict(xgb_best, X, y, cv=CV, method='predict_proba')[:,1]

lgb_best = lgb.LGBMClassifier(**best_lgb_params)
lgb_proba = cross_val_predict(lgb_best, X, y, cv=CV, method='predict_proba')[:,1]

# アンサンブル（加重平均: F1スコアで重み付け）
xgb_w = xgb_study.best_value
lgb_w = lgb_study.best_value
total_w = xgb_w + lgb_w
ens_proba = (xgb_proba * xgb_w + lgb_proba * lgb_w) / total_w

print("\n=== 各モデル・各閾値比較 ===")
print(f"{'モデル':<20} {'閾値':<6} {'F1':>8} {'Prec':>8} {'Rec':>8} {'予測件数':>10}")
for name, proba_ in [('XGBoost(Optuna)', xgb_proba), ('LightGBM(Optuna)', lgb_proba), ('アンサンブル', ens_proba)]:
    for thr in [0.35, 0.40, 0.45, 0.50, 0.55, 0.60]:
        p_ = (proba_ >= thr).astype(int)
        f1 = f1_score(y, p_, zero_division=0)
        pr = precision_score(y, p_, zero_division=0)
        re = recall_score(y, p_, zero_division=0)
        print(f"{name:<20} {thr:<6.2f} {f1:>8.4f} {pr:>8.4f} {re:>8.4f} {p_.sum():>10}")

# ─── 最良モデルの特徴量重要度 ───────────────────
print("\n=== 最良モデルの特徴量重要度（上位20件）===")
xgb_best.fit(X, y)
imp_df = pd.DataFrame({'feat': X.columns, 'imp': xgb_best.feature_importances_}).sort_values('imp', ascending=False)
for _, row in imp_df.head(20).iterrows():
    print(f"  {row['feat']}: {row['imp']:.4f}")

# ─── 最良設定を JSON 保存 ───────────────────
results = {
    'best_xgb_params': best_xgb_params,
    'best_lgb_params': best_lgb_params,
    'xgb_best_f1': xgb_study.best_value,
    'lgb_best_f1': lgb_study.best_value,
    'ensemble_weight_xgb': float(xgb_w),
    'ensemble_weight_lgb': float(lgb_w),
    'feature_cols': list(X.columns),
    'best_threshold': 0.45,
}
with open('scratch/ml_phase3_config.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2, default=str)
print("\nscratch/ml_phase3_config.json に保存しました")
