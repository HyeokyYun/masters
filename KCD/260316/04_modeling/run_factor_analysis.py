from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "260316" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from research_pipeline.config import get_work_dir, load_config
from research_pipeline.io_utils import build_logger, ensure_layout, save_csv, save_text
from research_pipeline.modeling import run_factor_analysis_bundle


def main() -> None:
    work_dir = get_work_dir()
    cfg = load_config()
    ensure_layout(work_dir)
    log = build_logger(work_dir / "outputs" / "logs" / "run_factor_analysis.log")

    log("260316 Step 4: factor analysis and econometrics")
    bundle = run_factor_analysis_bundle(cfg, log)

    save_csv(bundle["life_cycle_summary"], work_dir / "outputs" / "tables" / "life_cycle_group_summary.csv")
    save_csv(bundle["cluster_summary"], work_dir / "outputs" / "tables" / "cluster_group_summary.csv")
    save_csv(bundle["cluster_feature_screening"], work_dir / "outputs" / "tables" / "cluster_feature_screening.csv")
    save_csv(bundle["cluster_selected_features"], work_dir / "outputs" / "tables" / "cluster_selected_features.csv")
    save_csv(
        bundle["cluster_selected_numeric_summary"],
        work_dir / "outputs" / "tables" / "cluster_selected_numeric_summary.csv",
    )
    save_csv(
        bundle["cluster_selected_categorical_summary"],
        work_dir / "outputs" / "tables" / "cluster_selected_categorical_summary.csv",
    )
    save_csv(bundle["classification_metrics"], work_dir / "outputs" / "tables" / "life_cycle_classification_metrics.csv")
    save_csv(bundle["classification_reports"], work_dir / "outputs" / "tables" / "life_cycle_classification_reports.csv")
    save_csv(bundle["cluster_ablation_metrics"], work_dir / "outputs" / "tables" / "life_cycle_cluster_ablation_metrics.csv")
    save_csv(bundle["cluster_ablation_reports"], work_dir / "outputs" / "tables" / "life_cycle_cluster_ablation_reports.csv")
    save_csv(
        bundle["cluster_screened_classification_metrics"],
        work_dir / "outputs" / "tables" / "life_cycle_cluster_screened_metrics.csv",
    )
    save_csv(
        bundle["cluster_screened_classification_reports"],
        work_dir / "outputs" / "tables" / "life_cycle_cluster_screened_reports.csv",
    )
    save_csv(bundle["feature_importance"], work_dir / "outputs" / "tables" / "life_cycle_feature_importance.csv")
    save_csv(bundle["regression_metrics"], work_dir / "outputs" / "tables" / "life_cycle_regression_metrics.csv")
    save_csv(bundle["regression_coefficients"], work_dir / "outputs" / "tables" / "life_cycle_regression_coefficients.csv")
    save_csv(
        bundle["cluster_screened_regression_metrics"],
        work_dir / "outputs" / "tables" / "growth_rate_cluster_screened_metrics.csv",
    )
    save_csv(bundle["mnlogit_metrics"], work_dir / "outputs" / "tables" / "multinomial_logit_metrics.csv")
    save_csv(bundle["mnlogit_coefficients"], work_dir / "outputs" / "tables" / "multinomial_logit_coefficients.csv")
    save_text(bundle["mnlogit_summary"], work_dir / "outputs" / "tables" / "multinomial_logit_summary.txt")
    log("Step 4 completed.")


if __name__ == "__main__":
    main()
