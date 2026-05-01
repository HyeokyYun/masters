# 통합 색인 — 계절성 보정 점포 생애주기 예측 논문

상태: 260430 미팅 이후 학위논문용 범위 재설정 초안

## 가제

카드거래 데이터 기반 소상공인 점포 생애주기 조기 예측 연구: 서울시 외식업 점포의 계절성 보정 검증

## 한 문장 논지

서울시 외식업 점포의 초기 카드거래 패턴은 이후 성장, 유지, 하락 상태를 예측하는 데 유의미한 정보를 제공하며, 이 예측 신호는 같은 월에 시작하는 feature window와 target window를 비교하는 계절성 보정 rolling-window 검증에서도 완전히 사라지지 않는다.

## 연구질문

RQ1. 초기 영업 기간의 거래 패턴은 이후 점포 생애주기 상태를 얼마나 예측할 수 있는가?

RQ2. 관측 가능한 초기 기간이 길어질수록 Growth, Stable, Decline 예측 성능은 어떻게 달라지는가?

RQ3. 기존 late-window outcome 정의가 계절성을 반영했을 가능성을 통제해도 조기 예측 신호는 유지되는가?

RQ4. cluster, change-point 등 trajectory representation은 기본 거래 feature 대비 예측 성능을 개선하는가?

## 장별 구성

1. [초록](ch0_abstract.md)
2. [서론](ch1_introduction.md)
3. [선행연구](ch2_literature.md)
4. [데이터](ch3_data.md)
5. [방법론](ch4_methodology.md)
6. [결과](ch5_results.md)
7. [토의](ch6_discussion.md)
8. [결론](ch7_conclusion.md)
9. [참고문헌](references.md)

## v3에서 v4로 줄인 범위

| 항목 | v3 | v4 |
|---|---|---|
| 중심 서사 | 6대 기여를 포함한 DSR형 통합 논문 | 점포 생애주기 조기 예측 |
| 핵심 검증 | hybrid, EWS, LEVI, Golden Cross, survival 등 병렬 제시 | 예측 성능 + 계절성 보정 rolling 검증 |
| LEVI | 주요 기여 중 하나 | 후속 연구 또는 부록성 논의 |
| EWS | decision-support artifact | 응용 가능성 논의 |
| Golden Cross | 인과/메커니즘 분석 | 보조 메커니즘 |
| 방어 포인트 | 넓은 기여의 완결성 | 계절성 우려를 반영한 방법론적 정합성 |

## 현재 핵심 수치

| 구분 | 수치 | 해석 |
|---|---:|---|
| 점포 수 | 59,089 | `original_data/meta.csv` 기준 |
| 관측 기간 | 2021-01 ~ 2023-08 | 주간 카드거래 패널 |
| 기존 baseline Macro-F1 | 0.548 | `top_tier` 기본 예측 결과 |
| 기존 hybrid Macro-F1 | 0.639 | trajectory/change-point representation 포함 결과 |
| 기존 hybrid AUC | 0.824 | 다중분류 one-vs-rest 기준 |
| 계절성 보정 best Macro-F1 | 0.509 | 260430 rolling-window robustness |
| 계절성 보정 best AUC | 0.722 | `y2021_m09_w20_lag1y` |
| 계절성 보정 best Decline recall | 0.663 | 하락 점포 조기 포착 가능성 |

## 본문 작성 원칙

1. 학위논문 본문은 store-level lifecycle prediction에 집중한다.
2. 계절성 문제는 약점이 아니라 방법론을 개선한 핵심 robustness로 쓴다.
3. LEVI/EWS는 “쓸모 있음”과 “학문적 중심 기여”를 구분해 낮춘다.
4. 예측 시점 이후 정보를 feature로 사용하지 않았는지 계속 확인한다.
5. 정책적 함의는 가능성으로만 쓰고, 실제 개입효과를 주장하지 않는다.

