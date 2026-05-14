# 제 1 장 서론

## 1.1 연구 배경

소상공인은 한국 사업체 수의 약 92%, 고용의 약 47% 를 차지한다 (중소
벤처기업부, 2024). 코로나19 팬데믹 이후 정부와 지방자치단체는 점포
단위의 신용·세제 지원과 자영업자 안전망 확대를 추진했고, 그 일부 정책
은 점포의 영업 상태를 조기에 식별할 수 있는 데이터를 전제로 한다.
그러나 통계청과 행정안전부의 사업자 등록 통계는 폐업 신고 시점에야
점포의 종료를 잡고, 점포가 위축되는 과정에서의 매출·고객 흐름은 보이지
않는다.

카드 결제 데이터는 거의 실시간으로 점포의 영업 상태를 보여주는 거의
유일한 비행정 데이터다. 본 연구는 한국신용데이터(KCD) 가 보유한 약
5 만 9 천 개 서울시 외식업 점포의 주간 카드거래 패널을 분석 대상으로
삼는다. 데이터 기간은 2021-01-01 부터 2023-08-28 까지 총 142 주이며,
코로나 확산기와 엔데믹 회복기를 모두 포함한다.

본 연구의 분석 단위는 점포이며, 영업 초기 1 ~ 7 개월의 거래 패턴을
입력으로 받아 이후 점포가 Growth (성장) / Stable (유지) / Decline
(쇠퇴) 의 어느 상태로 가는지를 분류·예측한다. 본 분류 문제는 거래
기반 점포 진단의 일반화된 형식이지만, 본 연구가 직접 다루는 세 가지
방법론적 쟁점이 있다.

## 1.2 문제 의식

본 연구의 출발점은 **"초기 거래 패턴으로 점포의 G/S/D 를 얼마나 잘
예측할 수 있고, 어떤 요인·표현·모델이 그 예측을 개선시키는가"** 라는
prediction-oriented 질문이다. 이 질문은 다음 세 가지 하위 쟁점으로
분해된다.

### 1.2.1 누가 G / S / D 로 가는가 — 요인의 정체

거래 기반 점포 분류 연구는 macro-F1 같은 합집합 지표를 보고하지만,
어떤 sub-population (업력 cohort, KMeans cluster, 신규고객 유입 패턴)
이 어떤 lifecycle 결과로 흘러가는지에 대한 미시 분해는 자주 누락된다.
본 연구는 advisor 미팅(2026-04-30) 의 권유에 따라, cluster 와 cohort
가 G/S/D 분포를 어떻게 구조적으로 나누는지를 본문에서 보고한다.

### 1.2.2 라벨 정의의 시즌 confound

같은 데이터에서 "마지막 30 주" 또는 전체 기간 기울기로 G/S/D 라벨을
정의하면, 데이터 컷오프(2023-08-28) 직전 6 ~ 8 월 매출이 라벨 구간에
항상 들어간다. 6 ~ 8 월은 외식업의 휴가 시즌이므로, 라이프사이클 상의
"쇠퇴" 가 아니라 단순한 "휴가 시즌 이탈" 이 같은 라벨 안으로 묶이게
된다. 이 confound 는 모델 정확도와 신호 해석 양쪽에 영향을 준다.

### 1.2.3 예측 모델·표현의 개선 한계

기존 파이프라인은 baseline + KMeans 클러스터 + change-point 의 hybrid
representation 이 baseline 을 macro-F1 기준 약 +0.05 향상시킨다고
보고했으나, 이는 §1.2.2 의 시즌 confound 가 라벨 안에 들어가 있는
상태에서 얻은 결과다. 시즌을 통제한 라벨에서도 같은 향상 폭이 유지
되는지, 그리고 hybrid 외의 model novelty (cost-sensitive weighting, 시
계열 SOTA / LightGBM 등) 가 SMB 단기 G/S/D 분류에 실제로 도움이
되는지를 본 연구는 정량적으로 검토한다.

이 세 쟁점은 결국 "초기 거래 패턴 → G/S/D 예측" 이라는 prediction
질문 위에서 각각 (1) 요인 해석, (2) 라벨 robustness, (3) representation·
model 개선 의 세 축을 형성한다.

## 1.3 연구 질문

본 연구는 다음 네 개 연구 질문(RQ) 으로 구성된다.

- **RQ1 (baseline 과 요인 분해).** 영업 초기 1 ~ 7 개월의 카드거래
  패턴은 점포의 이후 G/S/D 상태를 어느 정도 예측할 수 있는가? 신규고객
  유입·업력 cohort·KMeans cluster 같은 미시 구조는 G/S/D 분포와 어떻게
  연결되는가?
- **RQ2 (label robustness).** feature window 와 target window 를 같은
  캘린더 월로 정렬한 시즌 통제 라벨에서, 시작월·윈도우 길이 변화가
  모델 정확도에 미치는 진폭은 어떠한가?
- **RQ3 (representation·weighting).** baseline 매출/고객 피처에
  KMeans 클러스터 라벨과 change-point 피처를 추가하면, 시즌 통제 후
  에도 baseline 대비 통계적으로 유의한 향상이 유지되는가? class-weight
  / cost-sensitive sample weighting 같은 보조 modification 은 Decline
  recall 을 추가로 개선하는가?
