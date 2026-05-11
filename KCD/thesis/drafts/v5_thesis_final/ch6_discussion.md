# 제6장 논의

본 장은 §5 의 결과를 해석한다. §6.1 은 다섯 가지 주요 발견을 정리하고,
§6.2 는 각 발견의 학문적 의의를, §6.3 은 실무·정책적 함의를, §6.4 는 본
연구의 한계를, §6.5 는 미팅에서 본문 contribution 이 아닌 future work /
응용으로 분리된 LEVI / EWS / 외부 공공 데이터의 위치를 다룬다.

## 6.1 주요 발견 정리

### 발견 1: 시즌 confound 는 라이프사이클 분류 결과에 결정적이다

§5.2 에서 시즌 정렬 80 + α 개 specification 의 baseline macro-F1 은
0.43 ~ 0.54 사이에 분포한다. 시작월 효과의 진폭(0.10) 은 윈도우 길이 효과
(0.02 ~ 0.04) 나 시작연도 효과(0.01 미만) 보다 한 자릿수 크다. 같은 모델·
같은 피처·같은 5 만 점포에서도 라벨 정의가 시즌과 어떻게 결합되느냐에
따라 분류 정확도가 25% 가까이 변한다.

이는 기존 라이프사이클 분류 연구가 "마지막 30 주" 또는 전체 기간 기울기로
라벨을 정의해 왔던 관행이 라벨 시점 confound 에 노출돼 있음을 정량적으로
보여주는 결과다.

### 발견 2: hybrid representation 의 추가 향상은 조건부 contribution 이다

§5.5 에서 baseline + cluster + change-point 의 D 모델은 7 개 3-month
대표 panel 평균 +0.0022 macro-F1 향상에 그친다. 5% 유의는 1/7 panel
(`sy2022_sm03_w3m_off1`, p=0.026) 에서만 잡히고, 나머지 5 개 panel 은
p > 0.25 로 효과 자체가 noise 수준이다. 향상이 발생한 panel 은 baseline
Decline recall 이 가장 낮은(0.295) 라벨 편중 panel 이며, 이는 cluster +
change-point 가 baseline 이 잡지 못한 영역(라벨 편중으로 정보가 희소한
영역) 에서만 상보적 신호를 제공한다는 해석으로 이어진다.

확장 윈도우(4 / 6 / 7 개월) 7 개 panel 결과(§5.5.2) 가 도착하면 다음
세 가지 중 어느 시나리오인지에 따라 framing 이 결정된다.

- 시나리오 A — 7 개월 D − A ≈ +0.002: "조건부 contribution" 그대로 유지.
- 시나리오 B — 7 개월 D − A = +0.01 ~ +0.03: "윈도우 임계 contribution" 로
  micro-shift.
- 시나리오 C — 7 개월 D − A ≈ 0 또는 음수: hybrid contribution 사실상
  무력화. 시즌 robustness 만 단독 contribution.

본 드래프트는 1 차 결과만으로도 "기존 `top_tier` 파이프라인의 hybrid 모델
비교 결과(D ≫ A by ~0.05 macro-F1) 가 라벨 구간이 항상 2023 년 6 ~ 8 월
휴가 시즌에 고정된 시즌 confound 위에서 성립한 결과일 가능성이 높다" 는
결론에 도달한다. 시즌 정렬 라벨에서는 이 향상의 효과 크기와 통계적 유의성
이 모두 무너진다.

### 발견 3: 코로나 시기와 회복기 결과는 체계적으로 다르지 않다

§5.3 에서 2021 시작 panel 과 2022 시작 panel 의 평균 macro-F1 차이는
모든 윈도우 길이에서 0.02 이내다. 본 데이터에서 코로나 잔여 영향은 분류
정확도를 좌우하지 않는다. 미팅(전사 25:50 ~ 26:01) 에서 지도교수가
"이때가 또 코로나 기간이기도 하고" 라고 우려한 부분은 본 분석의 결론에
본질적 위협이 아니다.

다만 본 결과는 분류 정확도라는 한 차원에서의 결론이며, 라벨 분포 자체
(예: 2021 시작 panel 은 회복으로 인한 G 가 더 많고, 2022 시작 panel 은
라벨 균형이 다르다) 는 코로나 회복 과정에 영향을 받는다(§5.1). 따라서
"코로나 영향이 완전히 없다" 가 아니라 "분류 정확도에서는 작다" 가
정확한 해석이다.

