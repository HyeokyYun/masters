from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.step01_preprocessing import preprocess
from src.step02_feature_extraction import extract_features
from src.step03_label_assignment import assign_labels
from src.step04_clustering import load_or_run_clustering
from src.step05_modeling import run_factor_analysis
from src.step06_prediction import run_prediction


def _load_csv(name: str):
    import pandas as pd

    path = ROOT / "outputs" / "tables" / name
    df = pd.read_csv(path)
    if "public_id" in df.columns:
        df["public_id"] = df["public_id"].astype(str)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="260319_codex lifecycle pipeline")
    parser.add_argument("--step", type=int, default=0, help="특정 단계만 실행 (1-6), 0=전체")
    args = parser.parse_args()

    t0 = time.time()
    step = args.step
    print("=" * 64)
    print("  260319_codex: U/D + X/Y/Z 생애주기 코드 생성")
    print("=" * 64)

    weekly = None
    meta = None
    features = None
    labeled = None

    if step in (0, 1):
        print("\n[1/6] 전처리")
        weekly, meta = preprocess()

    if step in (0, 2):
        print("\n[2/6] 피처 추출")
        if weekly is None:
            weekly, meta = preprocess()
        features = extract_features(weekly)

    if step in (0, 3):
        print("\n[3/6] 라벨 할당")
        if features is None:
            features = _load_csv("store_features.csv")
        labeled = assign_labels(features)

    if step in (0, 4):
        print("\n[4/6] 클러스터링")
        if weekly is None:
            weekly, meta = preprocess()
        if labeled is None:
            labeled = _load_csv("store_features_labeled.csv")
        load_or_run_clustering(weekly, labeled)

    if step in (0, 5):
        print("\n[5/6] 요인 분석")
        if labeled is None:
            labeled = _load_csv("store_features_labeled.csv")
        if meta is None:
            import pandas as pd

            meta = pd.read_csv(ROOT.parent / "original_data" / "meta.csv")
            meta["public_id"] = meta["public_id"].astype(str)
        run_factor_analysis(labeled, meta)

    if step in (0, 6):
        print("\n[6/6] 조기 예측")
        if weekly is None:
            weekly, meta = preprocess()
        if labeled is None:
            labeled = _load_csv("store_features_labeled.csv")
        run_prediction(weekly, labeled)

    elapsed = time.time() - t0
    print("\n" + "=" * 64)
    if labeled is not None:
        print(f"완료: {len(labeled):,}개 매장, {elapsed:.1f}초")
    else:
        print(f"완료: {elapsed:.1f}초")
    print("=" * 64)


if __name__ == "__main__":
    main()
