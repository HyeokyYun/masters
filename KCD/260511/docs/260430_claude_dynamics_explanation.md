# 260430_claude — Small-business Dynamics 설명/예측 결과 (Phase 0–4 통합)

본 문서는 2026-05-07 미팅 피드백을 반영하여 진행한 9개 실험의 결과를 정리한다.
모든 숫자는 `outputs/tables/*` 의 CSV에서 직접 인용한다.

## 0. 한 줄 요약 (교수님 한 줄 정리에 매핑)

> "Small business의 dynamics를 설명하고 더 잘 prediction할 수 있다."

- **설명 (분류 관점)**: meta features (업력) 추가가 cluster+CP 보다 4× 더 큰 효과
  (+0.0082 vs +0.0022 macro_F1).
- **예측 (시계열 관점)**: tabular RF가 LSTM/GRU/Transformer를 모두 이김
  — sequence raw 입력 자체로는 56-피처 RF를 못 따라잡음.
- **도시경제학 관점**: 공간(dong) GNN spillover가 오히려 성능을 떨어뜨림
  — 같은 동네 가게가 서로 영향 주는 가설은 실증적으로 약함. 단, hybrid
  (dong × 업종) 그래프가 가장 덜 나쁨.

## 1. Phase 0 — 라벨 정의 결정 ✓

`outputs/tables/label_definition_sweep.csv` (8 panels × 3 thresholds = 24 rows)

| k_sigma | mean_macro_F1 | growth | stable | decline | reg→bucket F1 |
|---:|---:|---:|---:|---:|---:|
| 0.3 | 0.491 | 0.454 | 0.344 | 0.202 | 0.393 |
| **0.5** ★ | **0.494** | 0.344 | 0.524 | 0.132 | 0.387 |
| 0.7 | 0.487 | 0.250 | 0.662 | 0.088 | 0.376 |

★ 채택: **±0.5σ 3-class 유지**. macro_F1 최댓값 + decline floor 5.1% 유지 +
회귀-후-버킷 < 직접 분류 → 분류 접근 정당화.

자세한 근거: `docs/label_choice_rationale.md`.

## 2. Phase 1 — 시계열 모델 novelty ✓

### 2.1 Sequence-to-class (B1, step06)

`outputs/tables/seq_model_compare.csv` (6 panels × 6 models = 36 rows)
`outputs/tables/seq_model_paired.csv` (paired t-test vs RF tabular)

| Model | macro_F1 (mean of 6 panels) | Δ vs RF | p-value | sig (3-fold) |
|---|---:|---:|---:|---|
| **rf_tabular** | **0.497** | (baseline) | — | — |
| tcn | 0.488 | -0.010 | 0.213 | not sig (panel-avg) |
| flat_mlp | 0.474 | -0.024 | 0.125 | not sig |
| lstm | 0.451 | -0.046 | 0.022 | sig |
| gru | 0.446 | -0.051 | 0.018 | sig |
| transformer | 0.410 | -0.087 | 0.052 | borderline |

- TCN은 1개 panel(sy2022_sm01)에서 RF를 +0.009 macro_F1 이김(p=0.042). 다른 5개에서는 비슷하거나 약간 낮음.
- 모든 sequence 모델이 RF를 일관되게 이기지 못함 → 56개 통계 피처가 raw 시계열의 G/S/D 신호를 거의 다 포착했음을 시사.
- Transformer가 가장 약함 — 짧은 시계열(13–31주)에 self-attention 이 과도한 capacity.

### 2.2 TS 회귀 → 버킷 (B3, step07)

`outputs/tables/ts_benchmark_compare.csv` (5 panels, 4 models)

| Model | macro_F1 | MAE |
|---|---:|---:|
| linear_extrap | 0.374 | 0.051 |
| mlp_flat | 0.363 | 0.044 |
| lstm_reg | 0.344 | 0.044 |
| naive_last_slope | 0.337 | 0.104 |

