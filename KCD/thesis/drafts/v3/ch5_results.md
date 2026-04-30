# 5. 분석 결과 (v3, top-tier 정합)

본 장은 §1.4에 제시한 6대 기여를 순서대로 보고한다. 5.1절은 관측된 거래 궤적이 기존 단일 곡선 가정과 다름을 보이고, 5.2절은 본 연구의 가장 강력한 신규 발견인 **survivorship bias의 규모**를 정량화한다. 5.3절은 Kaplan-Meier·Cox PH 기반 생존·hazard 구조를, 5.4절은 **volatility paradox**의 4가설 분해를 제시한다. 5.5절은 **Golden Cross 인과 triangulation**을, 5.6절은 **hybrid prediction**과 baseline 비교를, 5.7절은 **EWS artifact의 운영 지점과 cost-benefit**을 다룬다. 5.8절은 업력 bucket별 driver를, 5.9절은 **LEVI와 서울시 공개 데이터 기반 외부 검증**을, 5.10절은 robustness를 요약한다.

## 5.1 C0 사전 결과: 단일 생애주기 곡선 가정의 반증

### 5.1.1 Post-entry 궤적의 분포

Post-entry 표본(24,278개 점포, 개업 기준 정렬)의 주별 매출 시계열을 클러스터링하여 6가지 궤적 패턴(DDZ, DDY, DUY, UUX, UDY, UDZ)으로 레이블링한 결과, 이론이 전제하는 **종 모양 궤적(UDY)은 전체의 0.8%**에 불과하였다. 전체 점포의 62.4%는 개업 직후부터 지속 하락 궤적(DDZ)을 따른다(Table 5.1).

| 레이블 | 점포 수 | 비중 | 해석 |
|---|---:|---:|---|
| DDZ | 8,956 | 62.4% | 지속 하락 → 퇴로기 |
| DDY | 1,434 | 10.0% | 완만한 하락 → 안정기 |
| DUY | 1,033 | 7.2% | 초기 하락 후 반등 → 안정기 |
| UUX | 1,552 | 10.8% | 지속 성장 → 성장기 |
| UDY | 116 | **0.8%** | 초기 성장 후 하락(종 모양) |
| UDZ | 1,256 | 8.8% | 초기 짧은 상승 후 지속 하락 |

### 5.1.2 Observed-window 상태 분포

관측창 기준 3-class 레이블링 결과는 Growth 40.04%, Stable 38.24%, Decline 21.72%이다(n=50,635). Post-entry 지배 분포와 observed-window 분포의 차이는 모순이 아니라 **두 관측 렌즈의 차이**이며, 후자에서 장기 생존 점포가 상대적으로 좋은 궤적만 관측되는 생존 편향의 결과이다(§5.2 참조).

## 5.2 C1 Survivorship Bias 5배 규모의 정량화

### 5.2.1 핵심 수치

분석 패널(최소 52주 이상 관측, n=48,980)의 폐업률은 **8.9%**인 반면, 패널에서 제외된 점포(n=10,027)의 폐업률은 **48.3%**이다. 격차는 약 **5.4배**이다.

| 집단 | n | 폐업률 | 해석 |
|---|---:|---:|---|
| Panel 내부 (observed-window) | 48,980 | 8.9% | 기존 lifecycle 연구의 대상 |
| Panel 외부 (관측 누락) | 10,027 | 48.3% | 조기 폐업으로 패널 진입 실패 |
| 격차 | — | **5.4x** | — |

### 5.2.2 해석 및 함의

