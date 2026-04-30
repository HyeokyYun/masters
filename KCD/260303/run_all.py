"""
260303 — Life cycle classification experiment

Y variable: life_cycle_category (rising / maintaining / declining)
  - rising     <- Pattern X
  - maintaining <- Pattern Y (stable)
  - declining   <- Pattern Z

Steps:
  1. Merge labels from final_code -> life_cycle_category
  2. Summary statistics + Multinomial Logit (baseline = maintaining)

Run from 26-1: python 260303/run_all.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

STEPS = [
    ("260303/01_merge_labels/run_merge_labels.py", "Step 1: Merge labels (life_cycle_category)"),
    ("260303/02_regression/run_summary_and_multinomial.py", "Step 2: Summary + Multinomial Logit"),
]

if __name__ == "__main__":
    print("=" * 60)
    print("260303 — Life cycle: rising / maintaining / declining")
    print("=" * 60)
    for script, desc in STEPS:
        path = ROOT / script
        if not path.exists():
            print(f"SKIP {desc}: {path} not found")
            continue
        print(f"\n>>> {desc}")
        r = subprocess.run([sys.executable, str(path)], cwd=str(ROOT))
        if r.returncode != 0:
            print(f"WARNING: {script} exited with {r.returncode}")
    print("\n" + "=" * 60)
    print("완료. 결과: 260303/outputs/tables/")
    print("=" * 60)
