from __future__ import annotations

import inspect
from typing import Callable, Dict, Iterable, Tuple

import matplotlib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import KFold, StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from research_pipeline.clustering import run_clustering_bundle
from research_pipeline.config import get_work_dir
from research_pipeline.lifecycle import build_lifecycle_bundle

try:
    import statsmodels.api as sm

    HAS_STATSMODELS = True
except Exception:
    HAS_STATSMODELS = False


def _compatible_logistic_regression(**kwargs) -> LogisticRegression:
    valid = inspect.signature(LogisticRegression.__init__).parameters
    filtered = {k: v for k, v in kwargs.items() if k in valid}
    return LogisticRegression(**filtered)


def _build_one_hot_encoder() -> OneHotEncoder:
    params = inspect.signature(OneHotEncoder.__init__).parameters
    if "sparse_output" in params:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=True)
    return OneHotEncoder(handle_unknown="ignore", sparse=True)


def default_feature_columns(df: pd.DataFrame, cfg: Dict[str, object]) -> list[str]:
    features_cfg = cfg["features"]
    candidates = features_cfg["numeric_candidates"] + features_cfg["categorical_candidates"]
    return [col for col in candidates if col in df.columns]


def unique_existing_features(df: pd.DataFrame, features: Iterable[str]) -> list[str]:
    seen = set()
    ordered = []
    for col in features:
        if col in df.columns and col not in seen:
            ordered.append(col)
            seen.add(col)
    return ordered


def _numeric_cluster_screen_score(series: pd.Series, cluster_series: pd.Series) -> float:
    work = pd.DataFrame({"value": series, "cluster": cluster_series}).dropna()
    if len(work) < 2 or work["cluster"].nunique() < 2:
        return np.nan
    grand_mean = float(work["value"].mean())
    totals = work.groupby("cluster")["value"].agg(["mean", "count"])
    ss_between = float((totals["count"] * np.square(totals["mean"] - grand_mean)).sum())
    ss_total = float(np.square(work["value"] - grand_mean).sum())
    if ss_total == 0:
        return np.nan
    return ss_between / ss_total


def _categorical_cluster_screen_score(series: pd.Series, cluster_series: pd.Series) -> float:
    work = pd.DataFrame({"value": series, "cluster": cluster_series}).dropna()
    if work.empty or work["cluster"].nunique() < 2 or work["value"].nunique() < 2:
        return np.nan
    table = pd.crosstab(work["value"], work["cluster"])
    n = float(table.to_numpy().sum())
    if n == 0 or min(table.shape) < 2:
        return np.nan
    observed = table.to_numpy(dtype=float)
    expected = np.outer(observed.sum(axis=1), observed.sum(axis=0)) / n
    valid = expected > 0
    chi2 = float(np.divide(np.square(observed - expected), expected, out=np.zeros_like(observed), where=valid).sum())
    denom = max(min(table.shape[0] - 1, table.shape[1] - 1), 1)
    return float(np.sqrt((chi2 / n) / denom))


def _build_cluster_numeric_summary(df: pd.DataFrame, cluster_col: str, features: list[str]) -> pd.DataFrame:
    rows = []
    for feature in features:
        grouped = (
            df[[cluster_col, feature]]
            .dropna(subset=[cluster_col, feature])
            .groupby(cluster_col)[feature]
            .agg(["mean", "median", "std", "count"])
            .reset_index()
        )
        for row in grouped.itertuples(index=False):
            rows.append(
                {
                    "cluster": getattr(row, cluster_col),
                    "feature": feature,
                    "mean": getattr(row, "mean"),
                    "median": getattr(row, "median"),
                    "std": getattr(row, "std"),
                    "count": getattr(row, "count"),
                }
            )
    return pd.DataFrame(rows)


def _build_cluster_categorical_summary(df: pd.DataFrame, cluster_col: str, features: list[str]) -> pd.DataFrame:
    rows = []
    for feature in features:
        grouped = (
            df[[cluster_col, feature]]
            .dropna(subset=[cluster_col, feature])
            .groupby([cluster_col, feature])
            .size()
            .rename("count")
            .reset_index()
        )
        if grouped.empty:
            continue
        grouped["cluster_total"] = grouped.groupby(cluster_col)["count"].transform("sum")
        grouped["share_within_cluster"] = grouped["count"] / grouped["cluster_total"].replace(0, np.nan)
        for row in grouped.itertuples(index=False):
            rows.append(
                {
                    "cluster": getattr(row, cluster_col),
                    "feature": feature,
                    "level": getattr(row, feature),
                    "count": row.count,
                    "share_within_cluster": row.share_within_cluster,
                }
            )
    return pd.DataFrame(rows)