### 발견 4: LightGBM tabular ensemble 은 RF 위에 일관된 추가 향상을 준다

§5.5.3 에서 동일 56 baseline 통계 피처 위의 LightGBM 이 RF 를 6 panel 중
5 개에서 능가하며 평균 +0.0075 macro-F1, 2 panel 에서 p<0.05 향상을 보였다.
이 향상은 §5.5 의 발견 2 (hybrid representation +0.0017) 와 비교해 **약
4 배 강하며** , Phase 5 외부 모델 14 종 (§5.6) 중 RF 를 능가하는 유일한
경우다.

향상의 sub-population 분해 (§5.5.3.1) 가 함의를 강화한다:

- tenure 가 길수록 Δ 가 단조 증가: Q1=+0.002 → Q4=+0.019 (전체의 2.4×).
- fragile cluster (Decline 17%) 에서 Δ = +0.044 (전체의 5.5×).
- 정책적 우선 대상 (오래된 + 위험 cluster) 에서 모델 향상이 가장 크다.

또한 LightGBM 의 의사결정 점수 (Decline 확률) 가 RF 보다 calibration 이
정확하다 (§5.5.3.2; Brier 0.097 vs 0.109, 11% 우위, top decile 관측 Decline
비율 0.348 = baseline 2.7× lift).

이는 M5 Walmart 정확도 대회 (Makridakis et al., 2022) 의 우승자 패턴
(LightGBM ensemble dominance) 이 SMB 단기 G/S/D 분류에도 전이됨을 의미한다.
sequence representation 의 추가 정보가 56 통계 피처에 거의 다 흡수된 본
데이터에서, RF 위로 가는 유일한 일반 경로는 같은 tabular feature 위의
GBDT ensemble 이다.

### 발견 5: stock-prediction SOTA 와 foundation model 은 SMB 단기 분류에 이식되지 않는다

§5.6 의 benchmark 에서 14 종 외부 모델 (foundation 3, stock SOTA 7, SMB
attention 3, RF cost-sensitive 변형 1) 중 **단 1 종 (LightGBM tabular) 을
제외한 모두가 RF baseline 에 패배** 했다. 효과 크기 분포는 다음과 같다:

- foundation models (TimesFM/Chronos/Moirai zero-shot): Δ = −0.19 ~ −0.27.
  거의 random guessing (F1 ≈ 0.33) 수준.
- stock SOTA 7 종 (TFT, N-BEATS, N-HiTS, PatchTST, DLinear, Informer,
  Autoformer): Δ = −0.14 ~ −0.26. DLinear 가 stock SOTA 1 위 (Zeng et al.,
  2023 의 "Transformer 무용론" 재현).
- SMB-specific attention 3 종 (FeatureAttnMLP, FiLM-tenure, TimeAttn):
  Δ = −0.035 ~ −0.092. FeatureAttnMLP 가 가장 RF 에 가까움.

본 발견은 부정 결과처럼 보이지만, 실제로는 본 학위논문의 main contribution
(시즌 정렬) 과 발견 2 (hybrid representation 조건부) 의 정당화 근거다 —
SMB 단기 G/S/D 분류는 기존 거대 시계열 literature 의 표준 방법론으로 풀
수 없는 별도 영역임을 정량으로 입증한다.

## 6.2 학문적 의의

### 6.2.1 라벨 시점 confound 의 정량 폭로

발견 1 은 거래 데이터 기반 점포 분류 연구가 빠지기 쉬운 함정을 정량
수준에서 드러낸다. forecasting / OOS 검증 문헌에서는 시즌 통제의 필요성
이 오랫동안 강조됐지만(Bergmeir & Benítez, 2012; Hyndman &
Athanasopoulos, 2021), 점포 단위 라이프사이클 분류 연구에서 80 + α 개
specification 수준의 robustness check 가 수행된 사례는 드물다. 본 연구의
시즌 정렬 rolling-window 설계는 이런 연구가 따라야 할 robustness 표준을
제안한다.

### 6.2.2 hybrid representation 의 외적 타당성 한계

발견 2 는 hybrid representation 의 향상 효과가 라벨 / 시즌 분포에 강하게
의존한다는 실증 증거다. KMeans cluster 와 change-point 는 시계열 분류
문헌(Paparrizos & Gravano, 2015; Truong et al., 2020) 에서 "거의 항상
도움이 된다" 는 톤으로 다뤄지지만, 본 연구는 라벨 정의가 깨끗할수록
baseline 통계 피처만으로도 거의 모든 정보를 흡수해 hybrid representation
의 추가 정보가 사라진다는 패턴을 보인다. 이 발견은 해당 representation 의
이론적 가치 자체를 부정하지 않지만, "어느 라벨에서 어느 정도 향상을 줄지"
를 사전에 예측할 수 없음을 시사한다.

