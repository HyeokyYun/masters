# KCD Top-Tier 업그레이드 — 연구 산출물 요약

본 보고서는 `top_tier/` 폴더의 원본 KCD 패널 기반 분석과 `thesis/data_external` 외부 행정·상권 데이터를 결합한 산출물을 요약합니다.

## 1. 데이터 기반

- 전체 점포: **59,089**개
- 폐업 점포: **9,247**개 (15.6%)
- 패널(≥52w) 포함: **49,007**개
- 전체 중위 생존주: 217, 폐업: 183, 생존: 225

**Outcome 분포**: Growth=20,087, Stable=18,003, Decline=10,917

## 2. 외부 행정·상권 데이터 검증

KCD 내부 lifecycle 지표가 표본 내부의 예측 성능에만 머물지 않는지 확인하기 위해 서울시 생활인구, 음식점 인허가/폐업 등록부, 상권분석서비스 추정매출·점포 데이터를 결합했다.

- **KCD LEVI vs 생활인구 변화율**: Pearson 0.853, Spearman 0.802, n=25
- **KCD LEVI vs 인허가 폐업률**: Pearson -0.430, Spearman -0.241, n=25
- **KCD 추정 폐업률 vs 인허가 폐업률**: Pearson 0.430, Spearman 0.275, n=25

- **KCD 분기 매출 vs 서울 상권 추정매출**: Pearson 0.766, Spearman 0.727, n=11
- **KCD QoQ 매출증감 vs 외부 QoQ 매출증감**: Pearson 0.839, Spearman 0.891, n=10

**자치구별 외부 검증 테이블 Top-8 (LEVI 순)**
| 자치구 | KCD 점포 | LEVI | 생활인구 변화율 | 인허가 월평균 폐업률 |
| --- | ---: | ---: | ---: | ---: |
| 종로구 | 2,087 | 0.443 | +6.60% | 0.419% |
| 중구 | 1,814 | 0.415 | +10.80% | 0.853% |
| 용산구 | 1,695 | 0.294 | +2.14% | 0.708% |
| 강남구 | 4,074 | 0.274 | +7.02% | 0.962% |
| 마포구 | 3,567 | 0.269 | +1.01% | 1.012% |
| 서초구 | 2,142 | 0.253 | -0.15% | 1.070% |
| 영등포구 | 2,301 | 0.239 | +4.71% | 0.764% |
| 광진구 | 1,899 | 0.213 | -2.82% | 0.913% |

Fig: fig17_external_gu_validation.png, fig18_external_temporal_validation.png. 산출물: external_validation_gu.csv, external_validation_correlations.csv, external_temporal_validation.csv, external_temporal_correlations.csv

## 3. Survivorship Bias 정량화

- 패널 내 폐업률: **8.9%** (n=48,980)
- 패널 바깥 폐업률: **48.3%** (n=10,027)
- ⇒ 기존 분석의 Growth/Stable 결론은 생존자 편향을 포함. 패널-밖 **폐업**이 약 5배 높음.

## 4. Kaplan-Meier 생존 분석

- Log-rank(outcome_3): χ²=7499.4, p=0.00e+00, k=3
- Log-rank(classification__kcd_v3__depth_2_name): χ²=390.0, p=2.85e-75, k=14

## 5. Cox Proportional Hazards

- 관측치 48,980개, event 4,352개, concordance=0.819

| 공변량 | HR | 95% CI | p |
| --- | --- | --- | --- |
| nc_rate | 1.141 | [1.108, 1.174] | 4.31e-19 |
| cv | 1.092 | [1.061, 1.123] | 1.06e-09 |
| slope_early_mm | 1.065 | [1.034, 1.097] | 2.67e-05 |
| slope_late_mm | 0.777 | [0.750, 0.804] | 2.88e-46 |
| r2_early | 1.194 | [1.161, 1.227] | 1.26e-35 |
| mdd | 0.744 | [0.729, 0.759] | 3.81e-174 |
| trend_slope | 0.444 | [0.428, 0.461] | 0.00e+00 |

## 6. 클러스터링 품질

**KMeans** top-3 by silhouette:
  - K=4: sil=0.168, DB=1.870
  - K=3: sil=0.167, DB=1.810
  - K=5: sil=0.122, DB=1.992
**GMM** top-3 by silhouette:
  - K=3: sil=0.006, DB=6.437
  - K=4: sil=-0.029, DB=7.638
  - K=5: sil=-0.044, DB=6.336
