# KCD 소상공인 생애주기 연구 Top-Tier 발전 전략 리뷰

작성일: 2026-04-16  
검토 범위: `docs/KCD_FINAL.pdf`, `original_data/weekly.parquet`, `original_data/meta.csv`, 날짜별 실험 폴더, 논문화 준비 문서, 주요 결과 표/그림

## 1. 결론부터

현재 연구는 석사 1저자 논문으로는 충분히 발전 가능성이 있습니다. 다만 지금 상태 그대로 top-tier CS/DS/IS/MIS/Economics outlet에 제출하기에는 기여가 너무 넓고, 인과 주장과 예측 주장 사이의 정합성이 약하며, 일부 초기 주장과 최신 결과가 충돌합니다.

가장 좋은 발전 방향은 다음입니다.

> 소상공인 생애주기는 단일한 창업-성장-성숙-쇠퇴 곡선이 아니다. 주별 거래 데이터는 개업 직후의 post-entry trajectory와 전체 생존 점포의 observed-window Growth/Stable/Decline 상태가 서로 다른 실증 렌즈임을 보여준다.

이 주장을 중심으로 논문을 좁히면, 현실적인 1저자 석사 논문 타깃은 다음 순서가 좋습니다.

1. 석사논문 및 국내/아시아권 학회: 현 결과를 정리해 안정적으로 제출
2. ICIS/ECIS/PACIS/WISE/CIST 계열: IS/MIS의 데이터 기반 진단 시스템 또는 digital trace 기반 small-business analytics로 포지셔닝
3. Decision Support Systems, Information & Management, Small Business Economics: 저널 확장
4. MISQ/ISR/Management Science/KDD/WWW/AAAI/NeurIPS Datasets Track급: 추가 데이터, 강한 식별전략, 공개 가능한 benchmark 또는 field validation이 있을 때만 도전

## 2. 검토한 자료의 현재 구조

전체 저장소는 3,547개 파일로 구성되어 있습니다. 주요 파일 유형은 CSV 1,032개, Python 816개, PNG 332개, Markdown 168개, TXT 129개, Parquet 20개, PDF 14개입니다. 핵심 연구 흐름은 다음과 같습니다.

| 구간 | 역할 | 판단 |
|---|---|---|
| `docs/KCD_FINAL.pdf` | baseline project, 기존 KCD 최종보고서 | 동기, 데이터 설명, 초기 trajectory framing은 유지. 최신 수치와 main result는 교체 필요 |
| `original_data/weekly.parquet`, `meta.csv` | 원자료 | 서울 외식업 59,089개 점포, 2021-01-01부터 2023-08-28까지 142주 관측 |
| `260121`, `260127` | 초기 clustering, LSTM, determinant analysis | exploratory 또는 appendix용 |
| `260204`-`260224` | UDX, inflection, prediction ablation | trajectory feature의 유용성 근거. K-shape 주장은 과장 금지 |
| `260303` | robustness, practical impact | appendix 및 실무적 타깃팅 근거로 중요 |
| `260319_cur`, `260321_cur` | post-entry trajectory, forecasting windows | Main Result 1과 3의 핵심 |
| `260325` | volatility, new customer, competition, feature ablation | 기존 주장을 정리하고 과장된 해석을 줄이는 최신 분석 |
| `260326_fullsample` | 전체 생존 점포 observed-window 분석 | Main Result 1과 2의 핵심 |
| `docs/thesis_figures` | 논문용 Figure 1-3 정리 | 현재 논문화에 가장 바로 쓸 수 있는 산출물 |

## 3. 원자료 확인 결과

### 3.1 `meta.csv`

- 점포 수: 59,089
- 변수 수: 14
- 지역: 서울특별시만 포함
- 주요 업종 depth 2:
  - 한식 19,308
  - 카페 9,206
  - 술집 7,863
  - 패스트푸드 4,987
  - 일식 3,910
  - 분식 2,863
  - 양식 2,850
- 배달 연결 점포: 10,064개
- 주요 결측:
  - 점포 면적 `business_square_size`: 59.1%
  - 점주 연령 `age`: 17.1%
  - `dong`: 15.9%
- `open_month`: 1977-08부터 2023-10까지 존재, 결측 41개

### 3.2 `weekly.parquet`

- 행 수: 6,582,263
- 변수 수: 12
- 점포 수: 59,089
- 기간: 2021-01-01부터 2023-08-28까지 142개 주차
- 최소 52주 이상 관측 점포: 50,635개
- 최소 104주 이상 관측 점포: 40,732개
- 142주 모두 관측 점포: 23,594개
- 주요 결측:
  - `sales_invoice`: 99.3%
  - `purchase_card`: 99.5%
  - `sales_delivery`: 82.6%
  - `purchase_invoice`: 75.5%
  - `sales_card`, `customer`: 13.6%

