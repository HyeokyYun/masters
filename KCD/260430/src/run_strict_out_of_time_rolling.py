"""Strict out-of-time rolling validation for the 260430 seasonality check.

Train on stores labeled by a same-calendar future window:

    feature: 2021-M for K weeks  -> label: 2022-M for K weeks

Then test on the next same-calendar roll:

    feature: 2022-M for K weeks  -> label: 2023-M for K weeks

This is stricter than the original 260430 seasonal check, which evaluated each
calendar-matched specification with store-level cross-validation.
"""
from __future__ import annotations

from pathlib import Path
import sys
import warnings

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_seasonal_window_analysis as seasonal  # noqa: E402


ROOT = seasonal.ROOT
BASE = seasonal.BASE
STRICT_DIR = BASE / "strict_rolling_validation"
TABLE_DIR = STRICT_DIR / "tables"
FIG_DIR = STRICT_DIR / "figures"
DOC_DIR = STRICT_DIR / "docs"
CLASSES = seasonal.CLASSES
SEED = seasonal.SEED

warnings.filterwarnings("ignore", message="Mean of empty slice", category=RuntimeWarning)


def ensure_dirs() -> None:
    for path in [TABLE_DIR, FIG_DIR, DOC_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def build_dataset(
    spec: seasonal.WindowSpec,
    sales_arr: np.ndarray,
    nc_arr: np.ndarray,
    cust_arr: np.ndarray,
    ids: np.ndarray,
) -> pd.DataFrame:
    feats = seasonal.extract_window_features(spec, sales_arr, nc_arr, cust_arr, ids)
    labels = seasonal.build_labels(spec, sales_arr, ids)
    return feats.merge(labels, on="public_id", how="inner")


def feature_columns(df: pd.DataFrame) -> list[str]:
    excluded = {
        "public_id",
        "outcome_3",
        "target_slope",
        "label_threshold",
        "feature_valid_weeks",
        "target_valid_weeks",
    }
    return [c for c in df.columns if c not in excluded]


def eval_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    proba: np.ndarray | None,
    proba_classes: np.ndarray | None,
) -> dict[str, float]:
    per = precision_recall_fscore_support(y_true, y_pred, labels=CLASSES, zero_division=0)
    row: dict[str, float] = {
        "accuracy": accuracy_score(y_true, y_pred),
        "macro_f1": f1_score(y_true, y_pred, average="macro", zero_division=0),
        "weighted_f1": f1_score(y_true, y_pred, average="weighted", zero_division=0),
    }
    if proba is not None and proba_classes is not None:
        try:
            proba_df = pd.DataFrame(proba, columns=proba_classes)
            proba_full = proba_df.reindex(columns=CLASSES, fill_value=0.0).to_numpy()
            y_bin = pd.get_dummies(pd.Series(y_true)).reindex(columns=CLASSES, fill_value=0).to_numpy()
            row["auc_ovr"] = roc_auc_score(y_bin, proba_full, multi_class="ovr")
        except Exception:
            row["auc_ovr"] = np.nan
    else:
        row["auc_ovr"] = np.nan
    for i, cls in enumerate(CLASSES):
        row[f"precision_{cls}"] = per[0][i]
        row[f"recall_{cls}"] = per[1][i]
        row[f"f1_{cls}"] = per[2][i]
        row[f"support_{cls}"] = float((y_true == cls).sum())
    return row


def label_distribution(df: pd.DataFrame, prefix: str) -> dict[str, float]:
    counts = df["outcome_3"].value_counts().reindex(CLASSES, fill_value=0)
    out: dict[str, float] = {f"{prefix}_n": float(len(df))}
    for cls, n in counts.items():
        out[f"{prefix}_{cls}_n"] = float(n)
        out[f"{prefix}_{cls}_share"] = float(n / len(df)) if len(df) else np.nan
    return out


