<!--
원본: 260516_overleaf_en/chapters/ch5_prediction.tex
번역일자: 2026-05-22
-->

# Chapter 5 — Prediction Models (국문 번역)

본 장은 예측 스토리를 하나의 흐름으로 전개한다. 서로 관련되나 구별되는 두 라벨 정의(§3.3) — 메인 삼항 G/S/D 상태와 보완적 이항 큰 폭 성장 타깃 — 를 쓰며, 둘의 절대 수치는 직접 비교 불가다. §§5.1–5.2 는 매출 곡선 형상(inflection-point + UDX) feature가 가장 강력한 큰 폭 성장 식별을, §5.3 이후는 cluster + change-point hybrid 와 Random Forest vs LightGBM 비교를 통한 시즌 정렬 삼항 G/S/D 예측을 보고한다.

**Figure 5.9 (Improvement ladder)** 는 본 논문 전체 모델 비교의 단일 시각화이다: G/S/D baseline Random Forest (macro-$F_1 \approx 0.50$), 세 비교 branch (representation hybrid, cost-sensitive weighting, external 모델 benchmarking), 총 **17 모델 변형**. LightGBM 계열 3종만 Random Forest baseline 위에 있고, 14개 비-LightGBM 비교 변형(2 foundation, 7 neural forecasting, 3 SMB-attention, 2 cost-sensitive)은 모두 아래.

---

## §5.1 큰 폭 성장 식별을 위한 Baseline

**Input (`base_only`)**: 17 운영 변수 — 신규 고객 비율, 매출 변동계수, 영업 개월 수, 사업 밀도, 평방미터, 평균 매출, 추세 슬로프, 총 관찰 주, 주말 매출 비율, 평균 고객 수, max/min 매출, max/min 비율, 동·시군구 점포 수와 평균 매출 — + `sigungu`·`depth_2` 더미. **Models**: RF, XGBoost, LightGBM. **Target**: `growth_type` ∈ {0,1}. **Metric**: binary $F_1$ (양성 = 큰 폭 성장). **Split**: stratified 80/20, single seed=42.

**Performance**: RF binary $F_1$ = **0.539** (accuracy 0.896), XGBoost = **0.681** (accuracy 0.909). accuracy ≥ 0.9 와 $F_1$ 사이의 간극이 클래스 불균형(양성 큰 폭 성장 클래스가 얇음) 을 반영하며 macro/binary-$F_1$ 채택의 정량 근거가 된다.

baseline 은 매출 시계열의 *shape* 신호(변곡점 위치, 세그먼트 슬로프, Up/Down 패턴)를 받지 않는다. 다음 절은 이 shape 신호를 representation 에 결합했을 때 $F_1$ 의 변화를 본다.

---

## §5.2 큰 폭 성장 식별을 위한 Inflection-Point + UDX Representation

### 설계 원리

**변곡점 검출.** 각 점포의 주간 매출 시계열에 대해 두 개의 breakpoint (P1, P2) 를 RSS 최소화로 선택하는 *piecewise linear regression* 을 적용한다. breakpoint 신호가 약하면(단조 시계열 등) week $\lfloor n/2 \rfloor$ 의 midpoint fallback 사용. 점포별 네 양:

- `slope_P1`: 첫 세그먼트(개업 → P1) 슬로프
- `slope_P2`: 두 번째 세그먼트(P1 → P2 또는 P1 → 끝) 슬로프
- `inflection_week`: P1의 week index
- `final_code` (UDX): P1·P2 두 슬로프의 Up/Down 두 글자 + 점포의 매출 궤적 cluster에서 매핑한 X/Y/Z 패턴 한 글자(§3.5; X = 성장형 클러스터, Y = 안정, Z = 쇠퇴형) — 예: DUY, DDZ. 데이터에 12종 등장

**Figure 5.A** — 샘플 점포의 검출된 P1과 두 세그먼트 슬로프.

