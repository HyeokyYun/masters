# 4. 연구방법 (v3, top-tier 정합)

본 장은 여섯 가지 기여에 대응하는 분석 방법을 체계적으로 제시한다. 4.1절은 전체 분석 프레임의 개요를, 4.2절은 생존 편향 정량화(C1) 설계를, 4.3절은 Kaplan-Meier·Cox PH 생존 분석을, 4.4절은 Volatility paradox 분해(C2) 설계를, 4.5절은 Golden Cross 인과 식별(C3) 설계를, 4.6절은 Hybrid prediction(C4)과 EWS artifact(C5) 구축을, 4.7절은 LEVI 설계와 외부 검증(C6)을, 4.8절은 robustness 검토를 다룬다.

## 4.1 분석 프레임 개관

본 연구의 전체 분석은 Design Science Research(Hevner et al. 2004; Peffers et al. 2007)의 build–evaluate 사이클을 따른다. 구체적으로 (a) build 단계에서는 주별 거래 데이터로부터 상태 레이블·feature·예측 모델·EWS artifact를 구축하고, (b) evaluate 단계에서는 내부 성능 평가(prediction metrics, cost-sensitive analysis)와 외부 타당성 평가(서울시 공개 데이터 기반 cross-validation)를 병렬 수행한다. 본 설계는 단순 예측 모델링에 비해 두 가지 점에서 차별화된다. 첫째, survivorship bias·volatility paradox 같은 **이론적 반증·조정** 결과를 artifact 개발 과정 안에 삽입하여 "모델 성능" 이상의 학문적 기여를 추출한다. 둘째, external validation을 artifact 평가의 필수 조건으로 배치하여 단일 민간 패널의 externality 약점을 체계적으로 보완한다.

## 4.2 Survivorship Bias 정량화 (C1)

### 4.2.1 정의와 측정

분석 패널(observed-window)의 정의인 "관측 창 중 최소 52주 이상 관측된 점포"를 기준으로 모집단을 두 집단으로 나눈다.

- $S_{\text{panel}}$ : 패널 포함 집단 (n=48,980)
- $S_{\text{excluded}}$ : 패널 미포함 집단 — 관측이 52주 미만이거나 첫 관측 이전에 폐업한 경우 (n=10,027)

각 집단의 폐업 여부는 KCD 메타 데이터의 `is_closed` 필드와 원자료 인허가 폐업일의 교차 검증으로 산출된다. 두 집단의 폐업률을 각각 $\pi_{\text{panel}}$, $\pi_{\text{excluded}}$로 정의하고, 그 비율 $\pi_{\text{excluded}} / \pi_{\text{panel}}$을 **survivorship bias 격차 비율**로 보고한다.

### 4.2.2 민감도

패널 포함 기준(52주)을 26주·78주·104주로 변경한 경우의 격차 비율 변동도 함께 보고한다(부록 C). 격차의 방향성과 크기 등급이 기준에 대해 강건한지 확인하기 위함이다.

## 4.3 Kaplan-Meier · Cox PH 생존 분석

### 4.3.1 생존 함수와 log-rank 검정

Kaplan-Meier 추정치 $\hat{S}(t) = \prod_{t_j \leq t} \left(1 - \frac{d_j}{n_j}\right)$ 를 outcome_3 그룹과 업종(depth_2) 그룹에 대해 각각 계산하고, log-rank 검정으로 그룹 간 차이를 평가한다. 검정 통계량과 자유도·p-value를 보고한다.

### 4.3.2 Cox Proportional Hazards

Cox PH 모형으로 다음 공변량의 hazard ratio를 추정한다:

$$
h_i(t) = h_0(t) \exp\big(\beta_1 \text{nc\_rate}_i + \beta_2 \text{cv}_i + \beta_3 \text{slope\_early\_mm}_i + \beta_4 \text{slope\_late\_mm}_i + \beta_5 r^2_{\text{early},i} + \beta_6 \text{mdd}_i + \beta_7 \text{trend\_slope}_i\big)
$$

모형 적합도는 concordance index로 평가하고, 비례위험 가정은 Grambsch-Therneau(1994) 방식의 Schoenfeld 잔차 기반 검정으로 확인한다(부록 B 표).

## 4.4 Volatility Paradox 분해 (C2)

### 4.4.1 네 가지 가설

§5.4에서 보일 Cox HR(cv) > 1과 단면 통계 Growth cv > Stable cv의 공존을 조정하기 위해, 다음 네 가설을 차례로 검정한다.

- **H1 Survivorship**: 생존자만 vs 폐업 포함 전체 비교로 bias 기여 분리
- **H2 Phase-dependent**: 관측 창을 w1-15, w16-30, w31+의 3단계로 나누어 phase별 cv × outcome 교차표 생성
- **H3 Inverted-U**: cv를 decile로 구간화하여 각 decile의 Growth rate, Decline rate, Closure rate 계산
- **H4 Outcome-stratified Cox**: Growth/Stable/Decline 각 부분집합에 Cox PH를 개별 적합하여 cv HR을 재추정

