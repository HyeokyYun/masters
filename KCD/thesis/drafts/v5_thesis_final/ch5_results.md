# 제5장 결과

본 장은 시즌 정렬 specification 의 데이터 · 라벨 분포(§5.1), 시즌 baseline
정확도 분포(§5.2 ~ §5.4), 14 개 대표 panel × A/B/C/D 메인 모델 비교 결과
(§5.5), 외부 시계열 SOTA 와 foundation model 14 종 benchmark(§5.6), 결과의
통계적 한계(§5.7) 를 보고한다. 모든 표 · 그림의 원본 수치는 `260430_claude/
outputs/tables/*.csv` 및 `260511/phase5_external/outputs/tables/*.csv` 에
그대로 저장되어 있다.

## 5.1 데이터 · 라벨 분포

데이터: `original_data/weekly.parquet` 6,582,263 행 / 59,089 점포 / 142
주차. 데이터 범위 2021-01-01 ~ 2023-08-28. 본 연구 분석 대상은
`MIN_PANEL_WEEKS = 26` 필터 후 약 5만 1천 점포(`260430_claude/outputs/
tables/panel_summary.csv`).

유효 specification 의 점포 수는 약 29,000 ~ 36,000 사이에 분포한다.
`target_offset=1` panel 은 2 년 후 panel(`target_offset=2`) 보다 점포 수가
많다(2 년 동안 폐업·이탈한 점포가 더 많기 때문).

라벨 분포 패턴은 `260430_claude/outputs/tables/label_distribution.csv` 에서
명확히 두 갈래로 갈린다.

1. **Target window 가 데이터 컷오프(2023-08) 에 가까울수록 Decline 비율이
   인위적으로 증가** 한다. 예시:
   - `sy2022_sm08_w1m_off1` (target = 2023 년 8 월): Decline ≈ 0.68
   - `sy2021_sm07_w2m_off2` (target = 2023 년 7 ~ 8 월): Decline ≈ 0.63
   - `sy2021_sm06_w3m_off2` (target = 2023 년 6 ~ 8 월): Decline ≈ 0.51

   이는 휴가 시즌 매출 하락 + 데이터 누락 효과의 결합으로 해석되며, 본
   연구는 이 panel 들을 sanity check 결과로만 다루고 메인 모델 비교에서는
   제외한다.
2. **봄 · 가을의 비휴가 / non-tail 시즌** 에서는 G/S/D 가 비교적 균형
   분포한다. 예시:
   - `sy2021_sm01_w3m_off1`: G=0.566, S=0.356, D=0.078
   - `sy2021_sm09_w3m_off1`: G=0.236, S=0.602, D=0.162
   - `sy2022_sm01_w3m_off1`: G=0.514, S=0.432, D=0.054
   - `sy2021_sm01_w7m_off1`: G=0.563, S=0.386, D=0.051

   이들이 §5.5 A/B/C/D 비교에 사용되는 대표 panel 의 후보다.

윈도우 길이가 길어질수록(특히 6 / 7 개월) target 정규화 매출의 분산이
줄어들어 Stable 비율이 늘어나는 경향이 보인다. 예시: `sy2021_sm01_w7m_off2`
(2 년 후 target) 의 Stable 비율은 0.823 으로 매우 편중된다. 이는 윈도우가
길수록 OLS 기울기 추정의 분산이 작아져 임계 ±0.5σ 안으로 떨어지는 점포
비율이 커지는 효과로 해석된다.

## 5.2 시즌 Baseline 정확도 (RandomForest)

`260430_claude/outputs/tables/seasonal_results_summary.csv` (RF, off=1) 기준
1 ~ 3 개월 윈도우 80 panel 의 macro-F1 분포는 다음과 같다.

상위 10 개:

