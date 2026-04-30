from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from src import config as cfg
from src.model_utils import fit_outcome_mnlogit
from src.step02_volatility import _prepare_weekly_sales, _relative_residual_scale


ROLLING_WINDOWS = [8, 10, 12, 13]


def _compute_window_metrics(weekly: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, float | str]] = []

    for public_id, group in weekly.groupby("public_id", sort=False):
        group = group.drop_duplicates("weeks_since_open").copy()
        y = group["sales_card"].to_numpy(dtype=float)
        if len(y) < cfg.MIN_WEEKS or not np.isfinite(y).any():
            continue

        row: dict[str, float | str] = {
            "public_id": public_id,
            "n_weeks_used": float(len(y)),
            "vol_cv_mean": float(np.nanstd(y) / (np.nanmean(y) + 1e-9)),
        }
        for window in ROLLING_WINDOWS:
            trend = pd.Series(y).rolling(window, min_periods=1, center=True).mean().to_numpy()
            row[f"vol_resid_rolling{window}"] = _relative_residual_scale(y, trend)
        records.append(row)

    return pd.DataFrame(records)


def _screen_windows(base_df: pd.DataFrame, metric_df: pd.DataFrame) -> pd.DataFrame:
    merged = base_df[["public_id", "outcome_3"]].merge(metric_df, on="public_id", how="inner")
    rows = []

    for window in ROLLING_WINDOWS:
        metric = f"vol_resid_rolling{window}"
        samples = {
            outcome: merged.loc[merged["outcome_3"] == outcome, metric].dropna()
            for outcome in cfg.OUTCOME_ORDER
        }
        f_stat, p_value = stats.f_oneway(*samples.values())
        rows.append(
            {
                "window_weeks": window,
                "metric": metric,
                "stable_mean": float(samples["Stable"].mean()),
                "growth_mean": float(samples["Growth"].mean()),
                "decline_mean": float(samples["Decline"].mean()),
                "growth_gap_vs_stable": float(samples["Growth"].mean() - samples["Stable"].mean()),
                "decline_gap_vs_stable": float(samples["Decline"].mean() - samples["Stable"].mean()),
                "anova_f": float(f_stat),
                "anova_p": float(p_value),
            }
        )

    screening = pd.DataFrame(rows).sort_values(["anova_p", "anova_f"], ascending=[True, False]).reset_index(drop=True)
    screening.to_csv(cfg.TABLE_DIR / "rolling_window_sensitivity_screening.csv", index=False, encoding="utf-8-sig")
    return screening


def _fit_models(base_df: pd.DataFrame, metric_df: pd.DataFrame) -> pd.DataFrame:
    baseline_predictors = [
        "slope_early_mm",
        "vol_cv_mean",
        "mdd",
        "nc_rate",
        "del_ratio_log",
        "before_noon",
        "weekend",
        "trend_slope",
        "seasonal_strength",
        "noise_ratio",
        "n_weeks",
    ]
    adjusted_predictors = [
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
    ]

    rows: list[pd.DataFrame] = []
    base_model_df = base_df.merge(metric_df[["public_id", "vol_cv_mean"]], on="public_id", how="inner")
    baseline_fit = fit_outcome_mnlogit(base_model_df, baseline_predictors, "outcome3_volatility_baseline_recheck")
    baseline_fit["window_weeks"] = 0
    baseline_fit["metric"] = "vol_cv_mean"
    rows.append(baseline_fit)

    for window in ROLLING_WINDOWS:
        metric = f"vol_resid_rolling{window}"
        model_df = base_df.merge(metric_df[["public_id", metric]], on="public_id", how="inner")
        model_df = model_df.rename(columns={metric: "preferred_volatility"})
        fit = fit_outcome_mnlogit(model_df, adjusted_predictors, f"outcome3_volatility_roll{window}")
        fit["window_weeks"] = window
        fit["metric"] = metric
        rows.append(fit)

    fit_df = pd.concat(rows, ignore_index=True)
    fit_df.to_csv(cfg.TABLE_DIR / "rolling_window_sensitivity_model_fit.csv", index=False, encoding="utf-8-sig")
    return fit_df


def run_rolling_window_sensitivity(base_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    base_df = base_df.copy()
    if "open_date" in base_df.columns:
        base_df["open_date"] = pd.to_datetime(base_df["open_date"], errors="coerce")
    weekly = _prepare_weekly_sales(base_df)
    metric_df = _compute_window_metrics(weekly)
    metric_df.to_csv(cfg.TABLE_DIR / "rolling_window_sensitivity_values.csv", index=False, encoding="utf-8-sig")

    screening = _screen_windows(base_df, metric_df)
    fit_df = _fit_models(base_df, metric_df)

    best_screen = screening.iloc[0]
    best_fit = fit_df[fit_df["window_weeks"] > 0].sort_values(["pseudo_r2", "aic"], ascending=[False, True]).iloc[0]

    note = f"""# Rolling Window Sensitivity

`rolling8`, `rolling10`, `rolling12`, `rolling13`을 같은 표본에서 비교했다.

## 집단 구분력 기준

가장 작은 ANOVA p-value와 가장 큰 F값을 보인 창은 `rolling{int(best_screen['window_weeks'])}`였다.

- best metric: `{best_screen['metric']}`
- Stable mean: `{best_screen['stable_mean']:.4f}`
- Growth mean: `{best_screen['growth_mean']:.4f}`
- Decline mean: `{best_screen['decline_mean']:.4f}`
- ANOVA F: `{best_screen['anova_f']:.4f}`

## 설명모형 적합도 기준

가장 높은 pseudo R²와 낮은 AIC를 보인 창은 `rolling{int(best_fit['window_weeks'])}`였다.

- best metric: `{best_fit['metric']}`
- pseudo R²: `{best_fit['pseudo_r2']:.6f}`
- AIC: `{best_fit['aic']:.4f}`
"""
    with open(cfg.DOC_DIR / "rolling_window_sensitivity_note.md", "w", encoding="utf-8") as handle:
        handle.write(note)

    return screening, fit_df