결합 representation은 17 변수 + `sigungu`/`depth_2` 더미에 다음을 추가:

**Table 5.1 — Components of high-growth combined representation (`base_udx_inflection`)**

| Component | Description |
|---|---|
| 17 변수 + `sigungu, depth_2` 더미 | baseline 과 공통 |
| `cluster` | 매출 궤적 cluster 라벨 ($K=6$) |
| `slope_P1`, `slope_P2` | P1, P2 변곡점 세그먼트 슬로프 |
| `inflection_week` | 첫 변곡점 week index |
| `final_code` (UDX) | P1/P2 Up/Down 부호 + 매출 궤적 cluster 패턴(X/Y/Z) 더미 (DUY, DDZ 등) |

### 성능

결합 representation은 binary $F_1$을 **RF 0.642 / XGBoost 0.818** 로 향상시킴 — $\Delta F_1$ +0.103 (RF), +0.137 (XGBoost).

**Table 5.2 — High-growth ablation**

| Model | spec | Accuracy | Binary $F_1$ | $\Delta F_1$ |
|---|---|---|---|---|
| Random Forest | `base_only` | 0.896 | 0.539 | --- |
| Random Forest | `base_udx_inflection` | 0.913 | **0.642** | **+0.103** |
| XGBoost | `base_only` | 0.909 | 0.681 | --- |
| XGBoost | `base_udx_inflection` | 0.945 | **0.818** | **+0.137** |

세 관찰:

1. **shape 신호의 강한 explanatory power.** 매출 곡선 *shape* 의 압축 representation(변곡점, 세그먼트 슬로프, Up/Down 패턴)이 17-변수 baseline 의 binary $F_1$ 을 크게 향상(RF +0.103, XGB +0.137).
2. **UDX 코드의 post-hoc summary 성질.** `final_code` (DUY, DDZ 등 12 코드 중 하나)는 본질적으로 매출 패턴 *shape* 의 사후 요약이므로 — 특히 X/Y/Z 글자가 전체 시계열을 본 매출 궤적 cluster에서 오므로, 큰 폭 성장 패턴(UU 등)과 강하게 연관됨. 따라서 이 $\Delta F_1$ 은 *forward predictive power* 의 직접 향상이 아닌 **explanatory ablation** 으로 해석되어야 함 — 매출 곡선 shape 이 장기 매출 성장과 강하게 연결된다는 의미. caveat 은 §\ref{sec:limitations} 에서 재논의.
3. **모델 비교.** 동일 representation 에서 XGBoost (0.818) 가 RF (0.642) 를 상회. 단 단일 80/20 holdout, single seed 평가는 모델 비교 주장을 통계적으로 검증하지 않음 — 그 검증은 G/S/D 14-패널 paired 비교(§\ref{sec:rf_vs_lgbm})로 위임.

**SHAP feature contributions.** XGBoost `base_udx_inflection` 의 SHAP summary (Figure 5.8) 에서 양성 클래스 예측 기여 최상위는 특정 `final_code` (UDX) 더미와 `cv_sales_card`, `slope_P1`, `new_customer_ratio` — §\ref{sec:significant_vars} 회귀 결과 (신규 고객 비율·매출 변동성 의 강한 효과) 와 정합.

---

## §5.3 시즌 정렬 삼항 G/S/D 예측 (14 패널)

### 모델 설정

- **Input (A_baseline)**: 43차원 representation — 매출 시계열 통계량 + 점포 메타데이터 + 고객 구성 변수.
- **Variants**: B (+`cluster`, 49 features), C (+change-point, 50 features), D (full hybrid, 56 features).
- **Target**: 1년 후 3개월 윈도우의 G/S/D 삼항.
- **Metric**: macro-$F_1$.
- **Split**: 14 시즌 정렬 패널 위의 store-grouped 5-fold CV.

### 성능 — 패널별 분포와 paired 비교