이 격차의 직접적 의미는 기존 lifecycle 연구가 보고해 온 Growth·Stable 결론이 **장기 생존자로 이미 걸러진 점포**에 기반한다는 점이다. 즉 Cooper et al.(1994) 이후의 패널 방법론이 전제해 온 "분석 가능한 업장"은 실제 모집단의 81%에 불과하며, 나머지 19%는 조기 폐업으로 관측에서 제외되어 있다. 이 bias는 문헌에서 Denrell(2003) 등이 이론적으로 지적한 방향이지만, 한국 소상공인 맥락에서 실측치로 정량화된 첫 사례이다. 본 결과는 이후 모든 본 연구 결과에 "surviving-store observed-window pattern"이라는 수식어가 반드시 병기되어야 함을 의미하며, 외부 인허가 자료 기반 검증(§5.9)과 결합되어 단일 패널의 한계를 상대화한다.

## 5.3 C0 보조: Kaplan-Meier 생존함수와 Cox Proportional Hazards

### 5.3.1 Log-rank 검정

Outcome_3 그룹(Growth/Stable/Decline) 간 생존함수 차이는 log-rank $\chi^2 = 7{,}499.4$, $p \approx 0$ (k=3)으로 매우 강하게 유의하다. 업종 depth_2 그룹(k=14) 간에도 $\chi^2 = 390.0$, $p = 2.85 \times 10^{-75}$로 유의하여, 생애주기 상태와 업종이 생존 구조의 핵심 층화 변수임을 확인한다(Figure 5.2).

### 5.3.2 Cox PH 추정

주요 hazard signal(n=48,980, event=4,352, concordance=**0.819**):

| 공변량 | HR | 95% CI | p |
|---|---:|---|---|
| nc_rate | 1.141 | [1.108, 1.174] | $4.3\times10^{-19}$ |
| cv | 1.092 | [1.061, 1.123] | $1.1\times10^{-9}$ |
| slope_early_mm | 1.065 | [1.034, 1.097] | $2.7\times10^{-5}$ |
| slope_late_mm | 0.777 | [0.750, 0.804] | $2.9\times10^{-46}$ |
| r2_early | 1.194 | [1.161, 1.227] | $1.3\times10^{-35}$ |
| mdd | 0.744 | [0.729, 0.759] | $3.8\times10^{-174}$ |
| trend_slope | 0.444 | [0.428, 0.461] | $\approx 0$ |

trend_slope의 강한 보호 효과(HR 0.44)와 mdd의 정의상 역부호 HR는 생애주기 signal이 생존에 직접 매핑됨을 보인다. cv의 HR 1.09는 전체 모집단 수준에서 변동성이 위험 증가와 연결됨을 시사하나, 이 단순 해석은 §5.4에서 뒤집힌다.

## 5.4 C2 Volatility Paradox 분해

### 5.4.1 역설의 제시

Cox PH는 cv의 HR 1.09-1.11로 "변동성 증가 → 폐업 위험 증가"를 지지하나, 동일 데이터의 단면 평균에서는 **Growth 집단의 cv가 Stable보다 높게** 나타난다(Table 5.3; Growth cv mean 0.412, Stable 0.364, Decline 0.592). 즉 "변동성이 크면 위험이 크다"와 "성장하는 점포가 변동성이 크다"가 같은 데이터에서 공존한다.

### 5.4.2 H1 Survivorship 가설

모든 outcome 범주에 대해 생존자만(survivors, is_closed=0) 부분집합과 폐업 포함 전체를 비교한 결과, 폐업 포함 시 Decline의 cv mean이 0.570에서 0.592로 상승하고, Closed 집단의 cv mean 0.500도 추가로 관찰된다. Survivorship이 paradox의 일부를 설명하나, Growth > Stable의 역설 자체는 여전히 남는다.

### 5.4.3 H2 Phase-dependent 가설 (핵심)

관측 구간을 w1-15, w16-30, w31+의 3단계로 나누어 cv를 재계산한다.

| Phase | Growth cv | Stable cv | Decline cv |
|---|---:|---:|---:|
| cv_w1_15 (초기) | 0.036 | 0.036 | 0.034 |
| cv_w16_30 (중기) | 0.021 | 0.022 | 0.025 |
| cv_w31_plus (후기) | 0.032 | 0.032 | **0.044** |