### 6.2.3 라이프사이클 라벨의 정의 자체에 대한 재검토 필요

발견 1 과 발견 2 를 합치면 더 일반적인 함의가 도출된다. 같은 데이터·같은
모델이라도 라벨 정의가 다르면 학술적 결론(D ≫ A 인지, D ≈ A 인지) 이
바뀐다. 본 연구는 시즌 정렬을 한 가지 대안으로 제시했지만, 라벨 정의의
다양성과 그에 따른 결과 의존성을 명시적으로 다룬 라이프사이클 분류 연구는
여전히 부족하다. 이는 해당 분야의 reproducibility 한계 가능성을 시사한다.

### 6.2.4 stock-prediction SOTA 의 SMB 미이식 — 4 가지 mechanism 가설

발견 5 의 14 종 negative 패턴은 단순한 데이터 우연이 아니라 구조적 이유에서
비롯된다. 본 절은 본 분석으로부터 도출되는 4 가지 mechanism 가설을 정리
한다. 각 가설은 §7 future work 에서 검증 실험으로 확장 가능하다.

**(a) Short window 가설.** 본 데이터의 입력 윈도우는 13 ~ 31 주 (3 / 7 개월).
TimesFM/Chronos/Moirai 의 pretrain 데이터는 utility/retail/traffic daily
시계열 중심으로, 200 + timestep context 를 가정한다. Informer/Autoformer/
PatchTST 같은 long-horizon Transformer 도 96 ~ 720 timestep 에 맞춰 설계
됐다. 13 주에서 self-attention 헤드가 학습할 패턴 자체가 부족하다.

**(b) Regression-vs-classification 변환 손실 가설.** foundation 과 stock
SOTA 는 모두 raw value forecasting 으로 학습됐다. 본 연구는 forecast →
slope_norm → ±0.5σ bucket 으로 3-class 변환한다. 이 변환에서 forecast
의 노이즈가 직접 amplified 된다. §5.6 에서 DLinear (단순 linear projection)
가 stock SOTA 1 위였던 점은 — 가장 노이즈를 적게 amplify 하는 모델 — 본
가설과 정합한다.

**(c) Multivariate channel compression 가설.** 본 데이터는 6 채널 multivariate
(sales_card, customer, customer_new, before_noon, weekend, sales_delivery).
56 개 통계 피처 (slope_all, ma4_slope, vol_w8, sales_cv 등) 는 6 채널을
channel-aware 하게 압축하며, RF/LightGBM 의 split-gain 학습이 이 압축
representation 위에서 채널 간 비선형 상호작용을 잡는다. raw 6 채널 sequence
를 LSTM/Transformer 가 직접 학습하는 것보다, 통계 압축 + tree ensemble 이
더 효과적이다 (§5.6 의 SMB-attention 3 종 패배가 이를 입증).

**(d) Calendar season confound dominance 가설.** 발견 1 에서 시작월 진폭
(0.10) 이 다른 변수보다 한 자릿수 크다. stock 데이터 (장 개장 daily) 에는
calendar season 효과가 미미하지만, SMB 주간 매출은 명절·계절 효과가
결정적이다. 본 연구의 main contribution (시즌 정렬) 위에서만 RF baseline
이 0.50 으로 안정되며, raw sequence 위에 시즌 통제 없이 학습하는 모든
SOTA 는 시즌-confounded 신호와 lifecycle 신호를 분리하지 못한다.

이 4 가지 가설은 §7.2 의 후속 연구 (synthetic long-history ablation 등)
에서 정량 검증할 수 있다.

### 6.2.5 본 연구의 SMB-specific 차별화 5 가지 (stock literature 대조)

발견 5 와 §5.6 의 70 편 lit review (`260511/phase5_external/docs/stock_vs_
smb_literature.md`) 를 종합하면, 본 학위논문이 stock-prediction literature
와 차별화되는 5 가지 지점이 명확해진다.

1. **시즌 캘린더 정렬 (main contribution)**: stock literature 에는 거의
   없는 통제 — 본 연구의 v5 main.