def build_cluster_screening_bundle(
    df: pd.DataFrame,
    cfg: Dict[str, object],
    cluster_col: str,
    features: list[str],
) -> Dict[str, pd.DataFrame | list[str]]:
    work = df.dropna(subset=[cluster_col]).copy()
    candidates = [col for col in unique_existing_features(work, features) if col != cluster_col]
    top_numeric = int(cfg["analysis"].get("cluster_screen_top_numeric", 8))
    top_categorical = int(cfg["analysis"].get("cluster_screen_top_categorical", 4))

    score_rows = []
    for feature in candidates:
        non_null = work[[cluster_col, feature]].dropna()
        if non_null.empty:
            continue
        if pd.api.types.is_numeric_dtype(work[feature]):
            feature_type = "numeric"
            score = _numeric_cluster_screen_score(work[feature], work[cluster_col])
            metric = "eta_squared_by_cluster"
        else:
            feature_type = "categorical"
            score = _categorical_cluster_screen_score(work[feature], work[cluster_col])
            metric = "cramers_v_with_cluster"
        score_rows.append(
            {
                "feature": feature,
                "feature_type": feature_type,
                "screening_metric": metric,
                "score": score,
                "non_null_obs": int(len(non_null)),
                "n_levels": int(non_null[feature].nunique()),
            }
        )

    scores = pd.DataFrame(score_rows)
    if scores.empty:
        return {
            "scores": scores,
            "selected_features": candidates,
            "selected_features_table": pd.DataFrame(columns=["feature", "feature_type", "score", "selection_rank"]),
            "numeric_summary": pd.DataFrame(columns=["cluster", "feature", "mean", "median", "std", "count"]),
            "categorical_summary": pd.DataFrame(columns=["cluster", "feature", "level", "count", "share_within_cluster"]),
        }

    scores = scores.sort_values(["feature_type", "score", "feature"], ascending=[True, False, True]).reset_index(drop=True)
    numeric_scores = scores[scores["feature_type"] == "numeric"].sort_values("score", ascending=False)
    categorical_scores = scores[scores["feature_type"] == "categorical"].sort_values("score", ascending=False)

    selected_numeric = numeric_scores.head(top_numeric)["feature"].tolist()
    selected_categorical = categorical_scores.head(top_categorical)["feature"].tolist()
    selected_features = selected_numeric + [feature for feature in selected_categorical if feature not in selected_numeric]
    if not selected_features:
        selected_features = candidates[: min(len(candidates), top_numeric + top_categorical)]

    selected_features_table = scores[scores["feature"].isin(selected_features)].copy()
    selected_features_table["selection_rank"] = (
        selected_features_table["feature"].map({feature: idx + 1 for idx, feature in enumerate(selected_features)})
    )
    selected_features_table = selected_features_table.sort_values("selection_rank").reset_index(drop=True)

    numeric_summary = _build_cluster_numeric_summary(work, cluster_col, selected_numeric)
    categorical_summary = _build_cluster_categorical_summary(work, cluster_col, selected_categorical)
    return {
        "scores": scores,
        "selected_features": selected_features,
        "selected_features_table": selected_features_table,
        "numeric_summary": numeric_summary,
        "categorical_summary": categorical_summary,
    }


def build_preprocessor(df: pd.DataFrame, features: Iterable[str]) -> ColumnTransformer:
    features = list(features)
    numeric = [col for col in features if pd.api.types.is_numeric_dtype(df[col])]
    categorical = [col for col in features if col not in numeric]
    return ColumnTransformer(
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
                        ("ohe", _build_one_hot_encoder()),
                    ]
                ),
                categorical,
            ),
        ],
        remainder="drop",
    )


