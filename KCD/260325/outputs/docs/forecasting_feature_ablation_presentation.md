# Forecasting Feature Ablation 발표 정리

## 1. 왜 이 실험이 필요한가

맞는 지적입니다.  
`초기 관측 주가 20주보다 30주, 40주, 50주일 때 accuracy가 올라가는 것`은 어느 정도 자연스러운 현상입니다.

그래서 이 실험의 목적은

`관측 기간이 길어져서 성능이 좋아진 것`과  
`우리 분석에서 만든 feature가 실제로 추가 정보를 준 것`

을 구분하는 것입니다.

이번에는 관측 기간을 `초기 30주`로 고정한 뒤, 같은 표본에서 feature block을 하나씩 추가하면서 성능이 얼마나 늘어나는지 확인했습니다.

---

## 2. 이번 ablation이 정확히 무엇을 예측했는가

이번 고정 `W=30` ablation은 `260316`의 조기예측 데이터셋을 사용했습니다.

- 데이터: [early_prediction_dataset.csv](/Volumes/SAMSUMG_128/master_graduate/KCD_source_code_from_Yang/26-1/260316/outputs/tables/early_prediction_dataset.csv)
- 표본 수: `50,635개 업장`
- early window: `개업 후 0~29주`
- future window: `30~41주`

이번 실험에서는 두 가지 target을 보았습니다.

### 2.1 분류 target

- `life_cycle_category`
  - `rising`
  - `maintaining`
  - `declining`

즉,

`초기 30주 정보만 보고 이 업장이 이후에 상승형 / 유지형 / 하락형 패턴으로 갈지를 예측`

한 것입니다.

### 2.2 회귀 target

- `future_avg_sales`

즉,

`초기 30주 정보만 보고 그 다음 12주의 평균 매출 수준을 예측`

한 것입니다.

주의할 점은, 이 ablation은 `260321_cur`의 `W=30 outcome3`와 완전히 같은 타깃은 아닙니다.  
이번 실험은 richer feature를 보기 위해 `260316`의 `초기 30주 조기예측 데이터셋`을 기준으로 했고, 따라서 분류 target은 `life_cycle_category`입니다.

---

## 3. 어떤 feature block을 비교했는가

같은 30주 정보에서 아래 block을 순서대로 추가했습니다.

### Block 1. `level_only`

단순 현재 수준 정보만 사용

- `avg_sales_total`
- `avg_customer`
- `max_sales`
- `min_sales`
- `business_square_size`

이 block은 쉽게 말해

`지금 얼마나 팔고 있는가, 손님이 얼마나 오는가, 점포 크기가 어느 정도인가`

만 보는 모델입니다.

### Block 2. `+ trend / volatility`

위에 더해서 시계열 패턴 추가

- `std_sales_total`
- `cv_sales_total`
- `growth_rate`
- `trend_slope`
- `max_min_ratio`

이 block은

`단순 수준`에서 끝나지 않고  
`올라가고 있는가`, `흔들림이 큰가`, `최대/최소 폭이 어떤가`

를 추가한 것입니다.

### Block 3. `+ customer behavior`

위에 더해서 고객행동 정보 추가

- `new_customer_ratio`
- `cv_customer`
- `weekend_ratio`
- `card_ratio`
- `invoice_ratio`
- `delivery_ratio`
- `before_noon_ratio`
- `after_noon_ratio`
- `purchase_to_sales_ratio`

이 block은

`누가 오고 있는가`, `신규 고객이 얼마나 들어오는가`, `주말 의존도가 높은가`, `배달/카드/시간대 구조가 어떤가`

를 반영합니다.

### Block 4. `+ local market context`

위에 더해서 지역/상권 맥락 추가

- `business_age_months`
- `age_numeric`
- `dong_store_count`
- `dong_avg_sales`
- `sigungu_store_count`
- `sigungu_avg_sales`
- `business_density`
- `delivery_link`

즉,

`업장의 연차`, `지역 내 업장 수`, `지역 평균 매출`, `상권 밀도`

를 추가한 것입니다.

### Block 5. `+ pattern summary`

위에 더해서 추가 구조 변수

- `growth_type`
- `early_cluster`

즉,

`초기 패턴을 요약한 범주형 정보`

를 추가한 마지막 block입니다.

---

## 4. 결과: 어떤 feature가 실제로 더 유의미했는가

산출물:

- [forecast_feature_ablation_classification.csv](/Volumes/SAMSUMG_128/master_graduate/KCD_source_code_from_Yang/26-1/260325/outputs/tables/forecast_feature_ablation_classification.csv)
- [forecast_feature_ablation_classification_gain.csv](/Volumes/SAMSUMG_128/master_graduate/KCD_source_code_from_Yang/26-1/260325/outputs/tables/forecast_feature_ablation_classification_gain.csv)
- [forecast_feature_ablation_regression.csv](/Volumes/SAMSUMG_128/master_graduate/KCD_source_code_from_Yang/26-1/260325/outputs/tables/forecast_feature_ablation_regression.csv)
- [forecast_feature_ablation_regression_gain.csv](/Volumes/SAMSUMG_128/master_graduate/KCD_source_code_from_Yang/26-1/260325/outputs/tables/forecast_feature_ablation_regression_gain.csv)

### 4.1 분류 예측에서의 추가 기여

`weighted F1` 기준:

