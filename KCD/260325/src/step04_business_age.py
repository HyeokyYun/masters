from __future__ import annotations

import numpy as np
import pandas as pd

from src import config as cfg
from src.model_utils import fit_binary_logit


def _build_age_outputs(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["age_bucket"] = pd.cut(
        out["business_age_months"],
        bins=cfg.AGE_BUCKET_BINS,
        labels=cfg.AGE_BUCKET_LABELS,
        right=True,
        include_lowest=True,
    )
    out["is_growth"] = (out["outcome_3"] == "Growth").astype(int)
    out["is_early_store"] = (out["business_age_months"] <= cfg.EARLY_STORE_MONTHS).astype(int)
    return out


def _save_age_summaries(df: pd.DataFrame) -> None:
    age_bucket_summary = (
        df.groupby(["age_bucket", "outcome_3"], observed=False)
        .size()
        .rename("store_count")
        .reset_index()
        .sort_values(["age_bucket", "outcome_3"])
    )
    age_bucket_summary.to_csv(cfg.TABLE_DIR / "business_age_bucket_summary.csv", index=False, encoding="utf-8-sig")

    early_summary = (
        df[df["is_early_store"] == 1]
        .groupby("outcome_3")
        .agg(
            stores=("public_id", "count"),
            mean_nc_rate=("nc_rate", "mean"),
            mean_preferred_volatility=("preferred_volatility", "mean"),
            mean_competition_index=("competition_index", "mean"),
            mean_delivery_link=("delivery_link", "mean"),
        )
        .reset_index()
    )
    early_summary.to_csv(cfg.TABLE_DIR / "young_store_outcome_summary.csv", index=False, encoding="utf-8-sig")

    compare = (
        df[df["is_early_store"] == 1]
        .groupby("is_growth")
        .agg(
            stores=("public_id", "count"),
            nc_rate_mean=("nc_rate", "mean"),
            preferred_volatility_mean=("preferred_volatility", "mean"),
            competition_index_mean=("competition_index", "mean"),
            delivery_link_mean=("delivery_link", "mean"),
            fastfood_share=("is_fastfood", "mean"),
            cafe_share=("is_cafe", "mean"),
            pub_share=("is_pub", "mean"),
        )
        .reset_index()
    )
    compare.to_csv(cfg.TABLE_DIR / "young_store_growth_vs_others.csv", index=False, encoding="utf-8-sig")

    category_summary = (
        df[df["is_early_store"] == 1]
        .groupby(["category", "is_growth"])
        .size()
        .rename("store_count")
        .reset_index()
        .sort_values(["category", "is_growth"])
    )
    category_summary.to_csv(cfg.TABLE_DIR / "young_store_category_summary.csv", index=False, encoding="utf-8-sig")


def _run_early_store_model(df: pd.DataFrame) -> None:
    early_df = df[df["is_early_store"] == 1].copy()
    if len(early_df) < 200:
        return

    category_dummies = pd.get_dummies(early_df["category"], prefix="cat", drop_first=True, dtype=float)
    early_df = pd.concat([early_df, category_dummies], axis=1)

    predictors = [
        "nc_rate",
        "preferred_volatility",
        "competition_index",
        "delivery_link",
        "business_square_size",
        "mdd",
        "trend_slope",
        "seasonal_strength",
        "fastfood_x_competition",
        "cafe_x_competition",
        "pub_x_competition",
    ] + list(category_dummies.columns)

    fit_binary_logit(early_df, "is_growth", predictors, "young_store_growth_logit")


def _plot_age(df: pd.DataFrame) -> None:
    cfg.set_korean_font()
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(15, 5))

    axes[0].hist(df["business_age_months"].dropna(), bins=30, color="#2a6f97", edgecolor="white")
    axes[0].axvline(cfg.EARLY_STORE_MONTHS, color="red", linestyle="--", label="초기 업장 기준 12개월")
    axes[0].set_title("업력 분포")
    axes[0].set_xlabel("Business age (months)")
    axes[0].legend()

    pivot = (
        pd.crosstab(df["age_bucket"], df["outcome_3"], normalize="index")
        .reindex(cfg.AGE_BUCKET_LABELS)
        .fillna(0)
    )
    pivot.plot(kind="bar", stacked=True, ax=axes[1], color=["#74a57f", "#2a6f97", "#cc5a71"])
    axes[1].set_title("업력 구간별 Outcome 비중")
    axes[1].set_xlabel("Age bucket")
    axes[1].set_ylabel("Share")
    axes[1].tick_params(axis="x", rotation=0)

    plt.tight_layout()
    plt.savefig(cfg.FIGURE_DIR / "business_age_overview.png", dpi=150)
    plt.close(fig)


def run_business_age_analysis(df: pd.DataFrame) -> pd.DataFrame:
    age_df = _build_age_outputs(df)
    _save_age_summaries(age_df)
    _run_early_store_model(age_df)
    _plot_age(age_df)
    age_df.to_csv(cfg.TABLE_DIR / "business_age_analysis_table.csv", index=False, encoding="utf-8-sig")
    return age_df
