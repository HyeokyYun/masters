# Frontmatter: 국문초록, Abstract, 목차

---

## 국문 초록

본 연구는 한국신용데이터(KCD)가 제공한 서울시 외식업 소상공인 59,089개 점포의 주별 거래 패널(2021년 1월-2023년 8월, 총 658만 관측치)을 활용하여, 개별 점포의 성장·정체·하락 상태를 진단·예측하고 이를 자치구 단위로 집계한 지역 경제 활력 지수(Local Economic Vitality Index, LEVI)가 서울시의 생활인구 동태와 외식업 폐업률 등 도시 경제 지표와 어떤 관계를 맺는지 검토한다.

분석은 미시(Micro)·메소(Meso)·거시(Macro)의 3단 구조로 구성된다. 미시 수준에서는 observed-window 표본(50,635개 생존 점포)을 매출 추세 기울기 기준으로 Growth/Stable/Decline의 3-class 상태로 레이블링하고, 업력 구간별(0-12, 12-24, 24-36, 36-60, 60-120, 120+개월) 다항 로짓 모형으로 드라이버 feature를 분석한다. 또한 post-entry 표본(24,278개 개업 점포)에서 매출 시계열을 클러스터링해 6가지 궤적 패턴(DDZ, DDY, DUY, UUX, UDY, UDZ)을 식별하고, 초기 20-50주 관측 기반 조기 예측을 수행한다. 메소 수준에서는 구별 "Growth 점포 비중 − Decline 점포 비중"을 기본 정의로 한 LEVI를 구축하며 4개 대안 공식과의 상관으로 강건성을 확인한다. 거시 수준에서는 서울 열린데이터광장의 자치구별 생활인구 추계와 서울시 일반음식점 인허가 정보를 전처리하여 자치구×월별 거시 변수를 구축하고, LEVI와의 Pearson·Spearman 상관을 검토한다.

주요 결과는 다음과 같다. 첫째, 통상적 생애주기 이론의 종 모양 궤적(UDY)은 전체 점포의 0.8%에 불과하며, 62.4%의 점포가 개업 직후부터 지속 하락 궤적(DDZ)을 따른다. 둘째, 매출 추세는 전 업력 구간 1위 드라이버이지만 신규 고객 비율의 importance는 업력이 길어질수록 단조 증가하며(12-24개월 2.2에서 60-120개월 7.5로 약 3.4배 증가), 120개월+ 구간에서는 2위로 올라선다. 셋째, 초기 30주 관측 기반 3-class 예측의 weighted F1은 0.669에 도달하며, 해석 가능한 trend·volatility·customer feature의 조합이 cluster label보다 더 큰 성능 기여를 한다. 넷째, 구별 LEVI와 생활인구 변화율의 Pearson 상관은 0.855로 매우 강하며, LEVI는 구의 인구 수준(크기)과는 무관하고 변화의 방향성과만 연결되어 있다. 외식업 폐업률과는 $r = -0.428$의 방향 일관된 음의 상관을 보인다.

본 연구의 기여는 세 가지이다. (1) 거래 데이터 기반 소상공인 진단 프레임워크로서 설문·재무제표에 의존하던 관행을 대체할 수 있는 정량적 대안을 제시하였다. (2) 업력별 드라이버의 이질성을 실증하여 "성숙기 이후의 단선적 쇠퇴"를 가정하는 조직 생애주기 이론에 대한 미시 수준의 반증 증거를 제공한다. (3) 미시 진단과 도시 경제·인구 동태를 잇는 집계 지표(LEVI)를 설계하고, 해당 지표가 서울 자치구의 생활인구 동태와 강한 상관으로 연결됨을 실증하여 거래 데이터의 지역 경제 monitoring 도구로서의 가능성을 제시한다. 본 연구의 결과는 서울시 외식업 2021-2023년 기간에 국한되며, 진단·예측적 성격에 한정된다는 한계를 명시한다.

**주제어**: 소상공인, 생애주기, 거래 데이터, 지역 경제, 생활인구, 조기 예측, 지역 경제 활력 지수

---

## Abstract (English)

This study examines whether weekly transaction data from small food-service businesses can serve both as a diagnostic signal for individual store trajectories and as an aggregate indicator of local economic dynamics. We analyze a large-scale panel of weekly sales for 59,089 independent restaurants in Seoul, Korea (January 2021 – August 2023, 6.58 million store-weeks) provided by Korea Credit Data (KCD), combined with two administrative data sources from the Seoul Open Data portal: district-level Living Population estimates and the full registry of food-service permits including closures.

