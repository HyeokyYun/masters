# LEVI and EWS Academic Strategy

## Bottom Line

LEVI and EWS can be academically meaningful, but only if they are framed as
validated measurement and decision-support artifacts rather than as convenient
labels added after the main prediction work.

The recommended split is:

- **Thesis main line**: store-level lifecycle prediction with the new
  seasonality-corrected rolling-window check.
- **Paper extension**: LEVI + EWS as an evaluated decision-support package for
  local small-business vitality.

## LEVI: Make It a Construct-Validation Contribution

Weak claim:

> We created LEVI.

Academic claim:

> LEVI operationalizes local business vitality from micro transaction outcomes
> and is externally validated against independent urban-economic indicators.

Evidence currently available:

| test_family                   | evidence                                                                 | academic_use                                                                      | risk                                                                                  |
|:------------------------------|:-------------------------------------------------------------------------|:----------------------------------------------------------------------------------|:--------------------------------------------------------------------------------------|
| convergent_validity           | LEVI vs living-population change Pearson=0.853, Spearman=0.802, n=25     | Use as construct-validation evidence for local business vitality.                 | n=25 districts; treat as external validity evidence, not causal identification.       |
| discriminant_check            | LEVI vs living-population level Pearson=-0.053, Spearman=0.045, n=25     | Use to argue the construct is about change/vitality, not area scale.              | This is a negative-control style check; it does not prove full discriminant validity. |
| criterion_validity            | LEVI vs permit closure rate mean Pearson=-0.430, Spearman=-0.241, n=25   | Use as criterion validity against independent administrative data.                | Closure-register timing and KCD outcome definitions are not identical.                |
| criterion_validity_robustness | LEVI vs permit closure rate median Pearson=-0.533, Spearman=-0.242, n=25 | Use as robustness for criterion validity.                                         | Spearman magnitude is weaker, so frame as directional support.                        |
| temporal_external_validity    | Pearson=0.766, Spearman=0.727, n=11                                      | Shows KCD transaction series aligns with independent Seoul commercial indicators. | Temporal validation supports data credibility but is not a causal test.               |
| temporal_external_validity    | Pearson=0.498, Spearman=0.773, n=11                                      | Shows KCD transaction series aligns with independent Seoul commercial indicators. | Temporal validation supports data credibility but is not a causal test.               |
| temporal_external_validity    | Pearson=0.839, Spearman=0.891, n=10                                      | Shows KCD transaction series aligns with independent Seoul commercial indicators. | Temporal validation supports data credibility but is not a causal test.               |
| temporal_external_validity    | Pearson=0.721, Spearman=0.879, n=10                                      | Shows KCD transaction series aligns with independent Seoul commercial indicators. | Temporal validation supports data credibility but is not a causal test.               |

Formula robustness:

- Minimum pairwise Pearson correlation across the five LEVI formulas:
  **0.979**
- This supports the claim that the result is not dependent on one arbitrary
  index formula.

Leave-one-district-out sensitivity:

| external_metric            |   pearson_min |   pearson_median |   pearson_max |   spearman_min |   spearman_median |   spearman_max |
|:---------------------------|--------------:|-----------------:|--------------:|---------------:|------------------:|---------------:|
| living_population_change   |      0.809545 |         0.852908 |      0.8669   |       0.777391 |          0.801739 |       0.833043 |
| permit_closure_rate_mean   |     -0.52586  |        -0.43321  |     -0.148909 |      -0.362609 |         -0.241739 |      -0.141739 |
| permit_closure_rate_median |     -0.615773 |        -0.535577 |     -0.32822  |      -0.351304 |         -0.238261 |      -0.143478 |

Recommended wording:

> LEVI is not presented as a causal index. It is a district-level measurement
> artifact that aggregates store-level Growth and Decline outcomes and is
> validated against independent indicators of population change, closure
> pressure, and commercial activity.

## EWS: Make It a Decision-Support Artifact

Weak claim:

> The model predicts decline.

Academic claim:

> The EWS converts lifecycle prediction into calibrated, cost-sensitive
> intervention priorities under explicit trade-offs between false alarms and
> missed decline cases.

Evidence currently available:

| evaluation_dimension    | claim                                                                                                  | evidence                                                                                | academic_use                                                                     | risk                                                                                              |
|:------------------------|:-------------------------------------------------------------------------------------------------------|:----------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------|
| ranking_quality_decline | EWS ranks future decline risk far above the base prevalence.                                           | Decline AP=0.688; baseline decline rate=0.223; lift=3.09x                               | Use as the primary decision-support ranking metric.                              | AP is a predictive metric; connect it to intervention decisions through threshold utility.        |
| ranking_quality_growth  | The same artifact can also rank growth opportunities.                                                  | Growth AP=0.819; baseline growth rate=0.410; lift=2.00x                                 | Use as secondary evidence for opportunity targeting.                             | Do not over-center growth targeting if the paper is about decline warning.                        |
| calibration             | EWS probabilities are usable as risk scores rather than only class labels.                             | Brier decline=0.111; Brier growth=0.144                                                 | Use to justify risk-score output for decision support.                           | Add reliability-bin table if a journal reviewer asks for calibration detail.                      |
| operating_point         | The artifact supports explicit policy trade-offs between missing decline and over-flagging.            | Optimal threshold=0.10; net utility=43626; precision=0.382; recall=0.939; flagged=54.7% | Use as DSR-style artifact evaluation beyond accuracy.                            | Cost weights are assumed; report sensitivity over thresholds and costs.                           |
| representation_value    | Hybrid trajectory representation improves the EWS input model.                                         | Base Macro-F1=0.548, AUC=0.736; Proposed Macro-F1=0.639, AUC=0.824                      | Use to show the artifact is not only a dashboard wrapper around a generic model. | Keep leakage and seasonal-window robustness clearly separated.                                    |
| seasonality_robustness  | The core early signal survives calendar-matched rolling-window checks, though weaker than full hybrid. | Best seasonal Macro-F1=0.509; Decline recall=0.663; spec=y2021_m09_w20_lag1y            | Use as a methodological response to the 260430 meeting concern.                  | Seasonal check uses a simpler balanced logistic model; present it as robustness, not replacement. |

