# 제1장 서론

## 1.1 연구 배경

소상공인은 한국 사업체 수의 약 92%, 고용의 약 47% 를 차지한다(중소벤처
기업부, 2024). 코로나19 팬데믹 이후 정부와 지방자치단체는 점포 단위의
신용·세제 지원과 자영업자 안전망 확대를 추진했고, 그 일부 정책은 점포의
영업 상태를 조기에 식별할 수 있는 데이터를 전제로 한다. 그러나 통계청과
행정안전부의 사업자 등록 통계는 폐업 신고 시점에야 점포의 종료를 잡고,
점포가 위축되는 과정에서의 매출·고객 흐름은 보이지 않는다.

카드 결제 데이터는 거의 실시간으로 점포의 영업 상태를 보여주는 거의 유일한
비행정 데이터이며, 본 연구는 한국신용데이터(KCD) 가 보유한 약 5만 9천 개
서울시 외식업 점포의 주간 카드거래 패널을 분석 대상으로 삼는다. 데이터
기간은 2021-01-01 부터 2023-08-28 까지 총 142 주이며, 코로나 확산기와
엔데믹 회복기를 모두 포함한다.

본 연구의 분석 단위는 점포이며, 영업 초기 1 ~ 7 개월의 거래 패턴을
입력으로 받아 이후 점포가 Growth (성장) / Stable (유지) / Decline (쇠퇴) 의
어느 상태로 가는지를 분류한다. 이 형식은 거래 기반 점포 진단 분야에서
일반화된 형식이지만(Aladangady et al., 2021; Lee & Park, 2023), 본 연구가
직접 다루는 두 가지 방법론적 쟁점이 있다.

## 1.2 문제의식: 시즌 confound 와 hybrid representation 의 일반화

본 연구의 출발점은 2026-04-30 진행한 지도교수 미팅이다(전사:
`thesis/meeting_stt/260430_personal_meeting.txt`). 미팅에서 지도교수는 두
가지 쟁점을 명시적으로 제기했다.

**첫째, 라벨 정의의 시즌 confound.** 같은 데이터에서 "마지막 30 주" 또는
전체 기간 기울기로 G/S/D 를 정의하면, 데이터 컷오프(2023-08-28) 직전
6–8월의 매출이 라벨 구간으로 항상 들어간다. 6–8월은 외식업의 휴가 시즌
이므로, 라이프사이클상의 "쇠퇴" 가 아니라 단순한 "휴가 시즌 이탈" 이 같은
라벨 안으로 묶인다. 이 confound 는 모델 정확도와 신호 해석 양쪽에 영향을
준다.

**둘째, hybrid representation 의 일반화 가능성.** 기존 `top_tier` 파이프라인
은 baseline + KMeans 클러스터 + change-point 의 hybrid representation 이
baseline 을 macro-F1 기준 +0.05 이상 향상시킨다고 보고했지만, 이는 위와
같은 시즌 confound 가 라벨 안에 들어가 있는 상태에서의 결과다. 시즌을 통제
한 라벨에서도 같은 향상 폭이 유지된다는 보장이 없다.

이 두 쟁점은 동일한 데이터·동일한 모델에서도 라벨 정의 선택이 결론을 바꿀
수 있다는, 라이프사이클 예측 연구 일반의 외적 타당성 문제로 이어진다. 본
연구는 이 두 쟁점을 분리해 정량적으로 답한다.

## 1.3 연구 질문

본 연구는 다음 네 개의 연구 질문(RQ)으로 구성된다.

- **RQ1.** 영업 초기 1 ~ 7 개월의 카드거래 패턴은 점포의 이후 G/S/D 상태를
  어느 정도 예측할 수 있는가?
- **RQ2.** feature window 와 target window 를 같은 캘린더 월로 정렬한 시즌
  통제 라벨에서, 시작월·윈도우 길이 변화가 모델 정확도에 미치는 진폭은
  어떠한가?
- **RQ3.** baseline 매출/고객 피처에 KMeans 클러스터 라벨 및 change-point
  피처를 추가하면, 시즌 통제 후에도 baseline 대비 통계적으로 유의한 향상이
  유지되는가? 윈도우 길이를 1–3 개월에서 4 / 6 / 7 개월로 늘리면 향상 폭이
  변화하는가?
- **RQ4.** 코로나 시기(2021 시작 panel)와 회복기(2022 시작 panel) 에서
  결과가 체계적으로 달라지는가?