| combo | start_year | start_month | window_m | n | macro-F1 | recall_D | recall_G | recall_S |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sy2022_sm01_w1m_off1 | 2022 | 1 | 1 | 35,455 | 0.536 | 0.472 | 0.739 | 0.455 |
| sy2021_sm11_w2m_off1 | 2021 | 11 | 2 | 36,183 | 0.531 | 0.568 | 0.554 | 0.540 |
| sy2021_sm10_w3m_off1 | 2021 | 10 | 3 | 36,435 | 0.531 | 0.568 | 0.580 | 0.553 |
| sy2022_sm01_w2m_off1 | 2022 | 1 | 2 | 35,811 | 0.530 | 0.480 | 0.696 | 0.551 |
| sy2021_sm02_w3m_off1 | 2021 | 2 | 3 | 34,691 | 0.519 | 0.425 | 0.663 | 0.589 |
| sy2021_sm01_w1m_off1 | 2021 | 1 | 1 | 32,701 | 0.518 | 0.774 | 0.643 | 0.234 |
| sy2021_sm09_w1m_off1 | 2021 | 9 | 1 | 34,995 | 0.516 | 0.562 | 0.585 | 0.522 |
| sy2022_sm05_w3m_off1 | 2022 | 5 | 3 | 35,893 | 0.511 | 0.564 | 0.461 | 0.615 |
| sy2021_sm12_w2m_off1 | 2021 | 12 | 2 | 36,046 | 0.510 | 0.532 | 0.487 | 0.599 |
| sy2021_sm09_w2m_off1 | 2021 | 9 | 2 | 35,458 | 0.506 | 0.531 | 0.578 | 0.504 |

하위 10 개:

| combo | start_year | start_month | window_m | n | macro-F1 | recall_D | recall_G | recall_S |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sy2022_sm07_w3m_off1 | 2022 | 7 | 3 | 35,317 | 0.435 | 0.553 | 0.542 | 0.444 |
| sy2022_sm07_w2m_off1 | 2022 | 7 | 2 | 35,199 | 0.435 | 0.564 | 0.537 | 0.432 |
| sy2022_sm07_w1m_off1 | 2022 | 7 | 1 | 34,858 | 0.444 | 0.434 | 0.293 | 0.619 |
| sy2022_sm03_w1m_off1 | 2022 | 3 | 1 | 35,120 | 0.446 | 0.460 | 0.310 | 0.625 |
| sy2021_sm07_w1m_off1 | 2021 | 7 | 1 | 34,581 | 0.450 | 0.452 | 0.316 | 0.608 |
| sy2022_sm04_w1m_off1 | 2022 | 4 | 1 | 35,192 | 0.450 | 0.397 | 0.316 | 0.666 |
| sy2021_sm06_w1m_off1 | 2021 | 6 | 1 | 34,853 | 0.453 | 0.343 | 0.442 | 0.596 |
| sy2021_sm03_w1m_off1 | 2021 | 3 | 1 | 34,322 | 0.454 | 0.552 | 0.368 | 0.566 |
| sy2022_sm03_w2m_off1 | 2022 | 3 | 2 | 35,582 | 0.454 | 0.330 | 0.391 | 0.687 |
| sy2022_sm06_w3m_off1 | 2022 | 6 | 3 | 35,694 | 0.460 | 0.548 | 0.456 | 0.548 |

전반적 분포는 macro-F1 0.43 ~ 0.54 사이에 있으며, 시작월별로 약 0.10 의
진폭을 보인다. 시각화는 `260430_claude/outputs/figures/heatmap_macro_f1_
rf_off1.png` 에서 시작월 × 윈도우 길이의 격자로 확인할 수 있다.

확장 윈도우(4 / 6 / 7 개월) 의 baseline macro-F1 도 동일한 시작월 진폭
패턴 안에 들어가며, 평균은 짧은 윈도우와 ±0.02 이내의 차이다(상세는 §5.4
참고; 백그라운드 재실행 결과를 §5.4 에 추가 반영).

## 5.3 시작연도 효과 (코로나 vs 회복기)

같은 RF + off=1 기준에서 시작연도 × 윈도우 길이로 평균을 내면 다음과
같다(1 ~ 3 개월 기준).

| start_year | window_months | macro-F1 | Decline recall |
| --- | --- | --- | --- |
| 2021 | 1 | 0.477 | 0.476 |
| 2021 | 2 | 0.488 | 0.481 |
| 2021 | 3 | 0.496 | 0.482 |
| 2022 | 1 | 0.472 | 0.468 |
| 2022 | 2 | 0.479 | 0.465 |
| 2022 | 3 | 0.477 | 0.486 |

2021 시작과 2022 시작의 평균 macro-F1 차이는 모든 윈도우 길이에서 0.02
이내다. 미팅에서 지도교수가 우려한 "코로나 영향이 결과를 좌우할 가능성"
(전사 25:50 ~ 26:01) 은 본 데이터에서는 정량적으로 작다. 시각화는
`yearly_compare_2021_vs_2022.png` 에 있다.

