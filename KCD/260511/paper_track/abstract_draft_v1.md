# HICSS 2027 Abstract Draft v1 (350 words)

본 파일은 HICSS abstract 초안. 단어 수 350 이내 (HICSS 표준). 지도교수와 다듬을 것.

---

## Title

**Why Stock-Style Forecasting Fails for Small-Business Lifecycle Analytics: A 14-Model Benchmark with Calendar-Aligned Evaluation**

## Abstract (draft, ~340 words)

Predicting which small businesses (SMBs) will grow, stay stable, or decline over
short horizons is a core problem for local economic policy and lending decisions.
Despite a flourishing literature on stock-price forecasting with deep learning
(LSTM, Transformer, foundation models such as TimesFM, Chronos, and Moirai),
the direct transfer of these techniques to SMB sales dynamics has not been
quantitatively examined. This paper provides the first systematic benchmark of
14 external models—3 time-series foundation models, 7 stock-prediction state-of-
the-art models (TFT, N-BEATS, N-HiTS, PatchTST, DLinear, Informer, Autoformer),
3 SMB-specific attention variants (Feature-Attention MLP, Time-Attention LSTM,
FiLM-tenure LSTM), and 1 cost-sensitive variant—against a Random Forest tabular
baseline on 6 calendar-aligned panels of weekly Korean SMB card-transaction data
(59,089 stores, 2021–2023, 3-fold stratified cross-validation).

We find that all 14 external models lose to Random Forest by macro-F1 −0.035 to
−0.270 (6/6 panels, p<0.001 in most cases). DLinear is the strongest stock SOTA
(F1=0.361, Δ=−0.139), while zero-shot foundation models drop near random
(F1=0.23–0.31). Only LightGBM tabular—reproducing the M5 competition winning
pattern—surpasses RF baseline (+0.008 macro-F1, 5/6 panels). Tenure meta
features add another +0.008.

We propose four mechanism hypotheses for the failure of stock-style transfer:
(1) short-window data (13–31 weeks) outside foundation models' pretraining
regime; (2) information loss in the regression-to-classification conversion;
(3) tabular statistical features outperforming raw multivariate sequence
representation in 6-channel SMB data; and (4) calendar-season confound that
SMB-specific calendar-aligned panel design eliminates.

Our results suggest a clear design template for SMB lifecycle decision-support
systems: start with GBDT baselines and tenure-cohort features rather than deep
sequence models, and prioritize feature engineering over architecture novelty.
We accompany the benchmark with a 70-paper literature survey mapping the
methodological gap between stock-forecasting and SMB-lifecycle prediction.

## Keywords (5)

small business, lifecycle prediction, time-series classification, foundation
models, benchmark study

---

## 작성 메모

- 350 words 안에 5가지 핵심 정량 수치 포함: macro-F1 0.500, Δ −0.139, Δ +0.008, 14 models, 70 papers.
- 4 mechanism hypotheses 명시 — paper 본문 §5 (Discussion) 의 핵심 contribution.
- 마지막 단락의 "design template for SMB lifecycle decision-support" 가 HICSS Decision Analytics track 키워드.
- "first systematic benchmark" 표현 — novelty claim. lit review 70편이 이를 뒷받침.

## 다음 작업 (지도교수와)

- [ ] 350 단어 정확히 맞추기 (현재 ~340)
- [ ] title 단어 선택 ("Stock-Style" vs "Stock-Prediction" vs "Financial-Forecasting")
- [ ] keywords 마지막 1개 후보: "early warning" / "small-medium enterprise" / "Korea"
- [ ] decision-support 와 service-analytics 중 어느 framing 강조할지 결정 (track 의존)
