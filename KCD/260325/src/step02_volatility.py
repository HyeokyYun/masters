from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.seasonal import STL

from src import config as cfg
from src.model_utils import fit_outcome_mnlogit


def _relative_residual_scale(y: np.ndarray, trend: np.ndarray) -> float:
    residuals = y - trend
    denom = max(float(np.nanmean(np.abs(trend))), float(np.nanmean(np.abs(y))), 1.0)
    return float(np.nanstd(residuals) / (denom + 1e-9))


def _fit_r2(y: np.ndarray, fitted: np.ndarray) -> float:
    ss_res = float(np.nansum((y - fitted) ** 2))
    ss_tot = float(np.nansum((y - np.nanmean(y)) ** 2))
    if ss_tot <= 1e-12:
        return 0.0
    return float(1.0 - ss_res / ss_tot)


def _prepare_weekly_sales(base_df: pd.DataFrame) -> pd.DataFrame:
    open_dates = base_df[["public_id", "open_date"]].drop_duplicates().copy()
    weekly = pd.read_parquet(cfg.get_weekly_path(), columns=["public_id", "date_id", "sales_card"])
    weekly["public_id"] = weekly["public_id"].astype(str)
    weekly["date_id"] = pd.to_datetime(weekly["date_id"])
    weekly = weekly[weekly["public_id"].isin(set(base_df["public_id"]))].copy()
    weekly.loc[weekly["sales_card"] < 0, "sales_card"] = np.nan
    weekly = weekly.merge(open_dates, on="public_id", how="left")
    weekly["weeks_since_open"] = ((weekly["date_id"] - weekly["open_date"]).dt.days // 7).clip(lower=0)
    weekly = weekly[weekly["weeks_since_open"] < cfg.MAX_WEEKS].copy()
    weekly.sort_values(["public_id", "weeks_since_open"], inplace=True)
    weekly["sales_card"] = weekly.groupby("public_id")["sales_card"].transform(
        lambda values: values.interpolate("linear").ffill().bfill()
    )
    return weekly


def _compute_store_volatility(weekly: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, float | str]] = []

    for public_id, group in weekly.groupby("public_id", sort=False):
        group = group.drop_duplicates("weeks_since_open").copy()
        y = group["sales_card"].to_numpy(dtype=float)
        if len(y) < cfg.MIN_WEEKS or not np.isfinite(y).any():
            continue

        t = np.arange(len(y), dtype=float)
        linear_coef = np.polyfit(t, y, 1)
        linear_trend = np.polyval(linear_coef, t)

        if len(y) >= 6:
            quadratic_coef = np.polyfit(t, y, 2)
            quadratic_trend = np.polyval(quadratic_coef, t)
        else:
            quadratic_trend = linear_trend

        rolling8_trend = pd.Series(y).rolling(8, min_periods=1, center=True).mean().to_numpy()
        rolling10_trend = pd.Series(y).rolling(10, min_periods=1, center=True).mean().to_numpy()
        rolling12_trend = pd.Series(y).rolling(12, min_periods=1, center=True).mean().to_numpy()
        rolling13_trend = pd.Series(y).rolling(cfg.STL_PERIOD, min_periods=1, center=True).mean().to_numpy()
        try:
            if len(y) >= 2 * cfg.STL_PERIOD:
                stl_trend = np.asarray(STL(y, period=cfg.STL_PERIOD, robust=True).fit().trend, dtype=float)
            else:
                stl_trend = rolling13_trend
        except Exception:
            stl_trend = rolling13_trend

        slope_linear, _, r_linear, _, _ = stats.linregress(t, y)
        records.append(
            {
                "public_id": public_id,
                "n_weeks_used": float(len(y)),
                "sales_mean": float(np.nanmean(y)),
                "sales_std": float(np.nanstd(y)),
                "vol_cv_mean": float(np.nanstd(y) / (np.nanmean(y) + 1e-9)),
                "vol_resid_linear": _relative_residual_scale(y, linear_trend),
                "vol_resid_quadratic": _relative_residual_scale(y, quadratic_trend),
                "vol_resid_rolling8": _relative_residual_scale(y, rolling8_trend),
                "vol_resid_rolling10": _relative_residual_scale(y, rolling10_trend),
                "vol_resid_rolling12": _relative_residual_scale(y, rolling12_trend),
                "vol_resid_rolling13": _relative_residual_scale(y, rolling13_trend),
                "vol_resid_stl13": _relative_residual_scale(y, stl_trend),
                "linear_fit_r2": _fit_r2(y, linear_trend),
                "quadratic_fit_r2": _fit_r2(y, quadratic_trend),
                "stl_fit_r2": _fit_r2(y, stl_trend),
                "sales_slope_linear": float(slope_linear),
                "sales_r2_linear": float(r_linear ** 2),
            }
        )

    return pd.DataFrame(records)


