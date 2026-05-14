# 03. 저널 / 컨퍼런스 버전 (Paper-track)

> **분리 원칙**: 학위논문 (`final_thesis/`) 과 paper-track (`260511/paper_track/`)
> 은 같은 데이터·코드 위에서 **framing 만 다른 두 산출물**. 학위논문이
> 졸업 우선이며, paper-track 은 졸업 후 6–18 개월 가속용.
> **한 줄 결론**: **HICSS 2027 (1순위) → DSS (2순위) → I&M (3순위)** 순서.

---

## 1. Venue 후보 5 개 비교

원본: `260511/paper_track/venue_strategy.md`.

| Venue | Fit | 강점 | 약점 | 마감 / 주기 | 우선순위 |
| --- | --- | --- | --- | --- | --- |
| **HICSS 2027** | Decision / Service Analytics track | Phase 5 14-model + 70 편 lit review 그대로 본문. CLAUDE.md "strongest fit". | 학회, citation index DSS 보다 낮음. | abstract **2026-06-15**, full paper **2026-08-17**, event Jan 2027 (Hawaii) | **★★★ 1순위** |
| **DSS** (Decision Support Systems) | Decision-support artifact, calibration, cost-sensitivity | 저널 IF ≈ 7. SMB EWS 정확한 fit. LGBM + cost-sensitive. | EWS calibration table + field validation 보강 필요. review 6–12 개월. | rolling | **★★ 2순위** |
| **Information & Management** | Digital trace, managerial implications | I&M IF ≈ 10. 디지털 매출 데이터 핵심. | managerial framing + theory contribution 강화 필요. | rolling | **★ 3순위** |
| Small Business Economics | tenure cohort × new-customer-slope economic mechanism | 도메인 직접 fit. tenure cohort 결과 활용. | causal inference + econometric framing 필요. 본 thesis 는 descriptive. | rolling | △ 보강 후 |
| ICIS / MISQ / ISR / JMIS | IS top venue | top tier exposure | IS theory contribution 부족. high rejection. | Apr/May | × paper 1회 후 |

---

## 2. HICSS 2027 (1순위) — 핵심 패키지

원본: `260511/paper_track/hicss_2027_plan.md` + `abstract_draft_v1.md`.

### 2.1 Title (draft)

> **"Why Stock-Style Forecasting Fails for Small-Business Lifecycle Analytics:
> A 14-Model Benchmark with Calendar-Aligned Evaluation"**

### 2.2 RQ 3 가지

- **RQ1**. Do stock-prediction SOTA models (LSTM/Transformer/PatchTST/TFT/
  foundation) transfer to short-window SMB lifecycle classification?
- **RQ2**. Which methodological adaptations (calendar alignment, tenure cohort,
  LightGBM) work, and which (feature attention, FiLM, spatial GNN, cost-
  sensitive sampling) do not?
- **RQ3**. What characteristics of SMB short-window data invalidate stock-style
  transfer?

### 2.3 Contribution claims 5 가지

1. **First systematic benchmark** of 14 external models (3 foundation + 7 stock
   SOTA + 3 SMB-attention + 1 cost-sensitive) on Korean SMB weekly card-
   transaction data for G/S/D classification + 70-paper lit review.
2. **Quantitative negative finding**: 14 모델 모두 RF/LightGBM baseline 대비
   macro-F1 **−0.035 ~ −0.270** (6/6 panel, 대부분 p<0.001).
3. **Quantitative positive finding**: LightGBM + tenure meta features 가
   **각 +0.008** 추가 (5/8 panel p<0.05).
4. **4 mechanism 가설**: short window / regression→classification 손실 /
   multivariate channel compression / calendar-season confound.
5. **SMB-specific design template**: GBDT baseline first, feature engineering >
   architecture novelty, feature attention > temporal attention.

### 2.4 Timeline (역산)

| 시점 | 작업 | 산출물 |
| --- | --- | --- |
| 2026-05-14 (오늘) | advisor 미팅에서 framing 합의 | D1/D2/D3 결정 |
| 2026-05-15 ~ 06-05 (3주) | additional 분석 4 가지 (`additional_analyses_plan.md`) | per-cohort 분해 / EWS calibration / cost-sensitivity sweep / synthetic long-history |
| 2026-06-06 ~ 06-15 | abstract 350 단어 다듬기 | `abstract_draft_v1.md` 최종 |
| **2026-06-15** | **abstract submit** | submission ID |
| 2026-06-16 ~ 08-15 (8주) | full paper 10 페이지 draft | 본문 |
| **2026-08-17** | **full paper submit** | — |
| 2026-09 ~ 11 | review + revision | reviewer comments |
| **2026-12** | accept/reject 통지 | — |
| **2027-01** | HICSS 발표 (Hawaii) | proceedings |

