# 제 7 장 결론

## 7.1 요약

본 학위논문은 KCD 서울시 외식업 점포 약 5 만 9 천 개의 주간 카드
거래 데이터(2021-01-01 ~ 2023-08-28, 142 주) 를 사용해, 영업 초기
1 ~ 7 개월의 거래 패턴이 이후 점포의 G/S/D (Growth / Stable / Decline)
상태 분류·예측에 어느 정도의 정보를 제공하는지를 분석했다. 상위
연구 질문은 **"초기 거래 패턴으로 G/S/D 를 얼마나 잘 예측할 수 있고,
어떤 요인·표현·모델이 그 예측을 개선시키는가"** 라는 prediction-first
질문이며, 그 아래에 (1) baseline 예측·요인 분해, (2) 시즌 정렬을 통한
label robustness 전제, (3) representation·weighting·model 세 갈래
개선 시도의 세 sub-component 가 위치한다.

일곱 가지 주요 발견은 다음과 같다.

1. **Prediction baseline 정확도.** 시즌 정렬된 145 specification 의
   macro-F1 은 0.43 ~ 0.55 범위에 분포한다 (§5.2). 14 대표 panel 의
   A baseline (43 통계 피처) macro-F1 평균은 약 0.50 으로, 균등 random
   guess (~0.33) 대비 17 pp 향상이지만 정책 처방용 정확도 수준은
   아니다.
2. **시즌 confound 의 정량적 진폭.** 시작월에 따른 macro-F1 진폭(약
   0.10) 이 윈도우 길이 효과(0.02 ~ 0.04) 나 시작연도 효과(0.01 미만)
   보다 한 자릿수 크다 (§5.2 ~ §5.4). 라벨 시점 선택이 prediction
   결론을 좌우할 수 있음이 정량 수준에서 입증된다.
3. **Hybrid representation 의 조건부 contribution.** baseline + cluster
   + change-point 의 D 모델은 14 panel 평균 ΔF1 = +0.0017, 5% 유의
   1 / 14 (Bonferroni 보정 후 0 / 14, §5.5). 효과가 살아남는 영역은
   7 개월 윈도우 또는 라벨 편중 panel 에 국한된다.
4. **Cost-sensitive 가중의 한계.** RF + Decline×2/×3 은 6 / 6 panel
   에서 RF baseline 대비 5% 유의 *하락* (ΔF1 = −0.035 ~ −0.063,
   §5.9). LightGBM + Decline×2 도 LGB baseline 대비 미세 손해 (−0.005).
   Sample weighting 만으로는 prediction 향상이 어렵다.
5. **외부 SOTA 14 종 negative + LightGBM 1 종 positive.** Foundation
   zero-shot 2 종, stock SOTA 7 종, SMB-attention 3 종, cost-sensitive
   2 종 중 LightGBM 패밀리 (3 종) 만 RF 를 능가하며 (lgbm_tabular ΔF1
   = +0.0075, 2/6 p<0.05), 나머지 11 종은 모두 RF 에 패배 (ΔF1 = −0.035
   ~ −0.246; §5.6). DLinear 가 stock SOTA 1 위, TFT / N-BEATS / Chronos
   가 가장 약하다.
6. **업력 cohort 별 신규고객 → Growth 의 logit 연관 단조성.** 업력이
   길어질수록 신규고객 유입의 logit β 가 안정·일관적이고, LightGBM
   의 RF 대비 향상도 단조 증가 (Q1_short +0.0021 → Q4_long +0.019,
   §5.7). 본 결과는 advisor 미팅의 "신규 유입·업력이 주요 요인"
   권유에 대한 정량 답이다.
7. **KMeans cluster 의 fragile / survivor 이원 구조.** 6 cluster 는
   panel 간 cluster 번호가 바뀌어도 Decline 35 ~ 60% 의 fragile
   cluster 와 Decline ≤ 13% 의 survivor cluster 의 이원 구조를 재현
   한다 (§5.8). LightGBM 의 RF 대비 향상은 fragile cluster 에서
   +0.044 로 평균의 약 5.9 배이며, 정책 우선 영역과 모델 향상의 여지
   가 일치한다.

본 학위논문은 다음 세 가지를 본문 contribution 으로 제시한다.

**기여 1 (prediction baseline 과 요인 분해).** 시즌 정렬된 G/S/D
예측의 baseline 정확도 (macro-F1 0.43 ~ 0.55) 와 함께, 업력 4 분위
cohort × G/S/D 교차표 / KMeans 6 cluster × G/S/D 분포 / cluster 내
macro-F1 분해 / cohort 별 신규고객 logit 회귀를 본문에서 보고한다.
"누가 G / S / D 로 가는가" 의 미시 구조를 보임으로써 advisor 미팅
의 "어떤 애들이 상승/유지/하락 인지 요인을 파악" 권유에 직접 답한다.

