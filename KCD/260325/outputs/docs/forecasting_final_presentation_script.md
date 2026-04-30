# Forecasting 최종 발표 대본

## 1. 먼저 가장 중요한 구분

발표에서 반드시 먼저 말해야 하는 것은 아래 두 가지가 다르다는 점입니다.

1. `설명분석`
   - 어떤 변수가 Growth / Stable / Decline과 더 잘 연결되는가

2. `forecasting`
   - 초기 30주 정보만으로 이후 결과를 얼마나 잘 예측하는가

이 구분이 중요한 이유는,  
`새로 정의한 변동성`은 **설명분석에서는 분명히 더 좋았지만**,  
`forecasting에서는 추가효과가 거의 없었기 때문`입니다.

---

## 2. 새 변동성이 어디에서 좋아졌는가

### 2.1 설명분석에서는 좋아졌습니다

`260325`의 변동성 재정의 실험에서는 기존 평균 기준 CV보다  
`추세조정 잔차 변동성`, 특히 `vol_resid_rolling13`이 더 잘 갈렸습니다.

근거:

- [volatility_metric_screening.csv](/Volumes/SAMSUMG_128/master_graduate/KCD_source_code_from_Yang/26-1/260325/outputs/tables/volatility_metric_screening.csv)
- [volatility_model_fit_comparison.csv](/Volumes/SAMSUMG_128/master_graduate/KCD_source_code_from_Yang/26-1/260325/outputs/tables/volatility_model_fit_comparison.csv)

핵심 수치:

- 추천 변동성: `vol_resid_rolling13`
- baseline pseudo R2: `0.57849`
- adjusted pseudo R2: `0.57878`
- AIC도 `18830.19 → 18817.21`로 개선

즉,  
`Growth/Stable/Decline을 설명하는 다항로짓 모형에서는 새 변동성이 기존 CV보다 더 적절했다`

고 말할 수 있습니다.

### 2.2 forecasting에서는 거의 좋아지지 않았습니다

하지만 `초기 30주 forecasting`에 새 변동성을 직접 넣어보니 결과는 달랐습니다.

근거:

- [forecast_newvol_competition_classification_gain.csv](/Volumes/SAMSUMG_128/master_graduate/KCD_source_code_from_Yang/26-1/260325/outputs/tables/forecast_newvol_competition_classification_gain.csv)
- [forecast_newvol_competition_regression_gain.csv](/Volumes/SAMSUMG_128/master_graduate/KCD_source_code_from_Yang/26-1/260325/outputs/tables/forecast_newvol_competition_regression_gain.csv)

핵심 수치:

- 분류 weighted F1:
  - `core_existing`: `0.63936`
  - `+ new volatility`: `0.63939`
  - 증가폭: `+0.00003`

- 회귀 R2:
  - `core_existing`: `0.89771`
  - `+ new volatility`: `0.89723`
  - 변화폭: `-0.00047`

즉,  
`새 변동성은 설명분석에서는 더 좋았지만, forecasting에서는 기존 core feature 위에 거의 추가 정보를 주지 못했다`

가 현재의 정확한 결론입니다.

---

## 3. 이번 forecasting 파트에서 정확히 무엇을 예측했는가

forecasting에서는 두 가지를 봤습니다.

### 3.1 분류 예측

- 입력: 개업 후 `초기 30주`
- 출력: `life_cycle_category`
  - `rising`
  - `maintaining`
  - `declining`

즉,

`초기 30주만 보고 이후에 상승형, 유지형, 하락형 중 어디로 갈지를 예측`

한 것입니다.

### 3.2 회귀 예측

- 입력: 개업 후 `초기 30주`
- 출력: `future_avg_sales`
  - 이후 `12주`의 평균 매출

즉,

`초기 30주만 보고 그 다음 12주의 평균 매출 수준을 예측`

한 것입니다.

---

## 4. baseline 비교에서는 무엇을 확인했는가

이 단계는  
`우리 모델이 단순 기준모형보다 낫기는 한가`

를 확인하기 위한 최소 검증입니다.

### 4.1 분류 baseline

- `MajorityClassCV`
- 각 fold에서 가장 흔한 클래스만 계속 찍는 방식

결과:

- `W=30`: accuracy `0.4568 → 0.5726`
- 오류율 `21.31%` 감소

### 4.2 회귀 baseline

- `NaiveGlobalMeanCV`
- `NaiveLastValue`
- `NaiveRecent4Mean`
- `NaiveEarlyMean`
- `SeasonalNaive13`

결과:

- `NaiveRecent4Mean` 대비
  - MAE `6.83%` 개선
  - RMSE `11.58%` 개선

- `SeasonalNaive13` 대비
  - MAE `11.46%` 개선
  - RMSE `7.25%` 개선

즉, baseline 비교는  
`단순 기준보다 의미 있게 낫다`

를 보여주는 단계입니다.

---

## 5. 하지만 baseline만으로는 부족했고, 그래서 feature ablation을 했다

맞는 지적처럼,

