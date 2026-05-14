# 제 6 장 논의

본 장은 §5 의 결과를 해석한다. §6.1 은 일곱 가지 주요 발견을 정리하고,
§6.2 는 각 발견의 학문적 의의 (4 가지 mechanism 가설 포함) 를, §6.3 은
실무·정책적 함의를, §6.4 는 본 연구의 한계를, §6.5 는 본문 contribution
이 아닌 future work 로 분리된 주제 (LEVI / EWS / GNN / Golden Cross /
외부 공공 데이터 등) 의 위치를 다룬다.

본 장은 §1.4 의 세 본문 기여를 중심으로 서술된다. §6.1.1 ~ §6.1.2 와
§6.1.6 ~ §6.1.7 은 prediction baseline 과 요인 분해 (기여 1), §6.1.3
은 시즌 정렬 (기여 2), §6.1.4 ~ §6.1.5 는 세 갈래 prediction-improvement
시도 (기여 3) 에 각각 대응한다.

## 6.1 주요 발견 정리

### 6.1.1 시즌 confound 는 라이프사이클 분류 결과에 결정적이다

§5.2 에서 시즌 정렬 145 개 specification 의 baseline macro-F1 은 약
0.43 ~ 0.54 사이에 분포한다. 시작월 효과의 진폭(약 0.10) 은 윈도우
길이 효과(0.02 ~ 0.04) 나 시작연도 효과(0.01 미만) 보다 한 자릿수
크다. 같은 모델·같은 피처·같은 5 만 점포에서도 라벨 정의가 시즌과
어떻게 결합되느냐에 따라 분류 정확도가 약 25% 변동한다.

본 결과는 기존 라이프사이클 분류 연구가 "마지막 30 주" 또는 전체 기간
기울기로 라벨을 정의해 온 관행이 라벨 시점 confound 에 노출되어 있음
을 정량적으로 보여준다.

### 6.1.2 Hybrid representation 의 추가 향상은 조건부다

§5.5 에서 baseline + cluster + change-point 의 D 모델은 7 개 3 개월
대표 panel 평균 ΔF1 = +0.0022 향상에 그친다. 5% 유의는 1 / 7 panel
(`sy2022_sm03_w3m_off1`, p = 0.026) 에서만 잡히고, 나머지 5 개 panel
은 p > 0.25 로 효과 자체가 noise 수준이다. 향상이 발생한 panel 은
baseline Decline recall 이 가장 낮은 라벨 편중 panel 이며, 이는
cluster + change-point 가 baseline 이 잡지 못한 영역(라벨 편중으로
정보가 희소한 영역) 에서만 상보적 신호를 제공한다는 해석으로 이어
진다.

확장 윈도우(4 / 6 / 7 개월) 7 개 panel 의 결과는 §5.5.2 에 보고되며,
3 개월 결과와 합쳐 14 panel 비교가 이루어진다. 본 드래프트는 1 차
결과만으로도 다음 결론에 도달한다 — 기존 파이프라인의 hybrid 모델
비교 결과(D ≫ A by 약 0.05 macro-F1) 가 라벨 구간이 항상 2023 년
6 ~ 8 월 휴가 시즌에 고정된 시즌 confound 위에서 성립한 결과일 가능
성이 높다. 시즌 정렬 라벨에서는 본 향상의 효과 크기와 통계적 유의성
이 모두 무너진다.

### 6.1.3 코로나 시기와 회복기 결과는 체계적으로 다르지 않다

§5.3 에서 2021 시작 panel 과 2022 시작 panel 의 평균 macro-F1 차이는
모든 윈도우 길이에서 0.02 이내다. 본 데이터에서 코로나 잔여 영향은
분류 정확도를 좌우하지 않는다.

다만 본 결과는 분류 정확도라는 한 차원에서의 결론이며, 라벨 분포
자체(예: 2021 시작 panel 은 회복으로 인한 G 가 더 많고, 2022 시작
panel 은 라벨 균형이 다르다) 는 코로나 회복 과정에 영향을 받는다
(§5.1). 따라서 "코로나 영향이 완전히 없다" 가 아니라 "분류 정확도
에서는 작다" 가 정확한 해석이다.

### 6.1.4 LightGBM tabular ensemble 은 RF 위에 일관된 추가 향상을 준다

