# 6. 토의 (v3, top-tier 정합)

## 6.1 이론적 함의

### 6.1.1 단일 생애주기 곡선에 대한 경험적 반증

Boulding(1950)·Miller & Friesen(1984)·Adizes(1979)의 조직 생애주기 이론은 중견·대기업에서 발달한 종 모양 곡선 가정을 토대로 한다. 본 연구는 서울시 외식업 소상공인의 주별 거래 데이터에서 이 가정이 경험적으로 매우 약함을 보였다. Post-entry 표본의 62.4%가 개업 직후부터 지속 하락 궤적을 따르며, 이론이 예측하는 종 모양(UDY)은 0.8%에 불과하다. 이 결과는 기업 생애주기 연구가 소상공인 영역에서 "곡선의 단계"가 아닌 **궤적 유형의 분포**로 재구성되어야 함을 시사한다.

### 6.1.2 Volatility Paradox의 3중 상호작용 해석

본 연구의 이론적 기여 중 가장 정교한 것은 Volatility paradox의 체계적 분해이다. "변동성이 크면 폐업 위험이 크다"(Cox HR 1.09)와 "성장 점포가 변동성이 크다"(단면 mean)의 모순을 (a) survivorship, (b) phase-dependent volatility, (c) inverted-U across deciles, (d) outcome-stratified Cox의 네 가설로 분해했을 때, 각각이 paradox의 일부를 설명하며 총체적으로는 **phase × outcome × survivorship의 3중 상호작용**으로 환원된다. 초기 phase의 변동성은 탐색적 적응으로 Growth와 양립하고, 후기 phase의 변동성은 구조적 붕괴로 Decline을 지시한다. 이 재해석은 기업 변동성을 단조 risk로 보는 전통을 수정하며, Knightian uncertainty 문헌의 "불확실성 양날의 칼" 구도에 경험적 근거를 추가한다.

### 6.1.3 신규 고객 유입의 Golden Cross 효과

§5.5의 삼각 인과 검증은 신규 고객 비율이 단순 상관이 아니라 매출 반등의 선행 지표로 기능할 수 있음을 시사한다. PSM+DiD의 ATT +0.117 log-sales (약 12.4%)는 처치군-통제군 비교에 기반한 인과 해석에 근접한 효과이며, Panel FE의 1주 시차 계수 0.278도 점포·시기 고정효과 통제 후에도 강하게 잔존한다. 이 효과가 업력 구간별 importance 상승(§5.8)과 결합되면, 소상공인 이론은 "성숙기 이후의 단선적 쇠퇴"를 가정하는 관점에서 벗어나 "장기 생존 점포 중 일부가 신규 고객 유입을 통해 재활력을 얻는다"는 이질적 경로를 인정해야 한다.

### 6.1.4 Micro-Meso-Macro 통합 관점

LEVI와 서울시 생활인구 변화율의 Pearson 0.853 상관(§5.9)은 미시 거래 데이터가 도시 경제·인구 동태의 거시 지표로 보존·변환될 수 있음을 실증한다. 이는 기존에 별개 문헌으로 발전해 온 "소상공인 경영 연구"와 "도시 경제학"이 거래 데이터를 매개로 연결될 수 있음을 의미한다. 기술경영 관점에서 이 연결은 **단일 민간 패널의 외적 타당성 확보 메커니즘**으로도 기능한다.

## 6.2 방법론적 함의

### 6.2.1 Hybrid Inductive Bias의 우위

§5.6의 Hybrid Proposed D(F1 0.639, AUC 0.824)가 base 46-feature(F1 0.548)과 개별 feature block(cluster only, change-point only) 모두를 상회한다는 결과는 Fawaz et al.(2019)·Shwartz-Ziv & Armon(2022)이 보고한 "moderate sample + short sequence에서 inductive bias 우위" 경향과 정합한다. 특히 관측 창이 30주로 짧고 표본 규모가 수만 단위인 경우, end-to-end 딥 시퀀스 학습이 요구하는 데이터 헝거를 충족시키기 어렵다. 본 결과는 소상공인 도메인에서 cluster label 같은 중간 수준 표현과 change-point 같은 시계열 요약 통계를 combined inductive bias로 활용하는 것이 실용적 우위를 가짐을 시사한다.

