"""
260321 미팅 피드백 반영 추가 분석
═══════════════════════════════════════════════════════════
실행:
  cd 260321_cur
  python main.py              # 전체 실행
  python main.py --task 1     # 특정 태스크만 실행
  python main.py --task 2 3   # 복수 태스크

Tasks:
  1) 매출 변동성 재정의 (trend-adjusted CV)
  2) 경쟁 밀도 지수 (competition index + interaction)
  3) 대표자 연령/성별 추가 MNLogit
  4) 업력별 서브샘플 분석
  5) 예측 주차별 ablation (30/40/50주) + 벤치마크

전제: 260319_cur 파이프라인이 실행되어
      outputs/tables/store_features_labeled.csv 가 존재해야 합니다.
═══════════════════════════════════════════════════════════
"""
import sys
import time
import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src import config as cfg


def main():
    parser = argparse.ArgumentParser(
        description="260321 미팅 피드백 추가 분석"
    )
    parser.add_argument(
        "--task", type=int, nargs="*", default=None,
        help="실행할 태스크 번호 (1-5). 생략 시 전체 실행."
    )
    args = parser.parse_args()

    tasks = args.task if args.task else [1, 2, 3, 4, 5]

    t0 = time.time()

    print("=" * 62)
    print("  260321 미팅 피드백 반영 추가 분석")
    print("=" * 62)

    # 260319_cur 산출물 확인
    feat_path = cfg.PREV_TABLE_DIR / "store_features_labeled.csv"
    if not feat_path.exists():
        print(f"\n[ERROR] 260319_cur 산출물이 필요합니다:")
        print(f"  {feat_path}")
        print("  먼저 260319_cur/main.py 를 실행하세요.")
        sys.exit(1)
    print(f"\n  기반 데이터: {feat_path}")

    # ── Task 1: 변동성 재정의 ────────────────────────
    if 1 in tasks:
        from src.task01_volatility import run_task01
        run_task01()

    # ── Task 2: 경쟁 밀도 지수 ───────────────────────
    if 2 in tasks:
        from src.task02_competition import run_task02
        run_task02()

    # ── Task 3: 대표자 연령/성별 ─────────────────────
    if 3 in tasks:
        from src.task03_demographics import run_task03
        run_task03()

    # ── Task 4: 업력별 서브샘플 ──────────────────────
    if 4 in tasks:
        from src.task04_subsample import run_task04
        run_task04()

    # ── Task 5: 예측 주차 ablation ───────────────────
    if 5 in tasks:
        from src.task05_forecast_weeks import run_task05
        run_task05()

    # ── 완료 ─────────────────────────────────────────
    elapsed = time.time() - t0
    print("\n" + "=" * 62)
    print(f"  완료  ({elapsed:.0f}초)")
    print("=" * 62)

    # 산출물 목록
    for d, label in [(cfg.TABLE_DIR, "Tables"), (cfg.FIGURE_DIR, "Figures")]:
        files = sorted(d.glob("*"))
        if files:
            print(f"\n  [{label}]")
            for f in files:
                sz = os.path.getsize(f) / 1024
                print(f"    {f.name:50s} {sz:7.0f} KB")


if __name__ == "__main__":
    main()
