# Strict Rolling Validation 논문용 해석

작성일: 2026-05-01

## 검증 목적

기존 `260430` seasonal rolling 분석은 feature window와 target window를 같은 calendar period로 맞추었다. 그러나 각 specification 안에서 점포 단위 5-fold cross-validation을 했기 때문에, 완전히 미래 연도로 넘어가는 out-of-time 검증은 아니었다.

이번 strict rolling validation은 더 보수적인 검증이다.

| 구분 | 학습 | 테스트 |
|---|---|---|
| strict rolling | 2021년 m월부터 k주 feature -> 2022년 m월부터 k주 label | 2022년 m월부터 k주 feature -> 2023년 m월부터 k주 label |

즉, 같은 시작월과 같은 관측기간 길이를 유지한 채, `2021 -> 2022` 관계가 `2022 -> 2023`으로 이전되는지를 본다.

## 핵심 결과

| 모델 | Macro-F1 | Weighted-F1 | AUC | Decline recall |
|---|---:|---:|---:|---:|
| Majority baseline | 0.221 | 0.384 | - | 0.000 |
| Strict rolling logistic | 0.407 | 0.508 | 0.650 | 0.357 |

가장 높은 Macro-F1은 `5월 시작, 12주 window`에서 나타났다.

| 시작월 | window | Macro-F1 | AUC | Decline recall |
|---:|---:|---:|---:|---:|
| 5월 | 12주 | 0.478 | 0.702 | 0.308 |
| 6월 | 4주 | 0.474 | 0.698 | 0.408 |
| 5월 | 8주 | 0.460 | 0.683 | 0.388 |
| 5월 | 4주 | 0.459 | 0.677 | 0.442 |
| 1월 | 4주 | 0.458 | 0.672 | 0.416 |

Decline recall만 보면 1월 시작 window가 높다.

| 시작월 | window | Macro-F1 | AUC | Decline recall |
|---:|---:|---:|---:|---:|
| 1월 | 12주 | 0.341 | 0.689 | 0.776 |
| 1월 | 8주 | 0.349 | 0.680 | 0.683 |
| 1월 | 16주 | 0.409 | 0.688 | 0.631 |

다만 이 경우 Macro-F1과 Decline F1은 낮다. 따라서 1월 window는 하락 점포를 넓게 잡는 경향이 있지만, 전체 class balance 관점에서는 좋은 모델이라고 말하기 어렵다.

## 기존 결과와 비교

| 분석 | 평가 방식 | Macro-F1 | 해석 |
|---|---|---:|---|
| 기존 `top_tier` baseline | within-sample CV 계열 | 0.548 | seasonality와 future-year transfer를 엄격히 분리하지 않음 |
| 기존 `top_tier` hybrid | within-sample CV 계열 | 0.639 | 성능 상한선에 가까운 exploratory result |
| `260430` seasonal CV best | 같은 calendar window 안에서 점포 단위 CV | 0.509 | seasonality는 맞췄지만 test year를 완전히 분리하지 않음 |
| strict rolling best | 2021->2022 학습, 2022->2023 테스트 | 0.478 | 가장 보수적인 out-of-time 검증 |
| strict rolling 평균 | 32개 조합 평균 | 0.407 | 미래연도 이전 시 성능 약화 |

## 중요한 발견

### 1. 예측력은 올라가지 않았다

strict rolling을 적용하면 성능은 상승하지 않는다. 오히려 기존 seasonal CV보다 낮아진다. 이는 자연스러운 결과다. 학습과 테스트가 서로 다른 미래 calendar year로 분리되기 때문에, 같은 specification 안에서 점포를 섞어 cross-validation하는 것보다 훨씬 어려운 검증이다.

따라서 논문에서 “rolling을 하니 성능이 좋아졌다”고 쓰면 안 된다.

### 2. 그래도 majority baseline보다는 명확히 낫다

