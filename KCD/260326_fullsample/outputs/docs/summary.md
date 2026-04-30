# 260326 전체 업장 observed-window 분석 요약

## 분석 목적

이 폴더는 `개업 초기 생애주기`가 아니라, `데이터에서 관측된 구간 기준 성장/안정/하락 패턴`을 전체 업장에 대해 새롭게 분석한 결과입니다.

즉,

- `260319_cur`, `260325`: 개업 후 초기 구간 중심 분석
- `260326_fullsample`: 전체 업장을 대상으로 한 관측 구간 중심 분석

입니다.

## 패널 구성 요약

                     item      value
      weekly_total_stores    59089.0
stores_with_min_obs_weeks    50635.0
           reference_date 2023-08-28

## observed-window 3분류 분포

outcome_3  store_count    share
   Stable        19365 0.382443
   Growth        20273 0.400375
  Decline        10997 0.217182

## 전체 업력 진단

                           item      value
            labeled_store_count    50635.0
                 reference_date 2023-08-28
median_full_business_age_months       54.0
 median_age_at_first_obs_months       24.0

## 전체 업력 구간별 outcome 요약

full_age_bucket outcome_3  store_count
          0_12m   Decline          238
          0_12m    Growth          234
          0_12m    Stable          186
         12_24m   Decline         1907
         12_24m    Growth         1528
         12_24m    Stable         1969
         24_36m   Decline         2130
         24_36m    Growth         2319
         24_36m    Stable         2650
         36_60m   Decline         3581
         36_60m    Growth         5997
         36_60m    Stable         5866
        60_120m   Decline         2467
        60_120m    Growth         6704
        60_120m    Stable         5901
      120m_plus   Decline          654
      120m_plus    Growth         3491
      120m_plus    Stable         2785

## 관측 시작 시점과 실제 업력 차이

full_age_bucket  stores  mean_age_at_first_obs_months  median_age_at_first_obs_months
          0_12m     658                     -3.715805                             0.0
         12_24m    5404                     -0.549223                             0.0
         24_36m    7099                      1.480208                             1.0
         36_60m   15444                     17.244302                            17.0
        60_120m   15072                     53.061969                            50.0
      120m_plus    6930                    147.336075                           133.0

## 모형 적합도

                  model_name    nobs  pseudo_r2           llf           aic
         fullsample_age_base 50635.0   0.042792 -51653.576235 103331.152471
fullsample_age_with_category 50635.0   0.071428 -50108.325236 100276.650471

## 업력 구간별 핵심 feature

이 결과는 `관측 길이(n_observed_weeks_used)`를 제외하고, 실제 해석 가능한 feature만 남겨 업력 구간별 다항 로짓으로 다시 본 것입니다.

### 버킷별 적합도

bucket_code bucket_label    nobs  pseudo_r2  growth_share  stable_share  decline_share
      0_12m       0~12개월   658.0   0.836563      0.355623      0.282675       0.361702
     12_24m      12~24개월  5404.0   0.785816      0.282754      0.364360       0.352887
     24_36m      24~36개월  7099.0   0.800655      0.326666      0.373292       0.300042
     36_60m      36~60개월 15444.0   0.805632      0.388306      0.379824       0.231870
    60_120m     60~120개월 15072.0   0.783553      0.444798      0.391521       0.163681
  120m_plus       120개월+  6930.0   0.756784      0.503752      0.401876       0.094372

### 버킷별 상위 feature

