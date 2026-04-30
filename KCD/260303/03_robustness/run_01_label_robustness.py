"""260303 robustness: label-definition sensitivity."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict

import numpy as np
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
CONFIG = ROOT / "260303" / "configs" / "robustness_labels.yaml"


def make_logger(path: Path):
    def _log(msg: str) -> None:
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    return _log


def apply_label_rule(df: pd.DataFrame, rule: Dict[str, object]) -> pd.Series:
    mode = str(rule.get("mode", "pattern_only"))
    pattern = df.get("Pattern_label", pd.Series(index=df.index, dtype=object)).astype(str).str.upper()

    if mode == "pattern_only":
        return pattern.map({"X": "rising", "Y": "maintaining", "Z": "declining"})

    growth = df.get("growth_rate")
    if growth is None:
        return pattern.map({"X": "rising", "Y": "maintaining", "Z": "declining"})

    q_low = float(rule.get("growth_q_low", 0.2))
    q_high = float(rule.get("growth_q_high", 0.8))
    low = float(growth.quantile(q_low))
    high = float(growth.quantile(q_high))

    y = pd.Series("maintaining", index=df.index)
    if mode == "pattern_plus_growth":
        y[(pattern == "X") | (growth >= high)] = "rising"
        y[(pattern == "Z") | (growth <= low)] = "declining"
        return y

    if mode == "strict_pattern_with_growth_gate":
        g_med = float(growth.median())
        y[(pattern == "X") & (growth >= g_med)] = "rising"
        y[(pattern == "Z") & (growth < g_med)] = "declining"
        return y

    return pattern.map({"X": "rising", "Y": "maintaining", "Z": "declining"})


def default_config() -> Dict[str, object]:
    return {
        "baseline": "maintaining",
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
        "scenarios": [
            {
                "name": "pattern_only_baseline",
                "mode": "pattern_only",
                "notes": "Pattern X/Y/Z only (same as base mapping)",
            },
            {
                "name": "pattern_plus_growth_q20_q80",
                "mode": "pattern_plus_growth",
                "growth_q_low": 0.2,
                "growth_q_high": 0.8,
                "notes": "Pattern + growth quantile tails",
            },
            {
                "name": "strict_pattern_growth_gate",
                "mode": "strict_pattern_with_growth_gate",
                "notes": "Pattern with median growth gate",
            },
        ],
    }


def main() -> None:
    safe_mkdir(OUT_DIR)
    safe_mkdir(LOG_DIR)
    log = make_logger(LOG_DIR / "run_robustness_label.log")

    if not INPUT.exists():
        log(f"ERROR: input not found: {INPUT}")
        return

    cfg = load_yaml_or_default(CONFIG, default_config())
    baseline = str(cfg.get("baseline", "maintaining"))

    df = pd.read_csv(INPUT)
    features = available_features(df, cfg.get("feature_candidates"))
    if not features:
        log("ERROR: no usable features found for robustness model")
        return

    rows = []
    baseline_signs = None

    for scen in cfg.get("scenarios", []):
        name = str(scen.get("name", "unnamed"))
        y = apply_label_rule(df, scen)
        work = df.copy()
        work["life_cycle_category_alt"] = y
        work = work[work["life_cycle_category_alt"].isin(["rising", "maintaining", "declining"])].copy()

        if work["life_cycle_category_alt"].nunique() < 3:
            log(f"SKIP {name}: does not produce 3 classes")
            continue

        result = evaluate_spec(
            work,
            y_col="life_cycle_category_alt",
            features=features,
            baseline=baseline,
            spec_name=name,
            spec_type="label_robustness",
            notes=str(scen.get("notes", "")),
            baseline_signs=baseline_signs,
        )

        if baseline_signs is None:
            baseline_signs = result.coef_signs

        dist = work["life_cycle_category_alt"].value_counts(normalize=True).round(4).to_dict()
        metric_row = dict(result.metrics)
        metric_row["class_dist"] = str(dist)
        rows.append(metric_row)
        log(f"DONE {name}: n={metric_row['n_obs']} macro_f1={metric_row.get('macro_f1_cv')}")

    out_csv = OUT_DIR / "robustness_label_results.csv"
    save_rows(rows, out_csv)
    log(f"Saved {out_csv}")


if __name__ == "__main__":
    main()