14 패널에 걸쳐 A_baseline 과 D_full hybrid 의 macro-$F_1$ 이 **약 0.50 주변의 좁은 띠** 에 cluster.

A vs D paired 비교:

- 14 패널 평균 $\Delta F_1$ (D − A): **+0.0017**
- paired $t$-test $p < 0.05$ 패널: 1/14 (`sy2021_sm01_w7m_off1`, $\Delta = +0.0054$, $p = 0.0073$)
- Bonferroni 보정 후 ($\alpha/14 = 0.00357$) 유의 패널: **0/14**

→ G/S/D baseline (매출 통계 + 메타데이터 + 고객 구성) 이 이미 macro-$F_1 \approx 0.50$ 을 달성하며, cluster + change-point hybrid 추가는 작은 marginal gain — 특정 시즌/윈도우에서만 *조건부* 유의. *단기 시즌 정렬* 라벨링 하에서 hybrid representation 의 증분 신호가 baseline 에 이미 거의 흡수됨을 시사.

### 두 타깃의 비교 불가

큰 폭 성장 타깃의 $\Delta F_1 \approx +0.10 \sim +0.14$ (이항, 단일 holdout) 와 G/S/D 상태의 $\Delta F_1 \approx +0.0017$ (macro, 14-패널 평균) 의 차이는 representation 효력 차이가 아니라 *label 정의·평가 지표·split 프로토콜의 차이*. 본 논문은 타깃 내 향상만 주장.

---

## §5.4 Model Selection: Random Forest vs LightGBM

이 절 및 이후 비교 절들(§5.7·§5.8까지)은 시즌 정렬 삼항 G/S/D (store-grouped 5-fold, macro-$F_1$)를 보고하며 큰 폭 성장 타깃과 직접 비교 불가. **패널 세트는 실험마다 다르다**: A/B/C/D 하이브리드 평가는 14개 main panel, RF vs LightGBM·외부모델·cost-sensitive 비교는 6-panel subset.

### 동일 representation 비교

G/S/D baseline 은 Random Forest. 동일 split·동일 representation 위에서 LightGBM 만이 일관된 우위를 보임: 평균 macro-$F_1$ 0.5048 vs RF 0.4973 (평균 $\Delta F_1 = +0.0075$, 6 패널 중 5승, 2에서 paired $t$-test $p<0.05$; 전체 표는 §5.7).

### 구조적 해석

LightGBM이 본 데이터의 무엇을 구조적으로 더 잘 잡는지, 본 데이터 feature가 그런 모델이 잘 동작하는 데이터와 어떤 측면에서 유사한지를 다음 세 가설로 해석한다:

세 가설:

1. **Leaf-wise growth.** LightGBM 의 leaf-wise split 은 *신호가 소수 유의 feature 에 집중* 될 때 더 깊은 split 을 우선. 본 representation은 영업기간·신규 고객 비율 같은 소수의 강한 신호를 가지므로 leaf-wise growth 가 그 신호를 효율적으로 소진하는 데 유리.
2. **Histogram-based splitting.** 주간 매출 통계 분포는 heavy tail 과 점포 간 수준 차이를 가짐. LightGBM 의 histogram-based split 이 이런 분위수 구조에 적응.
3. **고-카디널리티 구조의 효율적 처리.** 업종·동 같은 고-카디널리티 입력(인코딩된 dummy로 투입)에 대해 LightGBM 이 희소 구조를 효율적으로 분할하며, RF 의 다수결 split 보다 적은 noise 로 동작.

이 구조적 속성은 본 데이터의 *feature 이질성 + 강한 소수 클래스 신호 + 큰 categorical cardinality* 와 정합 — LightGBM 이 *일반적으로* 가 아니라 *이 데이터에서* 더 낫다는 해석을 정당화.

### 최종 선택

메인 G/S/D 결과(RQ3) 는 **D_full hybrid representation + LightGBM** 조합으로 보고. Random Forest 는 (i) A_baseline 모델 옵션, (ii) Chapter 6 paired-비교 baseline 으로 잔존.