§5.5.3 에서 동일한 56 개 baseline + cluster + cp 피처 위의 LightGBM
이 RF 를 6 panel 중 5 개에서 능가하며 평균 ΔF1 = +0.0075, 2 개 panel
에서 p < 0.05 향상을 보인다. 본 향상은 §5.5 의 hybrid representation
효과(평균 +0.0022) 와 비교해 약 4 배 강하며, §5.6 외부 모델 14 종 중
RF 를 능가하는 유일한 경우다.

향상의 sub-population 분해(§5.5.3.1) 가 함의를 강화한다.

- tenure 가 길수록 ΔF1 이 단조 증가: Q1 = +0.002 → Q4 = +0.019 (전체
  의 약 2.4 배).
- fragile cluster (Decline 17%) 에서 ΔF1 = +0.044 (전체의 약 5.5 배).
- 정책적 우선 대상 (오래된 + 위험 cluster) 에서 모델 향상이 가장 크다.

또한 LightGBM 의 의사결정 점수(Decline 확률) 가 RF 보다 calibration
이 정확하다(§5.5.3.2; Brier 0.097 vs 0.109). 본 결과는 M5 Walmart
정확도 대회의 우승자 패턴(LightGBM ensemble dominance, Makridakis
et al., 2022) 이 SMB 단기 G/S/D 분류로도 전이됨을 시사한다.

### 6.1.5 외부 시계열 SOTA 와 foundation model 은 SMB 단기 분류에 이식되지 않는다

§5.6 의 benchmark 에서 외부 SOTA 14 종 (foundation 2, stock SOTA 7,
SMB attention 3, cost-sensitive 변형 2) 중 LightGBM 패밀리 (lgbm_tabular,
lgbm_shap_weighted, lgbm_decline_x2) 를 제외한 모두가 RF baseline 에
패배한다. 효과 크기 분포는 다음과 같다 (`phase5_summary.csv` 인용).

- Foundation zero-shot (chronos_bolt_small, moirai_small): ΔF1 = −0.187
  ~ −0.211. 거의 random guessing 수준 (F1 ≈ 0.29 ~ 0.31).
- Stock SOTA 7 종 (TFT, N-BEATS, N-HiTS, PatchTST, DLinear, Informer,
  Autoformer): ΔF1 = −0.139 ~ −0.246. DLinear 가 stock SOTA 1 위
  (Zeng et al., 2023 의 Transformer 무용론 재현).
- SMB-specific attention 3 종 (FeatureAttnMLP, FiLM-tenure-LSTM,
  TimeAttn-LSTM): ΔF1 = −0.035 ~ −0.092. FeatureAttnMLP 가 가장 RF 에
  가까우나 6 / 6 panel 에서 5% 유의 패배.
- Cost-sensitive 변형 (rf_decline_x2, rf_decline_x3): ΔF1 = −0.035 ~
  −0.063, 6 / 6 panel 에서 RF baseline 대비 유의 *하락* (§5.9).

본 발견은 부정 결과이지만, 시즌 정렬 main contribution 과 §6.1.2
hybrid 의 조건부 한계의 정당화 근거가 된다 — SMB 단기 G/S/D 분류는
기존 거대 시계열 literature 의 표준 방법론으로 풀 수 없는 별도 영역
이다.

### 6.1.6 업력 cohort 가 길수록 신규고객 → Growth 의 logit 효과가 일관되어진다

§5.7 의 cohort 분석에서 `nc_slope` (feature window 안의 신규고객 증감
기울기) 가 Growth 와 갖는 logit 회귀 계수 β 는 cohort 별로 다음 패턴
을 보인다.

- Q1_short (업력 ~9 개월): panel 별 β 분산 큼 (0 ~ 2.0).
- Q4_long (업력 ~115 개월): panel 별 β 안정 (0.9 ~ 1.9).

업력이 길어질수록 신규고객 유입이 Growth 와 일관적·안정적으로 연관
된다. v2 draft 의 "신규 고객 비중이 업력 길어질수록 단조 증가
(2.2 → 7.5×)" 결론은 시즌 정렬 panel 위에서도 약화된 형태로 재현된다.