`기간이 길어지면 accuracy가 오르는 것`

은 어느 정도 당연합니다.

그래서 우리는 같은 `초기 30주`를 고정한 상태에서,

- 수준 정보만 쓴 경우
- 추세/변동성을 추가한 경우
- 고객행동 정보를 추가한 경우
- 지역/상권 맥락을 추가한 경우
- 요약 변수(`early_cluster` 등)를 추가한 경우

를 비교했습니다.

---

## 6. feature ablation에서 실제로 뭐가 더 중요했는가

### 6.1 분류 예측

근거:

- [forecast_feature_ablation_classification_gain.csv](/Volumes/SAMSUMG_128/master_graduate/KCD_source_code_from_Yang/26-1/260325/outputs/tables/forecast_feature_ablation_classification_gain.csv)

weighted F1 기준:

- `level_only`: `0.5620`
- `+ trend / volatility`: `0.6333`
  - `+0.0714`
- `+ customer behavior`: `0.6540`
  - `+0.0207`
- `+ local market context`: `0.6692`
  - `+0.0152`
- `+ early_cluster / growth_type`: `0.6690`
  - `-0.0002`

해석:

- 가장 크게 더한 것은 `추세/변동성`
- 그 다음은 `고객행동`
- 그 다음은 `지역/상권 맥락`
- `early_cluster`의 추가 이득은 거의 없음

### 6.2 회귀 예측

근거:

- [forecast_feature_ablation_regression_gain.csv](/Volumes/SAMSUMG_128/master_graduate/KCD_source_code_from_Yang/26-1/260325/outputs/tables/forecast_feature_ablation_regression_gain.csv)

R2 기준:

- `level_only`: `0.8753`
- `+ trend / volatility`: `0.8974`
  - `+0.0221`
- `+ customer behavior`: `0.9013`
  - `+0.0039`
- `+ local market context`: `0.9026`
  - `+0.0013`
- `+ early_cluster / growth_type`: `0.9021`
  - `-0.0005`

해석:

- 회귀도 가장 크게 더한 것은 `추세/변동성`
- 고객행동과 지역/상권은 소폭 추가 설명력
- `early_cluster`는 거의 기여 없음

---

## 7. 상권 밀집도와 경쟁강도는 의미가 있었는가

질문하신 부분을 별도로 다시 봤습니다.

근거:

- [forecast_newvol_competition.md](/Volumes/SAMSUMG_128/master_graduate/KCD_source_code_from_Yang/26-1/260325/outputs/docs/forecast_newvol_competition.md)

### 7.1 분류 예측에서는 약한 의미가 있습니다

- `core_existing` weighted F1: `0.63936`
- `+ competition` weighted F1: `0.64510`
- 증가폭: `+0.00574`

즉,

`Growth / Stable / Decline 같은 방향성 분류에서는 경쟁강도가 약하게나마 추가 정보를 준다`

고 말할 수 있습니다.

### 7.2 회귀 예측에서는 핵심적이지 않습니다

- `core_existing` R2: `0.89771`
- `+ competition` R2: `0.89664`
- 단독으로는 오히려 약간 감소

둘을 같이 넣었을 때는:

- `+ new volatility + competition`: `0.89816`
- core 대비 `+0.00045`

즉,

- 경쟁강도는 분류 예측에서는 약한 플러스
- 회귀 예측에서는 핵심 변수라고 보기 어려움
- 새 변동성과 함께 넣었을 때도 아주 미세한 결합효과만 있음

이 정도가 정직한 해석입니다.

---

## 8. 발표에서 최종적으로 어떻게 말할 것인가

아래처럼 말하면 가장 안전합니다.

`Forecasting에서는 먼저 baseline 비교를 통해 단순 기준모형보다 유의하게 낫다는 점을 확인했습니다. 다만 이것만으로는 우리 feature가 실제로 기여했는지 말하기 어려워서, 같은 초기 30주 조건에서 feature ablation을 추가로 수행했습니다. 그 결과 forecasting 성능을 가장 크게 끌어올린 것은 단순 매출 수준이 아니라 추세와 변동성이었고, 고객행동 및 지역/상권 맥락은 그 위에 보조적인 설명력을 더했습니다. 반면 early_cluster 같은 요약 변수의 추가 이득은 거의 없었습니다.`

`또한 새로 정의한 detrended volatility는 Growth/Stable/Decline 설명모형에서는 기존 CV보다 더 적절했지만, forecasting에서는 기존 core feature 위에 거의 추가 정보를 주지 못했습니다. 경쟁강도는 분류형 forecasting에서는 약한 플러스였지만, 미래 평균 매출 회귀에서는 핵심 변수라고 보기는 어려웠습니다.`

---

## 9. 한 줄 결론

`새 변동성은 설명분석에는 유의미했지만 forecasting 추가 변수로는 거의 효과가 없었고, forecasting에서 실제로 가장 중요한 것은 여전히 추세·변동성의 기본 패턴이며 경쟁강도는 분류 문제에서만 약한 보조효과를 보였다.`
