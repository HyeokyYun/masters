# 260316_cur 분석 요약

## 확인 범위

- 코드: `main.py`, `src/step01_preprocessing.py` ~ `src/step07_visualization.py`, `src/step03_clustering_gpu.py`, `src/config.py`, `requirements.txt`, `readme.md`
- 결과 표: `outputs/tables`
- 결과 그림: `outputs/figures`
- 보조 문서: `cursor_shap_analysis_error_with_gradien.md`

본 문서는 워크스페이스 내부 코드, 주석, 변수명, 실제 저장된 산출물만을 근거로 작성했다.

## 산출물 일치성 메모

- 이 폴더는 `260316`과 달리 `outputs/logs`가 없으며, 파일 로그 대신 콘솔 출력 중심으로 설계되어 있다.
- 현재 저장된 결과는 서로 다른 실행 시점의 산출물이 섞여 있다. 실제 표본 수가 파일별로 다르다.
  - `store_features*.csv`: 21,365개 매장
  - `cluster_labels*.csv`: 11,373개 매장
  - `mnlogit_summary.txt`: 20,794개 관측치
  - `classification_report.txt`, `confusion_matrix.csv`: 10,939개 관측치
- `step04b_variable_selection.py`는 다음 파일을 저장하도록 작성되어 있으나, 현재 `outputs/tables`에는 없다.
  - `label_summary_stats.csv`
  - `variable_importance_test.csv`
  - `selected_variables.csv`
  - `selected_early_variables.csv`
- 코드상 `selected_variables.csv`가 없으면 Step 05는 기본 변수(`DEFAULT_FEATURE_COLS`)를 사용하고, `selected_early_variables.csv`가 없으면 Step 06은 전체 early feature를 사용한다. 현재 저장된 산출물은 이 fallback 결과일 가능성이 높다. 이 부분은 코드와 현재 파일 상태를 바탕으로 한 추론이다.
- `readme.md`와 `step07_visualization.py`는 `fig01`~`fig09` 및 `shap_beeswarm_class0.png` 생성을 설명하지만, 현재 `outputs/figures`에는 `shap_summary_bar.png`, `shap_early_prediction.png` 두 파일만 존재한다.
- `readme.md`와 `step06_prediction.py`의 설명에는 AUC/PR-AUC가 포함되어 있으나, 현재 저장된 `prediction_full_evaluation.csv`에는 `F1_weighted`, `Accuracy`, `Precision`, `Recall`만 있다.
- 현재 코드의 `config.py`는 `CLUSTER_K_RANGE = range(4, 10)`으로 되어 있지만, 실제 산출물에는 `K=3` 평가표와 `cluster_labels_K3.csv`, `cluster_centers_K3.csv`가 존재한다. 따라서 현재 저장된 클러스터 결과는 현재 코드와 다른 실행 시점 또는 다른 설정에서 생성된 것으로 보인다.
- `classification_report.txt`와 `confusion_matrix.csv`는 교차검증 결과가 아니라, 코드상 최적 모델을 전체 데이터에 다시 적합한 뒤 같은 데이터에 예측한 결과다. 발표 자료에서는 `prediction_full_evaluation.csv`의 교차검증 지표와 구분해서 써야 한다.

## 결과 파일 설명

