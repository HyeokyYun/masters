# 초록

## 국문 초록

소상공인 점포의 성장과 쇠퇴를 조기에 식별하는 작업은 지역경제 모니터링과
자영업 정책의 기초이지만, 행정통계는 폐업 신고 시점에야 점포의 종료를
포착한다는 한계가 있다. 본 연구는 한국신용데이터(KCD) 가 보유한 서울시
외식업 점포의 주간 카드거래 패널(2021-01-01 ~ 2023-08-28, 142 주, 약 5만 9천
점포)을 사용해, 영업 초기 1–7 개월의 거래 패턴이 이후 점포의 생애주기 상태
(Growth / Stable / Decline) 분류에 어느 정도의 정보를 제공하는지 분석한다.

본 연구의 방법론적 핵심은 시즌 통제이다. 기존 거래 데이터 기반 점포 분류
연구는 "마지막 30 주" 또는 전체 기간 기울기로 라벨을 정의해, 데이터
컷오프(2023-08-28) 직전의 휴가 시즌 6–8 월 매출이 항상 라벨 구간에 들어가는
시즌 confound 에 노출된다. 본 연구는 feature window 와 target window 를 같은
캘린더 월·같은 길이로 정렬한 rolling-window 설계를 도입하고, 시작연도(2021,
2022) × 시작월(1–12) × 윈도우 길이(1, 2, 3, 4, 6, 7 개월) × target offset
(1 년 또는 2 년 후) 으로 정의되는 specification 을 데이터 범위 안에서 모두
평가한다. 모델은 baseline 매출/고객 통계 피처 위에 KMeans 클러스터(B)와
change-point 피처(C)를 단계적으로 추가하는 A → B → C → D 비교(stratified
5-fold CV, paired t-test)를 사용한다.

분석 결과는 다섯 가지로 정리된다. 첫째, 시즌 정렬 라벨에서 macro-F1 은
시작월에 따라 0.43 ~ 0.54 사이에서 약 0.10 의 진폭으로 흔들리며, 윈도우 길이
효과(약 0.02)나 시작연도 효과(0.01 미만)보다 훨씬 크다. 시즌 confound 가
라벨/모델 정확도 양쪽에서 결정적이다. 둘째, baseline + cluster + change-point
의 hybrid representation D 모델은 14 개 대표 panel 평균 +0.0017 macro-F1
향상에 그치며, 5% 유의는 1/14 panel 에서만 잡힌다. 윈도우 7 개월에서 가장
안정적(+0.0030)이지만 4 / 6 개월에서는 효과가 사실상 사라진다 — hybrid
representation 의 contribution 은 라벨/시즌/윈도우 분포에 의존하는
**조건부 contribution** 으로 관찰된다. 셋째, 코로나 시기(2021 시작 panel)와
회복기(2022 시작 panel) 의 정확도 차이는 평균 0.01 미만으로, 코로나 잔여
영향이 본 분석의 결과를 좌우하지 않는다. 넷째, 동일 56 baseline 통계 피처
위의 **LightGBM tabular 가 RF 를 6 panel 중 5 개에서 일관되게 능가** 한다
(Δ = +0.0075 macro-F1, 2 panels p<0.05; per-cohort 분해 시 Q4_long 업력
cohort +0.019, fragile cluster +0.044). 이는 M5 Walmart 우승자 패턴이 SMB
단기 G/S/D 분류에 transfer 됨을 의미한다. 다섯째, **stock-prediction
literature 의 SOTA 14 종 benchmark** (TimesFM/Chronos/Moirai zero-shot,
TFT/N-BEATS/N-HiTS/PatchTST/DLinear/Informer/Autoformer, SMB-specific
attention 3 종) 에서 LightGBM 1 종을 제외한 모두가 RF 에 패배 (Δ = −0.035
~ −0.270, 6/6 panels p<0.001). 본 결과는 SMB 단기 G/S/D 분류가
stock-prediction literature 와 차별화되는 별도 영역임을 정량 입증한다.

본 연구의 기여는 세 가지다. (a) **시즌 정렬 rolling-window 검증 방법론** —
기존 late-window outcome 정의의 취약성을 80 specification 이상 수준에서
정량 폭로하며, 거래 기반 점포 라이프사이클 분류 연구가 도입해야 할
robustness 표준을 제시한다. (b) **hybrid representation 의 조건부
contribution 발견** — 14-panel 재집계 평균 +0.0017 macro-F1 로 동일 데이터·
동일 모델에서도 라벨 정의가 학술적 결론을 뒤집을 수 있다는 실증 증거이며,
해당 분야의 reproducibility 한계에 구체적 자료를 제공한다. (c) **stock-
prediction SOTA 14 종에 대한 SMB-specific 차별화** — SMB 단기 G/S/D
분류가 4 가지 mechanism (short window, regression-to-classification 변환
손실, multivariate channel compression, calendar season confound) 으로
stock literature 와 차별화되는 별도 영역임을 14 모델 벤치마크로 입증하며,
본 연구 main contribution 의 정당화 근거를 제공한다. LEVI 도시경제 활력
지수, EWS 조기 쇠퇴 경보, 외부 공공 데이터와의 외적 타당도 검증은 미팅
결정에 따라 본문 contribution 이 아니라 future work 로 분리한다.

