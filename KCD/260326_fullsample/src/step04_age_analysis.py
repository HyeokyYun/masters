from __future__ import annotations

import pandas as pd

from src import config as cfg
from src.model_utils import fit_outcome_mnlogit


def run_fullsample_age_analysis(labeled: pd.DataFrame) -> pd.DataFrame:
    labeled = labeled.copy()
    for column in ("open_date", "first_observed_date", "last_observed_date"):
        if column in labeled.columns:
            labeled[column] = pd.to_datetime(labeled[column], errors="coerce")

    meta = pd.read_csv(cfg.META_CSV)
    meta["public_id"] = meta["public_id"].astype(str)
    meta["open_date"] = pd.to_datetime(meta["open_month"].astype(str), format="%Y-%m", errors="coerce")
    meta["category_from_meta"] = meta["classification__kcd_v3__depth_2_name"].apply(cfg.classify_industry)

    diagnostics = pd.read_csv(cfg.TABLE_DIR / "observed_window_panel_diagnostics.csv")
    ref_date = pd.to_datetime(diagnostics.loc[diagnostics["item"] == "reference_date", "value"].iloc[0])

    keep = [
        "public_id",
        "open_date",
        "delivery_link",
        "business_square_size",
        "dong",
        "category_from_meta",
    ]
    merged = labeled.merge(meta[keep], on="public_id", how="left", suffixes=("_labeled", "_meta"))
    if "open_date_labeled" in merged.columns:
        merged["open_date"] = pd.to_datetime(merged["open_date_labeled"], errors="coerce")
        if "open_date_meta" in merged.columns:
            merged["open_date"] = merged["open_date"].fillna(pd.to_datetime(merged["open_date_meta"], errors="coerce"))
    elif "open_date_meta" in merged.columns:
        merged["open_date"] = pd.to_datetime(merged["open_date_meta"], errors="coerce")

    if "category_labeled" in merged.columns:
        merged["category"] = merged["category_labeled"]
    elif "category" not in merged.columns:
        merged["category"] = pd.NA
    merged["category"] = merged["category"].fillna(merged.get("category_from_meta")).fillna("기타")
    merged["full_business_age_months"] = (
        (ref_date.year - merged["open_date"].dt.year) * 12
        + (ref_date.month - merged["open_date"].dt.month)
    )
    merged["age_at_first_obs_months"] = (
        (merged["first_observed_date"].dt.year - merged["open_date"].dt.year) * 12
        + (merged["first_observed_date"].dt.month - merged["open_date"].dt.month)
    )
    merged["full_age_bucket"] = pd.cut(
        merged["full_business_age_months"],
        bins=cfg.FULL_AGE_BUCKET_BINS,
        labels=cfg.FULL_AGE_BUCKET_LABELS,
        right=True,
        include_lowest=True,
    )
    merged["delivery_link"] = pd.to_numeric(merged["delivery_link"], errors="coerce").fillna(0)
    merged["business_square_size"] = pd.to_numeric(merged["business_square_size"], errors="coerce")

    sample_summary = pd.DataFrame(
        [
            {"item": "labeled_store_count", "value": float(merged["public_id"].nunique())},
            {"item": "reference_date", "value": str(ref_date.date())},
            {"item": "median_full_business_age_months", "value": float(merged["full_business_age_months"].median())},
            {"item": "median_age_at_first_obs_months", "value": float(merged["age_at_first_obs_months"].median())},
        ]
    )
    sample_summary.to_csv(cfg.TABLE_DIR / "fullsample_age_diagnostics.csv", index=False, encoding="utf-8-sig")

    bucket_summary = (
        merged.groupby(["full_age_bucket", "outcome_3"], observed=False)
        .size()
        .rename("store_count")
        .reset_index()
    )
    bucket_summary.to_csv(cfg.TABLE_DIR / "fullsample_age_bucket_outcome_summary.csv", index=False, encoding="utf-8-sig")

    open_obs_gap = (
        merged.groupby("full_age_bucket", observed=False)
        .agg(
            stores=("public_id", "count"),
            mean_age_at_first_obs_months=("age_at_first_obs_months", "mean"),
            median_age_at_first_obs_months=("age_at_first_obs_months", "median"),
        )
        .reset_index()
    )
    open_obs_gap.to_csv(cfg.TABLE_DIR / "fullsample_age_observation_gap_summary.csv", index=False, encoding="utf-8-sig")

    category_summary = (
        merged.groupby(["category", "outcome_3"])
        .size()
        .rename("store_count")
        .reset_index()
        .sort_values(["category", "outcome_3"])
    )
    category_summary.to_csv(cfg.TABLE_DIR / "fullsample_category_outcome_summary.csv", index=False, encoding="utf-8-sig")

    base_predictors = [
        "full_business_age_months",
        "age_at_first_obs_months",
        "delivery_link",
        "business_square_size",
        "n_observed_weeks_used",
    ]
    fit_a = fit_outcome_mnlogit(merged, base_predictors, "fullsample_age_base")

    category_dummies = pd.get_dummies(merged["category"], prefix="cat", drop_first=True, dtype=float)
    model_df = pd.concat([merged, category_dummies], axis=1)
    fit_b = fit_outcome_mnlogit(model_df, base_predictors + list(category_dummies.columns), "fullsample_age_with_category")
    pd.concat([fit_a, fit_b], ignore_index=True).to_csv(
        cfg.TABLE_DIR / "fullsample_age_model_fit_comparison.csv",
        index=False,
        encoding="utf-8-sig",
    )

    cfg.set_korean_font()
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(15, 5))

    axes[0].hist(merged["full_business_age_months"].dropna(), bins=40, color="#2a6f97", edgecolor="white")
    axes[0].set_title("전체 업장 표본의 실제 업력 분포")
    axes[0].set_xlabel("Full business age (months)")
    axes[0].set_ylabel("Store count")

    pivot = (
        pd.crosstab(merged["full_age_bucket"], merged["outcome_3"], normalize="index")
        .reindex(cfg.FULL_AGE_BUCKET_LABELS)
        .fillna(0)
    )
    pivot.plot(kind="bar", stacked=True, ax=axes[1], color=["#74a57f", "#2a6f97", "#cc5a71"])
    axes[1].set_title("전체 업력 구간별 Growth/Stable/Decline 비중")
    axes[1].set_xlabel("Full-age bucket")
    axes[1].set_ylabel("Share")
    axes[1].tick_params(axis="x", rotation=0)

    plt.tight_layout()
    plt.savefig(cfg.FIGURE_DIR / "fullsample_age_overview.png", dpi=150)
    plt.close(fig)

    merged.to_csv(cfg.TABLE_DIR / "fullsample_age_analysis_table.csv", index=False, encoding="utf-8-sig")
    return merged