본 발견은 advisor 미팅의 "신규 유입·업력이 주요 요인 (상승에 유의미)"
권유에 정량적으로 답하는 결과이며, prediction baseline 의 sub-population
구조를 보여준다. 다만 본 회귀는 관찰적이며, 신규고객 유입과 Growth
가 동시에 시즌·인지도 같은 외생 변수에 의해 결정될 가능성을 배제하
지 못한다 (§6.2.5 에서 논의).

### 6.1.7 KMeans cluster 는 fragile / survivor 의 이원 구조를 panel 간에 재현한다

§5.8 의 cluster × G/S/D 교차표에서 6 cluster 는 panel 간 cluster
번호가 바뀌어도 일관된 이원 구조를 보인다.

- **fragile cluster** (1 ~ 2 개 cluster): Decline 비중 35 ~ 60%,
  panel 전체 점포 수의 5 ~ 15%.
- **survivor cluster** (1 ~ 2 개 cluster): Decline 비중 ≤ 13%, Stable
  / Growth 비중 합 ≥ 85%.
- 나머지 cluster 는 mixed (Decline 15 ~ 27%).

LightGBM 의 RF 대비 향상 (§5.6.3) 은 fragile cluster 에서 가장 크다
— cluster 3 의 평균 ΔF1 = +0.044 는 전체 평균 (+0.0075) 의 약 5.9
배. 즉 prediction 향상이 정책 우선 대상 (Decline 비중 큰 cluster)
에 집중되어 있어, 모델 향상의 실효가 가장 크게 나타나는 영역과
정책적 우선 영역이 일치한다.

## 6.2 학문적 의의

### 6.2.1 라벨 시점 confound 의 정량 폭로

§6.1.1 은 거래 데이터 기반 점포 분류 연구가 빠지기 쉬운 함정을 정량
수준에서 드러낸다. forecasting / OOS 검증 문헌에서는 시즌 통제의 필요
성이 오랫동안 강조되었지만(Bergmeir & Benítez, 2012; Hyndman &
Athanasopoulos, 2021), 점포 단위 라이프사이클 분류 연구에서 145 개
specification 수준의 robustness check 가 수행된 사례는 드물다. 본
연구의 시즌 정렬 rolling-window 설계는 본 영역의 연구가 따라야 할
robustness 표준을 제안한다.

### 6.2.2 Hybrid representation 의 외적 타당성 한계

§6.1.2 는 hybrid representation 의 향상 효과가 라벨 / 시즌 분포에
강하게 의존한다는 실증 증거다. KMeans cluster 와 change-point 는
시계열 분류 문헌 (Paparrizos & Gravano, 2015; Truong et al., 2020)
에서 "거의 항상 도움이 된다" 는 톤으로 다루어지지만, 본 연구는 라벨
정의가 깨끗할수록 baseline 통계 피처만으로도 거의 모든 정보를 흡수해
hybrid representation 의 추가 정보가 사라지는 패턴을 보인다. 본 발견
은 해당 representation 의 이론적 가치 자체를 부정하지 않지만, "어느
라벨에서 어느 정도 향상을 줄지" 를 사전에 예측할 수 없음을 시사한다.

### 6.2.3 라이프사이클 라벨 정의 자체에 대한 재검토 필요

§6.1.1 과 §6.1.2 를 합치면 더 일반적인 함의가 도출된다. 같은 데이터·
같은 모델이라도 라벨 정의가 다르면 학술적 결론(D ≫ A 인지, D ≈ A
인지) 이 바뀐다. 본 연구는 시즌 정렬을 한 가지 대안으로 제시했지만,
라벨 정의의 다양성과 그에 따른 결과 의존성을 명시적으로 다룬 라이프
사이클 분류 연구는 여전히 부족하다. 본 점은 해당 분야의 reproducibility
한계 가능성을 시사한다.

### 6.2.4 SMB 단기 분류의 차별화 — 4 가지 mechanism 가설

§6.1.5 의 14 종 negative 패턴은 단순한 데이터 우연이 아니라 구조적
이유에서 비롯된다. 본 절은 본 분석에서 도출되는 4 가지 mechanism 가설
을 정리한다. 각 가설은 §7.2 에서 검증 실험으로 확장 가능하다.