**KShape** top-3 by silhouette:
  - K=3: sil=0.022, DB=3.642
  - K=4: sil=-0.019, DB=5.619
  - K=5: sil=-0.034, DB=4.387

**External validation (vs UDX label / outcome_3)**: top NMI
- nmi_vs_outcome:
  - KMeans K=6: NMI=0.156
  - KMeans K=11: NMI=0.154
  - KMeans K=9: NMI=0.152
- nmi_vs_label:
  - KShape K=7: NMI=0.182
  - KShape K=12: NMI=0.181
  - KShape K=9: NMI=0.180

## 7. 30주 조기 예측 — 모델 비교

```
     Unnamed: 0 macro_f1 macro_f1.1 weighted_f1 weighted_f1.1 auc_ovr auc_ovr.1 precision_Growth precision_Growth.1 recall_Growth recall_Growth.1 f1_Growth f1_Growth.1 precision_Stable precision_Stable.1 recall_Stable recall_Stable.1 f1_Stable f1_Stable.1 precision_Decline precision_Decline.1 recall_Decline recall_Decline.1 f1_Decline f1_Decline.1  fold  fold.1
0           NaN     mean        std        mean           std    mean       std             mean                std          mean             std      mean         std             mean                std          mean             std      mean         std              mean                 std           mean              std       mean          std  mean     std
1         model      NaN        NaN         NaN           NaN     NaN       NaN              NaN                NaN           NaN             NaN       NaN         NaN              NaN                NaN           NaN             NaN       NaN         NaN               NaN                 NaN            NaN              NaN        NaN          NaN   NaN     NaN
2      Logistic   0.5189     0.0042      0.5249        0.0037  0.3839    0.0033           0.5986             0.0043        0.6102          0.0065    0.6043      0.0047           0.5084             0.0071        0.4033          0.0046    0.4498      0.0053             0.444              0.0086         0.5794           0.0151     0.5027       0.0105   2.0  1.5811
3  RandomForest   0.5469     0.0037      0.5546        0.0029  0.3741    0.0026           0.6164             0.0027        0.6323          0.0047    0.6243      0.0031            0.514              0.004        0.4873          0.0039    0.5003      0.0032            0.5065               0.009          0.526           0.0126      0.516       0.0101   2.0  1.5811
4       XGBoost    0.548     0.0033      0.5607        0.0022  0.7356    0.0029           0.5974              0.002        0.6944          0.0064    0.6423      0.0035           0.5128             0.0052        0.5146          0.0074    0.5137      0.0059            0.5949              0.0114         0.4139           0.0155     0.4881        0.014   2.0  1.5811
```

## 8. Granger Causality

- 테스트 점포: 3,000
- nc→sales 유의: **10.5%**
- sales→nc 유의: 11.2%
- 비대칭(nc만 유의): **8.8%**

## 9. PSM + DiD (골든 크로스 처치효과)

- ATT = **+0.1165** (log-sales)
- t=18.07, p=1.805e-72
- n_treated=14,842, n_control=14,398

## 10. Panel Two-way FE Regression

```
      Unnamed: 0          coef   std_err             t              p  ci_lower  ci_upper   n_obs  n_stores
0          const -8.678200e-16  0.000051 -1.685604e-11   1.000000e+00 -0.000101  0.000101  988698     10000
1       nc_l1_fe  2.775516e-01  0.007421  3.740222e+01  3.596342e-306  0.263007  0.292096  988698     10000
2       nc_l2_fe  7.663668e-02  0.007034  1.089543e+01   1.211870e-27  0.062851  0.090423  988698     10000
3       nc_l4_fe  1.005480e-01  0.005296  1.898537e+01   2.253584e-80  0.090168  0.110928  988698     10000
4  sales_lag1_fe  6.199791e-01  0.007881  7.866871e+01   0.000000e+00  0.604533  0.635425  988698     10000
```

## 11. SHAP Feature Importance (Top-10)

```
       feature  mean_abs_shap
0      bn_mean       0.373437
1    slope_all       0.321736
2   ma10_slope       0.312716
3    sales_max       0.240727
4      wk_mean       0.217172
5  slope_21_30       0.165817
6      nc_mean       0.140127
7    ma5_slope       0.132542
8     del_mean       0.129693
9   sales_skew       0.117524
```

## 12. Ablation Study

