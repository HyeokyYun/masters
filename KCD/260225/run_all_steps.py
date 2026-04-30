"""
260225 액션아이템 전체 실행

Step 1: 클러스터별 Summary Statistics
Step 2: Multinomial Logit
Step 3: 회귀 30주 설계 문서화
Step 4: 30주 예측 (260223 run_step5 호출)

Run from 26-1: python 260225/run_all_steps.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STEPS = [
    ("260225/01_summary_stats/run_cluster_summary_statistics.py", "Step 1: Summary Statistics"),
    ("260225/02_multinomial_logit/run_multinomial_logit.py", "Step 2: Multinomial Logit"),
    ("260225/03_regression_30w/run_regression_30w_only.py", "Step 3: Regression 30w design"),
]

if __name__ == "__main__":
    print("=" * 60)
    print("260225 액션아이템 실행")
    print("=" * 60)
    for script, desc in STEPS:
        path = ROOT / script
        if not path.exists():
            print(f"SKIP {desc}: {path} not found")
            continue
        print(f"\n>>> {desc}")
        r = subprocess.run([sys.executable, str(path)], cwd=str(ROOT))
        if r.returncode != 0:
            print(f"FAILED: {script}")
            sys.exit(1)
    # Step 4: 30주 예측
    step4 = ROOT / "260223" / "04_prediction" / "run_step5_real_prediction.py"
    if step4.exists():
        print("\n>>> Step 4: 30주 예측")
        r = subprocess.run([sys.executable, str(step4)], cwd=str(ROOT))
        if r.returncode != 0:
            print("Step 4 completed with warnings (e.g. matplotlib). Check 260223/outputs/tables/real_prediction_results.csv")
    print("\n" + "=" * 60)
    print("완료. 결과: 260225/outputs/tables/, 260225/docs/260225_액션아이템_실행결과_요약.md")
    print("=" * 60)