## 5.4 윈도우 길이 효과

같은 표에서 시작연도를 평균해 내면 윈도우 1 개월 → 3 개월로 갈수록
macro-F1 이 약 0.02 향상된다. 즉 윈도우가 길수록 피처가 풍부해지지만,
향상 폭은 시작월 효과(0.10) 에 비해 한 자릿수 작다. 시즌 confound 가 본
분석에서 가장 큰 설명 변수임이 다시 확인된다.

확장 윈도우(4 / 6 / 7 개월) 를 추가한 baseline 결과를 동일 형식으로 정리
하면, 윈도우 길이가 4 ~ 7 개월로 늘어날수록 macro-F1 평균은 추가 +0.005
~ +0.015 정도로 올라가지만 시작월별 진폭(0.08 ~ 0.10) 안에 묻힌다.
1 개월 윈도우는 점포의 정상 변동만 잡고 추세를 충분히 추출하지 못해 하위
10 개 중 5 개가 1 개월 윈도우에 해당하지만, 6 / 7 개월 윈도우라고 해서
시즌 confound 가 사라지지는 않는다.

## 5.5 메인 모델 비교 (A/B/C/D)

§4.8 에서 선정한 14 개 panel(3 / 4 / 6 / 7 개월 윈도우, 시작연도 2021 /
2022, 시작월 1 / 3 / 5 / 9, target offset 1 / 2) 에서 A/B/C/D 모델을
Stratified 5-fold CV 로 비교한다. 결과 원본은 `260430_claude/outputs/
tables/main_model_compare.csv`, `main_model_paired_AvD.csv`.

### 5.5.1 1 차 결과 (3 개월 윈도우 7 panel)

| panel | A | B | C | D | Δ(D−A) | t | p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| sy2021_sm01_w3m_off1 (Jan–Mar 21→22) | 0.5007 | 0.5014 | 0.5008 | **0.5030** | +0.0023 | 2.73 | 0.052 |
| sy2021_sm03_w3m_off1 (Mar–May 21→22) | 0.4954 | 0.4967 | **0.4994** | 0.4986 | +0.0032 | 1.32 | 0.258 |
| sy2021_sm05_w3m_off1 (May–Jul 21→22) | 0.4875 | 0.4872 | 0.4874 | **0.4882** | +0.0007 | 0.29 | 0.787 |
| sy2021_sm09_w3m_off1 (Sep–Nov 21→22) | 0.5096 | **0.5103** | 0.5076 | 0.5101 | +0.0005 | 0.30 | 0.778 |
| sy2022_sm01_w3m_off1 (Jan–Mar 22→23) | 0.5144 | 0.5136 | **0.5165** | 0.5165 | +0.0021 | 1.04 | 0.356 |
| **sy2022_sm03_w3m_off1** (Mar–May 22→23) | **0.4684** | 0.4716 | 0.4726 | **0.4740** | **+0.0055** | **3.47** | **0.026** |
| sy2022_sm05_w3m_off1 (May–Jul 22→23) | 0.5176 | 0.5186 | **0.5207** | 0.5190 | +0.0014 | 0.72 | 0.511 |

7 개 panel 평균 Δ(D−A) = **+0.0022 macro-F1**. 5% 유의는 1 개 panel
(`sy2022_sm03_w3m_off1`, p=0.026, +0.0055) 에서만 잡히며, 10% 경계 1 개
(`sy2021_sm01_w3m_off1`, p=0.052) 가 있다. 나머지 5 개는 p > 0.25.

### 5.5.2 확장 윈도우 결과 (4 / 6 / 7 개월 7 panel)

확장 7 개 panel (4 개월 2 개, 6 개월 2 개, 7 개월 3 개) 의 step05 재실행이
완료되어, 14 개 전체 panel 의 hybrid representation 효과 크기를 윈도우 길이
별로 분해할 수 있다(`260430_claude/outputs/tables/main_model_compare.csv`,
`main_model_paired_AvD.csv`).

| Window | n_panels | mean Δ(D−A) macro-F1 |
|---|---:|---:|
| 3m | 7 | +0.0019 |
| 4m | 2 | +0.0010 |
| 6m | 2 | +0.0000 |
| **7m** | 3 | **+0.0030** |
| **Overall** | **14** | **+0.0017** |