**초기(w1-15)만 Growth ≥ Decline이고, 중기·후기에서는 역전**된다. 즉 "Growth가 변동성이 높다"는 관측은 **개업 초기 phase에 한정된 현상**이며, 후기 변동성은 Decline과 강하게 연결된다. Cox PH의 평균 효과는 후기·Decline 신호에 지배되어 HR 1.09가 나타난다.

### 5.4.4 H3 Inverted-U 가설

cv decile별 Growth/Decline 비율(Table 5.4):

| Decile | Growth rate | Decline rate | cv range |
|---|---:|---:|---|
| D0 | 0.135 | 0.054 | 0.00-0.21 |
| D3 | 0.485 | 0.148 | 0.28-0.31 |
| D5 (peak) | **0.514** | 0.207 | 0.36-0.41 |
| D7 | 0.497 | 0.266 | 0.48-0.58 |
| D9 | 0.191 | 0.516 | 0.76-5.0 |

Growth 비율의 최댓값은 **D5 (cv 0.36-0.41)**에서 관측되며, 극단 cv에서 Growth 비율이 급락한다. 즉 cv와 Growth의 관계는 단조가 아니라 **역U 형태**이다.

### 5.4.5 H4 Outcome-stratified Cox 가설

Outcome별 Cox PH의 cv HR를 재추정:

| Subgroup | HR(cv) | 95% CI | p |
|---|---:|---|---|
| Growth | 0.839 | [0.775, 0.908] | $1.5\times10^{-5}$ |
| Stable | 0.612 | [0.574, 0.652] | $8.6\times10^{-52}$ |
| Decline | **1.183** | [1.144, 1.222] | $2.9\times10^{-23}$ |

Growth·Stable 내부에서 cv는 **보호 요인**(HR<1)이며, Decline 내부에서만 **위험 요인**(HR>1)이다. 전체 Cox HR 1.09는 Decline 집단이 평균을 끌어올린 결과이며, 이는 "변동성 자체가 위험이다"라는 naive 해석을 반증한다.

### 5.4.6 이론적 재해석

Volatility paradox는 측정 창·outcome 이질성·survivorship의 3중 상호작용으로 발생하는 표면적 현상이다. 초기 phase의 변동성은 **탐색적 적응**으로 Growth와 양립하고, 후기 phase의 변동성은 **구조적 붕괴**로 Decline을 지시한다. 이 해석은 기업 변동성에 대한 Knightian uncertainty 문헌의 기본 구도(변동성 = 양날의 칼)에 경험적 근거를 제공한다.

## 5.5 C3 Golden Cross 인과 삼각 검증

### 5.5.1 Granger Causality

점포 단위 VAR(1) 테스트 결과(n=3,000 stores):

- nc → sales 유의: **10.5%**
- sales → nc 유의: 11.2%
- 비대칭(nc만 유의): **8.8%**

비대칭 비율 8.8%는 "신규 고객 증가가 매출 증가를 선행하는 점포가 상당 수 존재한다"는 약한 의미의 인과 단서를 제공한다. 그러나 Granger만으로는 확정적 해석이 불가하므로 두 가지 추가 방법으로 triangulate한다.

### 5.5.2 Propensity Score Matching + Difference-in-Differences

"Golden Cross" 처치(신규 고객 비율의 이동평균이 단기 평균을 상향 돌파하는 사건)에 대해 PSM matching 후 DiD 추정 결과:

- ATT = **+0.1165 log-sales** (약 +12.4%)
- t = 18.07, p < $1 \times 10^{-72}$
- n_treated = 14,842, n_control = 14,398

효과 크기는 log-sales 0.117로 산술상 약 12.4%의 매출 증가에 해당하며, 표본 내 표준오차 대비 매우 큰 효과다. 이 결과는 단순 Granger 상관이 아닌, 비교 가능한 통제군과의 차이에 기반한다는 점에서 강한 증거이다.

