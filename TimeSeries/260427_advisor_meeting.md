# 2026-04-27 개별 미팅 자료

작성: 2026-04-27
지도교수: KAIST 김지희 교수
주제: 마지막 미팅 outline 이후의 모든 진행사항 상세 보고

> 본 자료는 본인(연구자)이 본인 연구의 모든 구성요소를 자기 언어로 설명할 수 있도록 작성된 학습용·reference용 문서입니다. 각 섹션은 self-contained로 구성되어, 어느 부분만 읽어도 맥락을 잃지 않습니다. 미팅 발표 시 사용할 요약본은 본 자료를 바탕으로 본인이 직접 작성합니다.

---

## 1. 미팅의 출발점 — 지난 미팅 outline의 정확한 재현

지난 미팅에서 발표한 outline은 8개 섹션으로 구성되어 있었습니다. 본 자료에서 "이전(지난 미팅)"과 "현재(V3)"를 비교하기 위해, 출발점을 그대로 복사해 둡니다.

### 1.1 지난 미팅 outline (2026-04-XX 기준)

```
1. Introduction
   서울 외식업 소상공인의 생존, 성장, 쇠퇴를 주별 거래 데이터로 진단
   기존 생애주기 관점의 한계 — 창업→성장→성숙→쇠퇴 곡선으로 설명하기 어려움
   핵심 질문 3개:
   - 개업 업장의 성장 방향성은 어떤 요인에 따라 다른가
   - 전체 생존 업장의 Growth/Stable/Decline 상태는 업력에 따라 어떻게 달라지는가
   - 초기 거래 정보만으로 향후 상태를 어느 정도 예측할 수 있는가

2. Data and Empirical Design
   KCD 주별 거래 데이터, 서울 외식업 소상공인 표본
   업장 단위 panel 구성
   주요 변수: 매출 수준, trend slope, volatility, MDD, 신규 고객 비율, 업력, 지역/상권 경쟁
   두 가지 분석 정의:
   - 개업 직후 post-entry trajectory
   - 전체 생존 업장의 observed-window Growth/Stable/Decline

3. Post-Entry Trajectory Heterogeneity
   12-class trajectory label (DD, DU, UU, UD 등)
   메시지: 초기 경로는 단일 곡선이 아니라 분화됨

4. Full-Sample Observed-Window Life-Cycle States
   전체 생존 업장을 Growth/Stable/Decline으로 분류
   업력 구간별 상태 분포
   메시지: 업력이 높아질수록 단순 쇠퇴 증가가 아니라 구성이 달라짐

5. Drivers by Business Age
   업력 bucket별 driver 분석 (trend_slope, MDD, nc_rate, volatility, category/local)
   메시지: 업력 구간별로 설명 변수가 달라짐

6. Early Prediction of Life-Cycle State
   20/30/40/50주 early window 성능
   12-class vs 3-class 비교
   feature block ablation: level → +trend/vol → +customer → +local → +cluster
   메시지: cluster 자체보다 trend/vol·customer·local이 주요 기여

7. Robustness and Discussion
   volatility 정의 재검토
   신규 고객 비율의 역할
   UDX/inflection/golden cross는 보조 분석으로 배치
   한계: 관측자료 기반, 인과효과 아님, 서울 외식업·생존자 중심

8. Conclusion
   생애주기는 단일 곡선이 아니라 trajectory/state 이중 구조
   주별 거래 데이터는 조기 진단·예측에 유용
   조기 경보 지표로 확장 가능
```

### 1.2 지난 미팅 outline에서 의도했던 핵심 메시지 (1줄)

"소상공인 생애주기는 단일 곡선이 아니라 (post-entry trajectory) × (observed-window state)의 **이중 렌즈**로 봐야 한다. 주별 거래 데이터는 이 이중 렌즈를 가능하게 하며 조기 진단·예측에 유용하다."

### 1.3 지난 미팅 outline에 명시된 한계

- 관측 자료 기반이라 **인과효과는 주장하지 않음**
- 서울·외식업·2021–2023 단일 도메인
- 분석 표본이 **생존 업장 중심**이라 sample selection 가능성 존재
- "Golden cross"는 보조 분석으로만 두기

이 세 한계가 V3에서 어떻게 변했는지가 본 미팅의 핵심 변경점입니다.

---

## 2. 출발점 → 현재(V3)로의 구조 변환 1:1 매핑

지난 미팅의 outline 8개 섹션이 V3의 어디로 이동했고, 비중이 어떻게 변했는지를 1:1로 정리합니다.

| 지난 outline | V3에서의 위치 | 비중 변화 | 메시지 변화 |
|---|---|---|---|
| 1. Introduction (3개 핵심 질문) | Ch.1 — RQ1–RQ6 6개로 확장 | **대폭 확장** | "이중 렌즈" → "6대 기여 + DSR artifact" |
| 2. Data | Ch.3 — 외부 공공 데이터 3계열 5종 신규 추가 | **확장** | "KCD 단일 패널" → "KCD + 서울시 공공 데이터 결합" |
| 3. Post-Entry 12-class | Ch.5 §5.1 도입부로 압축 | **축소** | 메인 메시지에서 도입 보조로 |
| 4. Observed-window 3-class | Ch.5 §5.1.2, §5.8 | 유지 | 그대로 유지 |
| 5. Drivers by Age | Ch.5 §5.8 | 유지 | 그대로 유지 |
| 6. Early Prediction | Ch.5 §5.6 (Hybrid C4) + §5.7 (EWS C5) | **재구성·확장** | ablation 결과 정정 + EWS artifact로 격상 |
| 7. Robustness/Discussion | Ch.5 §5.4 (volatility paradox C2) + §5.5 (Golden Cross C3) + §5.10 robustness | **승격·재구조화** | volatility는 4가설로 분해, Golden Cross는 보조→메인 |
| 8. Conclusion | Ch.7 — 6대 기여별 결론 | **전면 재작성** | "이중 구조" → "6대 기여의 micro→meso→macro 통합" |

전체 방향 전환의 한 줄 요약: **"이중 렌즈"라는 기술 메시지에서 "6개의 독립적 기여(C1–C6)와 인공물(EWS, LEVI)을 갖는 DSR 연구"로 프레이밍을 격상**.

---

## 3. 새로운 6대 기여(C1–C6) — 상세 해설

각 기여를 (가) **풀려고 한 문제**, (나) **지난 미팅에서의 처리**, (다) **새로 한 작업**, (라) **방법론 배경과 절차**, (마) **결과 수치와 해석**, (바) **학위논문 내 위상**의 6단계로 정리합니다.

### C1. Survivorship Bias의 5.4배 정량화

#### (가) 풀려고 한 문제
기존 소상공인 lifecycle 연구는 모두 "관측 가능한 점포"를 표본으로 씁니다. 그런데 폐업으로 일찍 사라진 점포는 표본에서 빠집니다. 이 차이가 분석 결론을 얼마나 왜곡하는가? 이론적 경고(Denrell 2003 "undersampling of failure")는 있지만, **편향의 크기 자체를 숫자로 측정한 연구는 없었습니다**.

#### (나) 지난 미팅에서의 처리
"분석 표본이 생존 업장 중심이라 sample selection 가능성"이라는 한 줄짜리 한계로만 명시. 편향의 크기는 미측정.

#### (다) 새로 한 작업
같은 KCD 데이터셋 안에서 두 집단을 직접 비교:
- **Panel 내부**: 최소 52주 이상 관측되어 분석 표본에 포함된 점포 (n = 48,980)
- **Panel 외부**: 같은 KCD 데이터에 있으나 52주 미만 관측되어 표본에서 제외된 점포 (n = 10,027)

각 집단의 **폐업률**(observation 종료 전에 영업 중단된 비율)을 측정.