def run_strict_validation() -> tuple[pd.DataFrame, pd.DataFrame]:
    print("[strict] loading weekly matrix", flush=True)
    sales, nc_ratio, customer, dates = seasonal.load_weekly_matrix()
    ids = sales.index.astype(str).to_numpy()
    sales_arr = sales.to_numpy(dtype=float)
    nc_arr = nc_ratio.to_numpy(dtype=float)
    cust_arr = customer.to_numpy(dtype=float)

    specs = seasonal.build_specs(dates)
    spec_lookup = {(s.base_year, s.start_month, s.window_weeks, s.lag_years): s for s in specs}

    rows: list[dict[str, object]] = []
    distribution_rows: list[dict[str, object]] = []

    for month in seasonal.START_MONTHS:
        for weeks in seasonal.WINDOW_WEEKS:
            train_spec = spec_lookup.get((2021, month, weeks, 1))
            test_spec = spec_lookup.get((2022, month, weeks, 1))
            if train_spec is None or test_spec is None:
                continue

            train = build_dataset(train_spec, sales_arr, nc_arr, cust_arr, ids)
            test = build_dataset(test_spec, sales_arr, nc_arr, cust_arr, ids)
            if len(train) < 500 or len(test) < 500:
                continue

            train_counts = train["outcome_3"].value_counts()
            test_counts = test["outcome_3"].value_counts()
            if len(train_counts) < 3 or len(test_counts) < 3:
                continue

            x_cols = feature_columns(train)
            X_train = train[x_cols].to_numpy(dtype=float)
            y_train = train["outcome_3"].to_numpy()
            X_test = test[x_cols].to_numpy(dtype=float)
            y_test = test["outcome_3"].to_numpy()

            models = {
                "dummy_most_frequent": DummyClassifier(strategy="most_frequent"),
                "balanced_logistic": make_pipeline(
                    StandardScaler(),
                    LogisticRegression(
                        max_iter=800,
                        class_weight="balanced",
                        solver="lbfgs",
                        random_state=SEED,
                    ),
                ),
            }

            for model_name, model in models.items():
                model.fit(X_train, y_train)
                pred = model.predict(X_test)
                proba = None
                proba_classes = None
                if hasattr(model, "predict_proba"):
                    proba = model.predict_proba(X_test)
                    if hasattr(model, "classes_"):
                        proba_classes = model.classes_
                    elif hasattr(model, "steps") and hasattr(model.steps[-1][1], "classes_"):
                        proba_classes = model.steps[-1][1].classes_

                row: dict[str, object] = {
                    "model": model_name,
                    "start_month": month,
                    "window_weeks": weeks,
                    "train_spec_id": train_spec.spec_id,
                    "test_spec_id": test_spec.spec_id,
                    "train_feature_start": train_spec.feature_start_date.date().isoformat(),
                    "train_feature_end": train_spec.feature_end_date.date().isoformat(),
                    "train_target_start": train_spec.target_start_date.date().isoformat(),
                    "train_target_end": train_spec.target_end_date.date().isoformat(),
                    "test_feature_start": test_spec.feature_start_date.date().isoformat(),
                    "test_feature_end": test_spec.feature_end_date.date().isoformat(),
                    "test_target_start": test_spec.target_start_date.date().isoformat(),
                    "test_target_end": test_spec.target_end_date.date().isoformat(),
                    "n_train": len(train),
                    "n_test": len(test),
                    "n_features": len(x_cols),
                }
                row.update(eval_predictions(y_test, pred, proba, proba_classes))
                rows.append(row)

            dist_row: dict[str, object] = {
                "start_month": month,
                "window_weeks": weeks,
                "train_spec_id": train_spec.spec_id,
                "test_spec_id": test_spec.spec_id,
            }
            dist_row.update(label_distribution(train, "train"))
            dist_row.update(label_distribution(test, "test"))
            distribution_rows.append(dist_row)

            print(
                f"[strict] m={month:02d} w={weeks:02d} "
                f"train={len(train):,} test={len(test):,}",
                flush=True,
            )

    results = pd.DataFrame(rows)
    distributions = pd.DataFrame(distribution_rows)
    if results.empty:
        raise RuntimeError("Strict rolling validation produced no rows.")
    return results, distributions