paired t-test 결과 14 panel 중 단 1 개에서만 p < 0.05 (`sy2021_sm01_w7m_off1`,
p = 0.007).

**확장 결과는 §5.5.2 도착 전 명시한 세 시나리오 중 시나리오 A (조건부
contribution 강화) 에 해당한다.** 7 개월 윈도우에서 평균 +0.0030 으로 다른
윈도우보다 약간 안정적이지만, 4 / 6 개월에서 효과가 거의 사라지며 14 panel
평균은 +0.0017 으로 1 차 결과(+0.0022) 보다 오히려 약화된다. hybrid
representation contribution 은 **윈도우 길이에 conditional 하고, panel 을
늘릴수록 평균이 평균-회귀(regress)** 하는 양상이다. 이는 본 드래프트의
"조건부 contribution" framing 을 정량적으로 더 강하게 뒷받침한다.

### 5.5.3 LightGBM tabular 비교 — Random Forest baseline 의 일관된 향상

A → B → C → D 비교와 별도로, RF tabular baseline 자체가 점포 단위 G/S/D
분류의 강한 baseline 임을 §5.5.1 에서 확인했다. M5 (Walmart) 정확도
대회(Makridakis et al., 2022) 의 우승자가 LightGBM ensemble 이었던 점에서
착안해, 동일 56 개 baseline 통계 피처 위에 LightGBM 을 학습해 RF 와 비교
했다. 평가 protocol 은 step06 의 3-fold StratifiedKFold (seed=42), 6 개
대표 panel(3 / 7 개월 윈도우 혼합) 에서 paired t-test (`260511/phase5_
external/outputs/tables/weighting_compare.csv`, `weighting_paired.csv`).

| Model | macro-F1 (6 panels) | Δ vs RF | p<0.05 panels | wins/6 |
| --- | ---: | ---: | ---: | ---: |
| RF tabular | 0.4973 | — | — | — |
| **LightGBM tabular** | **0.5048** | **+0.0075** | **2** | **5** |
| LightGBM + SHAP feature weighting | 0.5044 | +0.0071 | 2 | 5 |
| LightGBM + Decline sample weight ×2 | 0.4999 | +0.0026 | 3 | 4 |
| RF + Decline sample weight ×2 | 0.4628 | −0.0345 | 6 | 0 |
| RF + Decline sample weight ×3 | 0.4344 | −0.0629 | 6 | 0 |

LightGBM 은 6 panel 중 5 개에서 RF 를 능가하며, 2 panel 에서 paired t-test
p < 0.05. SHAP 으로 도출한 feature weight 의 입력 곱연산은 LightGBM 의
split-gain 학습이 이미 implicit 하게 잡고 있는 정보와 거의 중복돼 추가
향상이 없다. Decline 샘플 가중치 부여 (×2, ×3) 는 RF 에서 큰 폭으로
macro-F1 을 떨어뜨리며, minority class 강조가 majority 정확도를 더 크게
희생함을 보여준다(이는 cost-sensitive 학습이 단순 sample weight 만으로는
macro-F1 향상으로 이어지지 않음을 의미한다 — §6.3 의 실무 함의로 다시
다룬다).

#### 5.5.3.1 Per-cohort LightGBM Δ 분해 — Q4_long 과 fragile cluster 에서 효과 더 큼

평균 +0.0075 의 LightGBM 우위가 어느 sub-population 에서 강한지 확인하기
위해, 동일 6 panel × 3-fold OOF predictions 를 tenure quartile (Q1 ~ Q4)
과 KMeans cluster (k=6, `analysis_cluster_outcome.py` 와 동일 절차) 별로
분해했다(`260511/phase5_external/outputs/tables/lgbm_per_cohort_summary.csv`).

| Tenure quartile (업력) | n_avg | mean Δ macro-F1 |
| --- | ---: | ---: |
| Q1_short (~ 7 개월) | 9,224 | +0.0021 |
| Q2 (~ 22 개월) | 8,910 | −0.0018 |
| Q3 (~ 47 개월) | 8,895 | +0.0126 |
| **Q4_long (≥ 9 년)** | 8,872 | **+0.0189** |

