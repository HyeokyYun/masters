"""
260301 Step 0: original_data 검증

기본 데이터 존재 여부, 행수, 컬럼 확인.
Run from 26-1: python 260301/01_verify_data/run_verify_original_data.py
"""
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = ROOT / "260301" / "outputs" / "tables"
LOG_DIR = ROOT / "260301" / "outputs" / "logs"

# 검증 대상
FILES = {
    "original_data/weekly.parquet": {"required": True, "cols": ["public_id", "sales_card", "customer", "customer_new"]},
    "original_data/weekly_processed.parquet": {"required": True, "cols": ["public_id", "day_after1", "sales_card"]},
    "original_data/meta.csv": {"required": True, "cols": ["public_id", "open_month", "sigungu"]},
    "original_data/meta_processed.csv": {"required": True, "cols": ["public_id", "sigungu", "depth_2"]},
    "basic_data/store_features_for_analysis.csv": {"required": True, "cols": ["public_id", "growth_rate", "new_customer_ratio"]},
    "260204/outputs/data_features_clean.parquet": {"required": True, "cols": ["public_id", "growth_rate"]},
    "260204/outputs/tables/store_cluster_labels_K6.parquet": {"required": True, "cols": ["public_id", "cluster"]},
    "260204_gem/outputs/tables/inflection_p1p2_labels.csv": {"required": True, "cols": ["public_id", "inflection_week"]},
    "260204_gem/outputs/tables/final_code_by_store_260121_outlier_removal.csv": {"required": True, "cols": ["public_id", "final_code"]},
}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "run_verify_original_data.log"

    def log(msg: str):
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    log("=" * 60)
    log("Step 0: original_data 및 의존성 검증")
    log("=" * 60)

    try:
        import pandas as pd
    except ImportError:
        log("ERROR: pandas required")
        return

    results = []
    all_ok = True

    for rel_path, spec in FILES.items():
        path = ROOT / rel_path
        req = spec.get("required", True)
        cols = spec.get("cols", [])

        row = {"file": rel_path, "exists": path.exists(), "rows": None, "cols_ok": None, "status": "OK"}
        if not path.exists():
            row["status"] = "MISSING" if req else "SKIP"
            if req:
                all_ok = False
            results.append(row)
            log(f"  {rel_path}: {'MISSING' if req else 'SKIP'}")
            continue

        try:
            if path.suffix == ".parquet":
                df = pd.read_parquet(path)
                row["rows"] = len(df)
            else:
                df = pd.read_csv(path)
                row["rows"] = len(df)
            missing = [c for c in cols if c not in df.columns]
            row["cols_ok"] = len(missing) == 0
            if missing:
                row["status"] = f"MISSING_COLS: {missing}"
                all_ok = False
            log(f"  {rel_path}: rows={row['rows']}, cols_ok={row['cols_ok']}")
        except Exception as e:
            row["status"] = str(e)
            all_ok = False
            log(f"  {rel_path}: ERROR {e}")
        results.append(row)

    df_out = pd.DataFrame(results)
    df_out.to_csv(OUT_DIR / "verify_original_data_report.csv", index=False, encoding="utf-8-sig")
    log(f"Saved {OUT_DIR / 'verify_original_data_report.csv'}")

    log("=" * 60)
    log("검증 완료." if all_ok else "일부 파일 누락/오류. 검토 필요.")
    log("=" * 60)
    return all_ok


if __name__ == "__main__":
    main()
