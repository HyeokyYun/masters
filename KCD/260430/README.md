# 260430 meeting follow-up

This folder contains the follow-up package for the 2026-04-30 personal meeting.

Primary goal:
- Re-run the growth/stable/decline prediction framing with calendar-matched
  rolling windows so that early and target windows compare the same season.

Main command:

```bash
python 260430/src/run_seasonal_window_analysis.py
python 260430/src/build_levi_ews_academic_package.py
```

Main outputs:
- `outputs/tables/seasonal_window_inventory.csv`
- `outputs/tables/seasonal_label_distribution.csv`
- `outputs/tables/seasonal_prediction_cv_results.csv`
- `outputs/tables/seasonal_prediction_summary.csv`
- `outputs/figures/seasonal_macro_f1_heatmap.png`
- `outputs/figures/seasonal_decline_recall_heatmap.png`
- `outputs/figures/baseline_vs_seasonal_comparison.png`
- `docs/260430_meeting_action_items.md`
- `docs/260430_seasonality_analysis_report.md`
- `docs/260430_thesis_story_update.md`
- `docs/260430_levi_ews_academic_strategy.md`
- `docs/260430_levi_ews_paper_outline.md`
- `docs/260430_levi_ews_next_analysis_checklist.md`

LEVI/EWS academic package outputs:
- `outputs/tables/levi_academic_validity_summary.csv`
- `outputs/tables/levi_formula_robustness.csv`
- `outputs/tables/levi_leave_one_district_out_sensitivity.csv`
- `outputs/tables/ews_academic_evaluation_summary.csv`
- `outputs/tables/ews_calibration_deciles.csv`
- `outputs/tables/ews_cost_sensitivity_scenarios.csv`
- `outputs/tables/levi_ews_venue_positioning.csv`
- `outputs/figures/levi_academic_validity_evidence.png`
- `outputs/figures/ews_academic_evaluation_evidence.png`
- `outputs/figures/ews_calibration_deciles.png`
- `outputs/figures/ews_cost_sensitivity_scenarios.png`
