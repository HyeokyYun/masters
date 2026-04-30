from __future__ import annotations

import pandas as pd

from src import config as cfg
from src.model_utils import fit_outcome_mnlogit


def _save_nc_summaries(df: pd.DataFrame) -> None:
    by_outcome = (
        df.groupby("outcome_3")
        .agg(
            stores=("public_id", "count"),
            nc_rate_mean=("nc_rate", "mean"),
            nc_rate_median=("nc_rate", "median"),
            preferred_volatility_mean=("preferred_volatility", "mean"),
            business_age_months_mean=("business_age_months", "mean"),
        )
        .reset_index()
    )
    by_outcome.to_csv(cfg.TABLE_DIR / "new_customer_outcome_summary.csv", index=False, encoding="utf-8-sig")

    by_category = (
        df.groupby("category")
        .agg(
            stores=("public_id", "count"),
            nc_rate_mean=("nc_rate", "mean"),
            growth_share=("is_growth", "mean"),
        )
        .reset_index()
        .sort_values("growth_share", ascending=False)
    )
    by_category.to_csv(cfg.TABLE_DIR / "new_customer_category_summary.csv", index=False, encoding="utf-8-sig")

    by_age = (
        df.groupby("age_bucket", observed=False)
        .agg(
            stores=("public_id", "count"),
            nc_rate_mean=("nc_rate", "mean"),
            growth_share=("is_growth", "mean"),
        )
        .reset_index()
    )
    by_age.to_csv(cfg.TABLE_DIR / "new_customer_age_bucket_summary.csv", index=False, encoding="utf-8-sig")

    quantile_df = df.copy()
    quantile_df["nc_rate_quintile"] = pd.qcut(
        quantile_df["nc_rate"].rank(method="first"),
        5,
        labels=["Q1_low", "Q2", "Q3", "Q4", "Q5_high"],
    )
    quantile_summary = (
        quantile_df.groupby("nc_rate_quintile", observed=False)
        .agg(
            stores=("public_id", "count"),
            mean_nc_rate=("nc_rate", "mean"),
            growth_share=("is_growth", "mean"),
            decline_share=("outcome_3", lambda x: (x == "Decline").mean()),
        )
        .reset_index()
    )
    quantile_summary.to_csv(cfg.TABLE_DIR / "new_customer_quantile_summary.csv", index=False, encoding="utf-8-sig")


def _run_nc_models(df: pd.DataFrame) -> None:
    category_dummies = pd.get_dummies(df["category"], prefix="cat", drop_first=True, dtype=float)
    model_df = pd.concat([df.copy(), category_dummies], axis=1)

    without_nc = [
        "preferred_volatility",
        "competition_index",
        "business_age_months",
        "delivery_link",
        "mdd",
        "trend_slope",
        "seasonal_strength",
        "fastfood_x_competition",
        "cafe_x_competition",
        "pub_x_competition",
    ] + list(category_dummies.columns)

    with_nc = ["nc_rate"] + without_nc

    fit_a = fit_outcome_mnlogit(model_df, without_nc, "outcome3_without_new_customer")
    fit_b = fit_outcome_mnlogit(model_df, with_nc, "outcome3_with_new_customer")
    pd.concat([fit_a, fit_b], ignore_index=True).to_csv(
        cfg.TABLE_DIR / "new_customer_model_fit_comparison.csv",
        index=False,
        encoding="utf-8-sig",
    )


def _plot_nc(df: pd.DataFrame) -> None:
    cfg.set_korean_font()
    import matplotlib.pyplot as plt

    quantile_summary = pd.read_csv(cfg.TABLE_DIR / "new_customer_quantile_summary.csv")
    outcome_summary = pd.read_csv(cfg.TABLE_DIR / "new_customer_outcome_summary.csv")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].bar(quantile_summary["nc_rate_quintile"], quantile_summary["growth_share"], color="#2a6f97")
    axes[0].set_title("신규고객 비율 분위별 Growth 비중")
    axes[0].set_xlabel("NC-rate quintile")
    axes[0].set_ylabel("Growth share")

    axes[1].bar(outcome_summary["outcome_3"], outcome_summary["nc_rate_mean"], color="#cc5a71")
    axes[1].set_title("Outcome별 평균 신규고객 비율")
    axes[1].set_xlabel("Outcome")
    axes[1].set_ylabel("Mean nc_rate")

    plt.tight_layout()
    plt.savefig(cfg.FIGURE_DIR / "new_customer_overview.png", dpi=150)
    plt.close(fig)


def run_new_customer_analysis(df: pd.DataFrame) -> None:
    work = df.copy()
    work["is_growth"] = (work["outcome_3"] == "Growth").astype(int)
    _save_nc_summaries(work)
    _run_nc_models(work)
    _plot_nc(work)