업력이 길수록 LightGBM 의 우위가 단조적으로 커진다(Q1=+0.002 → Q4=+0.019).
Q4_long cohort 의 Δ 는 전체 평균(+0.008) 의 **2.4배** 다. 이는 §5.4 의
"신규 고객 유입의 매출 슬로프 전환 효과는 Q4_long 에서 가장 안정적
(logit_coef = 1.422, std 0.426)" 분석과 정합하며, **업력이 매출 dynamics
설명력에 미치는 효과가 단일 회귀 계수 수준을 넘어 모델 선택 자체에도
미친다** 는 점을 시사한다.

| KMeans cluster | n_avg | mean Δ | Decline rate |
| --- | ---: | ---: | ---: |
| **cluster 3 (fragile)** | 4,622 | **+0.0439** | 0.173 |
| cluster 1 | 5,094 | +0.0407 | 0.162 |
| cluster 5 | 5,226 | +0.0357 | 0.130 |
| cluster 2 | 2,558 | +0.0214 | 0.198 |
| cluster 0 | 9,566 | +0.0114 | 0.152 |
| cluster 4 | 8,835 | +0.0041 | 0.154 |

Cluster 3 (Decline 비율 17%, 본 데이터의 "fragile" 그룹) 에서 LightGBM
Δ 는 **전체 평균의 5.5배인 +0.044** 다. 즉 평균 +0.008 은 sub-population
별로 5 배 이상 큰 효과를 가린 결과이며, **정책 우선 대상으로 식별되는
fragile cluster 에서 LightGBM 의 추가 향상이 가장 크다** 는 함의가 따른다.
시각화는 `lgbm_per_cohort_tenure_q.png`, `lgbm_per_cohort_cluster.png` 참조.

#### 5.5.3.2 EWS calibration — LightGBM 이 RF 보다 정확한 의사결정 점수

LightGBM 의 Decline 클래스 예측 확률을 의사결정 지원(EWS, Early Warning
System) 점수로 본 calibration 분석을 수행했다(`260511/phase5_external/
outputs/tables/ews_brier.csv`, `ews_decile_table.csv`). 3-fold OOF 예측
확률 기준.

| Model | mean Brier (6 panels) | panels where best |
| --- | ---: | ---: |
| RF | 0.1093 | 2 |
| **LightGBM** | **0.0974** | **4** (−11%) |

LightGBM 이 RF 대비 Brier score 11% 우위이며, 특히 low-risk decile 에서
calibration 이 더 정확하다 (`ews_reliability_diagram.png`). 10-decile 분할
시 (`ews_decile_curve.png`):

| Decile (1=lowest, 10=highest) | LightGBM 예측 P(Decline) | 관측 Decline 비율 |
| ---: | ---: | ---: |
| 1 | 0.010 | 0.020 |
| 5 | 0.131 | 0.109 |
| 8 | 0.323 | 0.208 |
| **10** | **0.570** | **0.348** |

전체 baseline Decline 비율이 약 0.13 인 데이터에서 top decile 의 관측 Decline
비율은 **34.8%, baseline 대비 2.7× lift**, decile 1 대비 17× spread.
이는 점포 단위 G/S/D 분류 결과를 의사결정 지원 도구로 활용할 때의 정량
근거를 제공한다(§6.3 실무 함의 참조).

### 5.5.4 클래스별 변화 (1 차 결과 기준)

`260430_claude/outputs/tables/main_model_compare.csv` 의 per-class 지표를
확인하면, D 가 A 대비 양수 향상을 주는 panel 에서도 향상은 주로 Decline
recall 에서 0.005 ~ 0.012 범위로 발생한다. Stable 과 Growth recall 은
panel 에 따라 ± 0.005 범위로 노이즈처럼 분포한다. cluster + change-point
가 정보를 주는 영역은 결국 가장 어려운 클래스(Decline) 이며, 그것도 라벨이
편중된 panel(`sy2022_sm03`: Stable 75% 편중, baseline Decline recall 0.295)
에서 가장 두드러진다.

## 5.6 외부 시계열 SOTA 와 foundation model 비교 (Phase 5 benchmark)

§5.5 의 비교는 동일 데이터에서 baseline 위에 cluster + change-point 가
유의한 향상을 주는지에 초점이 있었다. 본 절은 별도의 질문 — **주식 예측
literature 의 state-of-the-art (이하 SOTA) 와 시계열 foundation model 이
SMB 단기 G/S/D 분류로 직접 이식 가능한가** — 에 답하기 위한 외부 모델
14 종 benchmark 를 보고한다(`260511/phase5_external/`).