def evaluate_classification_models(
    df: pd.DataFrame,
    target: str,
    features: list[str],
    random_state: int,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, np.ndarray], pd.DataFrame]:
    features = unique_existing_features(df, features)
    work = df[features + [target]].dropna(subset=[target]).copy()
    if work.empty or work[target].nunique() < 2:
        return (
            pd.DataFrame([{"model": "NA", "n_obs": len(work), "note": "insufficient target classes"}]),
            pd.DataFrame(),
            {},
            pd.DataFrame(columns=["feature", "importance", "model"]),
        )
    class_counts = work[target].value_counts()
    min_count = int(class_counts.min())
    if min_count < 2:
        return (
            pd.DataFrame([{"model": "NA", "n_obs": len(work), "note": "a class has fewer than 2 observations"}]),
            pd.DataFrame(),
            {},
            pd.DataFrame(columns=["feature", "importance", "model"]),
        )
    n_splits = max(2, min(5, min_count))
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)

    models = {
        "LogisticRegression": _compatible_logistic_regression(
            multi_class="multinomial",
            solver="lbfgs",
            max_iter=2000,
            class_weight="balanced",
            random_state=random_state,
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=250,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1,
        ),
        "ExtraTrees": ExtraTreesClassifier(
            n_estimators=300,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1,
        ),
    }

    metrics_rows = []
    report_rows = []
    confusion_lookup = {}
    feature_importance_frames: list[pd.DataFrame] = []

    for model_name, model in models.items():
        pipe = Pipeline([("pre", build_preprocessor(work, features)), ("model", model)])
        pred = cross_val_predict(pipe, work[features], work[target], cv=cv, method="predict")

        metrics_rows.append(
            {
                "model": model_name,
                "n_obs": len(work),
                "accuracy": float(accuracy_score(work[target], pred)),
                "macro_f1": float(f1_score(work[target], pred, average="macro")),
                "weighted_f1": float(f1_score(work[target], pred, average="weighted")),
            }
        )
        report = classification_report(work[target], pred, output_dict=True, zero_division=0)
        for label, values in report.items():
            if isinstance(values, dict):
                report_rows.append({"model": model_name, "label": label, **values})
        confusion_lookup[model_name] = confusion_matrix(
            work[target],
            pred,
            labels=sorted(work[target].dropna().unique().tolist()),
        )

        pipe.fit(work[features], work[target])
        fitted_model = pipe.named_steps["model"]
        if hasattr(fitted_model, "feature_importances_"):
            pre = pipe.named_steps["pre"]
            feature_names = pre.get_feature_names_out()
            importances = fitted_model.feature_importances_
            feature_importance_frames.append(
                pd.DataFrame(
                    {"feature": feature_names, "importance": importances, "model": model_name}
                ).sort_values("importance", ascending=False)
            )

    feature_importance = (
        pd.concat(feature_importance_frames, ignore_index=True)
        if feature_importance_frames
        else pd.DataFrame(columns=["feature", "importance", "model"])
    )
    return pd.DataFrame(metrics_rows), pd.DataFrame(report_rows), confusion_lookup, feature_importance


