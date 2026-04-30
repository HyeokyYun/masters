from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "260316" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from research_pipeline.config import get_work_dir, load_config
from research_pipeline.data_prep import build_analysis_inputs
from research_pipeline.io_utils import build_logger, ensure_layout, save_csv, save_parquet


def main() -> None:
    work_dir = get_work_dir()
    cfg = load_config()
    ensure_layout(work_dir)
    log = build_logger(work_dir / "outputs" / "logs" / "run_prepare_base_data.log")

    log("260316 Step 1: prepare base panel and store features")
    bundle = build_analysis_inputs(cfg, log)

    save_parquet(bundle["panel"], work_dir / "outputs" / "tables" / "store_week_panel.parquet")
    save_csv(bundle["store_features"], work_dir / "outputs" / "tables" / "store_features_full.csv")
    save_csv(bundle["missingness"], work_dir / "outputs" / "tables" / "missingness_summary.csv")
    save_csv(bundle["coverage"], work_dir / "outputs" / "tables" / "panel_coverage_summary.csv")
    log("Step 1 completed.")


if __name__ == "__main__":
    main()