**(a) Short window 가설.** 본 데이터의 입력 윈도우는 13 ~ 31 주(3 / 7
개월) 다. TimesFM / Chronos / Moirai 의 pretrain 데이터는 utility /
retail / traffic daily 시계열 중심으로 200 + timestep context 를 가정
한다. Informer / Autoformer / PatchTST 같은 long-horizon Transformer
도 96 ~ 720 timestep 에 맞춰 설계되었다. 13 주에서 self-attention
헤드가 학습할 패턴 자체가 부족하다.

**(b) Regression-to-classification 변환 손실 가설.** foundation 과
stock SOTA 는 모두 raw value forecasting 으로 학습되었다. 본 연구는
forecast → slope_norm → ±0.5σ bucket 으로 3-class 변환을 수행한다.
본 변환에서 forecast 의 노이즈가 직접 amplify 된다. §6.1.5 에서
DLinear (단순 linear projection) 가 stock SOTA 1 위였던 점은 — 가장
노이즈를 적게 amplify 하는 모델 — 본 가설과 정합한다.

**(c) Multivariate channel compression 가설.** 본 데이터는 6 채널
multivariate (sales_card, customer, customer_new, before_noon,
weekend, sales_delivery) 다. 56 개 통계 피처(slope_all, ma4_slope,
vol_w8, sales_cv 등) 는 6 채널을 channel-aware 하게 압축하며,
RF / LightGBM 의 split-gain 학습이 본 압축 representation 위에서
채널 간 비선형 상호작용을 잡는다. raw 6 채널 sequence 를 LSTM /
Transformer 가 직접 학습하는 것보다, 통계 압축 + tree ensemble 이
더 효과적이다 (§6.1.5 의 SMB-attention 3 종 패배가 본 가설을 뒷받침
한다).

**(d) Calendar season confound dominance 가설.** §6.1.1 에서 시작월
진폭(0.10) 이 다른 변수보다 한 자릿수 크다. stock 데이터(장 개장
daily) 에는 calendar season 효과가 미미하지만, SMB 주간 매출은 명절·
계절 효과가 결정적이다. 본 연구의 메인 contribution(시즌 정렬) 위에
서만 RF baseline 이 0.50 으로 안정되며, raw sequence 위에 시즌 통제
없이 학습하는 모든 SOTA 는 시즌-confounded 신호와 lifecycle 신호를
분리하지 못한다.

본 4 가지 가설은 §7.2 의 후속 연구(synthetic long-history ablation
등) 에서 정량 검증할 수 있다.

### 6.2.5 Cohort 와 cluster 의 경제적 해석

§6.1.6 ~ §6.1.7 의 미시 구조는 SMB 라이프사이클 연구에 두 가지 함의
를 갖는다.

첫째, **신규고객 유입의 prediction 가치가 업력 cohort 에 따라
differential** 하다. 짧은 업력 (≤ 1 년) cohort 에서는 신규고객 유입과
Growth 의 logit 관계가 panel 간 진동이 크다. 이는 신규 점포가 영업
초기 인지도 형성기에서 시즌 / 입지 / 외부 자극에 더 흔들리며, 신규
고객 증가가 매출 성장 신호로 안정적으로 작동하지 않을 가능성을
시사한다. 반대로 업력이 긴 cohort 에서는 신규고객 증가가 Growth 와
더 일관적으로 연관되어, "재방문 고객 위에 신규 유입이 누적" 되는
경로가 작동할 수 있다. 본 해석은 관찰적이며 인과적 주장이 아니다.

둘째, **fragile / survivor 이원 구조는 단순한 random partition 이
아니라 prediction-relevant 한 sub-population 분할** 이다. fragile
cluster 의 Decline 비중 35 ~ 60% 는 panel 평균 (~15%) 의 2 ~ 4 배이며,
이는 데이터 안에 "쇠퇴가 집중되는 영역" 이 존재함을 의미한다. 본
이원 구조는 추후 EWS 형 의사결정 도구(§6.5) 의 1 차 segmentation
근거가 될 수 있다.

본 두 함의는 advisor 미팅의 "small business 들의 dynamics 를 설명
하고 더 잘 prediction 할 수 있다" 권유에 직접 대응한다. dynamics 설명
(누가 G/S/D 로 가는지) 과 prediction 향상 (어느 sub-population 에서
모델이 가장 잘 작동하는지) 이 동일 cohort × cluster 위에서 정합적으로
관찰된다.

## 6.3 실무·정책적 함의