```
      feature_group  n_features  macro_f1  recall_Growth  recall_Stable  recall_Decline  f1_Growth  f1_Stable  f1_Decline
                all          43  0.559307       0.704040       0.535192        0.420750   0.645653   0.543908    0.488360
              no_nc          37  0.554447       0.699255       0.533798        0.411930   0.642320   0.539624    0.481398
      no_volatility          32  0.558222       0.702314       0.536328        0.417659   0.644826   0.543396    0.486446
           no_slope          38  0.555153       0.702659       0.528376        0.416840   0.641243   0.539648    0.484568
no_delivery_pattern          39  0.553150       0.694914       0.532714        0.414566   0.639059   0.540197    0.480193
    only_core_stats           7  0.521271       0.662704       0.508185        0.376284   0.609993   0.510542    0.443279
```

## 13. Hybrid Prediction — Proposed Model

| Model | F1 (mean) | F1 (std) | Growth Recall | Decline Recall | AUC |
| --- | --- | --- | --- | --- | --- |
| A_base_46 | 0.548 | 0.003 | 0.694 | 0.414 | 0.736 |
| B_base_cluster | 0.634 | 0.006 | 0.760 | 0.536 | 0.819 |
| C_base_cp | 0.592 | 0.001 | 0.731 | 0.462 | 0.784 |
| D_base_cluster_cp_PROPOSED | 0.639 | 0.005 | 0.771 | 0.548 | 0.824 |

**Proposed Model D** (base + hybrid cluster + change-point)이 Base 대비 F1 +0.10, AUC +0.10 달성.

## 14. Volatility Paradox 재해석

Cox PH에서 cv의 HR=1.11 (전체)로 **변동성↑ ⇒ 폐업 위험↑** 로 추정되나, 실측 분포에서는 Growth의 cv가 Decline보다 높게 나타나는 역설이 관찰됨. 네 가지 가설로 분해 검증.

**H1: Survivorship Bias** — 생존자-only vs 전체 비교
| Population | Outcome | n | cv_mean | cv_median |
| --- | --- | --- | --- | --- |
| Survivors only (is_closed=0) | Growth | 19,678 | 0.413 | 0.366 |
| Survivors only (is_closed=0) | Stable | 17,848 | 0.373 | 0.291 |
| Survivors only (is_closed=0) | Decline | 8,242 | 0.570 | 0.471 |
| All stores (including closed) | Growth | 20,273 | 0.412 | 0.365 |
| All stores (including closed) | Stable | 19,365 | 0.364 | 0.287 |
| All stores (including closed) | Decline | 10,997 | 0.592 | 0.495 |
| All stores (including closed) | Closed | 4,867 | 0.500 | 0.425 |

**H2: Phase-dependent volatility** — 관측 구간을 3분할
| Phase | Outcome | n | cv_mean | cv_median |
| --- | --- | --- | --- | --- |
| cv_w1_15 | Growth | 20,273 | 0.036 | 0.030 |
| cv_w1_15 | Stable | 17,737 | 0.036 | 0.029 |
| cv_w1_15 | Decline | 10,997 | 0.034 | 0.027 |
| cv_w16_30 | Growth | 20,273 | 0.021 | 0.016 |
| cv_w16_30 | Stable | 17,737 | 0.022 | 0.015 |
| cv_w16_30 | Decline | 10,997 | 0.025 | 0.018 |
| cv_w31_plus | Growth | 20,273 | 0.032 | 0.028 |
| cv_w31_plus | Stable | 17,737 | 0.032 | 0.027 |
| cv_w31_plus | Decline | 10,997 | 0.044 | 0.034 |

초기(w1-15)만 Growth > Decline. 중기·후기(w16-30, w31+)는 Growth < Decline으로 역전. 즉 "변동성 Growth"는 **초기 phase에 국한된 현상**.

**H3: Inverted-U** — cv decile별 Growth/Decline 비율
| Decile | n | Growth rate | Decline rate | Closure rate | cv range |
| --- | --- | --- | --- | --- | --- |
| D0 | 5,064 | 0.135 | 0.054 | 0.183 | 0.000–0.207 |
| D1 | 5,063 | 0.347 | 0.091 | 0.050 | 0.207–0.245 |
| D2 | 5,064 | 0.436 | 0.120 | 0.048 | 0.245–0.278 |
| D3 | 5,063 | 0.485 | 0.148 | 0.053 | 0.278–0.314 |
| D4 | 5,064 | 0.511 | 0.178 | 0.059 | 0.314–0.357 |
| D5 | 5,063 | 0.514 | 0.207 | 0.071 | 0.357–0.410 |
| D6 | 5,063 | 0.513 | 0.239 | 0.086 | 0.410–0.479 |
| D7 | 5,064 | 0.497 | 0.266 | 0.094 | 0.479–0.580 |
| D8 | 5,063 | 0.375 | 0.354 | 0.129 | 0.580–0.762 |
| D9 | 5,064 | 0.191 | 0.516 | 0.188 | 0.762–5.000 |

