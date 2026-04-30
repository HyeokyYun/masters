"""Step 00 - Build the top_tier analysis panel from original_data only.

Inputs:
  original_data/weekly.parquet
  original_data/meta.csv

Outputs:
  outputs/tables/observed_window_panel.parquet
  outputs/tables/observed_window_features_labeled.csv

This step removes the dependency on older experiment folders.  It recreates the
panel and store-level lifecycle labels used by the downstream top_tier scripts.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg  # noqa: E402


MAX_FEATURE_WEEKS = 108
MIN_PANEL_WEEKS = 52


def _slope(y: np.ndarray) -> tuple[float, float]:
    x = np.arange(len(y), dtype=float)
    mask = np.isfinite(y)
    if mask.sum() < 3 or np.nanstd(y[mask]) < 1e-12:
        return 0.0, 0.0
    s, _, r, _, _ = stats.linregress(x[mask], y[mask])
    return float(s), float(r * r)


def _mdd(y: np.ndarray) -> float:
    if len(y) == 0:
        return 0.0
    peak = np.maximum.accumulate(y)
    dd = (peak - y) / (peak + 1e-9)
    return float(np.nanmax(dd))


def _category(v: object) -> str:
    v = str(v)
    if any(k in v for k in ["카페", "커피"]):
        return "카페"
    if any(k in v for k in ["베이커리", "디저트"]):
        return "베이커리/디저트"
    if any(k in v for k in ["술집", "주점", "호프"]):
        return "술집"
    for key in ["한식", "일식", "양식", "중식", "분식", "패스트푸드"]:
        if key in v:
            return key
    return "기타 외식업"


def load_original() -> tuple[pd.DataFrame, pd.DataFrame]:
    print("[00] loading original weekly/meta ...")
    weekly = pd.read_parquet(cfg.WEEKLY_PATH)
    meta = pd.read_csv(cfg.META_PATH)
    weekly["public_id"] = weekly["public_id"].astype(str)
    meta["public_id"] = meta["public_id"].astype(str)
    weekly["date_id"] = pd.to_datetime(weekly["date_id"])
    weekly.loc[weekly["sales_card"] < 0, "sales_card"] = np.nan
    meta["open_date"] = pd.to_datetime(
        meta["open_month"].astype(str), format="%Y-%m", errors="coerce"
    )
    meta["category"] = meta["classification__kcd_v3__depth_2_name"].map(_category)
    print(
        f"[00] weekly rows={len(weekly):,}, stores={weekly['public_id'].nunique():,}, "
        f"window={weekly['date_id'].min().date()}~{weekly['date_id'].max().date()}"
    )
    return weekly, meta


def build_panel(weekly: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    cnt = weekly.groupby("public_id")["date_id"].nunique()
    keep_ids = cnt[cnt >= MIN_PANEL_WEEKS].index
    panel = weekly[weekly["public_id"].isin(keep_ids)].copy()
    panel = panel.merge(
        meta[
            [
                "public_id",
                "open_month",
                "open_date",
                "delivery_link",
                "business_square_size",
                "classification__kcd_v3__depth_2_name",
                "dong",
                "category",
            ]
        ],
        on="public_id",
        how="left",
    )
    panel = panel.sort_values(["public_id", "date_id"])
    panel["observed_week_idx"] = panel.groupby("public_id").cumcount()
    panel = panel[panel["observed_week_idx"] < MAX_FEATURE_WEEKS].copy()

    panel["sales_card"] = panel.groupby("public_id")["sales_card"].transform(
        lambda s: s.interpolate("linear").ffill().bfill()
    )
    mins = panel.groupby("public_id")["sales_card"].transform("min")
    maxs = panel.groupby("public_id")["sales_card"].transform("max")
    panel["sales_card_mm"] = (panel["sales_card"] - mins) / (maxs - mins + 1e-9)
    panel["trend"] = panel.groupby("public_id")["sales_card"].transform(
        lambda s: s.rolling(5, min_periods=1, center=True).mean()
    )
    tmins = panel.groupby("public_id")["trend"].transform("min")
    tmaxs = panel.groupby("public_id")["trend"].transform("max")
    panel["trend_mm"] = (panel["trend"] - tmins) / (tmaxs - tmins + 1e-9)
    panel["seasonal"] = 0.0
    panel["resid"] = panel["sales_card"] - panel["trend"]
    print(f"[00] panel rows={len(panel):,}, stores={panel['public_id'].nunique():,}")
    return panel


def build_features(panel: pd.DataFrame) -> pd.DataFrame:
    print("[00] building vectorized lifecycle features ...")
    mm = panel.pivot_table(
        index="public_id", columns="observed_week_idx", values="sales_card_mm", aggfunc="mean"
    ).sort_index(axis=1)
    raw = panel.pivot_table(
        index="public_id", columns="observed_week_idx", values="sales_card", aggfunc="mean"
    ).reindex(index=mm.index, columns=mm.columns)
    arr = mm.to_numpy(dtype=float)
    raw_arr = raw.to_numpy(dtype=float)
    ids = mm.index.astype(str).to_numpy()
    x_all = np.arange(arr.shape[1], dtype=float)

    def slope_and_r2(y: np.ndarray, x: np.ndarray | None = None) -> tuple[float, float]:
        if x is None:
            x = np.arange(len(y), dtype=float)
        mask = np.isfinite(y)
        n = int(mask.sum())
        if n < 3:
            return 0.0, 0.0
        yy = y[mask]
        xx = x[mask]
        vx = xx - xx.mean()
        vy = yy - yy.mean()
        den = float(np.dot(vx, vx))
        vary = float(np.dot(vy, vy))
        if den < 1e-12 or vary < 1e-12:
            return 0.0, 0.0
        slope = float(np.dot(vx, vy) / den)
        r2 = float((np.dot(vx, vy) ** 2) / (den * vary))
        return slope, r2

    records = []
    n_valid = np.isfinite(arr).sum(axis=1)
    for i, pid in enumerate(ids):
        n = int(n_valid[i])
        y = arr[i, :n]
        y_raw = raw_arr[i, :n]
        h = max(3, n // 2)
        tail_n = max(8, n // 5)
        s_early, r2_early = slope_and_r2(y[:h])
        s_late, _ = slope_and_r2(y[h:])
        s_all, r2 = slope_and_r2(y)
        s_tail, _ = slope_and_r2(y[-tail_n:])
        records.append(
            {
                "public_id": pid,
                "n_observed_weeks_used": n,
                "slope_early_mm": s_early,
                "slope_late_mm": s_late,
                "slope_all_mm": s_all,
                "slope_tail_mm": s_tail,
                "r2": r2,
                "r2_early": r2_early,
                "cv": float(min(np.nanstd(y_raw) / (np.nanmean(y_raw) + 1e-9), 5.0)),
                "mdd": _mdd(y),
                "trend_slope": s_all,
                "seasonal_strength": 0.0,
                "noise_ratio": 1.0 - min(max(r2, 0.0), 1.0),
            }
        )
    feat = pd.DataFrame(records)

    panel_work = panel.copy()
    denom = panel_work["customer"].replace(0, np.nan)
    panel_work["nc_ratio_tmp"] = (panel_work["customer_new"] / denom).replace([np.inf, -np.inf], np.nan)
    panel_work["delivery_filled"] = panel_work["sales_delivery"].fillna(0)
    beh = (
        panel_work.groupby("public_id", observed=True)
        .agg(
            nc_rate=("nc_ratio_tmp", "mean"),
            sales_sum=("sales_card", "sum"),
            delivery_sum=("delivery_filled", "sum"),
            before_noon=("before_noon_sales", "mean"),
            weekend=("weekend_sales", "mean"),
        )
        .reset_index()
    )
    beh["del_ratio_log"] = np.log1p(beh["delivery_sum"] / beh["sales_sum"].replace(0, np.nan)).fillna(0.0)
    beh = beh.drop(columns=["sales_sum", "delivery_sum"])

    summary = (
        panel.groupby("public_id", observed=True)
        .agg(
            category=("category", "first"),
            open_date=("open_date", "first"),
            first_observed_date=("date_id", "min"),
            last_observed_date=("date_id", "max"),
        )
        .reset_index()
    )
    feat = feat.merge(summary, on="public_id", how="inner")
    feat = feat.merge(beh, on="public_id", how="left")

    sigma = feat["slope_all_mm"].std()
    thr = 0.5 * sigma
    feat["outcome_3"] = np.select(
        [feat["slope_all_mm"] > thr, feat["slope_all_mm"] < -thr],
        ["Growth", "Decline"],
        default="Stable",
    )
    suffix = feat["outcome_3"].map({"Growth": "X", "Stable": "Y", "Decline": "Z"})
    early = np.where(feat["slope_early_mm"] > 0, "U", "D")
    late = np.where(feat["slope_late_mm"] > 0, "U", "D")
    feat["label"] = early + late + "_" + suffix
    print(f"[00] features rows={len(feat):,}, threshold={thr:.6g}")
    print(feat["outcome_3"].value_counts().to_string())
    return feat


def main() -> None:
    weekly, meta = load_original()
    panel = build_panel(weekly, meta)
    features = build_features(panel)
    panel.to_parquet(cfg.PANEL_PATH, index=False)
    features.to_csv(cfg.FEATURES_PATH, index=False, encoding="utf-8-sig")
    print(f"[00] saved: {cfg.PANEL_PATH}")
    print(f"[00] saved: {cfg.FEATURES_PATH}")


if __name__ == "__main__":
    main()
