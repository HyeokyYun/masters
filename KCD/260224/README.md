# 260224 — 논문용 결과물 집합체 (전체 파이프라인 단계별 정리)

**목적**: 260121 → 260204 → 260204_gem → 260211 → 260223까지 진행한 **모든 결과물**을 논문 단계 순서에 맞게 한 곳에 모은 폴더입니다.  
**생성일**: 2026-02-24

---

## 논문 단계별 폴더 구조

| 단계 | 폴더 | 내용 | 출처 |
|------|------|------|------|
| **1** | `01_data` | 데이터 정의·정제·변수 설명 | 260204 run_01, basic_data |
| **2** | `02_clustering` | 시계열 클러스터링, 방법 비교, 코드 분류, 아웃라이어 제거, 결정요인 분석 | 260121, 260204 |
| **3** | `03_inflection_udx` | 변곡점(P1/P2) 추출, U/D 라벨, 최종 UDX 코드 | 260204_gem |
| **4** | `04_regression` | OLS/Logit 회귀 (growth_rate, 성공·클러스터별), Model 1/2/3 | 260204, 260223 |
| **5** | `05_prediction_ablation` | 30주 기반 예측·회귀, 성공 예측 ablation, Event Study 집계, Ablation 성능 | 260211, 260204, 260223 |
| **6** | `06_final_econometric` | 최종 마스터 테이블, 회귀표, Event Study·Ablation 표·그림 (논문 4·5장용) | 260223, 260204 figures |

---

## 1. 01_data — 데이터

- **data_features_clean.parquet**: 260204 run_01 정제 피처 (33,514업장). 260223 Step 1 입력.
- **variable_description_copy.csv** / **variable_description.csv**: 변수 정의.
- **data_missing_top30.csv**: 결측 상위 30 변수.
- *(원본 업장별 피처 CSV: `../basic_data/store_features_for_analysis.csv` — 용량 관계로 미복사, 필요 시 해당 경로 사용.)*

---

## 2. 02_clustering — 클러스터링·분류

- **6_cluster_labels.csv**: 260121 TimeSeriesKMeans 6클러스터 라벨.
- **6_cluster_*_distribution.csv**: 클러스터별 depth_1/2/3, sigungu, dong 분포.
- **code_classification/**: 피처로 생애주기 코드 분류 결과 (XGBoost, RF, LR 성능·중요도).
- **compare_methods_no_dtw.csv**: 260204 euclidean vs K-Shape 방법 비교.
- **cluster_stability_summary.csv**: K-Shape K=4~8 안정성 요약.
- **store_cluster_labels_K6.parquet**: 260204 K-Shape K6 최종 라벨 (260223에서 사용).
- **outlier_removal/**: 아웃라이어 제거 후 클러스터 라벨·통계.
- **determinant_analysis/**: 클러스터 결정요인 분석 (ANOVA, 로짓, RF/XGB 성능·중요도).

---

## 3. 03_inflection_udx — 변곡점·UDX

- **inflection_p1p2_labels.csv**: 구간별 변곡점(P1/P2), 기울기 U/D.
- **final_code_by_store_260121_outlier_removal.csv**: U/D + X/Y/Z 매핑 최종 코드 (DUY, DDZ 등). 260223 Step 2 입력.
- **UDX_analysis_report.csv**: UDX 분석 요약.

---

## 4. 04_regression — 회귀

- **ols_growth_rate.csv**: 260204 OLS (growth_rate 종속).
- **ols_total_sales.csv**: 260204 총매출 회귀.
- **regression_tables_ols.csv**, **regression_tables_logit.csv**: 260223 OLS/Logit long 형식 (Model 1/2/3).
- **regression_ols_wide_coef.csv**, **regression_ols_wide_pvalue.csv**: OLS 계수·p-value 가로 배치 (논문 표).
- **regression_logit_wide_coef.csv**, **regression_logit_wide_pvalue.csv**: Logit 계수·p-value 가로 배치 (논문 표).

---

## 5. 05_prediction_ablation — 예측·Ablation

- **success_rate_by_cluster.csv**: 260204 클러스터별 성공률.
- **ablation_results.csv**: 260204 M0~M3 성공 예측 ablation (LR vs XGB).
- **prediction_80_20_results.csv**: 260211 첫 30주 기반 8:2 예측 결과 (M0~M3).
- **regression_30w_results.csv**, **regression_total_sales_30w_results.csv**: 260211 30주 기반 회귀 결과.
- **event_study_means.csv**: 260223 Event Study — 변곡점 t=0 전후 12주, DUY vs DDZ 그룹별 평균·표준오차.
- **prediction_metrics.csv**: 260223 Ablation — base_only vs base_udx_inflection, RF/XGB/LGB accuracy·F1.

---

## 6. 06_final_econometric — 최종 계량·논문 4·5장

### tables

- **df_base_features.csv**, **df_udx_labels.csv**: 260223 마스터·UDX 통합 테이블.
- **regression_tables_ols.csv**, **regression_tables_logit.csv**, **regression_*_wide_*.csv**: 회귀 표.
- **event_study_means.csv**, **prediction_metrics.csv**: Event Study·Ablation 수치.

### figures

- **event_study_plots.png**: 변곡점 t=0 전후 DUY vs DDZ 신규 고객 비율(또는 4주 매출성장률) 추이.
- **feature_importance_*_full.png**, **shap_summary_*.png**: Ablation 변수 중요도·SHAP 요약.
- **cluster_means_K4.png** ~ **K8.png**: K-Shape 클러스터 평균 시계열.
- **success_rate_by_cluster.png**, **ablation_f1.png**: 260204 성공률·ablation F1.

---

## 원본 경로 (재생성 시 참고)

- **260121**: `260121/result_csv/`, `260121/result_csv/code_classification/`, `260121/result_csv/determinant_analysis/`
- **260204**: `260204/outputs/`, `260204/outputs/tables/`, `260204/outputs/figures/`
- **260204_gem**: `260204_gem/outputs/tables/`
- **260211**: `260211/outputs/tables/`
- **260223**: `260223/outputs/tables/`, `260223/outputs/figures/`
- **260223**: `260223/outputs/tables/`, `260223/outputs/figures/`
- **basic_data**: `basic_data/store_features_for_analysis.csv`, `basic_data/variable_description.csv`
- **260127**: 결정요인 분석 개선(KNN·Winsorization·SelectKBest 등) 결과는 `260127/model_improvement_v2/results/`, `260127/model_improvement/results/`에 있으며, 필요 시 해당 경로에서 복사해 사용할 수 있습니다.

---

## 논문에서 인용할 때

- **데이터**: 1단계(01_data) 변수 정의·정제 결과 인용.
- **클러스터·분류**: 2단계(02_clustering) 클러스터 라벨·방법 비교·코드 분류·결정요인 인용.
- **변곡점·UDX**: 3단계(03_inflection_udx) 최종 코드·변곡점 인용.
- **회귀**: 4단계(04_regression) OLS/Logit 표 인용.
- **예측·Ablation·Event Study**: 5·6단계 표·그림 인용.

자세한 분석 방법·데이터 범위는 `260223/docs/분석_데이터_및_방법_상세.md`를 참고하세요.