본 연구의 결과는 카드 매출 데이터를 통한 점포 조기 진단이 다음 조건
에서 의미 있음을 시사한다.

1. **라벨 시점이 명시적으로 시즌 통제될 때.** 단순히 "마지막 N 주"
   라벨로 조기 경보 모델을 학습한 결과를 그대로 정책 도구로 쓰는 것은
   시즌 효과를 라이프사이클 신호로 오인할 수 있다.
2. **라벨 분포가 편중된 시즌 (예: 봄·초여름 회복 시즌) 에서 hybrid
   representation 의 추가 향상이 실용적 효과를 가질 수 있다.** 다만
   본 연구의 수치(ΔF1 0.005 ~ 0.012 Decline recall) 가 실무 의사결정
   기준 (예: 정책 지원 점포 선별 임계) 을 넘는지는 별도 비용·편익
   분석이 필요하다.
3. **점포 단위 분류 정확도(macro-F1 0.5 수준) 는 정책 처방이 아니라
   우선 검토 대상 좁히기 도구로 활용해야 한다.** recall 0.4 ~ 0.6 의
   모델을 자동화된 폐업 예측·금융 거절 시스템으로 직접 사용하는 것
   은 false positive 로 인한 점포 피해를 야기할 수 있다.
4. **LightGBM 의사결정 점수의 decile 활용**(§5.5.3.2). 본 데이터
   calibration 결과 top decile (상위 10% 위험) 의 관측 Decline 비율은
   34.8% 로 baseline (13%) 의 약 2.7 배, 최저 decile 대비 약 17 배
   spread 다. 정책 의사결정 시 "100% 명단" 이 아닌 "top decile 우선
   검토" 형식의 targeting 으로 활용하면, false positive 비용을 통제
   하면서 효율적 자원 배분이 가능하다.
5. **fragile cluster (Decline 17%) 우선 적용.** §5.5.3.1 의 cluster
   분해 결과 LightGBM 의 우위가 fragile cluster 에서 가장 크다(+0.044,
   전체 평균의 약 5.5 배). 즉 모델 향상이 가장 절실한 영역에서 향상
   폭도 가장 크다.

본 연구는 정책 처방이나 인과 효과를 주장하지 않는다.

## 6.4 한계

본 연구의 결과 해석에 다음 한계가 따른다.

1. **검정력 한계.** 5-fold paired t-test 의 자유도는 4 로, ΔF1 +0.002
   정도의 작은 효과 크기에 대한 검정력은 약하다. 향후 repeated CV
   (예: 10-fold × 10 repeats) 나 seed-multi bootstrap 을 통해 효과
   크기와 분산을 안정적으로 추정할 필요가 있다.
2. **단일 random seed.** 모든 결과는 seed = 42 단일 시도다. KMeans
   초기화, stratified split, RandomForest 부트스트랩 모두 seed 에 의존
   한다.
3. **단순한 cluster / change-point 메서드.** KMeans k = 6 은 elbow /
   silhouette 같은 cluster 수 결정 절차를 거치지 않은 상수 선택이며,
   change-point 는 max-mean-gap 단일 분할로 단순화된 구현이다 (PELT
   다중 변곡점 대비 정보 손실 가능). K-Shape, DTW-KMeans, Bayesian
   online change-point 같은 정교한 representation 으로 다시 측정하면
   ΔF1 효과 크기가 살아날 수 있다.
4. **외식업 한정.** 본 데이터는 서울시 외식업 점포만 포함한다. 도소
   매·서비스업의 시즌 패턴(예: 의류는 환절기 강한 시즌성) 은 다르며,
   본 연구의 시즌 효과 진폭(0.10) 이 다른 업종에서도 같은 크기로 나타
   날지는 별도 검증이 필요하다.
5. **현금 결제 누락.** 카드 매출만 관측되므로 현금 비중이 큰 점포
   (전통시장 등) 의 분류 정확도가 체계적으로 떨어질 가능성이 있다.
6. **2 년 이상 panel 부족.** 본 데이터는 142 주(약 2.7 년) 이므로
   `target_offset = 2` (2 년 후 같은 캘린더 월) panel 은 9 월 이후
   시작월에서 모두 데이터를 벗어난다. 더 긴 패널 데이터에서는 더
   다양한 시즌 비교가 가능하다. 더 긴 윈도우(8 / 12 개월) 도 같은
   컷오프 제약으로 본 분석에서 제외되었다.

