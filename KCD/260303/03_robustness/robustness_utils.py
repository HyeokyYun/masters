"""Utilities for 260303 robustness analyses."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
import inspect
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    import statsmodels.api as sm
    HAS_STATSMODELS = True
except Exception:
    HAS_STATSMODELS = False


DEFAULT_FEATURE_CANDIDATES = [
    "business_age_months",
    "new_customer_ratio",
    "cv_sales_card",
    "growth_rate",
    "delivery_ratio",
    "weekend_ratio",
    "avg_customer",
    "trend_slope",
]


@dataclass
class ModelArtifacts:
    metrics: Dict[str, float]
    coef_signs: Dict[str, int]
    coef_pvalues: Dict[str, float]


def safe_mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def build_compatible_logistic_regression(**kwargs) -> LogisticRegression:
    """Create LogisticRegression while dropping args unsupported by older sklearn."""
    valid = set(inspect.signature(LogisticRegression.__init__).parameters.keys())
    filtered = {k: v for k, v in kwargs.items() if k in valid}
    return LogisticRegression(**filtered)


def available_features(df: pd.DataFrame, candidates: Optional[Iterable[str]] = None) -> List[str]:
    cand = list(candidates or DEFAULT_FEATURE_CANDIDATES)
    return [c for c in cand if c in df.columns]


def build_lr_pipeline(df: pd.DataFrame, features: List[str]) -> Pipeline:
    numeric = [c for c in features if pd.api.types.is_numeric_dtype(df[c])]
    categoric = [c for c in features if c not in numeric]

    pre = ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric,
            ),
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("ohe", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categoric,
            ),
        ],
        remainder="drop",
    )

    model = build_compatible_logistic_regression(
        multi_class="multinomial",
        solver="lbfgs",
        max_iter=1500,
        class_weight="balanced",
        random_state=42,
    )
    return Pipeline(steps=[("pre", pre), ("model", model)])


def _sklearn_metrics(df: pd.DataFrame, y_col: str, features: List[str], n_splits: int = 5) -> Dict[str, float]:
    work = df[features + [y_col]].dropna(subset=[y_col]).copy()
    class_counts = work[y_col].value_counts()
    if len(class_counts) < 3:
        return {"macro_f1_cv": np.nan, "weighted_f1_cv": np.nan, "accuracy_cv": np.nan}

    min_count = int(class_counts.min())
    if min_count < 2:
        return {"macro_f1_cv": np.nan, "weighted_f1_cv": np.nan, "accuracy_cv": np.nan}

    n_splits = max(2, min(n_splits, min_count))
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

    pipe = build_lr_pipeline(work, features)
    pred = cross_val_predict(pipe, work[features], work[y_col], cv=cv, method="predict")
    return {
        "macro_f1_cv": float(f1_score(work[y_col], pred, average="macro")),
        "weighted_f1_cv": float(f1_score(work[y_col], pred, average="weighted")),
        "accuracy_cv": float(accuracy_score(work[y_col], pred)),
    }


def _statsmodels_signs_and_pvalues(
    df: pd.DataFrame, y_col: str, features: List[str], baseline: str
) -> Tuple[Dict[str, int], Dict[str, float], Dict[str, float]]:
    if not HAS_STATSMODELS:
        return {}, {}, {}

    work = df[features + [y_col]].dropna().copy()
    if work.empty:
        return {}, {}, {}

    x = pd.get_dummies(work[features], drop_first=True)
    x = sm.add_constant(x, has_constant="add")

    classes = sorted(work[y_col].unique().tolist())
    if baseline in classes:
        classes = [baseline] + [c for c in classes if c != baseline]
    y = pd.Categorical(work[y_col], categories=classes)

    try:
        model = sm.MNLogit(y, x)
        res = model.fit(disp=0, maxiter=400)
        params = res.params
        pvals = res.pvalues
    except Exception:
        return {}, {}, {}

    signs: Dict[str, int] = {}
    sig: Dict[str, float] = {}

    for col in params.columns:
        cls_name = classes[col + 1] if col + 1 < len(classes) else f"class_{col}"
        for idx in params.index:
            if idx == "const":
                continue
            key = f"{cls_name}::{idx}"
            signs[key] = int(np.sign(params.loc[idx, col]))
            sig[key] = float(pvals.loc[idx, col])

    fit = {
        "aic": float(getattr(res, "aic", np.nan)),
        "bic": float(getattr(res, "bic", np.nan)),
        "llf": float(getattr(res, "llf", np.nan)),
        "pseudo_r2": float(getattr(res, "prsquared", np.nan)),
    }
    return signs, sig, fit


def evaluate_spec(
    df: pd.DataFrame,
    *,
    y_col: str,
    features: List[str],
    baseline: str,
    spec_name: str,
    spec_type: str,
    notes: str = "",
    baseline_signs: Optional[Dict[str, int]] = None,
) -> ModelArtifacts:
    metrics = _sklearn_metrics(df=df, y_col=y_col, features=features)
    signs, pvals, fit = _statsmodels_signs_and_pvalues(df=df, y_col=y_col, features=features, baseline=baseline)
    metrics.update(fit)

    # Sign-direction stability against baseline configuration.
    if baseline_signs:
        compared = 0
        matched = 0
        for k, v in signs.items():
            if k in baseline_signs:
                compared += 1
                if baseline_signs[k] == v:
                    matched += 1
        metrics["direction_match_ratio"] = float(matched / compared) if compared else np.nan
    else:
        metrics["direction_match_ratio"] = np.nan

    if pvals:
        metrics["significant_ratio_p05"] = float(np.mean([v < 0.05 for v in pvals.values()]))
    else:
        metrics["significant_ratio_p05"] = np.nan

    metrics["n_obs"] = int(df[y_col].notna().sum())
    metrics["n_class"] = int(df[y_col].nunique())
    metrics["spec_name"] = spec_name
    metrics["spec_type"] = spec_type
    metrics["notes"] = notes

    return ModelArtifacts(metrics=metrics, coef_signs=signs, coef_pvalues=pvals)


def save_rows(rows: List[Dict[str, object]], out_csv: Path) -> None:
    frame = pd.DataFrame(rows)
    frame.to_csv(out_csv, index=False, encoding="utf-8-sig")


def load_yaml_or_default(config_path: Path, default_payload: Dict[str, object]) -> Dict[str, object]:
    if not config_path.exists():
        return default_payload
    try:
        import yaml

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data or default_payload
    except Exception:
        return default_payload