2. **G/S/D 3-class 분류 + 회귀-후-버킷 비교**: 주식 literature 는 거의
   regression. 분류 접근의 우위 (Phase 1 의 ts_benchmark_compare.csv) 와
   변환 손실의 원인 (가설 b) 가 본 분석으로 정리된다.
3. **업력(tenure) cohort 효과**: stock 에는 없는 개념. 발견 4 의 LightGBM
   Q4_long Δ +0.019 와 §5.4 의 logit_coef 1.422 (Q4_long) 가 cohort 효과
   를 정량 입증.
4. **6 채널 multivariate + 매우 짧은 윈도우**: UCR / M5 와 다른 setup
   (가설 c).
5. **Spatial spillover negative**: 같은 동/업종 GNN 이 작동하지 않는다는
   별도 분석 (Phase 3, `260511/phase5_external` 외 영역) — stock 의 inter-
   stock correlation 과 대조.

## 6.3 실무 · 정책적 함의

본 연구의 결과는 카드 매출 데이터를 통한 점포 조기 진단이 다음 조건에서
의미 있음을 시사한다.

1. **라벨 시점이 명시적으로 시즌 통제될 때.** 단순히 "마지막 N 주" 라벨로
   조기 경보 모델을 학습한 결과를 그대로 정책 도구로 쓰는 것은 시즌 효과를
   라이프사이클 신호로 오인할 수 있다.
2. **라벨 분포가 편중된 시즌(예: 봄 · 초여름 회복 시즌) 에서 hybrid
   representation 의 추가 향상이 실용적 효과를 가질 수 있다.** 다만 본
   연구의 수치(Δ 0.005 ~ 0.012 Decline recall) 가 실무 의사결정 기준
   (예: 정책 지원 점포 선별 임계) 을 넘는지는 별도 비용·편익 분석이
   필요하다.
3. **점포 단위 분류 정확도(macro-F1 0.5 수준) 는 정책 처방이 아니라 우선
   검토 대상 좁히기 도구로 활용해야 한다.** recall 0.4 ~ 0.6 의 모델을
   자동화된 폐업 예측·금융 거절 시스템으로 직접 사용하는 것은 false
   positive 로 인한 점포 피해를 야기할 수 있다.
4. **LightGBM 의사결정 점수의 decile 활용** (§5.5.3.2). 본 데이터 EWS
   calibration 결과 top decile (상위 10% 위험) 의 관측 Decline 비율은
   34.8% 로 baseline (13%) 의 2.7×, 최저 decile 대비 17× spread 이다.
   정책 의사결정 시 "100% 명단" 이 아닌 "top decile 우선 검토" 형식의
   targeting 으로 활용하면, false positive 비용을 통제하면서 효율적 자원
   배분이 가능하다.
5. **fragile cluster (Decline 17%) 우선 적용.** §5.5.3.1 의 cluster 분해
   결과 LightGBM 의 우위가 fragile cluster 에서 가장 크다 (+0.044, 전체
   평균의 5.5×). 즉 모델 향상이 가장 절실한 영역에서 향상 폭도 가장 크다.

본 연구는 정책 처방이나 인과 효과를 주장하지 않는다.

## 6.4 한계

본 연구의 결과 해석에 다음 한계가 따른다.

1. **검정력 한계.** 5-fold paired t-test 의 자유도는 4 로, 효과 크기
   +0.002 macro-F1 정도의 작은 향상에 대한 검정력은 약하다. 향후 repeated
   CV (예: 10-fold × 10 repeats) 나 seed-multi bootstrap 을 통해 효과
   크기와 분산을 안정적으로 추정해야 한다(§5.6).
2. **단일 random seed.** 모든 결과는 seed=42 단일 시도. KMeans 초기화,
   stratified split, RandomForest 부트스트랩 모두 seed 에 의존한다.
3. **단순한 cluster / change-point 메서드.** KMeans k=6 은 elbow /
   silhouette 같은 cluster 수 결정 절차를 거치지 않은 상수 선택이며,
   change-point 는 max-mean-gap 단일 분할로 단순화된 구현(`top_tier` 의
   PELT 다중 변곡점 대비 정보 손실 가능). K-Shape, DTW-KMeans, Bayesian
   online change-point 같은 정교한 representation 으로 다시 측정하면 D − A
   효과 크기가 살아날 수 있다.
4. **외식업 한정.** 본 데이터는 서울시 외식업 점포만 포함한다. 도소매·
   서비스업의 시즌 패턴(예: 의류는 환절기 강한 시즌성) 은 다르며, 본
   연구의 시즌 효과 진폭(0.10) 이 다른 업종에서도 같은 크기로 나타날지는
   별도 검증이 필요하다.