| 단계 | 결과 파일 | 의미 |
| --- | --- | --- |
| Step 02 피처 추출 | `outputs/tables/store_features.csv` | 매장별 시계열/고객/운영/STL 피처 |
| Step 04 레이블 할당 | `outputs/tables/store_features_labeled.csv` | 피처 + 6개 생애주기 레이블 |
| Step 04 레이블 할당 | `outputs/tables/label_feature_means.csv` | 레이블별 평균 피처 비교 |
| Step 04 레이블 할당 | `outputs/tables/label_by_category.csv` | 업종별 레이블 분포 |
| Step 03 클러스터링 | `outputs/tables/cluster_evaluation.csv` | K=3~9의 KMeans 평가 지표 |
| Step 03 클러스터링 | `outputs/tables/cluster_method_comparison.csv` | Euclidean KMeans, DTW-KMeans, K-Shape 비교 |
| Step 03 클러스터링 | `outputs/tables/cluster_labels.csv` | 최적 K의 메인 클러스터 라벨 |
| Step 03 클러스터링 | `outputs/tables/cluster_labels_K3.csv`~`cluster_labels_K9.csv` | K별 라벨 결과 |
| Step 03 클러스터링 | `outputs/tables/cluster_centers_K3.csv`~`cluster_centers_K9.csv` | K별 중심선 |
| Step 03 클러스터링 | `outputs/tables/label_cluster_crosstab.csv` | 레이블과 클러스터의 교차표 |
| Step 03 보조 실험 | `outputs/tables/gpu_cluster_labels_K3_parallel.csv`, `gpu_cluster_centers_K3_parallel.csv`, `gpu_cluster_labels_K4_parallel.csv`, `gpu_cluster_centers_K4_parallel.csv` | GPU/병렬 클러스터링 보조 실험 결과 |
| Step 05 요인 분석 | `outputs/tables/mnlogit_summary.txt` | 다항 로짓 전체 결과표 |
| Step 05 요인 분석 | `outputs/tables/mnlogit_coefficients.csv` | 기준범주 `UU` 대비 계수표 |
| Step 05 요인 분석 | `outputs/tables/gbm_feature_importance.csv` | GBM 중요 변수 |
| Step 05 요인 분석 | `outputs/tables/psm_delivery_effect.csv` | 배달앱 채택 효과의 매칭 후 레이블 분포 차이 |
| Step 05 요인 분석 | `outputs/figures/shap_summary_bar.png` | GBM-SHAP 중요도 막대그래프 |
| Step 06 조기 예측 | `outputs/tables/ablation_early_prediction.csv` | early feature set별 교차검증 F1 비교 |
| Step 06 조기 예측 | `outputs/tables/prediction_full_evaluation.csv` | 모델별 교차검증 조기예측 성능 |
| Step 06 조기 예측 | `outputs/tables/classification_report.txt` | 최적 모델 재적합 후 분류 리포트 |
| Step 06 조기 예측 | `outputs/tables/confusion_matrix.csv` | 최적 모델 재적합 후 혼동행렬 |
| Step 06 조기 예측 | `outputs/figures/shap_early_prediction.png` | 최적 조기예측 모델 SHAP 중요도 |

## 1. 진행한 실험 및 분석의 목적

`260316_cur`은 `260316`의 3분류 파이프라인과 달리, 매장 생애주기를 6개 레이블로 더 세분화해 분석하는 실험 폴더다. 코드 기준 핵심 목적은 다음과 같다.

1. 개점 이후 주간 카드매출 시계열을 STL 기반으로 정제하고 매장별 동적 피처를 추출하는 것
2. 전반기/후반기 기울기와 손실 수준(`mdd`)을 조합해 6개 생애주기 레이블을 정의하는 것
3. 시계열 클러스터링으로 유사 궤적을 묶고, 레이블과의 대응 관계를 확인하는 것
4. 다항 로짓, GBM-SHAP, PSM을 이용해 생애주기 유형을 설명하는 요인을 찾는 것
5. 오픈 후 30주 정보만으로 향후 6개 레이블을 얼마나 조기 예측할 수 있는지 확인하는 것

## 2. 사용된 데이터와 변수들의 의미

### 데이터 구조

- 입력 데이터:
  - `../original_data/weekly.parquet` 또는 `weekly_reduced.parquet`
  - `../original_data/meta.csv`
- 설정값:
  - 최소 관측 주수 `MIN_WEEKS = 52`
  - 최대 사용 주수 `MAX_WEEKS = 108`
  - 개업일 하한 `OPEN_DATE_MIN = 2019-01-01`
  - STL 주기 `STL_PERIOD = 13`
  - 조기예측 구간 `EARLY_WEEKS = 30`

### 이 폴더에서 실제로 사용하는 매출 변수

이 폴더는 `260316`과 달리 `sales_total`이 아니라 `sales_card`를 중심으로 분석한다.

