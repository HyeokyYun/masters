from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import pandas as pd

from src.step01_build_base_dataset import build_base_dataset
from src.step02_volatility_analysis import compute_volatility_candidates
from src.step03_followup_analysis import run_followup_analysis
from src.step04_reporting import generate_reports


def _load_csv(name: str) -> pd.DataFrame:
    path = ROOT / "outputs" / "tables" / name
    df = pd.read_csv(path)
    if "public_id" in df.columns:
        df["public_id"] = df["public_id"].astype(str)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="260321_codex meeting follow-up pipeline")
    parser.add_argument("--step", type=int, default=0, help="Run a specific step only (1-4). Use 0 for all.")
    args = parser.parse_args()

    step = args.step
    started = time.time()

    base_df = None
    volatility_df = None

    print("=" * 72)
    print("260321_codex: meeting follow-up analysis package")
    print("=" * 72)

    if step in (0, 1):
        print("[1/4] Building enriched base dataset")
        artifacts = build_base_dataset()
        base_df = artifacts.base_df

    if step in (0, 2):
        print("[2/4] Computing alternative volatility definitions")
        if base_df is None:
            base_df = _load_csv("meeting_base_dataset.csv")
        volatility_df = compute_volatility_candidates(base_df)

    if step in (0, 3):
        print("[3/4] Running follow-up interaction and business-age analyses")
        if base_df is None:
            base_df = _load_csv("meeting_base_dataset.csv")
        if volatility_df is None:
            volatility_df = _load_csv("volatility_candidate_metrics.csv")
        run_followup_analysis(base_df, volatility_df)

    if step in (0, 4):
        print("[4/4] Writing meeting summary and benchmark templates")
        generate_reports()

    elapsed = time.time() - started
    print("=" * 72)
    print(f"Completed in {elapsed:.1f}s")
    print("=" * 72)


if __name__ == "__main__":
    main()
