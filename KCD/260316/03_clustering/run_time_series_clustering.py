from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "260316" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from research_pipeline.clustering import run_clustering_bundle
from research_pipeline.config import get_work_dir, load_config
from research_pipeline.io_utils import build_logger, ensure_layout, save_csv


def main() -> None:
    work_dir = get_work_dir()
    cfg = load_config()
    ensure_layout(work_dir)
    log = build_logger(work_dir / "outputs" / "logs" / "run_time_series_clustering.log")

    log("260316 Step 3: time-series clustering")
    bundle = run_clustering_bundle(cfg, log)

    save_csv(bundle["labels"], work_dir / "outputs" / "tables" / "trajectory_cluster_labels.csv")
    save_csv(bundle["profiles"], work_dir / "outputs" / "tables" / "trajectory_cluster_profiles.csv")
    save_csv(bundle["centers"], work_dir / "outputs" / "tables" / "trajectory_cluster_centers.csv")
    save_csv(bundle["metrics"], work_dir / "outputs" / "tables" / "trajectory_cluster_metrics.csv")
    log("Step 3 completed.")


if __name__ == "__main__":
    main()