- `step01_preprocessing.py`
  - `sales_card` 음수값을 결측 처리
  - 주별 전체 `sales_card` 합 대비 비율로 `sales_ratio` 계산
  - STL로 `trend`, `seasonal`, `resid` 생성
  - `sales_card_mm`, `trend_mm` MinMax 정규화
- `step02_feature_extraction.py`
  - 최종 피처 생성에는 `sales_card`, `sales_card_mm`, `trend_mm`, `seasonal`, `resid`가 직접 쓰인다.
  - `sales_ratio`는 전처리에서 계산되지만 현재 저장된 `store_features.csv`의 직접 피처로는 남아 있지 않다.

### 주요 피처

`store_features.csv` 기준 주요 설명변수는 다음과 같다.

- 추세 기울기:
  - `slope_early_mm`
  - `slope_late_mm`
  - `slope_all_mm`
  - `slope_tail_mm`
  - `trend_slope`
- 적합도:
  - `r2`
  - `r2_early`
  - `low_r2`
- 변동성과 손실:
  - `cv`
  - `mdd`
- 고객/영업:
  - `nc_rate`
  - `del_ratio_log`
  - `before_noon`
  - `weekend`
- STL 기반 구조:
  - `seasonal_strength`
  - `noise_ratio`
- 관측 길이:
  - `n_weeks`
- 업종:
  - `category`

### 종속변수와 레이블 체계

`step04_label_assignment.py` 기준 종속변수는 `label`이며, 다음 6개 클래스를 사용한다.

- `DD_Z`: 전반 하락, 후반 하락, 고손실
- `DD_Y`: 전반 하락, 후반 하락, 저손실
- `DU`: 전반 하락, 후반 상승
- `UU`: 전반 상승, 후반 상승
- `UD_Z`: 전반 상승, 후반 하락, 고손실
- `UD_Y`: 전반 상승, 후반 하락, 저손실

즉, 이 폴더는 `초기 추세 방향`, `후기 추세 방향`, `손실 깊이`를 함께 반영해 생애주기를 정의한다.

## 3. 분석 방법론

### 3.1 전처리와 피처 생성

- 메타의 `open_month`를 `open_date`로 변환하고 `weeks_since_open`을 계산한다.
- 2019-01-01 이후 개업한 매장만 남긴다.
- 점포별 관측 주 수가 52주 이상인 경우만 유지한다.
- `sales_card`를 업장별로 선형보간하고 forward/backward fill 한다.
- 관측치가 충분하면 STL 분해, 부족하면 7주 rolling mean으로 `trend`를 대체한다.
- 업장별 MinMax 정규화를 수행한다.
- 이후 업장별 1행 피처를 만든다.

### 3.2 시계열 클러스터링

- `sales_card_mm`를 이용해 `(n_stores, week)` 형태의 궤적 행렬을 구성한다.
- 결측이 많은 주차와 매장을 일정 기준으로 제외한 뒤 중앙값 보간을 한다.
- 기본 실험:
  - Euclidean KMeans
  - DTW-KMeans
  - K-Shape
- K는 3~9를 탐색하고 `silhouette` 기준 최적 K를 선택한다.
- `step03_clustering_gpu.py`는 별도의 가속 실험으로, 파일명상 현재는 `parallel` 방식의 K=3,4 결과만 저장돼 있다.

### 3.3 레이블 부여와 클러스터 교차검증

- `mdd` 중앙값을 임계값으로 고손실/저손실을 나눈다.
- `slope_early_mm > 0`, `slope_late_mm > 0` 여부를 조합해 6개 레이블을 만든다.
- `label_cluster_crosstab.csv`로 레이블과 클러스터를 교차 비교한다.
- 코드상 AMI도 계산하지만, 현재 저장된 결과 파일에는 AMI 숫자가 남아 있지 않다.

### 3.4 요인 분석

- 다항 로짓:
  - 기준범주 `UU`
  - 기본 변수 `DEFAULT_FEATURE_COLS`
  - `delivery_link`
  - 업종 더미(`category`)
