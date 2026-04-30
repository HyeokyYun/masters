# Forecast Feature Ablation

## 1. 왜 이 실험을 했는가

- 관측 주가 길어지면 성능이 올라가는 것은 자연스러운 현상이다.
- 그래서 같은 `초기 30주` 조건에서 feature block을 하나씩 추가하며 성능이 얼마나 늘어나는지 확인했다.
- 이 실험은 `시간이 길어져서 좋아진 것`과 `우리 feature가 실제로 도움이 된 것`을 구분하기 위한 것이다.

## 2. 분류 예측에서 무엇이 도움이 되었는가

- `level_only`: accuracy `0.5832`, weighted F1 `0.5620`, 직전 대비 F1 변화 `NA`
- `plus_trend_volatility`: accuracy `0.6529`, weighted F1 `0.6333`, 직전 대비 F1 변화 `+0.0714`
- `plus_customer_behavior`: accuracy `0.6733`, weighted F1 `0.6540`, 직전 대비 F1 변화 `+0.0207`
- `plus_local_context`: accuracy `0.6885`, weighted F1 `0.6692`, 직전 대비 F1 변화 `+0.0152`
- `plus_cluster`: accuracy `0.6883`, weighted F1 `0.6690`, 직전 대비 F1 변화 `-0.0002`

## 3. 미래 매출 회귀에서 무엇이 도움이 되었는가

- `level_only`: R2 `0.8753`, RMSE `1,822,517`, 직전 대비 R2 변화 `NA`
- `plus_trend_volatility`: R2 `0.8974`, RMSE `1,653,453`, 직전 대비 R2 변화 `+0.0221`
- `plus_customer_behavior`: R2 `0.9013`, RMSE `1,621,600`, 직전 대비 R2 변화 `+0.0039`
- `plus_local_context`: R2 `0.9026`, RMSE `1,610,918`, 직전 대비 R2 변화 `+0.0013`
- `plus_cluster`: R2 `0.9021`, RMSE `1,614,884`, 직전 대비 R2 변화 `-0.0005`

## 4. 발표용 해석

- `level_only`는 단순 현재 수준 정보만 쓴 경우다.
- `plus_trend_volatility`에서 성능이 오르면, 단순 수준보다 추세/변동성이 추가로 의미 있다는 뜻이다.
- `plus_customer_behavior`에서 더 오르면, 신규고객·주말 비중·결제/배달 구조가 추가 정보를 준다는 뜻이다.
- `plus_local_context`와 `plus_cluster`의 추가 이득은 상권/맥락 변수와 초기 패턴 군집 정보의 한계효과를 보여준다.