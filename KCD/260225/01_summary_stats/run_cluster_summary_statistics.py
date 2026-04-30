"""
260225 Step 1: 클러스터별 Summary Statistics (DUX, DUY, 평범, 쇠퇴)

목적: 회귀분석 전에 outcome_4(DUX/DUY/Stable/Decline)별 요약 통계 표 작성.
     "업력이 높은 가게는 DUX보다 평범 클러스터에 많았다" 등 단순 통계 비교.

Y 분류 (final_code 기반):
- DUX: 폭발적 성장
- DUY: 반등/유지형 성장
- Decline: DDZ (쇠퇴)
- Stable: 그 외 (UUZ, UDY, UDX, UUY, UDZ, DDY, UUX, DUZ, DDX 등)

Run from 26-1: python 260225/01_summary_stats/run_cluster_summary_statistics.py
"""
from pathlib import Path
import pandas as pd
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent.parent  # 26-1
OUT_DIR = ROOT / "260225" / "outputs" / "tables"
LOG_DIR = ROOT / "260225" / "outputs" / "logs"

# 입력 경로
FINAL_CODE_CSV = ROOT / "260224" / "03_inflection_udx" / "final_code_by_store_260121_outlier_removal.csv"
BASE_FEATURES_CSV = ROOT / "260224" / "06_final_econometric" / "tables" / "df_base_features.csv"
BASE_FEATURES_FALLBACK = ROOT / "260223" / "outputs" / "tables" / "df_base_features.csv"


def map_final_code_to_outcome4(code: str) -> str:
    """final_code -> outcome_4 (DUX, DUY, Stable, Decline)"""
    if code == "DUX":
        return "DUX"
    if code == "DUY":
        return "DUY"
    if code == "DDZ":
        return "Decline"
    return "Stable"  # UUZ, UDY, UDX, UUY, UDZ, DDY, UUX, DUZ, DDX 등


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "run_cluster_summary_statistics.log"

    def log(msg: str):
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    log("=" * 60)
    log("Step 1: 클러스터별 Summary Statistics (outcome_4)")
    log("=" * 60)

    # 1) final_code 로드
    if not FINAL_CODE_CSV.exists():
        log(f"ERROR: Not found {FINAL_CODE_CSV}")
        return
    df_code = pd.read_csv(FINAL_CODE_CSV)
    df_code["outcome_4"] = df_code["final_code"].map(map_final_code_to_outcome4)
    log(f"final_code -> outcome_4: {df_code['outcome_4'].value_counts().to_dict()}")

    # 2) df_base_features 로드
    if BASE_FEATURES_CSV.exists():
        df_base = pd.read_csv(BASE_FEATURES_CSV)
    elif BASE_FEATURES_FALLBACK.exists():
        df_base = pd.read_csv(BASE_FEATURES_FALLBACK)
    else:
        log(f"ERROR: df_base_features not found")
        return
    log(f"df_base_features: {len(df_base)} rows")

    # 3) 병합 (public_id 기준)
    df = df_base.merge(
        df_code[["public_id", "final_code", "outcome_4"]],
        on="public_id",
        how="inner",
    )
    log(f"Merged: {len(df)} rows")

    # 4) outcome_4별 요약 통계
    num_cols = [
        "business_age_months",
        "new_customer_ratio",
        "cv_sales_card",
        "growth_rate",
        "avg_sales_card",
        "trend_slope",
        "business_density",
        "business_square_size",
    ]
    num_cols = [c for c in num_cols if c in df.columns]

    agg_dict = {c: ["mean", "std", "median", "count"] for c in num_cols}
    summary = df.groupby("outcome_4").agg(agg_dict).round(4)

    # Flatten column names for CSV
    summary_flat = summary.copy()
    summary_flat.columns = [f"{c}_{m}" for c, m in summary.columns]
    summary_flat.to_csv(OUT_DIR / "outcome4_summary_statistics.csv", encoding="utf-8-sig")
    log(f"Saved {OUT_DIR / 'outcome4_summary_statistics.csv'}")

    # 5) 업종(depth_2) 분포
    if "depth_2" in df.columns:
        depth_dist = pd.crosstab(df["outcome_4"], df["depth_2"], normalize="index").round(4)
        depth_dist.to_csv(OUT_DIR / "outcome4_depth2_distribution.csv", encoding="utf-8-sig")
        log(f"Saved {OUT_DIR / 'outcome4_depth2_distribution.csv'}")

    # 6) 논문용 간단 표 (핵심 변수만)
    key_vars = ["business_age_months", "new_customer_ratio", "cv_sales_card", "growth_rate"]
    key_vars = [c for c in key_vars if c in df.columns]
    simple = df.groupby("outcome_4")[key_vars].agg(["mean", "std", "count"])
    simple.to_csv(OUT_DIR / "outcome4_summary_key_vars.csv", encoding="utf-8-sig")
    log(f"Saved {OUT_DIR / 'outcome4_summary_key_vars.csv'}")

    # 7) N by outcome_4
    n_by = df["outcome_4"].value_counts().sort_index()
    n_df = pd.DataFrame({"outcome_4": n_by.index, "n": n_by.values})
    n_df.to_csv(OUT_DIR / "outcome4_counts.csv", index=False, encoding="utf-8-sig")
    log(f"Counts: {n_by.to_dict()}")

    # 8) 병합 데이터 저장 (Step 2 Multinomial Logit 입력용)
    df.to_csv(OUT_DIR / "df_for_multinomial_logit.csv", index=False, encoding="utf-8-sig")
    log(f"Saved {OUT_DIR / 'df_for_multinomial_logit.csv'} (for Step 2)")

    log("Step 1 완료.")


if __name__ == "__main__":
    main()
