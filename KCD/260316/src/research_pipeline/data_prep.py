from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, Dict

import numpy as np
import pandas as pd

from research_pipeline.config import get_repo_root

SALES_COMPONENTS = ["sales_card", "sales_invoice", "sales_delivery"]
PURCHASE_COMPONENTS = ["purchase_card", "purchase_invoice"]
META_RENAME_MAP = {
    "classification__kcd_v3__depth_1_name": "depth_1",
    "classification__kcd_v3__depth_2_name": "depth_2",
    "classification__kcd_v3__depth_3_name": "depth_3",
}


def _linear_slope(values: np.ndarray) -> float:
    arr = np.asarray(values, dtype=float)
    mask = np.isfinite(arr)
    arr = arr[mask]
    if arr.size < 2:
        return np.nan
    x = np.arange(arr.size, dtype=float)
    x = x - x.mean()
    y = arr - arr.mean()
    denom = float(np.dot(x, x))
    return float(np.dot(x, y) / denom) if denom else 0.0


def _safe_ratio(numerator: float, denominator: float) -> float:
    if pd.isna(numerator) or pd.isna(denominator) or denominator == 0:
        return np.nan
    return float(numerator / denominator)


def _parse_age_bucket(value: object) -> float:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return np.nan
    match = re.search(r"(\d+)", str(value))
    return float(match.group(1)) if match else np.nan


def _months_between(later: pd.Timestamp, earlier: pd.Timestamp) -> float:
    if pd.isna(later) or pd.isna(earlier):
        return np.nan
    return float((later.year - earlier.year) * 12 + (later.month - earlier.month))


def load_raw_data(cfg: Dict[str, object], log: Callable[[str], None]) -> tuple[pd.DataFrame, pd.DataFrame]:
    root = get_repo_root()
    weekly_path = root / cfg["data"]["weekly_parquet"]
    meta_path = root / cfg["data"]["meta_csv"]
    log(f"Loading weekly data: {weekly_path}")
    weekly = pd.read_parquet(weekly_path)
    log(f"Loading meta data: {meta_path}")
    meta = pd.read_csv(meta_path)
    return weekly, meta


def prepare_weekly_panel(weekly: pd.DataFrame, meta: pd.DataFrame, cfg: Dict[str, object]) -> pd.DataFrame:
    analysis_cfg = cfg["analysis"]
    min_weeks = int(analysis_cfg["min_weeks"])

    weekly = weekly.copy()
    meta = meta.copy().rename(columns=META_RENAME_MAP)

    weekly["public_id"] = weekly["public_id"].astype(str)
    meta["public_id"] = meta["public_id"].astype(str)
    weekly["date_id"] = pd.to_datetime(weekly["date_id"], errors="coerce")
    meta["open_month"] = pd.to_datetime(meta["open_month"], errors="coerce")

    for col in SALES_COMPONENTS + PURCHASE_COMPONENTS + ["customer", "customer_new"]:
        if col in weekly.columns:
            weekly[col] = pd.to_numeric(weekly[col], errors="coerce")

    weekly = weekly.sort_values(["public_id", "date_id"]).reset_index(drop=True)

    sales_total = sum(weekly.get(col, 0).fillna(0.0) for col in SALES_COMPONENTS if col in weekly.columns)
    purchase_total = sum(weekly.get(col, 0).fillna(0.0) for col in PURCHASE_COMPONENTS if col in weekly.columns)
    weekly["sales_total"] = sales_total
    weekly["purchase_total"] = purchase_total
    weekly["customer_new_ratio_week"] = weekly["customer_new"] / weekly["customer"].replace(0, np.nan)
    weekly["week_index"] = weekly.groupby("public_id").cumcount()

    keep_meta = [
        "public_id",
        "sido",
        "sigungu",
        "dong",
        "address",
        "business_square_size",
        "delivery_link",
        "depth_1",
        "depth_2",
        "depth_3",
        "age",
        "open_month",
        "kostat_class_code",
        "kostat_class",
    ]
    keep_meta = [col for col in keep_meta if col in meta.columns]
    panel = weekly.merge(meta[keep_meta], on="public_id", how="left")

    panel["age_numeric"] = panel["age"].map(_parse_age_bucket)
    panel["weeks_since_open"] = ((panel["date_id"] - panel["open_month"]).dt.days / 7.0).clip(lower=0)

    def _minmax(series: pd.Series) -> pd.Series:
        valid = series.astype(float)
        span = valid.max() - valid.min()
        if pd.isna(span) or span == 0:
            return pd.Series(np.zeros(len(valid)), index=series.index)
        return (valid - valid.min()) / span

    panel["sales_minmax"] = panel.groupby("public_id")["sales_total"].transform(_minmax)
    coverage = panel.groupby("public_id").agg(total_weeks=("week_index", "count")).reset_index()
    valid_ids = coverage.loc[coverage["total_weeks"] >= min_weeks, "public_id"]
    panel = panel[panel["public_id"].isin(valid_ids)].copy()
    return panel


