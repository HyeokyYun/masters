from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import pandas as pd

from src.step01_prepare_panel import prepare_observed_panel
from src.step02_extract_features import extract_observed_window_features
from src.step03_assign_labels import assign_observed_window_labels
from src.step04_age_analysis import run_fullsample_age_analysis
from src.step06_bucket_feature_importance import run_bucket_feature_importance
from src.step05_reporting import write_reports


def _load_csv(name: str) -> pd.DataFrame:
    path = ROOT / "outputs" / "tables" / name
    df = pd.read_csv(path)
    if "public_id" in df.columns:
        df["public_id"] = df["public_id"].astype(str)
    return df


def _load_panel() -> pd.DataFrame:
    return pd.read_parquet(ROOT / "outputs" / "tables" / "observed_window_panel.parquet")


def main() -> None:
    parser = argparse.ArgumentParser(description="260326 full-sample observed-window analysis")
    parser.add_argument("--step", type=int, default=0, help="Run one step only (1-6). Use 0 for all.")
    args = parser.parse_args()

    step = args.step
    started = time.time()

    panel = None
    feat = None
    labeled = None

    print("=" * 72)
    print("260326_fullsample: all-store observed-window analysis")
    print("=" * 72)

    if step in (0, 1):
        print("[1/6] Preparing observed panel")
        panel = prepare_observed_panel()

    if step in (0, 2):
        print("[2/6] Extracting observed-window features")
        if panel is None:
            panel = _load_panel()
        feat = extract_observed_window_features(panel)

    if step in (0, 3):
        print("[3/6] Assigning observed-window labels")
        if feat is None:
            feat = _load_csv("observed_window_features.csv")
        labeled = assign_observed_window_labels(feat)

    if step in (0, 4):
        print("[4/6] Running full-age analysis on all-store labels")
        if labeled is None:
            labeled = _load_csv("observed_window_features_labeled.csv")
        run_fullsample_age_analysis(labeled)

    if step in (0, 5):
        print("[5/6] Running bucket-wise feature importance analysis")
        run_bucket_feature_importance()

    if step in (0, 6):
        print("[6/6] Writing documentation")
        write_reports()

    elapsed = time.time() - started
    print("=" * 72)
    print(f"Completed in {elapsed:.1f}s")
    print("=" * 72)


if __name__ == "__main__":
    main()
