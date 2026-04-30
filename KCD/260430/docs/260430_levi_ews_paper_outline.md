# LEVI/EWS Paper Outline

## Working Title

Transaction-Based Early Warning and Local Vitality Monitoring for Small
Businesses

## Research Questions

RQ1. Can early transaction traces identify stores at risk of later decline?

RQ2. Can a calibrated EWS translate these predictions into actionable
intervention priorities?

RQ3. Do aggregated lifecycle outcomes align with independent indicators of
local economic vitality?

## Contribution Structure

1. **Measurement contribution**: LEVI aggregates store-level lifecycle outcomes
   into a district-level local business vitality measure and validates it
   against external public data.
2. **Artifact contribution**: EWS converts predictive probabilities into
   calibrated, cost-sensitive risk scores and operating thresholds.
3. **Representation contribution**: hybrid trajectory states and change-point
   features improve lifecycle prediction over base features.
4. **Robustness contribution**: calendar-matched rolling windows address the
   seasonality concern raised in the 260430 meeting.

## Recommended Paper Boundary

Main paper:

- Data foundation
- Hybrid prediction
- EWS evaluation
- LEVI external validation
- Seasonality robustness

Appendix or future work:

- Full Cox/survival package
- Deep-learning baselines
- Extended causal Golden Cross triangulation
- Field deployment mock-up/API

## One-Paragraph Abstract Draft

Small businesses generate high-frequency digital traces, yet public monitoring
systems often observe local distress only after closures occur. We develop a
transaction-based decision-support artifact that predicts store-level
Growth/Stable/Decline outcomes and translates decline probabilities into a
calibrated early-warning score. The proposed hybrid representation combines
early transaction features with trajectory-state and change-point information,
improving predictive performance over base feature models. We further aggregate
store-level lifecycle outcomes into a Local Economic Vitality Index (LEVI) and
validate it against independent Seoul public indicators, including
living-population change and administrative closure rates. The results show how
private transaction traces can support both store-level risk prioritization and
district-level vitality monitoring, while calendar-matched rolling-window checks
address seasonality concerns in lifecycle prediction.