Growth 비율 최대 decile: **D5** (cv 0.36–0.41) — 역U 패턴 확인.

**H4: Outcome-specific Cox HR** — outcome subgroup 내 cv의 hazard
| Subgroup | n | events | HR(cv) | 95% CI | p |
| --- | --- | --- | --- | --- | --- |
| Growth | 20,273 | 595 | 0.839 | [0.775, 0.908] | 1.49e-05 |
| Stable | 19,355 | 1,512 | 0.612 | [0.574, 0.652] | 8.64e-52 |
| Decline | 10,977 | 2,738 | 1.183 | [1.144, 1.222] | 2.86e-23 |

Growth/Stable 내부에서는 cv가 **보호 요인** (HR<1), Decline 내부에서만 **위험 요인** (HR>1). 전체 Cox의 cv HR=1.11은 Decline 그룹이 지배적으로 기여한 결과.

**해석**: 'Volatility Paradox'는 측정 window, outcome 이질성, survivorship이 겹친 표면적 현상. 초기 변동성은 탐색적 적응으로 Growth와 양립, 후기 변동성은 구조적 붕괴 신호로 Decline을 지시.

## 15. Early Warning System (EWS)

Proposed Model D의 5-fold OOF 확률을 실무 의사결정 지원 산출물로 변환 (risk_score_decline ∈ [0, 100]).

- Average Precision — Decline: **0.688** (baseline 0.223) / Growth: **0.819** (baseline 0.410)
- Brier — Decline: 0.1112, Growth: 0.1442

**Operating points (Decline)** — threshold별 trade-off
| Threshold | Precision | Recall | F1 | Flagged % |
| --- | --- | --- | --- | --- |
| 0.05 | 0.318 | 0.977 | 0.479 | 68.5% |
| 0.15 | 0.433 | 0.893 | 0.583 | 46.0% |
| 0.25 | 0.524 | 0.783 | 0.628 | 33.3% |
| 0.35 | 0.605 | 0.660 | 0.631 | 24.3% |
| 0.45 | 0.685 | 0.538 | 0.603 | 17.5% |
| 0.55 | 0.748 | 0.421 | 0.539 | 12.5% |
| 0.65 | 0.813 | 0.309 | 0.447 | 8.5% |
| 0.75 | 0.870 | 0.195 | 0.318 | 5.0% |
| 0.85 | 0.922 | 0.088 | 0.161 | 2.1% |
| 0.95 | 0.986 | 0.019 | 0.037 | 0.4% |

**Cost-sensitive analysis** — B_prevent=10, C_support=2, C_miss=8
- 최적 threshold = **0.10**, Net utility = **43,626** (TP=10,256, FP=16,567, FN=661)

**Top-5 high-risk 업종 (mean risk score)**
| Category | n | Mean | Median |
| --- | --- | --- | --- |
| 패스트푸드 | 4,044 | 35.2 | 29.3 |
| 분식 | 2,398 | 30.6 | 21.8 |
| 분류정보없음 | 1,591 | 29.1 | 19.8 |
| 카페 | 7,603 | 25.3 | 19.7 |
| 베이커리/디저트 | 2,391 | 22.4 | 12.7 |

Fig: fig10_calibration.png, fig11_pr_curves.png, fig12_cost_benefit.png, fig13_ews_by_category.png
산출물: ews_scores_per_store.csv (store-level risk score), ews_operating_points_decline.csv, ews_cost_benefit.csv, ews_segment_score_distribution.csv

## 16. Deep Sequence Baseline 비교

Deep sequence baseline 표는 아직 새 `original_data` 기반 label로 재학습하지 않았다. 기존 deep baseline 산출물은 legacy 결과로 보존하되, 현재 리포트의 핵심 수치에는 포함하지 않는다. 현재 갱신 완료된 비교는 classical baseline vs Hybrid Proposed D이다.

## 17. Robustness 재실행 상태

기존 audit01-04, fold-safe leakage, enhanced PSM, multivariate deep-learning robustness 파일은 legacy label 기준 결과가 섞여 있어 현재 `original_data` 기반 리포트 본문에서는 제외한다. 새 기준으로 갱신 완료된 항목은 data foundation, survival/Cox, prediction baseline, hybrid model, EWS, SHAP, external validation이다.
