# 연구 흐름(분석 → 분류 → 예측) 및 학위논문 마무리 체크리스트

## 1. 연구 흐름 전체도: 분석 → 분류 → 예측

```
[원본 데이터]
  original_data/weekly_processed.parquet, meta_processed.csv
           │
           ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ 1. 분석 (Analysis)                                                        │
├──────────────────────────────────────────────────────────────────────────┤
│ • 260121: 원본 → 매장별 시계열 집계 (regenerate_store_features.py)         │
│   → basic_data/store_features_for_analysis.csv (growth_rate, trend 등)   │
│ • 260204_gem: 변곡점 추출 (P1/P2), 구간별 기울기 U/D 라벨                  │
│ • 260204 run_01: 피처 정제 (결측 처리) → data_features_clean.parquet       │
│ • 260204 run_03: OLS 회귀 (growth_rate 설명 변수) → ols_growth_rate.csv    │
└──────────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ 2. 분류 (Classification / Clustering)                                    │
├──────────────────────────────────────────────────────────────────────────┤
│ • 260121: 시계열 클러스터링 (TimeSeriesKMeans euclidean, 9→6 클러스터)      │
│   → cluster_labels.csv, 6_cluster_labels.csv                             │
│ • 260121 code_classification: 피처로 생애주기 코드(code) 분류 (XGBoost 등) │
│ • 260204 run_02: 주별 매출 시계열 K-Shape (K=4~8) + 안정성                 │
│   → store_cluster_labels_K6.parquet (최종 사용), cluster_means_K*.png     │
│ • 260204 run_00_compare: euclidean vs kshape 안정성·M1 F1 비교            │
│   → compare_methods_no_dtw.csv                                            │
│ • 260204_gem: 클러스터 → X/Y/Z 패턴 매핑, U/D + X/Y/Z → 최종 코드          │
│   → final_code_by_store_260121_outlier_removal.csv                         │
└──────────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ 3. 예측 (Prediction)                                                      │
├──────────────────────────────────────────────────────────────────────────┤
│ • 260211: 첫 30주만 사용한 성장/하락 예측 (실제 운영 조건 시뮬레이션)        │
│   - build_30w_features_and_labels: 원본 → 30주 피처 + 31주~끝 기울기 라벨   │
│   - run_prediction_80_20: 8:2 분할, M0(피처만) vs M1(피처+클러스터 더미)    │
│   → prediction_80_20_results.csv, prediction_80_20_M0_vs_M1.png            │
│ • 260204 run_04: 성공(success = growth_rate ≥ 1.0) 예측 ablation           │
│   - M0~M3 (피처만 / +클러스터 / +메타·숫자 / 둘 다), LR vs XGB             │
│   → success_rate_by_cluster.csv, ablation_results.csv, ablation_f1.png    │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 지금까지 완료된 것 (요약)

| 단계 | 내용 | 산출물 |
|------|------|--------|
| 분석 | 원본→매장별 피처, 변곡점 U/D, 피처 정제, OLS | store_features_for_analysis.csv, inflection_p1p2, data_features_clean, ols_growth_rate |
| 분류 | 260121 클러스터 6, 260204 K-Shape K6, 방법 비교, 코드 분류 | cluster_labels, store_cluster_labels_K6, compare_methods_no_dtw, code_classification 결과 |
| 예측 | 30주 기반 8:2 예측(M0/M1), 260204 ablation(M0~M3) | prediction_80_20_results, ablation_results, success_rate_by_cluster |

---

## 3. 논문 마무리를 위해 “더 해야 할 것”

### 3.1 반드시 할 것 (문서·정리)

| 번호 | 할 일 | 참고 |
|------|--------|------|
| 1 | **방법론**: 분석→분류→예측 순서로 한 번에 서술. 클러스터링은 260213 미팅 문서 반영 (경제 TS, K-Shape 한계, K=6·방법 선정 이유). | `260213_meeting_clustering_methodology.md` |
| 2 | **데이터 출처**: 원본 = weekly_processed.parquet + meta_processed.csv. store_features_for_analysis는 “원본에서 아래 절차로 생성”이라고 명시 (또는 260204에서 원본→피처 스크립트로 통일). | `data_source_and_original_data.md` |
| 3 | **클러스터 출처 통일**: success_rate_by_cluster·ablation에서 쓰는 cluster가 260121인지 260204 K-Shape K6인지 명확히. 논문에서는 “예측·성공률 모두 260204 K-Shape K6”로 통일해 서술하는 것을 권장. | run_04는 data_features_clean의 cluster 사용 → CSV에 260121이 들어가 있으면 260204 K6으로 덮어쓰는 단계 필요할 수 있음 |
| 4 | **표·그림 번호**: 클러스터 비교표, 예측 결과표, ablation표, 성공률 그림 등에 논문 표/그림 번호 부여. | `thesis_results_summary.md` |
| 5 | **실험 재현 순서** 한 문단으로 정리 (원본 → 피처 → 클러스터 → 예측 스크립트 순). | 아래 4.2 참고 |

### 3.2 있으면 좋은 것 (실험·코드)

| 번호 | 할 일 | 비고 |
|------|--------|------|
| 6 | **260204 run_04의 cluster를 K-Shape K6으로 통일**: 지금 data_features_clean에 들어 있는 cluster가 260121이면, run_04 전에 260204 store_cluster_labels_K6.parquet을 merge해 “성공률·ablation은 모두 K-Shape K6 기준”으로 맞추기. | 선택이지만 논문 일관성에 유리 |
| 7 | **예측 한 표로 정리**: 260211 (30주 8:2)와 260204 ablation(전체 기간 success)이 서로 다른 타깃·데이터임을 논문에 명시. “초기 30주만으로의 예측(260211)” vs “전체 기간 성공 여부 예측(260204)” 역할 구분. | 문단만 추가해도 됨 |
| 8 | **원본→피처 생성**을 260204(또는 공통) 스크립트 하나로 두고, CSV는 그 출력으로 문서화. | 재현성 강화용 |

### 3.3 추가로 “분석·실험”이 꼭 필요한가?

- **새로운 분석/실험**은 필수는 아님.  
  이미 **분석(피처·변곡점·OLS) → 분류(클러스터·코드) → 예측(30주 예측, ablation)** 흐름과 핵심 결과가 있음.
- 다만 다음은 **정리만** 하면 됨:
  - 두 “예측”의 역할 구분 (260211 vs 260204)
  - 클러스터 정의 일원화 (260204 K-Shape K6)
  - 원본 데이터와 피처 생성 과정 명시

---

## 4. 실행 순서 정리 (재현성)

### 4.1 260204 (분석·분류·성공률·ablation)

1. 원본 및 피처 CSV 준비: `store_features_for_analysis.csv` (또는 원본→피처 스크립트 실행).
2. `run_01_prepare_features` → `outputs/data_features_clean.parquet`.
3. (선택) cluster를 K-Shape K6으로 통일하려면, 여기서 `store_cluster_labels_K6.parquet`을 merge해 cluster 컬럼 덮어쓰기.
4. `run_02_cluster_fix` → `store_cluster_labels_K4~K8.parquet`, `cluster_stability_summary.csv`, `cluster_means_K*.png`.
5. `run_03_regression_ols` → `ols_growth_rate.csv`.
6. `run_04_storyline_ablation` → `success_rate_by_cluster.csv`, `ablation_results.csv`, `ablation_f1.png`.

방법 비교는 이미 수행됨: `run_00_compare_methods_no_dtw` → `compare_methods_no_dtw.csv`.

### 4.2 260211 (예측: 첫 30주 → 성장/하락)

1. `build_30w_features_and_labels` → `outputs/tables/features_30w_and_labels.parquet`.
2. `run_prediction_80_20` (클러스터는 `260204/.../store_cluster_labels_K6.parquet` 사용) → `prediction_80_20_results.csv`, `prediction_80_20_M0_vs_M1.png`.

### 4.3 260121·260204_gem (참고)

- 260121: 클러스터·코드 분류 (이미 결과 있음).
- 260204_gem: 변곡점 U/D, 최종 코드 (필요 시 인용).

---

## 5. 한 줄 요약

- **연구 흐름**: 원본 → **분석**(피처·변곡점·OLS) → **분류**(클러스터·코드) → **예측**(30주 성장/하락, 전체 기간 성공 ablation).
- **더 “해야 할 것”**: 새 대규모 실험보다는 **문서화·통일** (방법론, 원본 명시, 클러스터 출처 통일, 표·그림 번호, 실행 순서). 필요 시 run_04에서 사용하는 cluster를 260204 K-Shape K6으로 통일하고, 두 예측(260211 vs 260204)의 역할을 논문에 한 문단씩 명시하면 됨.
