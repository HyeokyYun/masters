from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.seasonal import STL

from src import config as cfg


def _safe_relative_resid_scale(y: np.ndarray, trend: np.ndarray) -> float:
    resid = y - trend
    denom = max(
        float(np.nanmean(np.clip(np.abs(y), 1.0, None))),
        float(np.nanmean(np.clip(np.abs(trend), 1.0, None))),
        1.0,
    )
    return float(np.nanstd(resid) / (denom + 1e-9))


def _fit_r2(y: np.ndarray, fitted: np.ndarray) -> float:
    ss_res = float(np.nansum((y - fitted) ** 2))
    ss_tot = float(np.nansum((y - np.nanmean(y)) ** 2))
    if ss_tot <= 1e-12:
        return 0.0
    return 1.0 - ss_res / ss_tot


def _prepare_weekly_subset(public_ids: set[str], open_dates: pd.DataFrame) -> pd.DataFrame:
    weekly = pd.read_parquet(cfg.get_weekly_path(), columns=["public_id", "date_id", "sales_card"])
    weekly["public_id"] = weekly["public_id"].astype(str)
    weekly["date_id"] = pd.to_datetime(weekly["date_id"])
    weekly = weekly[weekly["public_id"].isin(public_ids)].copy()
    weekly.loc[weekly["sales_card"] < 0, "sales_card"] = np.nan
    weekly = weekly.merge(open_dates, on="public_id", how="left")
    weekly["weeks_since_open"] = ((weekly["date_id"] - weekly["open_date"]).dt.days // 7).clip(lower=0)
    weekly = weekly[weekly["open_date"] >= cfg.OPEN_DATE_MIN].copy()
    weekly = weekly[weekly["weeks_since_open"] < cfg.MAX_WEEKS].copy()
    weekly.sort_values(["public_id", "weeks_since_open"], inplace=True)
    weekly["sales_card"] = weekly.groupby("public_id")["sales_card"].transform(
        lambda values: values.interpolate("linear").ffill().bfill()
    )
    return weekly


def compute_volatility_candidates(base_df: pd.DataFrame) -> pd.DataFrame:
    open_dates = base_df[["public_id", "open_date"]].drop_duplicates().copy()
    weekly = _prepare_weekly_subset(set(base_df["public_id"]), open_dates)

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

        rolling_trend = pd.Series(y).rolling(cfg.STL_PERIOD, min_periods=1, center=True).mean().to_numpy()
        if len(y) >= 2 * cfg.STL_PERIOD:
            try:
                stl = STL(y, period=cfg.STL_PERIOD, robust=True).fit()
                stl_trend = np.asarray(stl.trend, dtype=float)
            except Exception:
                stl_trend = rolling_trend
        else:
            stl_trend = rolling_trend

        slope_linear, _, r_linear, _, _ = stats.linregress(t, y)
        current_cv = float(np.nanstd(y) / (np.nanmean(y) + 1e-9))
        record = {
            "public_id": public_id,
            "n_weeks_used": float(len(y)),
            "sales_mean": float(np.nanmean(y)),
            "sales_std": float(np.nanstd(y)),
            "vol_cv_mean": current_cv,
            "vol_resid_linear": _safe_relative_resid_scale(y, linear_trend),
            "vol_resid_quadratic": _safe_relative_resid_scale(y, quadratic_trend),
            "vol_resid_rolling13": _safe_relative_resid_scale(y, rolling_trend),
            "vol_resid_stl13": _safe_relative_resid_scale(y, stl_trend),
            "linear_fit_r2": _fit_r2(y, linear_trend),
            "quadratic_fit_r2": _fit_r2(y, quadratic_trend),
            "stl_fit_r2": _fit_r2(y, stl_trend),
            "sales_slope_linear": float(slope_linear),
            "sales_r2_linear": float(r_linear ** 2),
        }
        records.append(record)

    volatility = pd.DataFrame(records)
    volatility.to_csv(cfg.TABLE_DIR / "volatility_candidate_metrics.csv", index=False, encoding="utf-8-sig")

    merged = base_df[["public_id", "outcome_3", "category"]].merge(volatility, on="public_id", how="inner")
    metrics = [
        "vol_cv_mean",
        "vol_resid_linear",
        "vol_resid_quadratic",
        "vol_resid_rolling13",
        "vol_resid_stl13",
    ]

    grouped = merged.groupby("outcome_3")[metrics].mean().reset_index()
    grouped.to_csv(cfg.TABLE_DIR / "volatility_by_outcome_summary.csv", index=False, encoding="utf-8-sig")

    screening_rows = []
    for metric in metrics:
        growth = merged.loc[merged["outcome_3"] == "growth", metric].dropna()
        stable = merged.loc[merged["outcome_3"] == "stable", metric].dropna()
        decline = merged.loc[merged["outcome_3"] == "decline", metric].dropna()
        if min(len(growth), len(stable), len(decline)) >= 5:
            f_stat, p_value = stats.f_oneway(growth, stable, decline)
        else:
            f_stat, p_value = np.nan, np.nan
        screening_rows.append(
            {
                "metric": metric,
                "growth_mean": float(growth.mean()) if len(growth) else np.nan,
                "stable_mean": float(stable.mean()) if len(stable) else np.nan,
                "decline_mean": float(decline.mean()) if len(decline) else np.nan,
                "anova_f": float(f_stat) if np.isfinite(f_stat) else np.nan,
                "anova_p": float(p_value) if np.isfinite(p_value) else np.nan,
            }
        )
    screening = pd.DataFrame(screening_rows).sort_values("anova_p", na_position="last")
    screening.to_csv(cfg.TABLE_DIR / "volatility_metric_screening.csv", index=False, encoding="utf-8-sig")
    return volatility