Selected operating points:

|   threshold |   decline_precision |   decline_recall |   decline_f1 |   flagged_pct |   net_utility |
|------------:|--------------------:|-----------------:|-------------:|--------------:|--------------:|
|        0.05 |            0.317546 |        0.9771    |    0.479319  |     0.685453  |         37486 |
|        0.1  |            0.382358 |        0.939452  |    0.543508  |     0.54733   |         43626 |
|        0.2  |            0.477764 |        0.839425  |    0.608944  |     0.391393  |         39254 |
|        0.3  |            0.565139 |        0.720802  |    0.633549  |     0.284123  |         26458 |
|        0.5  |            0.717391 |        0.477604  |    0.57344   |     0.148305  |         -8020 |
|        0.7  |            0.844383 |        0.251992  |    0.388148  |     0.0664803 |        -44334 |
|        0.9  |            0.961183 |        0.0476321 |    0.0907663 |     0.0110392 |        -79058 |

Calibration by risk decile:

|   risk_decile |    n |   mean_predicted_decline |   observed_decline_rate |   decline_cases |   calibration_gap |   decline_capture_share |
|--------------:|-----:|-------------------------:|------------------------:|----------------:|------------------:|------------------------:|
|             1 | 5150 |                0.0116068 |              0.00621359 |              32 |      -0.0053932   |              0.00293121 |
|             2 | 4953 |                0.0232067 |              0.013931   |              69 |      -0.00927579  |              0.00632042 |
|             3 | 4814 |                0.0377208 |              0.0286664  |             138 |      -0.00905442  |              0.0126408  |
|             4 | 4746 |                0.0613491 |              0.0488833  |             232 |      -0.0124659   |              0.0212513  |
|             5 | 4908 |                0.10028   |              0.0914833  |             449 |      -0.00879645  |              0.0411285  |
|             6 | 4863 |                0.158148  |              0.156488   |             761 |      -0.00165988  |              0.0697078  |
|             7 | 4917 |                0.236422  |              0.236526   |            1163 |       0.000104129 |              0.106531   |
|             8 | 4871 |                0.343053  |              0.339766   |            1655 |      -0.00328742  |              0.151598   |
|             9 | 4886 |                0.501655  |              0.521899   |            2550 |       0.0202442   |              0.233581   |
|            10 | 4899 |                0.761224  |              0.789549   |            3868 |       0.0283252   |              0.35431    |

Best threshold by cost scenario:

| scenario              |   threshold |   scenario_net_utility |   decline_precision |   decline_recall |   flagged_pct | interpretation                                                     |
|:----------------------|------------:|-----------------------:|--------------------:|-----------------:|--------------:|:-------------------------------------------------------------------|
| conservative_support  |        0.2  |                  10909 |            0.477764 |         0.839425 |      0.391393 | Support resources are expensive; false positives matter more.      |
| balanced_prevention   |        0.1  |                  64138 |            0.382358 |         0.939452 |      0.54733  | Baseline policy scenario used for balanced preventive support.     |
| aggressive_prevention |        0.05 |                 102579 |            0.317546 |         0.9771   |      0.685453 | Missing true decline is costly; broad early support is acceptable. |

High-risk segment profile:

| classification__kcd_v3__depth_2_name   |   count |    mean |   median |     std |
|:---------------------------------------|--------:|--------:|---------:|--------:|
| 패스트푸드                             |    4044 | 35.1923 |     29.3 | 28.3521 |
| 분식                                   |    2398 | 30.6055 |     21.8 | 26.7248 |
| 분류정보없음                           |    1591 | 29.0825 |     19.8 | 26.3403 |
| 카페                                   |    7603 | 25.2594 |     19.7 | 21.5126 |
| 베이커리/디저트                        |    2391 | 22.4488 |     12.7 | 22.8696 |
| 양식                                   |    2310 | 21.5375 |     11.4 | 23.2208 |
| 중식                                   |    1973 | 21.3497 |     13.4 | 22.4466 |
| 일식                                   |    3249 | 21.1281 |     13.1 | 21.9787 |

## How To Write This Academically

Use a Design Science / decision analytics structure:

1. Problem: small-business distress is hard to observe early with conventional
   public statistics.
2. Artifact: transaction-based EWS plus LEVI local-vitality monitor.
3. Evaluation: predictive ranking, calibration, threshold utility, subgroup
   profile, external validity, and seasonality robustness.
4. Boundary: this is not a causal policy-impact evaluation unless an actual
   intervention is observed.

## What Not To Claim

- Do not say LEVI proves population change causes store growth.
- Do not say EWS has been field deployed.
- Do not treat cost-sensitive utility as a real welfare estimate; it is a
  decision-scenario evaluation.
- Do not merge every analysis into the MSc thesis main line.
