from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from src import config as cfg


def _safe_linregress(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    if len(x) < 3 or np.std(y) < 1e-12:
        return 0.0, 0.0, 0.0
    slope, _, r_value, _, _ = stats.linregress(x.astype(float), y.astype(float))
    return float(slope), float(r_value), float(r_value**2)


def extract_observed_window_features(panel: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, float | str]] = []
    groups = panel.groupby("public_id", sort=False)

    for public_id, group in groups:
        group = group.sort_values("observed_week_idx").reset_index(drop=True)
        y_raw = group["sales_card"].fillna(0).to_numpy(dtype=float)
        y_mm = group["sales_card_mm"].fillna(0).to_numpy(dtype=float)
        if len(y_raw) < cfg.MIN_FEATURE_WEEKS or not np.isfinite(y_mm).all():
            continue

        n = len(y_mm)
        half = n // 2
        t = np.arange(n, dtype=float)

        slope_early, _, r2_early = _safe_linregress(t[:half], y_mm[:half])
        slope_late, _, _ = _safe_linregress(t[half:] - half, y_mm[half:])
        slope_all, _, r2_all = _safe_linregress(t, y_mm)
        tail_n = max(8, n // 5)
        slope_tail, _, _ = _safe_linregress(np.arange(tail_n, dtype=float), y_mm[-tail_n:])

        cv = min(float(np.std(y_raw) / (np.mean(y_raw) + 1e-9)), 5.0)
        cummax = np.maximum.accumulate(y_mm)
        mdd = float(((cummax - y_mm) / (cummax + 1e-9)).max())

        nc_rate = np.nan
        if "customer_new" in group.columns and "customer" in group.columns:
            denom = group["customer"].replace(0, np.nan) + 1
            nc = group["customer_new"] / denom
            nc_rate = float(nc.mean()) if nc.notna().any() else np.nan

        del_ratio_log = np.nan
        if "sales_delivery" in group.columns:
            total_sales = y_raw.sum()
            if total_sales > 0:
                del_ratio_log = float(np.log1p(group["sales_delivery"].fillna(0).sum() / total_sales))

        before_noon = float(group["before_noon_sales"].mean()) if "before_noon_sales" in group.columns else np.nan
        weekend = float(group["weekend_sales"].mean()) if "weekend_sales" in group.columns else np.nan

        trend_slope = 0.0
        seasonal_strength = 0.0
        noise_ratio = 0.0
        if "trend_mm" in group.columns:
            trend_slope, _, _ = _safe_linregress(t, group["trend_mm"].fillna(0).to_numpy(dtype=float))
        if "seasonal" in group.columns and "resid" in group.columns:
            total_var = np.var(y_raw) + 1e-9
            resid_var = np.var(group["resid"].to_numpy(dtype=float))
            seasonal_strength = float(max(0.0, 1.0 - resid_var / total_var))
            noise_ratio = float(resid_var / total_var)

        records.append(
            {
                "public_id": public_id,
                "category": group["category"].iloc[0] if "category" in group.columns else "기타",
                "open_date": group["open_date"].iloc[0] if "open_date" in group.columns else pd.NaT,
                "first_observed_date": group["date_id"].min(),
                "last_observed_date": group["date_id"].max(),
                "n_observed_weeks_used": n,
                "slope_early_mm": slope_early,
                "slope_late_mm": slope_late,
                "slope_all_mm": slope_all,
                "slope_tail_mm": slope_tail,
                "r2": r2_all,
                "r2_early": r2_early,
                "cv": cv,
                "mdd": mdd,
                "nc_rate": nc_rate,
                "del_ratio_log": del_ratio_log,
                "before_noon": before_noon,
                "weekend": weekend,
                "trend_slope": trend_slope,
                "seasonal_strength": seasonal_strength,
                "noise_ratio": noise_ratio,
            }
        )

    feat = pd.DataFrame(records)
    feat.to_csv(cfg.TABLE_DIR / "observed_window_features.csv", index=False, encoding="utf-8-sig")
    return feat