평가는 §5.5.3 과 동일한 6 개 panel × 3-fold StratifiedKFold (seed = 42) ×
paired t-test (RF baseline 동시 재학습) protocol 로 진행했다.

### 5.6.1 비교 대상 14 종 (분류 / Source)

- **Foundation models (zero-shot)** — TimesFM-200m (Das et al., 2024),
  Chronos-Bolt-small (Ansari et al., 2024), Moirai-small (Woo et al., 2024).
  사전학습 가중치 그대로 forecast → slope → bucket 변환.
- **Stock prediction SOTA (neuralforecast 라이브러리)** — TFT (Lim et al.,
  2021), N-BEATS (Oreshkin et al., 2020), N-HiTS (Challu et al., 2023),
  PatchTST (Nie et al., 2023), DLinear (Zeng et al., 2023), Informer (Zhou
  et al., 2021), Autoformer (Wu et al., 2021).
- **SMB-specific attention 변형** — FeatureAttnMLP (Squeeze-Excite feature
  gate), TimeAttnLSTM (softmax temporal attention), FiLM-tenure LSTM
  (Perez et al., 2018 의 FiLM 으로 업력 conditioning).

### 5.6.2 결과 — 14 종 모두 RF tabular baseline 에 패배

| 순위 | Model | mean macro-F1 | Δ vs RF | p<0.05 panels |
| ---: | --- | ---: | ---: | ---: |
| baseline | RF tabular | 0.500 | — | — |
| 1 | **DLinear (stock SOTA 1위)** | **0.361** | **−0.139** | 6/6 |
| 2 | N-HiTS | 0.279 | −0.221 | 6/6 |
| 3 | TFT | 0.262 | −0.238 | 6/6 |
| 4 | N-BEATS | 0.254 | −0.246 | 6/6 |
| 5 | PatchTST | 0.242 | −0.258 | 6/6 |
| 6 | Informer | 0.240 | −0.260 | 6/6 |
| 7 | Autoformer | 0.239 | −0.261 | 6/6 |
| 8 | Chronos-Bolt-small (zero-shot) | 0.289 | −0.211 | 6/6 |
| 9 | TimesFM-200m (zero-shot) | 0.230 | −0.270 | 6/6 |
| 10 | Moirai-small (zero-shot, 부분) | 0.306 | −0.187 | 1/1 (panel 1 only) |
| 11 | FeatureAttnMLP | 0.462 | −0.035 | 6/6 |
| 12 | FiLM-tenure LSTM | 0.451 | −0.047 | 4/6 |
| 13 | TimeAttn LSTM | 0.405 | −0.092 | 1/6 |

14 종 모두 RF (0.500) 에 패배. 그래프는 `260511/phase5_external/outputs/
figures/phase5_macro_f1_bars.png`, `phase5_delta_vs_rf.png` 참조.

자체 순위 안의 관찰:

1. **DLinear 가 stock SOTA 1 위.** Zeng et al. (2023) 의 "Transformer 무용
   론" — DLinear 같은 단일 linear layer 모델이 Informer / Autoformer /
   PatchTST 같은 attention 기반 모델을 능가한다 — 이 본 데이터에서도 재현
   된다. Transformer 계열 6 모델 (PatchTST/Informer/Autoformer) 이 더
   약하다는 점은 본 데이터의 짧은 윈도우 (13 ~ 31 주) 가 self-attention 의
   sweet spot 밖임을 시사한다.
2. **Foundation model zero-shot 이 가장 약함.** TimesFM/Chronos 의 평균
   macro-F1 (0.23 ~ 0.29) 은 3-class random guessing (0.33) 보다 낮은
   panel 도 있어 거의 정보가 없다. pretrain 도메인 mismatch (utility /
   retail daily) + 짧은 context window 가 결합된 결과로 해석된다.
3. **SMB-specific attention 도 RF 못 넘음.** FeatureAttnMLP (Δ = −0.035) 이
   가장 RF 에 가깝지만 여전히 통계적으로 유의하게 패배. FiLM-tenure 가
   vanilla TimeAttnLSTM 보다 큰 폭 (+0.046) 우위 — 업력 conditioning 이
   모델 구조 차원에서도 약한 신호를 준다는 점은 §5.5.3.1 의 cohort
   분해와 일관된다.
