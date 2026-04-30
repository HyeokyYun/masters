from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from src import config as cfg


def _safe_linregress(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    if len(x) < 3 or np.std(y) < 1e-12:
        return 0.0, 0.0
    slope, _, r_value, _, _ = stats.linregress(x.astype(float), y.astype(float))
    return float(slope), float(r_value**2)


def _relative_change(start: float, end: float) -> float:
    if not np.isfinite(start) or not np.isfinite(end):
        return np.nan
    if abs(start) < 1e-9:
        if abs(end) < 1e-9:
            return 0.0
        return 1.0 if end > 0 else -1.0
    return float((end - start) / abs(start))


def extract_features(ts: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    total = ts["public_id"].nunique()

    for idx, (public_id, group) in enumerate(ts.groupby("public_id"), start=1):
        if idx % 5000 == 0:
            print(f"  [{idx:,}/{total:,}]")

        group = (
            group.sort_values("weeks_since_open")
            .drop_duplicates("weeks_since_open")
            .reset_index(drop=True)
        )
        group = group[group["weeks_since_open"] < cfg.MAX_WEEKS]

        y_raw = group["sales_card"].fillna(0).to_numpy(dtype=float)
        y_mm = group["sales_card_mm"].fillna(0).to_numpy(dtype=float)
        trend_mm = group["trend_mm"].fillna(0).to_numpy(dtype=float)

        if len(y_raw) < cfg.MIN_WEEKS or not np.isfinite(y_mm).all():
            continue

        n = len(y_mm)
        h = n // 2
        t = np.arange(n, dtype=float)
        edge = min(cfg.PATTERN_EDGE_WEEKS, max(4, n // 4))

        slope_early, r2_early = _safe_linregress(t[:h], y_mm[:h])
        slope_late, r2_late = _safe_linregress(t[h:] - h, y_mm[h:])
        slope_all, r2_all = _safe_linregress(t, y_mm)
        trend_slope, _ = _safe_linregress(t, trend_mm)

        start_mean_mm = float(np.mean(y_mm[:edge]))
        end_mean_mm = float(np.mean(y_mm[-edge:]))
        overall_change_rate = _relative_change(start_mean_mm, end_mean_mm)

        cv = float(min(y_raw.std() / (y_raw.mean() + 1e-9), 2.0))
        running_max = np.maximum.accumulate(y_mm)
        mdd = float(((running_max - y_mm) / (running_max + 1e-9)).max())

        nc_rate = np.nan
        if {"customer_new", "customer"}.issubset(group.columns):
            denom = group["customer"].replace(0, np.nan) + 1
            nc = group["customer_new"] / denom
            nc_rate = float(nc.mean()) if nc.notna().any() else np.nan

        before_noon = float(group["before_noon_sales"].mean()) if "before_noon_sales" in group.columns else np.nan
        weekend = float(group["weekend_sales"].mean()) if "weekend_sales" in group.columns else np.nan

        seasonal_strength = 0.0
        noise_ratio = 0.0
        if "seasonal" in group.columns:
            var_total = float(np.var(y_raw) + 1e-9)
            var_resid = float(np.var(group["resid"].to_numpy(dtype=float))) if "resid" in group.columns else 0.0
            seasonal_strength = float(max(0.0, 1.0 - var_resid / var_total))
            noise_ratio = float(var_resid / var_total)

        category = "기타"
        if "classification__kcd_v3__depth_2_name" in group.columns:
            category = str(group["classification__kcd_v3__depth_2_name"].iloc[0])

        records.append(
            {
                "public_id": public_id,
                "category": category,
                "slope_early_mm": slope_early,
                "slope_late_mm": slope_late,
                "slope_all_mm": slope_all,
                "trend_slope": trend_slope,
                "r2_all": r2_all,
                "r2_early": r2_early,
                "r2_late": r2_late,
                "cv": cv,
                "mdd": mdd,
                "nc_rate": nc_rate,
                "before_noon": before_noon,
                "weekend": weekend,
                "seasonal_strength": seasonal_strength,
                "noise_ratio": noise_ratio,
                "start_mean_mm": start_mean_mm,
                "end_mean_mm": end_mean_mm,
                "overall_change_rate": overall_change_rate,
                "n_weeks": n,
            }
        )

    features = pd.DataFrame(records)
    out_path = cfg.TABLE_DIR / "store_features.csv"
    features.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[Step02] 저장 → {out_path.name} ({len(features):,} stores)")
    return features
