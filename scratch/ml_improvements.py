# -*- coding: utf-8 -*-
"""
ML予測システム改善モジュール
- Permutation Importanceによる特徴量選択
- 収支ベース閾値最適化
- Walk-forward バックテスト
- 累積収支グラフ出力
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import precision_score, recall_score, f1_score


def select_features_by_permutation(X, y, model, n_repeats=5):
    """Permutation Importanceで寄与のある特徴量のみを選択する"""
    from sklearn.inspection import permutation_importance
    n_splits = min(3, len(X) // 50)
    if n_splits < 2:
        return list(X.columns)
    tscv = TimeSeriesSplit(n_splits=n_splits)
    for train_idx, val_idx in tscv.split(X):
        pass
    model.fit(X.iloc[train_idx], y.iloc[train_idx])
    perm = permutation_importance(model, X.iloc[val_idx], y.iloc[val_idx],
                                   n_repeats=n_repeats, random_state=42, n_jobs=-1)
    selected = [col for col, imp in zip(X.columns, perm.importances_mean) if imp > 0]
    if len(selected) < 5:
        top_idx = np.argsort(perm.importances_mean)[-5:]
        selected = [X.columns[i] for i in top_idx]
    return selected


def optimize_threshold_by_profit(oof_probs, y_true, diffs):
    """
    閾値ごとに「選択台の平均差枚」を計算し、収支を最大化する閾値を探索。
    選択率が最低10%を下回らないよう制約を設ける。
    """
    best_profit = -np.inf
    best_th = 0.3
    best_stats = {}
    n_total = len(oof_probs)
    min_selection_rate = 0.10  # 最低10%は候補にする
    
    for th in np.arange(0.15, 0.75, 0.005):
        selected_mask = oof_probs >= th
        n_selected = int(selected_mask.sum())
        selection_rate = n_selected / n_total
        
        if n_selected < 3 or selection_rate < min_selection_rate:
            continue
        
        selected_diffs = diffs[selected_mask]
        avg_diff = float(selected_diffs.mean())
        precision = float(y_true[selected_mask].mean()) if n_selected > 0 else 0
        recall = float(y_true[selected_mask].sum() / y_true.sum()) if y_true.sum() > 0 else 0
        
        # 収支スコア: 平均差枚（ただし精度が25%未満なら大きくペナルティ）
        # 精度が低い＝偽陽性が多い → 実運用で損失リスク大
        profit_score = avg_diff
        if precision < 0.20:
            profit_score *= 0.5  # 精度が低すぎる場合はペナルティ
        
        if profit_score > best_profit:
            best_profit = profit_score
            best_th = th
            best_stats = {
                'threshold': float(th),
                'n_selected': n_selected,
                'selection_rate': selection_rate,
                'avg_diff': avg_diff,
                'precision': precision,
                'recall': recall,
            }
    
    return best_th, best_stats


def run_backtest(df_feat, feat_cols, model_factories_fn, reg_factory_fn, spw, top_n=3,
                 use_weights=False, use_lr_plus=False, use_soft_labels=False, use_shap_pruning=False):
    """
    Walk-forward バックテスト。
    学習期間を徐々に拡大しながら、毎日Top-N台を選択した場合の累積収支を計算。
    """
    all_dates = sorted(df_feat['日付'].unique())
    n_dates = len(all_dates)
    
    train_end_idx = int(n_dates * 0.6)
    if train_end_idx < 20:
        train_end_idx = min(20, n_dates - 10)
    
    df_cls = df_feat[df_feat['推定設定'].notna()].copy()
    df_cls['高設定フラグ'] = (df_cls['推定設定'] >= 4).astype(int)
    if '高設定確率' not in df_cls.columns:
        df_cls['高設定確率'] = df_cls['高設定フラグ'].astype(float)
    else:
        df_cls['高設定確率'] = df_cls['高設定確率'].fillna(df_cls['高設定フラグ'].astype(float))
        
    daily_results = []
    cumulative_profit = 0
    random_cumulative = 0
    avg_cumulative = 0
    
    retrain_interval = 5
    trained_models = None
    trained_reg_model = None
    trained_threshold = 0.5
    last_train_idx = -retrain_interval
    current_feat_cols = list(feat_cols)
    
    def to_regressor(clf):
        from xgboost import XGBRegressor
        import lightgbm as lgb
        from sklearn.ensemble import ExtraTreesRegressor
        from catboost import CatBoostRegressor
        
        clf_name = str(clf.__class__)
        params = clf.get_params()
        
        # 不要なパラメータを削除
        for key in ['scale_pos_weight', 'class_weight', 'auto_class_weights', 'eval_metric', 'tree_method', 'device', 'criterion', 'verbose', 'task_type']:
            params.pop(key, None)
            
        if 'XGBClassifier' in clf_name:
            return XGBRegressor(**params, tree_method='hist', device='cuda')
        elif 'LGBMClassifier' in clf_name:
            return lgb.LGBMRegressor(**params)
        elif 'ExtraTreesClassifier' in clf_name:
            return ExtraTreesRegressor(**params)
        elif 'CatBoostClassifier' in clf_name:
            return CatBoostRegressor(**params, verbose=0, task_type='GPU')
        return clf

    for eval_idx in range(train_end_idx, n_dates):
        eval_date = all_dates[eval_idx]
        train_dates = all_dates[:eval_idx]
        
        eval_df = df_feat[df_feat['日付'] == eval_date]
        if eval_df.empty:
            continue
        
        train_cls = df_cls[df_cls['日付'].isin(train_dates)]
        if len(train_cls) < 30 or train_cls['高設定フラグ'].sum() < 5:
            continue
            
        # ターゲットとサンプルの重みを決定
        settings_train = train_cls['推定設定'].values
        sample_weights = np.ones(len(train_cls))
        if use_weights:
            sample_weights[settings_train == 5] = 1.5
            sample_weights[settings_train == 6] = 2.0
            
        if use_soft_labels:
            y_train = train_cls['高設定確率'].values
        else:
            y_train = train_cls['高設定フラグ'].values
            
        train_reg = df_feat[df_feat['日付'].isin(train_dates)]
        y_train_reg = train_reg['最終差枚']
        overall_avg = float(y_train_reg.mean())
        
        if eval_idx - last_train_idx >= retrain_interval or trained_models is None:
            # 特徴量決定（SHAP削減）
            X_train_full = train_cls[feat_cols].replace([np.inf, -np.inf], 0).fillna(0)
            if use_shap_pruning:
                try:
                    import shap
                    from sklearn.ensemble import ExtraTreesClassifier
                    shap_model = ExtraTreesClassifier(n_estimators=100, max_depth=7, random_state=42, n_jobs=-1)
                    shap_model.fit(X_train_full, train_cls['高設定フラグ'])
                    explainer = shap.TreeExplainer(shap_model)
                    shap_values = explainer.shap_values(X_train_full)
                    if isinstance(shap_values, list):
                        sv = shap_values[1]
                    elif hasattr(shap_values, 'ndim') and shap_values.ndim == 3:
                        sv = shap_values[:, :, 1]
                    else:
                        sv = shap_values
                    mean_abs_shap = np.abs(sv).mean(axis=0)
                    shap_df = pd.Series(mean_abs_shap, index=feat_cols).sort_values(ascending=False)
                    shap_threshold = shap_df.max() * 0.01
                    active_feats = shap_df[shap_df >= shap_threshold].index.tolist()
                    if len(active_feats) >= 5:
                        current_feat_cols = active_feats
                    else:
                        current_feat_cols = list(feat_cols)
                except Exception as e_shap:
                    print(f"  [SHAP Pruning Error] {e_shap}")
                    current_feat_cols = list(feat_cols)
            else:
                current_feat_cols = list(feat_cols)
                
            X_train = train_cls[current_feat_cols].replace([np.inf, -np.inf], 0).fillna(0)
            X_train_reg = train_reg[current_feat_cols].replace([np.inf, -np.inf], 0).fillna(0)
            
            trained_models = []
            for factory in model_factories_fn(spw):
                m = to_regressor(factory) if use_soft_labels else factory
                if use_weights or use_soft_labels:
                    m.fit(X_train, y_train, sample_weight=sample_weights)
                else:
                    m.fit(X_train, y_train)
                trained_models.append(m)
                
            trained_reg_model = reg_factory_fn()
            trained_reg_model.fit(X_train_reg, y_train_reg)
            
            # OOFによる重み決定
            n_splits = min(3, int(train_cls['高設定フラグ'].sum()))
            if n_splits < 2:
                n_splits = 2
            tscv = TimeSeriesSplit(n_splits=n_splits)
            n_models = len(trained_models)
            oof_by_m = [np.full(len(X_train), np.nan) for _ in range(n_models)]
            
            for m_i, m_template in enumerate(model_factories_fn(spw)):
                m_cv = to_regressor(m_template) if use_soft_labels else m_template
                for tr_idx, val_idx in tscv.split(X_train):
                    m_cv_clone = m_cv.__class__(**m_cv.get_params())
                    if use_weights or use_soft_labels:
                        m_cv_clone.fit(X_train.iloc[tr_idx], y_train[tr_idx], sample_weight=sample_weights[tr_idx])
                    else:
                        m_cv_clone.fit(X_train.iloc[tr_idx], y_train[tr_idx])
                        
                    if use_soft_labels:
                        oof_by_m[m_i][val_idx] = np.clip(m_cv_clone.predict(X_train.iloc[val_idx]), 0.0, 1.0)
                    else:
                        oof_by_m[m_i][val_idx] = m_cv_clone.predict_proba(X_train.iloc[val_idx])[:, 1]
                        
            train_diffs = train_cls['最終差枚'].values
            TARGET_RATE = 0.25
            model_weights = []
            for m_i in range(n_models):
                m_oof = oof_by_m[m_i]
                valid = ~np.isnan(m_oof)
                if valid.sum() < 5:
                    model_weights.append(0.0)
                    continue
                v = m_oof[valid]
                v_min, v_max = v.min(), v.max()
                if v_max > v_min:
                    v_norm = (v - v_min) / (v_max - v_min)
                else:
                    v_norm = v
                th_top = np.percentile(v_norm, 100 * (1 - TARGET_RATE))
                sel = v_norm >= th_top
                avg_d = float(train_diffs[valid][sel].mean()) if sel.sum() > 0 else 0.0
                model_weights.append(max(0.0, avg_d))
                
            w_sum = sum(model_weights)
            if w_sum <= 0:
                trained_weights = np.ones(n_models) / n_models
            else:
                trained_weights = np.array(model_weights) / w_sum
                
            # 重み付きOOFで閾値最適化
            all_valid = np.all(~np.isnan(np.vstack(oof_by_m)), axis=0)
            if all_valid.sum() > 10:
                oof_weighted = np.average(
                    np.vstack([o[all_valid] for o in oof_by_m]), axis=0,
                    weights=trained_weights
                )
                trained_threshold, _ = optimize_threshold_by_profit(
                    oof_weighted,
                    train_cls['高設定フラグ'].values[all_valid],
                    train_cls['最終差枚'].values[all_valid]
                )
            last_train_idx = eval_idx
            
        X_eval = eval_df[current_feat_cols].replace([np.inf, -np.inf], 0).fillna(0)
        
        preds_stack = []
        for m in trained_models:
            if use_soft_labels:
                preds_stack.append(np.clip(m.predict(X_eval), 0.0, 1.0))
            else:
                preds_stack.append(m.predict_proba(X_eval)[:, 1])
        preds = np.average(np.vstack(preds_stack), axis=0, weights=trained_weights)
        
        eval_df = eval_df.copy()
        eval_df['pred_prob'] = preds
        
        pred_diffs = trained_reg_model.predict(X_eval)
        eval_df['adjusted_diff'] = preds * pred_diffs + (1 - preds) * overall_avg
        
        candidates = eval_df[eval_df['pred_prob'] >= trained_threshold]
        avg_profit = float(eval_df['最終差枚'].mean())
        
        if len(candidates) == 0:
            candidates = eval_df.nlargest(top_n, 'adjusted_diff')
            
        selected = candidates.nlargest(top_n, 'adjusted_diff')
        selected_profit = float(selected['最終差枚'].mean())
        random_profit = float(eval_df['最終差枚'].sample(
            min(top_n, len(eval_df)), random_state=eval_idx).mean())
            
        cumulative_profit += selected_profit
        random_cumulative += random_profit
        avg_cumulative += avg_profit
        
        selected_high = 0
        if '推定設定' in selected.columns:
            selected_high = int((selected['推定設定'].dropna() >= 4).sum())
            
        daily_results.append({
            'date': eval_date,
            'selected_profit': selected_profit,
            'n_selected': len(selected),
            'n_high_in_selected': selected_high,
            'random_profit': random_profit,
            'avg_profit': avg_profit,
            'cumulative_profit': cumulative_profit,
            'random_cumulative': random_cumulative,
            'avg_cumulative': avg_cumulative,
            'threshold': trained_threshold,
            'model_weights': trained_weights.tolist(),
            'skipped': False,
        })
        
    return daily_results



def plot_backtest(daily_results, output_path):
    """バックテスト結果の累積収支グラフをPNG出力"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import rcParams
    
    rcParams['font.family'] = 'sans-serif'
    rcParams['font.sans-serif'] = ['Yu Gothic', 'Meiryo', 'MS Gothic', 'Hiragino Sans']
    rcParams['axes.unicode_minus'] = False
    
    active_results = [r for r in daily_results if not r.get('skipped', False)]
    if not active_results:
        return None
    
    dates = [r['date'] for r in daily_results]
    cum_profit = [r['cumulative_profit'] for r in daily_results]
    cum_random = [r['random_cumulative'] for r in daily_results]
    cum_avg = [r['avg_cumulative'] for r in daily_results]
    daily_profit = [r['selected_profit'] for r in daily_results]
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})
    
    ax1 = axes[0]
    ax1.fill_between(range(len(dates)), cum_profit, alpha=0.15, color='#00C853')
    ax1.plot(range(len(dates)), cum_profit, label='モデル選択 (Top-3)',
             color='#00C853', linewidth=2.5, zorder=3)
    ax1.plot(range(len(dates)), cum_random, label='ランダム選択',
             color='#FF6D00', linewidth=1.5, linestyle='--', alpha=0.7)
    ax1.plot(range(len(dates)), cum_avg, label='全台平均',
             color='#2979FF', linewidth=1.5, linestyle=':', alpha=0.7)
    ax1.axhline(y=0, color='gray', linewidth=0.8, linestyle='-', alpha=0.5)
    
    peak = np.maximum.accumulate(cum_profit)
    drawdown = np.array(cum_profit) - peak
    dd_min = drawdown.min()
    
    ax1.set_title(f'バックテスト 累積収支推移\n'
                  f'最終収支: {cum_profit[-1]:+,.0f}枚 | '
                  f'最大DD: {dd_min:,.0f}枚 | '
                  f'稼働日数: {len(active_results)}日',
                  fontsize=14, fontweight='bold')
    ax1.set_ylabel('累積差枚', fontsize=12)
    ax1.legend(loc='upper left', fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    tick_interval = max(1, len(dates) // 10)
    tick_positions = list(range(0, len(dates), tick_interval))
    tick_labels_str = [pd.Timestamp(dates[i]).strftime('%m/%d') for i in tick_positions]
    ax1.set_xticks(tick_positions)
    ax1.set_xticklabels(tick_labels_str, rotation=45, fontsize=8)
    
    ax2 = axes[1]
    colors = ['#00C853' if d >= 0 else '#FF1744' for d in daily_profit]
    ax2.bar(range(len(dates)), daily_profit, color=colors, alpha=0.7, width=0.8)
    ax2.axhline(y=0, color='gray', linewidth=0.8, linestyle='-', alpha=0.5)
    ax2.set_title('日別損益', fontsize=11)
    ax2.set_ylabel('差枚', fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_xticks(tick_positions)
    ax2.set_xticklabels(tick_labels_str, rotation=45, fontsize=8)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    return output_path
