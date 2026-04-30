from __future__ import annotations

import numpy as np
import pandas as pd

from src import config as cfg


def _months_between(start: pd.Series, end: pd.Series) -> pd.Series:
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)
    months = (end.dt.year - start.dt.year) * 12 + (end.dt.month - start.dt.month)
    return months.astype(float)


def _load_labeled_features() -> pd.DataFrame:
    df = pd.read_csv(cfg.PRIOR_LABELED)
    df["public_id"] = df["public_id"].astype(str)
    df["outcome_3"] = df["label"].astype(str).str[-1].map(cfg.OUTCOME_MAP)
    return df


def _load_meta() -> pd.DataFrame:
    meta = pd.read_csv(cfg.META_CSV)
    meta["public_id"] = meta["public_id"].astype(str)
    meta["open_date"] = pd.to_datetime(meta["open_month"].astype(str), format="%Y-%m", errors="coerce")
    meta["category_from_meta"] = meta["classification__kcd_v3__depth_2_name"].apply(cfg.classify_industry)
    meta["delivery_link"] = pd.to_numeric(meta["delivery_link"], errors="coerce")
    meta["business_square_size"] = pd.to_numeric(meta["business_square_size"], errors="coerce")
    return meta


def _load_weekly_bounds(public_ids: set[str]) -> pd.DataFrame:
    weekly = pd.read_parquet(cfg.get_weekly_path(), columns=["public_id", "date_id"])
    weekly["public_id"] = weekly["public_id"].astype(str)
    weekly["date_id"] = pd.to_datetime(weekly["date_id"])
    weekly = weekly[weekly["public_id"].isin(public_ids)].copy()
    bounds = (
        weekly.groupby("public_id", as_index=False)
        .agg(
            first_observed_date=("date_id", "min"),
            last_observed_date=("date_id", "max"),
            observed_weeks=("date_id", "nunique"),
        )
    )
    return bounds


def _build_competition_metrics(meta_sample: pd.DataFrame) -> pd.DataFrame:
    sample = meta_sample.copy()
    sample["dong"] = sample["dong"].fillna("missing_dong")
    sample["category"] = sample["category_from_meta"].fillna("기타")

    dong_total = sample.groupby("dong").size().rename("dong_total_store_count").reset_index()
    dong_category = (
        sample.groupby(["dong", "category"])
        .size()
        .rename("dong_category_store_count")
        .reset_index()
    )

    categories = sorted(sample["category"].dropna().unique().tolist())
    share_specs = {
        f"share_cat_{cfg.category_to_slug(category)}_in_dong": category
        for category in categories
    }
    share_tables = []
    for column, category in share_specs.items():
        table = (
            sample.assign(flag=(sample["category"] == category).astype(int))
            .groupby("dong", as_index=False)["flag"]
            .mean()
            .rename(columns={"flag": column})
        )
        share_tables.append(table)

    merged = sample.merge(dong_total, on="dong", how="left")
    merged = merged.merge(dong_category, on=["dong", "category"], how="left")
    for table in share_tables:
        merged = merged.merge(table, on="dong", how="left")

    merged["local_same_category_share"] = (
        merged["dong_category_store_count"] / merged["dong_total_store_count"].replace(0, np.nan)
    )
    merged["dong_total_store_count"] = merged["dong_total_store_count"].fillna(0)
    merged["dong_category_store_count"] = merged["dong_category_store_count"].fillna(0)

    # Backward-compatible aliases used by prior reporting code.
    merged["fastfood_share_in_dong"] = merged.get("share_cat_fastfood_in_dong", 0.0)
    merged["cafe_share_in_dong"] = merged.get("share_cat_cafe_in_dong", 0.0)
    merged["pub_share_in_dong"] = merged.get("share_cat_pub_in_dong", 0.0)

    keep = [
        "public_id",
        "dong_total_store_count",
        "dong_category_store_count",
        "local_same_category_share",
        "fastfood_share_in_dong",
        "cafe_share_in_dong",
        "pub_share_in_dong",
    ] + list(share_specs.keys())
    return merged[keep].drop_duplicates("public_id")


def build_base_dataset() -> pd.DataFrame:
    labeled = _load_labeled_features()
    meta = _load_meta()
    meta_sample = meta[meta["public_id"].isin(labeled["public_id"])].copy()
    weekly_bounds = _load_weekly_bounds(set(labeled["public_id"]))
    competition = _build_competition_metrics(meta_sample)

    meta_keep = meta_sample[
        [
            "public_id",
            "sido",
            "sigungu",
            "dong",
            "address",
            "business_square_size",
            "delivery_link",
            "classification__kcd_v3__depth_2_name",
            "classification__kcd_v3__depth_3_name",
            "age",
            "open_month",
            "open_date",
            "category_from_meta",
        ]
    ].copy()

    base = labeled.merge(meta_keep, on="public_id", how="left")
    base = base.merge(weekly_bounds, on="public_id", how="left")
    base = base.merge(competition, on="public_id", how="left")

    base["category"] = base["category"].fillna(base["category_from_meta"]).fillna("기타")
    base["business_age_months"] = _months_between(base["open_date"], base["last_observed_date"])
    base["age_bucket"] = pd.cut(
        base["business_age_months"],
        bins=cfg.AGE_BUCKET_BINS,
        labels=cfg.AGE_BUCKET_LABELS,
        right=True,
        include_lowest=True,
    )
    base["is_early_store"] = (base["business_age_months"] <= cfg.EARLY_STORE_MONTHS).astype(int)
    base["is_fastfood"] = (base["category"] == "패스트푸드").astype(int)
    base["is_cafe"] = (base["category"] == "카페").astype(int)
    base["is_pub"] = (base["category"] == "술집").astype(int)
    base["delivery_link"] = base["delivery_link"].fillna(0).clip(lower=0)
    base["local_same_category_share"] = base["local_same_category_share"].fillna(base["local_same_category_share"].median())
    base["fastfood_share_in_dong"] = base["fastfood_share_in_dong"].fillna(0)
    base["cafe_share_in_dong"] = base["cafe_share_in_dong"].fillna(0)
    base["pub_share_in_dong"] = base["pub_share_in_dong"].fillna(0)
    for category, slug in cfg.CATEGORY_SLUGS.items():
        column = f"share_cat_{slug}_in_dong"
        if column in base.columns:
            base[column] = base[column].fillna(0)

    base.to_csv(cfg.TABLE_DIR / "base_dataset.csv", index=False, encoding="utf-8-sig")

    diagnostics = pd.DataFrame(
        [
            {"item": "sample_rows", "value": float(len(base))},
            {"item": "unique_stores", "value": float(base["public_id"].nunique())},
            {"item": "missing_open_date_rate", "value": float(base["open_date"].isna().mean())},
            {"item": "missing_dong_rate", "value": float(base["dong"].isna().mean())},
            {"item": "early_store_rate", "value": float(base["is_early_store"].mean())},
        ]
    )
    diagnostics.to_csv(cfg.TABLE_DIR / "base_dataset_diagnostics.csv", index=False, encoding="utf-8-sig")

    return base