The analysis proceeds on three linked layers. At the **micro** layer, we define Growth, Stable, and Decline states at the store level based on the slope of monthly-mean log sales over the observed window (n = 50,635 stores). Multinomial logit models fit by business-age bucket (0-12, 12-24, 24-36, 36-60, 60-120, 120+ months) identify feature-level drivers that separate the three states. A parallel post-entry trajectory analysis on 24,278 recently opened stores recovers six recurring patterns (DDZ, DDY, DUY, UUX, UDY, UDZ) and tests whether early 20-50 week observations predict longer-run outcomes. At the **meso** layer, we construct a Local Economic Vitality Index (LEVI) by aggregating store-level labels to Seoul's 25 administrative districts, with the primary formula defined as the Growth minus Decline share. Four alternative specifications are computed to establish robustness. At the **macro** layer, LEVI is correlated with district-level living-population change (2021-2023) and mean monthly closure rate.

Four findings emerge. First, the canonical hump-shaped life cycle (UDY) describes only 0.8% of post-entry trajectories, while 62.4% of stores follow a persistent-decline trajectory (DDZ). Second, sales trend is the dominant driver across all age buckets, but the importance of the new-customer ratio rises monotonically with business age — from 2.19 in the 12-24 month bucket to 7.47 in the 60-120 month bucket (a 3.4-fold increase), becoming the second most important feature in the 120+ month bucket. Third, early-window 3-class prediction using 30 weeks of data achieves weighted F1 of 0.669, with the largest performance gains coming from trend/volatility and customer-behavior blocks rather than cluster labels. Fourth, district-level LEVI correlates at Pearson r = 0.855 with changes in living population over 2021-2023, while being uncorrelated with living-population levels (r ≈ 0) — indicating that LEVI captures directional economic dynamics rather than district size. LEVI correlates at r = -0.428 with external closure rates, with the reduced magnitude attributable to the KCD sample being a subset of Seoul's full restaurant population.

The contribution is threefold. (1) A transaction-based diagnostic framework for small-business lifecycles that replaces survey-based or financial-statement-based approaches. (2) A micro-level refutation of the single life-cycle curve assumption, revealing that new-customer acquisition becomes an increasingly informative signal of growth as stores age. (3) An empirical demonstration that transaction-derived indicators (LEVI) strongly associate with urban population dynamics, positioning real-time transaction data as a candidate leading indicator for local economic monitoring. Results are descriptive and predictive, not causal, and are restricted to Seoul's food-service sector during 2021-2023.

**Keywords**: Small business, life cycle, transaction data, local economy, living population, early prediction, Local Economic Vitality Index

---

## 목차 (Table of Contents)

**국문 초록**  
**Abstract**  
**목차**  
**List of Tables**  
**List of Figures**  

**1. 서론**
 - 1.1 연구 배경
 - 1.2 문제의식
 - 1.3 연구 질문
 - 1.4 연구 기여
 - 1.5 논문의 구성

**2. 이론적 배경 및 선행 연구**
 - 2.1 조직 생애주기 이론과 소상공인 영역 적용
 - 2.2 소상공인 성장·폐업 결정요인 문헌
 - 2.3 거래 데이터·디지털 트레이스 기반 지역 분석
 - 2.4 조기 경보 시스템과 시계열 예측
 - 2.5 연구 격차와 본 연구의 포지셔닝

**3. 데이터**
 - 3.1 KCD 주별 거래 패널
 - 3.2 두 개의 실증 표본
 - 3.3 외부 공공 데이터
 - 3.4 표본 편향과 결측 처리

**4. 연구방법**
 - 4.1 분석 프레임 개관
 - 4.2 Micro 레이어: 개별 점포 상태 진단·예측
 - 4.3 Meso 레이어: LEVI 설계
 - 4.4 Macro 레이어: LEVI와 도시 동태의 관계
 - 4.5 Robustness 설계

**5. 분석 결과**
 - 5.1 Micro Result 1: 이질적 생애주기 궤적
 - 5.2 Micro Result 2: 업력 구간별 드라이버의 차이
 - 5.3 Micro Result 3: 조기 예측의 가능성과 한계
 - 5.4 Meso Result: 자치구별 LEVI 구축
 - 5.5 Macro Result: LEVI와 도시 동태의 관계
 - 5.6 Robustness

**6. 토의**
 - 6.1 이론적 함의
 - 6.2 방법론적 함의
 - 6.3 정책·플랫폼 함의
 - 6.4 연구의 한계
 - 6.5 향후 연구

**7. 결론**

**참고문헌**

**부록 A. Feature 정의표**  
**부록 B. 모델 하이퍼파라미터**  
**부록 C. Robustness 확장표**  
**부록 D. LEVI 구축 재현 코드**  
