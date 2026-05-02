# 4. 방법론

## 4.1 연구 설계

본 연구는 점포의 초기 거래 패턴을 사용하여 이후 생애주기 상태를 예측하는 supervised classification 문제로 구성된다. 각 점포에 대해 feature window와 target window를 정의하고, feature window에서 추출한 변수로 target window의 Growth, Stable, Decline 상태를 예측한다.

분석은 두 단계로 구성된다. 첫째, 기존 full-window 예측 결과를 통해 초기 거래 패턴과 trajectory representation의 예측력을 확인한다. 둘째, 계절성 보정 rolling-window 검증을 통해 예측 신호가 calendar timing에 의해 만들어진 것인지 점검한다.

## 4.2 Feature Window

feature window는 예측에 사용되는 초기 관측 기간이다. 짧은 window는 더 빠른 판단을 가능하게 하지만 정보량이 적고, 긴 window는 더 많은 정보를 제공하지만 조기 개입 가능성을 낮춘다. 본 연구는 다양한 window length를 비교하여 observation length와 예측 성능 사이의 trade-off를 분석한다.

feature는 매출 수준, 거래량, 고객 수, 추세, 변동성, trajectory representation으로 구성된다. 모든 feature는 target window 이전의 정보만 사용해야 한다. 이 원칙은 특히 cluster와 change-point feature를 사용할 때 중요하다. 예측 시점 이후의 변화를 반영한 feature는 모델 성능을 과대평가할 수 있기 때문이다.

## 4.3 Target Window와 Labeling

target window는 예측하고자 하는 이후 기간이다. 기본 label은 target window의 거래 변화가 기준 대비 상승하면 Growth, 큰 변화가 없으면 Stable, 하락하면 Decline으로 정의된다. label 기준은 본문에서 사용한 threshold와 slope 계산식을 명시해야 한다.

기존 분석에서는 마지막 30주를 target window로 두는 방식이 사용되었다. 이 방식은 전체 관측기간의 후반 상태를 예측한다는 점에서 직관적이지만, 관측 종료 시점이 특정 계절에 위치한다는 한계가 있다. 따라서 본 연구는 이를 exploratory baseline으로 다루고, 최종 해석에서는 계절성 보정 rolling-window 결과를 함께 제시한다.

## 4.4 계절성 보정 Rolling-Window 검증

계절성 보정 검증의 목적은 feature window와 target window의 calendar timing을 맞추는 것이다. 예를 들어 2021년 1월부터 시작하는 12주 feature window는 2022년 1월부터 시작하는 12주 target window와 비교한다. 같은 방식으로 2월 시작, 3월 시작, ..., 12월 시작 window를 구성한다. window length는 4주, 8주, 12주, 16주, 20주, 30주 등 여러 길이를 비교할 수 있다.

이 설계는 다음 질문에 답한다.

> 동일한 계절 구간끼리 비교해도 초기 거래 패턴은 이후 Growth, Stable, Decline 상태를 예측하는가?

260430 분석에서는 136개의 유효 window specification을 평가하였다. 각 specification에 대해 balanced logistic regression과 5-fold cross-validation을 사용하여 Macro-F1, Weighted-F1, one-vs-rest AUC, class별 recall을 계산하였다. 이 결과는 기존 full-window 모델을 대체하는 것이 아니라, 계절성 우려에 대한 robustness evidence로 해석한다.

## 4.5 Strict Out-of-Time Rolling 검증

추가로 본 연구는 더 보수적인 strict out-of-time rolling 검증을 수행한다. 이 검증은 같은 calendar window를 유지하되, 학습과 테스트를 서로 다른 미래연도로 분리한다.

| 구분 | 학습 | 테스트 |
|---|---|---|
| Strict rolling | 2021년 m월부터 k주 feature -> 2022년 m월부터 k주 label | 2022년 m월부터 k주 feature -> 2023년 m월부터 k주 label |

이 검증은 기존 seasonal CV보다 더 어렵다. Seasonal CV는 같은 specification 안에서 점포를 나누어 cross-validation을 수행하지만, strict rolling은 `2021 -> 2022` 관계가 `2022 -> 2023`으로 이전되는지를 평가한다. 따라서 strict rolling 성능은 본 연구의 conservative lower-bound evidence로 해석한다.

## 4.6 예측 모델과 평가 지표

주요 평가지표는 Macro-F1, Weighted-F1, AUC, class별 recall이다. Macro-F1은 Growth, Stable, Decline 세 class의 성능을 동일한 가중치로 평가하므로 class imbalance 상황에서 중요하다. Decline recall은 하락 점포를 얼마나 놓치지 않는지 보여주므로 조기진단 관점에서 별도로 보고한다.

기본 모델은 거래 feature만 사용한 분류 모델이다. 확장 모델은 cluster와 change-point 등 trajectory representation을 추가한다. 기존 `top_tier` 결과에서는 hybrid representation이 기본 모델보다 높은 Macro-F1과 AUC를 보였다. 다만 이 결과를 본문에 사용할 때에는 feature 계산 시점이 예측 시점 이전으로 제한되었는지 확인하고 명시해야 한다.

## 4.7 해석 전략

본 연구의 해석은 네 층으로 구성한다. 첫째, full-window 분석을 통해 초기 거래 패턴의 예측 가능성을 제시한다. 둘째, observation window가 길어질수록 특히 Decline 예측 성능이 개선되는지 검토한다. 셋째, 계절성 보정 rolling-window 결과를 통해 예측 신호가 단순한 seasonality artifact가 아님을 보인다. 넷째, strict out-of-time rolling 검증을 통해 이 신호가 미래연도 이전에서 얼마나 약화되는지 평가한다.

이 순서는 방어 가능성이 높다. 먼저 예측 문제가 성립함을 보이고, 그 다음 예측 timing의 trade-off를 설명하며, 마지막으로 미팅에서 제기된 가장 중요한 방법론적 우려를 단계적으로 검증하기 때문이다.
