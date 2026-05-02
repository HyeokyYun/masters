# Strict Out-of-Time Rolling Validation

## Purpose

This run adds the stricter validation requested after the 260430 meeting.
The model is trained on one calendar-aligned future relation and tested on the
next calendar-aligned future relation:

- Train: `2021-M-Kweeks feature -> 2022-M-Kweeks label`
- Test: `2022-M-Kweeks feature -> 2023-M-Kweeks label`

This differs from the earlier `260430` seasonal check, which used store-level
cross-validation inside each calendar-matched specification.

## Run Summary

- Evaluated start-month/window pairs: 32
- Start months covered: 8
- Window lengths covered: 6
- Model: balanced logistic regression
- Baseline: majority-class dummy classifier

## Mean Performance

| model | macro_f1 | weighted_f1 | auc_ovr | decline_recall |
|---|---:|---:|---:|---:|
| majority baseline | 0.221 | 0.384 | n/a | 0.000 |
| strict rolling logistic | 0.407 | 0.508 | 0.650 | 0.357 |

## Best Windows By Macro-F1

|   start_month |   window_weeks |   n_train |   n_test |   macro_f1 |   weighted_f1 |   auc_ovr |   recall_Growth |   recall_Stable |   recall_Decline |
|--------------:|---------------:|----------:|---------:|-----------:|--------------:|----------:|----------------:|----------------:|-----------------:|
|             5 |             12 |     33972 |    34248 |   0.47774  |      0.570896 |  0.702277 |        0.479696 |        0.688432 |         0.308255 |
|             6 |              4 |     34683 |    34820 |   0.4738   |      0.578975 |  0.697507 |        0.392814 |        0.657548 |         0.408484 |
|             5 |              8 |     34228 |    34553 |   0.459737 |      0.571705 |  0.682919 |        0.327095 |        0.68131  |         0.388166 |
|             5 |              4 |     34482 |    34972 |   0.45913  |      0.555875 |  0.677341 |        0.316558 |        0.654985 |         0.442025 |
|             1 |              4 |     31887 |    34458 |   0.458324 |      0.571325 |  0.672406 |        0.557345 |        0.540767 |         0.416235 |
|             4 |             16 |     33724 |    34160 |   0.457588 |      0.548165 |  0.686185 |        0.551508 |        0.613572 |         0.316361 |
|             5 |             16 |     33602 |    33874 |   0.454607 |      0.559511 |  0.699258 |        0.513943 |        0.703127 |         0.270795 |
|             7 |              8 |     33832 |    33973 |   0.452194 |      0.583762 |  0.680163 |        0.370163 |        0.710746 |         0.318084 |

## Best Windows By Decline Recall

|   start_month |   window_weeks |   n_train |   n_test |   macro_f1 |   weighted_f1 |   auc_ovr |   recall_Growth |   recall_Stable |   recall_Decline |
|--------------:|---------------:|----------:|---------:|-----------:|--------------:|----------:|----------------:|----------------:|-----------------:|
|             1 |             12 |     32159 |    34123 |   0.340638 |      0.496024 |  0.689264 |        0.482423 |        0.236873 |         0.776154 |
|             1 |              8 |     31923 |    34294 |   0.348863 |      0.502881 |  0.679613 |        0.579549 |        0.191604 |         0.682946 |
|             1 |             16 |     32205 |    34006 |   0.40885  |      0.528169 |  0.688464 |        0.472191 |        0.495217 |         0.630936 |
|             3 |              4 |     34105 |    34889 |   0.412603 |      0.55279  |  0.652666 |        0.233333 |        0.594523 |         0.557153 |
|             5 |              4 |     34482 |    34972 |   0.45913  |      0.555875 |  0.677341 |        0.316558 |        0.654985 |         0.442025 |
|             1 |             20 |     32724 |    34258 |   0.43169  |      0.546678 |  0.655509 |        0.604868 |        0.397273 |         0.437621 |
|             1 |              4 |     31887 |    34458 |   0.458324 |      0.571325 |  0.672406 |        0.557345 |        0.540767 |         0.416235 |
|             2 |              8 |     33332 |    34495 |   0.401358 |      0.511162 |  0.614598 |        0.314706 |        0.552018 |         0.410745 |

## By Window Length

|   window_weeks |   macro_f1_mean |   macro_f1_max |   auc_ovr_mean |   auc_ovr_max |   decline_recall_mean |   decline_recall_max |
|---------------:|----------------:|---------------:|---------------:|--------------:|----------------------:|---------------------:|
|              4 |           0.424 |          0.474 |          0.663 |         0.705 |                 0.365 |                0.557 |
|              8 |           0.41  |          0.46  |          0.657 |         0.69  |                 0.381 |                0.683 |
|             12 |           0.397 |          0.478 |          0.65  |         0.702 |                 0.367 |                0.776 |
|             16 |           0.404 |          0.458 |          0.652 |         0.699 |                 0.353 |                0.631 |
|             20 |           0.403 |          0.45  |          0.641 |         0.689 |                 0.329 |                0.438 |
|             30 |           0.366 |          0.406 |          0.591 |         0.612 |                 0.281 |                0.325 |

## By Start Month

|   start_month |   macro_f1 |   recall_Decline |
|--------------:|-----------:|-----------------:|
|             1 |      0.399 |            0.545 |
|             2 |      0.374 |            0.298 |
|             3 |      0.365 |            0.363 |
|             4 |      0.441 |            0.335 |
|             5 |      0.463 |            0.352 |
|             6 |      0.439 |            0.25  |
|             7 |      0.451 |            0.278 |
|             8 |      0.274 |            0.175 |

## Interpretation

The strict out-of-time result should be read as the most conservative
seasonality robustness check. It asks whether a relationship learned from
`2021 -> 2022` transfers to the next same-calendar roll, `2022 -> 2023`.

If performance is lower than the earlier within-specification seasonal CV,
that is expected: the test year is held out as a future calendar period rather
than mixed into cross-validation. The thesis claim should therefore avoid
saying that seasonal rolling improves performance. The stronger and safer claim
is:

> Once seasonality and future-period transfer are both imposed, predictive
> performance weakens, but the model still outperforms a majority baseline and
> retains non-zero decline detection. The original high hybrid scores should be
> treated as an upper-bound exploratory result, while strict rolling provides
> the conservative robustness evidence.

## Files

- `tables/strict_rolling_results.csv`
- `tables/strict_rolling_label_distribution.csv`
- `figures/strict_macro_f1_heatmap.png`
- `figures/strict_decline_recall_heatmap.png`
- `figures/strict_auc_heatmap.png`
- `figures/strict_by_window_line.png`
- `figures/strict_model_vs_dummy.png`