def make_figures(results: pd.DataFrame) -> None:
    sns.set_theme(style="whitegrid")
    main = results[results["model"] == "balanced_logistic"].copy()

    for metric, fname, title in [
        ("macro_f1", "strict_macro_f1_heatmap.png", "Strict out-of-time Macro-F1"),
        (
            "recall_Decline",
            "strict_decline_recall_heatmap.png",
            "Strict out-of-time Decline recall",
        ),
        ("auc_ovr", "strict_auc_heatmap.png", "Strict out-of-time AUC OvR"),
    ]:
        pivot = main.pivot(index="window_weeks", columns="start_month", values=metric).sort_index()
        plt.figure(figsize=(11, 5.8))
        sns.heatmap(pivot, annot=True, fmt=".3f", cmap="viridis", cbar_kws={"label": metric})
        plt.title(title)
        plt.xlabel("Feature start month")
        plt.ylabel("Window length (weeks)")
        plt.tight_layout()
        plt.savefig(FIG_DIR / fname, dpi=220)
        plt.close()

    by_window = (
        main.groupby("window_weeks", as_index=False)
        .agg(macro_f1=("macro_f1", "mean"), recall_Decline=("recall_Decline", "mean"))
        .melt(id_vars="window_weeks", var_name="metric", value_name="value")
    )
    plt.figure(figsize=(8.5, 4.8))
    sns.lineplot(data=by_window, x="window_weeks", y="value", hue="metric", marker="o")
    plt.ylim(0, max(0.75, float(by_window["value"].max()) + 0.05))
    plt.title("Strict rolling performance by observation window")
    plt.xlabel("Window length (weeks)")
    plt.ylabel("Mean score across start months")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "strict_by_window_line.png", dpi=220)
    plt.close()

    comp = results[results["model"].isin(["dummy_most_frequent", "balanced_logistic"])].copy()
    comp = comp.groupby("model", as_index=False).agg(
        macro_f1=("macro_f1", "mean"),
        weighted_f1=("weighted_f1", "mean"),
        recall_Decline=("recall_Decline", "mean"),
    )
    comp_long = comp.melt(id_vars="model", var_name="metric", value_name="value")
    plt.figure(figsize=(8.5, 4.8))
    sns.barplot(data=comp_long, x="metric", y="value", hue="model")
    plt.ylim(0, max(0.75, float(comp_long["value"].max()) + 0.05))
    plt.title("Strict rolling model vs majority baseline")
    plt.xlabel("")
    plt.ylabel("Mean score")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "strict_model_vs_dummy.png", dpi=220)
    plt.close()


