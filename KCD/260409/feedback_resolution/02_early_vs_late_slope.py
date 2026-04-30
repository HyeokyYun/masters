"""피드백 2 — 초기 10주 vs 마지막 10주 기울기 비교.

지난 미팅 피드백: "초기 10주, 마지막 10주 기울기 비교".

분석:
1. 30주 window를 (early 10주: w1-10, late 10주: w21-30)으로 분할
2. 각 segment의 sales 기울기 산출
3. Outcome (Growth/Stable/Decline)별 분포 비교 (mean, std, t-test)
4. early·late 두 기울기의 점포 단위 Pearson 상관
5. 두 기울기가 단독으로 outcome을 얼마나 예측하는지 (단변수 LightGBM)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from common import (OUT_DIR, OUTCOME_TO_INT, extract_segmented_features,
                    load_panel_with_labels, merge_label, run_cv)

WINDOW = 30
SEG_LEN = 10


def main():
    print("[02] Loading panel + labels ...")
    panel, feats_labeled = load_panel_with_labels()

    print(f"[02] Extracting segmented features (window={WINDOW}, seg_len={SEG_LEN}) ...")
    feats = extract_segmented_features(panel, weeks=WINDOW, seg_len=SEG_LEN)
    merged = merge_label(feats, feats_labeled)
    print(f"  n stores = {len(merged):,}")

    # 1) Outcome별 early/late slope 분포
    print("\n[02] (1) Outcome별 기울기 분포")
    dist_rows = []
    for outcome in ("Decline", "Stable", "Growth"):
        sub = merged[merged["outcome_3"] == outcome]
        dist_rows.append({
            "outcome": outcome, "n": len(sub),
            "early_slope_mean": sub["early_sales_slope"].mean(),
            "early_slope_std": sub["early_sales_slope"].std(),
            "early_slope_median": sub["early_sales_slope"].median(),
            "late_slope_mean": sub["late_sales_slope"].mean(),
            "late_slope_std": sub["late_sales_slope"].std(),
            "late_slope_median": sub["late_sales_slope"].median(),
        })
    dist_df = pd.DataFrame(dist_rows)
    print(dist_df.to_string(index=False))
    dist_df.to_csv(OUT_DIR / "02_slope_distribution_by_outcome.csv", index=False)

    # 2) Outcome간 t-test (Growth vs Decline)
    print("\n[02] (2) Outcome간 차이 t-test (Growth vs Decline)")
    g = merged[merged["outcome_3"] == "Growth"]
    d = merged[merged["outcome_3"] == "Decline"]
    t_e, p_e = stats.ttest_ind(g["early_sales_slope"], d["early_sales_slope"], equal_var=False)
    t_l, p_l = stats.ttest_ind(g["late_sales_slope"], d["late_sales_slope"], equal_var=False)
    test_rows = [
        {"variable": "early_slope", "t": t_e, "p": p_e},
        {"variable": "late_slope", "t": t_l, "p": p_l},
    ]
    test_df = pd.DataFrame(test_rows)
    print(test_df.to_string(index=False))
    test_df.to_csv(OUT_DIR / "02_slope_ttest_growth_vs_decline.csv", index=False)

    # 3) Early-Late slope 점포 단위 상관
    print("\n[02] (3) early/late slope 점포 단위 Pearson 상관")
    pearson_overall = merged[["early_sales_slope", "late_sales_slope"]].corr().iloc[0, 1]
    print(f"  전체: r = {pearson_overall:.4f}")
    corr_rows = [{"outcome": "All", "n": len(merged), "pearson_r": pearson_overall}]
    for outcome in ("Decline", "Stable", "Growth"):
        sub = merged[merged["outcome_3"] == outcome]
        r = sub[["early_sales_slope", "late_sales_slope"]].corr().iloc[0, 1]
        print(f"  {outcome}: r = {r:.4f}")
        corr_rows.append({"outcome": outcome, "n": len(sub), "pearson_r": r})
    corr_df = pd.DataFrame(corr_rows)
    corr_df.to_csv(OUT_DIR / "02_slope_correlation_by_outcome.csv", index=False)

    # 4) 단변수 예측력 비교 (LightGBM)
    print("\n[02] (4) 단변수 예측력 비교 (LightGBM 5-fold CV)")
    y = merged["y"].astype(int).to_numpy()
    cases = [
        ("early_slope_only", ["early_sales_slope"]),
        ("late_slope_only", ["late_sales_slope"]),
        ("both_slopes", ["early_sales_slope", "late_sales_slope"]),
    ]
    perf_rows = []
    for name, cols in cases:
        X = merged[cols].to_numpy(dtype=float)
        X = np.nan_to_num(X)
        m = run_cv(X, y)
        m["case"] = name
        m["n_features"] = len(cols)
        perf_rows.append(m)
        print(f"  {name}: F1={m['macro_f1_mean']:.4f}, AUC={m['auc_ovr_mean']:.4f}")
    perf_df = pd.DataFrame(perf_rows)
    perf_df = perf_df[["case", "n_features", "macro_f1_mean", "macro_f1_std",
                       "recall_Decline_mean", "recall_Stable_mean", "recall_Growth_mean", "auc_ovr_mean"]]
    perf_df.to_csv(OUT_DIR / "02_slope_predictive_power.csv", index=False)

    # 요약
    summary = {
        "window_weeks": WINDOW,
        "segment_length": SEG_LEN,
        "n_stores": int(len(merged)),
        "early_slope_growth_minus_decline_mean": float(g["early_sales_slope"].mean() - d["early_sales_slope"].mean()),
        "late_slope_growth_minus_decline_mean": float(g["late_sales_slope"].mean() - d["late_sales_slope"].mean()),
        "early_late_pearson_overall": float(pearson_overall),
        "best_predictor": str(perf_df.loc[perf_df["macro_f1_mean"].idxmax(), "case"]),
        "best_predictor_f1": float(perf_df["macro_f1_mean"].max()),
    }
    with open(OUT_DIR / "02_early_vs_late_slope_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=float)
    print(f"\n[02] 요약: {json.dumps(summary, indent=2, default=float)}")


if __name__ == "__main__":
    main()
