# Key Results — One Pager (협업자/지도교수 공유용)

## 한 줄

**Korean SMB 단기 매출 G/S/D 분류**에서 stock-prediction SOTA 14종 (foundation
+ Transformer + attention) 이 RF baseline에 모두 패배. 단 1종 **LightGBM이
RF를 +0.008 macro_F1로 안정적으로 이김** (M5 우승자 패턴 transfer).

## 데이터

- 59,089 stores, 2021–2023, 6.5M weekly card transactions
- 6 channels: sales_card, customer, customer_new, before_noon, weekend, sales_delivery
- 14 panels (3-month × 7 + 7-month × 7), calendar-aligned

## 모델 14종 정량 비교 (6 panels avg)

```
Rank  Model              macro_F1   Δ vs RF
1     lgbm_tabular        0.505     +0.008  ★ (5/6 wins, 2 p<0.05)
2     lgbm_shap_weighted  0.504     +0.007
3     lgbm_decline_x2     0.500     +0.003
4     rf_tabular          0.500       —
5     feature_attn_mlp    0.462     −0.035
6     film_tenure_lstm    0.451     −0.047
7     time_attn_lstm      0.405     −0.092
8     dlinear (5B best)   0.361     −0.139
9     nhits               0.279     −0.221
10    tft                 0.262     −0.238
11    nbeats              0.254     −0.246
12    patchtst            0.242     −0.258
13    informer            0.240     −0.260
14    autoformer          0.239     −0.261
15    chronos_bolt zero   0.289     −0.211
16    timesfm_200m zero   0.230     −0.270
```

## Phase 5 외에 검증된 다른 contribution

```
Method                           Δ vs base   Source
Seasonal calendar alignment       main      v5 (변경 없음)
Meta features (+ tenure)         +0.008     Phase 2.2 (8 panels, 3/8 p<0.05)
Cluster heterogeneity            G/S/D 7-36% Phase 2.3 (per-cluster Decline rate)
Hybrid (cluster + CP) 14-panel   +0.0017    Phase 5.5 재집계 (1/14 p<0.05)
```

## 4 mechanism hypotheses (왜 stock SOTA가 안 통하는가)

1. **Short window** (13–31주) — foundation/Transformer SOTA의 sweet spot 밖
2. **Regression → classification 변환** — forecast → slope → bucket에서 정보 손실
3. **6-channel multivariate** — 56-피처 통계가 raw 시계열보다 강함
4. **Calendar season confound** — SMB-specific, stock에는 약함

## 본 thesis 의 차별화 5가지 (vs stock literature)

1. Seasonal calendar alignment (main contribution)
2. G/S/D 3-class 분류 vs regression
3. 업력 cohort × new-customer-slope (stock에 없는 개념)
4. 6채널 multivariate, very short window
5. Spatial spillover negative (stock의 inter-stock correlation과 대조)

## 추천 venue 우선순위

1. **HICSS 2027** (Decision Analytics track) — 마감 2026-06-15 abstract / 2026-08-17 paper
2. **DSS journal** (12–18개월) — EWS calibration 보강 후
3. **Information & Management** (24개월) — managerial digital trace framing

## 신규 결과 (2026-05-11 분석 1, 2)

### Per-cohort LightGBM Δ 분해 (확인됨)

가설 H1 (Q4_long tenure cohort에서 더 큰 Δ) **CONFIRMED**:

```
Tenure quartile     mean Δ    n_panels
Q1_short (~7mo)     +0.002    6
Q2 (~22mo)          −0.002    6
Q3 (~47mo)          +0.013    6
Q4_long (≥9yr)      +0.019    6 ★ (2.4× overall avg)

Cluster decomposition:
cluster_3 (fragile, Decline 17%)  +0.044  (5.5× overall avg)
cluster_1 (n=5094)                +0.041
cluster_5 (n=5226)                +0.036
cluster_2                         +0.021
cluster_0 (n=9566)                +0.011
cluster_4                         +0.004
```

→ 평균 +0.008은 **sub-population에서 5× 더 큰 효과를 가린다**. 미팅 피드백
"업력이 상승에 유의미" 가 모델 향상에도 그대로 적용됨. paper 본문 핵심 결과.

### EWS calibration + decile table (확인됨)

```
                  mean Brier (6 panels)  panels LGBM better
RF                0.109                  —
LGBM              0.097                  4/6  (−0.012, ~11% improvement)

10-decile observed Decline rate (6-panel avg, LGBM):
Decile 0 (lowest):  2.0%
Decile 1:           3.6%
Decile 5:          10.9%
Decile 8:          20.8%
Decile 9 (highest): 34.8%  ★ (vs baseline 13% = 2.7× lift / 17× spread)
```

LGBM 이 RF 보다 calibration 더 정확 (특히 low-risk deciles 에서 over-prediction
감소). top decile 34.8% observed Decline = 정책 targeting 의 정량 자료.

→ paper_track DSS extension 핵심 자료 확보. HICSS paper 의 §4.6/§5.2 직접 사용 가능.

## 다음 action

1. ✅ per-cohort LightGBM Δ 분해 — Q4_long +0.019, fragile cluster +0.044
2. ✅ EWS calibration + decile table — LGBM Brier 0.097, top decile 34.8%
3. ⏳ HICSS abstract 350-word draft → 지도교수 review
4. ⏳ Cost-sensitivity sweep (dollar value)
5. ⏳ Synthetic long-history ablation

## 코드 / 데이터

- GitHub: https://github.com/HyeokyYun/masters/tree/main/KCD/260511
- env: `260511/phase5_external/envs/phase5_sm61.yml` (torch 2.3.1+cu118)
- 재현: `260511/phase5_external/README.md` 의 재실행 섹션

## 의문점 / decision pending

- [ ] HICSS abstract title 단어 — "Stock-Style Forecasting" vs "Stock-Prediction SOTA" vs "Financial Time-Series Methods"
- [ ] Target track — Decision Analytics vs Service Analytics vs Knowledge/Entrepreneurial Systems
- [ ] Co-author 추가 여부 (Phase 5 design / M5 expert)
- [ ] DSS field validation partner — 서울신용보증재단 / KCD / academic-only
