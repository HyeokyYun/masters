# New Volatility and Competition in Forecasting

## 1. 질문

- 최근에 새로 정의한 detrended volatility가 forecasting에도 실제로 도움이 되는가?
- 상권 밀집도/경쟁강도는 forecasting에서 추가 설명력을 주는가?

## 2. 실험 설계

- 초기 30주 표본 고정
- `core_existing`를 기준으로 삼고 새 변수만 추가
- 새 volatility는 `vol_resid_rolling13` 개념을 초기 30주에 맞춰 다시 계산한 `vol_resid_rolling13_30w` 사용
- competition은 동/구 수준 동일업종 점유율과 개수로 구성

## 3. 분류 예측 결과

- `core_existing`: accuracy `0.6386`, weighted F1 `0.6394`, core 대비 F1 변화 `+0.0000`
- `core_plus_new_volatility`: accuracy `0.6388`, weighted F1 `0.6394`, core 대비 F1 변화 `+0.0000`
- `core_plus_competition`: accuracy `0.6445`, weighted F1 `0.6451`, core 대비 F1 변화 `+0.0057`
- `core_plus_new_volatility_and_competition`: accuracy `0.6438`, weighted F1 `0.6446`, core 대비 F1 변화 `+0.0052`

## 4. 회귀 예측 결과

- `core_existing`: R2 `0.8977`, RMSE `1,650,824`, core 대비 R2 변화 `+0.0000`
- `core_plus_new_volatility`: R2 `0.8972`, RMSE `1,654,649`, core 대비 R2 변화 `-0.0005`
- `core_plus_competition`: R2 `0.8966`, RMSE `1,659,388`, core 대비 R2 변화 `-0.0011`
- `core_plus_new_volatility_and_competition`: R2 `0.8982`, RMSE `1,647,157`, core 대비 R2 변화 `+0.0005`

## 5. 해석

- 새 detrended volatility가 core 대비 꾸준히 성능을 올리면 forecasting에서도 의미가 있다고 본다.
- competition block이 별 이득이 없으면, 경쟁강도는 cross-sectional 설명에는 유용해도 현재 forecasting에는 한계가 있다고 해석한다.
- 둘 다 함께 넣었을 때만 오르면 단독효과보다 결합효과로 해석한다.