**주요어**: 소상공인, 카드거래 데이터, 생애주기 예측, 조기 분류, 계절성
통제, 롤링 윈도우 검증, 외식업, KCD.

## English Abstract

Identifying the growth and decline of small-business stores at an early
stage is foundational to local economic monitoring and self-employed support
policy, but conventional administrative statistics only register exits at
the time of the closure filing. This thesis uses a weekly card-transaction
panel from Korea Credit Data (KCD) covering food-service stores in Seoul
(2021-01-01 – 2023-08-28, 142 weeks, approximately 59,000 stores) to ask
how much early transaction patterns inform the subsequent lifecycle state
(Growth, Stable, or Decline) of each store.

The methodological focus is seasonal control. Prior transaction-based
store-classification work labels outcomes from a fixed "last 30 weeks" or
whole-period slope, which in this dataset always falls into the
holiday-season weeks of June–August 2023 just before the data cutoff and
confounds seasonal demand with lifecycle dynamics. We introduce a
rolling-window design that aligns the feature and target windows to the
same calendar months and the same length, and exhaustively evaluate
specifications defined by start year (2021, 2022) × start month (1–12) ×
window length (1, 2, 3, 4, 6, 7 months) × target offset (one or two years
ahead). The model comparison stacks KMeans cluster labels (B) and a
change-point feature (C) on top of a baseline of sales/customer statistics
(A), with A → B → C → D evaluated under stratified 5-fold CV and a paired
t-test for A vs. D.

Five findings emerge. (1) Under seasonal alignment, macro-F1 ranges from
0.43 to 0.54 across start months — an amplitude of 0.10 that dwarfs the
effect of window length (~0.02) or start year (<0.01). Seasonality is the
dominant source of variation in labeling and accuracy. (2) The hybrid
representation D yields a mean Δ(D−A) of only +0.0017 macro-F1 across 14
representative seasonal panels (7-month windows most stable at +0.0030;
4-/6-month effects vanish), with statistical significance (p < 0.05) in
only 1/14 panels. The hybrid representation thus delivers a **conditional
contribution** dependent on label/season/window distribution. (3)
Pre-recovery (2021 start) and recovery (2022 start) panels differ by less
than 0.01 macro-F1 on average; the residual COVID effect does not drive
the main results. (4) On the same 56 baseline statistical features,
**LightGBM tabular consistently surpasses RF** across 5/6 panels
(Δ = +0.0075 macro-F1, 2 panels p<0.05; per-cohort decomposition shows
Q4_long tenure cohort Δ = +0.019 and fragile cluster Δ = +0.044 — 2.4× and
5.5× the overall average). This transfers the M5 Walmart competition winner
pattern (LightGBM ensemble dominance) to SMB short-window classification.
(5) A direct benchmark of 14 external stock-prediction state-of-the-art
models (TimesFM/Chronos/Moirai foundation zero-shot, TFT/N-BEATS/N-HiTS/
PatchTST/DLinear/Informer/Autoformer, 3 SMB-specific attention variants)
finds **all but one (LightGBM) lose to RF baseline** (Δ = −0.035 to −0.270,
6/6 panels p<0.001 for most). This quantitatively establishes SMB
short-window G/S/D classification as a distinct regime from
stock-prediction.

The thesis contributes in three ways. First, the **seasonal rolling-window
robustness methodology** quantitatively exposes the fragility of
late-window outcome definitions in transaction-based store-lifecycle
research and proposes a robustness standard that future work in this area
should adopt. Second, the **conditional contribution of hybrid
representation** (mean Δ = +0.0017 across 14 panels) shows that, on the
same data and the same model, the choice of label definition can flip the
substantive conclusion — providing concrete empirical material for the
reproducibility limits of this literature. Third, the **14-model
stock-prediction-SOTA benchmark and four mechanism hypotheses** (short
window, regression-to-classification conversion loss, multivariate channel
compression, and calendar-season confound) establish SMB short-window
classification as a distinct regime requiring SMB-specific methodology,
justifying the first contribution. LEVI (local economic vitality index), an
EWS (early warning system), and external public-data validation are
deferred to future work per the advisor decision rather than treated as
main contributions of this thesis.

**Keywords**: small business, card-transaction data, lifecycle prediction,
early classification, seasonality control, rolling-window validation,
food service, KCD.
