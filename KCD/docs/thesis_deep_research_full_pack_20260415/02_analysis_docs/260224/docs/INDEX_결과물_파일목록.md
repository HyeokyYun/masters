# 260224 결과물 파일 인덱스 (논문 단계순)

아래는 260224에 포함된 **모든 파일**을 논문 단계 순서대로 나열한 목록입니다. 표/그림 인용 시 파일명으로 찾을 수 있습니다.

---

## 01_data

| 파일명 | 설명 |
|--------|------|
| data_features_clean.parquet | 260204 정제 피처 (33,514업장). 260223 입력. |
| variable_description_copy.csv | 변수 정의 (260204 복사본). |
| variable_description.csv | 변수 정의 (basic_data). |
| data_missing_top30.csv | 결측 상위 30개 변수. |

---

## 02_clustering

| 파일명 | 설명 |
|--------|------|
| 6_cluster_labels.csv | 260121 6클러스터 라벨. |
| 6_cluster_depth_1_distribution.csv | 클러스터별 depth_1 분포. |
| 6_cluster_depth_2_distribution.csv | 클러스터별 depth_2 분포. |
| 6_cluster_depth_3_distribution.csv | 클러스터별 depth_3 분포. |
| 6_cluster_sigungu_distribution.csv | 클러스터별 시군구 분포. |
| 6_cluster_dong_distribution.csv | 클러스터별 동 분포. |
| compare_methods_no_dtw.csv | euclidean vs K-Shape 방법 비교. |
| cluster_stability_summary.csv | K-Shape K=4~8 안정성 요약. |
| store_cluster_labels_K6.parquet | K-Shape K6 최종 라벨. |
| code_classification/classification_report_code_*.csv | 코드 분류 성능 (XGBoost, RF, LR). |
| code_classification/model_performance_code.csv | 코드 분류 모델 성능 요약. |
| code_classification/xgb_feature_importance_code.csv | 코드 분류 XGB 변수 중요도. |
| code_classification/rf_feature_importance_code.csv | 코드 분류 RF 변수 중요도. |
| outlier_removal/cluster_labels_with_outlier_removal.csv | 아웃라이어 제거 후 클러스터 라벨. |
| outlier_removal/outlier_removal_statistics.csv | 아웃라이어 제거 통계. |
| determinant_analysis/anova_results.csv | 클러스터 간 ANOVA. |
| determinant_analysis/classification_report_*.csv | 결정요인 분류 성능. |
| determinant_analysis/model_performance.csv | 결정요인 모델 성능. |
| determinant_analysis/logistic_regression_coefficients.csv | 로짓 계수. |
| determinant_analysis/odds_ratios.csv | 오즈비. |
| determinant_analysis/rf_feature_importance.csv | RF 변수 중요도. |
| determinant_analysis/xgb_feature_importance.csv | XGB 변수 중요도. |
| determinant_analysis/cluster_*_distribution.csv | 클러스터별 업종·지역 분포. |
| determinant_analysis/cluster_summary_statistics.csv | 클러스터 요약 통계. |

---

## 03_inflection_udx

| 파일명 | 설명 |
|--------|------|
| inflection_p1p2_labels.csv | 변곡점 P1/P2, 구간별 기울기 U/D. |
| final_code_by_store_260121_outlier_removal.csv | 최종 UDX 코드 (DUY, DDZ 등). |
| UDX_analysis_report.csv | UDX 분석 요약. |

---

## 04_regression

| 파일명 | 설명 |
|--------|------|
| ols_growth_rate.csv | 260204 OLS (growth_rate 종속). |
| ols_total_sales.csv | 260204 총매출 회귀. |
| regression_tables_ols.csv | 260223 OLS long (Model 1/2/3). |
| regression_tables_logit.csv | 260223 Logit long (Model 1/2/3). |
| regression_ols_wide_coef.csv | OLS 계수 가로 배치. |
| regression_ols_wide_pvalue.csv | OLS p-value 가로 배치. |
| regression_logit_wide_coef.csv | Logit 계수 가로 배치. |
| regression_logit_wide_pvalue.csv | Logit p-value 가로 배치. |

---

## 05_prediction_ablation

| 파일명 | 설명 |
|--------|------|
| success_rate_by_cluster.csv | 클러스터별 성공률. |
| ablation_results.csv | 260204 M0~M3 ablation. |
| prediction_80_20_results.csv | 260211 30주 기반 8:2 예측. |
| regression_30w_results.csv | 260211 30주 기울기 회귀. |
| regression_total_sales_30w_results.csv | 260211 30주 총매출 회귀. |
| event_study_means.csv | 변곡점 t=0 전후 DUY/DDZ 그룹별 평균·se. |
| prediction_metrics.csv | 260223 base vs full Ablation accuracy·F1. |

---

## 06_final_econometric/tables

| 파일명 | 설명 |
|--------|------|
| df_base_features.csv | 260223 마스터 테이블. |
| df_udx_labels.csv | 260223 UDX 통합 라벨. |
| regression_tables_ols.csv | OLS long. |
| regression_tables_logit.csv | Logit long. |
| regression_ols_wide_coef.csv | OLS 계수 wide. |
| regression_ols_wide_pvalue.csv | OLS p-value wide. |
| regression_logit_wide_coef.csv | Logit 계수 wide. |
| regression_logit_wide_pvalue.csv | Logit p-value wide. |
| event_study_means.csv | Event Study 집계. |
| prediction_metrics.csv | Ablation 성능. |

---

## 06_final_econometric/figures

| 파일명 | 설명 |
|--------|------|
| event_study_plots.png | DUY vs DDZ 신규 고객 비율(또는 4주 매출성장률) 추이. |
| feature_importance_randomforest_full.png | RF full 변수 중요도. |
| feature_importance_xgboost_full.png | XGBoost full 변수 중요도. |
| feature_importance_rf.png | RF 변수 중요도 (레거시). |
| shap_summary_plot.png | SHAP bar 요약. |
| shap_summary_randomforest.png | RF SHAP beeswarm. |
| shap_summary_xgboost.png | XGBoost SHAP beeswarm. |
| cluster_means_K4.png ~ K8.png | K-Shape 클러스터 평균 시계열. |
| success_rate_by_cluster.png | 클러스터별 성공률 막대. |
| ablation_f1.png | 260204 ablation F1 비교. |

---

*인덱스 갱신: 2026-02-24. 새 결과 추가 시 이 목록에 파일명·설명을 반영하세요.*
