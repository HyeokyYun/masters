from __future__ import annotations

import pandas as pd

from src import config as cfg


def _overall_suffix(slope_all: float, threshold: float) -> str:
    if slope_all > threshold:
        return "_X"
    if slope_all < -threshold:
        return "_Z"
    return "_Y"


def assign_observed_window_labels(feat: pd.DataFrame) -> pd.DataFrame:
    labeled = feat.copy()
    sa_std = labeled["slope_all_mm"].std()
    threshold = sa_std * cfg.SLOPE_ALL_THRESHOLD_FACTOR

    labeled["label"] = labeled.apply(
        lambda row: (
            ("D" if row["slope_early_mm"] <= 0 else "U")
            + ("D" if row["slope_late_mm"] <= 0 else "U")
            + _overall_suffix(row["slope_all_mm"], threshold)
        ),
        axis=1,
    )
    labeled["outcome_3"] = labeled["label"].str[-1].map(cfg.OUTCOME_MAP)

    summary = labeled["label"].value_counts().reindex(cfg.LIFECYCLE_LABELS, fill_value=0).reset_index()
    summary.columns = ["label", "store_count"]
    summary["share"] = summary["store_count"] / summary["store_count"].sum()
    summary.to_csv(cfg.TABLE_DIR / "observed_window_label_summary.csv", index=False, encoding="utf-8-sig")

    outcome_summary = labeled["outcome_3"].value_counts().reindex(cfg.OUTCOME_ORDER, fill_value=0).reset_index()
    outcome_summary.columns = ["outcome_3", "store_count"]
    outcome_summary["share"] = outcome_summary["store_count"] / outcome_summary["store_count"].sum()
    outcome_summary.to_csv(cfg.TABLE_DIR / "observed_window_outcome3_summary.csv", index=False, encoding="utf-8-sig")

    labeled.to_csv(cfg.TABLE_DIR / "observed_window_features_labeled.csv", index=False, encoding="utf-8-sig")
    return labeled