---

## §5.5 영업기간 사분위 코호트 분석

영업기간 사분위 코호트 수준에서 *영업기간* (ch4 유의 변수)이 G/S/D 결과와 어떻게 상호작용하는지 정량화.

### Cohort × G/S/D Crosstab

영업기간 사분위 (중위 Q1≈7개월, Q2≈23, Q3≈49, Q4≈113), 패널 `sy2021_sm01_w3m_off1`에서 Growth 비율: Q1 0.543 → Q2 0.572 → Q3 0.572 → Q4 0.579 — *영업기간에 따른 Growth 비율 단조 증가*. 동시에 Q1–Q2 단기 코호트에서 Decline 비중이 두꺼움 (진입 직후 학습·적응 단계의 변동성 가설).

### 코호트별 신규 고객 → Growth 로짓

nc_slope 계수가 모든 코호트에서 양 (Q1 +2.026, Q2 +1.255, Q3 +1.286, Q4 +1.649). 효과 크기는 Q1·Q4 양끝 코호트에서 최대. *신규 고객 유입이 성장의 일관된 신호임을 재확인*.

### 코호트별 LightGBM vs Random Forest

영업기간 사분위 코호트별 LGBM over RF $\Delta F_1$ (6 패널 평균):

**Table 5.3 — Per-cohort LightGBM vs RF**

| Cohort | Mean $n$ | RF mean $F_1$ | LGBM mean $F_1$ | $\Delta F_1$ |
|---|---|---|---|---|
| Q1_short | 9,224 | 0.475 | 0.477 | +0.002 |
| Q2 | 8,910 | 0.492 | 0.490 | −0.002 |
| Q3 | 8,895 | 0.497 | 0.509 | +0.013 |
| Q4_long | 8,872 | 0.526 | 0.545 | +0.019 |

장기 코호트 (Q3, Q4) 에서 LightGBM 마진이 더 큼. 단기 코호트에서는 진입 직후 noise 가 커서 모델 차이가 가려지고, 장기 코호트(누적 신호 충분) 에서 leaf-wise boosting 의 우위가 드러난다는 해석.

### 함의

코호트 분석은 (i) §\ref{sec:significant_vars} 의 유의 변수가 *모든 코호트에서 일관* 되는지, (ii) 어느 코호트에서 효과 크기가 가장 두드러지는지를 별도로 보여줌. §5.2 hybrid representation 이 단순 평균보다 추가 마진을 내는 *이유* 의 해석적 근거를 제공하며, §\ref{sec:cohort_lgbm} 의 LightGBM 우위 패턴(장기 코호트 중심) 은 §\ref{sec:rf_vs_lgbm} 구조적 해석을 코호트 차원에서 재확인.

---

## §5.6 패널 내부(Panel-Internal) Cluster 분해

점포를 6개 *패널 내부(panel-internal)* cluster로 분해하고 cluster 별 G/S/D 결과와 feature importance 를 보고. 이 cluster들은 각 시즌 정렬 패널 안에서 feature window의 정규화 매출 시퀀스만으로 적합되며 — G/S/D 모델이 쓰는 forward-valid `cluster` feature와 동일(§5.3) — Figure 3.2의 full-span 기술용(descriptive) 궤적 클러스터와는 다른 객체다. 따라서 여기 cluster 크기 합은 단일 패널의 점포 수(33,998)이며 Figure 3.2의 full-span 전체 점포 수가 아니다.

### Cluster × G/S/D 분포

**Table 5.4 — 6개 패널 내부 clusters (panel `sy2021_sm01_w3m_off1`)**