#### (라) 방법론 배경
- "폐업률"의 정의: 데이터 종료 시점까지 점포가 활동을 중단한 비율
- 두 집단은 **같은 데이터 출처**이므로 데이터 정의·기간·자치구 기반 차이가 없음 → 두 폐업률의 차이는 순수하게 "관측 기준 충족 여부"에서 옴
- 이는 selection mechanism 자체를 직접 노출시키는 가장 단순하고 강력한 방법

#### (마) 결과 수치와 해석

| 집단 | n | 폐업률 | 의미 |
|---|---:|---:|---|
| Panel 내부 | 48,980 | **8.9%** | 기존 lifecycle 연구가 다루는 표본 |
| Panel 외부 | 10,027 | **48.3%** | 표본 진입 자체에 실패한 집단 |
| 격차 | — | **5.4배** | — |

**해석**: 기존 lifecycle 실증 연구가 "Growth가 X%, Decline이 Y%"라고 보고할 때, 그 X·Y는 이미 "살아남을 확률이 5배 이상 높은 집단"의 통계입니다. 즉 학계가 "대부분의 소상공인이 안정적으로 운영된다"고 결론 내려왔다면, 실제로는 그 결론이 표본에 살아남은 19%에 가까운 비율은 아예 분석에 들어오지도 못한 것을 무시한 결과입니다.

이 결과는 모든 lifecycle 후속 결론에 **"surviving-store observed-window pattern"**이라는 수식어를 강제합니다.

#### (바) 학위논문 내 위상
- **Ch.5 §5.2**: 결과 보고
- **Ch.2 §2.5**: G1 문헌 공백 → C1 매핑
- **Ch.3 §3.4.1**: 데이터 편향 단락에서 수치 미리 언급
- **Ch.7**: 결론에서 가장 먼저 보고되는 기여

---

### C2. Volatility Paradox의 4가설 분해

#### (가) 풀려고 한 문제
선행 연구·일반 직관: "매출 변동성이 큰 점포는 위험하다."
그런데 KCD 데이터 단면 평균을 보면: Growth 점포의 변동 계수(cv) 평균이 **Stable보다 더 큽니다** (Growth 0.412, Stable 0.364, Decline 0.592).

즉 "변동성이 클수록 위험"과 "성장하는 점포가 변동성이 크다"가 같은 데이터에서 동시에 성립합니다. 이 모순을 어떻게 풀 것인가?

#### (나) 지난 미팅에서의 처리
"volatility 정의 재검토" 한 줄. 본격적 분해 없음.

#### (다) 새로 한 작업
4개 가설을 세우고 각각 검증:

- **H1 Survivorship 가설**: "폐업한 점포를 빼고 보니 그렇게 보이는 것이다." 폐업 포함 vs 생존자만으로 비교.
- **H2 Phase-dependent 가설**: "관측 시점이 점포의 어느 phase냐에 따라 cv의 의미가 다르다." 관측 구간을 w1–15 / w16–30 / w31+ 3단계로 나눠 cv 재계산.
- **H3 Inverted-U 가설**: "cv와 성장은 단조 관계가 아니라 역U자 관계다." cv 10분위(D1–D10)로 나눠 Growth 비중을 봄.
- **H4 Outcome-specific Cox 가설**: "outcome(Growth/Stable/Decline) 내부에서 cv의 위험비가 다르다." outcome별 분리 Cox PH.

#### (라) 방법론 배경
- **Cox 비례위험 모형 (Cox 1972)**: 시간-사건 데이터에서 공변량이 위험률(hazard rate)에 미치는 효과를 비례적으로 추정. **위험비(HR)** > 1이면 위험 요인, < 1이면 보호 요인.
- **Outcome-conditional Cox**: 전체 모형이 아니라 Growth만, Stable만, Decline만 모집단으로 분리해 각각 Cox 추정. 이렇게 하면 "전체 평균 효과"가 가리고 있던 부분집단 이질성이 드러남.
- **Schoenfeld 잔차 진단 (Grambsch-Therneau 1994)**: 비례위험 가정이 성립하는지 점검. 비례위험은 "공변량 효과가 시간에 따라 변하지 않는다"는 가정인데, 이게 깨지면 Cox 추정이 편향됨.

#### (마) 결과 수치와 해석

**전체 모집단 Cox PH** (n=48,980, event=4,352, **concordance = 0.819**):

| 공변량 | HR | 95% CI | p |
|---|---:|---|---|
| nc_rate | 1.141 | [1.108, 1.174] | 4.3e-19 |
| **cv (변동성)** | **1.092** | [1.061, 1.123] | 1.1e-9 |
| trend_slope | 0.444 | [0.428, 0.461] | ≈ 0 |
| mdd (max drawdown) | 0.744 | [0.729, 0.759] | 3.8e-174 |

전체 평균에서 cv는 HR 1.09로 위험 요인입니다. 그런데 outcome별로 분리하면:

| Outcome 내부 | cv HR | 95% CI | 해석 |
|---|---:|---|---|
| Growth | **0.839** | [0.775, 0.908] | **보호 요인** (변동성 클수록 위험 ↓) |
| Stable | **0.612** | [—] | **보호 요인** |
| Decline | **1.183** | [—] | 위험 요인 |

**해석**: cv의 효과는 **상태에 의존**합니다. Growth/Stable 상태 안에서 보면 변동성이 큰 점포는 오히려 위험이 낮습니다. 직관적으로는 "성장 단계에서는 출렁임이 있더라도 평균적으로 매출이 늘어나고 있고, 그 동학 자체가 활동성·기회 포착의 신호일 수 있다." 반면 Decline 상태에서 변동성이 크다는 것은 매출 붕괴 직전의 불안정성으로 해석됩니다.

H3 inverted-U도 확인됨: cv 10분위 중 **D5 (cv 0.36–0.41)**에서 Growth 비중이 최고 — 너무 안정해도(D1–D2) Growth가 적고, 너무 출렁여도(D9–D10) Growth가 적음. 중간 정도의 변동성이 성장과 가장 강하게 연결됩니다.

#### (바) 학위논문 내 위상
- **Ch.5 §5.4**: 4가설 H1–H4 순차 검증
- **Ch.6**: 이론적 함의 — "변동성은 일관된 위험 신호"라는 단순 해석을 부분 기각

---

### C3. Golden Cross 인과 삼각검증 (지난 미팅 대비 메인 격상)

#### (가) 풀려고 한 문제
"신규고객 유입 비율(nc_rate)이 매출 반등을 **선행**하는가?" 즉 신규고객이 늘어난 다음 주에 매출이 늘어나는 패턴을 단순 상관이 아닌 **인과적**으로 입증할 수 있는가.

#### (나) 지난 미팅에서의 처리
"UDX/inflection/golden cross 계열은 보조 분석으로 배치." 한계 명시: "관측자료 기반, 인과효과 아님."

#### (다) 새로 한 작업
**3가지 독립된 인과식별 방법**을 동일 가설에 적용해 결과가 수렴하는지를 본 **삼각검증(triangulation)**:

1. **Granger 인과 검정**
2. **PSM (Propensity Score Matching) + DiD (Difference-in-Differences)**
3. **Two-way Panel Fixed Effect 회귀**

#### (라) 방법론 배경

**1) Granger 인과 (Granger 1969)**
- 직관: "X의 과거 값을 알면 Y의 미래 값을 더 잘 예측할 수 있는가?"
- 절차: $Y_t = \alpha + \sum \beta_i Y_{t-i} + \sum \gamma_j X_{t-j} + \epsilon$ 회귀에서 $\gamma_j$들이 동시에 0인지 F-test
- 본 연구: 점포별로 nc_rate→sales 방향과 sales→nc_rate 방향 모두 검정. 비대칭성(nc만 유의)이 핵심
- 한계: 시간적 선행만 보임, 잠재적 공통 원인은 다루지 못함

