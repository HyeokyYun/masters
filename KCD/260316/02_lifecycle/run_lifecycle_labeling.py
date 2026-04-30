from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "260316" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from research_pipeline.config import get_work_dir, load_config
from research_pipeline.io_utils import build_logger, ensure_layout, save_csv
from research_pipeline.lifecycle import build_lifecycle_bundle


def main() -> None:
    work_dir = get_work_dir()
    cfg = load_config()
    ensure_layout(work_dir)
    log = build_logger(work_dir / "outputs" / "logs" / "run_lifecycle_labeling.log")

    log("260316 Step 2: lifecycle labeling")
    bundle = build_lifecycle_bundle(cfg, log)

    save_csv(bundle["labels"], work_dir / "outputs" / "tables" / "store_lifecycle_labels.csv")
    save_csv(bundle["analysis_table"], work_dir / "outputs" / "tables" / "lifecycle_analysis_table.csv")
    save_csv(bundle["distribution"], work_dir / "outputs" / "tables" / "lifecycle_distribution.csv")
    log("Step 2 completed.")


if __name__ == "__main__":
    main()
