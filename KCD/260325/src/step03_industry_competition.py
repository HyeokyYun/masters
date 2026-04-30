from __future__ import annotations

import numpy as np
import pandas as pd

from src import config as cfg
from src.model_utils import fit_outcome_mnlogit


def _prepare_analysis_table(base_df: pd.DataFrame, volatility_df: pd.DataFrame) -> pd.DataFrame:
    vol_note = pd.read_csv(cfg.TABLE_DIR / "volatility_selection_note.csv")
    preferred_metric = vol_note.loc[vol_note["item"] == "preferred_metric", "value"].iloc[0]
    merged = base_df.merge(volatility_df[["public_id", preferred_metric]], on="public_id", how="left")
    merged = merged.rename(columns={preferred_metric: "preferred_volatility"})
    merged["preferred_volatility"] = merged["preferred_volatility"].fillna(merged["cv"])
    merged["competition_index"] = merged["local_same_category_share"].fillna(0)
    merged["competition_index_logit"] = np.log1p(merged["competition_index"])
    merged["fastfood_x_competition"] = merged["is_fastfood"] * merged["fastfood_share_in_dong"].fillna(0)
    merged["cafe_x_competition"] = merged["is_cafe"] * merged["cafe_share_in_dong"].fillna(0)
    merged["pub_x_competition"] = merged["is_pub"] * merged["pub_share_in_dong"].fillna(0)
    return merged


def _save_industry_summaries(df: pd.DataFrame) -> None:
    industry_summary = (
        df.groupby(["category", "outcome_3"])
        .agg(
            stores=("public_id", "count"),
            mean_nc_rate=("nc_rate", "mean"),
            mean_preferred_volatility=("preferred_volatility", "mean"),
            mean_competition_index=("competition_index", "mean"),
            mean_business_age_months=("business_age_months", "mean"),
        )
        .reset_index()
        .sort_values(["category", "outcome_3"])
    )
    industry_summary.to_csv(cfg.TABLE_DIR / "industry_outcome_summary.csv", index=False, encoding="utf-8-sig")

    pivot = (
        df.pivot_table(index="category", columns="outcome_3", values="public_id", aggfunc="count", fill_value=0)
        .reset_index()
    )
    growth = pivot["Growth"] if "Growth" in pivot.columns else 0
    stable = pivot["Stable"] if "Stable" in pivot.columns else 0
    decline = pivot["Decline"] if "Decline" in pivot.columns else 0
    total = growth + stable + decline
    pivot["growth_share"] = growth / total.replace(0, np.nan)
    pivot["decline_share"] = decline / total.replace(0, np.nan)
    pivot = pivot.sort_values("growth_share", ascending=False)
    pivot.to_csv(cfg.TABLE_DIR / "industry_effect_detail.csv", index=False, encoding="utf-8-sig")

    competition_summary = (
        df.groupby(["category", "outcome_3"])
        .agg(
            mean_same_category_share=("local_same_category_share", "mean"),
            mean_fastfood_share_in_dong=("fastfood_share_in_dong", "mean"),
            mean_cafe_share_in_dong=("cafe_share_in_dong", "mean"),
            mean_pub_share_in_dong=("pub_share_in_dong", "mean"),
            mean_dong_total_store_count=("dong_total_store_count", "mean"),
        )
        .reset_index()
    )
    competition_summary.to_csv(cfg.TABLE_DIR / "competition_density_summary.csv", index=False, encoding="utf-8-sig")