def slice_panel_by_week(panel: pd.DataFrame, start_week: int = 0, end_week: int | None = None) -> pd.DataFrame:
    out = panel[panel["week_index"] >= start_week]
    if end_week is not None:
        out = out[out["week_index"] < end_week]
    return out.copy()


def summarize_store_panel(panel: pd.DataFrame, min_weeks: int = 8) -> pd.DataFrame:
    work = panel.copy().sort_values(["public_id", "date_id"])
    counts = work.groupby("public_id")["week_index"].count()
    valid_ids = counts[counts >= min_weeks].index
    work = work[work["public_id"].isin(valid_ids)].copy()

    records = []
    for public_id, group in work.groupby("public_id"):
        group = group.sort_values("date_id")
        sales = group["sales_total"].fillna(0.0).to_numpy(dtype=float)
        sales = np.clip(sales, a_min=0.0, a_max=None)
        customers = group["customer"].fillna(0.0).to_numpy(dtype=float)
        purchase = group["purchase_total"].fillna(0.0).to_numpy(dtype=float)
        total_sales = float(sales.sum())
        total_purchase = float(purchase.sum())
        n = len(group)
        edge = min(12, max(4, n // 4))
        first_sales = sales[:edge]
        last_sales = sales[-edge:]
        mean_sales = float(np.mean(sales)) if n else np.nan
        std_sales = float(np.std(sales, ddof=1)) if n > 1 else 0.0
        cv_sales = _safe_ratio(std_sales, mean_sales)
        growth_rate = _safe_ratio(float(np.mean(last_sales)) - float(np.mean(first_sales)), float(np.mean(first_sales)))
        trend_slope = _linear_slope(np.log1p(sales))
        avg_customer = float(np.mean(customers)) if n else np.nan
        std_customer = float(np.std(customers, ddof=1)) if n > 1 else 0.0
        cv_customer = _safe_ratio(std_customer, avg_customer)
        max_sales = float(np.max(sales)) if n else np.nan
        positive_sales = sales[sales > 0]
        min_sales = float(np.min(positive_sales)) if positive_sales.size else 0.0
        max_min_ratio = _safe_ratio(max_sales, min_sales)

        last_date = group["date_id"].max()
        open_month = group["open_month"].iloc[0] if "open_month" in group.columns else pd.NaT
        business_age_months = _months_between(last_date, open_month)

        row = {
            "public_id": public_id,
            "total_weeks": n,
            "avg_sales_total": mean_sales,
            "std_sales_total": std_sales,
            "cv_sales_total": cv_sales,
            "growth_rate": growth_rate,
            "trend_slope": trend_slope,
            "weekend_ratio": float(group["weekend_sales"].fillna(0.0).mean()) if "weekend_sales" in group else np.nan,
            "avg_customer": avg_customer,
            "cv_customer": cv_customer,
            "new_customer_ratio": _safe_ratio(float(group["customer_new"].fillna(0.0).sum()), float(group["customer"].fillna(0.0).sum())),
            "card_ratio": _safe_ratio(float(group["sales_card"].fillna(0.0).sum()), total_sales),
            "invoice_ratio": _safe_ratio(float(group["sales_invoice"].fillna(0.0).sum()), total_sales),
            "delivery_ratio": _safe_ratio(float(group["sales_delivery"].fillna(0.0).sum()), total_sales),
            "before_noon_ratio": float(group["before_noon_sales"].fillna(0.0).mean()) if "before_noon_sales" in group else np.nan,
            "after_noon_ratio": float(group["after_noon_sales"].fillna(0.0).mean()) if "after_noon_sales" in group else np.nan,
            "purchase_to_sales_ratio": _safe_ratio(total_purchase, total_sales),
            "max_sales": max_sales,
            "min_sales": min_sales,
            "max_min_ratio": max_min_ratio,
            "business_square_size": group["business_square_size"].iloc[0] if "business_square_size" in group else np.nan,
            "delivery_link": group["delivery_link"].iloc[0] if "delivery_link" in group else np.nan,
            "age": group["age"].iloc[0] if "age" in group else np.nan,
            "open_month": group["open_month"].iloc[0] if "open_month" in group else pd.NaT,
            "sido": group["sido"].iloc[0] if "sido" in group else np.nan,
            "sigungu": group["sigungu"].iloc[0] if "sigungu" in group else np.nan,
            "dong": group["dong"].iloc[0] if "dong" in group else np.nan,
            "depth_1": group["depth_1"].iloc[0] if "depth_1" in group else np.nan,
            "depth_2": group["depth_2"].iloc[0] if "depth_2" in group else np.nan,
            "depth_3": group["depth_3"].iloc[0] if "depth_3" in group else np.nan,
            "business_age_months": business_age_months,
            "age_numeric": group["age_numeric"].iloc[0] if "age_numeric" in group else np.nan,
            "first_observed_week": int(group["week_index"].min()),
            "last_observed_week": int(group["week_index"].max()),
        }
        records.append(row)

    features = pd.DataFrame(records)
    if features.empty:
        return features

    dong_stats = (
        features.groupby("dong", dropna=False)
        .agg(dong_store_count=("public_id", "count"), dong_avg_sales=("avg_sales_total", "mean"))
        .reset_index()
    )
    sigungu_stats = (
        features.groupby("sigungu", dropna=False)
        .agg(sigungu_store_count=("public_id", "count"), sigungu_avg_sales=("avg_sales_total", "mean"))
        .reset_index()
    )
    features = features.merge(dong_stats, on="dong", how="left")
    features = features.merge(sigungu_stats, on="sigungu", how="left")
    features["business_density"] = features["dong_store_count"] / features["sigungu_store_count"].replace(0, np.nan)

    def _growth_type(value: float) -> str:
        if pd.isna(value):
            return "unknown"
        if value >= 0.05:
            return "growing"
        if value <= -0.05:
            return "declining"
        return "stable"

    features["growth_type"] = features["growth_rate"].map(_growth_type)
    return features


def build_missingness_summary(panel: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    weekly_missing = panel.isna().sum().rename("missing_count").reset_index().rename(columns={"index": "column"})
    weekly_missing["dataset"] = "panel"
    meta_missing = meta.isna().sum().rename("missing_count").reset_index().rename(columns={"index": "column"})
    meta_missing["dataset"] = "meta"
    return pd.concat([weekly_missing, meta_missing], ignore_index=True).sort_values(
        ["dataset", "missing_count"], ascending=[True, False]
    )


def build_coverage_summary(panel: pd.DataFrame) -> pd.DataFrame:
    coverage = panel.groupby("public_id").agg(
        total_weeks=("week_index", "count"),
        start_date=("date_id", "min"),
        end_date=("date_id", "max"),
        avg_sales_total=("sales_total", "mean"),
    )
    return coverage.reset_index()


def build_analysis_inputs(cfg: Dict[str, object], log: Callable[[str], None]) -> Dict[str, pd.DataFrame]:
    weekly, meta = load_raw_data(cfg, log)
    panel = prepare_weekly_panel(weekly, meta, cfg)
    store_features = summarize_store_panel(panel, min_weeks=int(cfg["analysis"]["min_weeks"]))
    missingness = build_missingness_summary(panel, meta)
    coverage = build_coverage_summary(panel)
    log(f"Prepared panel rows: {len(panel):,}")
    log(f"Prepared stores: {store_features['public_id'].nunique():,}")
    return {
        "panel": panel,
        "store_features": store_features,
        "missingness": missingness,
        "coverage": coverage,
    }
