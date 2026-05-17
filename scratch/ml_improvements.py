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


def run_backtest(df_feat, feat_cols, model_factories_fn, reg_factory_fn, spw, top_n=3):
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
    
    daily_results = []
    cumulative_profit = 0
    random_cumulative = 0
    avg_cumulative = 0
    
    retrain_interval = 5
    trained_models = None
    trained_reg_model = None
    trained_threshold = 0.5
    last_train_idx = -retrain_interval
    
    for eval_idx in range(train_end_idx, n_dates):
        eval_date = all_dates[eval_idx]
        train_dates = all_dates[:eval_idx]
        
        eval_df = df_feat[df_feat['日付'] == eval_date]
        if eval_df.empty:
            continue
        
        train_cls = df_cls[df_cls['日付'].isin(train_dates)]
        if len(train_cls) < 30 or train_cls['高設定フラグ'].sum() < 5:
            continue
        
        X_train = train_cls[feat_cols].replace([np.inf, -np.inf], 0).fillna(0)
        y_train = train_cls['高設定フラグ']
        
        train_reg = df_feat[df_feat['日付'].isin(train_dates)]
        X_train_reg = train_reg[feat_cols].replace([np.inf, -np.inf], 0).fillna(0)
        y_train_reg = train_reg['最終差枚']
        overall_avg = float(y_train_reg.mean())
        
        if eval_idx - last_train_idx >= retrain_interval or trained_models is None:
            trained_models = []
            for factory in model_factories_fn(spw):
                m = factory
                m.fit(X_train, y_train)
                trained_models.append(m)
            
            trained_reg_model = reg_factory_fn()
            trained_reg_model.fit(X_train_reg, y_train_reg)
            
            n_splits = min(3, int(y_train.sum()), int(len(y_train) - y_train.sum()))
            if n_splits < 2:
                n_splits = 2
            tscv = TimeSeriesSplit(n_splits=n_splits)
            oof_probs = np.zeros(len(X_train))
            oof_count = np.zeros(len(X_train))
            for m_template in model_factories_fn(spw):
                for tr_idx, val_idx in tscv.split(X_train):
                    m_cv = m_template.__class__(**m_template.get_params())
                    m_cv.fit(X_train.iloc[tr_idx], y_train.iloc[tr_idx])
                    oof_probs[val_idx] += m_cv.predict_proba(X_train.iloc[val_idx])[:, 1]
                    oof_count[val_idx] += 1
            valid_mask = oof_count > 0
            if valid_mask.sum() > 10:
                oof_probs[valid_mask] /= oof_count[valid_mask]
                trained_threshold, _ = optimize_threshold_by_profit(
                    oof_probs[valid_mask],
                    y_train.values[valid_mask],
                    train_cls['最終差枚'].values[valid_mask]
                )
            last_train_idx = eval_idx
        
        X_eval = eval_df[feat_cols].replace([np.inf, -np.inf], 0).fillna(0)
        preds = np.zeros(len(X_eval))
        for m in trained_models:
            preds += m.predict_proba(X_eval)[:, 1]
        preds /= len(trained_models)
        
        eval_df = eval_df.copy()
        eval_df['pred_prob'] = preds
        
        pred_diffs = trained_reg_model.predict(X_eval)
        eval_df['adjusted_diff'] = preds * pred_diffs + (1 - preds) * overall_avg
        
        candidates = eval_df[eval_df['pred_prob'] >= trained_threshold]
        avg_profit = float(eval_df['最終差枚'].mean())
        
        if len(candidates) == 0:
            # 閾値超えがなくてもTop-Nを選択（バックテスト用：モデルの順位付け能力を評価）
            # 回帰モデルの期待差枚順でフォールバック
            candidates = eval_df.nlargest(top_n, 'adjusted_diff')
        
        # 候補の中から期待差枚が最も高いTop-Nを選択
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