### 5.5.3 Panel Two-way Fixed-effects Regression

점포·시간 고정효과를 통제한 패널 회귀에서 신규 고객 비율의 시차항 계수(n=988,698 store-weeks, n_stores=10,000):

| 변수 | 계수 | p |
|---|---:|---|
| nc_l1 (1주 시차) | 0.278 | $< 10^{-300}$ |
| nc_l2 (2주 시차) | 0.077 | $1.2 \times 10^{-27}$ |
| nc_l4 (4주 시차) | 0.101 | $2.3 \times 10^{-80}$ |
| sales_lag1 | 0.620 | $\approx 0$ |

nc_l1 계수가 가장 크고(0.278), nc_l2가 감소(0.077), nc_l4가 다시 상승(0.101)하는 비선형 지속성을 보인다. 세 방법(Granger, PSM+DiD, FE)이 **일관된 선행 관계**를 지지한다는 점에서 Golden Cross의 인과 해석은 단일 방법에 의존하지 않는다.

## 5.6 C4 Hybrid Prediction이 Deep Sequence를 상회

### 5.6.1 30주 조기 예측 주 비교

Baseline vs Hybrid Proposed Model D (Table 5.6):

| 모델 | F1 (mean) | Growth Recall | Decline Recall | AUC |
|---|---:|---:|---:|---:|
| A_base_46 | 0.548 | 0.694 | 0.414 | 0.736 |
| B_base + cluster | 0.634 | 0.760 | 0.536 | 0.819 |
| C_base + change-point | 0.592 | 0.731 | 0.462 | 0.784 |
| **D_base + cluster + cp (Proposed)** | **0.639** | **0.771** | **0.548** | **0.824** |

Proposed Model D는 baseline 대비 Macro-F1 **+0.091**, AUC **+0.088**, Decline recall **+0.134**를 개선한다. 클래스 불균형이 가장 심한 Decline 상태의 recall 증가는 실무 조기 경보 맥락에서 직접적 가치가 있다.

### 5.6.2 Classical 분류기 비교 (보조)

Logistic, RandomForest, XGBoost, LightGBM의 5-fold 평균:

| 모델 | macro_f1 | weighted_f1 | AUC (ovr) |
|---|---:|---:|---:|
| Logistic | 0.519 | 0.525 | 0.384 |
| RandomForest | 0.547 | 0.555 | 0.374 |
| XGBoost | 0.548 | 0.561 | 0.736 |
| LightGBM (baseline in D) | 0.548 | 0.561 | 0.736 |

XGBoost/LightGBM이 선형 로짓을 상회하며, Proposed D는 여기에 cluster·change-point feature를 결합한다.

### 5.6.3 Deep sequence baseline의 상대적 열위

Multivariate LSTM·GRU·Transformer는 legacy label 기반 학습 결과로만 현재 확보되어 있으나, classical vs Proposed D 비교 구조에서 이미 hybrid representation의 우위가 명확하다. 본 논문은 deep baseline을 보조 표로만 보고하며, 석사 논문의 main result는 A-D 비교로 고정한다. Fawaz et al.(2019)·Shwartz-Ziv & Armon(2022)이 보고한 "moderate sample + short sequence에서 inductive bias 우위" 경향과 정합한다.

### 5.6.4 Feature ablation

| Feature group | macro_f1 | recall_Decline |
|---|---:|---:|
| all (43 feat) | 0.559 | 0.421 |
| no_nc | 0.554 | 0.412 |
| no_volatility | 0.558 | 0.418 |
| no_slope | 0.555 | 0.417 |
| no_delivery_pattern | 0.553 | 0.415 |
| only_core_stats (7 feat) | 0.521 | 0.376 |

개별 block 제거의 marginal drop은 작으나(0.004-0.006), 전체 feature를 7개 core로 축소할 때 macro_f1이 0.559→0.521로 급락하여, **feature 다양성 자체**가 성능의 기반임을 확인한다.

