# Thesis Figure Pack

이 폴더는 석사학위논문 본문과 appendix에 넣기 위해 새로 정리한 figure pack입니다. 모든 핵심 그림은 PNG와 PDF 두 형식으로 저장했습니다.

## Main Figures

### Figure 1. Two empirical lenses for small-business life cycles

- File:
  - `main_figures/figure1_two_lenses_lifecycle.png`
  - `main_figures/figure1_two_lenses_lifecycle.pdf`
- Role:
  - 논문의 대표 그림으로 사용합니다.
  - Panel A는 개업 직후 trajectory heterogeneity를 보여줍니다.
  - Panel B는 전체 생존 업장의 observed-window Growth/Stable/Decline 구조를 보여줍니다.
- Caption draft:
  - Figure 1 presents two complementary empirical lenses for small-business life-cycle analysis. Panel A shows heterogeneous post-entry sales trajectories among recently opened stores, while Panel B summarizes Growth, Stable, and Decline states across business-age buckets in the full surviving-store sample.

### Figure 2. Age-specific drivers of Growth and Decline

- File:
  - `main_figures/figure2_age_bucket_drivers.png`
  - `main_figures/figure2_age_bucket_drivers.pdf`
- Role:
  - Main Result 2의 핵심 그림입니다.
  - 업력 bucket별 driver가 다르다는 주장을 보여줍니다.
  - Panel A는 feature importance score를 log scale로 보여줍니다.
  - Panel B는 `Sales trend`, `Max drawdown`, `New-customer ratio`의 Growth/Decline coefficient 변화를 보여줍니다.
- Caption draft:
  - Figure 2 shows that the correlates of life-cycle states vary by business age. Sales trend is the dominant driver across age buckets, while max drawdown and new-customer ratio become especially informative after the first year of operation.

### Figure 3. Early prediction improves with temporal dynamics and context

- File:
  - `main_figures/figure3_prediction_windows_and_ablation.png`
  - `main_figures/figure3_prediction_windows_and_ablation.pdf`
- Role:
  - Main Result 3의 핵심 그림입니다.
  - Panel A는 early observation window가 길어질수록 예측 성능이 개선됨을 보여줍니다.
  - Panel B는 level-only 대비 trend/volatility, customer behavior, local context의 feature block gain을 보여줍니다.
- Caption draft:
  - Figure 3 evaluates early prediction of life-cycle states. Panel A shows that 3-class Growth/Stable/Decline prediction is more stable than 12-class trajectory prediction and improves with longer early observation windows. Panel B shows that trend and volatility features provide the largest gain over level-only features, while customer behavior and local context add further improvements.

## Supporting Figures

### Figure S1. Supporting evidence on customer mix and volatility

- File:
  - `supporting_figures/figureS1_new_customer_and_volatility.png`
  - `supporting_figures/figureS1_new_customer_and_volatility.pdf`
- Role:
  - Appendix 또는 robustness/discussion에 넣기 좋습니다.
  - 신규 고객 비율과 volatility 정의 재검토를 한 그림에 묶었습니다.
- Caption draft:
  - Figure S1 reports supporting evidence on customer composition and volatility measurement. Panel A compares Growth and Decline shares across new-customer-ratio quintiles. Panel B shows that volatility interpretation depends on whether the measure is based on conventional CV or trend-adjusted residual volatility.

## Source Tables

- `source_tables/fullsample_age_bucket_feature_top5.csv`
- `source_tables/fullsample_age_bucket_feature_importance.csv`
- `source_tables/fullsample_age_bucket_outcome_summary.csv`
- `source_tables/forecast_feature_ablation_classification.csv`
- `source_tables/forecast_feature_ablation_classification_gain.csv`
- `source_tables/forecast_weeks_comparison.csv`
- `source_tables/forecast_weeks_3class.csv`
- `source_tables/new_customer_quantile_summary.csv`
- `source_tables/volatility_metric_screening.csv`

## Source Figures

- `source_figures/fig01_trajectories.png`
- `source_figures/fullsample_age_overview.png`

## Reproduction

To regenerate all figures:

```bash
MPLCONFIGDIR=/tmp/mplconfig python docs/thesis_figures/create_thesis_figures.py
```

The script reads source tables and existing source figures from the main project folders, then writes PNG/PDF outputs into `main_figures/` and `supporting_figures/`.
