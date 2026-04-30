from __future__ import annotations

import pandas as pd

from src import config as cfg


FULL_AGE_BUCKET_BINS = [0.0, 6.0, 12.0, 24.0, 36.0, 60.0, 120.0, 10_000.0]
FULL_AGE_BUCKET_LABELS = ["0_6m", "6_12m", "12_24m", "24_36m", "36_60m", "60_120m", "120m_plus"]


def _load_full_meta() -> pd.DataFrame:
    meta = pd.read_csv(cfg.META_CSV, usecols=["public_id", "open_month"])
    meta["public_id"] = meta["public_id"].astype(str)
    meta["open_date"] = pd.to_datetime(meta["open_month"].astype(str), format="%Y-%m", errors="coerce")
    return meta


def _load_reference_date() -> pd.Timestamp:
    weekly = pd.read_parquet(cfg.get_weekly_path(), columns=["date_id"])
    return pd.to_datetime(weekly["date_id"]).max()


def run_full_business_age_analysis() -> pd.DataFrame:
    meta = _load_full_meta()
    reference_date = _load_reference_date()
    labeled = pd.read_csv(cfg.PRIOR_LABELED, usecols=["public_id"])
    labeled["public_id"] = labeled["public_id"].astype(str)
    labeled_ids = set(labeled["public_id"])

    meta["full_business_age_months"] = (
        (reference_date.year - meta["open_date"].dt.year) * 12
        + (reference_date.month - meta["open_date"].dt.month)
    )
    meta = meta[meta["open_date"].notna()].copy()
    meta = meta[meta["full_business_age_months"] >= 0].copy()
    meta["open_year"] = meta["open_date"].dt.year.astype("Int64")
    meta["in_analysis_sample"] = meta["public_id"].isin(labeled_ids).astype(int)
    meta["full_age_bucket"] = pd.cut(
        meta["full_business_age_months"],
        bins=FULL_AGE_BUCKET_BINS,
        labels=FULL_AGE_BUCKET_LABELS,
        right=True,
        include_lowest=True,
    )

    summary = pd.DataFrame(
        [
            {"item": "reference_date", "value": str(reference_date.date())},
            {"item": "full_meta_store_count", "value": float(meta["public_id"].nunique())},
            {"item": "analysis_sample_count", "value": float(meta["in_analysis_sample"].sum())},
            {"item": "full_age_months_median", "value": float(meta["full_business_age_months"].median())},
            {"item": "full_age_months_mean", "value": float(meta["full_business_age_months"].mean())},
        ]
    )
    summary.to_csv(cfg.TABLE_DIR / "full_business_age_summary.csv", index=False, encoding="utf-8-sig")

    bucket_summary = (
        meta.groupby("full_age_bucket", observed=False)
        .size()
        .rename("store_count")
        .reset_index()
    )
    bucket_summary["store_share"] = bucket_summary["store_count"] / bucket_summary["store_count"].sum()
    bucket_summary.to_csv(cfg.TABLE_DIR / "full_business_age_bucket_summary.csv", index=False, encoding="utf-8-sig")

    inclusion_summary = (
        meta.groupby("full_age_bucket", observed=False)
        .agg(
            full_store_count=("public_id", "count"),
            analysis_sample_count=("in_analysis_sample", "sum"),
            inclusion_rate=("in_analysis_sample", "mean"),
        )
        .reset_index()
    )
    inclusion_summary.to_csv(cfg.TABLE_DIR / "full_age_sample_inclusion_summary.csv", index=False, encoding="utf-8-sig")

    open_year_summary = (
        meta.groupby("open_year", dropna=False)
        .agg(
            full_store_count=("public_id", "count"),
            analysis_sample_count=("in_analysis_sample", "sum"),
        )
        .reset_index()
        .sort_values("open_year")
    )
    open_year_summary["inclusion_rate"] = (
        open_year_summary["analysis_sample_count"] / open_year_summary["full_store_count"]
    )
    open_year_summary.to_csv(cfg.TABLE_DIR / "full_business_age_open_year_summary.csv", index=False, encoding="utf-8-sig")

    cfg.set_korean_font()
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(15, 5))

    axes[0].hist(meta["full_business_age_months"], bins=40, color="#2a6f97", edgecolor="white")
    axes[0].axvline(meta["full_business_age_months"].median(), color="red", linestyle="--", label="중앙값")
    axes[0].set_title("전체 업장 업력 분포")
    axes[0].set_xlabel("Business age (months)")
    axes[0].set_ylabel("Store count")
    axes[0].legend()

    axes[1].bar(inclusion_summary["full_age_bucket"].astype(str), inclusion_summary["inclusion_rate"], color="#cc5a71")
    axes[1].set_title("전체 업력 구간별 분석 표본 포함률")
    axes[1].set_xlabel("Full-age bucket")
    axes[1].set_ylabel("Inclusion rate")
    axes[1].tick_params(axis="x", rotation=25)

    plt.tight_layout()
    plt.savefig(cfg.FIGURE_DIR / "full_business_age_overview.png", dpi=150)
    plt.close(fig)

    note = f"""# 전체 업력 분석 메모

- 기준일: {reference_date.date()}
- 전체 meta 업장 수: {meta['public_id'].nunique():,}
- 현재 분석 표본 포함 업장 수: {int(meta['in_analysis_sample'].sum()):,}

## 해석 원칙

1. `full_business_age_months`는 전체 업장을 기준으로 계산한 진짜 업력입니다.
2. 반면 기존 `business_age_months`는 현재 분석 표본(최근 개업 + usable series 확보) 내부의 상대적 경과기간에 가깝습니다.
3. 따라서 발표에서는 `전체 업력 분석`과 `분석 표본 내부의 초기 단계 업력 분석`을 반드시 구분해서 설명해야 합니다.
"""
    with open(cfg.DOC_DIR / "full_business_age_note.md", "w", encoding="utf-8") as handle:
        handle.write(note)

    meta.to_csv(cfg.TABLE_DIR / "full_business_age_table.csv", index=False, encoding="utf-8-sig")
    return meta
