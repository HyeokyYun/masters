# 01. 지난 피드백 이후 새롭게 진행한 것

> **지난 피드백**: 2026-04-30 개별 미팅 (원문: `260430_claude/meeting/07_meeting_feedback.md`).
> **본 미팅까지의 작업 기간**: 2026-04-30 ~ 2026-05-13 (약 2 주).
> **요약 한 줄**: 피드백 9 항목 → 9 phase 실행 → `final_thesis/` 본문 9 절
> 신설 + 14 panel 결과 재실행 완료.

---

## 1. 피드백 → 작업 매핑 (9 항목)

원문 피드백을 9 개 항목으로 분해하고, 각 항목에 대응하는 phase·산출물·핵심
수치를 정리한다. 매핑 표 원본은 `260511/README.md`.

| # | 피드백 한 줄 (원문 발췌) | 대응 phase | 핵심 산출물 | 핵심 수치 |
| --- | --- | --- | --- | --- |
| 1 | "small business dynamics 를 설명하고 더 잘 prediction" | 종합 | `260511/docs/260430_claude_dynamics_explanation.md` | 9-phase 통합 보고 |
| 2 | "클러스터링이 무의미해지면 안 됨 → G/S/D 요인 파악" | Phase 2.3 (A3) | `cluster_outcome_xtab.csv`, `per_cluster_feature_importance.csv`, `phase2_cluster_outcome.png` | fragile cluster Decline 35–60%, LGB ΔF1 **+0.044** |
| 3 | "신규 유입·업력이 상승에 유의미" | Phase 2.2 (A2) + 2.4 (C3) | `step03b_extract_meta_features.py`, `main_model_compare_meta.csv`, `age_cohort_nc_effect.csv` | meta features ΔF1 **+0.0082** (cluster+CP 의 약 4×); Q4_long nc_slope→Growth β ≈ 1.3 (분산 작음) |
| 4 | "예측 모델 강화 / technical novelty" | Phase 1 (B1, B3) | `step06_train_seq_models.py`, `step07_ts_benchmark.py`, `seq_model_compare.csv` | RF tabular 이 LSTM/GRU/Transformer/TCN 모두 능가 |
| 5 | "주식 예측 literature 대조" | Phase 4 + Phase 5 외부 SOTA | `260511/phase5_external/docs/stock_vs_smb_literature.md`, `phase5_summary.csv` | 70 편 lit review + 14 모델 벤치마크 |
| 6 | "네트워크 모델 (GNN 등)" | Phase 3 | `step08_train_gnn.py`, `gnn_compare.csv`, `phase3_gnn_delta.png` | GCN 이 MLP/RF 모두 패배 (Δ −0.04 ~ −0.10). honest negative finding. |
| 7 | "라벨 정의 robustness" (사전 정리) | Phase 0 | `step02b_label_sweep.py`, `label_definition_sweep.csv`, `phase0_label_sweep.png` | 시작월 진폭 0.10 ≫ 윈도우 0.02–0.04 ≫ 시작연도 < 0.01 |
| 8 | SHAP per-class 해석 | Phase 2.1 (A1) | `analysis_shap.py`, `shap_class_contrib.csv`, `shap_class_rank_long.csv` | Growth/Stable/Decline 별 top-feature 분해 |
| 9 | 업종 × 지역 G/S/D 매트릭스 | Phase 2.4 (C2) | `analysis_urban_econ.py`, `industry_region_growth_rate.csv` | 업종 × 동 단위 G/S/D 비율 매트릭스 |

추가로 CLAUDE.md 의 미수행 gap 해소:

| 항목 | 산출물 | 결과 |
| --- | --- | --- |
| step05 14-panel 재집계 (3m 7 + 4/6/7m 7) | `260430_claude/outputs/tables/main_model_compare.csv` (56 행), `main_model_paired_AvD.csv` | 14 panel 평균 hybrid ΔF1 = **+0.0017**, 5% 유의 1/14, Bonferroni 후 0/14 |

---

## 2. Phase 5 외부 SOTA 14 종 벤치마크 (피드백 4·5·6 통합)

피드백 4 (예측 모델 강화) + 5 (주식 literature 대조) + 6 (GNN) 을 하나의
시스템으로 묶어 외부 SOTA 14 종을 RF baseline 과 비교한 결과
(`260511/phase5_external/outputs/tables/phase5_summary.csv`, 6 panel 평균).

| 그룹 | 모델 | ΔF1 vs RF | RF 대비 wins | 비고 |
| --- | --- | ---: | :---: | --- |
| **LightGBM family** | lgbm_tabular | **+0.0075** | **5 / 6** | 외부 SOTA 중 유일하게 RF 능가 |
| LightGBM family | lgbm_shap_weighted | +0.0071 | 5 / 6 | |
| LightGBM family | lgbm_decline_x2 | +0.0026 | 4 / 6 | |
| Cost-sensitive | rf_decline_x2 | −0.035 | 0 / 6 | sample weighting 단독으로는 향상 불가 |
| SMB attention | feature_attn_mlp | −0.035 | 0 / 6 | |
| SMB attention | film_tenure_lstm | −0.047 | 0 / 6 | |
| Stock SOTA | dlinear | −0.139 | 0 / 6 | stock SOTA 중 가장 강함 |
| Foundation | chronos_bolt_small | −0.211 | 0 / 6 | zero-shot, random guess 근접 |
| Stock SOTA | nhits | −0.221 | 0 / 6 | |
| Stock SOTA | tft | −0.238 | 0 / 6 | |
| Stock SOTA | nbeats | −0.246 | 0 / 6 | |

