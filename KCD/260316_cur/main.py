"""
소상공인 매출 시계열 생애주기 분석 ─ 통합 파이프라인
═══════════════════════════════════════════════════════════
실행:
  cd 260316_cur
  pip install -r requirements.txt
  python main.py                    # 전체 실행
  python main.py --step 1           # 특정 단계만
  python main.py --step 3 --skip-stl  # STL 건너뛰기 (빠른 테스트)
═══════════════════════════════════════════════════════════
"""
import sys
import time
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src import config as cfg
from src.step01_preprocessing    import preprocess
from src.step02_feature_extraction import extract_features
from src.step03_clustering       import run_clustering
from src.step04_label_assignment import run_labeling
from src.step04b_variable_selection import run_variable_selection
from src.step05_factor_analysis  import run_factor_analysis
from src.step06_prediction       import run_prediction
from src.step07_visualization    import run_visualization


def main():
    parser = argparse.ArgumentParser(description="소상공인 생애주기 분석 파이프라인")
    parser.add_argument("--step", type=int, default=0,
                        help="특정 단계만 실행 (1-7). 0=전체")
    args = parser.parse_args()

    t0 = time.time()
    step = args.step

    print("=" * 62)
    print("  소상공인 매출 시계열 생애주기 분석")
    print("=" * 62)

    # ── Step 1: 전처리 ──────────────────────────────
    if step in (0, 1):
        print("\n▶ Step 01: 전처리")
        ts, meta = preprocess()
    else:
        print("\n▶ Step 01: 중간 데이터 로드 시도...")
        import pandas as pd
        feat_path = cfg.TABLE_DIR / "store_features_labeled.csv"
        if feat_path.exists():
            feat = pd.read_csv(feat_path)
            feat["public_id"] = feat["public_id"].astype(str)
        ts, meta = None, None

    # ── Step 2: 피처 추출 ────────────────────────────
    if step in (0, 2):
        print("\n▶ Step 02: 피처 추출")
        feat = extract_features(ts)

    # ── Step 3: 클러스터링 ───────────────────────────
    km_model, eval_df, cluster_df, all_km_models = None, None, None, None
    if step in (0, 3):
        print("\n▶ Step 03: 클러스터링")
        cluster_df, km_model, eval_df, compare, all_km_models = run_clustering(ts)

    # ── Step 4: 레이블 할당 ──────────────────────────
    if step in (0, 4):
        print("\n▶ Step 04: 레이블 할당")
        feat = run_labeling(feat, cluster_df)

    # ── Step 4b: 변수 선택 ───────────────────────────
    selected_vars, early_selected_vars = None, None
    if step in (0, 4):
        print("\n▶ Step 04b: 변수 선택")
        var_result = run_variable_selection(feat)
        selected_vars = var_result["selected_vars"]
        early_selected_vars = var_result["early_selected_vars"]

    # ── Step 5: 요인 분석 ────────────────────────────
    if step in (0, 5):
        print("\n▶ Step 05: 요인 분석")
        import pandas as pd
        if meta is None:
            meta = pd.read_csv(cfg.META_CSV)
            meta["public_id"] = meta["public_id"].astype(str)
        if "feat" not in dir():
            feat = pd.read_csv(cfg.TABLE_DIR / "store_features_labeled.csv")
            feat["public_id"] = feat["public_id"].astype(str)
        run_factor_analysis(feat, meta, selected_vars=selected_vars)

    # ── Step 6: 예측 ────────────────────────────────
    abl_df = None
    if step in (0, 6):
        print("\n▶ Step 06: 조기 예측")
        if ts is None:
            print("  ts 로드 중 (전처리 재실행)...")
            ts, meta = preprocess()
        if "feat" not in dir():
            import pandas as pd
            feat = pd.read_csv(cfg.TABLE_DIR / "store_features_labeled.csv")
            feat["public_id"] = feat["public_id"].astype(str)
        pred_results = run_prediction(ts, feat, early_selected_vars=early_selected_vars)
        abl_df = pred_results.get("ablation")

    # ── Step 7: 시각화 ──────────────────────────────
    if step in (0, 7):
        print("\n▶ Step 07: 시각화")
        if "feat" not in dir():
            import pandas as pd
            feat = pd.read_csv(cfg.TABLE_DIR / "store_features_labeled.csv")
            feat["public_id"] = feat["public_id"].astype(str)
        run_visualization(feat, ts, km_model, eval_df, abl_df, all_km_models)

    # ── 완료 ────────────────────────────────────────
    elapsed = time.time() - t0
    print("\n" + "=" * 62)
    print(f"  완료  ({elapsed:.0f}초)")
    print("=" * 62)

    if step == 0 and "feat" in dir():
        vc = feat["label"].value_counts().reindex(cfg.LIFECYCLE_LABELS, fill_value=0)
        print(f"\n  {'레이블':<6} {'매장수':>7} {'비율':>7}  설명")
        print("  " + "-" * 55)
        for lbl in cfg.LIFECYCLE_LABELS:
            cnt = vc[lbl]
            pct = cnt / len(feat) * 100
            print(f"  {lbl:<6} {cnt:>7,} {pct:>6.1f}%  {cfg.LABEL_DESC[lbl]}")
        print()

    # 산출물 목록
    import os
    for d, label in [(cfg.TABLE_DIR, "Tables"), (cfg.FIGURE_DIR, "Figures")]:
        files = sorted(d.glob("*"))
        if files:
            print(f"\n  [{label}]")
            for f in files:
                sz = os.path.getsize(f) / 1024
                print(f"    {f.name:45s} {sz:7.0f} KB")


if __name__ == "__main__":
    main()
