"""260303 robustness: sample-definition sensitivity."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict

import pandas as pd

from robustness_utils import (
    available_features,
    evaluate_spec,
    load_yaml_or_default,
    save_rows,
    safe_mkdir,
)

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "260303" / "outputs" / "tables"
LOG_DIR = ROOT / "260303" / "outputs" / "logs"
INPUT = OUT_DIR / "df_for_life_cycle_regression.csv"
CONFIG = ROOT / "260303" / "configs" / "robustness_samples.yaml"


def make_logger(path: Path):
    def _log(msg: str) -> None:
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    return _log


def default_config() -> Dict[str, object]:
    return {
        "baseline": "maintaining",
        "label_col": "life_cycle_category",
        "feature_candidates": [
            "business_age_months",
            "new_customer_ratio",
            "cv_sales_card",
            "growth_rate",
            "delivery_ratio",
            "weekend_ratio",
            "avg_customer",
            "trend_slope",
            "depth_2",
        ],
        "samples": [
            {"name": "all", "query": "life_cycle_category == life_cycle_category", "notes": "Full sample"},
            {"name": "min_weeks_78", "query": "total_weeks >= 78", "notes": "Stores with >= 78 observed weeks"},
            {"name": "min_weeks_104", "query": "total_weeks >= 104", "notes": "Stores with >= 104 observed weeks"},
            {
                "name": "young_stores_half",
                "query": "business_age_months <= business_age_months.median()",
                "notes": "Younger half by business age",
            },
            {
                "name": "older_stores_half",
                "query": "business_age_months > business_age_months.median()",
                "notes": "Older half by business age",
            },
        ],
    }


def main() -> None:
    safe_mkdir(OUT_DIR)
    safe_mkdir(LOG_DIR)
    log = make_logger(LOG_DIR / "run_robustness_sample.log")

    if not INPUT.exists():
        log(f"ERROR: input not found: {INPUT}")
        return

    cfg = load_yaml_or_default(CONFIG, default_config())
    label_col = str(cfg.get("label_col", "life_cycle_category"))
    baseline = str(cfg.get("baseline", "maintaining"))

    df = pd.read_csv(INPUT)
    if label_col not in df.columns:
        log(f"ERROR: label column missing: {label_col}")
        return

    features = available_features(df, cfg.get("feature_candidates"))
    if not features:
        log("ERROR: no usable features found")
        return

    rows = []
    baseline_signs = None

    for sample in cfg.get("samples", []):
        name = str(sample.get("name", "unnamed"))
        query = str(sample.get("query", "life_cycle_category == life_cycle_category"))

        try:
            sub = df.query(query, engine="python").copy()
        except Exception as exc:
            log(f"SKIP {name}: invalid query ({exc})")
            continue

        sub = sub[sub[label_col].isin(["rising", "maintaining", "declining"])].copy()
        if sub.empty or sub[label_col].nunique() < 3:
            log(f"SKIP {name}: insufficient classes")
            continue

        result = evaluate_spec(
            sub,
            y_col=label_col,
            features=features,
            baseline=baseline,
            spec_name=name,
            spec_type="sample_robustness",
            notes=str(sample.get("notes", "")),
            baseline_signs=baseline_signs,
        )
        if baseline_signs is None:
            baseline_signs = result.coef_signs

        row = dict(result.metrics)
        row["class_dist"] = str(sub[label_col].value_counts(normalize=True).round(4).to_dict())
        rows.append(row)
        log(f"DONE {name}: n={row['n_obs']} macro_f1={row.get('macro_f1_cv')}")

    out_csv = OUT_DIR / "robustness_sample_results.csv"
    save_rows(rows, out_csv)
    log(f"Saved {out_csv}")


if __name__ == "__main__":
    main()
