"""Step 02 — 생존 분석 (Kaplan-Meier + Cox Proportional Hazards).

Survivorship bias 정량화. 업종·outcome·변동성 그룹별 생존 함수 비교, Cox 모형으로 공변량 효과 추정.

Output:
  outputs/tables/km_by_outcome.csv
  outputs/tables/km_by_category.csv
  outputs/tables/logrank_tests.csv
  outputs/tables/cox_ph_summary.csv
  outputs/figures/km_by_outcome.png
  outputs/figures/km_by_category.png
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.statistics import multivariate_logrank_test

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg  # noqa: E402

plt.rcParams.update(cfg.FIG_STYLE)


def load_unified() -> pd.DataFrame:
    return pd.read_parquet(cfg.TABLE_DIR / "unified_store_table.parquet")


def km_curves(df: pd.DataFrame, group_col: str, out_csv: Path, out_fig: Path, title: str,
              min_n: int = 500):
    kmf = KaplanMeierFitter()
    groups = df[group_col].dropna().value_counts()
    groups = groups[groups >= min_n].index.tolist()

    fig, ax = plt.subplots(figsize=(8, 5))
    rows = []
    for g in groups:
        mask = df[group_col] == g
        sub = df[mask]
        if sub["event_indicator"].sum() < 10:
            continue
        kmf.fit(sub["survival_weeks"], sub["event_indicator"], label=str(g))
        kmf.plot_survival_function(ax=ax, ci_show=True)
        sf = kmf.survival_function_.reset_index()
        sf.columns = ["timeline_weeks", f"S_{g}"]
        rows.append(sf)

    ax.set_xlabel("Weeks since open")
    ax.set_ylabel("Survival probability S(t)")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=9)
    fig.savefig(out_fig)
    plt.close(fig)

    if rows:
        merged = rows[0]
        for r in rows[1:]:
            merged = merged.merge(r, on="timeline_weeks", how="outer")
        merged.sort_values("timeline_weeks").to_csv(out_csv, index=False, encoding="utf-8-sig")


def run_logrank(df: pd.DataFrame, group_col: str) -> dict:
    sub = df.dropna(subset=[group_col, "survival_weeks", "event_indicator"]).copy()
    if sub[group_col].nunique() < 2:
        return {"group": group_col, "test_statistic": np.nan, "p_value": np.nan, "n_groups": 0}
    res = multivariate_logrank_test(
        sub["survival_weeks"].values,
        sub[group_col].values,
        sub["event_indicator"].values,
    )
    return {
        "group": group_col,
        "test_statistic": float(res.test_statistic),
        "p_value": float(res.p_value),
        "n_groups": int(sub[group_col].nunique()),
        "n_stores": int(len(sub)),
    }


def run_cox(df: pd.DataFrame) -> pd.DataFrame:
    covariates = [c for c in ["nc_rate", "cv", "slope_early_mm", "slope_late_mm",
                              "r2_early", "mdd", "trend_slope", "seasonal_strength"]
                  if c in df.columns]
    if not covariates:
        return pd.DataFrame()

    cox_df = df[["survival_weeks", "event_indicator"] + covariates].copy()
    cox_df = cox_df.replace([np.inf, -np.inf], np.nan)
    cox_df = cox_df.dropna()
    usable = []
    for c in covariates:
        lo, hi = cox_df[c].quantile([0.01, 0.99])
        cox_df[c] = cox_df[c].clip(lo, hi)
        sd = cox_df[c].std()
        if np.isfinite(sd) and sd > 1e-12:
            cox_df[c] = (cox_df[c] - cox_df[c].mean()) / sd
            usable.append(c)
    cox_df = cox_df[["survival_weeks", "event_indicator"] + usable]
    if not usable:
        return pd.DataFrame()

    cph = CoxPHFitter(penalizer=0.01)
    cph.fit(cox_df, duration_col="survival_weeks", event_col="event_indicator", show_progress=False)
    summary = cph.summary.reset_index().rename(columns={"index": "covariate", "covariate": "covariate"})
    summary["n_obs"] = len(cox_df)
    summary["n_events"] = int(cox_df["event_indicator"].sum())
    summary["concordance"] = cph.concordance_index_
    return summary


def main():
    df = load_unified()
    print(f"[02] Unified table: {len(df):,}")

    df = df.dropna(subset=["survival_weeks", "event_indicator"]).copy()
    df = df[df["survival_weeks"] > 0]

    km_curves(
        df, "outcome_3",
        cfg.TABLE_DIR / "km_by_outcome.csv",
        cfg.FIGURE_DIR / "km_by_outcome.png",
        "Kaplan-Meier Survival — by Outcome (Growth/Stable/Decline)",
    )
    print("[02] km_by_outcome saved")

    cat_col = "classification__kcd_v3__depth_2_name"
    if cat_col in df.columns:
        km_curves(
            df, cat_col,
            cfg.TABLE_DIR / "km_by_category.csv",
            cfg.FIGURE_DIR / "km_by_category.png",
            "Kaplan-Meier Survival — by Category (Top-6)",
            min_n=1500,
        )
        print("[02] km_by_category saved")

    logrank_rows = [run_logrank(df, "outcome_3")]
    if cat_col in df.columns:
        logrank_rows.append(run_logrank(df, cat_col))
    lr_df = pd.DataFrame(logrank_rows)
    lr_df.to_csv(cfg.TABLE_DIR / "logrank_tests.csv", index=False, encoding="utf-8-sig")
    print(lr_df.to_string(index=False))

    cox_summary = run_cox(df)
    if not cox_summary.empty:
        cox_summary.to_csv(cfg.TABLE_DIR / "cox_ph_summary.csv", index=False, encoding="utf-8-sig")
        print("[02] Cox PH summary:")
        print(cox_summary[["covariate", "exp(coef)", "exp(coef) lower 95%", "exp(coef) upper 95%", "p"]].to_string(index=False))

    panel = df[df["in_panel"] == 1]
    non_panel = df[df["in_panel"] == 0]
    bias_row = {
        "panel_n": len(panel),
        "panel_closure_rate": panel["event_indicator"].mean(),
        "non_panel_n": len(non_panel),
        "non_panel_closure_rate": non_panel["event_indicator"].mean(),
        "panel_median_survival": panel["survival_weeks"].median(),
        "non_panel_median_survival": non_panel["survival_weeks"].median(),
    }
    pd.DataFrame([bias_row]).to_csv(cfg.TABLE_DIR / "survivorship_bias_quantification.csv",
                                     index=False, encoding="utf-8-sig")
    print("[02] survivorship bias quantified:", bias_row)


if __name__ == "__main__":
    main()