### 2.5 추가 분석 4 종 (HICSS submission 전 필수)

- (1) per-cohort LightGBM Δ 분해 — **이미 완료** (`lgbm_per_cohort_summary.csv`).
- (2) EWS calibration + decile table — 2–3 일.
- (3) cost-sensitivity sweep (dollar-value version) — 1–2 일.
- (4) synthetic long-history ablation — 3–4 일.

---

## 3. DSS (2순위) — 확장 전략

원본: `260511/paper_track/dss_extension_plan.md`.

### 3.1 한 줄 framing

> "Small-Business Lifecycle Early Warning System: Calibrated, Cost-Sensitive
> Decision Support from Card-Transaction Trace"

### 3.2 신규 자료 (~40%)

| Paper section | 자료 | 신규 작업 |
| --- | --- | --- |
| Artifact design | LightGBM + tenure feature EWS proba | thesis 그대로 |
| Calibration | Brier score, reliability diagram | **신규** |
| Cost sensitivity | proba decile × observed-decline | **신규 (일부 phase 2.3 활용)** |
| Policy implication | fragile cluster 식별 → 정책 시나리오 | **신규** |
| (option) Field validation | 정책 partner 1 개 deployment | **대규모 신규** |

### 3.3 Timeline

- 2027 Q1 — HICSS 발표 직후 DSS 작성 시작.
- 2027 Q2 — DSS submission.
- 2027 Q3–Q4 — review + revision.

---

## 4. I&M (3순위) — managerial framing

원본: `260511/paper_track/paper_outline.md`.

- 50% 활용 + 50% framing 재정의.
- digital trace 관점 + managerial implication 강화.
- additional theory layer (예: organizational learning, customer-base
  diffusion) 필요.
- DSS revision/acceptance 후 (2028 Q1–Q2) 작성 권장.

---

## 5. Phase 5 결과의 paper 활용도

| Phase 5 산출물 | HICSS | DSS | I&M |
| --- | :---: | :---: | :---: |
| 14-model 벤치마크 (`phase5_summary.csv`) | ★★★ | ★ | ★ |
| 70 편 lit review (`stock_vs_smb_literature.md`) | ★★★ | — | ★ |
| Cohort 요인 분해 (`lgbm_per_cohort_summary.csv`) | ★★ | ★★★ | ★★ |
| Cluster fragile (`cluster_outcome_xtab.csv`) | ★ | ★★★ | ★ |
| EWS calibration (미작성, 신규 필요) | ★ | ★★★ | ★ |
| SHAP per-class (`shap_class_contrib.csv`) | ★ | ★★ | ★★ |

---

## 6. 위험 / 완화

| 위험 | 완화 |
| --- | --- |
| HICSS submission 너무 빠름 → 결과 불완전 | abstract 6 월 / full paper 8 월. 추가 분석 3 개월 시간 있음. |
| +0.008 macro-F1 너무 작아 reviewer reject | per-cohort 분해 (Q4_long +0.019, fragile cluster +0.044) + 14-model benchmark scope 강조. |
| DSS 너무 늦으면 결과 stale | HICSS 발표 직후 (1–3 개월 내) DSS submission. |
| Moirai 결과 1 panel partial | submission 까지 6 panel 풀 가능 여부 점검. |
| advisor co-author 일정 | 미팅에서 추후 일정 협의. |
| 한국 데이터 한정 비판 | method 자체는 일반적 + future work 에 다른 도시 명시. |

---

## 7. 학위논문 vs paper-track 분리 원칙

| 항목 | 학위논문 (`final_thesis/`) | paper-track (`260511/paper_track/`) |
| --- | --- | --- |
| 우선순위 | 졸업 우선 (2026 정기) | 졸업 후 6–18 개월 가속 |
| Framing | prediction-first 3 contribution | venue 별 (HICSS = benchmark / DSS = artifact / I&M = managerial) |
| 인용 본문 | ch0 ~ ch7 + references | abstract_draft_v1.md / paper_outline.md |
| 결정 채널 | advisor 1:1 미팅 | submission + reviewer 응답 |
| 수치 원천 | 동일 (`260430_claude/outputs/tables/`, `260511/phase5_external/outputs/tables/`) | 동일 |

---

## 8. 한 줄 요약

> Paper-track 은 HICSS 2027 (Decision Analytics track) 을 1 순위로,
> **2026-06-15 abstract / 08-17 full paper** 마감을 역산해 추가 분석 4 종
> (per-cohort 분해 ✅ 외 3 종) 을 5–6 월에 진행. DSS (2 순위) 는 EWS
> calibration + cost-sensitivity 보강 후 HICSS 발표 직후 (2027 Q2) submission.
> 학위논문 졸업이 paper 보다 우선.
