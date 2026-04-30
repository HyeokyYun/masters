from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import STL

from src import config as cfg

warnings.filterwarnings("ignore")


def load_raw_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    source = cfg.WEEKLY_PARQUET if cfg.WEEKLY_PARQUET.exists() else cfg.WEEKLY_REDUCED
    ts = pd.read_parquet(source)
    meta = pd.read_csv(cfg.META_CSV)

    ts["public_id"] = ts["public_id"].astype(str)
    meta["public_id"] = meta["public_id"].astype(str)
    ts["date_id"] = pd.to_datetime(ts["date_id"])
    ts.loc[ts["sales_card"] < 0, "sales_card"] = np.nan
    return ts, meta


def _time_alignment(ts: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    keep = [
        c
        for c in (
            "public_id",
            "open_month",
            "delivery_link",
            "business_square_size",
            "classification__kcd_v3__depth_2_name",
            "age",
        )
        if c in meta.columns
    ]
    aligned = meta[keep].copy()
    aligned["open_date"] = pd.to_datetime(
        aligned["open_month"].astype(str), format="%Y-%m", errors="coerce"
    )
    ts = ts.merge(aligned, on="public_id", how="left")
    ts["weeks_since_open"] = ((ts["date_id"] - ts["open_date"]).dt.days // 7).clip(lower=0)
    return ts


def _filter_stores(ts: pd.DataFrame) -> pd.DataFrame:
    ts = ts[ts["open_date"] >= cfg.OPEN_DATE_MIN].copy()
    counts = ts.groupby("public_id")["weeks_since_open"].count()
    keep_ids = counts[counts >= cfg.MIN_WEEKS].index
    return ts[ts["public_id"].isin(keep_ids)].copy()


def _interpolate_sales(ts: pd.DataFrame) -> pd.DataFrame:
    ts = ts.sort_values(["public_id", "weeks_since_open"]).copy()
    ts["sales_card"] = ts.groupby("public_id")["sales_card"].transform(
        lambda x: x.interpolate("linear").ffill().bfill()
    )
    return ts


def _stl_trend(group: pd.DataFrame) -> pd.DataFrame:
    y = group["sales_card"].to_numpy(dtype=float)
    n = len(y)
    period = cfg.STL_PERIOD
    result = group.copy()

    if n >= 2 * period and np.isfinite(y).all():
        try:
            fitted = STL(y, period=period, robust=True).fit()
            result["trend"] = fitted.trend
            result["seasonal"] = fitted.seasonal
            result["resid"] = fitted.resid
            return result
        except Exception:
            pass

    trend = pd.Series(y).rolling(7, min_periods=1, center=True).mean().to_numpy()
    result["trend"] = trend
    result["seasonal"] = 0.0
    result["resid"] = y - trend
    return result


def _apply_stl(ts: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for _, group in ts.groupby("public_id", sort=False):
        parts.append(_stl_trend(group))
    return pd.concat(parts, ignore_index=True)


def _minmax_normalize(ts: pd.DataFrame) -> pd.DataFrame:
    ts = ts.copy()
    for col in ("sales_card", "trend"):
        ts[f"{col}_mm"] = ts.groupby("public_id")[col].transform(
            lambda x: (x - x.min()) / (x.max() - x.min() + 1e-9)
        )
    return ts


def preprocess() -> tuple[pd.DataFrame, pd.DataFrame]:
    ts, meta = load_raw_data()
    ts = _time_alignment(ts, meta)
    ts = _filter_stores(ts)
    ts = _interpolate_sales(ts)
    ts = _apply_stl(ts)
    ts = _minmax_normalize(ts)

    out_path = cfg.TABLE_DIR / "processed_weekly_panel.parquet"
    ts.to_parquet(out_path, index=False)
    print(f"[Step01] 저장 → {out_path.name} ({len(ts):,} rows)")
    return ts, meta
