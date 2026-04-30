from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "260316" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from research_pipeline.config import get_work_dir
from research_pipeline.io_utils import build_logger, ensure_layout, save_csv, save_text
from research_pipeline.reporting import build_inventory_bundle


def main() -> None:
    work_dir = get_work_dir()
    ensure_layout(work_dir)
    log = build_logger(work_dir / "outputs" / "logs" / "run_build_inventory.log")

    log("260316 Step 6: build output inventory")
    bundle = build_inventory_bundle(work_dir)

    save_csv(bundle["manifest"], work_dir / "outputs" / "tables" / "output_manifest.csv")
    save_text(bundle["markdown"], work_dir / "docs" / "output_inventory.md")
    log("Step 6 completed.")


if __name__ == "__main__":
    main()
