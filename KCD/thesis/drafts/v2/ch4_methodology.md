# 4. 연구방법

본 장은 본 연구의 3단 분석 프레임을 제시한다. 4.1절에서 전체 설계를 개관하고, 4.2-4.4절에서 Micro·Meso·Macro 각 층의 세부 방법론을 서술한다. 4.5절은 robustness 검토 설계를 요약한다.

## 4.1 분석 프레임 개관

본 연구의 분석은 세 층으로 구성된다.

- **Micro (개별 점포)**: 점포-주 단위 거래 데이터로부터 개별 점포의 Growth/Stable/Decline 상태를 진단·예측한다. Post-entry 표본에서는 매출 시계열 궤적 자체를, observed-window 표본에서는 관측된 성장 추세를 기준으로 상태를 정의한다. 각 업력 구간에서 상태를 가르는 드라이버 feature를 파악하고, 초기 관측 기반 조기 예측의 가능성을 평가한다.

- **Meso (자치구)**: Micro 레이어의 개별 상태 레이블을 자치구 단위로 집계한 **지역 경제 활력 지수(Local Economic Vitality Index, LEVI)**를 구축한다. LEVI는 구별 "Growth 점포 비중 − Decline 점포 비중"을 기본 정의로 하며, 본 연구는 5가지 대안 공식을 함께 제시해 선택 민감도를 확인한다.

- **Macro (도시)**: Meso에서 구축한 LEVI가 서울시의 거시 동태(생활인구 변화, 외식업 폐업률)와 어떤 관계를 맺는지 분석한다. 본 연구는 동시 상관 및 시차 상관을 중심으로 검토하며, 인과 주장을 피하고 진단적·예측적 해석을 유지한다.

이 3단 구조는 "점포 단위에서 잘 작동하는 진단이 지역 경제의 leading indicator로 기능할 수 있는가"라는 기술경영적 질문에 답하기 위한 설계이다. 단일 층에서의 결과만으로는 이 질문에 답할 수 없으며, 세 층의 결과가 일관되게 맞물릴 때 비로소 거래 데이터 기반 지역 경제 모니터링의 가능성이 실증된다.

## 4.2 Micro 레이어: 개별 점포 상태 진단·예측

### 4.2.1 Post-entry trajectory 레이블링

Post-entry 표본(§3.2.1)의 각 점포에 대해 주별 매출 시계열(108주 또는 162주)을 min-max 정규화한 후, 동일 시점 전체 점포 매출 합에 대한 비율로 재조정한다. Euclidean 거리 기반 K-Means 클러스터링을 업종·샘플 기간별로 각각 K=9로 실행하고, 각 클러스터의 대표 곡선을 관찰하여 생애주기 패턴 레이블을 부여한다. 레이블 체계는 초기 구간(기간1)·변곡점 이후 구간(기간2)·현재 시점 패턴을 상승(U)/하락(D)·성장(X)/안정(Y)/퇴로(Z) 알파벳 3자리로 표기한다(예: DDZ, UUX). 시범 분석에서 Euclidean K-Means가 K-shape 대비 안정성(seed ARI 0.856 vs 0.320)이 우수함을 확인하여 본 연구의 주 방법으로 사용한다.

### 4.2.2 Observed-window 3-class 상태 레이블링

Observed-window 표본(§3.2.2)의 각 점포에 대해 전체 관측 기간의 월평균 log 매출의 추세 기울기 $s_i^{\text{all}}$을 계산한다. 기울기의 분포 표준편차 $\sigma$를 기준으로 다음과 같이 3-class로 레이블링한다.

$$
y_i = 
\begin{cases}
\text{Growth} & \text{if } s_i^{\text{all}} > +0.5\sigma \\
\text{Decline} & \text{if } s_i^{\text{all}} < -0.5\sigma \\
\text{Stable} & \text{otherwise}
\end{cases}
$$

결과적으로 Growth 40.04%, Stable 38.24%, Decline 21.72%의 분포가 관측된다. 컷오프 ±0.5σ는 ±0.3σ, ±0.7σ 대안과 비교하는 robustness 분석을 수행한다(§4.5, §5.5).

