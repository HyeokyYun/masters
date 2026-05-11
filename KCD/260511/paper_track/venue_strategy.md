# Venue Strategy — 5개 후보 + 우선순위

본 thesis의 결과를 어느 학회/저널에 제출할지 정리. CLAUDE.md "Venue Strategy"
와 Phase 5 정량 결과를 종합.

## 한 줄 결론

> **HICSS 2027 (1순위) → DSS (2순위) → Information & Management (3순위)** 의 순서로 진행. ICIS / MISQ 는 paper 1회 성공 후 검토.

## 5개 후보 비교

| Venue | 정확한 fit | 강점 | 약점 | 마감/주기 | 우선순위 |
|---|---|---|---|---|---|
| **HICSS 2027** | Decision Analytics / Service Analytics / Public Sector Analytics track | Phase 5 14-model benchmark + 70편 lit review 그대로 본문. CLAUDE.md "strongest fit". 통과율 비교적 높음. | 학회 paper, citation index DSS보다 낮음 | abstract Jun 15 2026 / full paper Aug 17 2026 / event Jan 2027 | **★★★ 1순위** |
| **DSS (Decision Support Systems)** | Decision-support artifact, calibration, cost-sensitivity | 저널, IF≈7. SMB EWS 정확한 fit. LGBM + cost-sensitive 결과 활용. | EWS calibration table + field validation 보강 필요. review 6–12 months. | rolling | **★★ 2순위** |
| **Information & Management** | Digital trace, managerial implications | I&M IF≈10. 디지털 매출 데이터 핵심. | managerial framing 강화 필요. theory contribution 요구. | rolling | **★ 3순위** |
| **Small Business Economics** | Tenure cohort × new-customer-slope economic mechanism | SBE는 본 도메인 직접 fit. tenure cohort 결과 활용. | causal inference + econometric framing 필요. 본 thesis는 descriptive. | rolling | △ 보강 후 |
| **ICIS** | IS conference top tier | top conference exposure | IS theory contribution 부족. high rejection. | Apr/May | × paper 1회 후 |
| **MISQ/ISR/JMIS** | Top IS journals | top tier citation | theory contribution far away. paper 2–3회 후. | rolling | × 장기 |

## 시점별 권장 순서

### Year 1 (now ~ +12 months)

- **Months 1–3**: HICSS 추가 분석 4가지 (paper_track/additional_analyses_plan.md)
- **Months 3–6**: HICSS abstract + full paper submit (마감 Aug 2026)
- **Months 6–12**: HICSS review 대기 + DSS extension 준비 (EWS calibration)

### Year 2 (+12 ~ +24)

- **HICSS 2027 발표 (Jan 2027, Hawaii)** — networking + feedback
- HICSS 결과 토대로 DSS journal submission (Q2 2027)
- DSS review 대기 + I&M 보강 시작 (managerial framing)

### Year 3+

- DSS revision/acceptance → I&M paper
- (optional) LEVI 통합 SBE paper

## 각 venue 별 본 thesis 자료 사용도

### HICSS — 95% 그대로 활용 가능

| Paper section | 사용할 본 thesis 자료 |
|---|---|
| Introduction | `260511/phase5_external/docs/phase5_findings.md` 의 한 줄 결과 |
| Related Work | `260511/phase5_external/docs/stock_vs_smb_literature.md` 의 70편 |
| Method | thesis Ch4 seasonal alignment + Ch5 LGBM |
| Results | Phase 5 14-model benchmark + Phase 0–4 + figures 7장 |
| Discussion | thesis_track/ch6_integration.md mechanism 4가지 + 차별화 5가지 |
| Future | DSS 확장 + LEVI |

추가 분석: 4가지 (additional_analyses_plan.md)

### DSS — 60% 활용, 40% 신규 (EWS 보강)

| Paper section | 사용할 본 thesis 자료 |
|---|---|
| Artifact design | LightGBM + tenure feature를 EWS proba output로 |
| Calibration | Brier score, reliability diagram (**신규**) |
| Cost sensitivity | proba decile × observed-decline (**신규 — 일부 phase 2.3 자료 활용**) |
| Policy implication | fragile cluster 식별 (Phase 2.3) → 정책 시나리오 (**신규**) |
| Field validation | (option) 정책 partner 1개와 deciles deployment (**대규모 신규**) |

### I&M — 50% 활용, 50% framing 재정의

managerial digital trace 관점으로 본 thesis 결과를 재포장. additional theory
layer 필요.

## 위험 / trade-off

| 위험 | 완화 |
|---|---|
| HICSS submission 너무 빠름 → 결과 불완전 | abstract 6월, full paper 8월 — 추가 분석 3개월 시간 있음 |
| +0.008 macro_F1 너무 작아 reviewer reject | per-cohort 분해 (Q4_long 등 sub-population에서 더 큼 가정) + benchmark scope 강조 |
| DSS는 너무 늦으면 결과 stale | HICSS 결과 발표 직후 (1–3개월 내) DSS submission |
| ICIS/MISQ 의 IS theory 부족 | paper 1회 성공 후 검토 |

## 한 줄 결론

> HICSS 1순위로 시작, 추가 분석 4가지 보강 후 6월 abstract 제출. paper-track 의
> 나머지 문서가 그 timeline 을 지원한다.
