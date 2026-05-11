# 학위논문 전체 인덱스 (v5_thesis_final)

본 파일은 각 장의 진입점만 모은 인덱스이며, 본문 합본이 아니다. 마크다운
링크로 각 장 파일을 참조한다.

## 메타

- **제목**: 시즌 정렬 Rolling-Window 검증으로 본 카드거래 기반 점포 라이프
  사이클 분류의 조건부 contribution
- **저자**: 윤혁
- **지도교수**: KAIST 김지희
- **학위**: 석사 (논문)
- **데이터**: KCD 서울시 외식업 주간 카드거래 패널 (2021-01-01 ~
  2023-08-28, 142 주, 약 5만 9천 점포)
- **분석 산출물**: `260430_claude/outputs/`
- **드래프트 일자**: 2026-05-03
- **드래프트 정책**: README.md 참조

## 장 구성

| 장 | 파일 | 핵심 메시지 |
| --- | --- | --- |
| 초록 | [`ch0_abstract.md`](ch0_abstract.md) | 한·영 초록. cluster + CP 는 조건부 contribution, 시즌 정렬 robustness 가 메인 contribution. |
| 1장 서론 | [`ch1_introduction.md`](ch1_introduction.md) | 미팅에서 제기된 두 쟁점, RQ1 ~ RQ4, 두 contribution 명시. |
| 2장 선행연구 | [`ch2_literature.md`](ch2_literature.md) | 라이프사이클 / 거래 데이터 진단 / 시계열 분류 / 시즌 통제 robustness 네 갈래. |
| 3장 데이터 | [`ch3_data.md`](ch3_data.md) | KCD weekly panel 변수, 전처리, 145 specification 카탈로그. |
| 4장 방법론 | [`ch4_methodology.md`](ch4_methodology.md) | 시즌 정렬 rolling-window, G/S/D 라벨, 가변 윈도우 피처, A/B/C/D 모델, paired t-test. |
| 5장 결과 | [`ch5_results.md`](ch5_results.md) | 80 + α specification baseline + 14 panel × A/B/C/D, Δ(D−A) = +0.0022, 1/7 유의. |
| 6장 논의 | [`ch6_discussion.md`](ch6_discussion.md) | 시즌 confound 함의, hybrid representation 외적 타당성, 한계, future work 분리. |
| 7장 결론 | [`ch7_conclusion.md`](ch7_conclusion.md) | 요약 + 후속 4 가지 (검정력 보강, 신규 고객 선행성 재검증, 메서드 정교화, 외적 타당도). |
| 참고문헌 | [`references.md`](references.md) | APA 7판. 본문 인용만. |

## 데이터 / 산출물 빠른 참조

| 출처 | 위치 |
| --- | --- |
| 원시 데이터 | `original_data/weekly.parquet`, `original_data/meta.csv` |
| 미팅 전사 | `thesis/meeting_stt/260430_personal_meeting.txt` |
| 분석 코드 | `260430_claude/src/step01-step05*.py` |
| 분석 한 페이지 요약 | `260430_claude/docs/260430_claude_summary.md` |
| 시즌 결과 표 | `260430_claude/outputs/tables/seasonal_results_summary.csv` |
| 메인 모델 비교 표 | `260430_claude/outputs/tables/main_model_compare.csv` |
| Paired t-test | `260430_claude/outputs/tables/main_model_paired_AvD.csv` |
| 시즌 heatmap | `260430_claude/outputs/figures/heatmap_macro_f1_rf_off1.png` |
| D − A 막대 | `260430_claude/outputs/figures/main_model_delta.png` |
| 시작연도 비교 | `260430_claude/outputs/figures/yearly_compare_2021_vs_2022.png` |

## 본문에서 다루지 않은 항목 (future work / 응용)

- LEVI 도시경제 활력 지수 → ch6.5, ch7 §7.2
- EWS 조기 쇠퇴 경보 → ch6.5, ch7 §7.2
- 외부 공공 데이터 5 종 추가 검증 → ch6.5
- 신규 고객 유입 선행성(Golden Cross) 의 시즌 정렬 재검증 → ch7 §7.2
- 도소매 · 서비스업으로의 일반화 → ch6.4

## 빌드 / 검토 가이드

- 본 드래프트는 마크다운 그대로 검토한다 (PDF / LaTeX 빌드 없음).
- 각 장은 독립적으로 읽을 수 있도록 작성됐다. 빠른 검토는 ch5 → ch6 →
  ch0 (abstract) 순으로 보면 핵심 발견과 framing 이 빠르게 보인다.
- 결과 검증 시 `260430_claude/outputs/tables/*.csv` 의 원본 수치를 직접
  대조한다(특히 §5.5 의 표).