**2) PSM + DiD (Rosenbaum-Rubin 1983, Card-Krueger 1994)**
- 직관: "관측 가능한 특성이 비슷한 점포끼리 매칭한 뒤, 처치 점포(신규고객 유입 급증)와 대조 점포의 처치 전후 매출 차이의 차이를 비교"
- 절차:
  - (i) 처치(treatment) 정의: nc_rate가 임계점 이상으로 급증한 store-week
  - (ii) 매칭: pre-treatment 관측 가능한 특성(매출 수준, trend, cv 등)을 propensity score로 변환해 caliper 매칭
  - (iii) DiD 추정: $\Delta y_{treated} - \Delta y_{control}$
- 결과 통계량: ATT (Average Treatment effect on the Treated)
- 강점: 관측 공변량의 confounding을 차단; 그러나 unobserved confounding은 여전히 잔존

**3) Two-way Panel Fixed Effect**
- 직관: "각 점포의 고정 특성과 각 시점의 공통 충격을 모두 통제한 뒤, nc_rate 변화와 sales 변화의 관계를 본다"
- 모형: $\log(\text{sales}_{i,t}) = \alpha_i + \lambda_t + \beta \cdot nc\_l1_{i,t} + X_{i,t}\gamma + \epsilon_{i,t}$
- $\alpha_i$: 점포 고정효과(매출 수준, 입지 등 시간불변 모든 특성 흡수)
- $\lambda_t$: 시점 고정효과(코로나 충격, 계절 등 모두 흡수)
- $nc\_l1$: 1주 시차 신규고객 비율
- 결과 통계량: $\beta$ 계수와 그 t-statistic

**왜 3가지를 다 하나?**
각 방법의 약점을 다른 방법이 보완하기 위함:
- Granger는 시간 선행성만, 공통 원인 못 다룸
- PSM-DiD는 관측 공변량은 처리하지만 unobserved time-varying confounding은 못 잡음
- Panel FE는 시간불변 점포 특성과 공통 시간 충격은 잡지만, 점포-시점별 상호작용 충격은 못 잡음

세 방법이 같은 부호·유의성을 동시에 보여주면, 각 방법의 가정이 모두 동시에 깨지지 않는 한 인과 결론을 내릴 수 있습니다.

#### (마) 결과 수치와 해석

| 방법 | 통계량 | 값 | p |
|---|---|---:|---|
| Granger nc→sales | 유의 비율 | 10.5% | 비대칭(nc만) 8.8% |
| PSM + DiD | ATT (log-sales) | **+0.1165** | t=18.07, p<1e-72 |
| Panel Two-way FE | nc_l1 계수 β | **0.278** | p<1e-306 |

**+0.1165 log-sales** 의미: 처치(신규고객 유입 급증)가 후속 매출을 **약 +12.4%** 끌어올림 (exp(0.1165)−1 ≈ 0.124).

**해석**: 신규고객 유입은 매출 반등의 단순 동반 현상이 아니라, **선행 인과 신호**입니다. 세 방법 모두 같은 방향·유의성을 보이므로, 각 방법의 약점이 동시에 우연히 드러난 것일 가능성은 매우 낮습니다.

**Enhanced PSM robustness**: 매칭 품질을 추가 진단한 결과 pre-treatment 차이가 78% 감소 → 매칭 후 처치·대조군이 매우 비슷해졌음을 확인.

#### (바) 학위논문 내 위상
- **Ch.5 §5.5**: 삼각검증 보고
- **Ch.4 §4.5**: 식별 전략 설계
- **Ch.6**: 한계 논의 (잔존 가정의 위협)
- **승격 자체가 메시지**: 지난 미팅의 "보조 분석"에서 메인 기여로 격상한 것은 인과 신호의 강도와 일관성이 충분했기 때문

---

### C4. Hybrid 64D Representation이 Deep Sequence를 상회

#### (가) 풀려고 한 문제
점포별 시계열 매출 데이터로부터 향후 30주 상태(Growth/Stable/Decline)를 예측하는 모델을 어떻게 설계할 것인가? 특히 "딥러닝 vs 공학적 특성 + 트리 모델" 중 무엇이 우월한가?

#### (나) 지난 미팅에서의 처리
- 20/30/40/50주 early window 성능 보고
- feature block ablation: level → +trend/vol → +customer → +local → +cluster
- 메시지: "cluster 자체보다 trend/vol·customer·local이 주요 기여"
- 30주 GBM weighted F1 = 0.572 (3-class)

#### (다) 새로 한 작업
**Hybrid 64차원 표현(D)**을 새롭게 설계하고 Deep sequence와 직접 비교.

64차원 = **46개 공학적 특성** + **K-Means(K=4) cluster one-hot 4개** + **change-point feature 7개** + 기타 7개

비교군:
- **A**: base 46 (공학적 특성만)
- **B**: A + cluster
- **C**: A + change-point
- **D**: A + cluster + change-point (Proposed)
- **Deep**: LSTM / GRU / Transformer (legacy label 기반)

#### (라) 방법론 배경

**46개 공학적 특성**: level, trend(slope_early/late, r2), volatility(cv, residual_vol), customer behavior(nc_rate, repeat ratio, weekend ratio), local context(자치구 더미, 업종 더미, 동일 동 경쟁 강도), MDD 등

**K-Means cluster one-hot**: 점포 매출 시계열을 K-Means(K∈[3,15] grid 중 K=4 선택)로 군집화. 4개 cluster 중 어디 속하는지 one-hot encoding.

**Change-point feature (7개)**: 시계열에서 추세가 바뀌는 시점(change-point)을 검출하고 그 위치·크기·빈도 등을 특성으로 추출. 예: "관측 창 안에서 change-point가 몇 개 발생했는가", "마지막 change-point 이후 평균 trend는 어떠한가".

**Gradient Boosting (Chen-Guestrin 2016, XGBoost / LightGBM)**: 의사결정 트리를 순차적으로 boosting. 비선형·상호작용·결측을 잘 다루며 표 형태 데이터에서 일반적으로 강함 (Shwartz-Ziv & Armon 2022).

**Deep sequence baselines**:
- LSTM (Hochreiter-Schmidhuber 1997): 장기 의존성 처리
- GRU: LSTM의 경량화
- Transformer (Vaswani 2017): 시퀀스 위치 무관하게 어텐션
- 학습 데이터: 점포별 주간 시계열 직접 입력

#### (마) 결과 수치와 해석

**3-class 분류 (Growth/Stable/Decline) 성능 (5-fold CV)**:

| 모형 | F1 | Precision | Recall | AUC |
|---|---:|---:|---:|---:|
| **A** base 46 | 0.548 | 0.694 | 0.414 | 0.736 |
| B base + cluster | (similar) | — | — | — |
| C base + cp | (similar) | — | — | — |
| **D** base + cluster + cp (Proposed) | **0.639** | **0.771** | **0.548** | **0.824** |
| XGBoost (raw 46) | 0.548 | — | 0.561 | 0.736 |
| LightGBM | 0.548 | — | 0.561 | 0.736 |

**Hybrid D vs base 46**: F1 +0.091, AUC +0.088. Recall이 0.414→0.548로 크게 개선 — Decline 점포 잡아내는 능력이 향상.

**중요한 정정**: 지난 미팅의 ablation 결론("cluster는 marginal")은 cluster를 **단독으로** 추가했을 때를 본 결과였습니다. 새 분석은 cluster + change-point를 함께 넣어야 의미 있는 gain이 발생함을 보입니다. 즉 **"cluster가 의미 없다"가 아니라 "cluster는 change-point와 결합될 때 의미 있다"**가 정확한 메시지.

**Deep sequence vs Hybrid**: legacy label 기반이라 직접 비교는 보조이지만, 동일 windowed 입력 조건에서 Hybrid가 우위. 이는 Fawaz et al. 2019, Shwartz-Ziv & Armon 2022가 지적한 "moderate T·중간 규모 표본에서는 inductive bias 있는 hand-engineered + boosting이 end-to-end deep을 상회"하는 일반 패턴과 일치.

