from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src import config as cfg


@dataclass
class BaseArtifacts:
    base_df: pd.DataFrame
    diagnostics_df: pd.DataFrame


def _months_between(start: pd.Series, end: pd.Series) -> pd.Series:
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)
    months = (end.dt.year - start.dt.year) * 12 + (end.dt.month - start.dt.month)
    return months.astype(float)


def _parse_owner_age(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).str.strip()
    mapped = cleaned.map(cfg.AGE_BAND_TO_NUMERIC)
    return mapped.astype(float)


def _find_owner_gender_column(meta: pd.DataFrame) -> str | None:
    candidates = [
        "gender",
        "sex",
        "owner_gender",
        "representative_gender",
        "ceo_gender",
        "male_female",
    ]
    for column in meta.columns:
        lower = column.lower()
        if column in candidates or "gender" in lower or "sex" in lower:
            return column
    return None


def _load_labeled_features() -> pd.DataFrame:
    df = pd.read_csv(cfg.PRIOR_LABELED)
    df["public_id"] = df["public_id"].astype(str)
    df["trajectory_code"] = df["label"].astype(str).str[:2]
    df["outcome_3"] = df["label"].astype(str).str[-1].map(cfg.OUTCOME_MAP)
    return df


def _load_meta() -> pd.DataFrame:
    meta = pd.read_csv(cfg.META_CSV)
    meta["public_id"] = meta["public_id"].astype(str)
    meta["open_date"] = pd.to_datetime(meta["open_month"].astype(str), format="%Y-%m", errors="coerce")
    meta["category_from_meta"] = meta["classification__kcd_v3__depth_2_name"].apply(cfg.classify_industry)
    meta["owner_age_numeric"] = _parse_owner_age(meta["age"])
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
            observed_weeks_raw=("date_id", "nunique"),
        )
    )
    return bounds


def _build_competition_metrics(meta_sample: pd.DataFrame) -> pd.DataFrame:
    sample = meta_sample.copy()
    sample["category_for_density"] = sample["category_from_meta"].fillna("기타")

    dong_total = (
        sample.groupby("dong")
        .size()
        .rename("dong_total_store_count")
        .reset_index()
    )
    dong_category = (
        sample.groupby(["dong", "category_for_density"])
        .size()
        .rename("dong_category_store_count")
        .reset_index()
    )
    fastfood_share = (
        sample.assign(is_fastfood=(sample["category_for_density"] == "패스트푸드").astype(int))
        .groupby("dong", as_index=False)["is_fastfood"]
        .mean()
        .rename(columns={"is_fastfood": "fastfood_share_in_dong"})
    )
    cafe_share = (
        sample.assign(is_cafe=(sample["category_for_density"] == "카페").astype(int))
        .groupby("dong", as_index=False)["is_cafe"]
        .mean()
        .rename(columns={"is_cafe": "cafe_share_in_dong"})
    )
    pub_share = (
        sample.assign(is_pub=(sample["category_for_density"] == "술집").astype(int))
        .groupby("dong", as_index=False)["is_pub"]
        .mean()
        .rename(columns={"is_pub": "pub_share_in_dong"})
    )

    merged = sample.merge(dong_total, on="dong", how="left")
    merged = merged.merge(
        dong_category,
        on=["dong", "category_for_density"],
        how="left",
    )
    merged = merged.merge(fastfood_share, on="dong", how="left")
    merged = merged.merge(cafe_share, on="dong", how="left")
    merged = merged.merge(pub_share, on="dong", how="left")
    merged["local_same_category_share"] = (
        merged["dong_category_store_count"] / merged["dong_total_store_count"].replace(0, np.nan)
    )
    keep = [
        "public_id",
        "dong_total_store_count",
        "dong_category_store_count",
        "local_same_category_share",
        "fastfood_share_in_dong",
        "cafe_share_in_dong",
        "pub_share_in_dong",
    ]
    return merged[keep].drop_duplicates("public_id")


def build_base_dataset() -> BaseArtifacts:
    labeled = _load_labeled_features()
    meta = _load_meta()
    weekly_bounds = _load_weekly_bounds(set(labeled["public_id"]))
    meta_sample = meta[meta["public_id"].isin(labeled["public_id"])].copy()
    competition = _build_competition_metrics(meta_sample)

    owner_gender_column = _find_owner_gender_column(meta_sample)
    if owner_gender_column is None:
        owner_gender = pd.Series([np.nan] * len(meta_sample), index=meta_sample.index)
    else:
        owner_gender = meta_sample[owner_gender_column]

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
            "owner_age_numeric",
            "open_month",
            "open_date",
            "category_from_meta",
        ]
    ].copy()
    meta_keep["owner_gender"] = owner_gender

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
    base["is_very_early_store"] = (base["business_age_months"] <= cfg.VERY_EARLY_STORE_MONTHS).astype(int)
    base["is_early_store"] = (base["business_age_months"] <= cfg.EARLY_STORE_MONTHS).astype(int)
    base["is_fastfood"] = (base["category"] == "패스트푸드").astype(int)
    base["is_cafe"] = (base["category"] == "카페").astype(int)
    base["is_pub"] = (base["category"] == "술집").astype(int)
    base["owner_age_missing"] = base["owner_age_numeric"].isna().astype(int)
    base["owner_gender_missing"] = base["owner_gender"].isna().astype(int)
    base["business_square_size_missing"] = base["business_square_size"].isna().astype(int)

    diagnostics = pd.DataFrame(
        [
            {"item": "sample_rows", "value": float(len(base))},
            {"item": "unique_stores", "value": float(base["public_id"].nunique())},
            {"item": "missing_owner_age_rate", "value": float(base["owner_age_numeric"].isna().mean())},
            {"item": "missing_owner_gender_rate", "value": float(base["owner_gender"].isna().mean())},
            {"item": "missing_square_size_rate", "value": float(base["business_square_size"].isna().mean())},
            {"item": "owner_gender_column_found", "value": float(owner_gender_column is not None)},
        ]
    )

    base.to_csv(cfg.TABLE_DIR / "meeting_base_dataset.csv", index=False, encoding="utf-8-sig")
    diagnostics.to_csv(cfg.TABLE_DIR / "data_availability_diagnostics.csv", index=False, encoding="utf-8-sig")
    return BaseArtifacts(base_df=base, diagnostics_df=diagnostics)
