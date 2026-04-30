from __future__ import annotations

import numpy as np
import pandas as pd

from src import config as cfg


def _load_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    weekly = pd.read_parquet(cfg.get_weekly_path())
    meta = pd.read_csv(cfg.META_CSV)
    weekly["public_id"] = weekly["public_id"].astype(str)
    meta["public_id"] = meta["public_id"].astype(str)
    weekly["date_id"] = pd.to_datetime(weekly["date_id"])
    weekly.loc[weekly["sales_card"] < 0, "sales_card"] = np.nan
    return weekly, meta


def _add_meta(weekly: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    keep = [
        "public_id",
        "open_month",
        "delivery_link",
        "business_square_size",
        "classification__kcd_v3__depth_2_name",
        "dong",
    ]
    info = meta[[column for column in keep if column in meta.columns]].copy()
    info["open_date"] = pd.to_datetime(info["open_month"].astype(str), format="%Y-%m", errors="coerce")
    weekly = weekly.merge(info, on="public_id", how="left")
    weekly["category"] = weekly["classification__kcd_v3__depth_2_name"].apply(cfg.classify_industry)
    return weekly


def _filter_observed_window(weekly: pd.DataFrame) -> pd.DataFrame:
    weekly = weekly.sort_values(["public_id", "date_id"]).drop_duplicates(["public_id", "date_id"]).copy()
    observed_counts = weekly.groupby("public_id")["date_id"].nunique()
    keep_ids = observed_counts[observed_counts >= cfg.MIN_OBS_WEEKS].index
    weekly = weekly[weekly["public_id"].isin(keep_ids)].copy()
    weekly["observed_week_idx"] = weekly.groupby("public_id").cumcount()
    weekly = weekly[weekly["observed_week_idx"] < cfg.MAX_OBS_WEEKS].copy()
    return weekly


def _interpolate_sales(weekly: pd.DataFrame) -> pd.DataFrame:
    weekly["sales_card"] = weekly.groupby("public_id")["sales_card"].transform(
        lambda values: values.interpolate("linear").ffill().bfill()
    )
    return weekly


def _apply_trend(group: pd.DataFrame) -> pd.DataFrame:
    group = group.copy()
    y = group["sales_card"].to_numpy(dtype=float)
    group["trend"] = pd.Series(y).rolling(cfg.STL_PERIOD, min_periods=1, center=True).mean().to_numpy()
    group["seasonal"] = 0.0
    group["resid"] = y - group["trend"].to_numpy()
    return group


def prepare_observed_panel() -> pd.DataFrame:
    weekly, meta = _load_raw()
    weekly = _add_meta(weekly, meta)
    weekly = _filter_observed_window(weekly)
    weekly = _interpolate_sales(weekly)

    parts = []
    for _, group in weekly.groupby("public_id", sort=False):
        parts.append(_apply_trend(group))
    weekly = pd.concat(parts, ignore_index=True)

    for column in ("sales_card", "trend"):
        weekly[f"{column}_mm"] = weekly.groupby("public_id")[column].transform(
            lambda values: (values - values.min()) / (values.max() - values.min() + 1e-9)
        )

    weekly.to_parquet(cfg.TABLE_DIR / "observed_window_panel.parquet", index=False)

    diagnostics = pd.DataFrame(
        [
            {"item": "weekly_total_stores", "value": float(meta["public_id"].nunique())},
            {"item": "stores_with_min_obs_weeks", "value": float(weekly["public_id"].nunique())},
            {"item": "reference_date", "value": str(weekly["date_id"].max().date())},
        ]
    )
    diagnostics.to_csv(cfg.TABLE_DIR / "observed_window_panel_diagnostics.csv", index=False, encoding="utf-8-sig")
    return weekly
