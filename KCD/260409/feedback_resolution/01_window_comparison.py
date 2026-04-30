"""피드백 1 — 초기 예측 기간(window 길이) 비교.

window ∈ {10, 20, 30, 40, 50}주에서 동일 feature·동일 모델로 5-fold CV 비교.
지난 미팅에서 받은 "예측 기간을 자르는 비교" 피드백에 답하는 분석.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from common import (OUT_DIR, extract_window_features, load_panel_with_labels,
                    merge_label, run_cv)


def main():
    print("[01] Loading panel + labels ...")
    panel, feats_labeled = load_panel_with_labels()
    print(f"  panel rows: {len(panel):,}, labeled stores: {len(feats_labeled):,}")

    windows = [10, 20, 30, 40, 50]
    results = []

    feature_cols_template = None  # 각 window마다 동일한 feature set 사용

    for w in windows:
        t0 = time.time()
        print(f"\n[01] window = {w} weeks")
        feats = extract_window_features(panel, weeks=w)
        merged = merge_label(feats, feats_labeled)

        # 사용할 feature
        feat_cols = [c for c in merged.columns if c not in ("public_id", "outcome_3", "y")]
        if feature_cols_template is None:
            feature_cols_template = feat_cols
        X = merged[feat_cols].to_numpy(dtype=float)
        X = np.nan_to_num(X)
        y = merged["y"].astype(int).to_numpy()

        metrics = run_cv(X, y)
        metrics.update({"window_weeks": w, "n_stores": int(len(merged)), "elapsed_sec": round(time.time() - t0, 1)})
        results.append(metrics)
        print(f"  n={len(merged):,}, macro F1 = {metrics['macro_f1_mean']:.4f}, "
              f"AUC = {metrics['auc_ovr_mean']:.4f}, elapsed = {metrics['elapsed_sec']}s")

    df = pd.DataFrame(results)
    cols = ["window_weeks", "n_stores", "macro_f1_mean", "macro_f1_std",
            "recall_Decline_mean", "recall_Stable_mean", "recall_Growth_mean",
            "auc_ovr_mean", "elapsed_sec"]
    df = df[cols]

    csv_path = OUT_DIR / "01_window_comparison.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n[01] Saved: {csv_path}")
    print("\n=== Summary ===")
    print(df.to_string(index=False))

    summary = {
        "windows": windows,
        "best_window_by_f1": int(df.loc[df["macro_f1_mean"].idxmax(), "window_weeks"]),
        "f1_at_30w": float(df.loc[df["window_weeks"] == 30, "macro_f1_mean"].iloc[0]),
        "feature_set_used": feature_cols_template,
    }
    with open(OUT_DIR / "01_window_comparison_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"[01] Best window by F1: {summary['best_window_by_f1']} weeks")


if __name__ == "__main__":
    main()
