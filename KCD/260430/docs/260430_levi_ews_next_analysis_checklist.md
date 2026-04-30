# Next Analysis Checklist for LEVI/EWS Academic Submission

## Already Done

| component             | weak_version                               | academic_version                                                                                                                              | minimum_evidence_needed                                                            | current_status                                                                |
|:----------------------|:-------------------------------------------|:----------------------------------------------------------------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------|:------------------------------------------------------------------------------|
| LEVI                  | We made a local vitality index.            | LEVI operationalizes local business vitality and is validated against independent population, closure, and commercial-sales indicators.       | Formula robustness, convergent validity, criterion validity, and scope cautions.   | Mostly available from existing external-validation outputs.                   |
| EWS                   | We predict declining stores.               | A calibrated, cost-sensitive early-warning artifact prioritizes intervention targets under explicit false-positive/false-negative trade-offs. | AP, calibration, operating thresholds, cost utility, subgroup stability, examples. | Mostly available from existing EWS outputs.                                   |
| Hybrid representation | Cluster and change point improve accuracy. | Trajectory-state and change-point representations encode lifecycle dynamics that improve decision-support predictions.                        | Ablation against base features plus robustness to leakage and seasonality.         | Available for main top_tier run; seasonal robustness now available in 260430. |
| Golden Cross          | New customers rise before sales rebound.   | New-customer inflow is a plausible leading mechanism for rebound, triangulated by Granger, matched DiD, and fixed-effects evidence.           | Triangulated tests with careful non-causal or cautiously causal wording.           | Available as support, not necessary as the central paper contribution.        |

## Still Worth Adding Before Submission

1. **LEVI leave-one-district-out sensitivity**
   - Completed in `levi_leave_one_district_out_sensitivity.csv`.
   - Summary is embedded in `260430_levi_ews_academic_strategy.md`.

2. **LEVI alternative formula table**
   - Already feasible from the five LEVI formulas.
   - Put V1-V5 external correlations in one table.

3. **EWS calibration bins**
   - Completed in `ews_calibration_deciles.csv`.

4. **EWS cost sensitivity**
   - Completed in `ews_cost_sensitivity_scenarios.csv`.

5. **EWS subgroup stability**
   - For major food-service categories, report AP or recall if available.
   - Current segment table shows risk-score distribution only.

6. **Seasonality connection**
   - Use `260430` rolling-window result as robustness, not as the main model.
   - State clearly that seasonal Macro-F1 is lower than full hybrid, but signal
     survives calendar matching.

## Venue Positioning

| venue                    | fit                       | best_framing                                                                                   | lead_component       | what_to_emphasize                                                                         | risk                                                                          |
|:-------------------------|:--------------------------|:-----------------------------------------------------------------------------------------------|:---------------------|:------------------------------------------------------------------------------------------|:------------------------------------------------------------------------------|
| HICSS                    | High                      | Decision-support artifact for small-business vitality monitoring.                              | EWS + LEVI           | Artifact design, external validation, policy-use threshold, explainable risk scores.      | Needs a clean paper narrative; avoid trying to include every thesis analysis. |
| DSS                      | Medium-high after polish  | Calibrated and cost-sensitive early-warning system from transaction traces.                    | EWS + Hybrid         | Decision analytics, calibration, operating points, cost utility, representation ablation. | Must strengthen artifact evaluation and reviewer-facing methodology.          |
| Information & Management | Medium                    | Data-driven small-business lifecycle intelligence.                                             | Hybrid + EWS         | Managerial relevance, digital trace data, actionable analytics.                           | Needs tighter theory of digital trace-based decision support.                 |
| Small Business Economics | Medium, different framing | Micro transaction traces as indicators of urban small-business vitality.                       | LEVI + external data | Small-business dynamics, local economic vitality, closure/growth distribution.            | Needs stronger economic theory and cautious claims; EWS should be secondary.  |
| ICIS                     | Possible but risky        | IS artifact translating private transaction traces into public/economic decision intelligence. | EWS + theory         | Digital trace, decision support, public-value analytics, DSR rigor.                       | Theory framing must be much stronger than a performance report.               |