- 비선형 모델:
  - `GradientBoostingClassifier`
  - 교차검증 지표는 `f1_weighted`
  - SHAP으로 해석
- 인과적 보조분석:
  - `delivery_link`를 처리변수로 놓고 Propensity Score Matching 수행

### 3.5 조기 예측

- 오픈 후 30주 구간만 사용해 early feature를 만든다.
- early feature:
  - `e_slope_all`
  - `e_slope_early`
  - `e_cv`
  - `e_mdd`
  - `e_r2`
  - `e_mean`
  - `e_nc_rate`
- 모델:
  - `RandomForest`
  - `GradientBoosting`
  - `LightGBM`
- Ablation:
  - `Base`
  - `+Shape`
  - `+Customer`
  - 코드상 `Selected`도 가능하지만 현재 관련 변수 선택 파일은 없음

## 4. 결과에 대한 분석

### 4.1 전체 레이블 분포

`store_features_labeled.csv` 기준 21,365개 매장의 레이블 분포는 다음과 같다.

- `UU`: 6,431
- `DU`: 4,031
- `UD_Y`: 3,488
- `UD_Z`: 2,842
- `DD_Z`: 2,540
- `DD_Y`: 2,033

즉, 가장 큰 군은 `지속 성장(UU)`이고, 그 다음은 `반등(DU)`이다. 6분류 체계이지만 완전 쇠퇴(`DD_Z`)보다 상승 또는 반등 성격의 유형이 더 많이 관측된다.

### 4.2 레이블별 평균 피처 차이

`label_feature_means.csv` 기준:

- `UU`
  - `slope_early_mm = 0.0059`
  - `slope_late_mm = 0.0051`
  - `trend_slope = 0.0060`
- `DU`
  - `slope_early_mm = -0.0052`
  - `slope_late_mm = 0.0046`
  - 전반 하락 후 후반 회복
- `DD_Z`
  - `mdd = 0.9987`
  - `cv = 0.4567`
  - `trend_slope = -0.0066`
- `UD_Z`
  - `slope_early_mm = 0.0067`
  - `slope_late_mm = -0.0055`
  - `mdd = 0.9985`

즉, 레이블 정의에 사용된 기울기와 손실 지표가 실제 평균값에서도 선명하게 구분된다.

### 4.3 업종별 레이블 분포

`label_by_category.csv` 기준으로 업종 간 패턴 차이가 존재한다.

- `술집`
  - `UU` 36.6%로 가장 높음
  - `UD_Z` 19.0%도 높음
- `카페`
  - `UD_Y` 20.1%로 완만 하락 비중이 큼
- `패스트푸드`
  - `UU` 18.6%로 낮음
  - `DD_Y + DD_Z` 합이 34.9%로 상대적으로 높음

즉, 업종은 생애주기 레이블과 무관하지 않으며, 특히 `술집`과 `패스트푸드`는 다른 레이블 구성을 보인다.

### 4.4 클러스터링 결과

`cluster_evaluation.csv` 기준:

- 최적 K는 `3`
- K=3:
  - silhouette 0.1726
  - Davies-Bouldin 1.7998
  - Calinski-Harabasz 4141.01
- K가 커질수록 silhouette는 감소하고 Davies-Bouldin은 악화된다.

`cluster_method_comparison.csv` 기준:

- `KMeans-Euclidean (전체)`: silhouette 0.1726
- `DTW-KMeans (층화추출)`: silhouette 0.1521
- `K-Shape (층화추출)`: silhouette 0.0078

즉, 현재 저장된 결과에서는 Euclidean KMeans가 가장 안정적이며, K-Shape는 매우 낮은 분리도를 보인다.

### 4.5 클러스터 표본 범위와 레이블 대응

`cluster_labels.csv`와 `cluster_labels_K3.csv`는 11,373개 매장만 포함한다. 이는 `store_features_labeled.csv`의 21,365개보다 작다. 코드상 궤적 행렬 구성 단계에서 결측 기준으로 매장/주차가 추가 필터링되기 때문이다.

`cluster_labels.csv` 기준 군집 크기:

