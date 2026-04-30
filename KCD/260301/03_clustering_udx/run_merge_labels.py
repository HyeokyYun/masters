"""
260301 Step 2: Clustering + UDX 라벨 병합

df_base_features + final_code + (선택) cluster K6 병합.
outcome_3 (Growth/Stable/Decline) 생성 — Pattern_label(X/Y/Z) 기준.
Run from 26-1: python 260301/03_clustering_udx/run_merge_labels.py
"""
from pathlib import Path
import pandas as pd
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = ROOT / "260301" / "outputs" / "tables"
LOG_DIR = ROOT / "260301" / "outputs" / "logs"

DF_BASE = ROOT / "260301" / "outputs" / "tables" / "df_base_features.csv"
FINAL_CODE = ROOT / "260204_gem" / "outputs" / "tables" / "final_code_by_store_260121_outlier_removal.csv"
CLUSTER_K6 = ROOT / "260204" / "outputs" / "tables" / "store_cluster_labels_K6.parquet"

# 260301 df_base 없으면 260223/260224 fallback
DF_BASE_FALLBACK = ROOT / "260223" / "outputs" / "tables" / "df_base_features.csv"
if not DF_BASE_FALLBACK.exists():
    DF_BASE_FALLBACK = ROOT / "260224" / "06_final_econometric" / "tables" / "df_base_features.csv"


def map_outcome3(code: str) -> str:
    """Pattern_label(final_code 마지막 글자)로 Growth/Stable/Decline 분류."""
    pattern = code[-1] if isinstance(code, str) and len(code) >= 1 else ""
    if pattern == "X":
        return "Growth"
    if pattern == "Z":
        return "Decline"
    return "Stable"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "run_merge_labels.log"

    def log(msg: str):
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    log("=" * 60)
    log("Step 2: Clustering + UDX 라벨 병합")
    log("=" * 60)

    df_path = DF_BASE if DF_BASE.exists() else DF_BASE_FALLBACK
    if not df_path.exists():
        log(f"ERROR: Run Step 1 first. Not found {df_path}")
        return

    df_base = pd.read_csv(df_path)
    log(f"df_base: {len(df_base)} rows")

    if not FINAL_CODE.exists():
        log(f"ERROR: {FINAL_CODE} not found")
        return

    df_code = pd.read_csv(FINAL_CODE)
    df_code["outcome_3"] = df_code["final_code"].map(map_outcome3)
    log(f"final_code -> outcome_3: {df_code['outcome_3'].value_counts().to_dict()}")

    df = df_base.merge(df_code[["public_id", "final_code", "outcome_3"]], on="public_id", how="inner")
    log(f"Merged: {len(df)} rows")

    if CLUSTER_K6.exists():
        cluster = pd.read_parquet(CLUSTER_K6)
        df = df.drop(columns=["cluster"], errors="ignore")
        df = df.merge(cluster[["public_id", "cluster"]], on="public_id", how="left")
        log(f"Cluster K6 merged")

    out_path = OUT_DIR / "df_for_multinomial_logit.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    log(f"Saved {out_path}")
    log("Step 2 완료.")


if __name__ == "__main__":
    main()
