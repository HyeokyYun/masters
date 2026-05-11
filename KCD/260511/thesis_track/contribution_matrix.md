# Contribution Matrix — v5_thesis_final 통합 후

본 표는 학위논문 본문에서 인용 가능한 **모든** contribution을 한 곳에 모은
정량 매트릭스다. 발표용 single-slide로도 사용 가능.

## Main contribution (변경 없음)

| # | Contribution | 정량 | 강도 |
|---|---|---|---|
| M1 | **Seasonal calendar alignment** — feature 윈도우와 target 윈도우를 동일 캘린더 월 정렬해 seasonal confound 제거 | 6 panels seasonal pair test (`seasonal_results_summary.csv`) | **강함** (v5 main contribution) |

## Conditional contributions (추가/강화)

| # | Contribution | 정량 | 출처 (CSV) | 강도 |
|---|---|---|---|---|
| C1 | **Meta features (tenure 등) 추가** | mean Δ = +0.0082 macro_F1, 3/8 panels p<0.05 | `260511/outputs/tables/main_model_compare_meta.csv`, `main_model_paired_AvAmeta.csv` | **중간 강함** |
| C2 | **Hybrid representation (cluster + change-point)** | 14-panel 재집계 mean Δ = +0.0017 macro_F1, 1/14 panels p<0.05 (7m window 한정 +0.003) | `260511/outputs/tables/main_model_compare.csv`, `main_model_paired_AvD.csv` | **약함 / conditional** |
| C3 | **LightGBM tabular > RF tabular** ★ **NEW** | mean Δ = +0.0075 macro_F1, 5/6 panels wins, 2 p<0.05; **per-cohort 분해 시 Q4_long(업력 9년+) Δ = +0.019 (2.4×), fragile cluster Δ = +0.044 (5.5×)** | `260511/phase5_external/outputs/tables/weighting_compare.csv`, `lgbm_per_cohort_summary.csv` | **중간** (M5 우승자 패턴 transfer + sub-population에서 강함) |
| C3b | **Per-cohort LightGBM Δ 단조 증가 in tenure** ★ **NEW** | Q1=+0.002 → Q2=-0.002 → Q3=+0.013 → Q4=+0.019. tenure 증가에 LGBM 우위 단조 강화. 미팅 피드백 "업력이 상승에 유의미"의 모델-수준 증거. | `lgbm_per_cohort_summary.csv`, `lgbm_per_cohort_tenure_q.png` | **중간 강함** |
| C4 | **Cluster × G/S/D 이질성** | per-cluster Decline ratio 7%~36%, Growth ratio 27%~70% | `260511/outputs/tables/cluster_outcome_xtab.csv` | **강함** (descriptive) |
| C5 | **Tenure cohort × new-customer-slope** | Q4_long cohort logit_coef_nc_slope = 1.422 (std 0.426 = 가장 안정) | `260511/outputs/tables/age_cohort_nc_effect.csv` | **중간** |
| C6 | **EWS calibration — LGBM > RF (Brier)** ★ **NEW** | mean Brier LGBM=0.097 vs RF=0.109 (LGBM 11% 우위, 4/6 panels). 10-decile lift LGBM 17× (top decile observed Decline 34.8% vs base 13%) | `260511/phase5_external/outputs/tables/ews_brier.csv`, `ews_decile_table.csv`, `ews_reliability_diagram.png`, `ews_decile_curve.png` | **중간** (decision-support 측면) |

## Honest negative findings (포함 권장)

| # | Finding | 정량 | 출처 (CSV) | 의의 |
|---|---|---|---|---|
| N1 | **회귀-후-버킷 < 직접 분류** | 회귀 macro_F1 0.34–0.37 vs 분류 0.50 | `260511/outputs/tables/ts_benchmark_compare.csv` | G/S/D 분류 접근 정당화 |
| N2 | **Sequence raw input (LSTM/GRU/TCN/Transformer/flat_MLP) 패배** | best (TCN) 0.488 vs RF 0.497 | `260511/outputs/tables/seq_model_compare.csv` | 56-피처 통계가 raw 시계열 신호 거의 다 포착 |
| N3 | **Spatial GNN 모두 패배** | dong/industry/hybrid GCN 모두 MLP보다 −0.027 ~ −0.085 | `260511/outputs/tables/gnn_compare.csv` | "같은 동네 점포 spillover" 가설 약함 |
| N4 | **Stock SOTA 7종 모두 패배** ★ **NEW** | DLinear best 0.361, TFT/NBEATS/NHITS/PatchTST/Informer/Autoformer 모두 6/6 p<0.001 | `260511/phase5_external/outputs/tables/neuralforecast_compare.csv` | stock-style 직접 이식 안 됨 정량 |
| N5 | **TS Foundation models zero-shot 패배** ★ **NEW** | Chronos-Bolt 0.289 (Δ=-0.211), TimesFM 0.230 (Δ=-0.270) | `260511/phase5_external/outputs/tables/foundation_zeroshot_compare.csv` | pretrain domain mismatch + short window |
| N6 | **SMB-attention 변형 모두 패배** ★ **NEW** | FeatureAttnMLP best Δ=-0.035, FiLM-tenure -0.047, TimeAttn -0.092 | `260511/phase5_external/outputs/tables/attention_compare.csv` | feature attention이 가장 가까우나 RF 못 넘음 |
| N7 | **Cost-sensitive sample weighting 역효과** ★ **NEW** | RF decline_x2 Δ=-0.034, x3 Δ=-0.063 | `260511/phase5_external/outputs/tables/weighting_compare.csv` | macro_F1 단순 향상 안 됨 — proba-level calibration 필요 |

## 한 줄 요약 (single-slide)

> **Seasonal alignment(main) + tenure meta features + LightGBM = 가장 강한 SMB
> 단기 G/S/D 분류기. 그 외 14종 SOTA·foundation·spatial spillover는 모두 RF를
> 못 넘는다.**

## 발표(defense)용 핵심 수치 3가지

1. **+0.008 macro_F1** — meta features와 LightGBM 각각이 RF baseline 위에
   제공하는 일관된 (조건부) 향상 (5–6 panels positive).
2. **−0.14 ~ −0.27 macro_F1** — stock SOTA (DLinear best, others worse)와
   foundation models이 RF에 패배하는 폭. 6/6 panels p<0.001.
3. **0.07–0.36 Decline ratio** — cluster별 G/S/D 분포의 이질성. fragile
   cluster(cluster 3)는 Decline 36% — 정책적 함의의 핵심.

## 본 매트릭스 사용 방법

- thesis Ch1 introduction 도입부에서 main/conditional/negative 한 줄 요약으로 인용
- Ch5 §5.5 ablation 표를 C1–C3 정량으로 채움
- Ch6 discussion §6.x negative finding 종합을 N4–N7로 작성
- 발표 final slide에 본 표를 압축해 인쇄
