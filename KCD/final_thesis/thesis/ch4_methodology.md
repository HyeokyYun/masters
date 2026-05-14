# 제 4 장 방법론

본 장은 본 연구의 방법론을 다음 순서로 기술한다. 4.1 시즌 정렬
rolling-window 분석 프레임, 4.2 specification 카탈로그, 4.3 G/S/D
라벨 생성, 4.4 가변 윈도우 피처 추출, 4.5 모델 비교 프로토콜
(A/B/C/D), 4.6 시즌 baseline 평가, 4.7 평가 지표, 4.8 대표 panel 의
선정 기준, 4.9 cohort/cluster 분해 정의 (§5.7 ~ §5.8 의 분석 단위),
4.10 cost-sensitive 보조 실험 프로토콜 (§5.9), 4.11 재현 절차. 모든
절차는 일곱 개의 스크립트 (`260430_claude/src/step01_*` ~ `step05_*`,
`step05c_*`, `analysis_cluster_outcome.py`) 에 그대로 구현되어 있다.

본 연구의 상위 prediction RQ 는 §1.3 에 따라 (RQ1 baseline·요인,
RQ2 label robustness, RQ3 representation·weighting, RQ4 SOTA transfer)
네 가지로 구성되며, 4.1 의 시즌 정렬 설계는 그 중 RQ2 에 대응하는
방법론적 전제다. 4.3 의 라벨 정의·4.5 의 비교 프로토콜·4.8 의 panel
선정·4.9 의 cohort 분해·4.10 의 보조 실험이 모두 이 시즌 정렬 위에서
작동한다.

## 4.1 분석 프레임 — 시즌 정렬 rolling window

각 specification 은 4-튜플 `(start_year, start_month, window_months,
target_offset)` 로 정의된다. 이 4-튜플로부터 다음 두 시간 구간이
결정된다.

- **Feature window** — `start_year`-`start_month`-01 부터
  `window_months` 개월. 점포의 영업 초기 거래 패턴을 관측하는 구간이며,
  입력 피처를 추출하는 데이터 소스다.
- **Target window** — `(start_year + target_offset)`-`start_month`-01
  부터 `window_months` 개월. feature window 와 **같은 캘린더 월,
  같은 길이**를 가지며, 점포의 G/S/D 상태 라벨을 정의하는 구간이다.
- **Lag window** — feature 끝과 target 시작 사이 구간. 라벨 누설을
  막기 위한 hold-out 영역이며, 본 연구는 lag window 데이터를 사용
  하지 않는다.

본 설계의 핵심은 feature 와 target 이 같은 캘린더 월이라는 점이다.
명절·휴가·학기·날씨 등 시즌 변동은 두 윈도우에 비슷한 강도로 들어가므로,
시즌 변동이 라이프사이클 신호로 잘못 해석될 위험이 줄어든다. 이는
시계열 분류 평가에서 흔히 누락되는 통제이며, 본 연구의 §5.2 결과는
이 통제를 빼면 시작월에 따라 macro-F1 이 0.10 까지 흔들린다는 것을
보인다.

## 4.2 Specification 카탈로그

`260430_claude/src/utils_panel.py:enumerate_combos` 가 다음 조건을
만족하는 4-튜플을 자동 생성한다.

- `feature_start ≥ 2021-01-01` (데이터 시작)
- `target_start ≤ 2023-08-28` (데이터 컷오프 안에 target 시작이
  들어와야 함)

총 288 개 후보 중 데이터 범위를 벗어나는 specification 들은 panel
구성 단계에서 0 개 점포로 떨어지고, 본 연구의 분석 대상으로 살아남는
specification 은 약 145 개다
(`260430_claude/outputs/tables/panel_summary.csv`).

이 중 §4.5 의 메인 모델 비교에는 §4.8 의 기준을 만족하는 14 개
panel 만 사용한다. 시즌 baseline 평가(§4.6, §5.2) 는 145 개 유효
panel 모두에 대해 수행한다.

## 4.3 G/S/D 라벨 생성

`260430_claude/src/step02_relabel_gsd_calendar.py` 의 절차다.

1. 각 점포의 feature + target 합친 평균(`store_mean`) 으로 매출을 나눠
   정규화한다. 본 정규화는 점포 간 매출 규모 차이를 표준화하여 기울기
   비교를 가능하게 한다.
2. 점포의 target window 정규화 매출 시퀀스에 OLS 기울기
   `slope_target` 을 계산한다 (`utils_panel.row_slopes`). 결측치는
   NaN-safe linear regression 으로 처리한다.
3. 점포 간 `slope_target` 의 표준편차 σ 를 계산하고 임계값
   `thr = 0.5σ` 를 설정한다 (`config.SLOPE_THRESHOLD_SIGMA = 0.5`).
