# 초록

## 국문 초록

소상공인 점포의 성장과 쇠퇴는 지역경제 모니터링과 금융지원 정책에서 중요한
관찰 대상이지만, 기존 행정통계는 점포 단위의 동태적 변화를 조기에 포착하는 데
한계가 있다. 본 연구는 서울시 외식업 점포의 주간 카드거래 데이터를 활용해, 영업
초기 거래 패턴이 이후 점포의 생애주기 상태(Growth/Stable/Decline)를 예측할 수
있는지를 분석한다. 분석 대상은 2021년 1월부터 2023년 8월까지 142주 동안
관측된 약 5만 9천 개 점포이며, 초기 1–3개월 윈도우의 매출, 고객, 신규 고객,
변동성, 추세 등 43개 피처를 입력으로 사용한다.

본 연구의 핵심 방법론적 쟁점은 계절성이다. 기존의 라이프사이클 분류 연구는
"마지막 30주" 또는 전체 기간 기울기로 라벨을 정의해, 데이터 컷오프(2023년 8월)
근처의 휴가 시즌이 결과에 그대로 들어간다. 이 confound를 분리하기 위해 본
연구는 feature window와 target window를 같은 캘린더 월로 정렬한 rolling-window
설계를 도입한다. 시작연도(2021/2022) × 시작월(1–12) × 윈도우 길이(1/2/3개월) ×
타겟 오프셋(1년/2년 후) 80개 specification을 모두 평가한다.

분석 결과는 세 가지로 정리된다. 첫째, 시즌 정렬 시 macro-F1은 시작월에 따라
0.43에서 0.54 사이에서 진폭 0.10으로 흔들리며, 윈도우 길이 효과(약 0.02)나
시작연도 효과(0.01 미만)보다 훨씬 크다. 즉 시즌 confound가 라벨/모델 정확도
양쪽에서 결정적이다. 둘째, 코로나 시기(2021 시작)와 회복기(2022 시작) panel의
정확도 차이는 평균 0.01 미만으로, 코로나 영향이 본 분석의 결과를 좌우하지
않는다. 셋째, baseline + cluster + change-point의 hybrid representation은
시즌 정렬 7개 대표 panel × Stratified 5-fold CV 기준 평균 Δ(D−A) = +0.0022
macro-F1로, 5% 유의는 1/7 panel(`sy2022_sm03_w3m_off1`, p=0.026)에서만
관찰된다. 라벨이 편중된 시즌 panel에서만 cluster + change-point가 추가
정보를 제공하는 **조건부 contribution** 양상이다.

본 연구는 두 가지로 기여한다. 첫째, 시즌 정렬 rolling-window 설계는 기존
late-window outcome 정의의 취약성을 정량적으로 드러내고, 카드거래 기반 점포
생애주기 분류 연구가 라벨 시점에 의해 inflate될 수 있음을 80 specification
수준에서 입증한다. 둘째, hybrid representation의 향상 효과가 라벨/시즌 분포에
의존적이라는 발견은, 동일 데이터·동일 모델이라도 라벨 정의가 다르면 결론이
바뀔 수 있음을 보여준다. LEVI 도시경제 활력 지수, EWS 조기 쇠퇴 경보, 외부
공공 데이터와의 외적 타당도 검증 등은 본 논문의 본문 기여로 다루지 않고
후속 연구 및 응용 영역으로 분리한다.

주요어: 소상공인, 카드거래 데이터, 생애주기 예측, 조기 분류, 계절성 통제,
롤링 윈도우 검증, 외식업

## English Abstract

Small-business growth and decline are key signals for local economic
monitoring and credit support policy, but conventional administrative
statistics rarely capture store-level dynamics at an early stage. This thesis
asks whether early transaction patterns predict the subsequent lifecycle
state — Growth, Stable, or Decline — of food-service stores in Seoul. We use
weekly card-transaction data from 2021-01-01 through 2023-08-28, covering
roughly 59,000 stores across 142 weeks, and extract 43 features (sales,
customer counts, new-customer share, volatility, trend) over a 1–3 month
early window.

The methodological focus is seasonality. Prior store-lifecycle work labels
outcomes from a fixed "last 30 weeks" or whole-period slope, which in this
dataset always falls into mid-2023 summer holiday weeks and confounds
seasonal demand with lifecycle dynamics. We address this by aligning the
feature window and the target window to the same calendar months, and
evaluate 80 valid specifications across start-year (2021 / 2022), start-month
(1–12), window length (1, 2, or 3 months), and target offset (one or two
years ahead).

Three findings emerge. (1) After seasonal alignment, macro-F1 ranges from
0.43 to 0.54 across start months, an amplitude of 0.10 — substantially larger
than the effect of window length (~0.02) or start year (<0.01). Seasonality
dominates the labeling and model-accuracy variation. (2) Pre-recovery (2021
start) and recovery (2022 start) panels differ by less than 0.01 macro-F1 on
average; the residual COVID effect does not drive the main results.
(3) The hybrid representation that adds KMeans cluster labels and a
change-point feature on top of the baseline yields a mean Δ(D−A) of only
+0.0022 macro-F1 across seven representative seasonal panels under
Stratified 5-fold CV, and the improvement is statistically significant
(p < 0.05) in only one panel (`sy2022_sm03_w3m_off1`, p = 0.026). The
hybrid representation thus delivers a **conditional contribution** that
survives mainly in panels with strongly imbalanced labels.

The thesis contributes in two ways. First, the seasonal rolling-window
design quantitatively exposes the fragility of late-window outcome
definitions in transaction-based store-lifecycle research and shows, across
80 specifications, that prior accuracy claims may be inflated by label
timing. Second, the documented dependence of hybrid-representation gains on
label / season distribution implies that, on the same data and the same
model, label-definition choices can flip the substantive conclusion. LEVI,
EWS, and external public-data validation are deferred to future work and
application contexts rather than treated as main contributions of this
thesis.

Keywords: small business, card-transaction data, lifecycle prediction, early
classification, seasonality control, rolling-window validation, food service.