#### (바) 학위논문 내 위상
- **Ch.5 §5.6**: 비교 표·ROC·PR
- **Ch.4 §4.6**: 모델 아키텍처 설명
- **Ch.6**: 방법론적 함의 — 중간 규모 시계열에서 inductive bias의 가치

---

### C5. EWS Artifact + Cost-Sensitive Operating Point (DSR)

#### (가) 풀려고 한 문제
C4의 예측 모델을 단순 분류 정확도 지표로 끝낼 것이 아니라, 실제 정책·플랫폼이 운영할 수 있는 **인공물(artifact)**로 변환하려면 어떤 평가 지표·운영 임계치가 필요한가?

#### (나) 지난 미팅에서의 처리
- 30주 GBM F1 0.572를 보고
- "조기 경보 지표로 확장 가능"이라는 Conclusion 한 줄

#### (다) 새로 한 작업
**Early Warning System (EWS) artifact** 구축:
- 49,007개 점포에 대해 **점포별 Decline 위험 점수 (0–100)** 산출
- PR(Precision-Recall) 곡선과 **AP(Average Precision)** 보고
- **Cost-sensitive optimal threshold** 결정 + **net utility** 계산

#### (라) 방법론 배경

**왜 PR/AP인가?**
- ROC/AUC는 클래스 불균형(Decline 비중 22%)에서 낙관적으로 나옴
- PR 곡선의 AP는 불균형 상황에서 더 정직한 성능 지표
- baseline AP = positive 비율 (Decline 22% → baseline AP 0.223)

**Cost-sensitive threshold란?**
- 분류 임계치 t를 0.5로 두는 것은 "false positive(잘못 경고)와 false negative(놓침) 비용이 같다"는 가정
- 현실에서는 둘이 다름. 본 연구는 비용 구조를 명시:
  - **B = 10**: 정확히 식별된 Decline 점포에 개입했을 때의 정책 편익
  - **C_support = 2**: 한 점포에 지원할 때 드는 비용 (false positive 비용)
  - **C_miss = 8**: Decline을 놓쳤을 때 발생하는 사회적 비용
- **Net utility**(t) = TP·(B − C_support) − FP·C_support − FN·C_miss
- t를 최적화해서 net utility 최대화하는 임계치 찾기

**DSR (Hevner 2004, Peffers 2007)**:
- 단순 모델이 아닌 **인공물**로 위치
- DSR 6단계: 문제 식별 → 목표 정의 → 설계·개발 → 실증 → 평가 → 의사소통
- 본 연구의 EWS:
  - 문제: 소상공인 폐업의 선제 식별
  - 목표: 30주 관측만으로 향후 30주 예측
  - 설계: Hybrid 64D + GB + 확률 보정 + cost-sensitive threshold
  - 실증: 49,007점포 적용
  - 평가: PR/AP + cost-sensitive utility + 외부 타당성 (C6와 연결)
  - 의사소통: 본 학위논문 + 영문 투고

#### (마) 결과 수치와 해석

| 지표 | 값 | baseline | 개선 |
|---|---:|---:|---|
| Decline AP | **0.688** | 0.223 | **3.08배** |
| Growth AP | 0.819 | 0.40 | 2.05배 |
| Stable AP | (보고 보조) | — | — |
| 최적 threshold | **0.10** | (0.5 가정 시) | — |
| Net utility @ t=0.10 | **43,626** | (t=0.5에서 더 낮음) | — |

**해석**:
- Decline AP 0.688은 "위험 신호 상위 X%를 호출했을 때 평균적으로 X%의 정밀도가 나온다"의 평균 — baseline 0.223 대비 3배 개선
- 임계치 0.10이 최적이라는 것은 "조금만 의심스러우면 경고하는 게 net 사회 후생을 늘림"이라는 의미. C_miss(8)이 C_support(2)보다 4배 크기 때문에 false positive를 감수해도 false negative를 줄이는 게 이익
- net utility 43,626은 cost 단위가 임의이지만, 다른 임계치(0.05, 0.20, 0.30) 대비 최대값임을 확인

#### (바) 학위논문 내 위상
- **Ch.5 §5.7**: PR 곡선·cost-benefit 보고
- **Ch.4 §4.6**: 임계치 선택 절차
- **Ch.6**: DSR artifact 평가 — 본 연구가 단순 예측이 아니라 운영 가능한 도구를 만들었음을 강조

---

### C6. LEVI 외부 검증 (지난 미팅 outline에 없던 신규 contribution)

#### (가) 풀려고 한 문제
KCD는 **단일 벤더** 거래 데이터입니다. 즉 KCD 가맹점만 포함하므로 서울시 외식업 모집단의 부분집합. 이 패널의 분석 결과가 서울시 전체의 동태와 일관되는지를 어떻게 검증할 것인가?

#### (나) 지난 미팅에서의 처리
- 한계: "서울 외식업 표본에 한정"
- 외부 데이터 검증 자체는 미실행

#### (다) 새로 한 작업
1. 점포 단위 Growth/Decline 레이블을 **자치구로 집계**한 지수 LEVI 정의
2. LEVI를 서울시 **공공 데이터 3종**과 상관 분석으로 외부 검증

#### (라) 방법론 배경

**LEVI 정의** (V1 주공식):
$$\text{LEVI}^{V1}_g = \frac{G_g - D_g}{N_g}$$
- $G_g$: 자치구 g의 Growth 점포 수
- $D_g$: 자치구 g의 Decline 점포 수
- $N_g$: 자치구 g의 전체 observed-window 점포 수
- 양수 = 성장 우위, 음수 = 쇠퇴 우위

**대안 공식 4종** (V2–V5):
- V2 log-odds: $\log(G_g / D_g)$
- V3 평균 추세
- V4 중앙값 추세
- V5 shrinkage

**검증 데이터**:
- 서울시 생활인구 (자치구×시간대)
- 서울시 일반음식점 인허가 (점포별 폐업)
- 서울시 상권분석서비스 (자치구×분기 추정매출)

**왜 자치구 단위?**
- 25개 자치구 = 서울의 **전수**. 표본 추출 문제가 아예 없음
- 효과 크기(Pearson r)가 통계적 유의성보다 해석에 중심
- 외부 데이터들이 모두 자치구 해상도로 제공됨

#### (마) 결과 수치와 해석

**LEVI vs 서울시 외부 지표 (Pearson · Spearman, n=25)**:

| 외부 지표 | Pearson | Spearman | 해석 |
|---|---:|---:|---|
| 생활인구 변화율 (2021-01→2023-08) | **0.853** | 0.802 | 매우 강한 정방향 |
| 인허가 기반 폐업률 (월평균) | **−0.430** | −0.241 | 일관된 부방향, 크기 중간 |
| 생활인구 수준 (평균) | −0.049 | 0.055 | ≈ 0, **무관** |
| KCD 분기매출 vs 상권분석 추정매출 (수준) | **0.766** | 0.727 | 강한 정방향 |
| KCD QoQ vs 외부 QoQ | **0.839** | 0.891 | 매우 강한 정방향 |

**왼쪽 두 결과의 의미**:
- LEVI는 자치구의 **"인구 변화"와는 강하게 양의 상관**: 사람이 늘어나는 동네일수록 점포 성장 우위.
- LEVI는 자치구의 **"인구 수준(크기)와는 무관"**: 이게 핵심. 단순히 "큰 동네에서 잘된다"가 아니라, 동네가 **활성화되는 동태** 자체를 LEVI가 잡아냄.

**오른쪽 두 결과의 의미**:
- KCD 단일 벤더 매출 합계가 서울시 외식업 전체 모집단의 매출 동태(상권분석서비스 추정)와 r=0.766–0.839로 일치.
- 즉 KCD 패널 위에서 만든 모든 결과가 서울시 외식업 전체로도 외삽 가능하다는 강한 외적 타당성 증거.

