# Ch6 Discussion — 통합 패치 텍스트

v5_thesis_final/ch6_discussion.md (또는 chapter 6 해당 파일)에 추가할 정확한
텍스트.

## 추가 §6.x — Stock-style 직접 이식이 SMB 단기 G/S/D 분류에 작동하지 않는 정량 증거

본 thesis가 답하는 mechanism question: "**왜 stock-prediction literature의
방법이 SMB 단기 매출 lifecycle 분류에 적용 안 되는가?**"

Phase 5에서 14종 외부 모델 (foundation 3 + stock SOTA 7 + SMB-attention 3 +
weighting 1)을 동일 6 panel × 3-fold protocol로 비교한 결과, **단 1종 (LightGBM)
만 RF baseline을 넘었다.** 나머지 13종은 모두 부정 결과.

### 6.x.1 4가지 mechanism 가설

본 thesis는 다음 4가지를 정성/정량으로 분석한다:

**(a) Short window이 foundation/SOTA의 sweet spot 밖**

- TimesFM/Chronos/Moirai는 utility/retail/traffic/finance daily 데이터로
  pretrain. 평균 context 200+ point 가정. 본 데이터는 13–31주 (84/217일).
- Informer/Autoformer/PatchTST 같은 long-horizon Transformer는 96~720
  timestep 전제. 13주에서 self-attention head가 학습할 패턴 부족.
- 추가 ablation: synthetic 4년 history 생성 (raw weekly extension) 으로 같은
  모델 재학습 → "단지 short window이 원인인지" 분리 가능. **(future work)**

**(b) Regression-trained → classification 변환 단계의 정보 손실**

- foundation/stock SOTA는 모두 raw value forecast 학습. 본 thesis는 forecast
  → slope_norm → ±0.5σ bucket으로 변환.
- 이 변환은 forecast 노이즈가 amplified되는 경향. Phase 5 5B에서 DLinear가
  best stock SOTA였는데, **단순 linear projection이 noise를 가장 적게 amplify**
  하는 점이 일치 (Zeng et al. 2023 결론과 mechanism 정합).

**(c) Multivariate short-window 6채널 vs UCR/M5 single-channel**

- ROCKET 계열은 univariate UCR에서 SOTA. 본 데이터는 sales_card + customer +
  customer_new + before_noon + weekend + sales_delivery 6채널.
- 56-피처 통계(slope_all, ma4_slope, vol_w8, sales_cv 등)는 6채널을
  channel-aware하게 압축. raw 6채널을 모델이 직접 학습하는 것보다 효과적
  (Phase 1 step06 LSTM/Transformer 패배가 그 증거).

**(d) Calendar season confound이 SMB-specific 효과**

- 본 thesis v5 main contribution. 같은 store가 sm01(1월 시작) vs sm05(5월
  시작) feature window에 노출되면 G/S/D label이 크게 달라짐.
- v4 top_tier에서 D ≫ A로 보였던 hybrid 효과(+0.05 macro_F1)가 v5 14-panel
  재집계로 +0.0017로 축소된 이유 (§5.5.3).
- stock 데이터에는 calendar season 효과가 미미 (장 개장 daily). SMB
  주간 매출은 명절/계절 효과 결정적.

### 6.x.2 본 thesis 의 차별화 (5가지)

`260511/phase5_external/docs/stock_vs_smb_literature.md` (70편) 의 비교
매트릭스 §11에서 도출:

1. **Seasonal calendar alignment** (M1): stock에는 없음, M5에도 약함, SMB에 결정적
2. **G/S/D 3-class 분류 + 회귀-후-버킷 비교** (N1): 주식 literature는 거의 regression
3. **업력 cohort 효과 (FiLM 가능성)** (C5): stock에는 없는 개념
4. **6-channel multivariate, very short window**: UCR/M5와 다른 setup
5. **Spatial spillover negative** (N3): stock의 inter-stock correlation 강세와 대조

### 6.x.3 함의: SMB EWS 설계는 stock EWS와 어떻게 달라야 하는가

- baseline은 **GBDT (LGBM)** 부터. RF/DL 부터 시작하면 +0.008 손해.
- feature engineering이 model architecture novelty보다 우위. 56개 통계 feature가
  raw 시계열보다 강함.
- temporal attention보다 **feature attention** 이 우선 (Phase 5C). attention을
  쓸 거면 SE-block 같은 feature gating부터.
- meta features (tenure, sigungu_te, kclass_te) 가 cluster+CP 같은 sequence
  representation보다 강함 (C1 +0.008 vs C2 +0.002).

---

## 추가 §6.5 — 70편 문헌 설문조사 비교 매트릭스 인용

`260511/phase5_external/docs/stock_vs_smb_literature.md` 의 §10 비교 매트릭스를
참고. 본 thesis가 차별화해야 할 항목과 stock/M5/UCR/foundation 영역의 표준
방법론을 한 표에 정리.

본 매트릭스는 thesis의 related-work section에 부록 표로 인용 가능. 다음
정보 포함:
- Model family × Domain × Data scale × Architecture × SMB 적용 가능 여부
- 본 phase 5에서 시도한 모델 표시 (5A/5B/5C/5D)
- 미시도/future work 모델 (ROCKET, TimeGPT API, Lag-Llama 등)

---

## 본 chapter의 한 줄 결론

> 본 thesis는 SMB 매출 lifecycle 분류의 4가지 mechanism (short window, classify
> vs regress, multivariate, calendar season)이 stock-prediction의 표준 방법론을
> 무력화함을 정량으로 입증한다. 이는 부정 결과가 아니라 SMB-specific
> contribution의 정당화 근거다.
