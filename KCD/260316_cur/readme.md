# 소상공인 매출 시계열 생애주기 분석

**석사 학위 논문**: 소상공인 매출 시계열 패턴의 유형화와 도시 인구 변화 예측

---

## 1. 파이프라인 구조

```
260316_cur/
├── main.py                          ← 전체 파이프라인 실행
├── requirements.txt
├── readme.md
├── src/
│   ├── config.py                    ← 경로·하이퍼파라미터·레이블
│   ├── step01_preprocessing.py      ← 전처리 + STL 분해
│   ├── step02_feature_extraction.py ← 업장별 피처 추출
│   ├── step03_clustering.py         ← DTW/K-Shape/KMeans 클러스터링
│   ├── step04_label_assignment.py   ← 6-class 레이블 할당
│   ├── step05_factor_analysis.py    ← MNLogit + GBM-SHAP + PSM
│   ├── step06_prediction.py         ← 30주 조기 예측 + Ablation
│   └── step07_visualization.py      ← 논문용 Figure 일괄 생성
└── outputs/
    ├── figures/                     ← fig01~fig08.png, SHAP plots
    └── tables/                      ← CSV, TXT 산출물
```

---

## 2. 실행 방법

```bash
cd 260316_cur
pip install -r requirements.txt
python main.py            # 전체 실행
python main.py --step 3   # 특정 단계만
```

데이터 위치: `../original_data/weekly.parquet`, `../original_data/meta.csv`
(weekly_reduced.parquet 자동 fallback)

---

## 3. 방법론 상세

### Step 01 — 전처리
| 항목 | 방법 |
|------|------|
| 거시변수 통제 | 주별 전체 매출 합 대비 개별 비율 (sales_ratio) |
| Time alignment | open_month → weeks_since_open 변환 |
| 희소성(Sparsity) | 선형 보간 + forward/backward fill |
| Seasonal Decomposition | **STL** (period=13주, robust), 단기 관측은 7주 rolling mean |
| 정규화 | 업장별 MinMax [0, 1] |

**기존 대비 개선**: STL 분해를 통해 trend·seasonal·residual을 분리하여
노이즈 없는 추세 기반 기울기를 산출. 계절성 강도(seasonal_strength)를 
피처로 활용하여 '계절에 민감한 업종'과 '안정적 업종'을 구분.

### Step 02 — 피처 추출
- **추세 피처**: 전반/후반/전체/tail 기울기 (MinMax 기반), R²
- **STL 유래**: trend_slope, seasonal_strength, noise_ratio
- **변동성**: CV (capped at 2.0), MDD (Maximum Drawdown)
- **고객**: 신규고객비율 (customer_new / customer)
- **영업**: 배달비율(log1p), 오전비율, 주말비율

### Step 03 — 클러스터링
| 방법 | 거리 | 장점 |
|------|------|------|
| KMeans-Euclidean | L2 | 빠르고 안정적 (baseline) |
| **DTW-KMeans** | Dynamic Time Warping | 시간 왜곡에 강건 |
| **K-Shape** | Cross-correlation | 형태 기반, 스케일 불변 |

**검증 지표**: Silhouette Score, Davies-Bouldin Index, Calinski-Harabasz Index
**Optimal-K**: 3~9 범위에서 Silhouette 극대화

### Step 04 — 레이블 할당 (6-class, data-driven)
```
slope_early × slope_late × mdd(median) → 6개 클래스

  DD_Z: 전반↓ 후반↓ 고손실  — 전형적 쇠퇴
  DD_Y: 전반↓ 후반↓ 저손실  — 저성과 안정
  DU  : 전반↓ 후반↑         — 반등 (턴어라운드)
  UU  : 전반↑ 후반↑         — 지속 성장
  UD_Z: 전반↑ 후반↓ 고손실  — 성장 후 급락
  UD_Y: 전반↑ 후반↓ 저손실  — 성장 후 완만 하락
```

**교차검증**: 궤적 클러스터와의 Adjusted Mutual Information (AMI)