### 4.2.3 업력 구간 구성

각 점포의 첫 관측 시점에서의 업력(개업 이후 경과 개월)을 기준으로 6개 구간 bucket을 정의한다: 0-12, 12-24, 24-36, 36-60, 60-120, 120+개월. 업력 bucket은 소상공인 정책 문헌의 일반적 구분(창업기, 성장기, 성숙기, 쇠퇴기)과 정합하면서도 본 데이터의 관측 분포를 반영하도록 설계되었다.

### 4.2.4 Feature 엔지니어링

각 점포에 대해 다음 네 묶음(feature block)의 변수를 계산한다.

- **Level features**: 평균 주별 매출, 매출 규모 백분위. 이 묶음은 "현재 점포가 얼마나 큰가"를 포착한다.
- **Trend/Volatility features**: `trend_slope`(관측 창 전체의 log 매출 추세 기울기), `mdd`(maximum drawdown), `cv`(coefficient of variation), 잔차 변동성(`vol_resid_rolling12`). 본 연구에서 변동성은 기존 CV가 추세와 혼합되는 문제를 피하기 위해 추세 제거 후 잔차 변동성으로 재정의한다.
- **Customer behavior features**: `nc_rate`(평균 신규 고객 비율), 주말 매출 비중(`weekend`), 오전 매출 비중(`before_noon`), 배달 비중 log(`del_ratio_log`).
- **Local context features**: 자치구 더미, 업종 더미, 점포 면적.

### 4.2.5 모델링

**업력 bucket별 driver 분석 (Multinomial Logit)**. Growth/Stable/Decline을 종속변수로 하는 다항 로짓 모형을 업력 bucket별로 적합시킨다. Stable을 기준 범주로 두고 Growth와 Decline의 log-odds를 추정하여, 각 bucket에서 어떤 feature가 Growth/Decline을 가르는지 확인한다. 본 연구는 계수의 부호·크기보다 feature importance(likelihood ratio 기반)의 구간별 순위 변화에 초점을 둔다.

**조기 예측 (Gradient Boosting)**. XGBoost·GBM 기반 분류기로 초기 $T_{\text{obs}} \in \{20, 30, 40, 50\}$주의 관측만으로 점포의 장기 Growth/Stable/Decline 상태를 예측한다. 데이터는 7:3 층화 표본으로 train/test 분할하고, 클래스 불균형을 고려하여 weighted F1과 macro F1을 주요 평가지표로 사용한다. 평가는 feature block을 점증 추가하는 ablation 방식(`level_only` → `+trend/volatility` → `+customer` → `+local` → `+cluster`)으로 수행한다.

## 4.3 Meso 레이어: LEVI 설계

### 4.3.1 기본 정의

자치구 $g$의 LEVI를 다음과 같이 정의한다. $N_g$는 구 $g$에 속한 KCD observed-window 표본 점포 수, $G_g$·$D_g$는 각각 Growth·Decline 레이블 점포 수이다.

$$
\text{LEVI}^{V1}_g = \frac{G_g - D_g}{N_g}
$$

LEVI_V1은 $[-1, +1]$ 구간에서 해석된다. 값이 클수록 해당 구의 외식업 점포 중 성장 우위가 높다.

### 4.3.2 대안 공식 (robustness)

단일 공식에 결과가 종속되지 않도록 4개의 대안을 함께 구축한다.

- $\text{LEVI}^{V2}_g = \log\left(\frac{G_g + 0.5}{D_g + 0.5}\right)$ : Growth 대 Decline의 로그-오즈
- $\text{LEVI}^{V3}_g = \overline{s_i^{\text{all}}}\big|_{i \in g}$ : 구별 점포의 평균 추세 기울기
- $\text{LEVI}^{V4}_g = \text{median}\{s_i^{\text{all}} : i \in g\}$ : 구별 점포 추세 기울기의 중앙값
- $\text{LEVI}^{V5}_g = \frac{G_g - D_g}{N_g + 20}$ : shrinkage LEVI ($N_g$가 작을 때 0으로 축소)