- **RQ4 (외부 SOTA transfer).** 시계열 예측 영역의 SOTA (foundation
  zero-shot · Transformer · LightGBM · SMB-attention 등) 14 종은 SMB
  단기 G/S/D 분류에 transfer 되는가? 코로나 확산기(2021 시작) 와
  회복기(2022 시작) 차이는 결과를 좌우하는가?

RQ1 은 prediction 의 baseline 정확도와 요인 구조를 본다. RQ2 는 §1.2.2
의 시즌 쟁점에, RQ3 는 §1.2.3 의 표현·가중 쟁점에, RQ4 는 §1.2.3 의
모델 선택 쟁점과 데이터 기간 통제에 답한다.

## 1.4 본 연구의 기여

본 연구는 다음 세 가지를 본문 기여로 제시한다. 모두 상위 RQ "초기
거래 패턴으로 G/S/D 를 어떻게 잘 예측할 것인가" 아래의 sub-component
다.

**기여 1 (prediction baseline 과 요인 분해).** 시즌 정렬된 G/S/D
예측의 baseline 정확도 (macro-F1 0.43 ~ 0.54) 와 동시에, 어떤 sub-
population 이 어떤 lifecycle 로 흘러가는지를 정량 보고한다. 구체적
으로 (a) 업력 4 분위 (Q1_short ~ Q4_long) × G/S/D 교차표와 신규고객
slope coefficient, (b) KMeans 6 cluster × G/S/D 교차표 (fragile cluster
Decline 17% ~ 60% vs survivor cluster Decline ~3%), (c) cluster 내
macro-F1 분포를 §5.7 ~ §5.8 에서 보고한다. 본 결과는 advisor 미팅의
"어떤 애들이 상승/유지/하락 인지 요인을 파악" 요청에 정량적으로 답한다.

**기여 2 (seasonal calendar alignment 으로서의 label robustness 전제).**
시즌 정렬 rolling-window 검증 설계를 145 개 specification 수준에서
구현하고, 라벨 시점 선택이 예측 정확도에 미치는 정량 효과를 보인다.
시작월에 따른 macro-F1 진폭(약 0.10) 이 윈도우 길이 효과(약 0.02 ~
0.04) 나 시작연도 효과(약 0.01) 보다 한 자릿수 크다는 결과는, 같은
데이터·같은 모델에서도 라벨 정의가 prediction 결론을 좌우할 수 있음
을 정량적으로 보여준다. 본 결과는 거래 기반 점포 분류 연구가 외적
타당도를 주장할 때 따라야 할 robustness 전제를 제안한다.

**기여 3 (세 가지 prediction-improvement 시도와 그 한계).** Prediction
정확도를 baseline 위에서 개선할 수 있는지 세 갈래로 검토한다. (a)
representation 측: baseline + cluster + change-point 의 hybrid 가
14 panel 평균 ΔF1 = +0.0017 의 **조건부 contribution** 으로 5% 유의
1/14 (Bonferroni 후 0/14, §5.5). (b) weighting 측: cost-sensitive
class-weight 보조 실험에서 Decline 가중치 조정의 효과를 §5.9 에서
보고. (c) model 측: 시계열 SOTA 14 종(foundation 3 + Transformer/linear
7 + SMB-attention 3 + cost-sensitive 변형 1) 중 LightGBM 1 종만 RF
baseline 을 능가, 나머지는 −0.035 ~ −0.270 패배 (§5.6). 본 세 갈래
결과는 SMB 단기 G/S/D 가 4 가지 mechanism (short window, classification
변환 손실, multivariate channel compression, calendar season confound)
으로 stock-prediction literature 와 차별화되는 별도 영역임을 정량
입증하며, advisor 미팅의 "technical novelty 시도" 와 "stock-prediction
literature 비교" 요청에 동시에 답한다.

LEVI 도시경제 활력 지수, EWS 조기 쇠퇴 경보, GNN 네트워크 모델 및
외부 공공 데이터와의 외적 타당도 검증은 본문 contribution 이 아니라
future work 으로 §6.5 및 §7.2 에서 다룬다 (2026-04-30 미팅 결정).

## 1.5 논문의 구성

제 2 장은 소상공인 라이프사이클, 거래 데이터 기반 점포 진단, 시계열
분류, 시즌 통제 robustness check 에 대한 선행연구를 정리한다. 제 3
장은 KCD weekly 패널의 구조와 변수, 전처리 절차를 기술한다. 제 4 장은
시즌 정렬 rolling-window 설계, G/S/D 라벨 생성, 가변 윈도우 피처
추출, A/B/C/D 모델 비교 프로토콜, cohort 정의, cost-sensitive 보조
실험 프로토콜을 설명한다. 제 5 장은 145 specification 의 baseline
결과와 14 대표 panel 의 A/B/C/D paired 비교, 업력·신규고객 cohort
분석(§5.7), cluster 요인 분해(§5.8), cost-sensitive 보조 실험(§5.9),
외부 SOTA 14 종 benchmark(§5.6) 를 보고한다. 제 6 장은 prediction
정확도의 한계, cohort·cluster 의 경제적 해석, 시즌 confound 의 함의,
hybrid·cost-sensitive·SOTA 세 갈래 개선 시도의 한계, 본 연구의
한계, LEVI/EWS/GNN/외부 공공 데이터의 future work 위치를 논의한다.
제 7 장은 결론과 다음 단계를 제시한다.
