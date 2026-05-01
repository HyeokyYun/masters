# v4_claude — 학위논문 드래프트 (조건부 contribution + 시즌 robustness)

## 목적

2026-04-30 지도교수 미팅(`thesis/meeting_stt/260430_personal_meeting.txt`)을 기반
으로 한 학위논문 드래프트. `260430_claude/` 시즌 정렬 롤링 윈도우 + 메인 모델
재학습 결과(2026-05-01 실행)를 본문 핵심 결과로 사용한다.

## v4 (`v4_seasonality_corrected_lifecycle_prediction`)와의 차이

같은 9장 골격을 차용하되, 두 가지를 정직하게 반영한다.

1. **메인 모델 contribution 톤 조정.** v4는 cluster + change-point가 baseline
   대비 향상한다는 결과를 "신호가 유지된다 = robustness evidence"로 framing.
   본 드래프트(v4_claude)는 시즌 정렬 7개 panel × 5-fold paired t-test에서
   평균 Δ(D−A) = +0.0022 macro-F1, 1/7 panel만 5% 유의(`sy2022_sm03_w3m_off1`,
   p=0.026)임을 명시한다. 따라서 cluster+CP의 향상은 **조건부 contribution**
   (라벨이 편중된 시즌 panel에서만 살아남는 효과)으로 기술한다.
2. **시즌 confound 노출 자체를 contribution으로 격상.** 시즌 정렬을 단순한
   robustness check가 아니라, 기존 라이프사이클 분류 연구 라벨 정의의 취약성을
   드러내는 방법론적 발견으로 ch5/ch6에서 정조준한다.

## 디렉토리

```
v4_claude/
  README.md                — 본 문서
  ch0_abstract.md          — 한국어 초록 + 영문 abstract
  ch1_introduction.md      — 배경, 문제의식, 연구 질문, contribution
  ch2_literature_review.md — 라이프사이클, 시계열 분류, 시즌 통제 robustness
  ch3_data.md              — KCD weekly panel, 변수 정의, 전처리
  ch4_methodology.md       — 시즌 정렬 롤링 윈도우, 라벨, 피처, A/B/C/D 모델
  ch5_results.md           — 시즌 80개 + 7 panel × A/B/C/D 결과
  ch6_discussion.md        — 조건부 contribution, 시즌 confound 함의, 한계
  ch7_conclusion.md        — 요약 + future work
  references.md            — 참고문헌
  THESIS_FULL.md           — 전체 인덱스
```

## 인용 자산 (read-only)

- 미팅: `thesis/meeting_stt/260430_personal_meeting.txt`
- 분석 결과:
  - `260430_claude/docs/260430_claude_summary.md` — 한 페이지 결론
  - `260430_claude/docs/260430_claude_rolling_results.md`
  - `260430_claude/docs/260430_claude_main_model_results.md`
  - `260430_claude/outputs/tables/seasonal_results_summary.csv`
  - `260430_claude/outputs/tables/main_model_compare.csv`
  - `260430_claude/outputs/tables/main_model_paired_AvD.csv`
  - `260430_claude/outputs/figures/heatmap_macro_f1_rf_off1.png`
  - `260430_claude/outputs/figures/main_model_delta.png`
  - `260430_claude/outputs/figures/yearly_compare_2021_vs_2022.png`
- 코드 (이론/재현용 인용):
  - `260430_claude/src/step01_build_seasonal_panels.py` ~ `step05_train_main_model.py`
  - `top_tier/src/step00_prepare_original_panel.py`
  - `top_tier/src/step03_prediction_model.py`
  - `top_tier/src/step10_hybrid_prediction.py`

## 본 드래프트의 작성 정책

- 한국어 본문 + 영문 abstract 병기.
- LEVI / EWS / 외부 공공 데이터 / 도시활력 / Golden Cross는 본문 contribution
  으로 다루지 않음. ch6.5 / ch7 future work 1–2 문단으로만 처리.
- 그림·표는 본 폴더에 복제하지 않고 `260430_claude/outputs/...` 경로 명시.
- 모든 수치는 `260430_claude/outputs/tables/*.csv`에서 그대로 인용. 임의의
  반올림으로 톤을 부드럽게 만들지 않음.
- 미팅에서 격리된 항목(2/3/4/5번)은 ch6.5에서 한 단락으로만 위치 정리.

## 빌드 / 리뷰 가이드

- 본 드래프트는 PDF / LaTeX 빌드를 포함하지 않는다. 검토는 마크다운 그대로.
- ch5의 수치를 검증할 때는 `260430_claude/outputs/tables/main_model_compare.csv`,
  `main_model_paired_AvD.csv`, `seasonal_results_summary.csv`를 직접 열어
  대조한다.
- `THESIS_FULL.md`는 각 장 진입점 인덱스로 사용한다 (전체 본문을 합치지는
  않음).

## 결정/한계 메모

- 다음 미팅에서 contribution framing을 (a) 조건부 contribution / (b)
  trajectory 정성 해석 / (c) 시즌 confound 노출 메인 — 셋 중 어느 방향으로
  최종 정조준할지 교수와 합의 필요. 본 드래프트는 (a)+(c) 병행안.
- repeated CV / bootstrap, 신규 고객 유입 선행성 시즌 panel 재검증은 ch6.4 /
  ch7에서 후속으로만 언급. 본 드래프트에서는 실행하지 않음.
