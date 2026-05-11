# HICSS 2027 Submission Plan

## 한 줄 목표

> HICSS 58 (2027) Decision Analytics / Service Analytics track 에
> **"Why Stock-Style Forecasting Fails for Small-Business Lifecycle Analytics:
> A 14-Model Benchmark with Calendar-Aligned Evaluation"** 제출.

## Timeline (역산)

| 시점 | 작업 | 산출물 |
|---|---|---|
| **2026-05-11 (현재)** | paper_track 폴더 + thesis_track 분리 완료 | 본 문서들 |
| 2026-05-12 ~ 06-05 (3주) | additional 분석 4가지 실행 | `additional_analyses_plan.md` 산출물 |
| 2026-06-06 ~ 06-15 | abstract 350자 다듬기 | `abstract_draft_v1.md` 최종 |
| **2026-06-15 (HICSS 마감)** | abstract submit | submission ID |
| 2026-06-16 ~ 08-15 (8주) | full paper draft 작성 | 10-page paper |
| **2026-08-17 (HICSS 마감)** | full paper submit | submission |
| 2026-09 ~ 10 | first round review | reviewer comments |
| 2026-10 ~ 11 | revision | revised paper |
| **2026-12 (notification)** | accept/reject 통지 | — |
| **2027-01 (HICSS event, Hawaii)** | 발표 | conference proceedings |

## Target track 추천

HICSS 가 매년 track 구성을 약간 바꾸지만, 안정적으로 fit 되는 후보:

1. **Decision Analytics, Mobile Services and Service Science** (DAMSSS)
2. **Service Analytics** (단독)
3. **Knowledge, Innovation, and Entrepreneurial Systems** (small business 관점)
4. **Digital and Social Media**

CFP 발표 (보통 2–3월) 시 정확한 track 결정. **DAMSSS 가 첫 후보**.

## Paper 핵심 구성

10 페이지 (HICSS 표준). 본 thesis 자료가 본문 80% 차지:

| Section | Page | Content |
|---|---|---|
| 1. Introduction | 1.5 | Problem motivation, contribution summary, RQ 3가지 |
| 2. Related Work | 1.5 | 70편 lit review 압축 (5 영역 매트릭스) |
| 3. Method | 2.0 | Seasonal alignment, panel structure, 14 model 분류 |
| 4. Results | 3.0 | Phase 5 14-model 벤치마크 + 4 mechanism 가설 |
| 5. Discussion | 1.5 | SMB-specific 차별화 5가지 + decision-support implication |
| 6. Conclusion + Future | 0.5 | DSS 확장 미리 명시 |

## RQ (Research Questions) 3가지

```
RQ1. Do stock-prediction state-of-the-art models (LSTM/Transformer/PatchTST/
     TFT/foundation models) transfer to short-window SMB lifecycle classification?
RQ2. Which methodological adaptations (calendar alignment, tenure cohort,
     LightGBM) work, and which (feature attention, FiLM conditioning, spatial
     GNN, cost-sensitive sampling) do not?
RQ3. What characteristics of SMB short-window data invalidate stock-style
     transfer?
```

## 핵심 contribution claims (paper 본문)

1. **First systematic benchmark** of 14 external models (3 foundation + 7 stock
   SOTA + 3 SMB-attention + 1 cost-sensitive) on Korean SMB weekly sales data
   for G/S/D classification. 70-paper literature survey accompanying.

2. **Quantitative negative finding**: all 14 models lose to RF/LightGBM
   baseline by macro_F1 −0.035 to −0.270 (6/6 panels, mostly p<0.001).

3. **Quantitative positive finding**: LightGBM + tenure meta features deliver
   +0.008 each on top of RF baseline (5/8 panels p<0.05).

4. **4 mechanism hypotheses** for why stock-style transfer fails:
   short window, regression-vs-classification gap, multivariate channel
   compression, calendar-season confound dominance.

5. **SMB-specific design implications** for EWS / decision-support: GBDT
   baseline, feature engineering > architecture novelty, feature attention >
   temporal attention.

## 추가 분석 (paper submission 전 필수)

다음 4가지는 `additional_analyses_plan.md`에 상세 — 3주 안에 완료 가능:

1. **per-cohort LightGBM Δ 분해** (1–2일)
2. **EWS calibration + decile table** (2–3일)
3. **cost-sensitivity sweep (dollar value)** (1–2일)
4. **synthetic long-history ablation** (3–4일)

## Co-authors / Acknowledgment 후보

- 지도교수 — first author 본인, second author 지도교수
- 데이터 출처 (KCD) — acknowledgment 명시
- (option) 한 분야 expert (M5/foundation models familiar) — collaborative
  review 시 third author 가능

## Risk Checklist

- [ ] reviewer: "+0.008은 너무 작다" → per-cohort 분해 + benchmark scope 강조
- [ ] reviewer: "왜 foundation models이 finetune 안 됐는가" → zero-shot이 너무
      약해 finetune이 도움될 가능성 낮음 + paper에 명시 + future work
- [ ] reviewer: "한국 데이터에 한정" → method 자체는 일반적 + future work에 다른 도시 명시
- [ ] reviewer: "causal claim 부족" → descriptive/predictive 명시
- [ ] reviewer: "Moirai 결과 불완전" → 1 panel partial 명시 + future work
