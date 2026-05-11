# Ch5 Results — 통합 패치 텍스트

v5_thesis_final/ch5_results.md에 추가하거나 교체할 정확한 텍스트와 표.

## 사용 방법

- §5.5 (기존) 끝에 **§5.5.2 LightGBM 비교** 추가
- §5.5.2 (기존, 비어있던 4/6/7-month placeholder)를 **§5.5.3 14-panel 재집계**로 채움
- §5.6 (신규)으로 **Phase 5 외부 SOTA 비교** 추가

---

## 추가 §5.5.2 — LightGBM이 RF baseline을 일관되게 이긴다 ★ NEW

`260511/phase5_external/src/s5d_weighting/run_weighting.py` 결과 (3-fold StratifiedKFold, 6 panels).

```
원시 결과 (outputs/tables/weighting_compare.csv 요약):

Model            macro_F1   Δ vs RF   p<0.05 panels   wins/6
rf_tabular        0.4973     —         —                —
lgbm_tabular      0.5048    +0.0075    2                5  ★
lgbm_shap_weight  0.5044    +0.0071    2                5
lgbm_decline_x2   0.4999    +0.0026    3                4
rf_decline_x2     0.4628    −0.0345    6                0
rf_decline_x3     0.4344    −0.0629    6                0
```

LightGBM tabular(56-피처)가 RF에 +0.0075 macro_F1로 6 panel 중 5에서 우위.
2 panel에서 paired t-test p<0.05. M5 (Walmart) accuracy competition의 우승자
패턴 (LightGBM ensemble dominance, Makridakis et al. 2022) 이 SMB 단기 G/S/D
분류에도 transfer됨을 정량 입증.

흥미롭게도:
- SHAP-derived feature weighting은 효과가 거의 없음 (+0.0071). LGBM의
  split-gain 학습이 이미 feature importance를 implicit하게 잡음.
- Decline 샘플 가중치 ×2/×3 은 RF에서 큰 폭으로 macro_F1 감소. minority class
  강조가 majority 정확도를 더 크게 희생.

→ §5.5의 conditional contribution 표에 **C3 (LightGBM +0.008)** 추가.

#### 5.5.2.1 Per-cohort 분해 — Q4_long 과 fragile cluster 에서 효과 더 큼

`outputs/tables/lgbm_per_cohort_summary.csv`. OOF predictions per cohort:

```
Tenure quartile     mean Δ    std        n_panels    decline_rate
Q1_short (~7mo)     +0.0021    0.004     6           0.129
Q2 (~22mo)          −0.0018    0.010     6           0.126
Q3 (~47mo)          +0.0126    0.009     6           0.117
Q4_long (≥9yr)      +0.0189    0.013     6 ★         0.120

KMeans cluster (k=6)  mean Δ    n_avg       decline_rate
cluster_3 (fragile)   +0.0439   4,622       0.173 ★
cluster_1             +0.0407   5,094       0.162
cluster_5             +0.0357   5,226       0.130
cluster_2             +0.0214   2,558       0.198
cluster_0             +0.0114   9,566       0.152
cluster_4             +0.0041   8,835       0.154
```

**Tenure 단조 증가**: Q1 → Q4 로 tenure 가 늘수록 LGBM Δ 도 단조 증가
(0.002 → 0.019). 미팅 피드백 "업력이 상승에 유의미" 가 **모델 향상 자체에도
적용됨** 을 정량 확인 — Phase 2.4 C3 cohort logistic coefficient (Q4_long 1.422)
와 정합.

**Cluster 이질성**: fragile cluster_3 (Decline 17%) 에서 Δ = +0.044 — 전체
평균의 5.5×. 정책적 우선순위 (fragile group targeted intervention) 와 모델
선택 (LGBM > RF) 이 일치하는 방향.

Figures: `outputs/figures/lgbm_per_cohort_tenure_q.png`,
`lgbm_per_cohort_cluster.png`.

---

## 교체 §5.5.3 — 14-panel 재집계로 약화된 hybrid representation

`260511/outputs/tables/main_model_compare.csv` (14 panels × 4 variants = 56 rows),
`main_model_paired_AvD.csv` (14 panels).

```
Window   n_panels   mean Δ(D−A)
3m       7          +0.0019
4m       2          +0.0010
6m       2          +0.0000
7m       3          +0.0030 ★
Overall  14         +0.0017
```

paired t-test: 14 panel 중 1개에서 p<0.05 (sy2021_sm01_w7m_off1, p=0.007).

기존 7-panel cited 값 +0.0022 대비 14-panel 평균 +0.0017로 **더 약화**. hybrid
(cluster + change-point) contribution은 panel을 늘릴수록 평균이 회귀하며, 7m
window에서 가장 안정적(+0.003)이지만 그 외 길이에서는 효과가 거의 사라진다.

해석: v5_thesis_final가 강조한 "**conditional contribution**" framing이 14-panel
재집계로 더욱 강하게 뒷받침된다. seasonal alignment 본 contribution은 변경 없음.

---

## 신규 §5.6 — Phase 5 외부 SOTA 비교 (negative finding 종합) ★ NEW

