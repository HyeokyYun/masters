"""Compute practical impact metrics for early risk targeting."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "260303" / "outputs" / "tables"
LOG_DIR = ROOT / "260303" / "outputs" / "logs"
INPUT = OUT_DIR / "df_for_life_cycle_regression.csv"

FEATURES = [
    "business_age_months",
    "new_customer_ratio",
    "cv_sales_card",
    "growth_rate",
    "delivery_ratio",
    "weekend_ratio",
    "avg_customer",
    "trend_slope",
]



def make_logger(path: Path):
    def _log(msg: str) -> None:
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    return _log



def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = make_logger(LOG_DIR / "run_practical_impact_metrics.log")

    if not INPUT.exists():
        log(f"ERROR: input not found: {INPUT}")
        return

    df = pd.read_csv(INPUT)
    df = df[df["life_cycle_category"].isin(["rising", "maintaining", "declining"])].copy()

    use_features = [c for c in FEATURES if c in df.columns]
    if not use_features:
        log("ERROR: no usable features")
        return

    work = df[use_features + ["life_cycle_category"]].dropna(subset=["life_cycle_category"]).copy()
    y = (work["life_cycle_category"] == "declining").astype(int)

    min_class = int(y.value_counts().min()) if y.nunique() > 1 else 0
    if min_class < 2:
        log("ERROR: declining/non-declining balance is too small for CV")
        return

    n_splits = max(2, min(5, min_class))
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

    clf = Pipeline(
        steps=[
            ("imp", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )

    pred = cross_val_predict(clf, work[use_features], y, cv=cv, method="predict")
    proba = cross_val_predict(clf, work[use_features], y, cv=cv, method="predict_proba")[:, 1]

    # Top-decile targeting quality.
    cutoff = float(np.quantile(proba, 0.9))
    top = proba >= cutoff
    base_rate = float(y.mean())
    top_rate = float(y[top].mean()) if top.any() else np.nan
    lift = float(top_rate / base_rate) if base_rate > 0 and np.isfinite(top_rate) else np.nan

    rows = [
        {"metric": "declining_precision", "value": float(precision_score(y, pred, zero_division=0)), "definition": "Precision for declining-risk class"},
        {"metric": "declining_recall", "value": float(recall_score(y, pred, zero_division=0)), "definition": "Recall for declining-risk class"},
        {"metric": "declining_f1", "value": float(f1_score(y, pred, zero_division=0)), "definition": "F1 for declining-risk class"},
        {"metric": "top_decile_lift", "value": lift, "definition": "Declining prevalence lift in top 10% predicted-risk segment"},
        {"metric": "declining_base_rate", "value": base_rate, "definition": "Overall declining share"},
        {"metric": "declining_top_decile_rate", "value": top_rate, "definition": "Declining share in top 10% risk segment"},
    ]

    if "total_weeks" in df.columns:
        potential_lead = (df["total_weeks"] - 30).clip(lower=0)
        rows.extend(
            [
                {
                    "metric": "intervention_lead_weeks_median",
                    "value": float(potential_lead.median()),
                    "definition": "Median weeks between 30-week signal and end of observed trajectory",
                },
                {
                    "metric": "intervention_lead_weeks_p75",
                    "value": float(potential_lead.quantile(0.75)),
                    "definition": "75th percentile lead window",
                },
            ]
        )

    out = OUT_DIR / "practical_impact_metrics.csv"
    pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8-sig")
    log(f"Saved {out}")


if __name__ == "__main__":
    main()
