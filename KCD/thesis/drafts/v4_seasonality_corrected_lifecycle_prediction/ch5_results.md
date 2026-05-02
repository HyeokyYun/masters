# 5. 결과

## 5.1 기술통계와 label 분포

본 장에서는 먼저 분석 표본의 기본 분포를 보고한다. 전체 원자료에는 서울시 외식업 점포 59,089개가 포함되어 있으며, 관측 기간은 2021년 1월부터 2023년 8월까지이다. 예측 분석에 사용되는 유효 표본은 feature window와 target window를 모두 충족해야 하므로 specification별로 달라진다.

본문 표에는 다음 항목을 포함한다.

| 표 | 내용 | 후보 파일 |
|---|---|---|
| Table 5.1 | 전체 점포 수, 관측 주차, 업종/지역 분포 | `original_data/meta.csv` |
| Table 5.2 | Growth/Stable/Decline label 분포 | `top_tier/outputs/`, `260430/outputs/tables/seasonal_label_distribution.csv` |
| Table 5.3 | window specification별 유효 표본 수 | `260430/outputs/tables/seasonal_window_inventory.csv` |

## 5.2 초기 관측 기간과 예측 성능

기존 분석에서는 초기 관측 기간이 길어질수록 예측 성능이 전반적으로 개선되는 경향이 확인되었다. 특히 Decline class의 recall 개선이 중요하다. 이는 하락 점포가 초기에 완전히 드러나지 않더라도, 일정 기간의 거래 흐름을 관측하면 이후 하락 상태를 더 잘 포착할 수 있음을 의미한다.

이 결과는 조기 예측의 trade-off를 보여준다. 너무 이른 시점의 예측은 intervention timing 측면에서 유리하지만 정보가 부족하고, 더 긴 관측은 성능을 높이지만 대응 시점을 늦춘다. 본문에서는 observation window별 Macro-F1, class별 recall, 특히 Decline recall을 함께 제시한다.

## 5.3 Hybrid Representation 결과

기존 `top_tier` 분석에서는 기본 거래 feature만 사용한 모델 대비, trajectory cluster와 change-point feature를 포함한 hybrid representation이 더 높은 성능을 보였다. 현재 정리된 기준 수치는 다음과 같다.

| 모델 | Macro-F1 | AUC |
|---|---:|---:|
| 기본 예측 모델 | 0.548 | 0.736 |
| Hybrid representation | 0.639 | 0.824 |

이 결과는 점포의 평균 매출 수준뿐 아니라 거래 궤적의 형태와 변화 시점이 이후 생애주기 상태를 설명하는 데 중요할 수 있음을 시사한다. 다만 본문에서는 이 feature들이 예측 시점 이전 자료로만 계산되었는지를 확인한 뒤 제시해야 한다. 예측 이후 정보를 사용한 representation은 조기 예측 근거로 사용할 수 없다.

## 5.4 계절성 보정 Rolling-Window 결과

260430 분석에서는 feature window와 target window가 같은 calendar month에 시작하도록 맞춘 rolling-window robustness check를 수행하였다. 총 136개의 유효 window specification이 평가되었고, 각 specification에 대해 5-fold cross-validation 결과가 산출되었다.

가장 높은 Macro-F1을 보인 specification은 `y2021_m09_w20_lag1y`였다. 주요 성능은 다음과 같다.

| specification | N | Macro-F1 | Weighted-F1 | AUC | Growth recall | Stable recall | Decline recall |
|---|---:|---:|---:|---:|---:|---:|---:|
| y2021_m09_w20_lag1y | 34,221 | 0.509 | 0.555 | 0.722 | 0.614 | 0.390 | 0.663 |

계절성 보정 결과의 성능은 full-window hybrid 결과보다 낮다. 그러나 이는 예상 가능한 결과이다. rolling-window 검증은 계절성을 통제하기 위해 분석 window를 제한하고, 더 단순한 모델 구조를 사용했기 때문이다. 중요한 점은 성능이 완전히 사라지지 않았다는 것이다. 이는 초기 거래 패턴이 단순히 특정 계절 효과만을 반영한 것이 아니라, 이후 상태와 관련된 정보를 포함한다는 robustness evidence로 해석할 수 있다.

## 5.5 Strict Out-of-Time Rolling 결과