| Cluster | $n$ | Growth | Stable | Decline | macro-$F_1$ |
|---|---|---|---|---|---|
| 0 | 6,603 | 0.513 | 0.429 | 0.058 | 0.456 |
| 1 | 5,561 | 0.699 | 0.235 | 0.066 | 0.429 |
| 2 | 9,891 | 0.691 | 0.276 | 0.033 | 0.406 |
| **3 (fragile)** | 744 | 0.267 | 0.374 | **0.359** | **0.337** |
| **4 (stable)** | 10,223 | 0.426 | **0.462** | 0.112 | **0.464** |
| 5 | 976 | 0.609 | 0.273 | 0.119 | 0.383 |

두 cluster가 본 논문의 핵심 분리점:

- **Stable-dominant cluster (4).** Stable 비중 46.2% (가장 두꺼움), 내부 macro-$F_1$ 0.464 (가장 높음). 중수준 매출, 낮은 변동성, 낮은 신규 고객 비율 특성.
- **Fragile cluster (3).** Decline 비중 35.9% 누적, 내부 macro-$F_1$ 0.337 (가장 낮음). $n=744$ 의 작은 cell — 높은 변동성, 낮은 객단가, 정체된 신규 고객 유입 공존. 클러스터는 패널마다 재적합되어 **인덱스는 패널 간 비교 불가**; 재현되는 건 *패턴* — 고-Decline cluster가 매 패널 등장(예: `sy2021_sm05_w3m_off1` 45.2%, `sy2021_sm09_w3m_off1` ~0.60).

### Per-Cluster Feature Importance

LightGBM top-importance feature 는 cluster 별로 다름. 특히 *fragile cluster* 에서 **고객수 변동성·관측 coverage·신규 고객 동태**가 최상위 — §\ref{sec:cohort_lgbm} 신규 고객 신호와 대체로 정합.

### 함의

Cluster 분해는 *전체 평균 macro-$F_1$* 으로 가려지는 *cell 별 rank 차이* 를 드러냄. G/S/D 에서 fragile cluster (Decline 35–45%) 가 명확히 분리되어 *조기 경보(early-warning)* 응용의 1차 표적이 된다; cluster별 모델 마진은 작은 cell 크기(cluster 3, $n=744$) 때문에 신중히 해석해야 한다.

---

## §5.7 14 비-LightGBM 모델 비교

경계 조건 점검으로서, G/S/D *D_full hybrid + LightGBM* 조합을 14 비-LightGBM 비교 모델과 동일 G/S/D 데이터, 동일 라벨, 동일 6-패널 store-grouped split 위에서 비교.

비교 대상은 foundation model, neural forecasting model, SMB-specific attention 변형, cost-sensitive 변형을 포함한다.

### 비교 대상 분류

**Table 5.5 — 14 비-LightGBM 비교 모델 분류**

| Group | Count | Models |
|---|---|---|
| Foundation zero-shot | 2 | Chronos-Bolt, TimesFM |
| Neural forecasting | 7 | TFT, N-BEATS, N-HiTS, PatchTST, DLinear, Informer, Autoformer |
| SMB-specific attention | 3 | (3 attention 변형) |
| Cost-sensitive 변형 | 2 | rf_decline_x2, rf_decline_x3 |

### 결과

14개 비-LightGBM 비교 변형 중 RF baseline을 넘은 것은 없고, LightGBM 계열 3종만 *완만하지만 일관된 우위* 를 보임. 대다수 비-LightGBM 변형은 *성능이 더 낮음*. 아래 결과는 6 패널 평균이다.

**Table 5.6 — $\Delta F_1$ vs RF baseline (6 패널 평균)**

