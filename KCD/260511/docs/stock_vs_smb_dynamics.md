# 주식 시계열 예측 vs 소상공인 매출 시계열 예측 — 구조적 차이 (Phase 4 / D2)

본 문서는 2026-05-07 미팅 피드백을 반영하여, 주식 가격 예측 literature와 소상공인 매출
예측이 본질적으로 어떻게 다른지를 정리한다. 비교의 목적은 "왜 주식 모델을 그대로
가져오면 안 되는가"와 "소상공인 매출 예측에 추가로 필요한 요소가 무엇인가"를 명확히
구분해 본 연구의 contribution을 위치 짓는 것이다.

## 1. 본질적 시계열 특성 차이

| 차원 | 주식 (대형주) | 소상공인 매출 (KCD) |
|---|---|---|
| 관측 단위 | 1 종목 = 1 시계열, 길이 수년~수십년 | 1 점포 = 1 시계열, 길이 평균 1.5–4년 (`tenure_log` 분포) |
| 관측 빈도 | 분/일 단위 고해상도 | 주 단위 (집계 노이즈 큼) |
| 결측 | 거의 없음 (휴장 외) | 매우 흔함 (개점 전, 휴업, 영업 시간 변경) |
| 정상성 | 약한 정상성 가정 가능 (return 기반) | 비정상; 생애주기·계절성·외생충격 동시 작동 |
| 외생 충격 | 매크로 이벤트가 전 종목에 동기적 | 일부 동·업종에만 비동기 충격 (코로나 영업제한, 상권 재개발 등) |
| 자기상관 | 약한 양/음의 lag-1 상관 | feature window의 trend가 target window에 어느 정도 보존됨 (slope_*) |
| 노이즈 비율 | 가격 자체의 microstructure noise | 주 단위 매출 변동성이 매우 큼 (vol_w4, vol_w8) |

## 2. 도메인 세팅 차이

| 차원 | 주식 | 소상공인 매출 |
|---|---|---|
| 예측 대상 | 다음 close, return, 변동성 | 다음 분기 매출 슬로프(상승/유지/하락) |
| 의사결정 단위 | 트레이더/포트폴리오 매니저 | 점주, 정책 입안자, 가맹본부 |
| 손실 함수 | sharpe, MSE, directional accuracy | macro_F1 (클래스 불균형) |
| 라벨 정의 | 자명 (수익률 부호) | 정의 자체가 연구 대상 (Phase 0 sweep) |
| 경쟁자 | HFT/quant, 시장 참가자 다수 | 도메인 모델/관행 → 베이스라인이 약함 |

## 3. 모델링 함의 (Why stock models don't directly transfer)

1. **생애주기 효과 (lifecycle)**: 주식은 보통 stable 운영 기업; 소상공인은 개업 → 성장 →
   포화 → 쇠락의 라이프사이클이 핵심. 예측이 정확하려면 `tenure_log`(업력) 같은
   생애주기 메타정보가 입력에 필요하다. **본 연구의 A2 실험**에서 정량화.
2. **계절성 confound**: 같은 모델도 panel의 시작 월에 따라 라벨 분포가 크게 다름
   (5월 시작 panel은 D=25%, 1월 시작 panel은 D=8%). 주식에는 이런 캘린더 의존
   라벨 분포가 거의 없다. **본 연구의 main contribution(seasonal alignment)** 이
   바로 이 confound 통제.
3. **공간 spillover**: 주식 종목 간 cross-asset 상관은 인덱스/섹터 채널이지만,
   소상공인 매출은 같은 골목, 같은 동네의 다른 점포가 직접 고객 점유를 나눠 갖는
   spillover가 가설적으로 존재. 주식의 cross-asset GNN은 attention/correlation 그래프인
   반면, 소상공인의 GNN은 **공간/업종 ground truth 그래프**가 자연스럽게 존재.
   **본 연구 Phase 3 (step08_train_gnn.py)** 가 이를 검증.
4. **클래스 불균형**: 주식 return은 대체로 0 부근 정규에 가까움; 소상공인 매출 슬로프는
   생애주기 단계에 따라 크게 비대칭. macro_F1 평가가 필수.
5. **희소성/scale**: 주식 종목 수는 수천~수만이지만 거래 데이터가 풍부. 소상공인은
   점포 수가 많지만 점포당 시계열이 짧고 zero-inflation이 있음. 주식의 deep TS
   모델(Informer/Autoformer/PatchTST)은 긴 시퀀스를 가정하므로 fine-tuning 없이는
   직접 사용 불가.

## 4. 본 연구의 D1 baseline 위치

| 모델 | 카테고리 | macro_F1 (예정) |
|---|---|---|
| naive_last_slope | 통계적 외삽 | (pending) |
| linear_extrap | 통계적 외삽 | (pending) |
| ARIMA / Prophet | 고전 TS | (pending) |
| LSTM / GRU / TCN | 일반 시계열 NN | (pending) |
| Transformer encoder | 주식 PatchTST류와 가장 유사 | (pending) |
| RF on tabular 56 features | tabular baseline | (이미 0.48–0.50) |
| RF + meta (tenure 등) | 도메인 정보 추가 | (pending) |
| GCN on dong/industry/hybrid | 공간 spillover | (pending) |

표는 step06/07/08 결과로 자동 채워짐.

## 5. 결론 골격 (서사)

- 주식 예측 literature의 시퀀스 모델은 "긴 정상 시계열의 단기 변동을 예측"한다.
- 소상공인 매출 예측은 "짧고 비정상 시계열의 (G/S/D) 분기 결정"이며, 추가로
  (a) 생애주기, (b) 계절성, (c) 공간 spillover 라는 도메인 신호가 모델 입력에
  명시적으로 포함되어야 한다.
- 본 연구는 (b) seasonal alignment를 main contribution으로, (a) tenure/meta 통합과
  (c) 공간 GNN spillover를 conditional contribution으로 제시한다.