### 4.4.2 재해석 규칙

네 가설이 모두 paradox의 일부만 설명할 경우, 총체적 해석은 phase·outcome·survivorship의 **3중 상호작용**이다. 이 재해석은 변동성을 단조 risk factor로 보는 기존 관행을 수정하는 이론적 기여로 정리된다.

## 4.5 Golden Cross 인과 삼각 검증 (C3)

### 4.5.1 Granger Causality (점포 수준 VAR)

각 점포 i에 대해 다음 VAR(1) 모형을 적합하고 nc_rate → log(sales)의 Granger 유의성을 개별 검정한다.

$$
\begin{cases}
\log(\text{sales}_{i,t}) = \alpha_{i,1} + \sum_{\ell=1}^{p} \beta_{i,\ell} \log(\text{sales}_{i,t-\ell}) + \sum_{\ell=1}^{p} \gamma_{i,\ell} \text{nc}_{i,t-\ell} + \epsilon_{i,t,1} \\
\text{nc}_{i,t} = \alpha_{i,2} + \sum_{\ell=1}^{p} \delta_{i,\ell} \log(\text{sales}_{i,t-\ell}) + \sum_{\ell=1}^{p} \eta_{i,\ell} \text{nc}_{i,t-\ell} + \epsilon_{i,t,2}
\end{cases}
$$

점포 3,000개 표본에서 nc→sales 유의 비율, sales→nc 유의 비율, 비대칭(nc만 유의) 비율을 보고한다. Granger는 약한 인과 단서이므로, 아래 두 방법으로 triangulate한다.

### 4.5.2 Propensity Score Matching + Difference-in-Differences

"Golden Cross" 처치를 다음과 같이 정의한다: 점포 i의 nc_rate 4주 이동평균이 그 직전 4주 평균을 유의하게 상향 돌파하는 주(week)가 관측 기간 내 적어도 1회 발생한 경우 처치군(treated), 아니면 통제군(control)으로 분류한다.

- 처치 선택 모형: 점포 수준 공변량(업종, 면적, 개업월, 초기 slope 등)의 로지스틱 회귀로 propensity score 추정
- Matching: nearest-neighbor, caliper 0.1, 1:1 매칭 (enhanced PSM은 후속)
- DiD: 처치 전후 4주 평균 log-sales 차이의 처치군-통제군 차이

ATT를 주요 추정치로, t-통계량·p-value·샘플 크기를 함께 보고한다.

### 4.5.3 Panel Two-way Fixed Effects Regression

점포·시간 고정효과를 모두 통제한 패널 회귀:

$$
\log(\text{sales}_{i,t}) = \alpha_i + \lambda_t + \sum_{\ell \in \{1,2,4\}} \beta_\ell \text{nc}_{i,t-\ell} + \theta \log(\text{sales}_{i,t-1}) + \epsilon_{i,t}
$$

$\beta_\ell$ 계수는 "점포와 시기의 고정된 이질성을 제거한 뒤 신규 고객 비율의 시차 효과"로 해석된다. n=988,698 store-weeks, 10,000 stores 표본에서 계수·표준오차·p를 보고한다.

### 4.5.4 삼각 검증 해석 규칙

세 방법이 같은 방향을 지지할 때에만 "선행 관계 존재"로 해석한다. 인과 규명은 여전히 random assignment 수준에 미치지 못하므로, 모든 서술은 "evidence consistent with a causal interpretation" 수준으로 제한한다.

## 4.6 Hybrid Prediction (C4)과 EWS Artifact (C5)

### 4.6.1 Outcome label과 관측 창

30주 조기 예측을 목표로 한다. 각 점포의 첫 30주 관측에서 feature를 추출하고, 해당 점포의 장기 outcome (Growth/Stable/Decline 3-class, §3.2.2의 정의)을 예측한다. 5-fold stratified cross-validation으로 macro F1·weighted F1·AUC(ovr)·class-specific precision/recall을 산출한다.

### 4.6.2 Feature 구성

네 가지 feature 묶음:

- **46 engineered features**: 매출 수준·추세·변동성·신규 고객·시간대·요일·계절성 등 하드-엔지니어링된 통계량
- **KMeans cluster one-hot** (K=4): 주별 매출 normalized 시계열을 Euclidean 거리 기반 KMeans로 K=4 군집화한 후 one-hot 인코딩
- **Change-point features**: 점포별 slope break 탐지(이동평균 교차 기반)와 그 시점·강도 요약
- (대체 지표) **K-shape cluster** one-hot(K=7): Paparrizos & Gravano(2015) 방법, robustness용

