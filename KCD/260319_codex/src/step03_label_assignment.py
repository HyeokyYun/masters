from __future__ import annotations

import pandas as pd

from src import config as cfg


def _direction_label(slope: float) -> str:
    return "U" if pd.notna(slope) and slope >= cfg.SLOPE_EPSILON else "D"


def _pattern_label(change_rate: float) -> str:
    if pd.isna(change_rate):
        return "Y"
    if change_rate >= cfg.PATTERN_GROWTH_THRESHOLD:
        return "X"
    if change_rate <= -cfg.PATTERN_GROWTH_THRESHOLD:
        return "Z"
    return "Y"


def assign_labels(features: pd.DataFrame) -> pd.DataFrame:
    labeled = features.copy()
    labeled["P1_label"] = labeled["slope_early_mm"].apply(_direction_label)
    labeled["P2_label"] = labeled["slope_late_mm"].apply(_direction_label)
    labeled["Pattern_label"] = labeled["overall_change_rate"].apply(_pattern_label)
    labeled["final_code"] = (
        labeled["P1_label"] + labeled["P2_label"] + labeled["Pattern_label"]
    )
    labeled["life_cycle_category"] = labeled["Pattern_label"].map(cfg.LIFE_CYCLE_MAP)

    labeled_path = cfg.TABLE_DIR / "store_features_labeled.csv"
    labeled.to_csv(labeled_path, index=False, encoding="utf-8-sig")

    pattern_dist = (
        labeled["Pattern_label"]
        .value_counts()
        .rename_axis("Pattern_label")
        .reset_index(name="store_count")
        .sort_values("Pattern_label")
    )
    pattern_path = cfg.TABLE_DIR / "pattern_distribution.csv"
    pattern_dist.to_csv(pattern_path, index=False, encoding="utf-8-sig")

    code_dist = (
        labeled["final_code"]
        .value_counts()
        .rename_axis("final_code")
        .reset_index(name="store_count")
    )
    code_path = cfg.TABLE_DIR / "final_code_distribution.csv"
    code_dist.to_csv(code_path, index=False, encoding="utf-8-sig")

    summary_cols = [
        "slope_early_mm",
        "slope_late_mm",
        "slope_all_mm",
        "trend_slope",
        "overall_change_rate",
        "start_mean_mm",
        "end_mean_mm",
        "cv",
        "mdd",
        "nc_rate",
        "n_weeks",
    ]
    available = [col for col in summary_cols if col in labeled.columns]
    code_means = labeled.groupby("final_code")[available].mean().round(6)
    means_path = cfg.TABLE_DIR / "final_code_feature_means.csv"
    code_means.to_csv(means_path, encoding="utf-8-sig")

    print(f"[Step03] 저장 → {labeled_path.name}")
    print(f"[Step03] 저장 → {pattern_path.name}")
    print(f"[Step03] 저장 → {code_path.name}")
    print(f"[Step03] 저장 → {means_path.name}")

    print("\n[Step03] Pattern 분포:")
    for _, row in pattern_dist.iterrows():
        print(f"  {row['Pattern_label']}: {int(row['store_count']):,}")

    print("\n[Step03] 상위 final_code:")
    for _, row in code_dist.head(10).iterrows():
        print(f"  {row['final_code']}: {int(row['store_count']):,}")

    return labeled
