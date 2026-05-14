# 260514 — 2026-05-14 개별 미팅 준비 자료

본 폴더는 2026-05-14 advisor 개별 미팅용 자료를 담는다. final_thesis/
의 prediction-first framing 재정의와 새로 본문화한 cohort/cluster/
14-model SOTA 결과를 advisor 에게 보고하고, 3 가지 의사결정 (framing
적절성·hybrid 톤·GNN 일정) 을 받아오기 위한 자료다.

## 파일 안내

```
260514/
├── README.md                       — 본 파일
├── meeting_memo.md                 — 메인 1 페이지 메모 (먼저 읽음)
├── tables/                         — 첨부 표 4 종 (markdown)
│   ├── three_contributions.md      — 본문 3 contribution 요약
│   ├── ext_sota14_summary.md       — 14 모델 vs RF baseline 정렬 표
│   ├── cohort_lgbm_delta.md        — 업력 4 cohort × LGB ΔF1
│   └── cluster_lgbm_delta.md       — KMeans 6 cluster × LGB ΔF1
├── figures/                        — 새 PNG 4 장 (DPI 200)
│   ├── fig01_three_contributions.png       — 3-contribution 다이어그램
│   ├── fig02_seasonal_amplitude.png        — 시즌 진폭 + 비교 bar
│   ├── fig03_three_improvement_ladder.png  — improvement ladder 17 모델
│   └── fig04_cohort_cluster_lift.png       — cohort + cluster ΔF1 2 panel
├── decisions/
│   └── decisions_to_discuss.md     — D1/D2/D3 옵션 + 학생 권고
└── src/
    ├── make_figures.py             — 4 PNG 생성 스크립트 (재현용)
    └── make_figures.log            — stdout 로그
```

## 미팅 진행 순서 (제안)

1. **현재 진행 상황** (1 분) — `meeting_memo.md` §1.
2. **Framing 재정의** (5 분) — `meeting_memo.md` §2 + `figures/fig01`.
   - **D1 결정 요청** (`decisions/` D1).
3. **새 결과 공유** (10 분):
   - (a) cohort × cluster 요인 분해 — `figures/fig04` + 표 3, 4.
   - (b) seasonal amplitude — `figures/fig02`.
   - (c) 14-model SOTA + hybrid — `figures/fig03` + 표 2.
4. **Hybrid 톤 의사결정** (3 분) — `decisions/` D2.
5. **GNN 확장 일정** (3 분) — `decisions/` D3.
6. **남은 학생 입력** (3 분) — `meeting_memo.md` §5.
   - 학위명 영문 / 한·영 제목 후보 / 심사 일정 / repeated CV 여부.

## 재현 절차

그림 4 장을 재생성하려면:

```
cd /home/hyeoky98/kcd
python 260514/src/make_figures.py
```

wall clock 약 20 ~ 30 초. matplotlib + pandas + numpy 필요. 한글 글리프
는 fig03 의 일부에서만 사용되었으므로 영어로 교체되었다 (DejaVu Sans
글리프 한계).

## 인용된 외부 산출물 (수정 금지)

- `final_thesis/thesis/` 본문 (재구성 결과)
- `260430_claude/outputs/tables/seasonal_results_summary.csv` (145 spec
  baseline) — fig02 입력
- `260430_claude/outputs/tables/main_model_paired_AvD.csv` (14 panel
  paired) — fig03 hybrid 행 입력
- `260511/phase5_external/outputs/tables/phase5_summary.csv` (14 모델
  ΔF1) — fig03 + ext_sota14_summary.md 입력
- `260511/phase5_external/outputs/tables/lgbm_per_cohort_summary.csv`
  (cohort × cluster ΔF1) — fig04 + cohort/cluster md 입력
- `260430_claude/outputs/tables/age_cohort_nc_effect.csv` (logit β
  per cohort) — cohort_lgbm_delta.md 보완 표

## 미팅 후 후속 작업

D1/D2/D3 advisor 결정에 따른 후속 본문 보정 작업을 `final_thesis/`
에서 수행한다. 가장 가능성 큰 boundary cases:

- D2 = 대안 A 채택 → ch5 §5.5 / ch6 §6.1.2·§6.2.2 / ch1 §1.4 표현
  보정 (반나절).
- D3 = 옵션 A 채택 → GNN 6 panel 확장 + 표 + figure (2–3 일).
- D1 = 대안 A/B 채택 → 학위논문 전체 재서술 (2–3 일).