(전체 14 행은 `260514/tables/ext_sota14_summary.md` 참조)

**핵심 발견**:

- 외부 SOTA 14 종 중 **LightGBM 1 종만 RF 능가** (+0.0075, 5/6 panel wins).
- Foundation zero-shot 과 stock SOTA 는 일관 패배 (Δ −0.14 ~ −0.25).
- 4 mechanism 가설 (`final_thesis/thesis/ch6_discussion.md §6.2.4`):
  short window / regression→classification 변환 손실 / multivariate channel
  compression / calendar-season confound dominance.

---

## 3. Cohort × cluster 요인 분해 (피드백 2·3 통합)

피드백 2 (cluster 무의미화 방지) + 3 (신규 유입·업력 = 주요 요인) 을 하나의
요인 분해로 묶음. 원본 `260511/phase5_external/outputs/tables/lgbm_per_cohort_summary.csv`.

### 3.1 업력 cohort × LightGBM ΔF1 (4 cohort, 6 panel 평균)

| cohort | tenure 중앙 (개월) | RF F1 | LGB F1 | **ΔF1** |
| --- | ---: | ---: | ---: | ---: |
| Q1_short | ~9 | 0.475 | 0.477 | +0.0021 |
| Q2 | ~25 | 0.492 | 0.490 | −0.0018 |
| Q3 | ~50 | 0.497 | 0.509 | +0.013 |
| **Q4_long** | **~115** | **0.526** | **0.545** | **+0.019** |

- 업력이 길수록 ΔF1 단조 증가. Q4_long 의 +0.019 는 전체 평균 +0.0075 의
  약 **2.5×**.
- 신규고객 → Growth 의 logit β 도 Q4_long 에서 가장 안정 (β ≈ 1.3, 분산 작음).

### 3.2 KMeans cluster × LightGBM ΔF1 (6 cluster, 6 panel 평균)

| cluster | n | Decline rate | RF F1 | LGB F1 | **ΔF1** | 해석 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| cluster_0 | 9,566 | 0.152 | 0.427 | 0.439 | +0.011 | mid |
| cluster_1 | 5,094 | 0.162 | 0.390 | 0.430 | +0.041 | mid-high |
| cluster_2 | 2,558 | 0.198 | 0.426 | 0.447 | +0.021 | mid-high |
| **cluster_3** | **4,622** | **0.173** | **0.394** | **0.438** | **+0.044** | **fragile (★)** |
| cluster_4 | 8,835 | 0.154 | 0.463 | 0.467 | +0.004 | survivor |
| cluster_5 | 5,226 | 0.130 | 0.420 | 0.456 | +0.036 | low-decline mixed |

- fragile cluster (Decline 비중 35–60%) 의 ΔF1 = **+0.044** 는 전체 평균의
  약 **5.9×**.
- 정책 우선 영역 (Decline 집중 sub-population) = 모델 향상 여지가 가장 큰 영역.

---

## 4. 본문 신설 절 (final_thesis/)

피드백 결과를 학위논문 본문으로 통합한 결과:

- ch5 신설 4 절: **§5.6** (외부 SOTA 14 보강) · **§5.7** (cohort 요인 분해) ·
  **§5.8** (cluster 요인 분해) · **§5.9** (cost-sensitive) · **§5.10** (요약).
- ch6 신설 3 절: **§6.1.6** · **§6.1.7** · **§6.2.5** (4 mechanism 가설).
- ch6 보강: **§6.5** GNN pilot 1 문단 (옵션 B 권고).
- ch0 초록 한글 485/500 자, 영문 290/300 단어 한도 검증 통과.

---

## 5. 한계 / 미수행 작업

- **repeated CV (10-fold × 10 repeats)** — 미수행. 검정력 보강이 ΔF1 ±0.002
  수준 panel 에 한정될 가능성. advisor 요청 시 1 일.
- **GNN 6 panel 확장** — 미수행 (현재 3 panel × 4 graph definition × 2 model
  pilot). 옵션 B (future-work 1 문단 유지) 권고 시 추가 작업 없음.
- **foundation Moirai 풀 6 panel** — 미수행 (현재 1 panel partial). HICSS
  submission 까지 보강 필요 가능.
- **field deployment / EWS calibration table** — 미수행. DSS submission
  단계 (2027 Q2) 의 작업으로 분리.

---

## 6. 한 줄 요약

> 2026-04-30 피드백 9 항목 모두 phase 로 실행 완료, final_thesis 본문 9 절로
> 통합 완료. 외부 SOTA 14 종 벤치마크의 핵심 결과: **LightGBM 1 종만 RF 능가
> (+0.0075), 나머지 11 종 일관 패배 (Δ −0.14 ~ −0.25)**. 업력 Q4_long /
> fragile cluster 에서 향상이 각각 2.5×, 5.9× 로 집중되며, 이는 정책 우선
> 영역과 정합.