- cluster 0: 3,820
- cluster 1: 3,012
- cluster 2: 4,541

`label_cluster_crosstab.csv` 기준:

- cluster 0은 `UU`가 1,641건으로 가장 많다.
- cluster 1은 `DU` 848건, `DD_Z` 644건 비중이 상대적으로 크다.
- cluster 2도 `UU` 1,592건이 가장 많지만 `DU` 1,007건도 많다.

즉, 클러스터는 레이블과 완전히 일치하지 않지만, 일부 군은 `UU` 중심, 일부 군은 `DU`·`DD_Z` 비중이 높은 형태로 해석할 수 있다.

### 4.6 다항 로짓 결과

`mnlogit_summary.txt` 기준:

- 기준범주: `UU`
- 관측치 수: 20,794
- Pseudo R-squared: 0.248
- `No. Iterations: 2000`
- `Converged: 0.0000`

즉, 설명력은 일정 수준 확보됐지만, 최종 수렴에는 실패한 결과다. 발표나 논문에는 “해석 참고용”으로 다루는 것이 안전하다.

`mnlogit_coefficients.csv`와 요약표 상단 기준으로 `UU` 대비 주요 설명변수는 다음이 포함된다.

- 연속형:
  - `slope_early_mm`, `cv`, `mdd`, `nc_rate`, `del_ratio_log`, `before_noon`, `weekend`, `trend_slope`, `seasonal_strength`, `noise_ratio`, `n_weeks`, `delivery_link`
- 범주형:
  - `category` 더미

요약표 첫 비교식(`y = 0`, 즉 `DD_Y` 대 `UU`)에서는 `slope_early_mm`, `cv`, `mdd`, `nc_rate`, `del_ratio_log`, `before_noon`, `trend_slope` 등이 유의하게 나타난다. 다만 전체 모형 비수렴 상태를 고려하면 계수 해석은 보수적으로 해야 한다.

### 4.7 GBM 기반 요인 분석과 SHAP

`gbm_feature_importance.csv` 기준 중요도 순위:

1. `slope_early_mm`: 0.5157
2. `mdd`: 0.2184
3. `trend_slope`: 0.1176
4. `n_weeks`: 0.0381
5. `cv`: 0.0229

즉, 이 폴더의 6분류 생애주기 설명에서 가장 중요한 축은 “초기 추세 방향”과 “낙폭 깊이”다.

`shap_summary_bar.png`도 같은 결론을 시각적으로 보여준다.

- 가장 큰 막대: `slope_early_mm`
- 다음: `mdd`, `trend_slope`
- 이후 `n_weeks`, `cv`, `seasonal_strength`, `noise_ratio`, `nc_rate` 순
- `delivery_link`의 기여는 매우 작다.

### 4.8 배달앱 채택 효과(PSM)

`psm_delivery_effect.csv` 기준, 배달앱 채택군(`treated`)과 매칭 통제군 비교:

- `UU`: `-4.10%p`
- `DD_Z`: `+1.81%p`
- `DD_Y`: `+1.66%p`
- `DU`: `+0.70%p`

즉, 현재 저장된 PSM 결과만 보면 배달앱 채택군은 `UU` 비중이 더 낮고, 쇠퇴형(`DD_Z`, `DD_Y`) 비중이 조금 더 높게 나온다. 다만 이는 매칭 기반 보조분석이며, 레이블 분포 차이를 요약한 결과다.

### 4.9 조기 예측: Ablation 결과

`ablation_early_prediction.csv` 기준 최고 성능은 `+Customer + GBM`이다.

- `Base + GBM`: F1 0.3220
- `+Shape + GBM`: F1 0.3716
- `+Customer + GBM`: F1 0.3767
- `+Customer + LightGBM`: F1 0.3638
- `+Shape + RF`: F1 0.3267

즉, 초기 30주 예측에서는 단순 규모/변동성(`Base`)보다 기울기와 적합도(`+Shape`)를 추가할 때 개선폭이 크고, 신규고객비율(`+Customer`)이 소폭 추가 개선을 만든다.

### 4.10 조기 예측: 모델 성능