**기여 2 (seasonal calendar alignment 의 label robustness 전제).**
145 specification 에서 시작월 진폭(0.10) ≫ 윈도우 길이 효과(0.02
~ 0.04) ≫ 시작연도 효과(0.01 미만) 을 입증해, feature window 와
target window 를 같은 캘린더 월·길이로 정렬하는 rolling-window 검증
설계가 거래 기반 점포 분류 연구의 label robustness 전제임을 정량
제안한다.

**기여 3 (세 갈래 prediction-improvement 시도와 SMB-specific 차별화).**
representation 측 (hybrid 의 조건부 +0.0017), weighting 측 (cost-
sensitive 의 음(−) 효과), model 측 (외부 SOTA 14 종 중 1 종만 RF 능가)
의 세 갈래 결과는, SMB 단기 G/S/D 분류가 4 가지 mechanism (short
window, classification 변환 손실, multivariate channel compression,
calendar season confound) 으로 stock-prediction literature 와 차별화
되는 별도 영역임을 정량 입증한다.

LEVI 도시경제 활력 지수, EWS 조기 쇠퇴 경보, GNN 네트워크 모델 확장,
외부 공공 데이터와의 외적 타당도 검증은 advisor 미팅 결정에 따라
본문 contribution 이 아닌 future work (§6.5, §7.2) 로 분리한다.

## 7.2 후속 연구

본 학위논문의 결과를 안정화하고 확장하기 위한 후속 연구는 다음 네
가지로 정리된다.

1. **통계적 안정성 보강.** repeated CV (10-fold × 10 repeats) 와
   seed-multi bootstrap 을 통해 ΔF1 효과 크기와 95% CI 를 더 안정적
   으로 추정한다. 본 연구의 5-fold × seed = 42 단일 시도는 ΔF1 +0.002
   정도의 작은 향상에 대해 검정력이 약하므로, 안정화된 측정이 필요
   하다.
2. **GNN / 네트워크 확장 본격화.** 본 연구의 `gnn_compare.csv` pilot
   은 행정동 / 업종 / hybrid 그래프 위 GCN 이 RF 대비 ΔF1 = −0.04 ~
   −0.10 으로 패배함을 보였다. 그래프 정의 (이웃 점포 선택, edge
   weight, 시간 의존성) 와 message passing layer / heterogeneous GNN /
   spatial-temporal GNN 등 본격적 architecture grid 가 필요하다. 본
   확장은 advisor 미팅의 "네트워크 모델 추가 (GNN 등)" 권유의 본
   격적 후속이다.
3. **Cohort × cluster 인과 효과 분석.** §5.7 의 신규고객 → Growth
   logit 회귀와 §5.8 의 fragile cluster 분포는 모두 관찰적 결과다.
   PSM, IV, Synthetic control 같은 인과 추정 기법으로 본 연구의 미시
   구조를 인과 효과로 확장하는 작업은 별도 연구 frame 에서 다뤄야
   한다. 시즌 정렬 panel 위에서 신규고객 유입의 매출 반등 선행성
   (Golden Cross) 을 다시 검정하면 "시즌-robust 선행 신호" 라는 세
   번째 contribution 후보가 추가될 수 있다.
4. **외적 타당도 확장.** LEVI 도시경제 활력 지수, EWS 조기 쇠퇴 경보,
   외부 공공 데이터(서울시 카드 매출 공개 자료, 자치구 생활 인구) 등
   은 본 학위논문의 본문 contribution 에서 분리되었으나, 저널 확장
   단계에서 시즌 정렬 panel 과 통합해 본 연구의 외적 타당도를 보강
   하는 contribution 으로 발전시킬 수 있다.

## 7.3 마무리

본 학위논문은 **"초기 거래 패턴으로 G/S/D 를 어떻게 잘 예측할 것
인가"** 라는 prediction-first 질문 위에서, 라이프사이클 예측 연구의
세 가지 외적 타당성 쟁점 — (1) 누가 G/S/D 로 가는가 (cohort·cluster
요인), (2) 라벨 시점의 시즌 confound, (3) representation·weighting·
model 세 갈래 개선의 한계 — 에 정직한 실증 답을 제시한다.

결과는 prediction 정확도 향상이 단순한 모델 교체나 sample weighting
이 아니라 (i) 라벨 정의의 시즌 통제 위에서, (ii) 업력·신규고객·cluster
같은 미시 구조 안에서 차별화된 개선의 형태로만 가능하다는 점을
보여준다. 동시에 외부 시계열 SOTA 14 종 중 LightGBM 1 종만 RF 를
능가하는 일관된 패턴은 — SMB 단기 G/S/D 분류가 stock-prediction 의
거대 representation 학습 패러다임으로 풀 수 없는 별도 영역임을
정량적으로 입증한다.

본 학위논문이 제안하는 (a) prediction baseline 과 요인 분해 frame,
(b) 시즌 정렬 rolling-window 검증 표준, (c) hybrid·cost-sensitive·외부
SOTA 세 갈래 개선의 SMB-specific 차별화 frame 이 후속 거래 기반
점포 분류 연구의 기본 프로토콜로 자리잡을 때, 본 분야의 결과 신뢰
도와 정책 응용 가능성이 한 단계 올라갈 수 있을 것으로 기대한다.
