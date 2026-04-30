# 성능 향상 및 회귀(Regression) 진행 가이드

## 1. 현재 구조 요약

| 구분 | 입력(피처) | 타깃 | 비고 |
|------|------------|------|------|
| **260211 분류** | **첫 30주** 피처만 | 성장(1)/하락(0) | 31주~끝 기울기 ≥ 0 이진 |
| **260211 회귀** | **첫 30주** 피처만 | **31주~끝 구간 기울기** (slope_after_30w) | 30주 기반 회귀 |
| **260204 run_03** | **전체 기간** 집계 피처 (store_features) | **성장률(growth_rate)** | OLS, 설명용 (train/test 없음) |
| **260211 회귀(총매출)** | **첫 30주** 피처만 | **31주~끝 총 매출** (total_sales_after_30w) | M0/M1, Ridge/XGBRegressor, 8:2 |
| **260204 run_03_total_sales** | **전체 기간** 피처 (avg·total_weeks 제외) | **전체 총 매출** (avg×주수) | OLS, 설명용 |
| **260204 run_04** | 전체 기간 피처 + 클러스터 | success(1/0) | growth_rate ≥ 1.0 이진 |

### 1.1 “30주 회귀” vs “전체 매출/전체 기간 회귀”

- **30주에 대한 회귀 (260211)**  
  - **입력**: 매장당 **첫 30주**만 사용해 만든 피처 (평균·표준편차·기울기 등).  
  - **타깃**: 31주~끝 구간 매출의 **선형 기울기(slope_after_30w)** (연속값).  
  - 즉, “30주(입력)로 이후 구간의 **추세(기울기)** 를 예측”하는 회귀입니다. **전체 매출액**을 예측하는 회귀는 아닙니다.

- **전체 기간 데이터로 하는 회귀 (260204 run_03)**  
  - **입력**: **전체 기간** 매출·메타로 만든 store_features (avg_sales_card, trend_slope, 지역·업종 등).  
  - **타깃**: **growth_rate** (전체 기간에서 정의된 성장률, 예: 초기 25% vs 후기 25% 구간 비교).  
  - 즉, “전체 기간 요약 피처로 **성장률(growth_rate)** 을 설명”하는 OLS 회귀입니다.

- **전체 매출(총 매출액) 회귀**  
  - **260211** `run_regression_total_sales_30w.py`: 첫 30주 피처 → **31주~끝 구간 총 매출** (`total_sales_after_30w`) 예측 (M0/M1, Ridge/XGBRegressor, 8:2).  
  - **260204** `run_03_regression_total_sales.py`: 전체 기간 피처(avg_sales_card·total_weeks 제외) → **전체 총 매출** (avg_sales_card × total_weeks) 설명 OLS.

---

## 2. 성능을 더 올리는 방법

### 2.1 분류(260211) 성능 향상

- **회귀 후 이진화 (regression-then-classify)**  
  연속 타깃(slope_after_30w)을 예측한 뒤 `pred >= 0`으로 성장/하락을 나누면, 이진 분류만 할 때보다 성능이 나은 경우가 많습니다.  
  → `run_regression_30w.py`에서 M0/M1별로 `f1_from_regression`을 보고, 기존 `run_prediction_80_20` F1과 비교해 보세요.

- **피처 확장 (30주 구간)**  
  - 30주를 10주씩 나눠 구간별 기울기·평균·변동계수 추가  
  - 초반 5주 vs 후반 5주 비율, 최대/최소 발생 주차 등  
  → `build_30w_features_and_labels.py`의 `features_from_first_n_weeks`를 확장해 새 컬럼을 넣고, 동일 8:2로 재학습·평가.

- **메타(지역·업종) 활용**  
  이미 M0_meta, M1_meta로 넣었으면, 회귀 쪽에도 동일하게 M0_meta·M1_meta 스펙을 두고 R²·RMSE를 비교할 수 있습니다 (필요 시 `run_regression_30w.py`에 meta 더미 추가).