`prediction_full_evaluation.csv`는 교차검증 기반 성능이다.

- `GBM`: F1_weighted 0.3713, Accuracy 0.3934
- `LightGBM`: F1_weighted 0.3633, Accuracy 0.3567
- `RF`: F1_weighted 0.3331, Accuracy 0.3322

즉, 6개 생애주기를 오픈 후 30주만으로 예측하는 문제는 상당히 어렵다. 3분류였던 `260316`보다 훨씬 낮은 수준의 성능이 저장돼 있다.

### 4.11 조기 예측: 재적합 분류표와 SHAP

`classification_report.txt`와 `confusion_matrix.csv`는 최적 모델 `GBM`을 전체 데이터에 다시 적합한 뒤 같은 데이터에 예측한 결과다.

- support 합계: 10,939
- weighted F1: 0.73
- accuracy: 0.73

혼동행렬 주요 값:

- `DD_Z → DD_Z`: 1,238
- `DU → DU`: 1,987
- `UD_Z → UD_Z`: 1,137
- `UU → UU`: 2,571
- `UD_Y`는 `UU`로 320건 오분류
- `UD_Z`는 `UU`로 369건 오분류

이 값은 교차검증 성능이 아니라 재적합 성능이므로, 발표에서는 `prediction_full_evaluation.csv`보다 낙관적으로 보일 수 있다는 점을 반드시 밝혀야 한다.

`shap_early_prediction.png` 기준 조기예측 SHAP 중요도 순위:

1. `e_slope_all`
2. `e_mean`
3. `e_mdd`
4. `e_r2`
5. `e_cv`
6. `e_nc_rate`
7. `e_slope_early`

즉, 조기예측에서는 초기 30주의 전체 기울기와 평균 수준이 가장 중요하고, 그 다음이 낙폭과 설명력, 변동성, 신규고객비율이다.

## 5. 결과 해석 및 시사점

이 폴더는 연구 전체에서 다음 의미를 가진다.

1. `260316_cur`은 생애주기를 3분류가 아니라 6분류로 세분화해, “상승/하락”뿐 아니라 “반등”, “급락”, “완만 하락”, “저성과 안정”까지 분리하려는 시도다.
2. 실제 결과는 `slope_early_mm`, `mdd`, `trend_slope`가 가장 중요한 결정 요인임을 보여준다. 즉, 생애주기 유형화의 핵심은 초기 추세와 손실 구조다.
3. 업종별 분포와 PSM 결과를 보면, 생애주기는 순수 시계열 패턴만이 아니라 업종 구조와 운영 방식(`delivery_link`)과도 연결될 가능성이 있다.
4. 클러스터링은 K=3일 때 가장 안정적이었고, Euclidean KMeans가 DTW/K-Shape보다 현재 저장 결과상 더 나은 평가를 받았다.
5. 조기 예측은 6분류 문제에서 상당히 어렵다. 초기 30주만으로는 클래스 경계가 충분히 분리되지 않으며, 특히 교차검증 기준 성능은 0.37 수준에 머문다.
6. 반면 재적합 분류표는 0.73 수준으로 높게 나타난다. 따라서 발표에서는 “교차검증 성능”과 “학습 데이터 재적합 성능”을 절대 혼용하면 안 된다.
7. 저장된 산출물 기준으로 Step04b 변수선택 결과와 Step07 그림 대부분이 남아 있지 않다. 따라서 현재 폴더는 “완전한 최종본”이라기보다, 일부 단계 결과가 누락된 중간 또는 혼합 상태의 실행 산출물로 보는 편이 정확하다.

## 한 줄 정리

`260316_cur`은 STL 기반 전처리와 6개 생애주기 레이블 체계를 도입해 `260316`보다 더 세분화된 패턴 유형화를 시도한 폴더이며, 실제 저장 결과상 핵심 설명변수는 초기 기울기와 낙폭이고, 조기 예측은 어려우며, 현재 남아 있는 산출물은 여러 실행 시점이 섞인 상태라 발표 시 파일별 표본과 평가 방식을 분리해 해석해야 한다.