중요한 점은, baseline 보고서의 66,667개 및 2019-2023 표현과 현재 원자료의 59,089개 및 2021-2023 관측창이 다르다는 것입니다. 최종 논문에서는 반드시 표본 버전을 명확히 분리해야 합니다.

## 4. 현재 연구의 강점

1. 대규모 실거래 기반 데이터입니다. 설문 기반 소상공인 연구보다 관측 빈도와 행동 기반 측정에서 강점이 있습니다.
2. 단일 생애주기 곡선을 부정하고 trajectory heterogeneity를 보여주는 문제의식이 좋습니다.
3. `post-entry trajectory`와 `observed-window state`를 분리한 최신 구조가 설득력 있습니다.
4. 50,635개 생존 점포에 대해 업력 bucket별 Growth/Stable/Decline driver를 분석한 결과가 탄탄합니다.
5. 예측에서는 level-only 대비 trend/volatility, customer behavior, local context가 성능을 올린다는 feature-block 결과가 명확합니다.
6. 논문용 Figure 1-3이 이미 `docs/thesis_figures`에 정리되어 있어 빠르게 manuscript로 옮길 수 있습니다.

## 5. 치명적 약점과 수정 방향

### 5.1 표본 선택과 생존 편향

`260326_fullsample`의 observed-window 분석은 50,635개 생존 또는 관측 가능 점포 기준입니다. 업력이 길수록 Growth 비중이 높고 Decline 비중이 낮아지는 결과는 실제 생애주기라기보다 survivor stock의 단면일 가능성이 큽니다.

수정 방향:

- 논문 본문에서 "surviving-store observed-window state"라고 명시
- 폐업 또는 관측 중단을 outcome으로 둔 survival analysis 추가
- 최소한 censoring/attrition table을 넣기
- 가능하면 서울시 인허가 폐업일 데이터와 매칭

### 5.2 인과 주장의 부족

신규 고객 비율, volatility, MDD가 Growth/Decline과 연결된다는 결과는 현재로서는 predictive/descriptive association입니다. "신규 고객이 성장을 유발한다" 또는 "골든크로스가 반등을 만든다"라고 쓰면 top-tier 리뷰에서 바로 공격받습니다.

수정 방향:

- 본문 표현을 "predictive signal", "associated with", "diagnostic marker"로 제한
- 골든크로스는 appendix 또는 exploratory result로 이동
- Granger-style lead-lag test, event-study pre-trend, placebo timing test 추가
- 정책 효과를 말하려면 DiD/RD/IV가 필요

### 5.3 클러스터링 품질과 방법론 novelty

baseline 보고서의 DTW/K-means clustering은 silhouette 0.03-0.07 수준으로 분리력이 약합니다. 또한 K-shape를 핵심 방법론 혁신으로 내세우기에는 이후 비교에서 안정성이 약했습니다.

수정 방향:

- 클러스터링을 "classification target" 또는 "behavioral state construction"의 보조 도구로 낮추기
- 핵심 기여를 새로운 clustering algorithm이 아니라 transaction-based lifecycle diagnosis로 이동
- 클러스터 품질 지표를 투명하게 보고하고, label robustness를 appendix에 배치

### 5.4 예측 성능 서사의 정합성

`260224` 계열에서는 UDX/inflection 추가 후 F1 0.84가 보이지만, `260321_cur`의 30주 early prediction은 3-class GBM weighted F1 0.572입니다. 두 숫자는 서로 다른 task일 가능성이 큽니다.

수정 방향:

- "30주 예측 F1 0.84"를 그대로 main claim으로 쓰지 않기
- 예측 task를 세 가지로 분리:
  - 기존 전체 정보 기반 classification
  - early-window 3-class prediction
  - 12-class trajectory prediction
- Main Result 3은 "level-only 대비 feature block gain"으로 재구성

### 5.5 데이터 공개와 재현성

KDD, WWW, NeurIPS Datasets, Management Science류는 데이터와 코드 disclosure를 강하게 요구합니다. KCD 원자료가 비공개라면 CS/DS top-tier는 훨씬 어렵습니다.

수정 방향:

- 공개 가능한 synthetic data 또는 aggregate benchmark release 설계
- 변수 정의, 전처리, 표본 구성, label construction code를 하나의 재현 파이프라인으로 정리
- proprietary data exception 및 IRB/privacy statement 준비

## 6. 추천 논문 포지셔닝

### 추천 중심 논문

영문 가제:

