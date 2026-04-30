# Forecast Baseline Comparison

## 1. 분류형 조기예측: majority baseline 대비

- `W=20주`: baseline 정확도 `0.4601`, 현재 최고모델 `GBM` 정확도 `0.5432`. 정확도 개선은 `8.31%p`, 오류율 감소는 `15.39%`.
- `W=30주`: baseline 정확도 `0.4568`, 현재 최고모델 `GBM` 정확도 `0.5726`. 정확도 개선은 `11.58%p`, 오류율 감소는 `21.31%`.
- `W=40주`: baseline 정확도 `0.4506`, 현재 최고모델 `GBM` 정확도 `0.6007`. 정확도 개선은 `15.01%p`, 오류율 감소는 `27.32%`.
- `W=50주`: baseline 정확도 `0.4472`, 현재 최고모델 `GBM` 정확도 `0.6310`. 정확도 개선은 `18.38%p`, 오류율 감소는 `33.24%`.

## 2. 연속형 미래매출 예측: naive / seasonal naive 대비

- `NaiveGlobalMeanCV` 대비 현재 최고모델 `RandomForestRegressor_same_subset`은 MAE를 `73.27%`, RMSE를 `62.66%` 줄였고, R2는 `-0.0000`에서 `0.8606`로 올랐다.
- `NaiveLastValue` 대비 현재 최고모델 `RandomForestRegressor_same_subset`은 MAE를 `20.50%`, RMSE를 `42.69%` 줄였고, R2는 `0.5755`에서 `0.8606`로 올랐다.
- `NaiveEarlyMean` 대비 현재 최고모델 `RandomForestRegressor_same_subset`은 MAE를 `20.44%`, RMSE를 `13.63%` 줄였고, R2는 `0.8131`에서 `0.8606`로 올랐다.
- `NaiveRecent4Mean` 대비 현재 최고모델 `RandomForestRegressor_same_subset`은 MAE를 `6.83%`, RMSE를 `11.58%` 줄였고, R2는 `0.8217`에서 `0.8606`로 올랐다.
- `SeasonalNaive13` 대비 현재 최고모델 `RandomForestRegressor_same_subset`은 MAE를 `11.46%`, RMSE를 `7.25%` 줄였고, R2는 `0.8379`에서 `0.8606`로 올랐다.

## 3. 발표용 해석

- 분류형 조기예측은 단순 다수 클래스 찍기보다 의미 있게 낫다.
- 연속형 미래매출 예측은 단순 최근값/초기평균/13주 seasonal naive보다도 개선 폭이 크다.
- 따라서 현재 모델은 단순 benchmark를 이기지 못하는 수준이 아니라, 실제로 baseline 대비 유의한 개선을 보인다고 설명할 수 있다.