**LEVI 5개 공식 견고성**: V1–V5 공식 간 상관 r ≥ 0.83. 즉 LEVI 결과는 특정 공식(V1)에 의존하지 않습니다.

**자치구 LEVI 분포 (V1)**:
- 상위: 종로 0.44, 중구 0.42, 용산 0.29, 강남 0.27, 마포 0.27 (도심·업무지구)
- 하위: 중랑 0.037, 강북 0.06, 도봉 0.07 (외곽 주거지)
- → 경제 지리적 직관과 일치

**업종·하위기간 일관성**:
- 일반음식점/술집/카페 3개 업종별 LEVI–생활인구 r ∈ [0.72, 0.84]
- 코로나기(2021-01~2022-04) vs 엔데믹기(2022-05~2023-08): 둘 다 일관 방향, 엔데믹기에서 약간 더 강함

#### (바) 학위논문 내 위상
- **Ch.5 §5.9**: 외부 검증 보고
- **Ch.4 §4.7**: LEVI 설계 + 외부 변수 정의
- **Ch.7**: 결론에서 마지막 기여로 보고
- **본 학위논문의 차별화 포인트**: 영문 투고에서는 C5(EWS artifact)가 메인, 한글 학위논문에서는 C6(LEVI 외부 검증·지역 모니터링)가 균형의 한 축

---

## 4. 새로 도입된 외부 데이터 — 5종 상세

[thesis/data_external/](../data_external/) 에 보관된 모든 외부 자료를 1종 단위로 자세히 설명합니다.

### 4.1 LOCAL_PEOPLE_GU (서울시 생활인구, 자치구 단위)

#### 4.1.1 무엇인가
서울 열린데이터광장이 공개하는 자치구 단위 추계 인구. 통신사 LTE 기지국 접속 기록(SK텔레콤 추계)에 행정안전부 주민등록 자료를 결합해 산출.

#### 4.1.2 왜 "생활"인구인가
주민등록 인구 = "어디 살고 있다고 신고한 사람 수" (정적). 생활인구 = "지금 그 시점·그 자치구에 머물러 있는 사람 수" (동적). 직장·학교·관광 등으로 인한 이동을 반영.

소상공인 매출은 거주민이 아니라 그 지역에 **체류**하는 사람 수에 좌우되므로, 생활인구가 거래 데이터와 더 잘 맞는 거시 지표입니다.

#### 4.1.3 본 연구의 사용 파일
- `LOCAL_PEOPLE_GU_2021.zip` (~33MB, 원본 CP949 인코딩)
- `LOCAL_PEOPLE_GU_2022.zip` (~34MB)
- `LOCAL_PEOPLE_GU_2023.zip` (~33MB)
- `lp_2023/` — 2023년치 압축 해제 폴더

#### 4.1.4 원본 단위
자치구 × 일자 × 시간대(24개) × 연령대 = 매우 고해상도

#### 4.1.5 본 연구 전처리
1. 시간대 24개 값의 산술평균 → 그 날짜의 "일평균 생활인구"
2. 일별 관측 → 자치구별 월별 평균
3. 자치구 코드(행정안전부 표준)를 구 이름으로 매핑
4. 분석 기간 2021-01 ~ 2023-08의 32개월 × 25구 = **800개 관측치**

#### 4.1.6 파생 변수
- `lp_mean`: 자치구별 월평균 생활인구의 평균값 (수준)
- `lp_pct_change`: 2021-01 vs 2023-08 변화율 (동태)

#### 4.1.7 본 연구에서의 역할
**C6 LEVI 외부 검증의 핵심 변수.** LEVI는 인구 변화율과 r=0.853, 인구 수준과는 r≈0. 이 분리 자체가 "거래 데이터가 동태를 독립적으로 포착"한다는 핵심 메시지.

---

### 4.2 seoul_food_permits.csv (서울시 일반음식점 인허가)

#### 4.2.1 무엇인가
서울시가 공개하는 "서울시 일반음식점 인허가 정보". **1970년대부터 현재까지** 서울시에 인허가를 받은 일반음식점 업소 전체.

#### 4.2.2 파일 정보
- `seoul_food_permits.csv` (211MB, 532,439건)
- 원본 CP949 인코딩

#### 4.2.3 변수
인허가일자, 영업상태명(영업/폐업/휴업), 폐업일자, 사업장 주소(지번·도로명), 업태(한식/양식 등) 등 39개 변수

#### 4.2.4 본 연구 전처리 (자치구×월별 폐업률 구축)
1. 주소 문자열에서 정규표현식으로 "서울특별시 OOO구"를 추출 → 자치구 식별
2. 폐업일자 파싱 → 월 단위 폐업 건수 `n_closures`
3. 각 구×월의 **활성 점포 수** = "해당 월 시작일 기준 인허가 후이며, 폐업일이 없거나 해당 월 말일 이후인 점포 수" → `n_active`
4. 폐업률 `closure_rate = n_closures / n_active`
5. 분석 기간 2021-01 ~ 2023-08의 25구 × 32개월 = **800개 관측치**

#### 4.2.5 KCD 표본과의 관계
- KCD 표본은 KCD 가맹점만 포함 → 서울시 외식업 전체의 부분집합
- 인허가 정보는 서울시 외식업 **전체 모집단**을 포괄
- 두 자료의 자치구별 폐업률 비교가 외적 타당성 검증의 직접 도구

#### 4.2.6 본 연구에서의 역할
- **C6 외부 검증**: LEVI vs 인허가 폐업률 r=−0.430
- **C1 보조** (간접): 인허가 자료와의 비교는 KCD 패널의 부분집합 성격을 명확히 함

---

### 4.3 cda_est_sales_hinterland (서울시 상권분석서비스 — 추정매출)