5. **현금 결제 누락.** 카드 매출만 관측되므로 현금 비중이 큰 점포(전통
   시장 등) 의 분류 정확도가 체계적으로 떨어질 가능성이 있다.
6. **2 년 이상 panel 부족.** 본 데이터는 142 주(약 2.7 년) 이므로
   `target_offset=2` (2 년 후 같은 캘린더 월) panel 은 9 월 이후 시작월
   에서는 모두 데이터를 벗어난다. 더 긴 패널 데이터에서는 더 다양한 시즌
   비교가 가능하다. 더 긴 윈도우(8 / 12 개월) 도 같은 컷오프 제약으로
   본 분석에서 제외했다.

## 6.5 본 연구 범위 밖 (Future Work / 응용)

미팅(전사 18:00 ~ 22:55) 에서 지도교수와 합의한 대로, 다음 주제는 본
학위논문의 본문 contribution 에서 의도적으로 제외했다. 학위논문 디펜스
에서는 future work 로, 저널 확장 시에는 별도 contribution 으로 다룬다.

- **LEVI (Local Economic Vitality Index).** 자치구 단위 점포 라이프사이클
  종합 지표. 본 연구의 점포 단위 분류 결과를 자치구 단위로 집계해 서울시
  생활 인구 · 이동 인구 데이터와의 상관을 검증한 사전 분석이 있으나
  (`260430/docs/260430_levi_ews_paper_outline.md`), 본 학위논문 본문에는
  포함하지 않는다. 미팅에서 "LEVI 를 굳이 지금 입원할 필요는 없다" 는
  결정에 따른다.
- **EWS (Early Warning System).** 점포 단위 쇠퇴 위험 점수 기반 정책
  지원 우선순위 도구. 본 연구의 cluster + change-point 결과가 라벨 편중
  panel 에서만 의미 있으므로, EWS 의 cost-sensitive 의사결정 평가는 별도
  분석 frame 에서 다뤄야 한다. 미팅에서 "아카데믹 앵글이 아직 약하다" 는
  판단에 따라 본문에 포함하지 않는다.
- **외부 공공 데이터 5 종 추가 검증.** 서울시 카드 매출 공개 자료 등으로
  KCD 데이터의 외적 타당도를 보강한 사전 분석이 있으나, 본 학위논문 본문
  에는 포함하지 않는다. 미팅에서 "보강용으로 OK, 5 번은 괜찮음" 으로
  평가됐고 contribution 은 아니다.
- **신규 고객 유입의 매출 반등 선행성 시즌 panel 재검증.** Granger / PSM
  등 인과 기법으로 신규 고객 유입이 매출 반등을 선행한다는 분석이 있으나
  (Golden Cross), 시즌 정렬 panel 에서 이 선행성이 유지되는지는 본 연구의
  메인 모델 비교에 들어가지 않았다. 후속 연구의 우선순위 중 하나다.
- **Chronos / TimesFM LoRA finetune.** §5.6 의 foundation model zero-shot
  결과 (F1 = 0.23 ~ 0.31) 가 너무 약해 본문 비교에서는 zero-shot 만 다뤘다.
  본 데이터에 LoRA finetune 시 RF 근접 가능성은 낮지만 실험적 가치가
  있으며, 본문 외부의 future work 로 분리한다.
- **Cost-sensitivity dollar value sweep.** §6.3 항목 4 의 top-decile
  targeting 정책 권고를 한국 폐업 cost assumption 으로 환산해 정책 시나리오
  3 종 (lending, subsidy, intervention) 의 expected loss 표를 작성한다.
  본 학위논문 contribution 이 아닌 paper 확장 단계 (DSS) 의 핵심 자료.
- **Synthetic long-history ablation.** §6.2.4 의 가설 (a) "short window 가
  stock SOTA 패배의 원인인가" 를 분리 검증. raw weekly 에서 4 년 연속
  history 있는 stores subset 으로 같은 SOTA 를 재학습해 window × model
  매트릭스로 mechanism 정량 입증.

이 일곱 가지 주제는 본 학위논문의 본문 결론에 포함되지 않으며, 본 연구의
세 contribution(시즌 정렬 robustness 방법론, hybrid representation 의
조건부 contribution 발견, LightGBM 의 일관된 RF 우위 + 14 종 외부 SOTA
negative 의 SMB-specific 차별화 입증) 과 분리되어 다뤄진다.
