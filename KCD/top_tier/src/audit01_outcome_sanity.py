"""Audit 01 — Outcome_3 definition의 편향 검증.

확인 항목:
  (a) outcome_3의 실제 정의 이해: slope_all_mm 기반
  (b) 초기 30주 총매출 사분위별 outcome_3 분포 — 저매출 점포에 Growth 쏠려 있는가?
  (c) 초기 30주 slope와 slope_all_mm의 상관 — prediction task의 trivial-ness 검증
  (d) slope_all_mm threshold 값 보고
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg  # noqa: E402


def main():
    feats = pd.read_csv(cfg.FEATURES_PATH)
    feats["public_id"] = feats["public_id"].astype(str)
    print(f"[audit01] labeled features: {feats.shape}, columns include slope_*_mm, cv, outcome_3")
    print(f"[audit01] outcome_3 distribution:\n{feats['outcome_3'].value_counts(dropna=False)}")
    print()

    sa_std = feats["slope_all_mm"].std()
    print(f"[audit01] slope_all_mm std = {sa_std:.5f}")
    print(f"[audit01] slope_all_mm mean = {feats['slope_all_mm'].mean():.5f}")

    panel = pd.read_parquet(cfg.PANEL_PATH)
    panel["public_id"] = panel["public_id"].astype(str)
    panel_30 = panel[panel["observed_week_idx"] < cfg.PREDICTION_WEEKS]

    init_sales = panel_30.groupby("public_id")["sales_card"].sum().rename("total_sales_1_30w")
    merged = feats.merge(init_sales.reset_index(), on="public_id", how="inner")
    merged = merged.dropna(subset=["outcome_3", "total_sales_1_30w"])
    print(f"[audit01] merged: {len(merged):,} stores with both outcome + init_sales")

    merged["init_sales_quartile"] = pd.qcut(merged["total_sales_1_30w"], q=4,
                                             labels=["Q1_low", "Q2", "Q3", "Q4_high"])

    ct = pd.crosstab(merged["init_sales_quartile"], merged["outcome_3"], normalize="index")
    ct_count = pd.crosstab(merged["init_sales_quartile"], merged["outcome_3"])
    print("\n=== (a) 초기 30주 총매출 사분위 × outcome_3 (row %, 비율) ===")
    print(ct.round(3).to_string())
    print("\n=== (a) 절대 개수 ===")
    print(ct_count.to_string())

    baseline = merged["outcome_3"].value_counts(normalize=True).sort_index()
    print("\n=== (a) Baseline outcome_3 비율 (전체) ===")
    print(baseline.round(3).to_string())

    print("\n=== (a) 사분위 - baseline 차이 (percentage point) ===")
    diff = (ct - baseline) * 100
    print(diff.round(2).to_string())

    corr = merged[["slope_early_mm", "slope_all_mm", "slope_late_mm"]].corr()
    print("\n=== (c) slope feature 상관 행렬 ===")
    print(corr.round(3).to_string())

    print("\n=== (c) slope_early의 outcome_3 예측력 (signal-only baseline) ===")
    for q, sub in merged.groupby(pd.qcut(merged["slope_early_mm"], q=5)):
        dist = sub["outcome_3"].value_counts(normalize=True).reindex(
            ["Growth", "Stable", "Decline"], fill_value=0)
        print(f"  slope_early {q}: Growth={dist['Growth']:.3f} Stable={dist['Stable']:.3f} Decline={dist['Decline']:.3f}  n={len(sub):,}")

    audit_out = cfg.TABLE_DIR / "audit01_outcome_sanity.csv"
    ct.to_csv(audit_out, encoding="utf-8-sig")
    print(f"\n[audit01] saved cross-tab to {audit_out}")


if __name__ == "__main__":
    main()
