"""
Step 2: Signal Extraction — df_udx_labels (클러스터·변곡점·UDX) 통합.
Input: 260204 store_cluster_labels_K6, 260204_gem inflection + final_code
Output: 260223/outputs/tables/df_udx_labels.parquet, .csv

Run from 260223: python 02_extract/run_step2_udx_labels.py
"""
from pathlib import Path
import pandas as pd
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
        return {"data": {"id_col": "public_id", "cluster_k6_parquet": "../260204/outputs/tables/store_cluster_labels_K6.parquet", "inflection_csv": "../260204_gem/outputs/tables/inflection_p1p2_labels.csv", "final_code_csv": "../260204_gem/outputs/tables/final_code_by_store_260121_outlier_removal.csv"}}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "run_step2_udx_labels.log"

    def log(msg: str):
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    cfg = load_config()
    data_cfg = cfg.get("data", {})
    id_col = data_cfg.get("id_col", "public_id")

    # Paths (relative to 260223)
    cluster_path = (ROOT / data_cfg.get("cluster_k6_parquet", "../260204/outputs/tables/store_cluster_labels_K6.parquet")).resolve()
    inflection_path = (ROOT / data_cfg.get("inflection_csv", "../260204_gem/outputs/tables/inflection_p1p2_labels.csv")).resolve()
    final_code_path = (ROOT / data_cfg.get("final_code_csv", "../260204_gem/outputs/tables/final_code_by_store_260121_outlier_removal.csv")).resolve()

    # 1) Final code has: public_id, inflection_week, P1_label, P2_label, slope_P1, slope_P2, cluster, Pattern_label, final_code
    if not final_code_path.exists():
        log(f"ERROR: Not found {final_code_path}")
        return
    log(f"Loading {final_code_path}")
    udx = pd.read_csv(final_code_path)
    log(f"  rows={len(udx)}")

    # 2) K-Shape K6 라벨이 있으면 cluster 컬럼 덮어쓰기 (논문 통일)
    if cluster_path.exists():
        k6 = pd.read_parquet(cluster_path)
        if id_col in k6.columns and "cluster" in k6.columns:
            k6 = k6[[id_col, "cluster"]].rename(columns={"cluster": "cluster_K6"})
            udx = udx.drop(columns=["cluster"], errors="ignore")
            udx = udx.merge(k6, on=id_col, how="left")
            udx = udx.rename(columns={"cluster_K6": "cluster"})
            log(f"Merged K-Shape K6 from {cluster_path}; cluster column overwritten.")
    else:
        log("cluster_k6_parquet not found; using cluster from final_code (260121).")

    # 3) Inflection CSV에서 추가 컬럼만 merge (final_code에 이미 inflection_week, P1/P2 있음)
    if inflection_path.exists():
        inf = pd.read_csv(inflection_path)
        extra = [c for c in inf.columns if c != id_col and c not in udx.columns]
        if extra:
            inf_cols = [id_col] + extra
            udx = udx.merge(inf[inf_cols], on=id_col, how="left")
            log(f"Merged extra columns from inflection CSV: {extra}")

    # 4) 저장
    out_parquet = OUT_DIR / "df_udx_labels.parquet"
    out_csv = OUT_DIR / "df_udx_labels.csv"
    udx.to_parquet(out_parquet, index=False)
    udx.to_csv(out_csv, index=False, encoding="utf-8-sig")
    log(f"Saved {out_parquet} and {out_csv} (rows={len(udx)})")
    return udx


if __name__ == "__main__":
    main()