- **클래스 불균형**  
  하락이 소수면 `class_weight="balanced"`(LR), `scale_pos_weight`(XGB)는 이미 적용됨.  
  필요 시 오버샘플링(SMOTE) 또는 임계값 조정(0이 아닌 최적 cutoff)을 시도.

- **모델·하이퍼파라미터**  
  - XGBoost/LightGBM: `n_estimators`, `max_depth`, `learning_rate` 등 그리드 서치  
  - Ridge 회귀: `alpha` 튜닝 (회귀 쪽)

### 2.2 회귀(260211) 성능 향상

- **타깃 변환**  
  slope가 왜도가 크면 `log(slope + c)` 또는 표준화만 해서 학습 후 역변환 예측.  
  → R²·RMSE가 개선되는지 비교.

- **동일 피처 확장**  
  분류와 동일하게 30주 구간 기반 피처를 늘리면 회귀 R²도 올라갈 수 있음.

- **정규화**  
  Ridge 외에 Lasso/ElasticNet, XGBRegressor에 정규화 파라미터를 두고 비교.

---

## 3. “결국 regression을 해야 한다”에 대한 정리

### 3.1 논문에서 regression의 위치

- **설명 목적 (왜 성장률이 달라지는가)**  
  → **260204 run_03 OLS** 유지. growth_rate를 종속변수로 두고 계수·유의성으로 변수 해석.  
  이미 `ols_growth_rate.csv`로 결과가 있음.

- **예측 목적 (첫 30주만 보고 이후 기울기/성장 여부를 맞추기)**  
  → **260211**에서  
  1) **분류**: 기존처럼 성장/하락 이진 예측 (run_prediction_80_20),  
  2) **회귀**: 첫 30주 → `slope_after_30w` 연속값 예측 (run_regression_30w).  
  회귀 결과를 임계값 0으로 이진화하면 “regression으로 분류 성능까지” 논의 가능.

### 3.2 실행 순서 (회귀 포함)

1. **피처·연속 타깃 생성**  
   ```bash
   cd 260211
   python scripts/build_30w_features_and_labels.py
   ```  
   → `features_30w_and_labels.parquet`에 `growth`, `slope_after_30w` 모두 포함.

2. **분류 (기존)**  
   ```bash
   python scripts/run_prediction_80_20.py
   ```  
   → `prediction_80_20_results.csv`, M0/M1 등 F1.

3. **회귀 (신규)**  
   ```bash
   python scripts/run_regression_30w.py
   ```  
   → `regression_30w_results.csv` (RMSE, MAE, R², 선택 시 f1_from_regression),  
   → `regression_30w_r2.png`.

4. **260204 OLS (설명용)**  
   data_features_clean 준비 후  
   ```bash
   cd 260204 && python scripts/run_03_regression_ols.py
   ```  
   → `ols_growth_rate.csv`.

### 3.3 논문 서술 예시

- “매출 성장률(growth_rate)에 대한 설명은 OLS 회귀(260204)로 제시하였고, 개업 초기 30주만을 사용한 **예측**은 연속 기울기(slope_after_30w) 회귀(260211)와 성장/하락 이진 분류(260211)를 모두 수행하였다. 회귀 예측값을 0으로 이진화한 경우의 F1도 분류 모델과 비교하였다.”

---

## 4. 요약

- **성능 올리기**: (1) 회귀 후 이진화 F1 확인, (2) 30주 피처 확장, (3) 메타·클러스터 활용 유지, (4) 모델/하이퍼파라미터 튜닝.  
- **Regression**: (1) 설명용 = 260204 run_03 OLS 유지, (2) 예측용 = 260211에 `slope_after_30w` 회귀 추가(run_regression_30w), (3) 회귀→이진 F1으로 분류와 동일 조건 비교.

이미 반영된 코드: `build_30w_features_and_labels.py`에 `slope_after_30w` 추가, `260211/scripts/run_regression_30w.py` 추가.