5개 공식 간 상관이 $r \geq 0.83$ 이상이면 선택 민감도가 낮다고 판단하고 V1을 주 공식으로 확정한다. 이 조건은 본 연구에서 충족됨을 결과(§5.2.1)에서 확인한다.

### 4.3.3 공간·시간 구조

본 연구는 자치구×연구기간 단일 시점에서 LEVI를 계산하는 단면 구조를 기본으로 한다. 즉 LEVI는 2021-01 ~ 2023-08의 관측 창 전체에 대한 하나의 값이다. 단, robustness로 분석 창을 둘로 나눈 (2021H1-2022H1, 2022H2-2023H2) 이기간 LEVI를 구하여 시간적 일관성을 확인한다. 동(dong) 단위 LEVI도 참고지표로 구축하되, 외부 데이터 매칭 한계로 인해 본 논문의 Macro 분석은 구 단위로 고정한다(§3.3.3).

## 4.4 Macro 레이어: LEVI와 도시 동태의 관계

### 4.4.1 거시 변수

분석에 사용하는 거시 변수는 §3.3에서 정의한 두 지표이다.

- `lp_mean`: 구별 월평균 생활인구의 평균 수준(2021-01 ~ 2023-08)
- `lp_pct_change`: 구별 생활인구 증감률(2021-01 → 2023-08)
- `closure_rate_mean`: 구별 월평균 외식업 폐업률의 평균 수준

본 연구의 핵심 가설은 "LEVI가 구별 **동태**를 포착하되 **수준**에는 의존하지 않는다"이다. 이에 따라 `lp_mean`(수준)과 `lp_pct_change`(동태) 모두와 비교하며, LEVI가 전자와 무관하고 후자와 강한 상관을 보이는지 검증한다.

### 4.4.2 상관 분석

자치구(n=25)는 서울시 자치구의 **전수**이므로 표본이 아니라 모집단 자체이다. 따라서 p-value 기반 유의성 검증보다 **효과 크기** 해석이 본 분석의 중심이다. 본 연구는 Pearson 상관과 Spearman 상관을 함께 보고하여 선형성 가정과 순위 기반 robustness 모두를 검토한다.

### 4.4.3 시차·층위 분석

두 가지 보조 분석을 통해 상관의 구조를 검토한다.

- **상·하위 층위 비교**: LEVI 상위 5개 구와 하위 5개 구의 생활인구·폐업률 시계열을 각각 평균해 비교한다. 수준 차와 동태 차 모두를 시각화한다(Figure 5.x).
- **시차 분석**: LEVI는 2021-01~2023-08 단면값이지만, 생활인구 변화율은 월단위 dynamics를 갖는다. 분석 창을 반으로 나눈 LEVI(1H, 2H)와 해당 기간의 생활인구 변화율의 조합 상관을 보조적으로 계산하여, LEVI가 동시 동태인지 시차 동태인지를 탐색한다.

## 4.5 Robustness 설계

본 연구의 robustness는 네 축에서 수행된다.

- **레이블 컷오프 민감도**: Growth/Stable/Decline 컷오프를 ±0.3σ, ±0.5σ, ±0.7σ로 변경해 주요 결과 재현
- **관측 창 민감도**: 최소 관측 주수 52, 78, 104주 기준별 표본 재구성
- **LEVI 공식 민감도**: V1~V5 5개 공식 각각에 대해 Macro 상관 재계산
- **업종·하위기간 일관성**: 일반음식점·술집·카페 3개 업종, 코로나기·엔데믹기 2개 기간별로 Macro 상관 확인

모든 민감도 분석 결과는 5.5절과 부록 표에 요약된다.

---

### 변수 정의 및 하이퍼파라미터

- 전체 feature 목록과 정의는 부록 A에 수록
- GBM 하이퍼파라미터(n_estimators, max_depth, learning_rate 등)와 5-fold stratified CV 설정은 부록 B에 수록
- LEVI 공식 간 상관, 하위기간 LEVI 재계산 결과는 부록 C에 수록