def evaluate_regression_models(
    df: pd.DataFrame,
    target: str,
    features: list[str],
    random_state: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    reg_features = unique_existing_features(df, [col for col in features if col != target])
    work = df[reg_features + [target]].dropna(subset=[target]).copy()
    if len(work) < 2:
        return (
            pd.DataFrame([{"model": "NA", "n_obs": len(work), "note": "insufficient observations"}]),
            pd.DataFrame(columns=["feature", "importance", "model"]),
        )
    cv = KFold(n_splits=min(5, len(work)), shuffle=True, random_state=random_state)
    models = {
        "Ridge": Ridge(alpha=1.0),
        "RandomForestRegressor": RandomForestRegressor(
            n_estimators=250,
            random_state=random_state,
            n_jobs=-1,
        ),
    }
    metrics_rows = []
    feature_importance_frames: list[pd.DataFrame] = []

    for model_name, model in models.items():
        pipe = Pipeline([("pre", build_preprocessor(work, reg_features)), ("model", model)])
        pred = cross_val_predict(pipe, work[reg_features], work[target], cv=cv, method="predict")
        metrics_rows.append(
            {
                "model": model_name,
                "n_obs": len(work),
                "mae": float(mean_absolute_error(work[target], pred)),
                "rmse": float(np.sqrt(mean_squared_error(work[target], pred))),
                "r2": float(r2_score(work[target], pred)),
            }
        )

        pipe.fit(work[reg_features], work[target])
        fitted_model = pipe.named_steps["model"]
        if hasattr(fitted_model, "feature_importances_"):
            pre = pipe.named_steps["pre"]
            feature_names = pre.get_feature_names_out()
            importances = fitted_model.feature_importances_
            feature_importance_frames.append(
                pd.DataFrame(
                    {"feature": feature_names, "importance": importances, "model": model_name}
                ).sort_values("importance", ascending=False)
            )

    feature_importance = (
        pd.concat(feature_importance_frames, ignore_index=True)
        if feature_importance_frames
        else pd.DataFrame(columns=["feature", "importance", "model"])
    )
    return pd.DataFrame(metrics_rows), feature_importance


def evaluate_classification_specs(
    df: pd.DataFrame,
    target: str,
    feature_specs: Dict[str, list[str]],
    random_state: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    metrics_frames = []
    report_frames = []
    for spec_name, spec_features in feature_specs.items():
        metrics, reports, _, _ = evaluate_classification_models(
            df=df,
            target=target,
            features=spec_features,
            random_state=random_state,
        )
        if not metrics.empty:
            metrics = metrics.copy()
            metrics["feature_spec"] = spec_name
            metrics["n_features"] = len(unique_existing_features(df, spec_features))
            metrics_frames.append(metrics)
        if not reports.empty:
            reports = reports.copy()
            reports["feature_spec"] = spec_name
            report_frames.append(reports)
    metrics_df = pd.concat(metrics_frames, ignore_index=True) if metrics_frames else pd.DataFrame()
    reports_df = pd.concat(report_frames, ignore_index=True) if report_frames else pd.DataFrame()
    return metrics_df, reports_df


def evaluate_regression_specs(
    df: pd.DataFrame,
    target: str,
    feature_specs: Dict[str, list[str]],
    random_state: int,
) -> pd.DataFrame:
    frames = []
    for spec_name, spec_features in feature_specs.items():
        metrics, _ = evaluate_regression_models(
            df=df,
            target=target,
            features=spec_features,
            random_state=random_state,
        )
        if metrics.empty:
            continue
        metrics = metrics.copy()
        metrics["feature_spec"] = spec_name
        metrics["n_features"] = len(unique_existing_features(df, [col for col in spec_features if col != target]))
        frames.append(metrics)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def fit_ols(df: pd.DataFrame, target: str, features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not HAS_STATSMODELS:
        return (
            pd.DataFrame([{"model": "OLS", "note": "statsmodels not installed"}]),
            pd.DataFrame(columns=["term", "coef", "pvalue"]),
        )
    numeric_features = [col for col in features if col != target and pd.api.types.is_numeric_dtype(df[col])]
    work = df[numeric_features + [target]].dropna(subset=[target]).copy()
    x = work[numeric_features].fillna(work[numeric_features].median())
    x = sm.add_constant(x, has_constant="add")
    y = work[target]
    model = sm.OLS(y, x).fit()
    metrics = pd.DataFrame(
        [
            {
                "model": "OLS",
                "n_obs": int(model.nobs),
                "r2": float(model.rsquared),
                "adj_r2": float(model.rsquared_adj),
                "aic": float(model.aic),
                "bic": float(model.bic),
            }
        ]
    )
    coef = pd.DataFrame(
        {
            "term": model.params.index,
            "coef": model.params.values,
            "pvalue": model.pvalues.values,
            "std_err": model.bse.values,
        }
    )
    return metrics, coef


def fit_multinomial_logit(df: pd.DataFrame, target: str, features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    if not HAS_STATSMODELS:
        return (
            pd.DataFrame([{"model": "MNLogit", "note": "statsmodels not installed"}]),
            pd.DataFrame(columns=["class", "term", "coef", "pvalue"]),
            "statsmodels not installed",
        )

    work = df[features + [target]].dropna().copy()
    x = pd.get_dummies(work[features], drop_first=True)
    if x.empty or work[target].nunique() < 3:
        return (
            pd.DataFrame([{"model": "MNLogit", "note": "insufficient classes or features"}]),
            pd.DataFrame(columns=["class", "term", "coef", "pvalue"]),
            "insufficient classes or features",
        )
    x = x.replace([np.inf, -np.inf], np.nan)
    x = x.apply(pd.to_numeric, errors="coerce")
    x = x.fillna(x.median(numeric_only=True)).fillna(0.0).astype(float)
    x = sm.add_constant(x, has_constant="add")

    y_cat = pd.Categorical(work[target])
    classes = list(y_cat.categories)
    y = pd.Series(y_cat.codes, index=work.index, name=target).astype(int)
    valid = y >= 0
    x = x.loc[valid].copy()
    y = y.loc[valid].copy()

    try:
        model = sm.MNLogit(y, x)
        result = model.fit(disp=0, maxiter=300)
    except Exception as exc:
        return (
            pd.DataFrame([{"model": "MNLogit", "note": f"fit failed: {exc}"}]),
            pd.DataFrame(columns=["class", "term", "coef", "pvalue"]),
            f"fit failed: {exc}",
        )

    coef_rows = []
    for class_index, class_name in enumerate(classes[1:]):
        for term in result.params.index:
            coef_rows.append(
                {
                    "class": class_name,
                    "term": term,
                    "coef": float(result.params.iloc[:, class_index].loc[term]),
                    "pvalue": float(result.pvalues.iloc[:, class_index].loc[term]),
                }
            )

    metrics = pd.DataFrame(
        [
            {
                "model": "MNLogit",
                "n_obs": int(result.nobs),
                "aic": float(result.aic),
                "bic": float(result.bic),
                "llf": float(result.llf),
                "pseudo_r2": float(getattr(result, "prsquared", np.nan)),
            }
        ]
    )
    return metrics, pd.DataFrame(coef_rows), str(result.summary())


def save_confusion_matrices(confusions: dict[str, np.ndarray], class_labels: list[str], prefix: str) -> None:
    work_dir = get_work_dir()
    for model_name, matrix in confusions.items():
        fig, ax = plt.subplots(figsize=(6, 5))
        im = ax.imshow(matrix, cmap="Blues")
        ax.set_xticks(range(len(class_labels)))
        ax.set_xticklabels(class_labels, rotation=45, ha="right")
        ax.set_yticks(range(len(class_labels)))
        ax.set_yticklabels(class_labels)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
        ax.set_title(f"{prefix} Confusion Matrix: {model_name}")
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                ax.text(j, i, str(matrix[i, j]), ha="center", va="center", color="black")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        fig.tight_layout()
        fig.savefig(work_dir / "outputs" / "figures" / f"{prefix.lower()}_confusion_matrix_{model_name.lower()}.png", dpi=180)
        plt.close(fig)


def save_feature_importance_plot(feature_importance: pd.DataFrame, out_name: str) -> None:
    work_dir = get_work_dir()
    if feature_importance.empty:
        return
    top = feature_importance.sort_values("importance", ascending=False).head(20)
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(top["feature"][::-1], top["importance"][::-1], color="#2f5c85")
    ax.set_title(out_name.replace("_", " ").title())
    ax.set_xlabel("Importance")
    fig.tight_layout()
    fig.savefig(work_dir / "outputs" / "figures" / f"{out_name}.png", dpi=180)
    plt.close(fig)


def run_factor_analysis_bundle(cfg: Dict[str, object], log: Callable[[str], None]) -> Dict[str, pd.DataFrame | str]:
    work_dir = get_work_dir()
    analysis_path = work_dir / "outputs" / "tables" / "lifecycle_analysis_table.csv"
    if analysis_path.exists():
        df = pd.read_csv(analysis_path)
        if "public_id" in df.columns:
            df["public_id"] = df["public_id"].astype(str)
    else:
        log("Lifecycle analysis table not found. Building Step 2 outputs on the fly.")
        df = build_lifecycle_bundle(cfg, log)["analysis_table"]

    cluster_path = work_dir / "outputs" / "tables" / "trajectory_cluster_labels.csv"
    if cluster_path.exists():
        clusters = pd.read_csv(cluster_path)
        if "public_id" in clusters.columns:
            clusters["public_id"] = clusters["public_id"].astype(str)
    else:
        log("Cluster labels not found. Building Step 3 outputs on the fly.")
        clusters = run_clustering_bundle(cfg, log)["labels"]
    df = df.drop(columns=["cluster"], errors="ignore").merge(clusters[["public_id", "cluster"]], on="public_id", how="left")

    features = unique_existing_features(df, default_feature_columns(df, cfg))
    features_no_cluster = [col for col in features if col != "cluster"]
    cluster_screening = build_cluster_screening_bundle(df, cfg, "cluster", features_no_cluster)
    screened_features = unique_existing_features(df, cluster_screening["selected_features"])
    classification_specs = {
        "base_without_cluster": features_no_cluster,
        "base_with_cluster": features,
    }
    screened_classification_specs = {
        "cluster_screened": screened_features,
        "cluster_screened_plus_cluster": unique_existing_features(df, screened_features + ["cluster"]),
    }
    regression_specs = {
        "base_with_cluster": features,
        "cluster_screened": screened_features,
        "cluster_screened_plus_cluster": unique_existing_features(df, screened_features + ["cluster"]),
    }
    random_state = int(cfg["analysis"]["random_state"])

    life_cycle_summary = (
        df.groupby("life_cycle_category")[["avg_sales_total", "growth_rate", "avg_customer", "delivery_ratio"]]
        .agg(["mean", "median", "count"])
        .reset_index()
    )
    life_cycle_summary.columns = ["life_cycle_category"] + [f"{a}_{b}" for a, b in life_cycle_summary.columns.tolist()[1:]]

    cluster_summary = (
        df.groupby("cluster")[["avg_sales_total", "growth_rate", "avg_customer", "delivery_ratio"]]
        .agg(["mean", "median", "count"])
        .reset_index()
    )
    cluster_summary.columns = ["cluster"] + [f"{a}_{b}" for a, b in cluster_summary.columns.tolist()[1:]]

    cls_metrics, cls_reports, confusions, feature_importance = evaluate_classification_models(
        df=df,
        target="life_cycle_category",
        features=features,
        random_state=random_state,
    )
    cluster_ablation_metrics, cluster_ablation_reports = evaluate_classification_specs(
        df=df,
        target="life_cycle_category",
        feature_specs=classification_specs,
        random_state=random_state,
    )
    cluster_screened_metrics, cluster_screened_reports = evaluate_classification_specs(
        df=df,
        target="life_cycle_category",
        feature_specs=screened_classification_specs,
        random_state=random_state,
    )
    save_confusion_matrices(confusions, sorted(df["life_cycle_category"].dropna().unique().tolist()), "life_cycle")
    save_feature_importance_plot(feature_importance[feature_importance["model"] == "RandomForest"], "life_cycle_feature_importance")

    reg_metrics_ml, reg_importance = evaluate_regression_models(
        df=df,
        target="growth_rate",
        features=features,
        random_state=random_state,
    )
    reg_screened_metrics = evaluate_regression_specs(
        df=df,
        target="growth_rate",
        feature_specs=regression_specs,
        random_state=random_state,
    )
    reg_metrics_ols, reg_coef = fit_ols(df, target="growth_rate", features=features)
    reg_metrics = pd.concat([reg_metrics_ml, reg_metrics_ols], ignore_index=True)
    save_feature_importance_plot(reg_importance[reg_importance["model"] == "RandomForestRegressor"], "growth_rate_feature_importance")

    mnlogit_metrics, mnlogit_coef, mnlogit_summary = fit_multinomial_logit(
        df=df,
        target="life_cycle_category",
        features=features,
    )
    log(f"Factor-analysis rows: {len(df):,}")

    return {
        "life_cycle_summary": life_cycle_summary,
        "cluster_summary": cluster_summary,
        "cluster_feature_screening": cluster_screening["scores"],
        "cluster_selected_features": cluster_screening["selected_features_table"],
        "cluster_selected_numeric_summary": cluster_screening["numeric_summary"],
        "cluster_selected_categorical_summary": cluster_screening["categorical_summary"],
        "classification_metrics": cls_metrics,
        "classification_reports": cls_reports,
        "cluster_ablation_metrics": cluster_ablation_metrics,
        "cluster_ablation_reports": cluster_ablation_reports,
        "cluster_screened_classification_metrics": cluster_screened_metrics,
        "cluster_screened_classification_reports": cluster_screened_reports,
        "feature_importance": feature_importance,
        "regression_metrics": reg_metrics,
        "regression_coefficients": reg_coef,
        "cluster_screened_regression_metrics": reg_screened_metrics,
        "mnlogit_metrics": mnlogit_metrics,
        "mnlogit_coefficients": mnlogit_coef,
        "mnlogit_summary": mnlogit_summary,
    }