### 4.6.3 Proposed Model D 아키텍처

"Hybrid Proposed D" = 46 engineered features $\oplus$ KMeans one-hot $\oplus$ change-point features 를 입력으로 하는 LightGBM 분류기.

- 하이퍼파라미터: n_estimators=500, learning_rate=0.05, max_depth=6, num_leaves=31, colsample_bytree=0.8, subsample=0.8
- 클래스 가중치: 불균형 고려 (balanced)
- 평가: 5-fold stratified CV, confusion matrix per class

비교군:
- **A_base_46** (46 engineered만), **B_base_cluster** (46 + cluster), **C_base_cp** (46 + change-point), **D_base_cluster_cp** (Proposed, 46 + cluster + cp)

### 4.6.4 Deep Sequence Baseline (보조)

Multivariate LSTM (2-layer BiLSTM, hidden 64), BiGRU (2-layer, hidden 64), Transformer Encoder (d_model=32, 2 heads, 2 layers)를 동일 30주 × 5채널 입력으로 재학습. 본 석사 논문에서는 legacy label 기반 결과를 부록 표로만 제시하며, 주 비교는 Hybrid A-D에 고정한다.

### 4.6.5 EWS Artifact 구축

Proposed Model D의 5-fold out-of-fold 확률을 store-level risk score $r_i \in [0, 100]$로 선형 매핑한다.

$$r_i = 100 \cdot \Pr(\text{outcome}_i = \text{Decline} \mid x_i)$$

Average Precision, Brier score, reliability curve로 calibration을 평가한다.

### 4.6.6 Cost-Sensitive Threshold

Benefit-cost 파라미터 $B_{prevent}$(진양성 이득), $C_{support}$(위양성 비용), $C_{miss}$(위음성 비용)를 정의하고 net utility 함수를 도입한다.

$$U(\tau) = B_{prevent} \cdot \text{TP}(\tau) - C_{support} \cdot \text{FP}(\tau) - C_{miss} \cdot \text{FN}(\tau)$$

본 연구는 $B_{prevent}=10, C_{support}=2, C_{miss}=8$을 기본 parameterization으로 사용하며 sensitivity는 robustness에서 제시한다. 최적 $\tau^*$와 해당 operating point의 precision·recall·flagged percentage를 보고한다.

## 4.7 LEVI 설계와 외부 검증 (C6)

### 4.7.1 LEVI 정의

자치구 $g$의 LEVI를 다음과 같이 정의한다.

$$\text{LEVI}^{V1}_g = \frac{G_g - D_g}{N_g}$$

여기서 $G_g, D_g, N_g$는 구 $g$에 속한 observed-window 점포의 Growth·Decline·전체 수이다.

대안 공식 4종(V2 log-odds, V3 평균 추세, V4 중앙값 추세, V5 shrinkage)을 함께 구축하고 공식 간 상관을 robustness로 보고한다.

### 4.7.2 외부 거시 변수

- **서울시 생활인구**: 자치구 단위 월평균 생활인구 $\text{lp\_mean}_g$, 2021-01 → 2023-08 변화율 $\text{lp\_pctchg}_g$
- **외식업 폐업률**: 서울시 일반음식점 인허가 정보로부터 자치구 $\times$ 월별 폐업률 $\text{closurerate}_{g,m}$을 구성하고 월평균을 취함
- **상권 추정매출**: 서울시 상권분석서비스(추정매출-상권배후지)의 분기별 매출을 자치구 단위로 집계

### 4.7.3 상관 분석

LEVI와 각 외부 변수의 Pearson·Spearman 상관을 보고한다. 25개 자치구는 서울시의 전수이므로 표본 추출 문제가 없으며 **효과 크기**가 해석의 중심이다. 분기별 패널(n=11 분기)에서 KCD 매출 QoQ 변화 vs 외부 QoQ 변화의 상관도 시간 축에서 확인한다.

## 4.8 Robustness 설계

네 축에서 체계적 민감도 분석을 수행한다.

- **Outcome cutoff 민감도**: Growth/Decline 컷오프 ±0.3σ, ±0.5σ, ±0.7σ
- **관측 창 민감도**: 최소 관측 주수 52, 78, 104주
- **LEVI 공식 민감도**: V1-V5 5개 공식
- **업종·하위기간 일관성**: 일반음식점·술집·카페 3개 업종, 코로나기(2021-01~2022-04)·엔데믹기(2022-05~2023-08) 2개 하위기간

모든 민감도 결과는 §5.10과 부록 C에 수록한다.

---

### 요약

본 장은 여섯 기여 C1-C6에 각각 대응하는 분석 방법을 제시했다. 각 방법은 독립적 검증이 가능하지만, Design Science Research의 build-evaluate 사이클 안에서 서로를 강화한다. 다음 장은 여섯 기여를 순서대로 보고한다.
