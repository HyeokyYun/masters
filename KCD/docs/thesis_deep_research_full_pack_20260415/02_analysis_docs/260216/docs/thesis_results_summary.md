# 석사학위논문 — 지금까지 결과 종합 및 필요 결과 정리

## 1. 프로젝트 구조 요약

| 폴더 | 역할 |
|------|------|
| **260121** | 시계열 클러스터링(TimeSeriesKMeans euclidean, 9클러스터) 및 6클러스터 라벨, 아웃라이어 제거, 지역/업종 분포, 코드 분류(XGBoost 등) |
| **260204** | 주별 parquet 기반 클러스터링 비교(euclidean vs kshape), K-Shape 안정성, 회귀/예측/ablation, 성공률·클러스터별 통계 |
| **260204_gem** | 변곡점(P1/P2) 추출, U/D 라벨, 260121 클러스터와 매핑한 X/Y/Z·최종 코드 |
| **260211** | 첫 30주 기반 피처·라벨 생성, 8:2 예측(M0/M1 등), GAF PoC |
| **260216** | 미팅 정리(260213), 논문 결과 정리, 추가 작업 산출물 저장 |

---

## 2. 논문에 쓸 수 있는 결과 파일 (필요 결과 목록)

### 2.1 클러스터링·방법 비교

| 결과 | 경로 | 용도 |
|------|------|------|
| 클러스터 라벨 (최종 사용) | `260204/outputs/tables/store_cluster_labels_K6.parquet` | 예측(M1) 및 논문 전반의 클러스터 정의 |
| 클러스터 centroid 시각화 | `260204/outputs/figures/cluster_means_K4.png` ~ `K8.png` | K-Shape 클러스터 평균 곡선 (K=6 권장) |
| 방법 비교 (euclidean vs kshape) | `260204/outputs/tables/compare_methods_no_dtw.csv` | 안정성(ARI/NMI), M1 F1, K-Shape 한계 근거 |
| 클러스터 안정성 요약 | `260204/outputs/tables/cluster_stability_summary.csv` | K=4~8 seed/bootstrap ARI, K 선정 근거 |

### 2.2 예측 (첫 30주 → 성장/하락)

| 결과 | 경로 | 용도 |
|------|------|------|
| 8:2 예측 결과 (M0/M1 등) | `260211/outputs/tables/prediction_80_20_results.csv` | Accuracy, F1 by spec (M0, M1, …) |
| 30주 피처·라벨 | `260211/outputs/tables/features_30w_and_labels.parquet` | 재실험·표 작성용 (필요 시) |

### 2.3 회귀·스토리라인·성공률

| 결과 | 경로 | 용도 |
|------|------|------|
| Ablation (모델/스펙별 F1) | `260204/outputs/tables/ablation_results.csv` | M0~M3, LogisticRegression vs XGBoost |
| 클러스터별 성공률 | `260204/outputs/tables/success_rate_by_cluster.csv` | 클러스터별 성공률 분포 |
| OLS 성장률 등 | `260204/outputs/tables/ols_growth_rate.csv` | 회귀 분석 결과 (사용 시) |

### 2.4 변곡점·최종 코드 (260204_gem)

| 결과 | 경로 | 용도 |
|------|------|------|
| 변곡점 P1/P2 라벨 | `260204_gem/outputs/tables/inflection_p1p2_labels.csv` | U/D 구간 |
| 최종 코드 (260121 아웃라이어 제거) | `260204_gem/outputs/tables/final_code_by_store_260121_outlier_removal.csv` | U/D + X/Y/Z 결합 코드 |

### 2.5 260121

| 결과 | 경로 | 용도 |
|------|------|------|
| 6클러스터 라벨 | `260121/result_csv/6_cluster_labels.csv`, `cluster_labels.csv` | 대안 클러스터 소스 |
| 클러스터별 지역/업종 분포 | `260121/result_csv/cluster_*_distribution.csv` | 서술·해석 |
| 코드 분류 성능 | `260121/result_csv/code_classification/model_performance_code.csv` 등 | 분류 실험 결과 |

---

## 3. 표/그림으로 정리할 핵심 수치 (요약)

- **클러스터 방법 비교**  
  - Euclidean K=6: seed ARI ≈ 0.856, bootstrap ARI ≈ 0.834.  
  - K-Shape K=6: seed ARI ≈ 0.320, bootstrap ARI ≈ 0.373.  
  - M1 F1: 두 방법 동일 ≈ 0.445.

- **예측 (260211)**  
  - M0: Accuracy ≈ 0.623, F1 ≈ 0.758 (LogisticRegression); XGBoost F1 ≈ 0.731.  
  - M1: Accuracy ≈ 0.633, F1 ≈ 0.748 (LR); XGBoost F1 ≈ 0.731.

- **Ablation (260204)**  
  - M1에서 XGBoost F1 ≈ 0.798; M3 ≈ 0.805 (최고).

- **클러스터 안정성**  
  - K=4~8 bootstrap ARI ≈ 0.39~0.42; K=6 기준으로 논의.

---

## 4. 260216에 복사해 둔 결과 (선택)

- `docs/260213_meeting_clustering_methodology.md` — 260213 미팅 내용 반영 (경제 TS clustering, kshape 한계, 선정 이유).
- 추가로 필요한 테이블/그림은 `260216/outputs/tables`, `260216/outputs/figures`에 복사해 두면 논문 작성 시 한곳에서 참조 가능.
