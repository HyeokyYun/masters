# 미팅 한 페이지 (Rolling 결과)

## 한 줄

시즌 정렬 후 **시작월 효과(0.0682) ≫ 윈도우 길이 효과(0.0143)** —
시즈널리티가 라이프사이클 분류 난이도를 좌우한다는 것을 146개 panel로 확증.
시즌 정렬을 강제하면 cluster+CP의 추가 신호는 평균 +0.002 macro-F1로 사실상 사라짐.

## 무엇을 했나 (04-30 미팅 요청 → 본 결과)

| 04-30 피드백 (전사 라인) | 결과물 |
| --- | --- |
| "feature window와 target window를 같은 캘린더 월로 정렬" (09:01) | 146 panel × RF/LGB 평가 (`seasonal_results_summary.csv`) |
| "롤링 윈도우 — 1월3월, 2월4월, 3월5월, …" (10:39) | start_month 1..12 × window 1·2·3·4·6·7개월 |
| "2022년 1월부터 시작도 봐라" (26:22) | sy2022_sm01..07 panel 전부 포함 |
| "체인지 포인트랑 클러스터는 앞 정보로 알 수 있나?" (17:29) | feature 구간에서만 계산 (step05 line 166) |
| "마지막 거(베이스라인+클러스터+체인지포인트)는 academic" (18:32) | Step 05 A/B/C/D 비교, paired t-test (`main_model_compare.csv`) |

## 핵심 수치 (RF, target_offset=1)

| 비교 | 값 | 함의 |
| --- | --- | --- |
| 시작월 진폭 (w=3 평균, sm10–sm06) | **+0.0682** | 시즌 confound가 일순위 |
| 윈도우 길이 진폭 (w=3 – w=1) | +0.0143 | 윈도우는 부차적 |
| 시작연도 차 (2021–2022) | +0.0114 | 코로나 잔여는 결정적 아님 |
| 확장 윈도우 (w=4) macro-F1 | 0.4963 | w=3 이후 정착 |
| RF vs LGB 평균차 | 0.004 | 모델 선택 무관 |
| Step 05 평균 Δ(D−A) (7 panel) | **+0.0022** | hybrid contribution 약화 |

## 시즈널 confound의 직접 증거

- Q4(10–12월) 시작 panel이 macro-F1 안정 상위. G/S/D 균형이 좋음.
- 7월 시작 panel은 target이 데이터 끝(2023-08)에 닿아 라벨 인공 편중
  (`sy2022_sm07_w3` Decline 0.55).
- 같은 모델·같은 점포에서 라벨링 시점만 바꿔도 macro-F1이 0.43–0.54로 분산.

## 미팅 결론 (말하기 좋은 형태)

> "라벨링 시점을 정렬하면 같은 데이터·같은 모델로도 분류 난이도가
> 0.10 폭으로 흔들린다. 따라서 기존 `top_tier`의 hybrid contribution
> (D ≫ A by ~0.05)은 시즈널 confound를 통제한 뒤 다시 평가해야 하고,
> 정렬 후에는 평균 +0.002 macro-F1로 사실상 사라진다 (Step 05)."

## 다음 결정 한 줄

- **D1**: 메인 panel 7개 유지 + 80 panel D−A delta heatmap 추가? (Y/N)
- **D2**: 2023-08 직전 panel은 부록 sanity로만 분리? (Y/N)
- **D3**: 논문 1번 framing은 (c) "시즈널 confound 노출"로? (Y/N)
- **D4**: w=3 정착점 본문 명시? (Y/N)

(상세 근거 + D5–D8: `03_discussion_points.md`)
