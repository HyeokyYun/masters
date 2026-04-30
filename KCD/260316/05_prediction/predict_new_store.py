from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "260316" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from research_pipeline.config import get_work_dir, load_config
from research_pipeline.io_utils import save_csv
from research_pipeline.prediction import build_new_store_feature_frame


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score a new store using weekly sales input.")
    parser.add_argument("--weekly-csv", required=True, help="Path to new-store weekly CSV.")
    parser.add_argument("--meta-csv", required=False, help="Optional path to one-row meta CSV.")
    parser.add_argument("--model-pkl", required=True, help="Pickle file produced after training.")
    parser.add_argument(
        "--output-csv",
        default=str(get_work_dir() / "outputs" / "tables" / "new_store_prediction.csv"),
        help="Where to save the scoring result.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config()
    weekly_df = pd.read_csv(args.weekly_csv)
    meta_df = pd.read_csv(args.meta_csv) if args.meta_csv else None
    feature_frame = build_new_store_feature_frame(weekly_df, meta_df, cfg)

    with open(args.model_pkl, "rb") as f:
        payload = pickle.load(f)

    model = payload["model"]
    feature_columns = payload["feature_columns"]
    prediction = model.predict(feature_frame[feature_columns])
    result = feature_frame.copy()
    result["predicted_life_cycle"] = prediction

    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(feature_frame[feature_columns])
        for idx, cls in enumerate(getattr(model, "classes_", [])):
            result[f"prob_{cls}"] = proba[:, idx]

    save_csv(result, Path(args.output_csv))
    print(f"Saved {args.output_csv}")


if __name__ == "__main__":
    main()