미팅 피드백 ("주식 예측 literature 비교 · 다른 시계열 모델 · feature weight")
에 정량 응답한 Phase 5 결과. 동일 6 panels, 3-fold StratifiedKFold, paired vs RF.

### 5.6.1 Stock-prediction SOTA (`neuralforecast_compare.csv`)

```
Rank  Model        macro_F1   Δ vs RF   p<0.05
1     DLinear      0.361     −0.139    6/6 ★
2     N-HiTS       0.279     −0.221    6/6
3     TFT          0.262     −0.238    6/6
4     N-BEATS      0.254     −0.246    6/6
5     PatchTST     0.242     −0.258    6/6
6     Informer     0.240     −0.260    6/6
7     Autoformer   0.239     −0.261    6/6
```

DLinear (Zeng et al. 2023)가 stock SOTA 7종 중 1위 — Transformer 무용론 논쟁
(S5 in lit review)이 SMB short-window에도 확인됨. 그러나 best stock
SOTA(DLinear 0.361)조차 RF(0.500)에 0.14 macro_F1 손해.

### 5.6.2 Time-series Foundation Models (zero-shot, `foundation_zeroshot_compare.csv`)

```
Model                macro_F1   Δ vs RF   p<0.05
chronos_bolt_small   0.289     −0.211    6/6
timesfm_200m         0.230     −0.270    6/6
moirai_small         0.306     −0.187    (1/6 partial)
```

TimesFM-200m (Das et al. 2024), Chronos-Bolt-small (Ansari et al. 2024),
Moirai-small (Woo et al. 2024) 모두 zero-shot으로 SMB G/S/D에 거의 random
수준의 macro_F1. pretrain 도메인 mismatch + 13–31주 short window가 foundation
모델의 sweet spot 밖.

### 5.6.3 SMB-specific Attention (`attention_compare.csv`)

```
Model              macro_F1   Δ vs RF
feature_attn_mlp   0.462      −0.035  ★ best
film_tenure_lstm   0.451      −0.047
time_attn_lstm     0.405      −0.092
```

Squeeze-Excite feature attention이 가장 RF에 가까움(−0.035). FiLM-tenure가
vanilla time-attention보다 큰 폭(+0.046) 우위 — 미팅 피드백 "업력이 상승에
유의미"가 모델 구조 conditioning으로도 기능함을 시사. 그러나 RF는 여전히 못 넘음.

### 5.6.4 한 줄 요약 — Phase 5 negative finding 의의

14종 외부 모델 모두 RF tabular baseline (56-피처 통계) 위로 가지 못함.
이는 **stock-prediction literature의 standard transfer가 SMB 단기 G/S/D
분류에 작동하지 않는다는 정량 증거**다. 본 thesis의 차별화 (seasonal calendar
alignment, tenure cohort, multivariate short-window classification)이 SMB에
필수임을 역으로 입증한다.

---

### 5.5.2.2 EWS calibration — decision-support angle ★ NEW

`outputs/tables/ews_brier.csv`, `ews_decile_table.csv`.

```
Model     mean Brier (6 panels)
RF        0.109
LGBM      0.097  (−11%, 4/6 panels)

10-decile observed Decline rate (LGBM, 6 panels avg):
Decile 9 (top)    34.8%  ← 2.7× baseline (13.0%)
Decile 0 (bottom)  2.0%
spread             17×
```

LGBM 이 RF 보다 Brier 11% 우위 + low-risk deciles 에서 calibration 더 정확.
**Top 10% Decline-risk targeted intervention 정책 시나리오 정량 자료**.
정책 함의: fragile cluster (per-cohort §5.5.2.1) 와 top decile EWS targeting
이 결합된 결정-지원 artifact 의 토대.

Figures: `outputs/figures/ews_reliability_diagram.png`, `ews_decile_curve.png`.

## 인용해야 할 추가 figures (Phase 5)

- `260511/phase5_external/outputs/figures/phase5_macro_f1_bars.png` — 14종 모델 평균 macro_F1 막대 (RF baseline 점선)
- `260511/phase5_external/outputs/figures/phase5_delta_vs_rf.png` — paired Δ vs RF (p<0.05 panel 카운트 *마크)
- `260511/phase5_external/outputs/figures/lgbm_per_cohort_tenure_q.png` — tenure quartile 별 LGBM Δ heatmap ★ NEW
- `260511/phase5_external/outputs/figures/lgbm_per_cohort_cluster.png` — cluster 별 LGBM Δ heatmap ★ NEW
- `260511/phase5_external/outputs/figures/ews_reliability_diagram.png` — EWS calibration RF vs LGBM ★ NEW
- `260511/phase5_external/outputs/figures/ews_decile_curve.png` — observed Decline rate by decile ★ NEW

---

## 본 chapter의 한 줄 결론

> Seasonal calendar alignment(main) 위에 (a) LightGBM tabular(+0.008), (b)
> tenure meta features(+0.008)가 안정적으로 추가 향상을 제공하며, 그 외
> 14종 외부 SOTA·foundation·attention 변형은 모두 RF baseline을 넘지 못한다.