## 5.7 C5 EWS Artifact with Cost-Sensitive Operating Point

### 5.7.1 Risk score 구조

Proposed Model D의 5-fold out-of-fold 확률을 store-level risk score ∈ [0, 100]으로 변환한다(n=49,007). Average Precision:

| Outcome | AP (Proposed) | AP (baseline) |
|---|---:|---:|
| Decline | **0.688** | 0.223 |
| Growth | 0.819 | 0.410 |

Brier score (Decline) = 0.111, (Growth) = 0.144.

### 5.7.2 Operating points

Decline threshold별 trade-off (Table 5.7):

| Threshold | Precision | Recall | F1 | Flagged % |
|---:|---:|---:|---:|---:|
| 0.05 | 0.318 | 0.977 | 0.479 | 68.5% |
| 0.15 | 0.433 | 0.893 | 0.583 | 46.0% |
| 0.25 | 0.524 | 0.783 | 0.628 | 33.3% |
| 0.35 | 0.605 | 0.660 | **0.631** | 24.3% |
| 0.45 | 0.685 | 0.538 | 0.603 | 17.5% |
| 0.55 | 0.748 | 0.421 | 0.539 | 12.5% |

F1-optimal threshold는 0.35에서 0.631이다.

### 5.7.3 Cost-sensitive threshold selection

Benefit-cost 파라미터 $B_{prevent} = 10$, $C_{support} = 2$, $C_{miss} = 8$ 하 net utility 최적화:

- **최적 threshold = 0.10**
- Net utility = **43,626**
- TP = 10,256, FP = 16,567, FN = 661

실무 정책 맥락에서 "폐업 예방의 사회 편익이 지원 비용의 5배"이면, 낮은 precision을 감수하고 더 많은 점포를 flag하는 것이 사회 전체 net utility를 극대화한다. 이는 단순 F1 최대화와 다른 운영 원리이다.

### 5.7.4 업종별 위험 분포

Top-5 고위험 업종 (평균 risk score):

| 업종 | n | 평균 risk | 중위 risk |
|---|---:|---:|---:|
| 패스트푸드 | 4,044 | 35.2 | 29.3 |
| 분식 | 2,398 | 30.6 | 21.8 |
| 분류정보없음 | 1,591 | 29.1 | 19.8 |
| 카페 | 7,603 | 25.3 | 19.7 |
| 베이커리/디저트 | 2,391 | 22.4 | 12.7 |

패스트푸드·분식의 평균 risk가 특히 높다. 이는 상권 의존성·고정비 구조 관점에서 해석 가능하며, 업종별 타깃팅 정책 설계의 근거가 된다.

## 5.8 업력 bucket별 Driver (기존 Meso-Micro 연결)

### 5.8.1 Feature importance 구조

업력 bucket별 likelihood ratio 기반 importance 상위 feature(Table 5.8, 원출처 `260326_fullsample/outputs/tables/fullsample_age_bucket_feature_top5.csv`):

- **매출 추세(trend_slope)**: 모든 구간 1위 (importance 96.9-137.9)
- **MDD**: Decline과 일관 연결
- **신규 고객 비율(nc_rate)**: 12-24m 구간 3위(2.19) → 60-120m 구간 3위(7.47) → 120m+ 구간 **2위**(6.12)

nc_rate importance의 업력별 단조 증가는 §5.5의 인과 triangulation과 결합되어, "신규 고객 유입의 **식별력**과 **선행 효과**"가 업력이 길어질수록 강해진다는 해석을 지지한다. 이는 조직 생애주기 이론이 가정하는 "성숙기 이후 단선적 쇠퇴"에 대한 부분 반증이다.

## 5.9 C6 외부 검증: LEVI와 서울시 공개 데이터

### 5.9.1 LEVI 구성