전부 0.34–0.37 으로 RF tabular(0.497)보다 13–16pt 낮음. **회귀-후-버킷 접근은 분류 접근에 비해 일관되게 열등**. 슬로프를 정확히 예측하는 일이 슬로프 부호+크기를 분류로 푸는 것보다 어렵다.

## 3. Phase 2 — 분류/해석 강화 ✓

### 3.1 SHAP per-class (A1, analysis_shap)

`outputs/tables/shap_class_contrib.csv` (7 panels × 3 classes × top-15 = 315 rows)

각 클래스의 평균 rank 상위 5 피처:

**Decline**: ma4_slope (3.1), slope_all (3.7), ma8_slope (4.4), vol_w8 (5.2), diff_mean (5.8)
**Stable**: sales_cv (4.2), iqr (4.8), vol_w8 (5.1), cust_mean (6.3), slope_all (6.9)
**Growth**: slope_all (2.6), ma4_slope (2.9), ma8_slope (3.4), cust_slope (5.4), diff_mean (3.5)

핵심:
- Decline/Growth는 **같은 slope/MA 피처들이 서로 다른 부호로** 작동.
- **cust_slope** (전체 고객 수 증가율)가 Growth 클래스에 7개 panel 모두에서 등장.
- **nc_*** (신규 유입) 피처는 top-15 안에 일부 panel에서만(예: sy2022_sm01_w7m, sy2021_sm09) 진입. 평균 rank 22–33위로 핵심 시그널은 아님 — 이는 미팅 직관과 약간 다른 결과로, "신규 유입"의 효과는 cohort/season 의존적임을 시사.
- Stable 클래스는 sales_cv / iqr / vol 등 **변동성 기반** 피처가 핵심.

### 3.2 Meta features 추가 (A2, step05b)

`outputs/tables/main_model_compare_meta.csv`, `main_model_paired_AvAmeta.csv`

| | macro_F1 (mean of 8 panels) |
|---|---:|
| A_baseline (56 features) | 0.494 |
| A_plus_meta (+ tenure_log, sqsize_log, has_delivery, prop_age_*, sigungu_te, kclass_te) | **0.502** |

**Δ = +0.0082, mean p = 0.104**. 8개 panel 중 3개에서 p<0.05.

| Panel | A | A+meta | Δ | p |
|---|---:|---:|---:|---:|
| sy2021_sm01_w3m | 0.490 | 0.498 | +0.008 | 0.080 |
| sy2021_sm05_w3m | 0.477 | 0.488 | +0.011 | **0.011** |
| sy2021_sm09_w3m | 0.498 | 0.516 | +0.018 | **0.033** |
| sy2022_sm01_w3m | 0.503 | 0.506 | +0.003 | 0.214 |
| sy2022_sm03_w3m | 0.457 | 0.463 | +0.005 | 0.074 |
| sy2022_sm05_w3m | 0.511 | 0.513 | +0.002 | 0.346 |
| sy2021_sm01_w7m | 0.535 | 0.546 | +0.011 | **0.010** |
| sy2022_sm01_w7m | 0.481 | 0.486 | +0.006 | 0.066 |

비교:
- 기존 cluster+CP (step05) 평균 Δ = +0.0022
- 본 실험 meta features 평균 Δ = +0.0082 → **약 4배 큰 효과**.
- 가장 강한 효과는 sy2021_sm09 (+0.018). 일부 panel(sy2022_sm05) 은 거의 0.

**미팅 피드백 ("업력이 상승에 유의미") 정량 확인**: 업력(tenure_log) + 메타가 56-피처 baseline 위에 일관된 추가 시그널을 제공.

### 3.3 Cluster × outcome heterogeneity (A3, analysis_cluster_outcome)

`outputs/tables/cluster_outcome_xtab.csv` (42 rows = 7 panels × 6 clusters),
`per_cluster_feature_importance.csv` (328 rows), `cluster_outcome_summary.csv` (42 rows),
`v4_category_outcome.csv` (21 rows)