4. 라벨링 규칙:
   - `slope_target >  thr` → **Growth (G)**
   - `slope_target < -thr` → **Decline (D)**
   - 그 외 → **Stable (S)**
5. target window 내 유효 주차가 3 주 미만인 점포는 제외한다.

라벨이 **target 구간에서만 추정한 기울기** 라는 점이 중요하다. 기존
프로토콜에서 흔히 쓰이는 전체 기간 기울기는 feature 구간의 시즌까지
라벨에 흡수해 분류 난이도를 인위적으로 높이거나 낮춘다.

## 4.4 가변 윈도우 피처 추출

`260430_claude/src/step03_extract_features.py` 는 feature window 가
4 ~ 31 주로 가변임을 반영한다. 핵심 피처 43 개는 다음 7 개 그룹으로
분류된다.

| 그룹 | 피처 |
| --- | --- |
| 매출 통계 | `sales_mean`, `sales_std`, `sales_median`, `sales_min`, `sales_max`, `sales_range`, `sales_cv` |
| 기울기 | `slope_all`, `slope_first_half`, `slope_second_half`, `slope_half_diff` (윈도우 ≥ 6 주: `slope_1_3`, `slope_2_3`, `slope_3_3`, `slope_accel`) |
| 이동평균 | 윈도우 ≥ 4 주: `ma4_slope`, `ma4_std`, `vol_w4`; 윈도우 ≥ 8 주: `ma8_slope`, `ma8_std`, `vol_w8` |
| 신규 고객 | `nc_mean`, `nc_std`, `nc_slope`; 윈도우 ≥ 4 주: `nc_last_q`, `nc_first_q`, `nc_delta` |
| 고객 | `cust_slope`, `cust_mean`, `cust_cv` |
| 채널 | `del_mean`, `del_slope`, `bn_mean`, `wk_mean` |
| 분포 | `q25`, `q50`, `q75`, `iqr`; 윈도우 ≥ 3 주: `diff_mean`, `diff_std`, `diff_max_abs`, `zero_cross` |

가변 윈도우 처리의 핵심은 윈도우 길이가 짧을 때 정의되지 않는 피처
(예 `slope_1_3` 처럼 3 등분 슬로프) 를 자동으로 skip 하는 것이다.
이 설계로 1 ~ 7 개월 윈도우 사이의 직접 비교가 가능해진다. 점포 5 만
개 단위 벡터화 처리로 panel 당 5 ~ 15 초가 걸린다 (윈도우가 길수록
약간 더 걸림).

## 4.5 모델 비교 프로토콜 (A/B/C/D)

`260430_claude/src/step05_train_main_model.py` 의 프로토콜이다. 비교
대상은 다음 네 모델이다.

| 코드 | 피처 구성 | 피처 수 |
| --- | --- | --- |
| **A. Baseline** | §4.4 의 43 개 피처만 | 43 |
| **B. + Cluster** | A + KMeans (k=6) one-hot | 49 |
| **C. + Change-point** | A + change-point 7 개 | 50 |
| **D. + Cluster + CP (Hybrid)** | A + B + C | 56 |

**B 의 클러스터링.** feature window 의 점포별 정규화 매출 시퀀스 위에
StandardScaler 적용 후 KMeans (k=6, n_init=10, seed=42) 를 학습한다.
점포별 클러스터 라벨은 6 개 더미 변수로 인코딩한다.

**C 의 change-point.** 각 점포의 정규화 매출 시퀀스에 max-mean-gap
알고리즘으로 최적 분할 지점을 찾고, 7 개 피처
(`cp_position`, `cp_pre_slope`, `cp_post_slope`, `cp_delta_slope`,
`cp_magnitude`, `has_up_cp`, `has_down_cp`) 를 생성한다.

**모델 · 하이퍼파라미터.** 모든 비교 모델은 동일한
`RandomForestClassifier` (`n_estimators=240`, `max_depth=14`,
`min_samples_leaf=10`, `n_jobs=-1`, `class_weight="balanced"`,
`random_state=42`) 를 사용한다. 모델 자체를 통제하므로 A/B/C/D 의
차이는 오직 피처 구성에서 온다.

**평가.** 각 모델에 대해 Stratified 5-fold CV (seed=42) 로 macro-F1,
per-class recall, per-class F1 을 계산한다.

**검정.** A vs D 의 통계적 유의성을 per-fold macro-F1 에 대한
paired t-test (자유도 4, `scipy.stats.ttest_rel`) 로 검정한다.
다중 panel 비교에 대한 Bonferroni 보정 결과는 §5.5 에서 별도 보고한다.

