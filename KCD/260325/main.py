from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import pandas as pd

from src.step01_build_base import build_base_dataset
from src.step02_volatility import run_volatility_analysis
from src.step03_industry_competition import run_industry_competition_analysis
from src.step04_business_age import run_business_age_analysis
from src.step05_new_customer import run_new_customer_analysis
from src.step06_full_business_age import run_full_business_age_analysis
from src.step07_reporting import write_summary_report
from src.step08_forecast_baseline import run_forecast_baseline_analysis
from src.step09_forecast_feature_ablation import run_forecast_feature_ablation
from src.step10_forecast_newvol_competition import run_forecast_newvol_competition
from src.step11_sample_feature_overview import run_sample_feature_overview
from src.step12_rolling_window_sensitivity import run_rolling_window_sensitivity


def _load_csv(name: str) -> pd.DataFrame:
    path = ROOT / "outputs" / "tables" / name
    df = pd.read_csv(path)
    if "public_id" in df.columns:
        df["public_id"] = df["public_id"].astype(str)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="260325 meeting TODO analysis")
    parser.add_argument("--step", type=int, default=0, help="Run one step only (1-12). Use 0 for all.")
    args = parser.parse_args()

    step = args.step
    started = time.time()

    base_df: pd.DataFrame | None = None
    volatility_df: pd.DataFrame | None = None
    enriched_df: pd.DataFrame | None = None
    age_df: pd.DataFrame | None = None

    print("=" * 72)
    print("260325: meeting TODO follow-up")
    print("=" * 72)

    if step in (0, 1):
        print("[1/8] Building base dataset")
        base_df = build_base_dataset()

    if step in (0, 2):
        print("[2/8] Redefining sales volatility")
        if base_df is None:
            base_df = _load_csv("base_dataset.csv")
        volatility_df = run_volatility_analysis(base_df)

    if step in (0, 3):
        print("[3/8] Industry, competition, and interaction analysis")
        if base_df is None:
            base_df = _load_csv("base_dataset.csv")
        if volatility_df is None:
            volatility_df = _load_csv("volatility_candidates.csv")
        enriched_df = run_industry_competition_analysis(base_df, volatility_df)

    if step in (0, 4):
        print("[4/8] Business-age distribution and young-store analysis")
        if enriched_df is None:
            enriched_df = _load_csv("industry_competition_analysis_table.csv")
        age_df = run_business_age_analysis(enriched_df)

    if step in (0, 5):
        print("[5/8] New-customer interpretation analysis")
        if enriched_df is None:
            enriched_df = _load_csv("industry_competition_analysis_table.csv")
        if age_df is None:
            age_df = _load_csv("business_age_analysis_table.csv")
        run_new_customer_analysis(age_df)

    if step in (0, 6):
        print("[6/8] Full-population business-age analysis")
        run_full_business_age_analysis()

    if step in (0, 7):
        print("[7/8] Writing summary report")
        write_summary_report()

    if step in (0, 8):
        print("[8/9] Forecast baseline comparison")
        run_forecast_baseline_analysis()

    if step in (0, 9):
        print("[9/9] Forecast feature ablation")
        run_forecast_feature_ablation()

    if step in (0, 10):
        print("[10/10] Forecast new volatility and competition test")
        run_forecast_newvol_competition()

    if step in (0, 11):
        print("[11/11] Sample-wide feature overview")
        run_sample_feature_overview()

    if step in (0, 12):
        print("[12/12] Rolling-window sensitivity check")
        if base_df is None:
            base_df = _load_csv("base_dataset.csv")
        run_rolling_window_sensitivity(base_df)

    elapsed = time.time() - started
    print("=" * 72)
    print(f"Completed in {elapsed:.1f}s")
    print("=" * 72)


if __name__ == "__main__":
    main()