## 6.5 본 연구 범위 밖 (Future Work)

다음 주제는 본 학위논문의 본문 contribution 에서 의도적으로 제외했다.
저널 확장 시에는 별도 contribution 으로 발전시킬 수 있다.

- **LEVI (Local Economic Vitality Index).** 자치구 단위 점포 라이프
  사이클 종합 지표. 본 연구의 점포 단위 분류 결과를 자치구 단위로
  집계해 서울시 생활 인구·이동 인구 데이터와의 상관을 검증한 사전
  분석이 있다. 본 학위논문 본문에는 포함하지 않으며 §7.2 에서 다시
  다룬다.
- **EWS (Early Warning System).** 점포 단위 쇠퇴 위험 점수 기반 정책
  지원 우선순위 도구. 본 연구의 cluster + change-point 결과가 라벨
  편중 panel 에서만 의미 있으므로, EWS 의 cost-sensitive 의사결정 평가
  는 별도 분석 frame 에서 다뤄야 한다.
- **외부 공공 데이터 5 종 추가 검증.** 서울시 카드 매출 공개 자료 등
  으로 KCD 데이터의 외적 타당도를 보강한 사전 분석이 있으나, 본
  학위논문 본문에는 포함하지 않는다.
- **신규 고객 유입의 매출 반등 선행성 (Golden Cross) 시즌 panel 재
  검증.** Granger / PSM 등 인과 기법으로 신규 고객 유입이 매출 반등
  을 선행한다는 분석이 있으나, 시즌 정렬 panel 에서 본 선행성이 유지
  되는지는 본 연구의 메인 모델 비교에 들어가지 않았다.
- **Chronos / TimesFM LoRA finetune.** §6.1.5 의 foundation model
  zero-shot 결과(F1 = 0.23 ~ 0.31) 가 너무 약해 본문 비교에서는
  zero-shot 만 다루었다. 본 데이터에 LoRA finetune 시 RF 근접 가능성
  은 낮지만 실험적 가치가 있다.
- **Cost-sensitivity dollar-value sweep.** §6.3 항목 4 의 top-decile
  targeting 정책 권고를 한국 폐업 cost assumption 으로 환산해 정책
  시나리오 3 종(lending, subsidy, intervention) 의 expected loss 표를
  작성하는 작업.
- **Synthetic long-history ablation.** §6.2.4 의 (a) "short window 가
  stock SOTA 패배의 원인인가" 를 분리 검증. raw weekly 에서 4 년 연속
  history 가 있는 점포 subset 으로 같은 SOTA 를 재학습해 window ×
  model 매트릭스로 mechanism 을 정량 입증하는 작업.
- **GNN (네트워크 모델) 확장.** advisor 미팅 권유 중 하나는 "네트워크
  모델 추가 (GNN 등)" 였다. 본 연구의 `gnn_compare.csv` (260430_claude/
  outputs/tables/) 는 행정동 / 업종 / hybrid 그래프 위에 GCN + MLP 를
  시험한 pilot 결과를 담는다 (대표 3 panel). 현재까지 GCN 은 RF
  baseline 대비 ΔF1 = −0.04 ~ −0.10 으로 패배하며, MLP 는 RF 와
  비슷한 수준 (−0.07 안팎) 이다. 그래프 정의 (이웃 점포 선택, 가중치)
  와 message passing layer 수 grid 가 필요하므로 본문 contribution
  에서 분리한다.
- **Cost-sensitive policy sweep.** §5.9 의 rf_decline_x2 / lgbm_decline_x2
  결과는 macro-F1 에서는 음(−) 또는 미세 차이지만, Decline recall /
  Decline F1 만 본다면 trade-off 가 존재한다. 한국 폐업 비용 가정
  하에 cost matrix grid (1 ~ 5 배) 와 expected loss 표를 작성하면 정책
  의사결정 시나리오를 만들 수 있다.

본 여덟 가지 주제는 본 학위논문의 본문 결론에 포함되지 않으며, 본
연구의 세 contribution (prediction baseline 과 요인 분해 / 시즌 정렬
robustness 전제 / hybrid·cost-sensitive·외부 SOTA 세 갈래 개선 한계
+ SMB-specific 차별화) 과 분리되어 다루어진다.
