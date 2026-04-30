from __future__ import annotations

from pathlib import Path

import pandas as pd

from src import config as cfg


def _load_csv(path: Path) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def generate_reports() -> None:
    diagnostics = _load_csv(cfg.TABLE_DIR / "data_availability_diagnostics.csv")
    volatility = _load_csv(cfg.TABLE_DIR / "volatility_metric_screening.csv")
    age_summary = _load_csv(cfg.TABLE_DIR / "business_age_bucket_summary.csv")

    if not volatility.empty:
        preferred_metric = volatility.iloc[0]["metric"]
    else:
        preferred_metric = "vol_resid_stl13"

    diagnostic_map = {}
    if not diagnostics.empty:
        diagnostic_map = {row["item"]: row["value"] for _, row in diagnostics.iterrows()}

    early_total = None
    if not age_summary.empty:
        early_total = int(age_summary.loc[age_summary["age_bucket"].isin(["0_6m", "6_12m"]), "store_count"].sum())

    action_plan = f"""# 260321 Meeting Action Plan

## What was requested in the meeting

1. Redefine sales volatility so that it measures deviation around a growth trend rather than deviation around a flat mean.
2. Test competition or crowding interactions, especially for fast-food stores.
3. Re-check business age and run a separate analysis for young stores.
4. Add owner demographics when available.
5. Benchmark forecasting performance against literature.
6. Treat franchise status cautiously because missingness is high.

## What this folder now does

1. Builds an enriched base dataset by merging the current labeled lifecycle output with `meta.csv` and weekly observation bounds.
2. Computes multiple candidate volatility metrics:
   - `vol_cv_mean`
   - `vol_resid_linear`
   - `vol_resid_quadratic`
   - `vol_resid_rolling13`
   - `vol_resid_stl13`
3. Creates dong-level competition metrics and interaction-ready variables.
4. Summarizes business-age buckets and runs an early-store subsample model.
5. Merges owner age, checks whether owner gender exists, and records missingness.
6. Writes a forecasting benchmark template for the external literature review.

## Immediate interpretation

- Recommended volatility candidate for the next meeting: `{preferred_metric}`
- Sample size in the new base table: `{int(diagnostic_map.get("sample_rows", 0)):,}`
- Missing owner-age rate: `{diagnostic_map.get("missing_owner_age_rate", float("nan")):.3f}`
- Missing owner-gender rate: `{diagnostic_map.get("missing_owner_gender_rate", float("nan")):.3f}`
- Young-store observations in 0-12 months buckets: `{early_total if early_total is not None else "not available"}`

## Recommended next actions

1. Review `volatility_metric_screening.csv` and choose one trend-relative volatility definition for the main table.
2. Check `mnlogit_outcome3_interaction_*` outputs to see whether fast-food crowding changes the growth/stable/decline odds.
3. Use `business_age_bucket_summary.csv` and the young-store model to define the final cutoff for "short business age".
4. If owner gender exists in another source, merge it into `meeting_base_dataset.csv` and rerun this folder.
5. Fill the external forecasting benchmark template with literature values before claiming whether 0.37 to 0.43 is high.
6. Keep franchise status out of the main model unless a defensible missing-data rule is agreed upon.
"""

    with open(cfg.DOC_DIR / "meeting_action_plan.md", "w", encoding="utf-8") as handle:
        handle.write(action_plan)

    benchmark_template = pd.DataFrame(
        [
            {
                "paper_or_source": "",
                "domain": "sales_forecasting",
                "sample_context": "",
                "forecast_horizon": "",
                "task_type": "future_forecasting",
                "model_family": "",
                "metric_name": "R2_or_other",
                "metric_value": "",
                "notes": "",
            },
            {
                "paper_or_source": "",
                "domain": "demand_forecasting",
                "sample_context": "",
                "forecast_horizon": "",
                "task_type": "future_forecasting",
                "model_family": "",
                "metric_name": "R2_or_other",
                "metric_value": "",
                "notes": "",
            },
            {
                "paper_or_source": "",
                "domain": "small_business_forecasting",
                "sample_context": "",
                "forecast_horizon": "",
                "task_type": "future_forecasting",
                "model_family": "",
                "metric_name": "R2_or_other",
                "metric_value": "",
                "notes": "Fill this row first if a directly comparable study is found.",
            },
        ]
    )
    benchmark_template.to_csv(cfg.TABLE_DIR / "forecasting_benchmark_template.csv", index=False, encoding="utf-8-sig")

    task_inventory = pd.DataFrame(
        [
            {"priority": 1, "task": "Finalize volatility definition", "status": "implemented_for_screening"},
            {"priority": 2, "task": "Check fast-food competition interaction", "status": "implemented_for_screening"},
            {"priority": 3, "task": "Define short business-age cutoff", "status": "implemented_for_screening"},
            {"priority": 4, "task": "Add owner age and check owner gender", "status": "partially_implemented"},
            {"priority": 5, "task": "Literature benchmark for forecasting R2", "status": "template_only"},
            {"priority": 6, "task": "Franchise variable decision", "status": "pending_data_rule"},
        ]
    )
    task_inventory.to_csv(cfg.TABLE_DIR / "next_steps_inventory.csv", index=False, encoding="utf-8-sig")