> Diagnosing Small-Business Life-Cycle States from Weekly Transaction Data: Post-Entry Trajectories and Observed-Window Evidence

핵심 research question:

> How can weekly transaction data be used to diagnose heterogeneous small-business life-cycle states, and what early signals improve prediction beyond level-only store characteristics?

핵심 기여:

1. Survey/age-based lifecycle 대신 weekly transaction-based lifecycle diagnosis 제안
2. Post-entry trajectory와 observed-window state를 분리하는 empirical design 제시
3. 업력별 driver가 다름을 보임: trend, MDD, new-customer ratio
4. Early prediction에서 level-only보다 temporal dynamics와 customer/local context가 중요함을 보임

## 7. Main Results 재구성

### Main Result 1: 두 개의 실증 렌즈가 필요하다

주장:

> 개업 직후 trajectory는 매우 이질적이며, 전체 생존 점포의 observed-window Growth/Stable/Decline 분포와 같은 것이 아니다.

핵심 근거:

- `260319_cur`: 12개 trajectory label 및 `fig01_trajectories.png`
- `260326_fullsample`: 50,635개 점포 중 Growth 40.0%, Stable 38.2%, Decline 21.7%
- 업력별로 older bucket에서 Growth 비중 상승, Decline 비중 하락

주의:

- 이것을 "업력이 길수록 성장한다"라고 쓰면 안 됩니다.
- "surviving-store observed-window pattern"이라고 제한해야 합니다.

### Main Result 2: 업력별 driver가 다르다

주장:

> Sales trend는 전 업력 구간에서 가장 강한 discriminator이고, MDD는 Decline과, 신규 고객 비율은 특히 12개월 이후 Growth/dynamic state와 연결된다.

핵심 근거:

- `260326_fullsample/outputs/tables/fullsample_age_bucket_feature_top5.csv`
- `trend_slope`는 모든 age bucket에서 압도적 1위
- 12-24개월부터 `nc_rate`가 상위 feature로 등장
- 24-36개월, 60-120개월 구간에서 MDD와 신규 고객 비율의 해석력이 강함

주의:

- 신규 고객 비율을 causal driver로 쓰지 말고 diagnostic/predictive marker로 쓰기
- 점주 연령, 점포 면적, 동 정보 결측 처리 민감도 필요

### Main Result 3: 조기 예측은 cluster보다 feature block이 중요하다

주장:

> 초기 정보 기반 lifecycle state 예측에서 level-only features보다 trend/volatility, customer behavior, local context가 성능을 높이며, cluster는 추가 기여가 작다.

핵심 근거:

- `260325/outputs/tables/forecast_feature_ablation_classification.csv`
- Weighted F1:
  - level-only: 0.5620
  - plus trend/volatility: 0.6333
  - plus customer behavior: 0.6540
  - plus local context: 0.6692
  - plus cluster: 0.6690
- `260321_cur`: 3-class early prediction은 20주 F1 0.542, 30주 0.572, 40주 0.600, 50주 0.631

주의:

- "30주만으로 F1 0.84"가 아니라, task별 성능을 정확히 분리해야 합니다.
- Top-tier용으로는 out-of-time validation이 필수입니다.

## 8. 분야별 outlet 전략

### 8.1 MIS/IS

가장 유망합니다. 데이터 기반 진단 시스템, digital trace, decision support, small-business analytics로 포지셔닝할 수 있습니다.

적합 후보:

- ICIS, ECIS, PACIS, WISE, CIST
- Information & Management
- Decision Support Systems
- ISR/MISQ는 장기 목표

ISR/MISQ급으로 가려면:

- 이론 기여가 필요합니다. 예: small-business lifecycle theory를 transaction-based diagnostic states로 재정의
- artifact evaluation 또는 expert/field validation이 필요합니다.
- 단순 ML 성능보다 "왜 IS artifact인가", "어떤 의사결정을 바꾸는가"가 명확해야 합니다.

### 8.2 Data Science / CS

KDD/WWW/AAAI/TKDE류는 지금 상태로는 어렵습니다. 방법론 novelty가 부족하고 데이터 공개 제약이 큽니다.

가능한 우회:

- KDD Applied Data Science track: 실제 산업 문제와 대규모 transaction data, deployment 가능성 강조
- KDD Datasets & Benchmarks track: 공개 가능한 benchmark/synthetic dataset 필요
- TKDE/DMKD: 방법론을 더 일반화하고 SOTA 비교, ablation, scalability 추가

KDD 2026의 경우 공식 CFP상 두 submission cycle이 있었고, 2026 second cycle paper deadline은 2026-02-08로 이미 지났습니다. 다음 KDD cycle을 노리는 것이 현실적입니다.

