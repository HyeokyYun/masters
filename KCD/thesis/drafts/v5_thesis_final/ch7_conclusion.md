# 제7장 결론

## 7.1 요약

본 학위논문은 KCD 서울시 외식업 점포 약 5만 9천 개의 주간 카드거래 데이터
(2021-01-01 ~ 2023-08-28) 를 사용해, 영업 초기 1 ~ 7 개월의 거래 패턴이
이후 점포의 G/S/D 상태 분류에 어느 정도의 정보를 제공하는지 분석했다.
분석의 방법론적 핵심은 feature window 와 target window 를 같은 캘린더
월로 정렬한 시즌 통제 rolling-window 설계이며, 80 + α 개 specification
에서 baseline 정확도 분포와 14 개 대표 panel 에서 baseline + cluster +
change-point 의 hybrid representation 향상을 측정했다.

다섯 가지 주요 발견은 다음과 같다.

1. **시즌 confound 는 본 분석에서 가장 큰 설명 변수다.** 시작월에 따른
   macro-F1 진폭(0.10) 이 윈도우 길이 효과(0.02 ~ 0.04) 나 시작연도 효과
   (0.01 미만) 보다 한 자릿수 크다.
2. **hybrid representation 의 추가 향상은 14 개 panel 평균 +0.0017
   macro-F1, 5% 유의 1/14 panel 에 그쳐 라벨이 편중된 시즌·7 개월 윈도우
   에서만 살아남는 조건부 contribution 양상이다.** 14-panel 재집계로 1 차
   7-panel 결과 (+0.0022) 보다 추가 약화됐다.
3. **코로나 시기(2021 시작) 와 회복기(2022 시작) panel 의 정확도 차이는
   0.02 이내** 로, 코로나 영향은 본 분석의 결론을 좌우하지 않는다.
4. **LightGBM tabular ensemble 이 동일 56 baseline 통계 피처 위에서 RF 를
   일관되게 능가** 한다 (mean Δ = +0.0075, 5/6 panels wins, 2 p<0.05).
   per-cohort 분해 시 Q4_long 업력 cohort 에서 +0.019 (전체 평균의 2.4×),
   fragile cluster (Decline 17%) 에서 +0.044 (5.5×). EWS calibration 도
   LightGBM 이 RF 대비 Brier 11% 우위, top decile 관측 Decline 비율 0.348
   (baseline 2.7× lift).
5. **stock-prediction literature 의 SOTA 14 종 (foundation 3 + Transformer/
   linear 7 + SMB attention 3 + RF cost-sensitive 변형 1) 직접 적용 결과,
   LightGBM 1 종을 제외한 모두가 RF baseline 에 패배** (Δ = −0.035 ~
   −0.270, 6/6 panels p<0.001 대부분). DLinear 가 stock SOTA 1 위, TimesFM
   zero-shot 이 최약. SMB 단기 G/S/D 분류는 4 가지 mechanism (short window,
   classification 변환 손실, multivariate channel compression, calendar
   season confound) 으로 stock literature 와 차별화된 별도 regime 임이
   정량 입증된다.

본 연구는 세 가지로 기여한다. 시즌 정렬 rolling-window 설계는 라벨 시점
선택이 점포 분류 결과에 미치는 정량 효과를 80 + α specification 수준에서
폭로해, 거래 기반 라이프사이클 분류 연구가 따라야 할 robustness 표준을
제안한다. hybrid representation 의 조건부 향상 발견 (14-panel +0.0017) 은,
동일 데이터·동일 모델에서도 라벨 정의·윈도우 길이가 학술적 결론을 바꿀
수 있음을 보여 해당 분야의 reproducibility 한계에 경험적 자료를 제공한다.
stock-prediction SOTA 14 종 negative + LightGBM 1 종 positive 의 정량
benchmark 는 SMB 단기 G/S/D 분류의 SMB-specific 차별화를 4 가지 mechanism
가설과 함께 입증해, 본 학위논문의 첫 contribution (시즌 정렬) 의 정당화
근거를 강화한다.

## 7.2 후속 연구

본 학위논문의 결과를 안정화하고 확장하기 위한 후속 연구는 다음 네 가지로
정리된다.

1. **통계적 안정성 보강.** repeated CV (10-fold × 10 repeats) 와 seed-
   multi bootstrap 을 통해 D − A 효과 크기와 95% CI 를 더 안정적으로
   추정한다. 본 연구의 5-fold × seed=42 단일 시도는 효과 크기 +0.002 정도
   의 작은 향상에 대해서는 검정력이 약하므로, 안정화된 측정이 필요하다.
2. **신규 고객 유입 선행성의 시즌 정렬 재검증.** 신규 고객 유입이 매출
   반등을 선행한다는 기존 분석(Golden Cross) 을 시즌 정렬 panel 위에서
   다시 검정한다. 만약 시즌 통제 후에도 선행성이 안정적으로 유지된다면,
   본 학위논문의 두 contribution 에 더해 "시즌-robust 선행 신호" 라는
   세 번째 contribution 이 추가될 수 있다.
3. **메서드 정교화.** KMeans 대신 K-Shape 또는 DTW-KMeans, 단순 max-
   mean-gap change-point 대신 PELT 다중 변곡점 / Bayesian online change-
   point detection 을 사용해 본 연구의 D − A 결과를 다시 측정한다.
   메서드의 단순성이 효과 크기 약화의 원인일 가능성을 분리한다.
4. **외적 타당도 확장.** LEVI 도시경제 활력 지수, EWS 조기 쇠퇴 경보,
   외부 공공 데이터(서울시 카드 매출 공개 자료, 자치구 생활 인구) 등은
   본 학위논문의 본문 contribution 에서 분리됐으나, 저널 확장 단계에서
   시즌 정렬 panel 과 통합해 본 연구의 외적 타당도를 보강하는 contribution
   으로 발전시킬 수 있다.

## 7.3 마무리 메모

본 학위논문은 2026-04-30 / 2026-05-07 지도교수 미팅에서 명시적으로 제기된
쟁점 (시즌 confound, hybrid representation 일반화, 주식 예측 literature 와의
비교, 더 나은 prediction 가능성, feature weighting) 에 대한 정직한 실증
답안이다. 결과는 기존 D ≫ A 결론의 강도를 약화시키는 방향이지만, 이는
데이터·메서드의 결함이 아니라 정확한 robustness 검증의 결과로 이해되어야
한다. 동시에 LightGBM 의 일관된 RF 우위 (per-cohort 분해 시 fragile cluster
+0.044) 와 14 종 외부 SOTA 의 일관된 패배는, SMB 단기 G/S/D 분류가 stock-
prediction 의 거대 representation 학습 패러다임으로 풀 수 없는 별도 영역
임을 시사한다. 본 학위논문이 제안하는 시즌 정렬 표준과 SMB-specific
benchmark 가 후속 거래 기반 점포 분류 연구의 기본 프로토콜로 자리잡을 때,
본 분야의 결과 신뢰도와 정책 응용 가능성이 한 단계 올라갈 수 있을 것으로
기대한다.
