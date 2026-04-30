# V1 — 지난 미팅 outline (점포 단위 분석만)

작성 시점: 2026-04-XX (지난 개별미팅 발표)
상태: outline 단계 — 공식 본문 작성 전
중심 메시지: 주별 거래 데이터로 본 소상공인 생애주기의 **이중 렌즈** (post-entry trajectory × observed-window state)

---

## 0. V1의 정체성

V1은 **본 학위논문의 출발점**입니다. 이 시점에는 아래의 8개 섹션 outline만 있었고, 정식 본문(Ch.1–Ch.7) 초안은 아직 없었습니다. 사용한 데이터는 KCD 주별 거래 패널뿐이며, 외부 공공 데이터·인과 식별·DSR 같은 후속 확장은 V1에 포함되지 않았습니다.

V1의 한 줄 메시지:

> "주별 거래 데이터로 보면 소상공인 생애주기는 (post-entry trajectory) × (observed-window state)의 **이중 렌즈**로 봐야 한다. 초기 30주 거래 정보만으로도 의미 있는 진단·예측이 가능하다."

---

## 1. V1 outline (8개 섹션)

### 1. Introduction

서울 외식업 소상공인의 생존, 성장, 쇠퇴를 주별 거래 데이터로 진단.

기존 생애주기 관점의 한계: 창업 → 성장 → 성숙 → 쇠퇴의 단일 곡선으로 설명하기 어려움.

핵심 질문 3개:
1. 개업 업장의 성장 방향성은 어떤 요인에 따라 다른가
2. 전체 생존 업장의 Growth/Stable/Decline 상태는 업력에 따라 어떻게 달라지는가
3. 초기 거래 정보만으로 향후 상태를 어느 정도 예측할 수 있는가

### 2. Data and Empirical Design

- KCD 주별 거래 데이터 설명
- 서울 외식업 소상공인 표본 정의
- 업장 단위 panel 구성
- 주요 변수: 매출 수준, trend slope, volatility, MDD, 신규 고객 비율, 업력, 지역/상권 경쟁 지표
- 두 가지 분석 정의:
  - 개업 직후 post-entry trajectory
  - 전체 생존 업장의 observed-window Growth/Stable/Decline

### 3. Post-Entry Trajectory Heterogeneity

- 개업 직후 업장의 매출 trajectory 유형 제시
- 12-class trajectory label 설명 (DD, DU, UU, UD 등 초기 방향성과 후속 상태의 조합)
- 핵심 메시지: 초기 소상공인 경로는 단일 성장 곡선이 아니라 여러 경로로 분화됨
- 단, 12-class 자체를 예측 대상으로 삼으면 난도가 높다는 점도 명시

### 4. Full-Sample Observed-Window Life-Cycle States

- 전체 생존 업장을 Growth/Stable/Decline으로 분류
- 업력 구간별 상태 분포 분석
- 핵심 메시지: 전체 sample에서는 개업 직후 trajectory와 다른 observed-window 상태 구조가 나타남
- 업력이 높아질수록 단순 쇠퇴만 증가하는 것이 아니라 Growth/Stable/Decline 구성이 다르게 나타남

### 5. Drivers by Business Age

- 업력 bucket별 Growth/Stable/Decline driver 분석
- 핵심 변수: trend_slope, MDD, 신규 고객 비율, volatility, category/local context
- 핵심 메시지: 모든 업력에 같은 driver가 작동하는 것이 아니라, 업력 구간별로 설명 변수가 달라짐

### 6. Early Prediction of Life-Cycle State

- 20주, 30주, 40주, 50주 early window별 예측 성능
- 12-class trajectory 예측과 3-class Growth/Stable/Decline 예측 비교
- feature block ablation: level only, trend/volatility 추가, customer behavior 추가, local context 추가, cluster 추가
- 핵심 메시지: 예측 성능 개선은 cluster 자체보다 trend/volatility, customer behavior, local context에서 주로 발생

### 7. Robustness and Discussion

- volatility 정의 재검토
- 신규 고객 비율의 역할
- UDX/inflection/golden cross 계열 결과는 보조 분석으로 배치
- practical targeting metric
- 한계:
  - 관측자료 기반, 인과효과 아님
  - 서울 외식업 표본에 한정
  - 생존 업장 중심 sample selection 가능성

### 8. Conclusion

- 소상공인 생애주기는 단일 곡선이 아니라 trajectory/state의 이중 구조로 봐야 함
- 주별 거래 데이터는 조기 진단과 예측에 유용함
- 정책/금융/상권 모니터링에서 조기 경보 지표로 확장 가능

---

## 2. V1 시점의 사용 자원

### 2.1 데이터

- KCD 주별 거래 패널 (2021-01 ~ 2023-08, 142주, ~59,000개 점포)
- 외부 공공 데이터 **사용하지 않음**

### 2.2 분석 도구

- 시계열 클러스터링 (K-Means, K-Shape 비교)
- Multinomial Logit (업력별 driver)
- Gradient Boosting (조기 예측)
- Feature ablation

### 2.3 사용하지 않은 도구 (V2·V3에서 도입)

- 서울시 생활인구·인허가·상권분석서비스 데이터
- LEVI 자치구 집계 지수
- Cox 비례위험 모형, Kaplan-Meier 생존함수
- Granger 인과 검정, PSM, DiD, Two-way Panel FE
- Hybrid 64D representation (cluster + change-point)
- Cost-sensitive threshold + net utility (EWS)
- DSR (Design Science Research) 프레임

---

## 3. V1 시점의 3대 기여

| 기여 | 내용 |
|---|---|
| 기여 1 | 거래 궤적의 이질성 — post-entry는 단일 곡선이 아님 |
| 기여 2 | 업력별 driver의 차별성 — 신규고객 importance는 업력과 함께 단조 증가 |
| 기여 3 | 초기 30주 거래 정보로 조기 예측 가능 (3-class GBM weighted F1 0.572) |

---

## 4. V1 시점에 인지된 한계

지난 미팅에서 명시했던 한계:

1. **인과 해석 불가**: 진단·예측 틀임을 명시
2. **단일 도메인**: 서울·외식업·2021–2023
3. **생존 편향**: 분석 표본이 생존자 중심
4. **재현성 제한**: 데이터 비공개

이 4가지 한계 중 **(1) 인과 해석 불가**와 **(3) 생존 편향의 크기**는 V2·V3에서 새로 도입한 도구로 부분적으로 극복하게 됩니다. 그 변화의 추적은 [thesis/meeting/260428_version_evolution.md](../../meeting/260428_version_evolution.md) 참조.

---

## 5. V1 → V2 전환의 동기 (참고)

V1을 마무리하고 자료를 다시 들여다보면서 다음 질문이 떠올랐습니다.

> "KCD는 자사 가맹점만 포함된 단일 벤더 패널이다. 우리 결과가 서울시 외식업 전체 동태와 일치하는지를 어떻게 검증할 것인가?"

이 질문에 답하려면 KCD 외부에서 측정된 **인구·매출·점포 동태** 자료가 필요합니다. 그래서 V2에서:

- 서울시 생활인구 (자치구 단위)
- 서울시 일반음식점 인허가 (전수)
- 서울시 상권분석서비스 (자치구·배후지 단위)

세 종류 외부 자료를 도입하고, 점포 단위 결과를 자치구로 집계한 LEVI를 설계해 외부 자료와 상관 검증.

V2의 구체 결과는 [thesis/drafts/v2/](../v2/) 본문 참조.
