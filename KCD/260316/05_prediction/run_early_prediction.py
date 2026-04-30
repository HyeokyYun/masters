from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "260316" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from research_pipeline.config import get_work_dir, load_config
from research_pipeline.io_utils import build_logger, ensure_layout, save_csv
from research_pipeline.prediction import run_prediction_bundle


def main() -> None:
    work_dir = get_work_dir()
    cfg = load_config()
    ensure_layout(work_dir)
    log = build_logger(work_dir / "outputs" / "logs" / "run_early_prediction.log")

    log("260316 Step 5: early-window prediction")
    bundle = run_prediction_bundle(cfg, log)

    save_csv(bundle["early_features"], work_dir / "outputs" / "tables" / "early_window_features.csv")
    save_csv(bundle["early_cluster_labels"], work_dir / "outputs" / "tables" / "early_cluster_labels.csv")
    save_csv(
        bundle["early_cluster_feature_screening"],
        work_dir / "outputs" / "tables" / "early_cluster_feature_screening.csv",
    )
    save_csv(
        bundle["early_cluster_selected_features"],
        work_dir / "outputs" / "tables" / "early_cluster_selected_features.csv",
    )
    save_csv(
        bundle["early_cluster_selected_numeric_summary"],
        work_dir / "outputs" / "tables" / "early_cluster_selected_numeric_summary.csv",
    )
    save_csv(
        bundle["early_cluster_selected_categorical_summary"],
        work_dir / "outputs" / "tables" / "early_cluster_selected_categorical_summary.csv",
    )
    save_csv(bundle["prediction_dataset"], work_dir / "outputs" / "tables" / "early_prediction_dataset.csv")
    save_csv(bundle["classification_metrics"], work_dir / "outputs" / "tables" / "early_prediction_metrics.csv")
    save_csv(bundle["classification_reports"], work_dir / "outputs" / "tables" / "early_prediction_reports.csv")
    save_csv(
        bundle["classification_cluster_ablation_metrics"],
        work_dir / "outputs" / "tables" / "early_prediction_cluster_ablation_metrics.csv",
    )
    save_csv(
        bundle["classification_cluster_ablation_reports"],
        work_dir / "outputs" / "tables" / "early_prediction_cluster_ablation_reports.csv",
    )
    save_csv(
        bundle["classification_cluster_screened_metrics"],
        work_dir / "outputs" / "tables" / "early_prediction_cluster_screened_metrics.csv",
    )
    save_csv(
        bundle["classification_cluster_screened_reports"],
        work_dir / "outputs" / "tables" / "early_prediction_cluster_screened_reports.csv",
    )
    save_csv(bundle["regression_metrics"], work_dir / "outputs" / "tables" / "future_sales_regression_metrics.csv")
    save_csv(bundle["regression_feature_importance"], work_dir / "outputs" / "tables" / "future_sales_feature_importance.csv")
    save_csv(
        bundle["regression_cluster_ablation_metrics"],
        work_dir / "outputs" / "tables" / "future_sales_cluster_ablation_metrics.csv",
    )
    save_csv(
        bundle["regression_cluster_screened_metrics"],
        work_dir / "outputs" / "tables" / "future_sales_cluster_screened_metrics.csv",
    )
    save_csv(bundle["scoring_schema"], work_dir / "outputs" / "tables" / "new_store_scoring_schema.csv")
    log("Step 5 completed.")


if __name__ == "__main__":
    main()