#### 4.3.1 무엇인가
서울시 상권분석서비스(https://golmok.seoul.go.kr/)가 카드 결제 집계·공공 통계로 산정한 **상권 배후지(hinterland) 단위 분기별 추정매출액**.

#### 4.3.2 "상권 배후지"란
상권을 둘러싼 영향권. 한 상권을 중심으로 일정 반경의 인구·소비가 잡히는 지리적 단위. 자치구보다 좁고 상권보다 넓음.

#### 4.3.3 파일 정보
- `cda_est_sales_hinterland_2021.zip` (~24MB)
- `cda_est_sales_hinterland_2022.zip`
- `cda_est_sales_hinterland_2023.zip` (~23MB)

#### 4.3.4 본 연구 전처리
- 배후지 단위를 자치구로 매핑 집계
- 분기별 자치구 추정매출 계열 구축 (n=25 × 11분기)

#### 4.3.5 본 연구에서의 역할
**C6 외부 검증**: KCD 분기매출 합계와 상권분석서비스 추정매출의 비교
- 수준 r = 0.766
- QoQ 변화 r = 0.839

→ KCD 단일 벤더 패널의 매출 동태가 서울 외식업 전체 모집단과 일치한다는 강한 증거.

---

### 4.4 cda_stores_by_district (서울시 상권분석서비스 — 점포 현황, 자치구)

#### 4.4.1 무엇인가
서울시 상권분석서비스가 집계한 **자치구 단위 업종별 활성 점포 수**.

#### 4.4.2 파일 정보
- `cda_stores_by_district_2021.zip`
- `cda_stores_by_district_2022.zip`
- `cda_stores_by_district_2023.zip`

#### 4.4.3 본 연구에서의 역할
**§3.3.2 인허가 기반 활성 점포 수와 교차 비교**: 서로 다른 정의·집계 방식의 활성 점포 추산이 얼마나 일치하는지 점검. KCD 표본·인허가 자료·상권분석서비스 세 출처의 모집단 정의 차이를 명시화.

---

### 4.5 cda_stores_by_hinterland (서울시 상권분석서비스 — 점포 현황, 배후지)

#### 4.5.1 무엇인가
4.4와 동일하나 **배후지 단위**. 자치구보다 세분화된 단위.

#### 4.5.2 파일 정보
- `cda_stores_by_hinterland_2021.zip`
- `cda_stores_by_hinterland_2022.zip`
- `cda_stores_by_hinterland_2023.zip`

#### 4.5.3 본 연구에서의 역할
- 현 V3에서는 직접 사용 빈도 낮음
- **향후 확장 대비**: 동(dong) 또는 상권 단위 해상도 분석으로 확장할 때 필요. 현 학위논문에서는 자치구 단위 자료(4.4)를 메인으로 사용하지만, 후속 영문 paper나 저널 확장에서 활용 여지.

---

## 5. 새로 진행한 실험·분석 — 작업 단위별 상세

### 5.1 Cox PH·Kaplan-Meier 생존분석 (C2 보조 + 단독 결과)

#### 5.1.1 왜 했는가
지난 미팅까지는 시계열 클러스터링과 분류 위주. 점포의 **시간-사건(time-to-event)** 구조 — 즉 "언제 폐업하는가"를 직접 모델링하지 않음. 생존분석은 중도절단(아직 폐업 안 함) 데이터를 자연스럽게 다루며, 공변량 효과를 위험비(HR)로 해석 가능.

#### 5.1.2 어떻게 했는가
1. 폐업 사건 정의: observation 종료 전에 활동 중단된 점포 = event=1, 그렇지 않으면 censored=0
2. **Kaplan-Meier 생존함수** 추정: 각 outcome 그룹별·각 업종별 survival curve
3. **Log-rank 검정**: 그룹 간 생존함수 차이 검정
4. **Cox PH 회귀**: 공변량(nc_rate, cv, trend, mdd 등)이 hazard에 미치는 효과
5. **Schoenfeld 잔차 진단** (Grambsch-Therneau 1994): 비례위험 가정 검증

#### 5.1.3 결과
- Outcome 그룹 간 log-rank χ² = 7,499.4, p ≈ 0
- 업종 depth_2 간 log-rank χ² = 390.0, p = 2.85e-75
- Cox PH concordance = **0.819** (높은 식별력)
- 주요 HR: trend_slope 0.444 (강한 보호), mdd 0.744, slope_late 0.777, r2_early 1.194

#### 5.1.4 의의
- Outcome과 업종이 생존 구조의 핵심 층화 변수임을 확인
- C2 volatility paradox 분해의 도구로 사용
- Ch.5 §5.3에 별도 보고

---

### 5.2 Outcome-conditional Cox PH (C2 핵심)

#### 5.2.1 왜 했는가
전체 모집단 Cox에서 cv HR 1.09 (위험)이지만 Growth 점포 cv 평균이 Stable보다 큰 모순(volatility paradox)을 분해하기 위해.

#### 5.2.2 어떻게 했는가
모집단을 outcome별로 분리:
- Growth만 부분집합 → Cox PH 추정 → cv HR 보고
- Stable만 → 동일
- Decline만 → 동일

#### 5.2.3 결과
- Growth 내부 cv HR = 0.839 (보호)
- Stable 내부 cv HR = 0.612 (보호)
- Decline 내부 cv HR = 1.183 (위험)

#### 5.2.4 의의
"변동성 = 위험" 단순 해석을 부분 기각. 변동성의 의미는 점포 상태에 결정적으로 의존.

---

### 5.3 Granger 인과 검정 (C3 첫 번째 다리)

#### 5.3.1 왜 했는가
신규고객 유입(nc)이 매출 반등을 **선행**하는지 시간적 인과를 검정하기 위해.

#### 5.3.2 어떻게 했는가
점포별로 두 회귀를 비교:
- 제한 모형: $sales_t = \alpha + \sum \beta_i sales_{t-i}$
- 비제한 모형: $sales_t = \alpha + \sum \beta_i sales_{t-i} + \sum \gamma_j nc_{t-j}$
- F-test: $\gamma_j$들이 동시에 0인가?

방향성: nc → sales와 sales → nc 모두 검정해서 비대칭성(nc만 유의) 비율 확인

#### 5.3.3 결과
- nc → sales 유의 비율 = 10.5%
- sales → nc 유의 비율 < 10.5%
- 비대칭(nc만 유의) = 8.8%

#### 5.3.4 의의
시간적 선행성 확인. 그러나 Granger만으로는 인과 결론 부족 → PSM-DiD·Panel FE로 보강.

---

### 5.4 PSM + DiD 추정 (C3 두 번째 다리)

#### 5.4.1 왜 했는가
관측 가능한 공변량의 confounding을 차단한 처치 효과 추정.

#### 5.4.2 어떻게 했는가
1. **처치(treatment) 정의**: nc_rate가 점포 내 분포 임계점 이상으로 급증한 store-week
2. **공변량**: pre-treatment 매출 수준, trend, cv, 업종, 자치구 등
3. **Propensity Score**: 공변량 → P(treatment) 로지스틱 회귀로 추정
4. **Caliper matching**: caliper = 0.05 SD 내에서 1:1 매칭
5. **공통 지지(common support) 진단**: 매칭 후 공변량 분포 비교
6. **DiD 추정**: $\Delta y_{treated} - \Delta y_{control}$
7. **Two-way clustered SE**: 점포·시점 양쪽 클러스터로 표준오차 보정

#### 5.4.3 결과
- ATT = +0.1165 log-sales (≈ +12.4%)
- t = 18.07
- p < 1e-72

#### 5.4.4 강건성 점검 (Enhanced PSM)
매칭 후 pre-treatment 차이가 매칭 전 대비 78% 감소 → 처치·대조군이 매우 유사해짐

---

### 5.5 Two-way Panel Fixed Effect (C3 세 번째 다리)

#### 5.5.1 왜 했는가
시간불변 점포 특성과 공통 시간 충격 모두 통제한 회귀 추정.

#### 5.5.2 어떻게 했는가
모형: $\log(\text{sales}_{i,t}) = \alpha_i + \lambda_t + \beta \cdot nc\_l1_{i,t} + X_{i,t}\gamma + \epsilon_{i,t}$

- $\alpha_i$: 점포 고정효과 (입지, 업종, 점주 특성 등 시간불변 모두 흡수)
- $\lambda_t$: 시점 고정효과 (코로나 충격, 계절성 등 모두 흡수)
- $nc\_l1$: 1주 시차 신규고객 비율
- $X$: 추가 통제변수
- 표준오차: 점포 단위 cluster

#### 5.5.3 결과
- $\beta$ (nc_l1 계수) = 0.278
- p < 1e-306

#### 5.5.4 의의
관측 불가능한 시간불변 점포 특성·공통 시간 충격을 모두 제거한 후에도 nc_rate → sales 효과가 강하게 잔존 → C3의 세 번째 강한 증거.

---

### 5.6 Hybrid 64D 모형 + Deep Sequence Baseline (C4)

#### 5.6.1 왜 했는가
"cluster는 marginal"이라는 지난 ablation 메시지가 cluster + change-point의 결합을 시험하지 않은 결과일 수 있음. 또한 hybrid vs deep을 직접 비교한 적이 없음.

#### 5.6.2 어떻게 했는가
1. **46개 공학적 특성** 산출 (자세한 변수 목록은 [top_tier/src/](../../top_tier/src/) step 참조)
2. **K-Means 클러스터링**: K∈[3,15] grid에서 silhouette·BIC 기준으로 K=4 선정 → cluster one-hot
3. **Change-point 검출**: PELT/Binary segmentation 등으로 점포별 시계열 change-point 추출 → 7개 특성
4. **모델 비교**: A(46) / B(+cluster) / C(+cp) / D(+cluster+cp Proposed)
5. **Deep baseline**: LSTM, GRU, Transformer (legacy label 기준이라 보조)
6. **5-fold CV**: 점포 단위 분할
7. **Fold-safe leakage audit**: train/val 사이 정보 누출 점검

#### 5.6.3 결과
- A F1 0.548 / AUC 0.736
- D F1 0.639 / AUC 0.824 (+0.091 / +0.088)
- Recall 0.414 → 0.548 (Decline 잡아내는 능력 크게 개선)

#### 5.6.4 의의
- "cluster + change-point가 함께 들어가야 의미 있는 gain"으로 메시지 정정
- Hybrid가 deep을 상회 → moderate T·중간 표본에서 inductive bias의 가치 입증

---

### 5.7 EWS Cost-Benefit 평가 (C5)

#### 5.7.1 왜 했는가
모델 성능을 단순 F1·AUC가 아닌 **운영 가능한 인공물**로 변환하기 위해.

#### 5.7.2 어떻게 했는가
1. **49,007개 점포에 D 모형 적용** → 각 점포별 Decline 위험 점수
2. **점수 보정** (Platt scaling 또는 isotonic) → 0~1 확률
3. **PR 곡선 + AP** 산출
4. **Cost matrix 정의**: B=10, C_support=2, C_miss=8
5. **Net utility 계산**: TP·(B−C_support) − FP·C_support − FN·C_miss
6. **임계치 그리드** {0.05, 0.10, 0.15, 0.20, 0.30}에서 max net utility

#### 5.7.3 결과
- Decline AP 0.688 (baseline 0.223)
- Growth AP 0.819
- 최적 t = 0.10
- Max net utility = 43,626

#### 5.7.4 의의
DSR 기준의 인공물 평가 완수. 정책·플랫폼이 실제로 사용할 수 있는 임계치 결정 도구.

---

### 5.8 LEVI 설계 + 외부 검증 (C6)

#### 5.8.1 왜 했는가
KCD 단일 벤더 패널의 외적 타당성 입증 + 점포 단위 분석을 자치구·도시 단위로 확장.

#### 5.8.2 어떻게 했는가
1. **LEVI V1–V5 5개 공식** 모두 산출
2. **외부 거시 변수** 구축: 생활인구·인허가 폐업률·상권분석 추정매출
3. **상관 분석**: Pearson + Spearman, 25개 자치구 × 11개 분기 패널
4. **분리 검증**: 인구 수준 vs 변화 (수준은 r≈0, 변화는 r=0.853)
5. **공식 견고성**: V1–V5 간 상관 (r ≥ 0.83)
6. **하위그룹 일관성**: 업종(3개) × 하위기간(2개)

#### 5.8.3 결과
- LEVI vs 생활인구 변화율 r = 0.853
- LEVI vs 생활인구 수준 r ≈ 0
- LEVI vs 인허가 폐업률 r = −0.430
- KCD vs 상권분석 매출 r = 0.766 (수준), 0.839 (QoQ)

#### 5.8.4 의의
KCD 단일 벤더의 외적 타당성 확보 + 거래 데이터의 도시 모니터링 잠재력 실증.

---

### 5.9 Robustness Audit (4종) — Supplement

#### 5.9.1 audit01 outcome sanity
- Outcome 정의가 데이터 정의에 잘 매핑되는지 점검
- 결론: outcome 분포가 안정적, 정의 변경 시에도 일관

#### 5.9.2 audit02 trivial baseline
- 모델 성능이 "majority class 예측" trivial baseline 대비 충분히 높은지
- 결론: F1 0.639는 trivial(0.40 수준) 대비 압도적

#### 5.9.3 audit03 threshold sensitivity
- Outcome 컷오프 ±0.3σ / ±0.5σ / ±0.7σ에서 결과 일관성
- 결론: 핵심 결과(C1–C6)는 컷오프 변경에서 방향·크기 일관

#### 5.9.4 audit04 cluster validity
- K-Means cluster의 정합성 점검 (silhouette, calibration)
- 결론: K=4가 silhouette·BIC 모두 최적

---

## 6. 새로운 방향성·프레이밍 변화

### 6.1 DSR (Design Science Research) 채택

#### 6.1.1 왜 채택했는가
지난 outline은 "기술경영 진단·예측 도구"라는 톤. V3에서는 EWS와 LEVI를 단순 분석 결과가 아닌 **인공물(artifact)**로 명시하면, 다음과 같은 이점이 생깁니다:
- **방법론적 정당화**: Hevner et al. 2004의 3-cycle (relevance/design/rigor)에 정렬되어, 본 연구가 단순 통계 추정이 아닌 시스템 설계 연구임이 분명해짐
- **평가 기준 강화**: Peffers et al. 2007의 6단계 DSRM에서 (v) 평가 단계는 단순 정확도가 아닌 cost-sensitive utility, 외부 타당성 등 다층 평가를 요구 → 본 연구의 평가 두께 증가
- **상위 학술지 정합**: HICSS·DSS·MISQ 등은 DSR 프레임이 익숙한 venue

#### 6.1.2 어디에 반영되어 있나
- Ch.2 §2.4.3: DSR 방법론 도입
- Ch.4 §4.6 도입부 + §4.7: EWS/LEVI를 artifact로 명시
- Ch.5 §5.7: cost-sensitive evaluation
- Ch.6: DSR artifact 평가 섹션

#### 6.1.3 한글 학위논문에서의 비중
이번 미팅 상의 사항. 옵션은 §8에서 정리.

---

### 6.2 인과 식별 도구 도입

#### 6.2.1 왜 추가했는가
지난 미팅의 한계: "관측자료 기반, 인과효과 아님." Golden Cross의 인과 신호가 충분히 강하면 이 한계를 부분적으로 극복 가능.

#### 6.2.2 어떤 도구
- Granger 1969 인과
- Rosenbaum-Rubin 1983 PSM
- Card-Krueger 1994 DiD
- Two-way Panel FE
- Cox 1972 PH (생존분석)

#### 6.2.3 적용 범위
- C3 (Golden Cross): 본격 인과 식별
- C2 (Volatility Paradox): outcome-conditional Cox로 부분 식별
- C1, C4, C5, C6: 진단·예측·검증 성격 유지

---

### 6.3 산출물 두 갈래 전략

#### 6.3.1 한글 학위논문
- 톤: 기술경영 + DSR
- 메인: 6대 기여 균형, C6(LEVI·지역 모니터링)을 한 축으로 강조
- 분량: 60–90쪽
- 구조: Ch.1–7 한글

#### 6.3.2 영문 top-tier 논문
- 톤: DSR artifact 중심
- 메인: C1–C5 (artifact + causal + paradox + survivorship + hybrid prediction)
- 보조: C6는 Evaluation 섹션의 외부 타당성 단락
- 후보 venue: HICSS 2027 / ICIS 2026 / DSS 저널

#### 6.3.3 공유 자산
- 데이터, 코드, figure, 수치는 **모두 동일** (top_tier/src/, top_tier/outputs/)
- 차이는 톤·구조·강조점뿐

---

### 6.4 파일 구조 일원화

#### 6.4.1 폴더명 변경
- 사용자 요청: `thesis_v2/` → `thesis/`

#### 6.4.2 drafts 분리
- [thesis/drafts/v2/](../drafts/v2/): 구 V2 초안 6개 (Ch.0/1/4/5/6, THESIS_FULL_V2.md)
- [thesis/drafts/v3/](../drafts/v3/): V3 본문 9개 + THESIS_FULL.md 색인

#### 6.4.3 추가 폴더 (오늘 신규)
- [thesis/meeting/](.) — 본 미팅 자료 보관

---

## 7. 학위논문 본문 진행 상태

### 7.1 V3 본문 9개 파일 완성도

| 장 | 파일 경로 | 분량 | V2→V3 변화 | 상태 |
|---|---|---:|---|---|
| 0 | [drafts/v3/ch0_abstract.md](../drafts/v3/ch0_abstract.md) | 8.3K | 6 contributions numbered list로 재작성 | 완료 |
| 1 | [drafts/v3/ch1_introduction.md](../drafts/v3/ch1_introduction.md) | 9.3K | RQ 3→6개, 6대 기여 명시 | 완료 |
| 2 | [drafts/v3/ch2_literature.md](../drafts/v3/ch2_literature.md) | ~14K | §2.4.3 DSR + §2.4.4 생존·인과 + §2.5 C1–C6 매핑 추가 | 완료 |
| 3 | [drafts/v3/ch3_data.md](../drafts/v3/ch3_data.md) | ~13K | §3.3.3 상권분석서비스 + §3.4.1 C1 수치 추가 | 완료 |
| 4 | [drafts/v3/ch4_methodology.md](../drafts/v3/ch4_methodology.md) | 11.6K | DSR 프레임 + C1–C6 분석 방법 | 완료 |
| 5 | [drafts/v3/ch5_results.md](../drafts/v3/ch5_results.md) | 18.1K | C1–C6 순차 보고로 전면 재구성 | 완료 |
| 6 | [drafts/v3/ch6_discussion.md](../drafts/v3/ch6_discussion.md) | 10.7K | DSR artifact 평가 추가 | 완료 |
| 7 | [drafts/v3/ch7_conclusion.md](../drafts/v3/ch7_conclusion.md) | ~6K | 6대 기여별 결론 11문단으로 재작성 | 완료 |
| Ref | [drafts/v3/references.md](../drafts/v3/references.md) | ~7.5K | Cox, KM, Granger, RR, XGBoost, Card-Krueger 추가 | 완료 |

### 7.2 색인 파일

[thesis/drafts/v3/THESIS_FULL.md](../drafts/v3/THESIS_FULL.md) — 다음 정보 포함:
- V2→V3 차이 비교 표
- V3 본문 파일 링크
- P2 통합 체크리스트 (모두 완료 표시)
- 핵심 수치 Quick Reference (KCD 점포 수, 패널, Cox HR, ATT, F1/AUC, EWS utility, LEVI r 등 모두 정리)
- Figure 배치표 (§5.1–§5.10에 어떤 그림이 들어가는지)
- 심사·투고 시나리오

### 7.3 미해결 작업

- **신규 figure (Fig 5.2 — survivorship bias 5-fold comparison bar chart)**: TBD 상태. C1을 시각적으로 강조하기 위함.
- **References 형식**: 현재는 plain text. 학위논문 제출 양식이 BibTeX 또는 특정 스타일 요구하면 변환 필요.

---

## 8. 상의가 필요한 사항 — 옵션별 trade-off

### 8.1 DSR 프레임 채택 강도

| 옵션 | 특징 | 장점 | 단점 |
|---|---|---|---|
| **A. 현행 유지** | DSR을 §2.4.3·Ch.4·Ch.6 평가에 도입, C5에 강하게 적용 | 영문 투고와 정합 | 한글 독자에게 낯선 프레임 |
| B. 확장 | 본문 전체를 DSR 6단계로 재구성 | 영문 투고와 단일 산출물화 | 한글 학위논문 표준에서 이탈 |
| C. 축소 | DSR 언급 최소화, 기술경영 톤 회귀 | 한글 학위논문 표준에 친숙 | 영문 투고와 톤 분리 → 작업량 증가 |

**현 추천**: A (현행 유지). 이유: 영문 투고와 단일 코드·figure 공유 가능, 한글 본문에서도 §2.4.3 한 절·Ch.6 한 절로 부담 적음.

### 8.2 C3 (Golden Cross) 인과 주장 위상

| 옵션 | 특징 |
|---|---|
| **A. 메인 기여로 유지** | 삼각검증의 강도 신뢰, 6대 기여 중 하나로 보고 |
| B. 메인 유지 + 한계 강화 | Ch.6 한계 절에서 잔여 가정 위협(unobserved time-varying confounders 등) 길게 명시 |
| C. 학위논문에서 보조 회귀 | 인과 주장은 영문 투고에 한정, 학위논문은 진단·예측 톤 유지 |

**현 추천**: B. 이유: 인과 주장의 강도는 충분하지만, 학위논문 심사위원이 잠재 confounder를 지적할 수 있으므로 한계를 명확히 해두면 방어가 쉬움.

### 8.3 한글/영문 제출 형식

| 옵션 | 특징 |
|---|---|
| **A. 본문 100% 한글 + 국·영문 초록** (현행 V3) | KAIST MoT 한글 학위 표준 |
| B. 본문 영문 + 한글 요약 | 영문 투고와 단일 산출물 |
| C. 혼합 (Ch.1·7 한글, Ch.4–6 영문) | 한글 톤 + 기술 부분 영문 |

**현 추천**: A. 학위논문과 영문 투고는 별개 산출물로 두는 게 작업 흐름상 효율적.

### 8.4 HICSS / ICIS 동시 투고

| 옵션 | 특징 | 마감 |
|---|---|---|
| **A. ICIS 2026 도전** | 28–30% 승인율, 12p completed research | **D-4 (2026-05-01)** — 매우 임박 |
| **B. HICSS 2027 집중** | 45–50% 승인율, 10p IEEE | 2026-06-15 (60일 여유) |
| C. HICSS + DSS·I&M 확장 2단 | HICSS 통과 후 2027년 하반기 저널 확장 | 장기 |

**현 추천**: B. ICIS는 D-4로 학위논문과 동시 진행이 매우 부담스러움.

### 8.5 학위논문 심사·일정

다음을 결정 필요:
- 심사위원 구성 (KAIST MoT 내부 N인 + 외부 N인)
- 예심·본심 일정
- 데이터 비공개 조항이 심사·논문 공개 가능성에 미치는 영향
- 학위 제출 양식 (KAIST MoT 표준 양식 vs LaTeX 자유)

### 8.6 신규 figure 작성 여부

- **Fig 5.2 (survivorship bias 5-fold comparison bar chart)**: C1을 시각적으로 강조
- 작업량: 1–2시간
- 결정: 작성할지/생략할지

---

## 9. 미팅 진행 시 활용 흐름 (제안)

본 자료를 미팅에서 활용할 수 있는 한 가지 흐름:

1. **§1**로 출발점 재확인 (지난 outline)
2. **§2**의 매핑 표로 "지난 미팅 → 현재"를 한 페이지로 보여줌
3. **§3**의 6대 기여 중 가장 새로운 3개(C1·C2·C3)에 시간 집중
4. **§4**의 외부 데이터 5종을 빠르게 훑음
5. **§5**의 새 실험은 표·수치만 빠르게 (상세는 본 자료에서 사후 참조)
6. **§6**의 DSR·인과식별·산출물 분할 방향성 공유
7. **§7**의 본문 진행 상태 빠르게 확인
8. **§8**의 상의 필요 사항 6가지를 미팅에서 결정

본인 요약본은 §3, §6, §8 중심으로 정리하시면 미팅에서 핵심을 빠르게 전달할 수 있습니다.

---

## 10. 미팅 후 다음 단계 (예정)

1. §8의 6개 상의 사항에 대한 교수님 결정을 본 자료의 상단에 반영
2. (필요 시) Ch.2 DSR 비중 조정
3. (필요 시) Fig 5.2 survivorship bias 그림 작성
4. References 최종 검수 (BibTeX 변환 결정)
5. 국·영문 초록 최종본 확정
6. 심사 일정에 맞춘 출력본 제작
7. (병행) 영문 paper draft 진행 — top_tier/paper_draft/ 의 Results/Discussion/Conclusion 작성

---

*본 자료의 모든 수치는 [thesis/drafts/v3/](../drafts/v3/) 본문, [top_tier/outputs/docs/top_tier_report.md](../../top_tier/outputs/docs/top_tier_report.md), [thesis/drafts/v3/THESIS_FULL.md](../drafts/v3/THESIS_FULL.md) Quick Reference의 V3 최신 수치와 정합합니다.*
