# 260211 — 첫 30주 기반 성장/하락 예측

- **입력**: 매장당 **첫 30주** 매출만 사용 (한 매장 데이터가 들어왔을 때와 동일한 조건).
- **타깃**: 30주 이후 구간 매출의 기울기 ≥ 0 → 성장(1), < 0 → 하락(0).
- **분할**: 매장 기준 **8:2** (훈련 80%, 테스트 20%).

## 설계 요약

- **80% (훈련)**  
  - 각 매장의 **첫 30주**에서 피처(평균·표준편차·기울기 등) 계산.  
  - 라벨은 **전체 기간**(31주~끝) 매출로 계산한 성장/하락.  
  - 이 80% 매장으로만 모델 학습.

- **20% (테스트)**  
  - 각 매장의 **첫 30주**만 입력으로 사용해 성장/하락 예측.  
  - 실제 라벨과 비교해 정확도·F1 등 산출.

## 실행 순서

1. **피처·라벨 생성** (최소 50주 이상 데이터 있는 매장만 사용)
   ```bash
   cd 260211
   python scripts/build_30w_features_and_labels.py
   ```
   - 출력: `outputs/tables/features_30w_and_labels.parquet`

2. **8:2 학습·예측·평가 (예측률 개선: 메타·클러스터·balanced)**
   ```bash
   python scripts/run_prediction_80_20.py
   ```
   - **M0**: 첫 30주 피처만 + **class_weight=balanced** (하락 소수 클래스 반영).
   - **M0_meta**: M0 + 지역·업종(sigungu, dong, depth_1~3) 더미. 메타는 `build_30w_features_and_labels.py`에서 `meta_processed.csv` 병합 시 자동 포함.
   - **M1**: M0 + (첫 30주로 예측한) 클러스터 더미.
   - **M1_meta**: M1 + 메타 더미.
   - 클러스터 라벨: `260204/.../store_cluster_labels_K6.parquet` 또는 `260121/.../cluster_labels.csv` 있으면 자동 병합.
   - 출력: `prediction_80_20_results.csv` (spec별 accuracy, f1), `prediction_80_20_M0_vs_M1.png`

## 설정

- `configs/prediction_30w.yaml`: `first_n_weeks`(30), `min_total_weeks`(50), `train_ratio`(0.8) 등.

---

## GAF PoC — 이미지 기반 클러스터링 (Proof of Concept)

142주 매출 시계열을 **Gramian Angular Field (GAF)** 이미지로 변환한 뒤, 샘플 시각화와 (선택) **CNN Autoencoder + K-Means** 클러스터링을 수행합니다.  
데이터 명세서 기반 업그레이드 전략(Imaging + Predictability-first)의 1분 판단용 PoC입니다.

### 실행

```bash
cd 260211
python scripts/run_gaf_poc.py
```

- **입력**: `../original_data/weekly_processed.parquet` (주별 `sales_card`, `day_after1`, `public_id`)
- **처리**: 142주 피벗 → 행별 [-1,1] 정규화 → GAF 변환 (142×142 픽셀)
- **출력**  
  - `outputs/figures/gaf_sample_1_*.png` ~ `gaf_sample_10_*.png`: 매장별 GAF 이미지  
  - `outputs/figures/gaf_sample_10_grid.png`: 10개 그리드  
  - (선택) `outputs/tables/gaf_cnn_cluster_labels.parquet`: CNN latent 기반 클러스터 라벨  
  - `outputs/logs/run_gaf_poc.log`: 실행 로그

### 설정

- `configs/gaf_poc.yaml`  
  - `gaf.n_weeks`: 142  
  - `gaf.method`: `summation`(GASF, 추세/형상) 또는 `difference`(GADF, 변동)  
  - `poc.max_stores`: PoC에 사용할 최대 매장 수 (메모리/속도). `null`이면 전부(약 5.5만)  
  - `poc.run_cnn_clustering`: `true`일 때 CNN Autoencoder + K-Means 수행 (torch 필요)  
  - `poc.n_sample_images`: 시각화용 샘플 개수 (기본 10)

### 의존성

- 기본: `numpy`, `pandas`, `matplotlib`, `scipy` (리사이즈)
- YAML 설정 사용 시: `pyyaml`
- CNN 클러스터링 사용 시: `torch`
- GAF는 **numpy만으로 구현**되어 있어 별도 `pyts` 설치 불필요.