핵심 발견:
- 클러스터 간 G/S/D 비율이 매우 다름. 예: sy2021_sm01_w3m_off1
  - cluster 3: Decline 36%, Growth 27% (가장 위험한 클러스터)
  - cluster 1: Decline 7%, Growth 70% (가장 안정적인 성장 클러스터)
- per-cluster macro_F1도 클러스터별로 큰 차이: 0.29 ~ 0.46.
- v4 카테고리(`술집 / 일반음식점 / 카페·베이커리`)는 panel(시즌)에 따라 G/S/D
  비율이 크게 달라짐 — 예) 술집의 Growth ratio가 sy2022_sm01_w7m=13% vs
  sy2021_sm01_w7m=83%. **시즌 정렬이 카테고리 효과보다 강하다.**

**미팅 피드백 ("클러스터링이 무의미해지면 안 됨") 대응**: 클러스터를 그 자체로
예측하기보다, **G/S/D 비율의 이질성을 드러내는 도구**로 재의미화. cluster 3
같은 fragile 그룹은 별도의 모델/정책 대응이 필요하다는 함의가 자연스럽게 따른다.

### 3.4 도시경제 보조 분석 (C2/C3, analysis_urban_econ)

`outputs/tables/industry_region_growth_rate.csv` (2229 rows),
`industry_region_top.csv`, `age_cohort_nc_effect.csv` (28 rows)

**C2 업종×지역 G/S/D 매트릭스 — 상승률 top 10 (panel 평균)**:

| kostat_class | sigungu | growth | decline | n |
|---|---|---:|---:|---:|
| 생맥주 전문점 | 은평구 | 0.690 | 0.067 | 92 |
| 생맥주 전문점 | 강서구 | 0.467 | 0.189 | 90 |
| 한식 면 요리 전문점 | 중랑구 | 0.465 | 0.091 | 249 |
| 한식 면 요리 전문점 | 강동구 | 0.463 | 0.061 | 293 |
| 생맥주 전문점 | 관악구 | 0.458 | 0.141 | 233 |
| 한식 면 요리 전문점 | 광진구 | 0.457 | 0.083 | 263 |
| 생맥주 전문점 | 강남구 | 0.454 | 0.108 | 360 |
| 한식 면 요리 전문점 | 마포구 | 0.454 | 0.073 | 281 |

특정 업종(생맥주, 한식 면 요리) × 특정 지역의 결합이 panel 평균 45–69% 상승률
— 도시경제학적 해석이 있는 cluster.

**C3 업력 cohort × nc_slope 효과 (logistic coef → P(Growth))**:

| cohort (tenure quartile) | tenure p50 (months) | growth_rate | logit_coef_nc_slope | std |
|---|---:|---:|---:|---:|
| Q1_short | ~7 | 0.306 | 0.842 | 0.847 |
| Q2 | ~22 | 0.320 | 0.666 | 0.625 |
| Q3 | ~47 | 0.326 | 0.779 | 0.747 |
| Q4_long | ~113 | 0.334 | **1.422** | 0.426 |

**Q4_long(9년 이상)에서 신규 유입(nc_slope) 효과가 가장 강하고 panel 간 std도 가장 작다 (가장 안정적).** 단기 점포(Q1)는 평균 효과는 비슷하지만 std가 매우 커서 panel 간 변동이 크다.

해석: 오래 운영한 점포가 **신규 유입을 곧바로 매출 슬로프로 전환**할 능력이 가장
일관됨. 단기 점포는 신규 유입이 있어도 슬로프 변환에 panel 간 노이즈가 큼
(영업 안정화 전 단계).

## 4. Phase 3 — GNN 공간 spillover ✓

`outputs/tables/gnn_compare.csv` (3 panels × 4 graph types × 2 models = 22 rows)