def write_report(results: pd.DataFrame, distributions: pd.DataFrame) -> None:
    main = results[results["model"] == "balanced_logistic"].copy()
    dummy = results[results["model"] == "dummy_most_frequent"].copy()
    best_macro = main.sort_values("macro_f1", ascending=False).head(8)
    best_decline = main.sort_values("recall_Decline", ascending=False).head(8)
    by_window = main.groupby("window_weeks", as_index=False).agg(
        macro_f1_mean=("macro_f1", "mean"),
        macro_f1_max=("macro_f1", "max"),
        auc_ovr_mean=("auc_ovr", "mean"),
        auc_ovr_max=("auc_ovr", "max"),
        decline_recall_mean=("recall_Decline", "mean"),
        decline_recall_max=("recall_Decline", "max"),
    )
    by_month = main.groupby("start_month")[["macro_f1", "recall_Decline"]].mean()
    dummy_mean = dummy[["macro_f1", "weighted_f1", "recall_Decline"]].mean()
    main_mean = main[["macro_f1", "weighted_f1", "auc_ovr", "recall_Decline"]].mean()

    text = f"""# Strict Out-of-Time Rolling Validation

## Purpose

This run adds the stricter validation requested after the 260430 meeting.
The model is trained on one calendar-aligned future relation and tested on the
next calendar-aligned future relation:

- Train: `2021-M-Kweeks feature -> 2022-M-Kweeks label`
- Test: `2022-M-Kweeks feature -> 2023-M-Kweeks label`

This differs from the earlier `260430` seasonal check, which used store-level
cross-validation inside each calendar-matched specification.

## Run Summary

- Evaluated start-month/window pairs: {main.shape[0]:,}
- Start months covered: {main['start_month'].nunique():,}
- Window lengths covered: {main['window_weeks'].nunique():,}
- Model: balanced logistic regression
- Baseline: majority-class dummy classifier

## Mean Performance

| model | macro_f1 | weighted_f1 | auc_ovr | decline_recall |
|---|---:|---:|---:|---:|
| majority baseline | {dummy_mean['macro_f1']:.3f} | {dummy_mean['weighted_f1']:.3f} | n/a | {dummy_mean['recall_Decline']:.3f} |
| strict rolling logistic | {main_mean['macro_f1']:.3f} | {main_mean['weighted_f1']:.3f} | {main_mean['auc_ovr']:.3f} | {main_mean['recall_Decline']:.3f} |

## Best Windows By Macro-F1

{best_macro[['start_month','window_weeks','n_train','n_test','macro_f1','weighted_f1','auc_ovr','recall_Growth','recall_Stable','recall_Decline']].to_markdown(index=False)}

## Best Windows By Decline Recall

{best_decline[['start_month','window_weeks','n_train','n_test','macro_f1','weighted_f1','auc_ovr','recall_Growth','recall_Stable','recall_Decline']].to_markdown(index=False)}

## By Window Length

{by_window.round(3).to_markdown(index=False)}

## By Start Month

{by_month.round(3).to_markdown()}

## Interpretation

The strict out-of-time result should be read as the most conservative
seasonality robustness check. It asks whether a relationship learned from
`2021 -> 2022` transfers to the next same-calendar roll, `2022 -> 2023`.

If performance is lower than the earlier within-specification seasonal CV,
that is expected: the test year is held out as a future calendar period rather
than mixed into cross-validation. The thesis claim should therefore avoid
saying that seasonal rolling improves performance. The stronger and safer claim
is:

> Once seasonality and future-period transfer are both imposed, predictive
> performance weakens, but the model still outperforms a majority baseline and
> retains non-zero decline detection. The original high hybrid scores should be
> treated as an upper-bound exploratory result, while strict rolling provides
> the conservative robustness evidence.

## Files

- `tables/strict_rolling_results.csv`
- `tables/strict_rolling_label_distribution.csv`
- `figures/strict_macro_f1_heatmap.png`
- `figures/strict_decline_recall_heatmap.png`
- `figures/strict_auc_heatmap.png`
- `figures/strict_by_window_line.png`
- `figures/strict_model_vs_dummy.png`
"""
    (DOC_DIR / "strict_out_of_time_rolling_report.md").write_text(text, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    results, distributions = run_strict_validation()
    results.to_csv(TABLE_DIR / "strict_rolling_results.csv", index=False, encoding="utf-8-sig")
    distributions.to_csv(
        TABLE_DIR / "strict_rolling_label_distribution.csv",
        index=False,
        encoding="utf-8-sig",
    )
    make_figures(results)
    write_report(results, distributions)
    best = (
        results[results["model"] == "balanced_logistic"]
        .sort_values("macro_f1", ascending=False)
        .iloc[0]
    )
    print(
        "[strict] best:",
        f"m={int(best['start_month']):02d}",
        f"w={int(best['window_weeks'])}",
        f"macro_f1={best['macro_f1']:.3f}",
        f"decline_recall={best['recall_Decline']:.3f}",
        flush=True,
    )
    print(f"[strict] saved under {STRICT_DIR}", flush=True)


if __name__ == "__main__":
    main()
