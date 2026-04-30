"""
260301 전체 실행

original_data 검증 → Base features → 라벨 병합 → Summary + Multinomial Logit → 30주 예측
Run from 26-1: python 260301/run_all.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

STEPS = [
    ("260301/01_verify_data/run_verify_original_data.py", "Step 0: original_data 검증"),
    ("260301/02_preprocess/run_build_base_features.py", "Step 1: Base features"),
    ("260301/03_clustering_udx/run_merge_labels.py", "Step 2: 라벨 병합"),
    ("260301/04_summary_regression/run_summary_and_multinomial.py", "Step 3-4: Summary + Multinomial Logit"),
    ("260301/05_prediction/run_30w_prediction.py", "Step 5: 30주 예측"),
]

if __name__ == "__main__":
    print("=" * 60)
    print("260301 — 석사논문 통합 파이프라인")
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
    print("완료. 결과: 260301/outputs/tables/")
    print("=" * 60)