def _screen_metrics(base_df: pd.DataFrame, volatility_df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    merged = base_df[["public_id", "outcome_3"]].merge(volatility_df, on="public_id", how="inner")
    metrics = [
        "vol_cv_mean",
        "vol_resid_linear",
        "vol_resid_quadratic",
        "vol_resid_rolling8",
        "vol_resid_rolling10",
        "vol_resid_rolling12",
        "vol_resid_rolling13",
        "vol_resid_stl13",
    ]

    summary = merged.groupby("outcome_3", as_index=False)[metrics].mean()
    summary.to_csv(cfg.TABLE_DIR / "volatility_by_outcome_summary.csv", index=False, encoding="utf-8-sig")

    rows = []
    for metric in metrics:
        samples = {
            outcome: merged.loc[merged["outcome_3"] == outcome, metric].dropna()
            for outcome in cfg.OUTCOME_ORDER
        }
        if min(len(values) for values in samples.values()) >= 5:
            f_stat, p_value = stats.f_oneway(*samples.values())
        else:
            f_stat, p_value = np.nan, np.nan
        detrended = metric != "vol_cv_mean"
        rows.append(
            {
                "metric": metric,
                "is_detrended": detrended,
                "stable_mean": float(samples["Stable"].mean()),
                "growth_mean": float(samples["Growth"].mean()),
                "decline_mean": float(samples["Decline"].mean()),
                "anova_f": float(f_stat) if np.isfinite(f_stat) else np.nan,
                "anova_p": float(p_value) if np.isfinite(p_value) else np.nan,
            }
        )

    screening = pd.DataFrame(rows).sort_values(["is_detrended", "anova_p"], ascending=[False, True], na_position="last")
    screening.to_csv(cfg.TABLE_DIR / "volatility_metric_screening.csv", index=False, encoding="utf-8-sig")
    preferred_metric = "vol_resid_rolling12"
    return screening, preferred_metric


def _plot_volatility(volatility_df: pd.DataFrame, preferred_metric: str) -> None:
    cfg.set_korean_font()
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    axes[0].scatter(volatility_df["vol_cv_mean"], volatility_df[preferred_metric], s=5, alpha=0.2, color="#2a6f97")
    axes[0].set_xlabel("기존 CV")
    axes[0].set_ylabel("선택된 추세조정 변동성")
    axes[0].set_title("기존 CV vs 추세조정 변동성")

    metric_cols = [
        "vol_cv_mean",
        "vol_resid_linear",
        "vol_resid_quadratic",
        "vol_resid_rolling8",
        "vol_resid_rolling10",
        "vol_resid_rolling12",
        "vol_resid_rolling13",
        "vol_resid_stl13",
    ]
    metric_means = volatility_df[metric_cols].mean().sort_values()
    axes[1].barh(metric_means.index, metric_means.values, color="#74a57f")
    axes[1].set_title("변동성 정의별 평균값")

    fit_cols = ["linear_fit_r2", "quadratic_fit_r2", "stl_fit_r2"]
    fit_means = volatility_df[fit_cols].mean().sort_values()
    axes[2].barh(fit_means.index, fit_means.values, color="#cc5a71")
    axes[2].set_title("추세 적합도 평균")

    plt.tight_layout()
    plt.savefig(cfg.FIGURE_DIR / "volatility_comparison.png", dpi=150)
    plt.close(fig)


def run_volatility_analysis(base_df: pd.DataFrame) -> pd.DataFrame:
    base_df = base_df.copy()
    if "open_date" in base_df.columns:
        base_df["open_date"] = pd.to_datetime(base_df["open_date"], errors="coerce")
    weekly = _prepare_weekly_sales(base_df)
    volatility_df = _compute_store_volatility(weekly)
    volatility_df.to_csv(cfg.TABLE_DIR / "volatility_candidates.csv", index=False, encoding="utf-8-sig")

    screening, preferred_metric = _screen_metrics(base_df, volatility_df)
    _plot_volatility(volatility_df, preferred_metric)

    model_df = base_df.merge(volatility_df[["public_id", "vol_cv_mean", preferred_metric]], on="public_id", how="inner")
    model_df = model_df.rename(columns={preferred_metric: "preferred_volatility"})

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

    fit_a = fit_outcome_mnlogit(model_df, baseline_predictors, "outcome3_volatility_baseline")
    fit_b = fit_outcome_mnlogit(model_df, adjusted_predictors, "outcome3_volatility_adjusted")
    pd.concat([fit_a, fit_b], ignore_index=True).to_csv(
        cfg.TABLE_DIR / "volatility_model_fit_comparison.csv",
        index=False,
        encoding="utf-8-sig",
    )

    note = pd.DataFrame(
        [
            {"item": "preferred_metric", "value": preferred_metric},
            {"item": "top_screen_metric", "value": screening.iloc[0]["metric"] if not screening.empty else np.nan},
        ]
    )
    note.to_csv(cfg.TABLE_DIR / "volatility_selection_note.csv", index=False, encoding="utf-8-sig")

    return volatility_df
