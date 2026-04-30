from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src import config as cfg


def _save_mnlogit_outputs(result, categories: list[str], out_prefix: str) -> None:
    params = result.params.copy()
    pvalues = result.pvalues.copy()

    if isinstance(params, pd.Series):
        params = params.to_frame("coef")
        pvalues = pvalues.to_frame("pvalue")

    target_names = categories[1:]
    params.columns = [f"{name}_coef" for name in target_names]
    pvalues.columns = [f"{name}_pvalue" for name in target_names]
    table = pd.concat([params, pvalues], axis=1).reset_index().rename(columns={"index": "feature"})
    table.to_csv(cfg.TABLE_DIR / f"{out_prefix}_coefficients.csv", index=False, encoding="utf-8-sig")

    fit_summary = pd.DataFrame(
        [
            {
                "model_name": out_prefix,
                "nobs": float(result.nobs),
                "pseudo_r2": float(getattr(result, "prsquared", np.nan)),
                "llf": float(result.llf),
                "aic": float(result.aic),
            }
        ]
    )
    fit_summary.to_csv(cfg.TABLE_DIR / f"{out_prefix}_fit.csv", index=False, encoding="utf-8-sig")

    with open(cfg.DOC_DIR / f"{out_prefix}_summary.txt", "w", encoding="utf-8") as handle:
        handle.write(str(result.summary2()))


def _fit_multinomial(df: pd.DataFrame, predictors: list[str], out_prefix: str) -> None:
    work = df[["outcome_3"] + predictors].copy()

    for column in predictors:
        if work[column].dtype.kind in {"i", "u", "f", "b"}:
            median = work[column].median()
            work[column] = work[column].fillna(median)
            lower = work[column].quantile(0.01)
            upper = work[column].quantile(0.99)
            work[column] = work[column].clip(lower=lower, upper=upper)
            std = work[column].std()
            if pd.notna(std) and std > 1e-12:
                work[column] = (work[column] - work[column].mean()) / std
            else:
                work[column] = 0.0
        else:
            work[column] = work[column].fillna(0)

    categories = list(cfg.OUTCOME_ORDER)
    y = pd.Categorical(work["outcome_3"], categories=categories, ordered=True)
    work = work[y.codes >= 0].copy()
    y = pd.Categorical(work["outcome_3"], categories=categories, ordered=True)
    X = sm.add_constant(work[predictors].astype(float), has_constant="add")

    model = sm.MNLogit(y.codes, X)
    result = model.fit(method="lbfgs", maxiter=500, disp=False)
    _save_mnlogit_outputs(result, categories, out_prefix)


def run_followup_analysis(base_df: pd.DataFrame, volatility_df: pd.DataFrame) -> pd.DataFrame:
    merged = base_df.merge(volatility_df, on="public_id", how="left")
    merged["preferred_volatility"] = merged["vol_resid_stl13"].fillna(merged["vol_resid_rolling13"])
    merged["fastfood_x_local_share"] = merged["is_fastfood"] * merged["fastfood_share_in_dong"].fillna(0)
    merged["cafe_x_local_share"] = merged["is_cafe"] * merged["cafe_share_in_dong"].fillna(0)
    merged["pub_x_local_share"] = merged["is_pub"] * merged["pub_share_in_dong"].fillna(0)

    age_bucket_summary = (
        merged.groupby(["age_bucket", "outcome_3"])
        .size()
        .rename("store_count")
        .reset_index()
        .sort_values(["age_bucket", "outcome_3"])
    )
    age_bucket_summary.to_csv(cfg.TABLE_DIR / "business_age_bucket_summary.csv", index=False, encoding="utf-8-sig")

    owner_age_summary = (
        merged.groupby("outcome_3")
        .agg(
            owner_age_mean=("owner_age_numeric", "mean"),
            owner_age_median=("owner_age_numeric", "median"),
            owner_age_missing_rate=("owner_age_missing", "mean"),
        )
        .reset_index()
    )
    owner_age_summary.to_csv(cfg.TABLE_DIR / "owner_age_summary.csv", index=False, encoding="utf-8-sig")

    industry_competition_summary = (
        merged.groupby(["category", "outcome_3"])
        .agg(
            mean_same_category_share=("local_same_category_share", "mean"),
            mean_fastfood_share_in_dong=("fastfood_share_in_dong", "mean"),
            mean_store_count_in_dong=("dong_total_store_count", "mean"),
            n=("public_id", "count"),
        )
        .reset_index()
    )
    industry_competition_summary.to_csv(
        cfg.TABLE_DIR / "industry_competition_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )

    base_predictors = [
        "nc_rate",
        "preferred_volatility",
        "business_age_months",
        "delivery_link",
        "owner_age_numeric",
        "owner_age_missing",
        "business_square_size",
        "business_square_size_missing",
        "local_same_category_share",
        "fastfood_share_in_dong",
        "is_fastfood",
        "is_cafe",
        "is_pub",
    ]
    interaction_predictors = base_predictors + [
        "fastfood_x_local_share",
        "cafe_x_local_share",
        "pub_x_local_share",
    ]

    model_df = merged.dropna(subset=["outcome_3", "preferred_volatility"]).copy()
    _fit_multinomial(model_df, base_predictors, "mnlogit_outcome3_base")
    _fit_multinomial(model_df, interaction_predictors, "mnlogit_outcome3_interaction")

    early_df = model_df[model_df["business_age_months"] <= cfg.EARLY_STORE_MONTHS].copy()
    if len(early_df) >= 200:
        _fit_multinomial(early_df, interaction_predictors, "mnlogit_outcome3_early_store")

    try:
        cfg.configure_matplotlib()
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, 5))
        merged["business_age_months"].dropna().plot(kind="hist", bins=30, ax=ax, color="#2a6f97", edgecolor="white")
        ax.set_title("Business Age Distribution")
        ax.set_xlabel("Months since opening")
        ax.set_ylabel("Store count")
        plt.tight_layout()
        plt.savefig(cfg.FIGURE_DIR / "business_age_histogram.png", dpi=150)
        plt.close(fig)

        age_outcome = (
            age_bucket_summary.pivot(index="age_bucket", columns="outcome_3", values="store_count")
            .fillna(0)
            .reindex(cfg.AGE_BUCKET_LABELS)
        )
        fig, ax = plt.subplots(figsize=(8, 5))
        age_outcome.plot(kind="bar", stacked=True, ax=ax, color=["#74a57f", "#2a6f97", "#cc5a71"])
        ax.set_title("Outcome mix by business-age bucket")
        ax.set_xlabel("Business-age bucket")
        ax.set_ylabel("Store count")
        plt.tight_layout()
        plt.savefig(cfg.FIGURE_DIR / "business_age_bucket_outcomes.png", dpi=150)
        plt.close(fig)
    except Exception as exc:
        with open(cfg.DOC_DIR / "plotting_warning.txt", "w", encoding="utf-8") as handle:
            handle.write(f"Plot generation skipped due to: {exc}\n")

    merged.to_csv(cfg.TABLE_DIR / "followup_analysis_table.csv", index=False, encoding="utf-8-sig")
    return merged