## 4.6 시즌 baseline 평가

`260430_claude/src/step04_evaluate_seasonal_baseline.py` 는 145 개
유효 specification 모두에 대해 RandomForest 와 LightGBM 두 모델로
baseline 정확도를 측정한다. 본 단계는 §4.5 의 A 모델만 평가하며,
시즌·시작연도·윈도우 길이별 정확도 분포를 heatmap 과 표로 보고한다
(§5.2).

LightGBM 설정: `n_estimators=200`, `learning_rate=0.05`,
`num_leaves=63`, `min_child_samples=30`, `subsample=0.9`,
`colsample_bytree=0.9`, `class_weight="balanced"`.

RF 와 LightGBM 두 모델로 측정하는 이유는 시즌 효과가 특정 학습
알고리즘의 특성이 아니라 데이터 자체의 성질이라는 점을 보이기
위함이다.

## 4.7 평가 지표

본 연구는 다음 지표를 기본으로 사용한다.

- **Macro-F1** — 세 클래스의 F1 단순 평균. 라벨 불균형에 robust 한
  1 차 지표이며 본 논문의 모든 모델 비교에 우선 사용한다.
- **Per-class recall** — Decline / Stable / Growth 각각의 재현율.
  쇠퇴 점포를 놓치지 않는지 (Decline recall) 가 정책 활용 관점에서
  가장 중요하다.
- **Per-class F1** — precision 과 recall 의 조화평균. 클래스별 모델
  성능을 세부 점검한다.
- **5-fold paired t-test** — 모델 비교의 유의성 검정. 자유도 4 의
  검정력 한계는 §6.4 에서 논의한다.

ROC AUC 는 본 연구의 multi-class 설정에서 부수 지표로만 사용한다.

## 4.8 대표 panel 14 개 선정 기준

§4.5 의 A/B/C/D 비교는 §4.6 baseline 결과에 기초해 다음 기준을 만족
하는 14 개 panel 에서 수행한다.

1. **시즌 분산** — 시작월 1, 3, 5, 9 월 중심으로 분포해 겨울·봄·
   초여름·가을 시즌을 모두 대표.
2. **시작연도 양쪽 포함** — 2021 (코로나) 과 2022 (회복기) 모두.
3. **윈도우 길이 분산** — 3 개월 7 개, 4 개월 2 개, 6 개월 2 개,
   7 개월 3 개. 길이 효과 측정이 가능.
4. **사용자 미팅 노트 직접 매칭** — "21 년 1 ~ 7 월 → 23 년 1 ~ 7 월"
   같은 7 개월·1 ~ 2 년 후 target 모두 포함.
5. **라벨 분포 편중 panel 우선 배제** — 데이터 컷오프 근접 panel 은
   선정 후보에서 제외.

선정된 14 개 panel:

```
sy2021_sm01_w3m_off1   (Jan-Mar 2021 → Jan-Mar 2022)
sy2021_sm03_w3m_off1   (Mar-May 2021 → Mar-May 2022)
sy2021_sm05_w3m_off1   (May-Jul 2021 → May-Jul 2022)
sy2021_sm09_w3m_off1   (Sep-Nov 2021 → Sep-Nov 2022)
sy2022_sm01_w3m_off1   (Jan-Mar 2022 → Jan-Mar 2023)
sy2022_sm03_w3m_off1   (Mar-May 2022 → Mar-May 2023)
sy2022_sm05_w3m_off1   (May-Jul 2022 → May-Jul 2023)
sy2021_sm01_w7m_off1   (Jan-Jul 2021 → Jan-Jul 2022, 7m)
sy2021_sm01_w7m_off2   (Jan-Jul 2021 → Jan-Jul 2023, 7m, 2y)
sy2022_sm01_w7m_off1   (Jan-Jul 2022 → Jan-Jul 2023, 7m)
sy2021_sm03_w6m_off1   (Mar-Aug 2021 → Mar-Aug 2022, 6m)
sy2021_sm09_w6m_off1   (Sep 2021-Feb 2022 → Sep 2022-Feb 2023, 6m)
sy2021_sm01_w4m_off1   (Jan-Apr 2021 → Jan-Apr 2022, 4m)
sy2022_sm03_w4m_off1   (Mar-Jun 2022 → Mar-Jun 2023, 4m)
```

본 선정은 시작월·시작연도·윈도우 길이의 세 차원에서 분산을 두어
"유리한 panel 만 골랐다"는 의심을 차단한다.

## 4.9 Cohort / cluster 분해 정의 (§5.7 ~ §5.8 의 분석 단위)

