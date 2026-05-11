# Paper Track — 학회/저널 submission 패키지

본 폴더는 **학위논문 졸업 이후 (또는 병행하여) 학회/저널 submission**을 위한
자료 묶음이다. 졸업용 thesis_track과 분리됨 — 졸업은 thesis_track으로 끝내고,
이 폴더로 paper 가속.

## 핵심 전략 (한 줄)

> 1순위: **HICSS 2027 (Decision Analytics track)** 6–9개월. Phase 5 benchmark + 70편 lit review가 paper 절반.
>
> 2순위: **DSS (Decision Support Systems)** 12–18개월. EWS calibration + cost-sensitivity 보강 후.

## 파일 안내

| 파일 | 내용 |
|---|---|
| `venue_strategy.md` | 5개 venue 후보 + 우선순위 + trade-off |
| `hicss_2027_plan.md` | HICSS 2027 submission plan (timeline, track, 필요 보강) |
| `paper_outline.md` | HICSS paper 6-section 구조 (initial draft) |
| `abstract_draft_v1.md` | 350-word HICSS abstract 초안 |
| `key_results_one_pager.md` | 협업자 공유용 결과 요약 1페이지 |
| `additional_analyses_plan.md` | paper submission 전 추가 분석 4가지 |
| `dss_extension_plan.md` | DSS 2순위 확장 plan (EWS 보강) |

## 우선순위 단계

### Stage 1 — HICSS 2027 (즉시 시작)

- Phase 5 결과 + 70편 lit review 가 그대로 paper 본문 자료
- **추가 분석 4가지 (additional_analyses_plan.md)** 만 보강하면 paper 80% 완성:
  1. per-cohort LightGBM Δ 분해
  2. EWS calibration + decile table
  3. cost-sensitivity sweep (dollar value)
  4. synthetic long-history ablation (단지 short window이 원인인지)
- 마감: **2026년 6월 중순** (HICSS abstract submission)

### Stage 2 — DSS 확장 (HICSS 통과 후)

- HICSS paper를 토대로 EWS 결정-지원 artifact 측면 강화
- field validation 1개 (실제 정책 partner와 deciles deployment 시나리오)
- managerial implications 강화
- 마감: HICSS 결과 발표 후 ~6–9개월

## 손대지 않는 것

- v5_thesis_final main contribution(seasonal alignment) 변경 없음
- Phase 5 결과 (CSV/figures) 변경 없음 — paper도 같은 정량 자료 사용
- 졸업 일정에 영향 없는 추가 분석만 진행

## 핵심 수치 (paper 본문에서 인용)

| 결과 | 값 | 출처 |
|---|---|---|
| RF baseline macro_F1 (6 panels) | 0.500 | `phase5_external/outputs/tables/phase5_summary.csv` |
| LightGBM tabular Δ | +0.0075 (5/6 wins, 2 p<0.05) | 같은 곳 |
| Meta features Δ (tenure) | +0.0082 (3/8 p<0.05) | `260511/outputs/tables/main_model_paired_AvAmeta.csv` |
| DLinear (best stock SOTA) Δ | −0.139 (6/6 p<0.001) | `phase5_external/.../neuralforecast_paired.csv` |
| Chronos-Bolt zero-shot Δ | −0.211 (6/6 p<0.001) | `phase5_external/.../foundation_zeroshot_paired.csv` |
| TimesFM-200m zero-shot Δ | −0.270 (6/6 p<0.001) | 같은 곳 |
| 14-panel hybrid Δ | +0.0017 (1/14 p<0.05) | `260511/outputs/tables/main_model_paired_AvD.csv` |
| 70편 literature 비교 매트릭스 | 6 영역 × 16 model family | `phase5_external/docs/stock_vs_smb_literature.md` |
