"""
Step 2: 동 단위 업종 밀도(경쟁 지표) + meta 연령 병합 + 추세 잔차 CV 병합

- dens_{업종}: 해당 동에서 해당 depth_2 점포 수 / 동 전체 점포 수
- 상호작용용: 각 더미와 해당 dens 곱은 run_03에서 생성 가능하도록 dens 컬럼 유지

Run from 26-1: ./.venv/bin/python 260320_codex/run_02_build_extended_dataset.py
"""
import re
import pandas as pd
import numpy as np
from datetime import datetime

from config import META_CSV, OUT_DIR, LOG_DIR, TOP_DEPTH2_FOR_DUMMY, resolve_multinom_path


def _parse_age_to_numeric(val) -> float:
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    if s in ("", "nan", "None"):
        return np.nan
    band = {"10대": 15, "20대": 25, "30대": 35, "40대": 45, "50대": 55, "60대": 65, "60대 이상": 68}
    if s in band:
        return float(band[s])
    # 생년월일 형태
    if re.match(r"^\d{4}-\d{2}$", s):
        try:
            y = int(s[:4])
            return float(2023 - y)  # 기준 연도는 논문 설정에 맞게 조정 가능
        except Exception:
            return np.nan
    try:
        return float(s)
    except Exception:
        return np.nan


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "run_02_build_extended_dataset.log"

    def log(msg: str):
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    df_path = resolve_multinom_path()
    if not df_path.exists():
        log(f"ERROR: {df_path} not found")
        return

    df = pd.read_csv(df_path)
    log(f"Loaded merged: {len(df)} rows")

    # outcome: prefer outcome_3
    if "outcome_3" not in df.columns and "life_cycle_category" in df.columns:
        m = {"rising": "Growth", "maintaining": "Stable", "declining": "Decline"}
        df["outcome_3"] = df["life_cycle_category"].map(m)
    if "outcome_3" not in df.columns:
        log("WARN: outcome_3 missing; need 260301 Step 2 merge")

    # 동×depth_2 밀도
    if "dong" not in df.columns or "depth_2" not in df.columns:
        log("ERROR: dong or depth_2 missing")
        return

    dong_n = df.groupby("dong").size().reset_index(name="dong_store_n")
    dc = df.groupby(["dong", "depth_2"]).size().reset_index(name="cohort_n")
    dc = dc.merge(dong_n, on="dong")
    dc["dens_this_depth_in_dong"] = dc["cohort_n"] / dc["dong_store_n"]

    df = df.merge(
        dc[["dong", "depth_2", "dens_this_depth_in_dong", "cohort_n"]],
        on=["dong", "depth_2"],
        how="left",
    )

    # 주요 업종별 동 밀도 (동 단위로 병합) — 상호작용 term용
    for name in TOP_DEPTH2_FOR_DUMMY:
        dsub = dc[dc["depth_2"] == name][["dong", "cohort_n"]].merge(dong_n, on="dong")
        dsub[f"dens_{name}"] = dsub["cohort_n"] / dsub["dong_store_n"]
        dsub = dsub[["dong", f"dens_{name}"]].drop_duplicates("dong")
        df = df.merge(dsub, on="dong", how="left")

    # meta 연령
    if META_CSV.exists():
        meta = pd.read_csv(META_CSV)
        if "age" not in meta.columns:
            log("WARN: meta has no age column")
            df["owner_age_numeric"] = np.nan
        else:
            meta["owner_age_numeric"] = meta["age"].map(_parse_age_to_numeric)
            df = df.merge(meta[["public_id", "owner_age_numeric"]], on="public_id", how="left")
            log(f"Merged owner_age_numeric; non-null: {df['owner_age_numeric'].notna().sum()}")
    else:
        log("WARN: meta.csv not found")
        df["owner_age_numeric"] = np.nan

    # 추세 잔차 CV
    trend_path = OUT_DIR / "store_trend_residual_cv.csv"
    if trend_path.exists():
        tr = pd.read_csv(trend_path)
        df = df.merge(tr, on="public_id", how="left")
        log("Merged store_trend_residual_cv.csv")
    else:
        log("WARN: store_trend_residual_cv.csv not found — run run_01 first")

    out = OUT_DIR / "df_extended_for_regression.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    log(f"Saved {out} ({len(df)} rows, {len(df.columns)} cols)")
    log("Done.")


if __name__ == "__main__":
    main()