§5.7 의 업력·신규고객 cohort 분석과 §5.8 의 cluster 요인분석은 다음
정의를 따른다.

**업력(tenure) cohort.** 각 점포의 영업 개시일 기준 panel feature 시
작일까지의 개월 수 (`tenure_months`) 를 계산하고, panel 안에서 4 분위
로 나눠 `Q1_short` (가장 짧음) ~ `Q4_long` (가장 김) 의 4 개 cohort 를
정의한다. 본 연구의 대표 7 개 panel 에서 Q1_short 중앙 업력은 6 ~ 11
개월, Q4_long 중앙 업력은 약 113 ~ 122 개월이다 (`260430_claude/outputs/
tables/age_cohort_nc_effect.csv`).

**신규고객 slope (`nc_slope`).** §4.4 의 `nc_slope` 피처. feature window
안에서 점포별 주간 신규 고객 수 시계열에 OLS 기울기를 회귀해 정규화한
값이다. 값이 양수일수록 feature window 안에서 신규 유입이 증가하는
점포, 음수일수록 감소하는 점포다.

**Cohort 별 logit 계수.** 각 panel × tenure cohort 에 대해 다음
이항 로지스틱 회귀를 적합한다.

```
logit P(growth) = β_0 + β_1 · nc_slope
```

여기서 `growth = 1` 은 outcome_3 = Growth 인 경우다. 본 회귀의 회귀
계수 `β_1` (이하 `logit_coef_nc_slope`) 가 cohort 별로 어떻게 다른지가
§5.7 의 핵심 결과다.

**KMeans cluster.** §4.5 의 B 모델과 동일한 KMeans (k=6, n_init=10,
seed=42) 출력을 cluster_id 로 사용한다. 각 cluster × G/S/D 의
교차표 ratio (Decline / Stable / Growth) 가 §5.8 의 핵심 결과다.

**Cluster 내 macro-F1.** §4.5 의 D 모델 (hybrid 56 피처) 의 5-fold CV
예측값을 cluster 단위로 분리해 macro-F1 을 다시 계산한 것이다. 본
값은 cluster 별 모델 난이도를 보여주는 진단 지표이며 학습된 모델의
fold-out 예측을 다시 stratify 한 결과다 (`260430_claude/outputs/tables/
cluster_outcome_summary.csv`).

## 4.10 Cost-sensitive 보조 실험 프로토콜

§1.4 의 기여 3-(b) 에 해당하는 보조 실험이다. §4.5 의 D 모델 (hybrid
56 피처) 위에서 RandomForest 의 `class_weight` 만을 바꾸는 세 가지
변형을 비교한다.

| 코드 | `class_weight` | 의미 |
| --- | --- | --- |
| R1_none | `None` | 가중 없음, raw multi-class log-loss |
| R2_balanced | `"balanced"` | 클래스 빈도의 역수로 균등 가중 (step05 의 기본) |
| R3_cost_decline3 | `{Decline:3, Stable:1, Growth:1}` | Decline 에 3 배 가중 |

R3 의 Decline 가중치 3 은 §4.5 의 paired 분석에서 라벨 편중 panel 의
Decline recall 이 0.30 안팎까지 떨어진 점을 근거로 한 single-step
choice 다 (1 ~ 5 의 더 정교한 grid 는 §6.5 future work).

대표 6 panel (`sy2021_sm01_w3m_off1`, `sy2021_sm03_w3m_off1`,
`sy2022_sm03_w3m_off1`, `sy2021_sm01_w4m_off1`, `sy2021_sm01_w7m_off1`,
`sy2022_sm01_w7m_off1`) 에서 동일한 Stratified 5-fold CV (seed=42) 로
macro-F1, Decline precision/recall/F1 을 측정한다. R3 vs R2 의 paired
t-test 도 함께 보고한다 (자유도 4). 산출은 `260430_claude/outputs/
tables/cost_sensitive_compare.csv`.

## 4.11 재현 절차

```
cd /home/hyeoky98/kcd
python 260430_claude/src/step01_build_seasonal_panels.py
python 260430_claude/src/step02_relabel_gsd_calendar.py
python 260430_claude/src/step03_extract_features.py
PYTHONUNBUFFERED=1 python -u 260430_claude/src/step04_evaluate_seasonal_baseline.py
PYTHONUNBUFFERED=1 python -u 260430_claude/src/step05_train_main_model.py
PYTHONUNBUFFERED=1 python -u 260430_claude/src/step05c_cost_sensitive.py
python 260430_claude/src/analysis_cluster_outcome.py
```

총 wall clock 은 8-core 기준 약 50 ~ 70 분이며 step04 가 가장 오래
걸린다. 모든 random seed 는 42 로 고정되어 있다.