def _run_models(df: pd.DataFrame) -> None:
    model_df = df.copy()
    category_dummies = pd.get_dummies(model_df["category"], prefix="cat", drop_first=True, dtype=float)
    model_df = pd.concat([model_df, category_dummies], axis=1)

    base_predictors = [
        "slope_early_mm",
        "preferred_volatility",
        "mdd",
        "nc_rate",
        "del_ratio_log",
        "before_noon",
        "weekend",
        "trend_slope",
        "seasonal_strength",
        "noise_ratio",
        "n_weeks",
        "business_age_months",
    ] + list(category_dummies.columns)

    competition_predictors = base_predictors + [
        "competition_index",
        "dong_total_store_count",
        "fastfood_share_in_dong",
        "cafe_share_in_dong",
        "pub_share_in_dong",
    ]

    interaction_predictors = competition_predictors + [
        "fastfood_x_competition",
        "cafe_x_competition",
        "pub_x_competition",
    ]
    explicit_share_columns = [
        f"share_cat_{slug}_in_dong"
        for category, slug in cfg.CATEGORY_SLUGS.items()
        if slug != "other" and f"share_cat_{slug}_in_dong" in model_df.columns
    ]
    explicit_share_interactions: list[tuple[str, str, str]] = []
    for category, slug in cfg.CATEGORY_SLUGS.items():
        if category == "기타":
            continue
        dummy_column = f"cat_{category}"
        share_column = f"share_cat_{slug}_in_dong"
        if dummy_column in model_df.columns and share_column in model_df.columns:
            interaction_name = f"int_{slug}_share"
            model_df[interaction_name] = model_df[dummy_column] * model_df[share_column]
            explicit_share_interactions.append((category, share_column, interaction_name))
    full_interaction_predictors = base_predictors + ["dong_total_store_count"] + explicit_share_columns + [
        interaction_name for _, _, interaction_name in explicit_share_interactions
    ]

    fit_a = fit_outcome_mnlogit(model_df, base_predictors, "outcome3_industry_base")
    fit_b = fit_outcome_mnlogit(model_df, competition_predictors, "outcome3_competition")
    fit_c = fit_outcome_mnlogit(model_df, interaction_predictors, "outcome3_competition_interaction")
    fit_d = fit_outcome_mnlogit(model_df, full_interaction_predictors, "outcome3_competition_full_interaction")
    pd.concat([fit_a, fit_b, fit_c, fit_d], ignore_index=True).to_csv(
        cfg.TABLE_DIR / "industry_competition_model_fit.csv",
        index=False,
        encoding="utf-8-sig",
    )

    coef = pd.read_csv(cfg.TABLE_DIR / "outcome3_competition_full_interaction_coefficients.csv").set_index("feature")
    rows = []
    rows.append(
        {
            "category": "기타",
            "share_column": "reference_omitted",
            "share_growth_coef": np.nan,
            "share_growth_pvalue": np.nan,
            "interaction_growth_coef": np.nan,
            "interaction_growth_pvalue": np.nan,
            "combined_growth_coef": np.nan,
            "share_decline_coef": np.nan,
            "share_decline_pvalue": np.nan,
            "interaction_decline_coef": np.nan,
            "interaction_decline_pvalue": np.nan,
            "combined_decline_coef": np.nan,
        }
    )
    for category, share_column, interaction_name in explicit_share_interactions:
        share_growth_coef = float(coef.loc[share_column, "Growth_coef"])
        share_growth_p = float(coef.loc[share_column, "Growth_pvalue"])
        int_growth_coef = float(coef.loc[interaction_name, "Growth_coef"])
        int_growth_p = float(coef.loc[interaction_name, "Growth_pvalue"])
        share_decline_coef = float(coef.loc[share_column, "Decline_coef"])
        share_decline_p = float(coef.loc[share_column, "Decline_pvalue"])
        int_decline_coef = float(coef.loc[interaction_name, "Decline_coef"])
        int_decline_p = float(coef.loc[interaction_name, "Decline_pvalue"])
        rows.append(
            {
                "category": category,
                "share_column": share_column,
                "share_growth_coef": share_growth_coef,
                "share_growth_pvalue": share_growth_p,
                "interaction_growth_coef": int_growth_coef,
                "interaction_growth_pvalue": int_growth_p,
                "combined_growth_coef": share_growth_coef + int_growth_coef,
                "share_decline_coef": share_decline_coef,
                "share_decline_pvalue": share_decline_p,
                "interaction_decline_coef": int_decline_coef,
                "interaction_decline_pvalue": int_decline_p,
                "combined_decline_coef": share_decline_coef + int_decline_coef,
            }
        )
    pd.DataFrame(rows).to_csv(
        cfg.TABLE_DIR / "industry_full_interaction_effects.csv",
        index=False,
        encoding="utf-8-sig",
    )


def _plot_industry_competition(df: pd.DataFrame) -> None:
    cfg.set_korean_font()
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(15, 5))

    growth_share = (
        df.assign(is_growth=(df["outcome_3"] == "Growth").astype(int))
        .groupby("category", as_index=False)["is_growth"]
        .mean()
        .sort_values("is_growth", ascending=True)
    )
    axes[0].barh(growth_share["category"], growth_share["is_growth"], color="#2a6f97")
    axes[0].set_title("업종별 Growth 비율")
    axes[0].set_xlabel("Growth share")

    comp = (
        df.groupby("category", as_index=False)["competition_index"]
        .mean()
        .sort_values("competition_index", ascending=True)
    )
    axes[1].barh(comp["category"], comp["competition_index"], color="#cc5a71")
    axes[1].set_title("업종별 평균 경쟁 밀도")
    axes[1].set_xlabel("Competition index")

    plt.tight_layout()
    plt.savefig(cfg.FIGURE_DIR / "industry_competition_overview.png", dpi=150)
    plt.close(fig)


def run_industry_competition_analysis(base_df: pd.DataFrame, volatility_df: pd.DataFrame) -> pd.DataFrame:
    analysis_df = _prepare_analysis_table(base_df, volatility_df)
    _save_industry_summaries(analysis_df)
    _run_models(analysis_df)
    _plot_industry_competition(analysis_df)
    analysis_df.to_csv(cfg.TABLE_DIR / "industry_competition_analysis_table.csv", index=False, encoding="utf-8-sig")
    return analysis_df
