# Frontmatter v3 (top-tier 정합)

## 국문 초록

본 연구는 서울시 외식업 소상공인의 주별 카드 거래 패널(59,089개 점포, 2021년 1월-2023년 8월, 6.58M 관측치)을 활용하여 기존 생애주기 연구의 방법론적 한계를 체계적으로 극복하고, 진단·예측·의사결정 지원을 통합하는 조기 경보 artifact를 제시한다. 여섯 가지 기여가 도출된다. **첫째**, 분석 패널 내부 폐업률(8.9%)과 바깥 폐업률(48.3%)의 5.4배 격차를 직접 측정하여 기존 lifecycle 연구의 생존 편향 규모를 정량화하였다. **둘째**, Cox PH 모형의 변동성 위험(HR 1.09)과 단면 통계의 "Growth cv > Stable cv" 역설을 (a) survivorship, (b) phase-dependent, (c) inverted-U, (d) outcome-stratified Cox의 네 가설로 분해하여, 초기 변동성은 탐색적 적응으로 Growth와 양립하고 후기 변동성은 구조적 붕괴로 Decline을 지시하는 **phase × outcome × survivorship의 3중 상호작용**으로 재해석하였다. **셋째**, 신규 고객 비율의 매출 반등 선행 효과(Golden Cross)를 Granger(비대칭 유의 8.8%)·PSM+DiD(ATT = +0.117 log-sales, t=18.07, p<1e-72)·Panel Two-way FE(nc_l1 계수 0.278)의 세 방법으로 삼각 검증하였다. **넷째**, 46개 engineered features에 KMeans cluster(K=4)와 change-point feature를 결합한 Hybrid Proposed Model D가 Macro-F1 0.639, AUC 0.824로 base 46-feature(F1 0.548) 대비 유의한 개선을 달성하며, 중간 표본·짧은 관측 창에서 inductive bias가 end-to-end 딥 시퀀스 학습을 상회함을 실증하였다. **다섯째**, 5-fold OOF 확률 기반 store-level Decline risk score를 구축하고 benefit-cost 파라미터 하에 최적 threshold 0.10에서 net utility 43,626을 달성하는 cost-sensitive EWS artifact를 설계·평가하였다. **여섯째**, 개별 상태 레이블을 자치구 단위로 집계한 지역 경제 활력 지수(LEVI)와 서울시 공개 데이터의 상관을 검증하였다(LEVI vs 생활인구 변화율 Pearson 0.853, vs 인허가 폐업률 -0.430, KCD 분기 매출 vs 서울 상권 추정매출 0.766). 본 연구는 Design Science Research 관점에서 artifact의 build-evaluate 사이클을 완료하면서 동시에 생애주기 이론의 경험적 반증·조정을 제시한 통합적 연구이다. 결과는 서울 외식업 2021-2023 기간에 국한되며 진단·예측적 성격에 한정된다.

**주제어**: 소상공인, 생애주기, 거래 데이터, 생존 편향, 변동성 역설, 신규 고객, 조기 경보 시스템, 지역 경제 활력 지수, 설계과학연구

---

## Abstract (English)

This study leverages a weekly card-transaction panel for 59,089 independent restaurants in Seoul (January 2021 – August 2023, 6.58 million store-weeks) provided by Korea Credit Data (KCD), combined with Seoul Open Data sources (Living Population, food-service permit register, Commercial District Analysis). We systematically address four limitations of prior small-business lifecycle research — self-reported stage categorization, the single hump-shaped curve assumption, unmeasured survivorship bias, and the disjoint treatment of prediction and decision support — through a Design Science Research (DSR) framework that integrates survival analysis, causal triangulation, hybrid prediction, and a cost-sensitive early warning system (EWS) artifact, all evaluated against external administrative data.

