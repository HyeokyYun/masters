# 260316 Analysis Notes

## 연구 흐름

1. `weekly.parquet`에서 매장별 주간 매출 패널을 구성합니다.
2. `meta.csv`와 결합해 업종, 지역, 개점시점, 점포면적 등 메타 정보를 붙입니다.
3. 점포별 집계 피처를 생성합니다.
4. 정규화 매출 시계열에서 변곡점을 찾고 `P1/P2/Pattern/final_code`를 생성합니다.
5. 생애주기를 `rising`, `maintaining`, `declining`으로 요약합니다.
6. 시계열 클러스터링과 지도학습으로 생애주기와 성장요인을 분석합니다.
7. 첫 30주만으로 향후 상태와 미래 매출을 예측합니다.

## 기본 해석 단위

- `store_week_panel.parquet`: 점포-주 패널 원자료
- `store_features_full.csv`: 점포별 집계 피처
- `store_lifecycle_labels.csv`: 생애주기 라벨
- `lifecycle_analysis_table.csv`: 회귀/분류용 마스터 테이블
- `trajectory_cluster_labels.csv`: 시계열 클러스터 라벨
- `early_prediction_dataset.csv`: 조기 예측용 데이터셋

## 조정 가능한 값

- 최소 사용 주 수: `configs/base.json > analysis.min_weeks`
- 클러스터 수: `configs/base.json > analysis.cluster_k`
- 초기 예측 구간: `configs/base.json > analysis.early_window`
- 생애주기 패턴 임계값: `configs/base.json > analysis.pattern_growth_threshold`

## 권장 확인 순서

1. `outputs/tables/panel_coverage_summary.csv`
2. `outputs/tables/lifecycle_distribution.csv`
3. `outputs/figures/trajectory_cluster_means.png`
4. `outputs/tables/life_cycle_classification_metrics.csv`
5. `outputs/tables/early_prediction_metrics.csv`
6. `docs/output_inventory.md`
