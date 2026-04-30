"""
260301 Step 5: 30주 예측

260223 run_step5_real_prediction.py 호출.
또는 직접 실행 (동일 로직).
Run from 26-1: python 260301/05_prediction/run_30w_prediction.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
STEP5_SCRIPT = ROOT / "260223" / "04_prediction" / "run_step5_real_prediction.py"


def main():
    if not STEP5_SCRIPT.exists():
        print(f"ERROR: {STEP5_SCRIPT} not found")
        return 1
    print("=" * 60)
    print("Step 5: 30주 예측 (260223 run_step5 호출)")
    print("=" * 60)
    r = subprocess.run([sys.executable, str(STEP5_SCRIPT)], cwd=str(ROOT))
    if r.returncode != 0:
        print("Step 5 completed with warnings. Check 260223/outputs/tables/real_prediction_results.csv")
    return 0


if __name__ == "__main__":
    exit(main())
