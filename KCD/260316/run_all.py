"""Run the full 260316 research pipeline step by step."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

STEPS = [
    ("260316/01_data_prep/run_prepare_base_data.py", "Step 1: Prepare panel and base features"),
    ("260316/02_lifecycle/run_lifecycle_labeling.py", "Step 2: Label lifecycle states"),
    ("260316/03_clustering/run_time_series_clustering.py", "Step 3: Time-series clustering"),
    ("260316/04_modeling/run_factor_analysis.py", "Step 4: Factor analysis and econometrics"),
    ("260316/05_prediction/run_early_prediction.py", "Step 5: Early-window prediction"),
    ("260316/06_reporting/run_build_inventory.py", "Step 6: Output inventory"),
]


def main() -> None:
    print("=" * 70)
    print("260316 Research Pipeline")
    print("=" * 70)
    for script, desc in STEPS:
        path = ROOT / script
        if not path.exists():
            print(f"SKIP {desc}: {path} not found")
            continue
        print(f"\n>>> {desc}")
        result = subprocess.run([sys.executable, str(path)], cwd=str(ROOT))
        if result.returncode != 0:
            print(f"WARNING: {script} exited with code {result.returncode}")
            break
    print("\n" + "=" * 70)
    print("Finished. See 260316/outputs/")
    print("=" * 70)


if __name__ == "__main__":
    main()
