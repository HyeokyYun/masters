# 260430 Seasonality Analysis Report

## Purpose

This run addresses the meeting concern that the original late-window label may
mix lifecycle signal with calendar seasonality. The revised analysis compares
feature and target windows that start in the same calendar month across years.

## Run Summary

- Valid window specifications: 136
- Evaluated CV specifications: 136
- Total CV rows: 680
- Label distribution rows: 408

## Existing Baseline Read From top_tier

- top_tier_xgb_macro_f1: 0.548
- top_tier_hybrid_macro_f1: 0.639
- top_tier_hybrid_auc: 0.824

## Best Seasonal Windows By Macro-F1

| spec_id             |     n |   macro_f1 |   weighted_f1 |   auc_ovr |   recall_Growth |   recall_Stable |   recall_Decline |
|:--------------------|------:|-----------:|--------------:|----------:|----------------:|----------------:|-----------------:|
| y2021_m09_w20_lag1y | 34221 |   0.508995 |      0.555077 |  0.722414 |        0.614355 |        0.389597 |         0.663335 |
| y2021_m07_w30_lag1y | 33820 |   0.508846 |      0.547888 |  0.713617 |        0.5672   |        0.464458 |         0.608491 |
| y2021_m12_w30_lag1y | 34023 |   0.508782 |      0.542162 |  0.717313 |        0.61305  |        0.445145 |         0.599049 |
| y2021_m06_w30_lag1y | 33898 |   0.508634 |      0.558722 |  0.707849 |        0.470892 |        0.567787 |         0.552395 |
| y2022_m05_w12_lag1y | 34248 |   0.508289 |      0.582512 |  0.716133 |        0.460531 |        0.613302 |         0.51512  |
| y2021_m09_w16_lag1y | 34210 |   0.502609 |      0.535402 |  0.695353 |        0.514078 |        0.533454 |         0.52124  |
| y2022_m04_w20_lag1y | 34132 |   0.499982 |      0.589557 |  0.711204 |        0.445832 |        0.633299 |         0.501743 |
| y2021_m11_w30_lag1y | 34151 |   0.49946  |      0.531617 |  0.701176 |        0.547278 |        0.481669 |         0.600703 |

## Best Seasonal Windows By Decline Recall

| spec_id             |     n |   macro_f1 |   weighted_f1 |   auc_ovr |   recall_Growth |   recall_Stable |   recall_Decline |
|:--------------------|------:|-----------:|--------------:|----------:|----------------:|----------------:|-----------------:|
| y2021_m09_w20_lag1y | 34221 |   0.508995 |      0.555077 |  0.722414 |        0.614355 |        0.389597 |         0.663335 |
| y2021_m10_w16_lag1y | 34221 |   0.474687 |      0.577534 |  0.707091 |        0.556184 |        0.38888  |         0.658482 |
| y2021_m12_w20_lag1y | 34394 |   0.497927 |      0.55249  |  0.711248 |        0.618759 |        0.421377 |         0.631615 |
| y2021_m01_w30_lag1y | 32893 |   0.464427 |      0.622743 |  0.731716 |        0.612061 |        0.497026 |         0.618841 |
| y2021_m03_w12_lag1y | 33318 |   0.446628 |      0.533601 |  0.673209 |        0.478659 |        0.514014 |         0.612894 |
| y2021_m03_w04_lag1y | 34105 |   0.422102 |      0.530692 |  0.668116 |        0.213654 |        0.636711 |         0.611033 |
| y2021_m03_w08_lag1y | 33844 |   0.442198 |      0.526382 |  0.668361 |        0.469769 |        0.50679  |         0.610783 |
| y2022_m01_w16_lag1y | 34006 |   0.474835 |      0.631241 |  0.721792 |        0.661475 |        0.449602 |         0.60918  |

## Interpretation

Use these outputs as a robustness check, not as a replacement for the full
`top_tier` pipeline. If the seasonal-window results preserve meaningful
classification performance, the thesis can argue that early trajectory signal is
not only a byproduct of comparing January starts with summer target windows.

The strongest defense wording is:

> After matching feature and target windows by calendar month, the early
> transaction signal remains informative for later Growth/Stable/Decline
> classification, though performance varies by start month and forecast horizon.

## Files

- `outputs/tables/seasonal_window_inventory.csv`
- `outputs/tables/seasonal_label_distribution.csv`
- `outputs/tables/seasonal_prediction_cv_results.csv`
- `outputs/tables/seasonal_prediction_summary.csv`
- `outputs/figures/seasonal_macro_f1_heatmap.png`
- `outputs/figures/seasonal_decline_recall_heatmap.png`
- `outputs/figures/baseline_vs_seasonal_comparison.png`