### 6.2.2 Cost-Sensitive 운영 관점의 도입

§5.7의 EWS artifact 평가에서 F1-최적 threshold(0.35)와 cost-sensitive 최적 threshold(0.10)가 크게 다르다는 관찰은, 예측 모델의 성능 보고를 순수 정확도 지표에서 **운영 맥락의 utility function**으로 확장해야 함을 의미한다. 본 연구가 사용한 parameterization($B=10, C_{support}=2, C_{miss}=8$)은 예시적 가정이며, 실제 정책 맥락에서는 해당 파라미터가 이해관계자(지자체, 금융기관, 플랫폼 사업자)에 따라 달라진다. 본 artifact의 설계는 파라미터를 외부 입력으로 받도록 일반화되어 있어 다양한 운영 시나리오에 이식 가능하다.

## 6.3 DSR Artifact 평가

### 6.3.1 Artifact 자체의 가치

Hevner et al.(2004)이 제시한 DSR의 세 축(design as an artifact, problem relevance, research rigor)에 대해 본 연구의 EWS artifact는 다음과 같이 평가된다.

- **Design as an artifact**: 49,007개 점포에 대한 store-level risk score 산출 기능이 구현되어 있고, cost-sensitive threshold selection이 포함된 완결된 산출물이다(`top_tier/outputs/tables/ews_scores_per_store.csv`).
- **Problem relevance**: 한국 소상공인 정책의 생애주기 기반 지원 체계가 자기 기입식 설문에 의존하는 현실에서, 실시간 거래 데이터 기반 조기 경보 artifact의 도입은 직접적 문제 해결 가치를 지닌다.
- **Research rigor**: 5-fold cross-validation, Brier calibration, precision-recall curve, cost-benefit analysis의 네 평가 축을 통해 artifact 성능을 다각도로 검증하였다.

### 6.3.2 External Validity의 제도화

DSR 문헌에서 artifact의 external validity는 종종 명시적 설계 요소로 다루어지지 않는다. 본 연구는 서울시 공개 데이터 기반 cross-validation(§5.9)을 artifact 평가의 필수 요소로 배치하여, 단일 민간 패널의 "in-sample 강함, out-of-sample 약함" 문제를 방법론적으로 부분 해결하였다. 이는 IS/DSR 공동체에서 artifact external validity 평가 관행을 강화하는 방향의 제언으로 읽을 수 있다.

## 6.4 정책·플랫폼 함의

### 6.4.1 생애주기 기반 소상공인 지원 체계의 재설계

현행 "창업·성장·재기" 3단계 지원 체계는 자기 기입식 단계 응답에 의존한다. 본 연구의 결과를 정책에 반영한다면 세 가지 방향의 재설계가 가능하다.

- **DDZ 궤적 조기 탐지**: 전체 점포의 62%가 이 궤적이므로, 개업 후 20-30주 내에 DDZ로 예측되는 점포를 EWS risk score로 탐지해 업종 전환·멘토링을 연결
- **Golden Cross 지원**: 초기 하락 후 반등 조짐이 있는 점포(Granger 비대칭 유의군)에 대해 마케팅·신규 고객 유치 지원을 우선 배정
- **장기 생존 점포의 재활력**: 120m+ 구간에서 nc_rate importance가 최고조에 이르는 결과를 바탕으로, 성숙기 점포의 신규 고객 유치 지원(디지털 전환·SNS 마케팅)을 별도 프로그램으로 운영

### 6.4.2 LEVI 기반 자치구 모니터링

자치구별 LEVI와 생활인구 변화율의 0.853 상관은 LEVI가 자치구 수준 지역 경제 monitoring에서 **실시간 leading indicator 후보**로 기능할 여지를 시사한다. 서울시·자치구 수준에서 월별 LEVI dashboard를 운영한다면, 통상 1-3개월 지연 발표되는 공공 통계보다 빠른 지역 경기 진단이 가능해진다. 이는 상권 지원 예산 배분·소상공인 정책 자금 운영·부동산 임대료 분석 등 다수 정책 맥락에서 활용될 수 있다.

