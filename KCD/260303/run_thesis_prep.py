"""Sequential thesis-prep runner for 260303 pipeline.

By default this script executes each step in order.
Use --dry-run to print commands only.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

STEPS = [
    ("Base lifecycle pipeline", [sys.executable, str(ROOT / "260303" / "run_all.py")]),
    (
        "Robustness: label",
        [sys.executable, str(ROOT / "260303" / "03_robustness" / "run_01_label_robustness.py")],
    ),
    (
        "Robustness: sample",
        [sys.executable, str(ROOT / "260303" / "03_robustness" / "run_02_sample_robustness.py")],
    ),
    (
        "Robustness: model",
        [sys.executable, str(ROOT / "260303" / "03_robustness" / "run_03_model_robustness.py")],
    ),
    (
        "Robustness: master table",
        [sys.executable, str(ROOT / "260303" / "03_robustness" / "run_04_build_master_table.py")],
    ),
    (
        "Practical impact metrics",
        [sys.executable, str(ROOT / "260303" / "04_practical_impact" / "run_practical_impact_metrics.py")],
    ),
    (
        "Doc templates",
        [sys.executable, str(ROOT / "260303" / "05_thesis_docs" / "generate_doc_templates.py")],
    ),
    (
        "Result inventory",
        [sys.executable, str(ROOT / "260303" / "05_thesis_docs" / "generate_result_inventory.py")],
    ),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")
    args = parser.parse_args()

    print("=" * 72)
    print("260303 thesis prep pipeline")
    print("=" * 72)

    for idx, (name, cmd) in enumerate(STEPS, start=1):
        print(f"\n[{idx}/{len(STEPS)}] {name}")
        print("$", " ".join(cmd))

        if args.dry_run:
            continue

        completed = subprocess.run(cmd, cwd=str(ROOT))
        if completed.returncode != 0:
            print(f"FAILED: {name} (exit={completed.returncode})")
            return completed.returncode

    print("\nAll thesis-prep steps finished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