bucket_code bucket_label  rank_within_bucket              feature feature_label  importance_score  growth_coef  decline_coef                       interpretation
      0_12m       0~12개월                   1          trend_slope         매출 추세        137.928087    11.494346     -9.014339           Growth 쪽으로 강하고 Decline은 억제
      0_12m       0~12개월                   2                  mdd    최대 낙폭(MDD)          0.883211    -0.560942      1.175731                            강한 신호는 아님
      0_12m       0~12개월                   3                   cv    기존 변동성(CV)          0.755797     0.678945     -0.044677                            강한 신호는 아님
      0_12m       0~12개월                   4        del_ratio_log    배달 비중(log)          0.602174     0.728537      0.375847                            강한 신호는 아님
      0_12m       0~12개월                   5 business_square_size         점포 면적          0.570118     0.482346      0.003361                            강한 신호는 아님
     12_24m      12~24개월                   1          trend_slope         매출 추세        106.069690     8.839141     -8.218540           Growth 쪽으로 강하고 Decline은 억제
     12_24m      12~24개월                   2                  mdd    최대 낙폭(MDD)          5.232948    -0.286919      1.264878                           Growth를 억제
     12_24m      12~24개월                   3              nc_rate      신규 고객 비율          2.194919     0.375700      0.169980                         Growth 쪽과 연결
     12_24m      12~24개월                   4                   cv    기존 변동성(CV)          0.515837     0.270993      0.128445                         Growth 쪽과 연결
     12_24m      12~24개월                   5        del_ratio_log    배달 비중(log)          0.354577    -0.217829     -0.175859                           Growth를 억제
     24_36m      24~36개월                   1          trend_slope         매출 추세        113.568086     9.464007     -8.567110           Growth 쪽으로 강하고 Decline은 억제
     24_36m      24~36개월                   2                  mdd    최대 낙폭(MDD)         19.493515    -0.101260      1.819806                        Decline 쪽과 연결
     24_36m      24~36개월                   3              nc_rate      신규 고객 비율          5.183066     0.515391      0.155853                         Growth 쪽과 연결
     24_36m      24~36개월                   4        del_ratio_log    배달 비중(log)          1.335906    -0.383653     -0.023545                           Growth를 억제
     24_36m      24~36개월                   5          before_noon      오전 매출 비중          0.618027    -0.230865      0.153889                           Growth를 억제
     36_60m      36~60개월                   1          trend_slope         매출 추세        120.546462    10.045538     -8.168951           Growth 쪽으로 강하고 Decline은 억제
     36_60m      36~60개월                   2                  mdd    최대 낙폭(MDD)          6.366791     0.000699      0.931041                        Decline 쪽과 연결
     36_60m      36~60개월                   3              nc_rate      신규 고객 비율          5.596682     0.466390      0.223040 Stable보다 Growth/Decline 같은 동적 상태와 연결
     36_60m      36~60개월                   4                   cv    기존 변동성(CV)          0.159832     0.031664      0.111420                        Decline 쪽과 연결
     36_60m      36~60개월                   5          before_noon      오전 매출 비중          0.137205     0.013759     -0.106121                            강한 신호는 아님
    60_120m     60~120개월                   1          trend_slope         매출 추세        108.120642     9.010053     -7.120015           Growth 쪽으로 강하고 Decline은 억제
    60_120m     60~120개월                   2                  mdd    최대 낙폭(MDD)         11.557755     0.179333      1.070390 Stable보다 Growth/Decline 같은 동적 상태와 연결
    60_120m     60~120개월                   3              nc_rate      신규 고객 비율          7.466502     0.622209      0.331228 Stable보다 Growth/Decline 같은 동적 상태와 연결
    60_120m     60~120개월                   4              weekend      주말 매출 비중          0.189016    -0.105600     -0.027204                           Growth를 억제
    60_120m     60~120개월                   5          before_noon      오전 매출 비중          0.136450     0.043299     -0.113788                            강한 신호는 아님
  120m_plus       120개월+                   1          trend_slope         매출 추세         96.888429     8.074036     -6.162553           Growth 쪽으로 강하고 Decline은 억제
  120m_plus       120개월+                   2              nc_rate      신규 고객 비율          6.124874     0.510445      0.459781 Stable보다 Growth/Decline 같은 동적 상태와 연결
  120m_plus       120개월+                   3                  mdd    최대 낙폭(MDD)          2.687077    -0.026528      0.761583                        Decline 쪽과 연결
  120m_plus       120개월+                   4          before_noon      오전 매출 비중          1.591827     0.287058      0.035349                         Growth 쪽과 연결
  120m_plus       120개월+                   5              weekend      주말 매출 비중          1.400365    -0.246150     -0.302936  Growth와 Decline 모두 낮아져 Stable 쪽과 연결