- `level_only`: `0.5620`
- `+ trend/volatility`: `0.6333`
  - 증가폭: `+0.0714`
- `+ customer behavior`: `0.6540`
  - 증가폭: `+0.0207`
- `+ local market context`: `0.6692`
  - 증가폭: `+0.0152`
- `+ pattern summary`: `0.6690`
  - 증가폭: `-0.0002`

해석:

1. 가장 큰 기여는 `추세/변동성 block`입니다.  
   단순 수준 정보만으로는 F1이 `0.5620`인데, 추세/변동성을 넣자 `0.6333`으로 크게 뛰었습니다.

2. 그 다음으로 의미 있게 더해진 것은 `고객행동 block`입니다.  
   신규고객, 주말 비중, 배달/결제 구조를 넣자 `+0.0207`만큼 더 올랐습니다.

3. `지역/상권 맥락 block`도 추가 이득이 있습니다.  
   증가폭은 `+0.0152`로 앞 블록보다는 작지만 여전히 양(+)입니다.

4. 반면 `growth_type`, `early_cluster` 같은 추가 요약 변수는 거의 더하지 못했습니다.  
   마지막 단계에서는 오히려 아주 미세하게 내려갔습니다.

즉, 분류 예측에서는

`현재 수준`보다 `추세와 변동성`이 훨씬 중요했고,  
그 다음에 `고객행동`, 그 다음에 `지역/상권 맥락`이 보조적으로 더해졌으며,  
`초기 패턴 요약 변수`의 추가 이득은 거의 없었습니다.

### 4.2 회귀 예측에서의 추가 기여

`R2` 기준:

- `level_only`: `0.8753`
- `+ trend/volatility`: `0.8974`
  - 증가폭: `+0.0221`
- `+ customer behavior`: `0.9013`
  - 증가폭: `+0.0039`
- `+ local market context`: `0.9026`
  - 증가폭: `+0.0013`
- `+ pattern summary`: `0.9021`
  - 증가폭: `-0.0005`

해석:

1. 회귀에서도 가장 큰 추가 기여는 `추세/변동성 block`입니다.  
   수준 정보만으로도 이미 R2가 `0.8753`으로 높지만, 추세/변동성을 넣으면 `0.8974`까지 올라갑니다.

2. `고객행동 block`은 추가 개선이 있긴 하지만 크지는 않습니다.  
   증가폭은 `+0.0039`입니다.

3. `지역/상권 맥락 block`도 아주 소폭 더해집니다.  
   증가폭은 `+0.0013`입니다.

4. `growth_type`, `early_cluster`는 여기서도 한계효과가 거의 없습니다.

즉, 미래 평균 매출 예측도

`현재 매출 수준`이 기본적으로 가장 중요하지만,  
그 다음으로 실질적인 추가 정보를 주는 것은 역시 `추세/변동성`입니다.

---

## 5. 이번 결과를 어떻게 말해야 하는가

이번 실험으로는 아래처럼 말할 수 있습니다.

### 말할 수 있는 것

`관측 기간이 길어져서 성능이 오른 것과 별개로, 같은 초기 30주 조건에서도 추세와 변동성 정보가 가장 큰 추가 예측력을 제공했다. 그 다음으로는 고객행동 정보와 지역/상권 맥락이 보조적으로 성능을 올렸고, early_cluster 같은 추가 요약 변수의 한계효과는 거의 없었다.`

### 말하면 안 되는 것

- `우리가 만든 모든 feature가 다 중요했다`
- `cluster가 forecasting 핵심이다`
- `신규고객 변수 하나가 결정적이었다`

현재 결과는 `block 수준`의 기여를 보여주는 것이지,
개별 변수 하나하나의 인과적 중요도를 보여주는 것은 아닙니다.

---

## 6. 발표용으로 가장 중요한 한 줄

`고정된 초기 30주 정보를 기준으로 보면, forecasting 성능을 가장 크게 끌어올린 것은 단순 매출 수준이 아니라 추세와 변동성 정보였고, 고객행동 및 상권 맥락 변수는 그 위에 추가적인 설명력을 제공했다. 반면 early_cluster 같은 요약 변수의 추가 이득은 거의 없었다.`

---

## 7. 발표 때 바로 읽을 수 있는 대본

`baseline 비교만으로는 단순 기준모형보다 낫다는 점만 말할 수 있고, 우리만의 feature가 실제로 도움이 됐는지는 별도 ablation이 필요합니다. 그래서 이번에는 관측 기간을 초기 30주로 고정하고, 같은 표본에서 feature block을 하나씩 추가해봤습니다.`

`그 결과 분류 예측에서는 level only 대비 trend와 volatility를 넣었을 때 weighted F1이 0.562에서 0.633으로 가장 크게 뛰었고, customer behavior를 넣으면 0.654, local market context를 넣으면 0.669까지 올라갔습니다. 반면 early_cluster 같은 추가 요약 변수는 거의 더하지 못했습니다.`

`회귀 예측도 같은 패턴입니다. future average sales 예측에서 level only의 R2는 0.875였는데, trend와 volatility를 넣자 0.897로 크게 오르고, customer behavior와 local market context는 그 위에 소폭 더해졌습니다. 따라서 우리 forecasting에서 핵심적으로 의미 있었던 것은 단순 수준보다 추세와 변동성이고, 고객행동과 상권 맥락은 추가 정보를 주는 보조 block으로 해석할 수 있습니다.`
