# meeting/ — 개인 미팅 자료 (Rolling 중심)

`260430_claude/`의 rolling(시즌 정렬) 결과를 다음 개인 미팅용으로 압축한
폴더. 원본 산출물은 그대로 `../docs/`, `../outputs/`에 보존되어 있다.

본 폴더는 2026-04-30 개인 미팅(`thesis/meeting_stt/260430_personal_meeting.txt`)
에서 받은 피드백을 항목 단위로 추적하여, 어느 결과가 어느 피드백에 답하는지
명시하도록 구성했다.

## 읽는 순서

1. **`00_meeting_brief.md`** — 미팅 시작 5분 오프닝.
2. **`01_one_pager.md`** — 한 페이지 핵심 수치 + 결정.
3. **`02_rolling_results.md`** — Step 04 + 확장 윈도우 상세.
4. **`03_discussion_points.md`** — 미팅에서 결정 받아야 할 8개 항목.
5. **`04_anticipated_qa.md`** — 교수가 미팅에서 던질 가능성 있는 질문 +
   사전 답변(target leakage, 시즈널×코로나 교란 분리 등).
6. **`05_feedback_traceback.md`** — 04-30 미팅 전사의 모든 피드백 항목과
   현재 자료 매핑.

## 본 폴더가 다루는 범위

- **포함**: Step 04(시즌 정렬 baseline 평가) + Step 05(A/B/C/D 메인 모델)
  결과 정리, 윈도우 길이 정착점, target-leakage 검증, 보류 항목 nuance.
- **제외(보류 항목 — 04-30 미팅 결정)**: LEVI / 도시경제 활력 지수 /
  EWS 조기 쇠퇴 경보 / 외부 공공 데이터 5종 / 5월 8일 학과 행정.
  단, 보류 사유와 future-work 가치는 `03_discussion_points.md` D7에 정리.

## 참조 원본

- `../README.md` — 폴더 전체 설명
- `../docs/260430_claude_design.md` — 설계 문서
- `../docs/260430_claude_rolling_results.md` — Step 04 원본 상세
- `../docs/260430_claude_main_model_results.md` — Step 05 원본 상세
- `../docs/260430_claude_summary.md` — 종합 한 페이지
- `../outputs/tables/seasonal_results_summary.csv` — rolling raw 수치
- `../outputs/figures/heatmap_*.png` — 시즌 heatmap 12종
- `../src/step05_train_main_model.py` — A/B/C/D 학습 (cluster/CP는
  `panel.segment == "feature"`에서만 계산: line 166)
