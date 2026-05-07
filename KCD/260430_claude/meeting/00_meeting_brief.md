# 개인 미팅 브리프 — Rolling 결과 정리 (2026-05-07)

> 본 폴더는 04-30 개인 미팅 피드백에 대한 후속 자료다. 메인 트랙은
> "feature window와 target window를 같은 캘린더 월로 정렬한 롤링 분석"이다.
> Step 04(146 panel × RF/LGB)가 핵심, Step 05(7 panel A/B/C/D)는 후속.

## 한 줄 요약 (먼저 말할 문장)

**"교수님 요청대로 캘린더 월 정렬 롤링을 146개 panel(시작월×윈도우 길이
1·2·3·4·6·7개월×offset 1·2)로 다 돌렸습니다. 시작월 효과 진폭이 윈도우
길이 효과의 약 5배라서 시즈널 confound가 라벨/모델 난이도를 좌우한다는
것을 확인했고, 시즌 정렬 후에는 cluster+CP의 추가 향상이 평균 +0.002
macro-F1로 거의 사라집니다."**

## 5분 안에 말할 5가지

1. **요청 그대로 구현** — 1월 시작 → 1월 정렬, 2월 시작 → 2월 정렬, …,
   각 시작월에 1/2/3/4/6/7-month 윈도우. 168 candidate 중 데이터 범위 안
   146 panel.
2. **시작월 효과 ≫ 윈도우 길이 효과** — RF·off=1·w=3 평균에서 시작월
   진폭 0.0682 vs 윈도우 진폭 0.0143 → **5배 차이**. 시즈널리티가 일순위 신호.
3. **2023-08 컷오프 직전 panel은 sanity로만** — `sm07/sm08+off2`는 라벨이
   인공적으로 Decline 0.51–0.68. 결론 근거에서 분리.
4. **2022 시작도 봤다 (코로나 잔여)** — 2021 vs 2022 평균 macro-F1 차이
   +0.0114로 정확도에 결정적이지 않음. 미팅 우려와 결과가 다름.
5. **시즌 정렬 후 hybrid contribution이 약화** — Step 05에서 D−A 평균
   +0.002 macro-F1, 7개 중 1개만 5% 유의(`sy2022_sm03`). 논문 1번 framing
   재조정 필요.

## 미팅에서 받아야 할 결정 (큰 줄기 4개)

- **D1 메인 panel 7개 유지 + 80 panel D−A delta heatmap 추가?** (현재 7개만)
- **D2 2023-08 직전 panel을 본문 제외 / 부록 sanity로 분리?**
- **D3 논문 1번 framing을 (a) 조건부 contribution / (b) trajectory 정성 /
  (c) 시즈널 confound 노출 자체 — 어느 쪽?**
- **D4 w=3개월 정착점을 본문에 명시?** (w 4·6·7로 늘려도 평탄)

(상세 8개 결정 + 보류 항목 nuance: `03_discussion_points.md`)

## 화면 공유용 그림 (순서)

1. `../outputs/figures/heatmap_macro_f1_rf_off1.png` — 시작연도×시작월 macro-F1.
2. `../outputs/figures/heatmap_decline_recall_rf_off1.png` — Decline recall.
3. `../outputs/figures/yearly_compare_2021_vs_2022.png` — 2021 vs 2022 비교.
4. `../outputs/figures/main_model_compare_bars.png` — Step 05 A/B/C/D.
5. `../outputs/figures/main_model_delta.png` — Step 05 D−A delta.

## 미팅에서 **꺼내지 말 것** (04-30 결정 유지)

- LEVI / EWS / 외부 공공 데이터 5종 / 도시경제 활력 지수.
- 기존 `top_tier`의 hybrid D ≫ A (~0.05) 숫자를 시즈널 정렬 없이 인용.
- 5/8 학과 커미티 제출 — 별도 행정.

## 교수가 던질 가능성이 있는 질문 (사전 답변 준비)

- "cluster/changepoint는 앞 정보로만 만들어졌나?" → **예. feature 구간에서만**
  (`step05_train_main_model.py:166`).
- "코로나 vs 시즈널 confound 분리됐나?" → 시작연도 진폭(0.0114) ≪ 시작월
  진폭(0.0682). 시즈널이 지배.
- "8월 직전이 이상한 거 알고 있나?" → 알고 있고 sanity로만 표시.

(자세한 답변 노트: `04_anticipated_qa.md`)

## 참조

- 한 페이지 요약: `01_one_pager.md`
- 상세 rolling 결과: `02_rolling_results.md`
- 결정 항목: `03_discussion_points.md`
- 사전 Q&A 노트: `04_anticipated_qa.md`
- 04-30 피드백 추적표: `05_feedback_traceback.md`
