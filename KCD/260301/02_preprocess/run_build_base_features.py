"""
260301 Step 1: Base features (df_base_features) 생성

260204 data_features_clean 또는 basic_data에서 로드 후 df_base_features 규격으로 저장.
결측 제거, Winsorize, growth_type 생성.
Run from 26-1: python 260301/02_preprocess/run_build_base_features.py
"""
from pathlib import Path
import pandas as pd
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = ROOT / "260301" / "outputs" / "tables"
LOG_DIR = ROOT / "260301" / "outputs" / "logs"

DATA_CLEAN = ROOT / "260204" / "outputs" / "data_features_clean.parquet"
FEATURES_CSV = ROOT / "basic_data" / "store_features_for_analysis.csv"

REQUIRED_NUM = [
    "public_id", "growth_rate", "new_customer_ratio", "cv_sales_card",
    "business_age_months", "business_density", "business_square_size",
    "avg_sales_card", "std_sales_card", "trend_slope", "total_weeks",
    "weekend_ratio", "avg_customer", "card_ratio", "delivery_ratio",
    "max_sales", "min_sales", "max_min_ratio",
    "dong_store_count", "dong_avg_sales", "sigungu_store_count", "sigungu_avg_sales",
]
REQUIRED_CAT = ["sigungu", "depth_1", "depth_2", "depth_3", "dong"]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "run_build_base_features.log"

    def log(msg: str):
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    log("=" * 60)
    log("Step 1: Base features (df_base_features)")
    log("=" * 60)

    if DATA_CLEAN.exists():
        log(f"Loading {DATA_CLEAN}")
        df = pd.read_parquet(DATA_CLEAN)
    elif FEATURES_CSV.exists():
        log(f"Loading {FEATURES_CSV}")
        df = pd.read_csv(FEATURES_CSV)
    else:
        log(f"ERROR: Neither {DATA_CLEAN} nor {FEATURES_CSV} found")
        return

    log(f"Loaded: {len(df)} rows, {len(df.columns)} cols")

    use_cols = [c for c in REQUIRED_NUM + REQUIRED_CAT if c in df.columns]
    df = df[use_cols].copy()

    key_numeric = ["growth_rate", "new_customer_ratio", "cv_sales_card", "business_age_months"]
    key_numeric = [c for c in key_numeric if c in df.columns]
    before = len(df)
    df = df.dropna(subset=key_numeric)
    log(f"Dropna on {key_numeric}: {before} -> {len(df)}")

    for col in ["growth_rate", "cv_sales_card"]:
        if col in df.columns:
            q1, q99 = df[col].quantile([0.01, 0.99])
            df[col] = df[col].clip(q1, q99)
    log("Winsorized growth_rate, cv_sales_card (1%, 99%)")

    df["growth_type"] = (df["growth_rate"] >= 1.0).astype(int)
    log(f"growth_type: 1={df['growth_type'].sum()}, 0={(df['growth_type']==0).sum()}")

    out_csv = OUT_DIR / "df_base_features.csv"
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    log(f"Saved {out_csv}")
    log("Step 1 완료.")


if __name__ == "__main__":
    main()