추가 검증에서는 `2021년 m월부터 k주 feature -> 2022년 m월부터 k주 label` 관계로 학습한 뒤, `2022년 m월부터 k주 feature -> 2023년 m월부터 k주 label` 관계에 테스트하였다. 이는 같은 calendar period를 유지하면서도 테스트 연도를 완전히 분리하는 가장 보수적인 검증이다.

평균 성능은 다음과 같다.

| 모델 | Macro-F1 | Weighted-F1 | AUC | Decline recall |
|---|---:|---:|---:|---:|
| Majority baseline | 0.221 | 0.384 | - | 0.000 |
| Strict rolling logistic | 0.407 | 0.508 | 0.650 | 0.357 |

최고 Macro-F1은 5월 시작 12주 window에서 나타났으며, Macro-F1 0.478, AUC 0.702, Decline recall 0.308을 보였다. Decline recall만 기준으로 보면 1월 시작 12주 window가 0.776으로 가장 높았지만, 이 경우 Macro-F1은 0.341로 낮다. 따라서 하락 점포를 넓게 포착하는 window와 전체 class balance가 좋은 window는 동일하지 않다.

Strict rolling 결과는 예측 성능이 더 올라갔다는 근거가 아니다. 오히려 계절성과 미래연도 이전을 동시에 통제하면 성능이 약화됨을 보여준다. 그러나 majority baseline보다 높은 Macro-F1과 AUC를 보이며, Decline recall도 0이 아닌 수준으로 유지된다. 따라서 논문에서는 다음과 같이 해석한다.

> 엄격한 미래연도 검증에서는 예측 성능이 낮아지지만, 초기 거래패턴은 majority baseline을 상회하는 정보를 제공한다. 이는 생애주기 예측 신호가 존재하되, 연도 간 일반화에는 한계가 있음을 의미한다.

또한 strict rolling에서는 window가 길수록 성능이 반드시 좋아지지 않았다. 30주 window의 평균 Macro-F1은 0.366으로 가장 낮았다. 이는 긴 window가 within-period CV에서는 정보량을 늘리지만, 미래연도 이전에서는 macro shock, 코로나 회복, 물가, 소비패턴 변화 같은 연도별 차이를 더 많이 포함할 수 있음을 시사한다.

## 5.6 Decline 예측의 의미

Decline class는 실무적 중요성이 크다. 하락 가능성이 높은 점포를 조기에 포착할 수 있다면, 금융지원, 컨설팅, 임대료 협상, 상권 정책 등 다양한 대응의 우선순위를 정하는 데 활용될 수 있다. 계절성 보정 결과에서 최고 specification의 Decline recall은 0.663이었다. 이는 같은 계절 구간 비교에서도 하락 점포의 상당 부분을 조기에 포착할 수 있음을 보여준다.

다만 recall만으로 모델의 실무적 유용성을 판단해서는 안 된다. 높은 recall은 false positive 증가와 함께 발생할 수 있다. 따라서 본 논문에서는 EWS threshold 최적화 자체를 중심 결과로 삼기보다, Decline recall을 생애주기 예측 신호의 중요한 class-specific evidence로 제시한다.

Strict rolling에서도 같은 주의가 필요하다. 1월 window는 Decline recall이 높지만 Macro-F1과 Decline F1이 낮아, 하락 점포를 과도하게 넓게 잡는 경향이 있을 수 있다. 따라서 본문에서는 Decline recall과 Macro-F1을 함께 보고한다.

## 5.7 결과 요약

본 장의 결과는 세 가지로 요약된다.

첫째, 초기 거래 패턴은 이후 Growth, Stable, Decline 상태를 예측하는 데 유의미한 정보를 제공한다.

둘째, trajectory representation을 포함하면 예측 성능이 개선될 수 있다. 이는 점포의 수준 변수뿐 아니라 변화의 형태가 중요함을 시사한다.

셋째, 같은 calendar month끼리 비교하는 rolling-window 검증에서도 예측 신호는 유지된다. 따라서 기존 결과를 계절성 artifact로만 해석하기는 어렵다.

넷째, strict out-of-time rolling에서는 성능이 더 낮아지지만 majority baseline을 상회한다. 이는 예측 신호가 존재하지만, 연도 간 이전가능성에는 한계가 있음을 보여준다.
