"""
Step 1: Data Preprocessing — df_base_features (마스터 테이블) 생성.
Input: store_features_for_analysis.csv (또는 260204 data_features_clean)
Output: 260223/outputs/tables/df_base_features.parquet, .csv

Run from 260223: python 01_preprocess/run_step1_base_features.py
"""
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "configs" / "pipeline.yaml"
OUT_DIR = ROOT / "outputs" / "tables"
LOG_DIR = ROOT / "outputs" / "logs"

try:
    import yaml
    def load_config():
        with open(CONFIG, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
except ImportError:
    def load_config():
        return {"data": {"data_clean_parquet": "../260204/outputs/data_features_clean.parquet", "features_csv": "../basic_data/store_features_for_analysis.csv"}}

# 컬럼: 계량경제·예측에 필요한 기본 피처 (variable_description 기준)
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
    log_path = LOG_DIR / "run_step1_base_features.log"

    def log(msg: str):
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    cfg = load_config()
    data_cfg = cfg.get("data", {})
    proj_root = ROOT / data_cfg.get("project_root", "..")

    # 1) data_features_clean.parquet 우선, 없으면 store_features_for_analysis.csv
    clean_path = (ROOT / data_cfg.get("data_clean_parquet", "../260204/outputs/data_features_clean.parquet")).resolve()
    features_path = (ROOT / data_cfg.get("features_csv", "../basic_data/store_features_for_analysis.csv")).resolve()

    if clean_path.exists():
        log(f"Loading {clean_path}")
        df = pd.read_parquet(clean_path)
    else:
        if not features_path.exists():
            log(f"ERROR: Not found {features_path}")
            return
        log(f"Loading {features_path}")
        df = pd.read_csv(features_path)

    log(f"Loaded rows={len(df)}, cols={len(df.columns)}")

    # 2) 사용할 컬럼만 선택 (있으면 유지)
    num_avail = [c for c in REQUIRED_NUM if c in df.columns]
    cat_avail = [c for c in REQUIRED_CAT if c in df.columns]
    use_cols = list(dict.fromkeys(num_avail + cat_avail))
    # cluster 있으면 유지 (Step 2에서 K6로 덮어쓸 수 있음)
    if "cluster" in df.columns and "cluster" not in use_cols:
        use_cols.append("cluster")
    df = df[use_cols].copy()

    # 3) 핵심 연속 변수 결측 제거 (회귀/예측에 필수)
    key_numeric = ["growth_rate", "new_customer_ratio", "cv_sales_card", "business_age_months"]
    key_numeric = [c for c in key_numeric if c in df.columns]
    if key_numeric:
        before = len(df)
        df = df.dropna(subset=key_numeric)
        log(f"Dropna on {key_numeric}: {before} -> {len(df)} rows")

    # 4) 이상치 완화 (선택): growth_rate, cv_sales_card 상하위 1% 클리핑
    for col in ["growth_rate", "cv_sales_card"]:
        if col not in df.columns:
            continue
        q1, q99 = df[col].quantile([0.01, 0.99])
        df[col] = df[col].clip(q1, q99)
    log("Winsorized growth_rate, cv_sales_card (1%, 99%)")

    # 5) 성장형/쇠퇴형 이진 (논문용): growth_rate >= 1 -> 1(성장), < 1 -> 0(쇠퇴)
    if "growth_rate" in df.columns:
        df["growth_type"] = (df["growth_rate"] >= 1.0).astype(int)
        log(f"growth_type: 1(growth)={df['growth_type'].sum()}, 0(decline)={(df['growth_type']==0).sum()}")

    # 6) 저장
    out_parquet = OUT_DIR / "df_base_features.parquet"
    out_csv = OUT_DIR / "df_base_features.csv"
    df.to_parquet(out_parquet, index=False)
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    log(f"Saved {out_parquet} and {out_csv} (rows={len(df)})")
    return df


if __name__ == "__main__":
    main()