### Step 05 — 요인 분석
1. **Multinomial Logit** (statsmodels): 전통 계량경제 모델.
   기준=UU, 설명변수: 기울기, CV, MDD, 신규고객비율, 배달비율, 업종 더미.
2. **GradientBoosting + SHAP**: 비선형 관계 포착 + TreeExplainer 해석.
   논문 Figure로 SHAP summary/beeswarm plot 자동 생성.
3. **Propensity Score Matching**: 배달앱 채택(delivery_link)의 인과효과 추정.
   처리군/통제군 매칭 후 레이블 분포 비교.

### Step 06 — 조기 예측 (오픈 후 30주)
- **Ablation Study**: Base → +Shape → +Customer 피처셋 단계적 확장
- **모델**: RF, GBM, LightGBM (class_weight=balanced)
- **평가**: F1-weighted, Accuracy, Precision, Recall, 혼동행렬
- **해석**: SHAP TreeExplainer로 예측 기여 변수 시각화

### Step 07 — 시각화
| Figure | 내용 |
|--------|------|
| fig01 | 레이블별 평균 궤적 (spaghetti) |
| fig02 | 레이블 분포 (bar) |
| fig03 | 전반/후반 기울기 사분면 |
| fig04 | K-Means 클러스터 중심선 |
| fig05 | Optimal-K 선택 (Silhouette) |
| fig06 | Ablation Study 결과 |
| fig07 | STL 분해 예시 |
| fig08 | 업종별 레이블 분포 (heatmap) |
| shap_* | SHAP summary/beeswarm plots |

---

## 4. 기존 파이프라인 대비 개선점

| 항목 | 기존 (v5 등) | 본 파이프라인 |
|------|-------------|--------------|
| Seasonal 처리 | 없음 | STL 분해 (trend/seasonal/residual 분리) |
| 클러스터링 | KMeans-Euclidean만 | DTW-KMeans + K-Shape + 3종 비교 |
| 클러스터 검증 | 없음 | Silhouette, DB, CH + Optimal-K 탐색 |
| 요인 분석 | MNLogit만 | + GBM-SHAP (비선형) + PSM (인과추론) |
| 예측 해석 | 없음 | SHAP TreeExplainer |
| 예측 평가 | F1만 | + AUC, PR-AUC, Precision, Recall, CM |
| 불균형 처리 | 미적용 | class_weight="balanced" |
| 시각화 | 수동 | 8종 Figure 자동 생성 |

---

## 5. 산출물

### Tables (outputs/tables/)
- `store_features.csv` — 업장별 피처
- `store_features_labeled.csv` — + 레이블
- `cluster_evaluation.csv` — K별 평가 지표
- `cluster_method_comparison.csv` — DTW/K-Shape/KMeans 비교
- `label_cluster_crosstab.csv` — 레이블 ↔ 클러스터 교차표
- `label_by_category.csv` — 업종별 분포
- `label_feature_means.csv` — 클래스별 피처 평균
- `mnlogit_summary.txt` — Multinomial Logit 결과
- `mnlogit_coefficients.csv` — 계수표
- `gbm_feature_importance.csv` — GBM 중요도
- `psm_delivery_effect.csv` — 배달앱 효과 (PSM)
- `ablation_early_prediction.csv` — Ablation 결과
- `prediction_full_evaluation.csv` — 예측 평가
- `classification_report.txt` — 분류 보고서
- `confusion_matrix.csv` — 혼동행렬

### Figures (outputs/figures/)
- `fig01_trajectories.png` ~ `fig08_category_heatmap.png`
- `shap_summary_bar.png`, `shap_beeswarm_class0.png`
- `shap_early_prediction.png`

---

## 6. 논문 목차 매핑

| 논문 장 | 파이프라인 단계 |
|---------|---------------|
| 3장 방법론 | Step 01-02 (전처리, 피처 설계) |
| 4장 유형화 | Step 03-04 (클러스터링, 레이블) |
| 5장 요인 분석 | Step 05 (MNLogit, SHAP, PSM) |
| 6장 예측 모델 | Step 06 (30주 예측, Ablation) |
| 전 장 | Step 07 (시각화) |