Strict rolling logistic의 평균 Macro-F1은 0.407로 majority baseline 0.221보다 높다. Decline recall도 baseline은 0이지만 strict rolling은 평균 0.357이다.

논문에서는 다음과 같이 쓰는 것이 안전하다.

> 계절성과 미래연도 이전을 동시에 통제하면 예측 성능은 약화되지만, 모델은 majority baseline보다 높은 성능을 보이며 하락 점포에 대한 일정 수준의 조기 포착 능력을 유지한다.

### 3. 긴 window가 항상 더 좋은 것은 아니다

기존 seasonal CV에서는 window가 길어질수록 Decline recall이 좋아지는 경향이 있었다. 그러나 strict rolling에서는 이 패턴이 약해진다.

| window | 평균 Macro-F1 | 평균 AUC | 평균 Decline recall |
|---:|---:|---:|---:|
| 4주 | 0.424 | 0.663 | 0.365 |
| 8주 | 0.410 | 0.657 | 0.381 |
| 12주 | 0.397 | 0.650 | 0.367 |
| 16주 | 0.404 | 0.652 | 0.353 |
| 20주 | 0.403 | 0.641 | 0.329 |
| 30주 | 0.366 | 0.591 | 0.281 |

이 결과는 중요한 해석을 만든다. 긴 관측기간은 같은 연도 안의 CV에서는 정보를 늘려 성능을 높일 수 있지만, 다음 연도로 이전할 때는 기간이 길어질수록 macro shock, 코로나 회복, 물가, 소비패턴 변화 같은 연도별 차이를 더 많이 포함할 수 있다.

따라서 본 논문에서는 “더 오래 보면 무조건 더 잘 예측한다”보다 다음 표현이 안전하다.

> 관측기간 확대는 within-period 예측에서는 유리하지만, calendar year를 넘어서는 strict rolling 검증에서는 일반화 성능을 반드시 개선하지 않는다. 이는 점포 생애주기 예측에서 관측기간 길이와 시간적 이전가능성 사이의 trade-off가 존재함을 시사한다.

### 4. 5월 시작 window가 전체 성능에서 가장 안정적이다

Macro-F1 기준으로는 5월 시작 window가 가장 좋다. 그러나 이를 과도하게 해석해서는 안 된다. 현재 데이터가 2021-2023이라는 특수한 기간이고, 2023년 8월까지만 관측되기 때문에 하반기 긴 window 조합은 평가할 수 없다.

논문에서는 “5월이 최적”이라고 주장하기보다, “성능이 시작월에 민감하다”고 쓰는 것이 안전하다.

## 논문 반영 방향

본문 결과 장에서는 다음 순서가 좋다.

1. 기존 full-window / top_tier 결과: 초기 거래패턴에 예측 신호가 있음을 보여주는 baseline.
2. `260430` seasonal CV: 같은 calendar period로 맞춰도 신호가 남음을 보여주는 seasonality robustness.
3. strict rolling validation: 미래 연도로 완전히 넘기면 성능이 낮아지지만 baseline보다 우수함을 보여주는 conservative validation.

최종 주장은 다음 수준으로 제한한다.

> 본 연구의 초기 거래패턴 기반 예측은 계절성 통제 전에는 비교적 높은 성능을 보였고, calendar-matched 검증에서도 일정 수준의 예측 신호를 유지했다. 가장 보수적인 strict out-of-time rolling 검증에서는 성능이 약화되었으나 majority baseline을 상회했으며, 이는 예측 신호가 존재하지만 연도 간 이전가능성에는 한계가 있음을 보여준다.

## 방어용 한 문장

> 이 결과는 기존 모델의 성능을 더 높이는 발견이라기보다, 기존 결과가 어느 정도 seasonality와 연도별 환경 변화에 민감한지를 드러내는 robustness evidence입니다. 따라서 논문에서는 높은 성능을 과장하지 않고, 엄격한 미래연도 검증에서도 baseline을 넘는 신호가 남는다는 점을 중심으로 쓰는 것이 맞습니다.