Six contributions emerge. **(1) Survivorship bias quantified at 5.4-fold**: panel closure rate is 8.9% (n = 48,980) versus 48.3% outside the panel (n = 10,027), revealing that prior lifecycle conclusions are systematically distorted by panel inclusion criteria. **(2) Volatility paradox decomposed**: the Cox PH hazard of volatility (HR = 1.09) coexists with the cross-sectional observation that Growth stores exhibit higher mean cv than Stable stores; we resolve this through four hypotheses (survivorship, phase-dependent volatility, inverted-U across deciles, outcome-stratified Cox) and re-interpret volatility as a three-way interaction between phase, outcome, and survivorship. **(3) Golden Cross causality triangulated**: Granger tests (asymmetric nc→sales significance at 8.8%), propensity-score matched DiD (ATT = +0.117 log-sales, t = 18.07, p < 10⁻⁷²), and two-way fixed-effects panel regression (nc_l1 coefficient 0.278) consistently support a leading relationship of new-customer inflow to sales rebound. **(4) Hybrid prediction beats deep sequence baselines**: Proposed Model D combining 46 engineered features, KMeans (K=4) cluster one-hot, and change-point features achieves Macro-F1 = 0.639 and AUC = 0.824, a +0.091 F1 improvement over the 46-feature baseline. **(5) Cost-sensitive EWS artifact**: 49,007 store-level Decline risk scores with benefit-cost analysis identify optimal threshold 0.10 yielding net utility 43,626; the artifact is evaluated under DSR build-evaluate rigor. **(6) External validity via Seoul public data**: a Local Economic Vitality Index (LEVI) constructed from micro-level labels correlates at Pearson r = 0.853 with district-level living-population change, r = -0.430 with permit-register closure rate, and r = 0.766 with official Commercial District estimated sales — substantially mitigating the external-validity concern of a single-vendor panel.

The study positions small-business lifecycle research at the intersection of empirical refutation of canonical curve assumptions, methodological reconciliation of volatility paradoxes, causally triangulated behavioral signals, inductive-bias prediction at moderate data scale, DSR artifact delivery with operational cost-sensitivity, and transaction-based micro-to-meso-to-macro integration with urban economics. Results are descriptive and predictive, not causal in the randomized-assignment sense, and are restricted to Seoul's food-service sector during 2021-2023.

**Keywords**: Small business lifecycle, transaction data, survivorship bias, volatility paradox, leading indicator, early warning system, Local Economic Vitality Index, Design Science Research

---

## 목차 (v3)

**국문 초록** · **Abstract** · **목차** · **List of Tables** · **List of Figures**

**1. 서론**
 - 1.1 연구 배경
 - 1.2 문제의식: 네 가지 한계
 - 1.3 연구 질문 (RQ1-RQ6)
 - 1.4 연구 기여 (C1-C6)
 - 1.5 학문적 포지셔닝
 - 1.6 논문의 구성

**2. 이론적 배경 및 선행 연구**
 - 2.1 조직 생애주기 이론과 소상공인 영역
 - 2.2 소상공인 성장·폐업 결정요인
 - 2.3 거래 데이터·디지털 트레이스 기반 지역 분석
 - 2.4 조기 경보 시스템과 Design Science Research
 - 2.5 시계열 표현 학습과 inductive bias
 - 2.6 연구 격차와 본 연구의 포지셔닝

**3. 데이터**
 - 3.1 KCD 주별 거래 패널
 - 3.2 두 개의 실증 표본
 - 3.3 외부 공공 데이터 (생활인구, 인허가, 상권분석서비스)
 - 3.4 표본 편향과 결측 처리

**4. 연구방법**
 - 4.1 분석 프레임 개관 (DSR build-evaluate)
 - 4.2 Survivorship bias 정량화 (C1)
 - 4.3 KM · Cox PH 생존 분석
 - 4.4 Volatility paradox 분해 (C2)
 - 4.5 Golden Cross 인과 삼각 검증 (C3)
 - 4.6 Hybrid prediction (C4) + EWS artifact (C5)
 - 4.7 LEVI 설계 및 외부 검증 (C6)
 - 4.8 Robustness 설계

**5. 분석 결과**
 - 5.1 C0 사전 결과: 단일 생애주기 곡선 반증
 - 5.2 C1 Survivorship bias 5배 정량화
 - 5.3 KM · Cox PH 생존·hazard
 - 5.4 C2 Volatility paradox 분해 (H1-H4)
 - 5.5 C3 Golden Cross 인과 삼각 검증
 - 5.6 C4 Hybrid prediction 비교
 - 5.7 C5 EWS artifact + cost-benefit
 - 5.8 업력 bucket별 driver
 - 5.9 C6 LEVI와 외부 검증
 - 5.10 Robustness

**6. 토의**
 - 6.1 이론적 함의
 - 6.2 방법론적 함의
 - 6.3 DSR artifact 평가
 - 6.4 정책·플랫폼 함의
 - 6.5 한계
 - 6.6 향후 연구

**7. 결론**

**참고문헌**

**부록 A. Feature 정의표**  
**부록 B. 모델 하이퍼파라미터 / Cox 비례위험 가정 검정 결과**  
**부록 C. Robustness 확장표 (컷오프·관측창·LEVI 공식·업종·하위기간)**  
**부록 D. EWS 재현 코드 및 ews_scores_per_store.csv 변수 사전**
