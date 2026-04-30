"""Step 01 — 통합 데이터 기반 구축.

weekly.parquet (59,089 stores raw) + meta.csv + features_labeled (50,635 stores panel) 결합.
각 점포의 폐업 여부/생존 시간을 추가하여 생존 분석 · Survivorship 보정 기반 테이블을 만든다.

Output:
  outputs/tables/unified_store_table.parquet  — 점포 단위 통합 테이블
  outputs/tables/closure_summary.csv          — 폐업/생존 요약
  outputs/tables/data_foundation_stats.json   — 기초 통계
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg  # noqa: E402


def load_weekly_summary() -> pd.DataFrame:
    """weekly에서 점포별 첫/마지막 관측 주차, 총 주수, 총 매출을 계산."""
    print("[01] weekly.parquet 로딩 중 ...")
    weekly = pd.read_parquet(cfg.WEEKLY_PATH)
    weekly["public_id"] = weekly["public_id"].astype(str)
    weekly["date_id"] = pd.to_datetime(weekly["date_id"])
    print(f"     rows={len(weekly):,}, stores={weekly['public_id'].nunique():,}")

    g = weekly.groupby("public_id", observed=True)
    summary = pd.DataFrame(
        {
            "first_obs_date": g["date_id"].min(),
            "last_obs_date": g["date_id"].max(),
            "n_weeks_observed": g["date_id"].nunique(),
            "total_sales_card": g["sales_card"].sum(),
            "total_customer": g["customer"].sum(),
        }
    ).reset_index()
    return summary


def load_meta() -> pd.DataFrame:
    meta = pd.read_csv(cfg.META_PATH)
    meta["public_id"] = meta["public_id"].astype(str)
    meta["open_date"] = pd.to_datetime(
        meta["open_month"].astype(str), format="%Y-%m", errors="coerce"
    )
    return meta


def load_features() -> pd.DataFrame:
    feats = pd.read_csv(cfg.FEATURES_PATH)
    feats["public_id"] = feats["public_id"].astype(str)
    return feats


def build_unified_table() -> pd.DataFrame:
    summary = load_weekly_summary()
    meta = load_meta()
    feats = load_features()

    obs_end = pd.Timestamp(cfg.OBSERVATION_END)

    df = summary.merge(meta, on="public_id", how="left")

    df["weeks_since_open_last"] = (
        (df["last_obs_date"] - df["open_date"]).dt.days // 7
    ).clip(lower=0)
    df["weeks_since_open_first"] = (
        (df["first_obs_date"] - df["open_date"]).dt.days // 7
    ).clip(lower=0)

    df["weeks_to_obs_end"] = ((obs_end - df["last_obs_date"]).dt.days // 7).clip(lower=0)
    df["is_closed"] = (df["weeks_to_obs_end"] >= cfg.CLOSURE_CUTOFF_WEEKS).astype(int)
    df["survival_weeks"] = df["weeks_since_open_last"].astype(float)
    df["event_indicator"] = df["is_closed"]

    df = df.merge(feats, on="public_id", how="left", suffixes=("", "_feat"))

    df["in_panel"] = df["outcome_3"].notna().astype(int)

    return df


def main():
    df = build_unified_table()

    out_path = cfg.TABLE_DIR / "unified_store_table.parquet"
    df.to_parquet(out_path, index=False)
    print(f"[01] saved unified table: {out_path} ({len(df):,} rows)")

    closure_summary = (
        df.groupby("is_closed")
        .agg(n_stores=("public_id", "count"), median_weeks=("survival_weeks", "median"))
        .reset_index()
    )
    closure_summary["is_closed"] = closure_summary["is_closed"].map({0: "Survived", 1: "Closed"})
    closure_summary.to_csv(cfg.TABLE_DIR / "closure_summary.csv", index=False, encoding="utf-8-sig")
    print(closure_summary.to_string(index=False))

    stats = {
        "n_stores_total": int(len(df)),
        "n_stores_closed": int(df["is_closed"].sum()),
        "n_stores_survived": int((df["is_closed"] == 0).sum()),
        "closure_rate": float(df["is_closed"].mean()),
        "n_in_panel": int(df["in_panel"].sum()),
        "n_not_in_panel": int((df["in_panel"] == 0).sum()),
        "median_survival_weeks_all": float(df["survival_weeks"].median()),
        "median_survival_weeks_closed": float(
            df.loc[df["is_closed"] == 1, "survival_weeks"].median()
        ),
        "median_survival_weeks_survived": float(
            df.loc[df["is_closed"] == 0, "survival_weeks"].median()
        ),
        "outcome_distribution": df["outcome_3"].value_counts(dropna=True).to_dict()
        if "outcome_3" in df.columns
        else {},
        "outcome_by_closure": (
            df.groupby(["is_closed", "outcome_3"]).size().unstack(fill_value=0).to_dict()
            if "outcome_3" in df.columns
            else {}
        ),
    }

    stats["outcome_distribution"] = {str(k): int(v) for k, v in stats["outcome_distribution"].items()}
    stats["outcome_by_closure"] = {
        str(k): {str(kk): int(vv) for kk, vv in v.items()}
        for k, v in stats["outcome_by_closure"].items()
    }

    with open(cfg.TABLE_DIR / "data_foundation_stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