| Group | Model | mean $F_1$ | $\Delta F_1$ | wins / 6 |
|---|---|---|---|---|
| 5D weighting | rf_tabular (reference) | 0.4973 | 0 | 0 |
| 5D weighting | **lgbm_tabular** | **0.5048** | **+0.0075** | **5** |
| 5D weighting | lgbm_shap_weighted | 0.5044 | +0.0071 | 5 |
| 5D weighting | lgbm_decline_x2 | 0.4999 | +0.0026 | 4 |
| 5D weighting | rf_decline_x2 | 0.4628 | −0.0345 | 0 |
| 5D weighting | rf_decline_x3 | 0.4344 | −0.0629 | 0 |
| 5C attention | feature_attn_mlp | 0.4621 | −0.0352 | 0 |
| 5C attention | film_tenure_lstm | 0.4507 | −0.0466 | 0 |
| 5C attention | time_attn_lstm | 0.4048 | −0.0925 | 0 |
| 5B neuralforecast | dlinear | 0.3612 | −0.1387 | 0 |
| 5A foundation | chronos_bolt_small | 0.2893 | −0.2105 | 0 |
| 5B neuralforecast | nhits | 0.2787 | −0.2212 | 0 |
| 5B neuralforecast | tft | 0.2617 | −0.2383 | 0 |
| 5B neuralforecast | nbeats | 0.2535 | −0.2464 | 0 |
| 5B neuralforecast | patchtst | 0.2423 | −0.2576 | 0 |
| 5B neuralforecast | informer | 0.2398 | −0.2601 | 0 |
| 5B neuralforecast | autoformer | 0.2393 | −0.2606 | 0 |
| 5A foundation | timesfm_200m | 0.2295 | −0.2705 | 0 |

요약: macro-$F_1$이 RF *이상* 인 모델은 LightGBM 계열 3종 뿐, 14 비-LightGBM 비교 변형(2 foundation, 7 neural forecasting, 3 SMB-attention, 2 cost-sensitive)은 모두 일관된 음의 마진. lgbm_tabular 의 +0.0075 마진은 6 패널 중 2 에서 paired $t$-test $p < 0.05$ (1 에서 $p < 0.01$).

### 데이터 특성 해석

이는 외부 예측 모델의 결함이 아니라 *데이터 특성 mismatch*. 이 모델들은 일반적으로 (i) 규칙적으로 샘플링된 시계열, (ii) 비교적 동질 단면, (iii) 불연속이 드문 연속적 신호 를 가정. 본 데이터는 (i) 주간, (ii) 점포 이질, (iii) 영업시간·휴무 불연속 빈번 — 위 가정과 어긋남.

이 해석의 의의는 §6.2 *robustness* 차원에서 반복 강조.

---

## §5.8 Cost-Sensitive Learning 보조 실험

클래스 불균형 보정의 한 갈래로 *cost-sensitive learning* 결과를 보고한다.

### 비교 대상

- **rf_decline_x2 / rf_decline_x3.** Decline 클래스 손실 가중 2×, 3× 의 RF 변형.
- **lgbm_decline_x2.** Decline 가중 2× 의 LightGBM.
- **rf_shap_weighted.** SHAP 값 기반 sample 가중치를 동적 할당한 RF.

### 결과 — 음의 효과

핵심 결과: *cost-sensitive 가중이 본 데이터에서 macro-$F_1$을 오히려 낮춤* (6 패널 평균).

- rf_tabular : 0.4973 (reference)
- rf_shap_weighted : 0.4969 [−0.0004]
- **rf_decline_x2** : 0.4628 [−0.0345]
- **rf_decline_x3** : 0.4344 [−0.0629]
- lgbm_tabular : 0.5048 (reference)
- lgbm_shap_weighted : 0.5044 [−0.0004]
- lgbm_decline_x2 : 0.4999 [−0.0048]

rf_decline_x2/x3 의 음의 효과는 6 패널 모두에서 paired $t$-test $p < 0.05$ (x2: 5/6 $p<0.01$, x3: 5/6 $p<0.01$). *Decline 가중이 강해질수록 macro-$F_1$ 이 단조 감소*. LGBM 계열의 SHAP·decline_x2 변형은 변화 미미.

#### 확장 manual reweighting 실험