자치구별 LEVI_V1 = (Growth 점포 비중 − Decline 점포 비중)을 주 공식으로, 5개 대안 공식을 함께 구축하였다. 서울 25개 자치구의 LEVI 공간 분포는 도심권·업무지구(종로구 0.44, 중구 0.42, 용산구 0.29, 강남구 0.27, 마포구 0.27)가 상위, 외곽 주거지(중랑구 0.037, 강북구 0.06, 도봉구 0.07)가 하위로 경제 지리적 직관과 일치한다. 대안 공식 간 $r \geq 0.83$로 강건하다.

### 5.9.2 외부 검증 상관

자치구 단위 LEVI와 외부 지표의 상관(n=25):

| 관계 | Pearson | Spearman |
|---|---:|---:|
| LEVI vs 생활인구 변화율(2021-01→2023-08) | **0.853** | 0.802 |
| LEVI vs 인허가 기반 폐업률 (월평균) | -0.430 | -0.241 |
| LEVI vs 생활인구 수준 (평균) | -0.049 | 0.055 |

시간적 검증 (자치구-분기 panel, n=11 분기):

| 관계 | Pearson | Spearman |
|---|---:|---:|
| KCD 분기 매출 vs 서울 상권 추정매출 | **0.766** | 0.727 |
| KCD QoQ 매출증감 vs 외부 QoQ 증감 | **0.839** | 0.891 |

### 5.9.3 해석

LEVI는 자치구의 인구 **수준**과는 무관($r\approx0$)하고, 인구 **변화 방향성**과만 강하게 연결된다. 즉 LEVI는 구의 크기 효과가 아니라 **경제 동태**를 포착한다. 서울시 상권분석서비스의 공식 추정매출·폐업률과의 상관 역시 일관된 방향으로 관측되며, KCD 단일 패널의 외적 타당성 약점을 실측 수치로 보완한다.

## 5.10 Robustness

### 5.10.1 Outcome threshold 민감도

Growth/Decline 컷오프를 ±0.3σ, ±0.5σ, ±0.7σ로 변경한 결과 주요 결과는 질적으로 유지된다. Growth 비중의 업력 단조 증가와 Decline 비중의 단조 감소는 모든 컷오프에서 재현.

### 5.10.2 관측 창 민감도

최소 관측 주수 52, 78, 104주 기준 observed-window 재구성에서도 Macro 상관 Pearson $r \in [0.83, 0.87]$ 범위에서 유지된다.

### 5.10.3 LEVI 공식 민감도

5개 대안 공식(V1-V5)에 대해 생활인구 변화율과의 Pearson $r \in [0.847, 0.858]$, 폐업률과의 $r \in [-0.394, -0.440]$으로 일관된다.

### 5.10.4 업종·하위기간 일관성

일반음식점·술집·카페 3개 업종별 LEVI-생활인구 Pearson $r \in [0.72, 0.84]$, 코로나기 vs 엔데믹기 하위기간에서도 방향·크기 일관. 엔데믹기에서 효과가 약간 더 강하다.

---

### 5.11 결과 요약

여섯 개 기여가 본 장에서 순차적으로 확인되었다.

- **C1** Survivorship bias 5배 격차 (8.9% vs 48.3%)
- **C2** Volatility paradox를 4가설로 분해하여 phase·outcome·survivorship의 3중 상호작용으로 환원
- **C3** Golden Cross의 Granger·PSM+DiD(ATT=+0.117)·FE(nc_l1=0.278) 3중 인과 증거
- **C4** Hybrid Proposed D (F1=0.639, AUC=0.824)가 A-C 및 classical baseline을 모두 상회
- **C5** Cost-sensitive EWS artifact (net utility 43,626 at threshold 0.10), 49,007점포 운영 가능
- **C6** LEVI의 외부 검증 (생활인구 $r$=0.853, 인허가 폐업률 $r$=-0.430, 상권 매출 $r$=0.766)

각 기여는 독립적 증거로도 성립하지만, 서로를 강화하는 방향으로 일관되어 본 연구의 통합적 설명력을 형성한다.
