# v5_thesis_final — 학위논문 최종 드래프트

## 목적

2026-04-30 지도교수 미팅과 그 후속 분석(`260430_claude/`)을 바탕으로 작성한
학위논문 최종 드래프트다. 본 드래프트는 디펜스 제출본을 기준으로 한 폴리시드
한국어 본문이며, v4_claude 의 내용을 압축·정련하고 4·6·7개월 확장 윈도우
결과를 통합한다.

## v4 / v4_claude 와의 관계

| 드래프트 | 톤 | 핵심 framing |
| --- | --- | --- |
| v4_seasonality_corrected_lifecycle_prediction | "신호 유지 = robustness evidence" | hybrid representation 향상이 시즌 정렬 후에도 살아남는다 |
| v4_claude | "조건부 contribution + 시즌 robustness" | 7개 panel 평균 D−A=+0.0022, 1/7 유의. 라벨 편중 panel에서만 살아남음 |
| **v5_thesis_final (본 드래프트)** | **"시즌 정렬 robustness가 메인, hybrid는 윈도우/시즌 의존적"** | 1·2·3개월 + 4·6·7개월 확장. 14개 panel 비교. framing 정련. |

v4_claude / v4_seasonality_corrected_lifecycle_prediction 는 보존하며 본
드래프트는 그것들의 후속이다.

## 폴더 구조

```
v5_thesis_final/
  README.md                — 본 파일
  ch0_abstract.md          — 한국어 + 영문 초록
  ch1_introduction.md      — 배경, 문제의식, 연구질문, 기여
  ch2_literature.md        — 라이프사이클 / 거래 데이터 / 시계열 분류 / robustness
  ch3_data.md              — KCD weekly + meta, 전처리, specification 카탈로그
  ch4_methodology.md       — 시즌 정렬, 라벨, 피처, A/B/C/D, 평가
  ch5_results.md           — baseline + A/B/C/D 결과
  ch6_discussion.md        — 발견 해석, 한계, future work 분리
  ch7_conclusion.md        — 요약, 다음 단계
  references.md            — APA 7판
  THESIS_FULL.md           — 인덱스
```

## 결과 인용 위치

| 자산 | 경로 |
| --- | --- |
| 시즌 baseline 표 | `260430_claude/outputs/tables/seasonal_results_summary.csv` |
| 메인 모델 비교 | `260430_claude/outputs/tables/main_model_compare.csv` |
| Paired t-test | `260430_claude/outputs/tables/main_model_paired_AvD.csv` |
| Heatmap (RF, off=1) | `260430_claude/outputs/figures/heatmap_macro_f1_rf_off1.png` |
| D − A 막대 | `260430_claude/outputs/figures/main_model_delta.png` |
| 시작연도 비교 | `260430_claude/outputs/figures/yearly_compare_2021_vs_2022.png` |
| 한 페이지 요약 | `260430_claude/docs/260430_claude_summary.md` |

## 작성 정책

- 한국어 본문 + 영문 초록.
- 그림/표는 본 폴더에 복사하지 않고 `260430_claude/outputs/...` 경로 명시.
- 수치는 모두 `260430_claude` 산출물에서 그대로 인용.
- LEVI / EWS / 외부 공공 데이터 / Golden Cross 는 본문 contribution 이 아니라
  ch6.5 / ch7 future work 에서만 1–2 문단으로 다룬다(미팅 결정).
- v4 톤("신호 유지")을 그대로 복사하지 않으며, hybrid representation 향상이
  시즌·윈도우 길이에 의존적이라는 정직한 톤을 유지한다.

## 검토 가이드

빠른 검토는 `ch0_abstract.md` → `ch5_results.md` → `ch6_discussion.md` 순으로
보면 핵심 발견과 framing 이 빠르게 보인다. 결과 검증은
`260430_claude/outputs/tables/*.csv` 의 원본 수치를 직접 대조한다.
