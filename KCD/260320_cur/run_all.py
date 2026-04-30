"""
260320_cur 전체 실행 (원본 weekly 필요한 단계는 시간이 걸릴 수 있음)

Run from 26-1: python 260320_cur/run_all.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = [
    "run_05_business_age_histogram.py",  # 입력만 df면 빠름
    "run_01_trend_residual_cv.py",       # weekly 전체 스캔 — 무거움
    "run_02_build_extended_dataset.py",
    "run_03_extended_mnlogit.py",
    "run_04_subsample_by_age.py",
]


def main():
    for name in SCRIPTS:
        path = ROOT / name
        print("=" * 60)
        print(path.name)
        print("=" * 60)
        r = subprocess.run([sys.executable, str(path)], cwd=str(ROOT))
        if r.returncode != 0:
            print(f"FAILED: {name} (code {r.returncode})")
            # run_01 실패 시에도 02는 기존 cv로 진행 가능
            if name == "run_01_trend_residual_cv.py":
                print("Continuing without trend residual features...")
                continue
            sys.exit(r.returncode)


if __name__ == "__main__":
    main()
