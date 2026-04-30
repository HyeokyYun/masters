# 260316 Research Pipeline

`original_data/weekly.parquet`와 `original_data/meta.csv`를 기반으로 소상공인 주간 매출의 생애주기 분석, 분류, 요인 파악, 신규 매장 예측을 수행하기 위한 작업 폴더입니다.

## 목표

1. 주단위 매출과 메타데이터를 결합해 분석용 패널과 점포별 피처를 생성합니다.
2. 매장별 생애주기 라벨(`rising`, `maintaining`, `declining`)과 세부 코드(`final_code`)를 생성합니다.
3. 시계열 클러스터링으로 유사 매출 궤적을 그룹화합니다.
4. 머신러닝, 회귀, 멀티노미얼 로짓으로 생애주기와 요인을 분석합니다.
5. 오픈 초기 구간만으로 향후 생애주기와 미래 매출을 예측하는 코드를 제공합니다.
6. 결과물 인벤토리와 로그를 자동 정리합니다.

## 폴더 구조

```text
260316/
├── 01_data_prep/
├── 02_lifecycle/
├── 03_clustering/
├── 04_modeling/
├── 05_prediction/
├── 06_reporting/
├── configs/
├── docs/
├── outputs/
│   ├── figures/
│   ├── logs/
│   └── tables/
├── src/research_pipeline/
├── templates/
└── run_all.py
```

## 단계별 역할

- `01_data_prep/run_prepare_base_data.py`
  - 원천 데이터 로드
  - 주차 패널 정리
  - 점포별 기본 피처 생성
  - 결측 현황 요약 저장
- `02_lifecycle/run_lifecycle_labeling.py`
  - 변곡점 추정
  - P1/P2 상승·하락 라벨
  - 전체 패턴(X/Y/Z) 및 `final_code`
  - 최종 생애주기 카테고리 생성
- `03_clustering/run_time_series_clustering.py`
  - 정규화된 매출 궤적 행렬 생성
  - K-Shape/DTW 가능 시 활용, 없으면 KMeans fallback
  - 클러스터 평균 궤적 그림 저장
- `04_modeling/run_factor_analysis.py`
  - 생애주기 분류 모델 성능 비교
  - 클러스터 포함/제외 ablation 비교
  - 회귀와 멀티노미얼 로짓
  - 요약통계, 변수중요도, 혼동행렬 저장
- `05_prediction/run_early_prediction.py`
  - 초기 30주 피처 생성
  - 초기 30주 기반 `early_cluster` 생성
  - 향후 생애주기 분류
  - 미래 매출 회귀
  - 클러스터 포함/제외 예측 ablation
  - 신규 매장 스코어링용 스키마 저장
- `05_prediction/predict_new_store.py`
  - 학습 후 저장된 모델을 기준으로 신규 매장 주간 데이터 점수화
- `06_reporting/run_build_inventory.py`
  - 산출물 manifest CSV
  - markdown 인벤토리 문서

## 실행 예시

프로젝트 루트(`26-1`)에서 실행합니다.

```bash
.venv/bin/python 260316/run_all.py
```

개별 단계만 실행하려면 예를 들어:

```bash
.venv/bin/python 260316/01_data_prep/run_prepare_base_data.py
.venv/bin/python 260316/02_lifecycle/run_lifecycle_labeling.py
```

## 주요 출력 경로

- 표: `260316/outputs/tables/`
- 그림: `260316/outputs/figures/`
- 로그: `260316/outputs/logs/`

대표 산출물 예시:

- `store_features_full.csv`
- `store_lifecycle_labels.csv`
- `lifecycle_analysis_table.csv`
- `trajectory_cluster_labels.csv`
- `life_cycle_classification_metrics.csv`
- `life_cycle_cluster_ablation_metrics.csv`
- `multinomial_logit_coefficients.csv`
- `early_prediction_metrics.csv`
- `early_prediction_cluster_ablation_metrics.csv`
- `future_sales_regression_metrics.csv`
- `future_sales_cluster_ablation_metrics.csv`
- `output_manifest.csv`

## 추가로 정리한 것

- `docs/analysis_notes.md`: 연구 흐름, 가정, 해석 포인트 정리
- `templates/new_store_weekly_template.csv`: 신규 매장 예측 입력 템플릿
- `docs/output_inventory.md`: 실행 후 생성되는 결과물 요약 문서

## 기본 가정

- 최소 관측 주 수는 기본 52주입니다.
- 생애주기 예측용 조기 관측 구간은 기본 30주입니다.
- 클러스터 수는 기본 6개입니다.
- 세부 값은 `configs/base.json`에서 조정할 수 있습니다.