RQ1 은 거래 데이터로 라이프사이클 예측 자체가 가능한지를 묻는 기초 질문
이다. RQ2 와 RQ3 는 미팅에서 제기된 두 쟁점에 대한 실증적 답이다. RQ4 는
분석 기간(2021–2023) 이 코로나에서 회복기로 걸쳐 있다는 데이터 특수성에
대한 통제 질문이다.

## 1.4 본 연구의 기여

본 연구는 세 가지로 기여한다.

**기여 1 (방법론).** 시즌 정렬 rolling-window 검증 설계를 80 개 이상의
specification 수준에서 구현하고, 라벨 시점 선택이 라이프사이클 분류 결과에
미치는 정량 효과를 보인다. 시작월에 따른 macro-F1 진폭(0.10) 이 윈도우
길이 효과(0.02) 나 시작연도 효과(0.01 미만) 보다 훨씬 크다는 결과는, 같은
데이터·같은 모델에서도 라벨 정의가 모델 결론을 좌우할 수 있음을 정량적
으로 보여준다. 이는 거래 기반 점포 분류 연구가 OOS 검증을 도입할 때 따라
야 할 robustness 표준을 제안한다.

**기여 2 (실증 발견 — 조건부).** baseline + cluster + change-point 의
hybrid representation 이 시즌 통제 후에도 향상을 유지하는지를 14 개 대표
panel × Stratified 5-fold CV × paired t-test 로 검정한 결과, 평균 향상은
+0.0017 macro-F1 (7-panel 1 차 +0.0022 → 14-panel 재집계 +0.0017 로 추가
약화), 5% 유의 panel 은 1 개에 그친다. 윈도우 7 개월에서 가장 안정적
(+0.0030) 이지만 4 / 6 개월에서는 효과가 거의 사라진다. 이는 hybrid
representation 의 contribution 이 라벨/시즌 분포에 의존적이라는 **조건부
contribution** 이며, 기존 연구의 D ≫ A 결론이 외적으로 일반화되지 않을
수 있음을 시사한다.

**기여 3 (외부 SOTA 차별화).** 본 데이터에 stock-prediction literature 의
state-of-the-art 14 종 (TimesFM/Chronos/Moirai zero-shot, TFT/N-BEATS/
N-HiTS/PatchTST/DLinear/Informer/Autoformer, SMB-specific attention 변형
3 종) 을 직접 적용한 benchmark 에서, **단 1 종 (LightGBM tabular ensemble)
을 제외한 모두가 RF baseline 에 패배** 한다(Δ = −0.035 ~ −0.270, 대부분
6/6 panels p<0.001). LightGBM 은 평균 Δ = +0.0075 (M5 우승자 패턴 transfer)
이며 per-cohort 분해 시 Q4_long (업력 ≥ 9 년) +0.0189, fragile cluster
+0.044 로 sub-population 별 효과가 더 크다. 본 결과는 SMB 단기 G/S/D
분류가 stock-prediction literature 와 차별화되는 4 가지 mechanism (short
window, classification 변환 손실, multivariate channel compression, calendar
season confound) 을 보유한 별도 영역임을 정량 입증하며, 본 연구의 main
contribution (시즌 정렬) 의 정당화 근거를 제공한다.

LEVI 도시경제 활력 지수, EWS 조기 쇠퇴 경보, 외부 공공 데이터와의 외적
타당도 검증은 미팅에서 본문 contribution 이 아니라 future work / 응용으로
분리하기로 결정되었다(미팅 18:00 ~ 22:55). 본 연구는 이 결정을 따른다.

## 1.5 논문의 구성

제2장은 소상공인 라이프사이클, 거래 데이터 기반 점포 진단, 시계열 분류,
시즌 통제 robustness check 에 대한 선행연구를 정리한다. 제3장은 KCD
weekly 패널의 구조와 변수, 전처리 절차를 기술한다. 제4장은 시즌 정렬
rolling-window 설계, G/S/D 라벨 생성, 가변 윈도우 피처 추출, A/B/C/D 모델
비교 프로토콜을 설명한다. 제5장은 시즌 specification 의 baseline 결과와
대표 panel 의 A/B/C/D paired 비교 결과를 보고한다. 제6장은 시즌 confound
의 함의, hybrid representation 의 조건부 contribution, 본 연구의 한계,
LEVI / EWS / 외부 공공 데이터의 future work 위치를 논의한다. 제7장은 결론
과 다음 단계를 제시한다.