### 8.3 Economics / Entrepreneurship

Small Business Economics가 가장 현실적인 저널 타깃입니다. 단, 이 분야에서는 인과 식별과 survival/selection handling이 중요합니다.

적합 후보:

- Small Business Economics
- Journal of Business Venturing Insights
- Research Policy 또는 Journal of Business Venturing은 장기 목표
- Regional Studies는 지역/상권 정책으로 확장할 때 가능

필요 보강:

- survival analysis
- entry/exit dynamics
- 폐업일 또는 인허가 자료 매칭
- 코로나 정책 충격 또는 지역 상권 충격을 활용한 quasi-experimental design

### 8.4 Management Science / OR / OM

Management Science는 지금 상태로는 매우 높습니다. 다만 decision analytics, risk targeting, intervention allocation으로 확장하면 장기적으로 가능성이 있습니다.

필요 보강:

- 예측에서 끝나지 않고 resource allocation 또는 intervention policy를 제시
- top-decile lift, intervention lead window를 실제 비용-효과 분석으로 연결
- disclosure plan과 reproducibility 준비

## 9. 6개월 발전 로드맵

### 1개월차: 논문 claim 정리

- baseline report와 최신 분석의 표본/수치 불일치 정리
- claim-to-evidence table 완성
- Figure 1-3을 manuscript용으로 고정
- 용어 정의: post-entry trajectory, observed-window state, Growth/Stable/Decline, UDX

### 2개월차: 표본 선택과 robustness

- attrition/censoring table 추가
- 최소 관측주차 30/52/78/104주 민감도 분석
- 업종별, 구별, 코로나 subperiod별 robustness
- 결측 민감도: age, dong, square size

### 3개월차: 예측 실험 재정리

- task별 성능 표준화
- out-of-time validation: earlier weeks train, later cohorts test
- class imbalance metric: macro F1, class-specific recall, balanced accuracy
- calibration, lift curve, top-decile targeting 추가

### 4개월차: 인과가 아닌 진단 논문으로 쓰기

- Literature review: small business dynamics, lifecycle theory, digital trace analytics, early warning systems
- Methods: label construction과 feature blocks를 투명하게 설명
- Results: 세 main result 중심으로 정리

### 5개월차: top-tier용 보강판 준비

- 가능하면 서울시 인허가 폐업일 매칭
- survival model 추가
- external validity: 다른 지역/업종 일부라도 추가
- 데이터 공개 불가 시 synthetic/aggregate reproducibility pack 설계

### 6개월차: 제출

- 석사논문 제출용 원고 완성
- IS conference 또는 entrepreneurship/data science workshop 제출
- 저널 확장용 appendix 정리

## 10. 지금 당장 할 일

1. 논문 제목과 핵심 claim을 "two empirical lenses"로 고정
2. `KCD_FINAL.pdf`의 66,667개/2019-2023 표현과 현재 원자료 59,089개/2021-2023 차이를 정확히 정리
3. `docs/thesis_figures`의 Figure 1-3을 중심으로 본문 구성
4. "golden cross", "growth volatility", "K-shape innovation", "cluster가 예측 핵심" 주장을 본문 중심에서 내리기
5. survival/attrition analysis를 새 폴더에서 추가 분석하기

## 11. 추천 abstract 방향

This study uses weekly transaction records from Seoul food-service establishments to examine whether small-business life cycles can be diagnosed from observed sales and customer dynamics. Rather than treating the life cycle as a single start-up-growth-maturity-decline curve, the study separates two empirical lenses: post-entry trajectories among recently opened establishments and observed-window Growth, Stable, and Decline states among surviving stores. Using 6.58 million weekly observations for 59,089 establishments, the analysis documents substantial heterogeneity in early trajectories and shows that the full surviving-store sample exhibits a different distribution of current states. Across business-age buckets, sales trend is the most consistent discriminator of Growth and Decline, while maximum drawdown and the new-customer ratio provide additional diagnostic information, especially after the earliest stage. Early prediction exercises show that temporal dynamics and customer/local-context features improve predictive performance over level-only specifications, whereas cluster labels add limited incremental value once these features are included. The findings contribute a transaction-based diagnostic framework for small-business dynamics and offer practical implications for early risk monitoring, while remaining descriptive rather than causal.

## 12. 참고한 외부 outlet 정보

- KDD 2026 CFP: https://kdd2026.kdd.org/datasets-and-benchmarks-track-call-for-papers/
- Management Science submission guidelines: https://pubsonline.informs.org/page/mnsc/submission-guidelines
- Small Business Economics journal page: https://link.springer.com/journal/11187

