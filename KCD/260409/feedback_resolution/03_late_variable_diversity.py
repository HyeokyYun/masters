"""피드백 3 — 마지막 구간 추정 변수의 다양화.

지난 미팅 피드백: "마지막 구간에서 측정하는 추정 변수(기울기, 평균 등)를 여러 개로".

분석:
1. 마지막 10주(w21-30)에서 측정하는 변수를 {slope, mean, vol, std, nc_rate, customer_mean}로 확장
2. 각 변수가 outcome을 단변수로 얼마나 예측하는지 (LightGBM 5-fold CV)
3. 누적 추가의 marginal gain (slope → +mean → +vol → +nc)
4. 모든 변수를 동시에 넣었을 때의 feature importance 순위
"""
from __future__ import annotations

import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from common import (OUT_DIR, extract_segmented_features,
                    load_panel_with_labels, merge_label, run_cv)

WINDOW = 30
SEG_LEN = 10

LATE_VARS = [
    "late_sales_slope",
    "late_sales_mean",
    "late_sales_vol",
    "late_sales_std",
    "late_nc_rate",
    "late_customer_mean",
]


def main():
    print("[03] Loading panel + labels ...")
    panel, feats_labeled = load_panel_with_labels()

    print(f"[03] Extracting segmented features (window={WINDOW}, seg_len={SEG_LEN}) ...")
    feats = extract_segmented_features(panel, weeks=WINDOW, seg_len=SEG_LEN)
    merged = merge_label(feats, feats_labeled)
    print(f"  n stores = {len(merged):,}")

    y = merged["y"].astype(int).to_numpy()

    # 1) 단변수 예측력
    print("\n[03] (1) 단변수 예측력")
    uni_rows = []
    for v in LATE_VARS:
        X = merged[[v]].to_numpy(dtype=float)
        X = np.nan_to_num(X)
        m = run_cv(X, y)
        m["variable"] = v
        uni_rows.append(m)
        print(f"  {v}: F1={m['macro_f1_mean']:.4f}, AUC={m['auc_ovr_mean']:.4f}")
    uni_df = pd.DataFrame(uni_rows)
    uni_df = uni_df[["variable", "macro_f1_mean", "macro_f1_std",
                     "recall_Decline_mean", "recall_Stable_mean", "recall_Growth_mean", "auc_ovr_mean"]]
    uni_df = uni_df.sort_values("macro_f1_mean", ascending=False).reset_index(drop=True)
    uni_df.to_csv(OUT_DIR / "03_univariate_predictive_power.csv", index=False)

    # 2) 누적 추가 (greedy by univariate F1 ranking)
    print("\n[03] (2) 변수 누적 추가의 marginal gain")
    ordered_vars = uni_df["variable"].tolist()
    cum_rows = []
    for k in range(1, len(ordered_vars) + 1):
        cols = ordered_vars[:k]
        X = merged[cols].to_numpy(dtype=float)
        X = np.nan_to_num(X)
        m = run_cv(X, y)
        m["k_features"] = k
        m["features"] = ", ".join(cols)
        cum_rows.append(m)
        print(f"  +{ordered_vars[k-1]} (k={k}): F1={m['macro_f1_mean']:.4f}, AUC={m['auc_ovr_mean']:.4f}")
    cum_df = pd.DataFrame(cum_rows)
    cum_df = cum_df[["k_features", "features", "macro_f1_mean", "macro_f1_std",
                     "recall_Decline_mean", "recall_Stable_mean", "recall_Growth_mean", "auc_ovr_mean"]]
    cum_df.to_csv(OUT_DIR / "03_cumulative_addition.csv", index=False)

    # 3) Feature importance (모든 변수 동시 입력)
    print("\n[03] (3) 전체 변수 동시 입력 시 feature importance")
    X = merged[LATE_VARS].to_numpy(dtype=float)
    X = np.nan_to_num(X)
    model = lgb.LGBMClassifier(n_estimators=200, num_leaves=31, learning_rate=0.05,
                                min_child_samples=50, random_state=42, n_jobs=-1, verbose=-1)
    model.fit(X, y)
    imp = pd.DataFrame({"feature": LATE_VARS, "importance": model.feature_importances_})
    imp = imp.sort_values("importance", ascending=False).reset_index(drop=True)
    imp.to_csv(OUT_DIR / "03_feature_importance.csv", index=False)
    print(imp.to_string(index=False))

    # 4) 단변수 vs 전체 비교 요약
    full_metric = run_cv(X, y)
    print(f"\n[03] (4) 전체 6변수 동시: F1={full_metric['macro_f1_mean']:.4f}, AUC={full_metric['auc_ovr_mean']:.4f}")

    summary = {
        "window_weeks": WINDOW,
        "segment_length": SEG_LEN,
        "n_stores": int(len(merged)),
        "univariate_ranking_by_f1": uni_df.to_dict(orient="records"),
        "best_univariate": str(uni_df.iloc[0]["variable"]),
        "best_univariate_f1": float(uni_df.iloc[0]["macro_f1_mean"]),
        "all_six_combined_f1": float(full_metric["macro_f1_mean"]),
        "feature_importance_top": imp.to_dict(orient="records"),
    }
    with open(OUT_DIR / "03_late_variable_diversity_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=float)
    print(f"\n[03] 최고 단변수: {summary['best_univariate']} (F1={summary['best_univariate_f1']:.4f})")
    print(f"[03] 6변수 동시: F1={summary['all_six_combined_f1']:.4f}")


if __name__ == "__main__":
    main()