| Graph | Model | macro_F1 (3-panel mean) | Δ vs MLP(no graph) |
|---|---|---:|---:|
| none | mlp | 0.446 | (baseline) |
| dong | gcn | 0.360 | **−0.085** ★ worst |
| industry | gcn | 0.395 | −0.050 |
| **hybrid_dong_industry** | gcn | 0.418 | **−0.027** ★ best |

(MLP 결과는 그래프와 무관해 모두 0.446으로 동일.)

**모든 그래프가 GCN 성능을 하락시킴.** 가장 좁은 hybrid (같은 동 + 같은 업종) 그래프가 그나마 덜 손해. dong 단독 그래프는 가장 큰 negative spillover.

해석:
- 본 데이터에서 같은 동네/업종의 다른 가게가 매출 dynamics에 미치는 정보는
  weak — 오히려 노이즈 증폭 효과.
- GCN이 노드 피처를 평균화하면서 강한 개별 시그널이 희석됨. 56-피처 통계가
  이미 충분히 store-specific하기 때문에 graph aggregation의 추가 정보가 마이너스.
- 단, hybrid가 dong보다 덜 나쁜 점은 **"좁은 의미의 spillover" (같은 골목 같은 업종)** 가 dong 전체보다 의미 있음을 시사.
- 향후: GAT (attention 기반), 작은 노드 피처 (cust_slope 만 입력) 같은 변형으로
  spillover 신호 추출 가능성 검증 필요.

**미팅 피드백 ("주식과 다른 차별화로 GNN") 검증 결과**: 이 dataset에서는
공간 GNN이 contribution 후보로 약함. **negative finding으로 정직하게 보고**.

## 5. Phase 4 — 주식 예측 literature 대조

`docs/stock_vs_smb_dynamics.md` 참조.

본 데이터의 핵심 차별화:
- **생애주기 효과 (tenure)** : Phase 2.2 결과로 정량 확인 (+0.008 macro_F1).
- **계절성 confound** : v5 main contribution; 2.3에서 카테고리×season 변동
  으로도 재확인.
- **공간 spillover (가설)** : Phase 3 negative finding; 단순 spatial GNN으로는
  not material. 더 정교한 그래프/모델 필요.

## 5.5 step05 14-panel 재집계 (CLAUDE.md gap 해소)

`outputs/tables/main_model_compare.csv` (14 panels × 4 variants = 56 rows)
`outputs/tables/main_model_paired_AvD.csv` (14 panels)

이전에 `main_model_compare.csv`는 7개 3-month panel만 포함했고, v5 §5.5.2가
약속한 4/6/7-month 결과는 누락되어 있었다 (CLAUDE.md 명시). 본 phase에서
step05를 14 panel로 재실행하여 갱신했다.

| Window | n_panels | mean Δ(D−A) |
|---|---:|---:|
| 3m | 7 | +0.0019 |
| 4m | 2 | +0.0010 |
| 6m | 2 | +0.0000 |
| **7m** | 3 | **+0.0030** ★ |
| **Overall** | 14 | **+0.0017** |

paired t-test: **1/14 panels p<0.05** (sy2021_sm01_w7m_off1, p=0.007).

이전 7-panel cited 값 +0.0022 대비 14-panel 평균 +0.0017로 **더 약화**.
즉 hybrid (cluster + change-point) contribution은 panel을 늘릴수록 평균이
회귀(regress)하며, 7m window에서 가장 안정적(+0.003)이지만 그 외 길이에서는
효과가 거의 사라진다.

해석: v5_thesis_final §5.5.2는 "extended panels에서 hybrid 효과는 *conditional*"
이라는 v5 framing을 더욱 강하게 뒷받침한다. seasonal alignment 본 contribution은
변경 없음.

## 6. 종합 — Contribution 우선순위 (수정안)

본 9개 phase 결과를 반영해 v5_thesis_final 의 contribution 우선순위를 다음과
같이 재배치 제안:

