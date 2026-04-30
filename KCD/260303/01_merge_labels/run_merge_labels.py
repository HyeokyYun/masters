"""
260303 Step 1: Merge labels — life_cycle_category from final_code

Label scheme: Period1 (U/D) + Period2 (U/D) + Pattern (X/Y/Z).
- X = rising (entire period)
- Y = stable/maintaining
- Z = declining

We classify into three categories for Y variable:
  rising     <- Pattern X
  maintaining <- Pattern Y
  declining   <- Pattern Z

Run from 26-1: python 260303/01_merge_labels/run_merge_labels.py
"""
from pathlib import Path
import pandas as pd
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = ROOT / "260303" / "outputs" / "tables"
LOG_DIR = ROOT / "260303" / "outputs" / "logs"

DF_BASE = ROOT / "260301" / "outputs" / "tables" / "df_base_features.csv"
FINAL_CODE = ROOT / "260204_gem" / "outputs" / "tables" / "final_code_by_store_260121_outlier_removal.csv"
CLUSTER_K6 = ROOT / "260204" / "outputs" / "tables" / "store_cluster_labels_K6.parquet"

# Fallback if 260301 df_base not present
DF_BASE_FALLBACK = ROOT / "260223" / "outputs" / "tables" / "df_base_features.csv"


def final_code_to_life_cycle(code: str) -> str:
    """Map final_code (P1+P2+Pattern) to life_cycle_category.
    Pattern is the third character: X=rising, Y=maintaining, Z=declining.
    """
    if not isinstance(code, str) or len(code) < 3:
        return None
    pattern = code[-1].upper()
    if pattern == "X":
        return "rising"
    if pattern == "Y":
        return "maintaining"
    if pattern == "Z":
        return "declining"
    return None


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
    log("260303 Step 1: Merge labels — life_cycle_category (rising/maintaining/declining)")
    log("=" * 60)

    df_path = DF_BASE if DF_BASE.exists() else DF_BASE_FALLBACK
    if not df_path.exists():
        log(f"ERROR: Base features not found. Tried {DF_BASE}, {DF_BASE_FALLBACK}")
        return

    df_base = pd.read_csv(df_path)
    log(f"df_base: {len(df_base)} rows")

    if not FINAL_CODE.exists():
        log(f"ERROR: {FINAL_CODE} not found")
        return

    df_code = pd.read_csv(FINAL_CODE)
    df_code["life_cycle_category"] = df_code["final_code"].map(final_code_to_life_cycle)
    df_code = df_code.dropna(subset=["life_cycle_category"])
    log(f"final_code -> life_cycle_category: {df_code['life_cycle_category'].value_counts().to_dict()}")

    df = df_base.merge(
        df_code[["public_id", "final_code", "Pattern_label", "life_cycle_category"]],
        on="public_id",
        how="inner",
    )
    log(f"Merged: {len(df)} rows")

    if CLUSTER_K6.exists():
        cluster = pd.read_parquet(CLUSTER_K6)
        df = df.drop(columns=["cluster"], errors="ignore")
        df = df.merge(cluster[["public_id", "cluster"]], on="public_id", how="left")
        log("Cluster K6 merged")

    out_path = OUT_DIR / "df_for_life_cycle_regression.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    log(f"Saved {out_path}")
    log("Step 1 완료.")


if __name__ == "__main__":
    main()
