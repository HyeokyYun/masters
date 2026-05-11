# Thesis Track — v5_thesis_final 통합 패키지

본 폴더는 **학위논문(졸업)을 위한** 자료 묶음이다. 빠른 길(졸업 우선)을 따르는
방어 가능한 contribution 정리와 v5_thesis_final 본문에 직접 통합할 수 있는 텍스트를 담는다.

## 목표

- v5_thesis_final draft에 추가/수정할 정확한 섹션 단위 텍스트와 표를 준비
- 졸업 발표(defense)에서 받을 수 있는 질문에 대한 정직한 답변 정리
- main / conditional / negative contribution을 한 매트릭스로 정리

## 파일 안내

| 파일 | 내용 |
|---|---|
| `contribution_matrix.md` | main + conditional + negative contribution 한 표 (수치 포함) |
| `ch5_integration.md` | Ch5 Results 추가/수정 텍스트 (§5.5 LGBM, §5.5.2 14-panel 재집계) |
| `ch6_integration.md` | Ch6 Discussion 추가 (Phase 5 negative 종합 + 70편 lit 비교) |
| `ch7_future_work.md` | Ch7 미래 연구 추가 항목 |
| `v5_diff_summary.md` | 현재 v5 → 통합 후 v5 변경점 한 페이지 |
| `defense_qa.md` | 예상 defense 질문 12개 + 정직한 답변 |

## 한 줄 통합 결과

> 통합 후 v5_thesis_final의 한 줄 contribution:
>
> "**Seasonal calendar alignment**을 main contribution으로 유지하고,
> **LightGBM tabular + tenure meta features**가 RF baseline 위에 안정적 +0.008
> macro_F1 추가 (conditional contribution)임을 정량 입증하며,
> **stock-prediction SOTA 14종 (LSTM/Transformer/foundation models)이 직접
> 이식되지 않음**을 honest negative finding으로 정직히 보고한다."

main 변경 없음, 핵심 수치 변경 없음. 추가만 됨.

## 권장 졸업 일정 (역산)

| 시점 | 작업 |
|---|---|
| Day 0 (현재) | 본 패키지 사용 가능. v5 draft에 통합 시작. |
| +1 week | Ch5/Ch6 통합 완료 (텍스트 약 1,500 단어 추가) |
| +2 weeks | 지도교수 review |
| +3 weeks | 표/그림 final fix (LGBM 추가, Phase 5 figure 통합) |
| +4 weeks | 발표 슬라이드 준비 |
| +5 weeks | defense |

## 손대지 않는 것

- v5 main contribution(seasonal alignment) 변경 없음
- 기존 cited 숫자(seasonal_results_summary.csv 등) 변경 없음
- v4 이전 draft 손대지 않음 (history)
