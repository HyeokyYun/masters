"""260303 robustness: model-family sensitivity."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC

from robustness_utils import available_features, build_compatible_logistic_regression, save_rows, safe_mkdir

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "260303" / "outputs" / "tables"
LOG_DIR = ROOT / "260303" / "outputs" / "logs"
INPUT = OUT_DIR / "df_for_life_cycle_regression.csv"


FEATURE_CANDIDATES = [
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


def evaluate_model(df: pd.DataFrame, y_col: str, features: list[str], model_name: str, pipe: Pipeline) -> dict:
    work = df[features + [y_col]].dropna().copy()
    min_class = int(work[y_col].value_counts().min())
    n_splits = max(2, min(5, min_class))
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

    pred = cross_val_predict(pipe, work[features], work[y_col], cv=cv, method="predict")
    return {
        "spec_name": model_name,
        "spec_type": "model_robustness",
        "n_obs": int(len(work)),
        "n_class": int(work[y_col].nunique()),
        "macro_f1_cv": float(f1_score(work[y_col], pred, average="macro")),
        "weighted_f1_cv": float(f1_score(work[y_col], pred, average="weighted")),
        "accuracy_cv": float(accuracy_score(work[y_col], pred)),
        "notes": "Base features with 5-fold (or feasible max) stratified CV",
    }


def main() -> None:
    safe_mkdir(OUT_DIR)
    safe_mkdir(LOG_DIR)
    log = make_logger(LOG_DIR / "run_robustness_model.log")

    if not INPUT.exists():
        log(f"ERROR: input not found: {INPUT}")
        return

    df = pd.read_csv(INPUT)
    y_col = "life_cycle_category"
    df = df[df[y_col].isin(["rising", "maintaining", "declining"])].copy()
    features = available_features(df, FEATURE_CANDIDATES)

    if not features:
        log("ERROR: no usable numeric features found")
        return

    common = [("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]

    models = {
        "multinomial_logit": Pipeline(
            steps=common
            + [
                (
                    "model",
                    build_compatible_logistic_regression(
                        multi_class="multinomial",
                        solver="lbfgs",
                        max_iter=1500,
                        class_weight="balanced",
                        random_state=42,
                    ),
                )
            ]
        ),
        "random_forest": Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=400,
                        min_samples_leaf=2,
                        class_weight="balanced_subsample",
                        random_state=42,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
        "linear_svm": Pipeline(
            steps=common
            + [
                (
                    "model",
                    LinearSVC(
                        C=1.0,
                        class_weight="balanced",
                        random_state=42,
                    ),
                )
            ]
        ),
    }

    rows = []
    for name, pipe in models.items():
        try:
            row = evaluate_model(df, y_col=y_col, features=features, model_name=name, pipe=pipe)
            rows.append(row)
            log(f"DONE {name}: macro_f1={row['macro_f1_cv']:.4f}")
        except Exception as exc:
            log(f"SKIP {name}: {exc}")

    rows = sorted(rows, key=lambda r: r.get("macro_f1_cv", -1), reverse=True)
    out_csv = OUT_DIR / "robustness_model_results.csv"
    save_rows(rows, out_csv)
    log(f"Saved {out_csv}")


if __name__ == "__main__":
    main()