### 6.4.3 KCD 및 POS 사업자 관점

거래 데이터 공급자(KCD 등) 관점에서 LEVI·EWS artifact는 원자료를 넘어선 부가가치 서비스로 상품화될 여지가 있다. 본 연구의 구조를 참고하여 "거래 데이터에서 파생된 지역 진단 지표"를 공공·민간 고객에게 제공하는 비즈니스 모델이 가능하다.

## 6.5 한계

### 6.5.1 인과 해석의 경계

Golden Cross의 PSM+DiD ATT +0.117은 random assignment 수준의 인과 증명이 아니다. 처치 정의 자체가 관측된 nc_rate 상향 돌파 사건에 기반하므로, 관측되지 않은 이질성이 처치와 결과에 동시 영향을 미칠 경우 편향이 남을 수 있다. 본 연구는 Granger·PSM+DiD·FE의 세 방법 일관성을 근거로 "evidence consistent with a causal interpretation" 수준의 해석을 유지하며, 더 강한 인과 증명은 상권 재개발·정책 자금 등 자연실험 기반 후속 연구로 남긴다.

### 6.5.2 표본과 기간 제약

본 연구는 서울특별시 외식업·2021-01 ~ 2023-08 기간을 대상으로 한다. 수도권 외 지역, 비외식업(도소매·서비스·수리업), 장기 안정기 기간에 대한 직접 일반화는 불가하다. 분석 창이 코로나 방역기와 엔데믹 전환기를 포함하는 점도 해석에 영향을 미친다.

### 6.5.3 Survivorship의 잔여 영향

§5.2가 정량화한 5.4배 격차는 observed-window 표본에 내재된 편향의 규모이며, 본 연구의 모든 나머지 결과는 이 편향의 영향 하에 있다. 외부 인허가 데이터를 활용한 검증은 부분적 보정이며 완전한 제거가 아니다. 본 연구는 이 제약을 모든 결과 해석에서 명시한다.

### 6.5.4 재현성 제약

KCD 원자료는 민감한 거래 데이터로 외부 공개가 제한되며, 완전 재현은 불가하다. 본 연구는 (a) 파생 변수·집계 테이블 수준의 자료 공개, (b) 전체 분석 코드의 공개를 통해 재현 가능성을 확보하였다(`top_tier/src/step00-15_*.py`, `thesis/analysis/*.py`). CS/DS top-tier venue 투고 시에는 synthetic/aggregate dataset release가 추가 필요하다.

### 6.5.5 Legacy 결과의 존재

본 연구의 일부 과거 분석(audit01-04, enhanced PSM, multivariate DL robustness)은 원자료 업데이트 전 legacy label에 기반해 수행되었으며, 현재 본문에서는 제외되었다. 최종 저널 확장 단계에서 새 label로 재실행이 필요하다.

## 6.6 향후 연구 방향

1. **타 업종·타 지역 확장**: 도소매·서비스업 등 비외식업, 광역시·중소도시로의 외적 타당성 검증
2. **인과 규명 강화**: 서울시 상권 재개발·정책 자금 등 자연실험 기반 DiD 설계
3. **동 단위 Meso 분석**: KCD 주소를 서울시 1,671개 상권 코드로 공간 조인한 세밀한 LEVI 구축
4. **EWS 실배포**: 파일럿 지자체·기관과 협력하여 artifact를 운영 환경에 배포하고 실제 의사결정에 미치는 영향 평가
5. **시차 leading indicator 검증**: 월 단위 LEVI 시계열로 생활인구·폐업률에 대한 lead-lag 관계를 엄밀히 검정
6. **Multi-modal 통합**: 리뷰·SNS·공공 상권 정보를 결합하여 behavioral trace 기반 종합 진단 모델로 확장
