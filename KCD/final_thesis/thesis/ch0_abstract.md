# 초록

> KAIST 학위논문 작성 및 제출요령 (2026, 14 쪽) 규정.
> 한글 초록 빈칸 제외 500자 이내, 영문 초록 빈칸 제외 300단어 이내.
> 핵심 낱말은 한글·영문 각각 5 ~ 10 개.

## 한글 초록

본 연구는 KCD 서울시 외식업 5.9만 점포 주간 카드거래 (2021–2023,
142주) 로 초기 1–7개월 거래가 이후 G/S/D 분류 예측에 주는 정보를
분석한다.

세 가지를 보고한다. 첫째, 145 specification baseline macro-F1
0.43–0.55 위에서 업력 4분위 × G/S/D, 6 cluster × G/S/D, 신규고객
→Growth logit 회귀로 요인을 분해한다. 둘째, feature·target 윈도우를
같은 캘린더 월로 정렬한 rolling-window 에서 시작월 진폭 0.10 ≫
윈도우 길이 0.02–0.04 ≫ 시작연도 0.01 미만 — 라벨 시점이 결론을
좌우한다. 셋째, 개선 세 갈래 중 hybrid 는 14 panel 평균 ΔF1 +0.0017
(유의 1/14, Bonferroni 후 0/14), cost-sensitive 가중은 음(−), 외부
SOTA 14 종 중 LightGBM 만 RF 능가 (+0.0075). 향상은 Q4_long 과
fragile cluster 에 집중된다.

본 연구는 요인 분해, 시즌 정렬 label robustness, SMB ≠ stock
literature 정량 차별화를 제시한다.

핵심 낱말 : 소상공인, 카드거래, 생애주기 분류, 시즌 통제, 롤링
윈도우 검증, cohort 분석, cluster 요인, 외식업, KCD.

## English Abstract

This thesis uses a weekly card-transaction panel from Korea Credit
Data covering about 59,000 food-service stores in Seoul (Jan 2021 to
Aug 2023, 142 weeks) to study how early transaction patterns over the
first one to seven months inform the subsequent Growth, Stable, or
Decline lifecycle state of each store. The umbrella question is
prediction-first: how well can early transactions predict G / S / D,
and which factors, representations, and models improve that
prediction.

Three findings are reported. First, on a baseline macro-F1 of 0.43 to
0.55 across 145 specifications, the thesis decomposes lifecycle
outcomes by tenure quartile cohort, by KMeans cluster, and by a
cohort-stratified logit regression of new-customer slope on the Growth
outcome. Second, under a seasonal rolling-window design that aligns
feature and target windows to the same calendar months and length, the
start-month effect (amplitude about 0.10) dwarfs window length (0.02
to 0.04) and start year (below 0.01); label timing dominates accuracy.
Third, on three prediction-improvement axes the gains are limited and
selective. A hybrid representation that adds KMeans cluster labels
and a change-point feature yields a mean ΔF1 of only +0.0017 across 14
panels, with statistical significance in one panel pre-correction and
zero panels after Bonferroni. Cost-sensitive Decline weighting hurts
Random Forest by 0.035 to 0.063 and gives no gain on LightGBM. Of 14
external state-of-the-art models (two foundation zero-shot, seven
stock-prediction time-series SOTA, three SMB-specific attention, two
cost-sensitive variants), only LightGBM tabular surpasses Random
Forest (+0.0075, five of six panels win). Gains concentrate on Q4_long
tenure stores (ΔF1 +0.019) and on a fragile cluster (Decline rate 35
to 60 percent, ΔF1 +0.044).

The thesis contributes a prediction baseline with factor decomposition,
a seasonal-alignment label-robustness standard, and a quantified
SMB-versus-stock-prediction differentiation for transaction-based
store-lifecycle classification.

Keywords : small business, card-transaction data, lifecycle
classification, seasonal control, rolling-window validation, cohort
analysis, cluster factors, food service, KCD.
