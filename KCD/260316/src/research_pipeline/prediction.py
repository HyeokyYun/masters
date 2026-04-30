from __future__ import annotations

import pickle
from typing import Callable, Dict

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from research_pipeline.config import get_work_dir
from research_pipeline.clustering import build_trajectory_matrix, cluster_trajectories
from research_pipeline.data_prep import (
    META_RENAME_MAP,
    build_analysis_inputs,
    prepare_weekly_panel,
    slice_panel_by_week,
    summarize_store_panel,
)
from research_pipeline.io_utils import ensure_layout
from research_pipeline.lifecycle import build_lifecycle_bundle
from research_pipeline.modeling import (
    _compatible_logistic_regression,
    build_cluster_screening_bundle,
    build_preprocessor,
    default_feature_columns,
    evaluate_classification_models,
    evaluate_classification_specs,
    evaluate_regression_models,
    evaluate_regression_specs,
    save_confusion_matrices,
    save_feature_importance_plot,
    unique_existing_features,
)


def build_early_cluster_labels(panel: pd.DataFrame, cfg: Dict[str, object]) -> pd.DataFrame:
    early_window = int(cfg["analysis"]["early_window"])
    min_weeks = max(8, early_window // 2)
    n_clusters = int(cfg["analysis"]["cluster_k"])
    random_state = int(cfg["analysis"]["random_state"])
    matrix = build_trajectory_matrix(panel, max_weeks=early_window, min_weeks=min_weeks)
    labels, _, method = cluster_trajectories(matrix, n_clusters=n_clusters, random_state=random_state)
    return pd.DataFrame(
        {
            "public_id": matrix.index.astype(str),
            "early_cluster": labels.astype(int),
            "early_cluster_method": method,
        }
    )


def build_prediction_dataset(cfg: Dict[str, object], log: Callable[[str], None]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    work_dir = get_work_dir()
    panel_path = work_dir / "outputs" / "tables" / "store_week_panel.parquet"
    lifecycle_path = work_dir / "outputs" / "tables" / "lifecycle_analysis_table.csv"

    if panel_path.exists():
        panel = pd.read_parquet(panel_path)
    else:
        log("Panel not found. Building Step 1 outputs on the fly.")
        panel = build_analysis_inputs(cfg, log)["panel"]

    if lifecycle_path.exists():
        lifecycle_table = pd.read_csv(lifecycle_path)
        if "public_id" in lifecycle_table.columns:
            lifecycle_table["public_id"] = lifecycle_table["public_id"].astype(str)
    else:
        log("Lifecycle table not found. Building Step 2 outputs on the fly.")
        lifecycle_table = build_lifecycle_bundle(cfg, log)["analysis_table"]

    early_window = int(cfg["analysis"]["early_window"])
    future_window = int(cfg["analysis"]["future_window"])

    early_panel = slice_panel_by_week(panel, 0, early_window)
    early_features = summarize_store_panel(early_panel, min_weeks=max(8, early_window // 2))
    early_cluster_labels = build_early_cluster_labels(panel, cfg)
    early_features = early_features.merge(early_cluster_labels, on="public_id", how="left")

    future_panel = slice_panel_by_week(panel, early_window, early_window + future_window)
    future_targets = (
        future_panel.groupby("public_id")
        .agg(
            future_avg_sales=("sales_total", "mean"),
            future_total_sales=("sales_total", "sum"),
            future_weeks=("sales_total", "count"),
        )
        .reset_index()
    )

    prediction_df = early_features.merge(
        lifecycle_table[["public_id", "life_cycle_category", "final_code"]],
        on="public_id",
        how="inner",
    ).merge(future_targets, on="public_id", how="inner")
    prediction_df = prediction_df[prediction_df["future_weeks"] >= max(4, future_window // 2)].copy()
    prediction_df["future_growth_rate"] = (
        prediction_df["future_avg_sales"] - prediction_df["avg_sales_total"]
    ) / prediction_df["avg_sales_total"].replace(0, np.nan)
    return early_features, prediction_df, early_cluster_labels


def persist_example_classifier(
    df: pd.DataFrame,
    features: list[str],
    target: str,
    cfg: Dict[str, object],
) -> None:
    work_dir = get_work_dir()
    ensure_layout(work_dir)
    model = Pipeline(
        [
            ("pre", build_preprocessor(df, features)),
            (
                "model",
                _compatible_logistic_regression(
                    multi_class="multinomial",
                    solver="lbfgs",
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=int(cfg["analysis"]["random_state"]),
                ),
            ),
        ]
    )
    work = df[features + [target]].dropna(subset=[target]).copy()
    if work.empty or work[target].nunique() < 2:
        return
    model.fit(work[features], work[target])
    payload = {"model": model, "feature_columns": features, "target": target}
    with open(work_dir / "artifacts" / "models" / "life_cycle_classifier.pkl", "wb") as f:
        pickle.dump(payload, f)


def build_new_store_feature_frame(
    weekly_df: pd.DataFrame,
    meta_df: pd.DataFrame | None,
    cfg: Dict[str, object],
) -> pd.DataFrame:
    weekly = weekly_df.copy()
    if "public_id" not in weekly.columns:
        weekly["public_id"] = "new_store_1"

    if meta_df is None:
        meta_df = pd.DataFrame({"public_id": weekly["public_id"].astype(str).unique()})
    else:
        meta_df = meta_df.copy().rename(columns=META_RENAME_MAP)

    early_window = int(cfg["analysis"]["early_window"])
    cfg_local = {
        **cfg,
        "analysis": {**cfg["analysis"], "min_weeks": max(4, early_window // 2)},
    }
    panel = prepare_weekly_panel(weekly, meta_df, cfg_local)
    early_panel = slice_panel_by_week(panel, 0, early_window)
    features = summarize_store_panel(early_panel, min_weeks=max(4, early_window // 2))
    return features


def run_prediction_bundle(cfg: Dict[str, object], log: Callable[[str], None]) -> Dict[str, pd.DataFrame]:
    early_features, prediction_df, early_cluster_labels = build_prediction_dataset(cfg, log)
    base_features = unique_existing_features(prediction_df, default_feature_columns(prediction_df, cfg))
    early_screening = build_cluster_screening_bundle(prediction_df, cfg, "early_cluster", base_features)
    screened_features = unique_existing_features(prediction_df, early_screening["selected_features"])
    features = base_features
    random_state = int(cfg["analysis"]["random_state"])
    classification_specs = {
        "base_without_cluster": base_features,
        "base_with_early_cluster": unique_existing_features(prediction_df, base_features + ["early_cluster"]),
    }
    screened_classification_specs = {
        "early_cluster_screened": screened_features,
        "early_cluster_screened_plus_cluster": unique_existing_features(prediction_df, screened_features + ["early_cluster"]),
    }
    regression_ablation_specs = {
        "base_without_cluster": base_features,
        "base_with_early_cluster": unique_existing_features(prediction_df, base_features + ["early_cluster"]),
    }
    regression_screened_specs = {
        "early_cluster_screened": screened_features,
        "early_cluster_screened_plus_cluster": unique_existing_features(prediction_df, screened_features + ["early_cluster"]),
    }

    cls_metrics, cls_reports, confusions, _ = evaluate_classification_models(
        df=prediction_df,
        target="life_cycle_category",
        features=features,
        random_state=random_state,
    )
    cluster_ablation_metrics, cluster_ablation_reports = evaluate_classification_specs(
        df=prediction_df,
        target="life_cycle_category",
        feature_specs=classification_specs,
        random_state=random_state,
    )
    cluster_screened_metrics, cluster_screened_reports = evaluate_classification_specs(
        df=prediction_df,
        target="life_cycle_category",
        feature_specs=screened_classification_specs,
        random_state=random_state,
    )
    save_confusion_matrices(
        confusions,
        sorted(prediction_df["life_cycle_category"].dropna().unique().tolist()),
        "early_prediction",
    )

    reg_metrics, reg_importance = evaluate_regression_models(
        df=prediction_df,
        target="future_avg_sales",
        features=features,
        random_state=random_state,
    )
    regression_ablation_metrics = evaluate_regression_specs(
        df=prediction_df,
        target="future_avg_sales",
        feature_specs=regression_ablation_specs,
        random_state=random_state,
    )
    regression_screened_metrics = evaluate_regression_specs(
        df=prediction_df,
        target="future_avg_sales",
        feature_specs=regression_screened_specs,
        random_state=random_state,
    )
    save_feature_importance_plot(
        reg_importance[reg_importance["model"] == "RandomForestRegressor"],
        "future_sales_feature_importance",
    )

    persist_example_classifier(prediction_df, features, "life_cycle_category", cfg)
    scoring_schema = pd.DataFrame({"feature_name": features, "feature_role": ["model_input"] * len(features)})
    log(f"Prediction dataset rows: {len(prediction_df):,}")
    return {
        "early_features": early_features,
        "early_cluster_labels": early_cluster_labels,
        "early_cluster_feature_screening": early_screening["scores"],
        "early_cluster_selected_features": early_screening["selected_features_table"],
        "early_cluster_selected_numeric_summary": early_screening["numeric_summary"],
        "early_cluster_selected_categorical_summary": early_screening["categorical_summary"],
        "prediction_dataset": prediction_df,
        "classification_metrics": cls_metrics,
        "classification_reports": cls_reports,
        "classification_cluster_ablation_metrics": cluster_ablation_metrics,
        "classification_cluster_ablation_reports": cluster_ablation_reports,
        "classification_cluster_screened_metrics": cluster_screened_metrics,
        "classification_cluster_screened_reports": cluster_screened_reports,
        "regression_metrics": reg_metrics,
        "regression_feature_importance": reg_importance,
        "regression_cluster_ablation_metrics": regression_ablation_metrics,
        "regression_cluster_screened_metrics": regression_screened_metrics,
        "scoring_schema": scoring_schema,
    }