특정 가중 구현의 artifact가 아님을 확인하기 위해, 6 시즌 정렬 패널에서 6개 *manual* 변형(scalar class weight·sample-duplication weight, Decline 클래스에 $w \in \{2,3,5\}$)을 추가 테스트했다. 결과는 일관된 null — 모든 변형이 RF baseline과 통계적으로 구별 불가(paired-$t$-test $p > 0.42$). 변형별 상세 수치는 Appendix B (Table B.1)로 미룬다.

### 해석

cost-sensitive (decline_x2/x3) + 6-변형 manual 의 null 결과는, 본 데이터에서 *Decline 성능이 단순히 class weight 를 키운다고 개선되지 않음* 을 가리킨다. Decline 가중을 키우면 (i) macro-$F_1$ 불변 (manual, $p > 0.42$) 또는 (ii) Stable precision 손실로 macro-$F_1$ 감소 (decline_x2/x3). G/S/D task 에서 제약 요인은 nominal class weight 가 아니라 baseline·hybrid representation 의 feature separability (신규 고객 비율, 영업기간; §\ref{sec:significant_vars}) 로 보인다. **본 데이터의 분류 경계는 sample weight 가 아니라 feature 로 설정됨.**

---

## §5.9 챕터 요약

본 장은 두 prediction 타깃에 걸쳐 여섯 가지를 확립.

1. **큰 폭 성장 식별.** 점포 관측구간 첫 분기 대비 마지막 분기 평균 매출 2배 이상(=100% 이상 성장) 이항 분류에서 inflection + UDX 결합 representation 이 17-변수 baseline 의 binary $F_1$ 을 RF 0.539→0.642, XGB 0.681→0.818로 향상 (§\ref{sec:taskA_ablation}). full-span 라벨이고 UDX·변곡점 feature가 실현 궤적을 사후 요약하므로, forward 예측이 아니라 *explanatory ablation* 으로 해석.
2. **G/S/D baseline vs hybrid.** 14 시즌 정렬 패널에서 RF baseline (A) macro-$F_1 \approx 0.50$ (패널 범위 **0.467–0.546**), cluster+CP hybrid (D) 와의 paired 비교 평균 $\Delta F_1 = +0.0017$, Bonferroni 후 14 패널 중 0개 유의 — *조건부* 개선 (§\ref{sec:taskB_main}).
3. **G/S/D 모델 비교.** 동일 representation 에서 LightGBM 이 RF 상회 (평균 $\Delta F_1 = +0.0075$, 6 패널 중 5승, 6 중 2에서 $p < 0.05$) — 본 데이터의 *feature 이질성 + 강한 소수 클래스 신호 + 큰 categorical cardinality* 와 LightGBM 구조 특성의 적합으로 해석 (§\ref{sec:rf_vs_lgbm}).
4. **G/S/D 코호트 분해.** 영업기간 사분위 코호트 분석은 신규 고객 → Growth 효과가 모든 코호트에서 일관, 효과 크기는 Q1·Q4 양끝에서 최대 (§5.4).
5. **G/S/D cluster 분해.** 패널 내부 cluster 분해는 *fragile cluster* (Decline 35–45%) 를 분리, 이 안에서 hybrid representation 의 마진이 가장 두드러짐 (§5.6).
6. **G/S/D 외부 비교 · cost-sensitive.** 14 비-LightGBM 비교 모델 중 RF를 상회하는 것은 없고, 우리 LightGBM 계열 3종만 상회 (lgbm_tabular +0.0075, 5/6 승); 14 비-LightGBM 변형 모두 일관된 음의 마진 (−0.0345 ~ −0.2705). cost-sensitive 가중 (rf_decline_x2/x3) 은 macro-$F_1$ 단조 감소 (§\ref{sec:phase5}, §5.8).

다음 장은 G/S/D 결과가 시즌·외부 비교·공간 그래프 모델에 걸쳐 안정적인지 검증. 큰 폭 성장 단일 holdout 의 external validity 는 한계·향후 연구 (§\ref{sec:limitations}) 로.
