# v5_thesis_final 변경 요약 — One Page Diff

본 통합 패치 적용 후 v5_thesis_final 의 한 페이지 diff 요약.

## 핵심 원칙

- **main contribution 손대지 않음**: seasonal calendar alignment (v5 main) 그대로
- **숫자 변경 없음**: seasonal_results_summary.csv 등 핵심 cited 수치 동일
- **추가만**: 5장에 LightGBM 비교, 6장에 negative 종합, 7장에 future work
- **CLAUDE.md gap 해소**: §5.5.2의 14-panel 재집계 약속 이제 정확히 채움 (+0.0017 정직히 기재)

## 변경 사항 한눈에

| 위치 | 현재 v5 | 변경 후 | 출처 |
|---|---|---|---|
| Ch1 Introduction | main + conditional 한 줄 | C3 (LGBM +0.008) 한 줄 추가 | `contribution_matrix.md` |
| §5.5 main table | A/B/C/D variant 비교, 7 panel | 14 panel + LGBM 추가 | `260511/outputs/tables/main_model_compare.csv`, `phase5_external/.../weighting_compare.csv` |
| §5.5.2 placeholder | "4/6/7m 결과 미수행 (gap)" | "14 panel 재집계 +0.0017, conditional 강화" | `260511/outputs/tables/main_model_compare.csv` |
| §5.6 (신규) | 없음 | Phase 5 외부 SOTA 14종 비교 | `260511/phase5_external/outputs/tables/*` |
| §6.x (신규) | 없음 | Mechanism 4가지 + literature 차별화 5가지 | `260511/phase5_external/docs/stock_vs_smb_literature.md` |
| §6.5 (변경) | LEVI/EWS 1–2 단락 | 70편 lit review 비교 매트릭스 추가 | 같은 곳 |
| §7 (신규 항목) | 일반 future work | per-cohort LGBM Δ, LoRA, synthetic history 등 | `ch7_future_work.md` |
| 부록 (신규) | — | Phase 5 figures 2장 (macro_F1 bars, Δ vs RF) | `phase5_external/outputs/figures/` |

## 분량 추정

- §5.5.2 (재집계): ~300 단어 + 1 표
- §5.6 (Phase 5 비교): ~700 단어 + 3 표 + 2 그림
- §6.x (mechanism + 차별화): ~1,000 단어 + 1 표
- §7.5 추가 항목: ~400 단어
- **총 추가**: ~2,400 단어 + 6 표 + 2 그림

## 발표 슬라이드 영향

- main contribution 슬라이드: 변경 없음
- conditional contribution 슬라이드: C3 LGBM 추가
- limitation / future work 슬라이드: §7.1–§7.5 항목 표시
- (옵션) 신규 슬라이드: "왜 stock SOTA가 안 통하는가" (14종 막대 그래프 + Δ vs RF)

## defense risk 평가

| 위험 | 완화 |
|---|---|
| "+0.008는 너무 작다" | per-cohort 분해, p<0.05 panel 수, M5 winner pattern transfer 언급 |
| "왜 14-panel 재집계가 더 약화됐는가" | v5 framing의 "conditional" 더 강화, seasonal alignment main은 변경 없음 |
| "Negative finding이 너무 많다" | 4가지 mechanism 가설로 정리, "literature transfer 부정 정량 입증"이라는 positive framing |
| "Foundation models은 더 시도해 봐야" | 3종 zero-shot이 모두 F1<0.30 (almost random) — finetune이 RF 근접 가능성 낮음. paper-track으로 명시 |

## 5분 안에 통합 가능한 작업

1. `ch5_integration.md` 의 §5.5.2/§5.5.3/§5.6 텍스트 복사 → ch5_results.md 알맞은 위치에 paste
2. `ch6_integration.md` 의 §6.x 통째로 복사 → ch6_discussion.md 끝에 추가
3. `ch7_future_work.md` 의 §7.1–§7.5 → ch7 미래 연구에 추가
4. Phase 5 figures 2장을 thesis figures 폴더에 복사 + caption 작성

## 점검 체크리스트 (defense 직전)

- [ ] main contribution 한 줄 변경 없음 확인
- [ ] §5.5 main table 행 수가 7 → 14 로 늘었음 확인
- [ ] LGBM 행이 conditional contribution 표에 들어가 있음
- [ ] Phase 5 negative figure (`phase5_delta_vs_rf.png`) 포함
- [ ] §6.x mechanism 4가지 정량 인용 (Δ 값, p값) 정확
- [ ] §7 paper-track 항목이 future work으로 명시
- [ ] defense_qa.md 의 12개 질문 답변 확인