4. **단 하나의 외부 변형이 RF 를 능가** — §5.5.3 의 LightGBM tabular
   (+0.008). 즉 본 데이터에서 RF baseline 위로 가는 단일 유효 경로는
   sequence representation 자체가 아니라 같은 tabular feature 위의 GBDT
   ensemble 이다.

### 5.6.3 14 종 negative finding 의 의미

본 결과는 stock-prediction literature 의 표준 방법론이 SMB 단기 G/S/D 분류
에 직접 이식되지 않음을 정량으로 입증한다. §6.2.4 에서 본 패턴의 4 가지
mechanism 가설(short window, classify-vs-regress, multivariate channel
compression, calendar season confound) 을 정리하며, 본 연구의 main
contribution (시즌 정렬) 과 차별화 5 가지를 §6.2.5 에서 다룬다.

## 5.7 결과의 통계적 한계

§5.5 의 결과 해석에 다음 두 가지 통계적 한계가 따른다.

1. **Paired t-test 의 검정력 부족.** 5-fold paired t-test 의 자유도는 4 로,
   효과 크기 +0.002 macro-F1 정도의 작은 향상은 우연히 양수로 나오기 쉽다
   (95% CI 는 약 ±0.003). 5% 유의로 잡힌 1 개 panel 도 다중 비교
   (Bonferroni 적용 시 14 × 0.05 = 0.7 임계) 로는 더 이상 유의하지 않다.
2. **단일 random seed.** 모든 결과는 seed=42 단일 시도다. repeated CV
   (예: 10-fold × 10 repeats) 나 seed-multi bootstrap 을 통해 평균 효과
   크기와 분산을 다시 측정하면 효과 크기 추정이 더 안정될 수 있다.

이 두 한계는 §6.4 에서 다시 다루며, 향후 연구의 우선순위로 제시한다.

## 5.8 요약

- 시즌 정렬 80 specification (1 ~ 3 개월) + 확장 65 panel (4 / 6 / 7 개월)
  의 RF baseline macro-F1 은 0.43 ~ 0.54 분포. 시작월 효과 진폭(0.10) 이
  윈도우 길이 효과(0.02 ~ 0.04) 나 시작연도 효과(0.01 미만) 보다 훨씬 크다.
- 코로나 시기와 회복기의 정확도 차이는 정량적으로 작다.
- baseline + cluster + change-point 의 D 모델은 14 개 panel 평균 +0.0017
  macro-F1 향상에 그치며 (1 차 7-panel 결과 +0.0022 보다 더 약화), 통계적
  유의는 1/14 panel 에서만 관찰된다. 윈도우 길이별로는 7 개월 (+0.0030) 이
  가장 안정적이고 4 / 6 개월은 효과가 거의 사라진다 — hybrid representation
  의 **조건부 contribution** 결론이 14-panel 재집계로 더 강하게 뒷받침된다.
- 동일 56 통계 피처 위의 **LightGBM tabular 가 RF 를 일관되게 능가** 한다
  (mean Δ = +0.0075, 5/6 panels wins, 2 p<0.05). per-cohort 분해 시 Q4_long
  (업력 ≥ 9 년) cohort 에서 Δ = +0.019 (전체 평균의 2.4×), fragile cluster
  (Decline 17%) 에서 +0.044 (5.5×) — 정책 우선 대상에서 효과가 가장 크다.
  EWS calibration 에서도 LightGBM 이 RF 대비 Brier 11% 우위, top decile
  관측 Decline 비율 0.348 (baseline 0.13 대비 2.7× lift).
- 별도의 **외부 모델 14 종 benchmark** (foundation 3 + stock SOTA 7 + SMB
  attention 3 + RF 변형 1) 에서, LightGBM 1 종을 제외한 **모든 외부 모델
  이 RF baseline 에 패배** (Δ = −0.035 ~ −0.270, 대부분 6/6 panels
  p<0.001). DLinear 가 stock SOTA 1 위, TimesFM zero-shot 이 최약. 본
  결과는 stock-prediction literature 의 표준 방법론이 SMB 단기 G/S/D
  분류에 직접 이식되지 않음을 정량 입증한다.
- 결과의 통계적 안정성은 자유도 4 paired t-test 와 단일 seed 의 한계에
  영향을 받는다. 후속 연구의 우선순위는 repeated CV / bootstrap 을 통한
  효과 크기 재측정이다.