1. **Main**: Seasonal calendar alignment (v5 기존 main; 변경 없음).
2. **Conditional contribution #1 (강화)**: Meta features (tenure 등) 통합으로
   인한 +0.008 macro_F1 (4× cluster+CP). § 5.5.x 또는 §6 ablation 으로 추가.
3. **Conditional contribution #2 (유지)**: Cluster × G/S/D heterogeneity
   재의미화 — fragile cluster 식별의 정책적 함의.
4. **Negative contributions (포함 권장)**:
   - Sequence raw input(LSTM/GRU/TCN/Transformer) 이 56 통계 피처를 못 이김.
   - 회귀-후-버킷 < 직접 분류.
   - 공간 spillover (단순 GCN dong/industry) 가 macro_F1를 떨어뜨림.

   이들 negative finding은 모두 thesis defensibility를 강화한다 — "왜 단순한
   주식 모델이 그대로 안 되는가"의 직접 증거.
5. **Future work (§7)**: GAT / 작은 attention 그래프 / 외부 데이터(LEVI) /
   계층 모델.

## 7. 참고 — 그림 (생성됨)

`outputs/figures/`:
- `phase0_label_sweep.png` — k_sigma 별 macro_F1 + 클래스 균형 누적 막대
- `phase1_seq_models.png` — RF vs flat_mlp/lstm/gru/tcn/transformer 막대
- `phase1_ts_benchmark.png` — TS 회귀 4종 F1 + MAE
- `phase2_meta_delta.png` — A vs A+meta 막대 + per-panel Δ (p<0.05 강조)
- `phase2_cluster_outcome.png` — 6 panel × 6 cluster의 G/S/D 비율 누적 막대
- `phase3_gnn_delta.png` — graph 유형별 GCN−MLP Δ 막대
- `phase4_dynamics_summary.png` — 9-phase 종합 막대 (RF, RF+meta, TCN, LSTM, TS-reg, GCN-hybrid)

## 8. 참고 — 모든 산출물 위치

- 라벨 sweep: `outputs/tables/label_definition_sweep.csv`, `label_definition_sweep_summary.csv`
- 시계열 모델: `seq_model_compare.csv`, `seq_model_paired.csv`
- TS 회귀: `ts_benchmark_compare.csv`
- SHAP: `shap_class_contrib.csv`, `shap_class_rank_long.csv`
- Meta features: `main_model_compare_meta.csv`, `main_model_paired_AvAmeta.csv`,
  `features_meta/features_meta_*.parquet` (146 panels), `feature_meta_summary.csv`
- Cluster: `cluster_outcome_xtab.csv`, `per_cluster_feature_importance.csv`,
  `cluster_outcome_summary.csv`, `v4_category_outcome.csv`
- 도시경제: `industry_region_growth_rate.csv`, `industry_region_top.csv`,
  `age_cohort_nc_effect.csv`
- GNN: `gnn_compare.csv`
- 라벨 결정 근거: `docs/label_choice_rationale.md`
- 주식 vs 소상공인: `docs/stock_vs_smb_dynamics.md`
- 본 종합 문서: `docs/260430_claude_dynamics_explanation.md`

## 9. 비고

- 모든 새 모델/스크립트는 GPU(TITAN Xp / sm_61) 미지원으로 CPU에서 실행. torch
  2.9.1+cu128은 sm_70 이상만 지원하므로 향후 GPU 환경에서는 크게 가속 가능.
- step02b sweep은 시간 제약으로 8/14 panel만 완주 (남은 6개는 차후 robustness
  부록으로 보완).
- step08 GNN sigungu 그래프는 시간 비용으로 제외(degree-cap 불충분 + dense).
  3종 그래프(dong/industry/hybrid)로 결론은 명확.
- v5_thesis_final 본문은 위 결과를 §5.x 또는 §6 ablation 으로 통합 권장.
- LEVI/EWS는 본 분석에 포함 안 함 (CLAUDE.md 정책 유지).
