<!--
원본: 260516_overleaf_en/chapters/ch1_introduction.tex
번역일자: 2026-05-22
-->

# Chapter 1 — Introduction (국문 번역)

## §1.1 연구 배경 (Research Background)

소상공인은 한국 경제의 사업체 수에서 압도적 다수를 차지하며, 동시에 거시 충격에 가장 먼저 반응하는 부문이다. 2023년 기준 전국 770만 사업체 중 약 695만 곳, 전체의 **약 90%** 가 소상공인으로 분류되며 \cite{kostat2024smb,mossme2024smb}, 총 고용에서도 상당한 비중을 차지한다. 이 부문은 세 가지 구조적 특성을 공유한다: (i) 자본·노동 capacity의 제약 \cite{cassar2004financing}, (ii) 외부 충격(수요 변동, 임차료 상승, 감염병, 플랫폼 환경 변화)에 대한 약한 완충 능력, (iii) 폐업과 재진입의 빠른 회전 \cite{stinchcombe1965social,bartelsman2005,parker2009economics}.

특히 2020–2022년의 COVID-19 충격은 외식업을 포함한 대면 서비스 소상공인에 **비대칭적·누적적 타격**을 가했다. 미국 PPP(Paycheck Protection Program)의 targeting 분석 \cite{granja2022ppp}이 보여주듯, 위기 상황에서 소상공인 대상 정책 자원의 **효과적 배분(effective allocation)** 문제는 결국 *어느 점포가 회복하고 어느 점포가 쇠퇴할지* 를 **사전에 정량적으로 식별**할 수 있는가의 문제로 귀결된다.

그러나 개별 점포가 매출에서 어떻게 성장·안정·쇠퇴하는지를 **직접 관찰**하는 일은, 가용 데이터의 시계열 길이와 단일 점포 식별 가능성에 의해 역사적으로 제약을 받아 왔다. 한국신용데이터(KCD) \cite{kcd2024manual}와 같은 데이터 공급자가 다년·점포-주 단위 카드 거래 패널을 최근에야 누적함으로써, 미시 수준의 점포 동태를 정량 분석하는 일이 비로소 가능해졌다 \cite{kim2021smb,lee2023kcd}.

본 학위논문은 KCD의 서울 외식업 약 59,000개 점포 주간 카드 매출 패널(2021년 1월–2023년 8월, 142주)을 이용하여, 각 점포의 매출 동태를 **Growth / Stable / Decline (G/S/D)** 로 분류하고, 이 상태와 연관된 점포·시장 수준 요인을 식별하며, **초기 거래 윈도우 feature** 로 이 상태를 예측할 수 있는지를 단일 실증 파이프라인에서 평가한다.

---

## §1.2 Research Gap

본 논문은 기존 문헌의 세 가지 격차를 다룬다. **첫째**, 현상 분석과 예측 모델링이 분리된 연구 전통으로 이어져, 회귀에서 유의한 변수가 예측 모델의 representation 단계로 잘 연결되지 않는 문제(§1.2.1). **둘째**, 범용 시계열 예측 모델이 규칙적 샘플링·비교적 동질적 시계열을 가정하여 주간·이질 단면의 소상공인 매출에 직접 전이되지 않는 문제(§1.2.2). **셋째**, 같은 상권 내 인접 점포 간의 공간–산업 의존성이 점포 매출 예측에 제한적으로만 활용되어 온 문제(§1.2.3).

### §1.2.1 현상 분석과 예측 모델링의 분리

기존 소상공인 연구는 *매출 성장·쇠퇴에 어떤 변수가 관련되는가* 의 질문을 횡단면 회귀 또는 생존 분석으로 접근해 왔다 \cite{gimeno1997survival,davidsson2003role,audretsch2005knowledge}. 이들은 인적 자본·자본 구조·입지·업종이 사업체 생존에 미치는 영향에 대해 강한 증거를 제공하지만, **확인된 변수가 예측 모델의 representation 단계로 그대로 이어진 사례** 는 드물다. 반대로 시계열 기반 매출 예측 연구 \cite{salinas2020deepar,fawaz2019deeplearning}는 series 자체의 패턴 학습에 뛰어나지만, 그 패턴의 **원인 해석** 은 부차적으로 다루는 경향이 있다.

본 논문은 두 흐름을 **단일 파이프라인** 에서 통합한다. 점포 수준 회귀·코호트 분석으로 매출 성장과 연관된 변수(영업기간, 신규 고객 비율 등)를 식별한 뒤, 이 변수를 예측 모델의 representation 단계에 **직접** 투입한다. 이로써 *"설명력이 있는 변수가 예측에도 유용한가?"* 라는 오랜 질문에 본 데이터셋 기준의 정량적 증거를 제공한다.

### §1.2.2 일반 시계열 모델의 제한된 이식성

최신 시계열 예측 모델 — Temporal Fusion Transformer \cite{lim2021tft}, N-BEATS \cite{oreshkin2020nbeats}, PatchTST \cite{nie2023patchtst}, Chronos-Bolt \cite{ansari2024chronos}, Moirai \cite{woo2024moirai} 등 — 은 표준 예측 벤치마크에서 강력한 성능을 보이지만, 일반적으로 **규칙적으로 샘플링된** 시계열과 **비교적 동질적·연속적인 단면** 을 가정한다. 이들을 소상공인 매출에 직접 이식하는 것은 단순하지 않다: 본 데이터는 **주간**이고, 점포 간(업종·동·영업기간·고객 구성) **이질성이 크며**, 잦은 불연속을 동반해 정상성·잡음 구조·불연속 빈도가 벤치마크 환경과 모두 다르다 \cite{hyndman2021forecasting,bergmeir2012use,elsayed2021dlmodels}. 우리는 14개 비-LightGBM 비교 모델을 동일 데이터 분할 위에서 직접 벤치마크(§5.7)함으로써 이 불일치를 정량화하고, 제한된 이식성을 데이터 특성의 관점에서 해석한다.

### §1.2.3 공간–산업 확장에 대한 제한된 증거

기존 점포 수준 매출 예측은 일반적으로 각 점포의 *시간적* 시계열만을 본다. 그러나 같은 동네의 점포들은 유동인구·상권 충격을 공유하고, 같은 업종의 점포들은 트렌드·계절성을 공유한다 \cite{jacobs1969economy,glaeser2010agglomeration}. 이 *공간–산업 의존성* 이 점포 매출 예측에 추가 마진을 줄 수 있는지는 엄밀하게 검증되지 않았다.

우리는 그래프 신경망 \cite{kipf2017semi,velickovic2018graph}을 이용한 **예비적** 비교 분석(§6.3)으로 이를 다루며, 이는 메인 예측 프레임워크가 아니라 확장·robustness 차원의 실험이다. 비교 결과 자체를 넘어, *어떤 그래프 구성과 가중치 학습 방법이 본 데이터의 공간 신호를 포착할 수 있는가* 에 대한 정량적 출발점을 제공하는 것이 목표다.

---

## §1.3 Research Questions

위 격차를 다루기 위해 네 개의 RQ를 제기한다.

- **RQ1 (현상 분석 — 점포 수준).** 어느 점포가 Growth/Stable/Decline으로 분류되는가? 영업기간, 신규 고객 비율, 고객 구성 등 어떤 요인이 통계적으로 유의한가? 그 효과의 방향·크기·일관성은 영업기간 코호트 별로 어떠한가?
- **RQ2 (현상 분석 — 업종 × 동).** 업종 × 동 조합 수준에서 Growth 비율이 높은 조합과 Decline 비율이 높은 조합의 분포는 어떠한가? 단순 업종 평균 또는 동 평균에 의해 가려지는 *공간 × 산업 상호작용* 은 얼마나 큰가?
- **RQ3 (예측).** 점포의 초기 거래 윈도우 feature로부터 Growth/Stable/Decline 상태를 얼마나 정확히 예측할 수 있으며, 운영·고객 구성·궤적 형상·cluster·change-point feature를 결합한 hybrid representation이 운영 baseline 대비 예측을 얼마나 향상시키는가? 동일 representation 위에서 Random Forest vs LightGBM 중 어느 분류기가 더 적합한가? 보완적 ablation으로, 궤적 형상 feature가 더 엄격한 이항 큰 폭 성장 결과(관측구간 첫/끝 분기 매출 2배)를 식별하는지도 검토한다.
- **RQ4 (Robustness).** 예측 결과가 (a) 다양한 시즌·시기의 시즌 정렬 rolling panel 위에서, (b) 14개 비-LightGBM 비교 모델 + 예비 GNN 대비 안정적인가? 불안정 지점이 있다면 어떻게 해석되는가?

---

## §1.4 Contributions

기여는 네 가지로 요약된다.

- **Contribution 1 — G/S/D 현상 분석의 정합적 구성.** 회귀를 통해 점포 수준에서 영업기간과 신규 고객 비율을 유의 변수로 식별하고, 이를 업종 × 동 수준의 G/S/D 분포로 확장하여 해석 가능한 현상 맵(map)을 제시한다. 신규 고객 슬로프의 Growth 로짓 계수는 단기-영업기간 코호트에서 **+2.026** 에 달하며, 모든 코호트에서 양의 부호를 유지한다 (§\ref{sec:significant_vars}). 나아가 패널 고정효과 분석은 신규 고객 유입이 평균적으로 매출 반등에 *선행* 함(lag1 계수 +0.278)을 보여, 이 연관에 시간적 패턴을 부여한다 (§\ref{sec:golden_cross}).
- **Contribution 2 — 궤적 형상 feature가 운영 변수를 넘어서는 설명적 정보를 더한다.** 보완적 큰 폭 성장 ablation(관측구간 첫/끝 분기 매출 2배, G/S/D 본 과제와 분리 평가)에서 궤적 형상 feature가 가장 뚜렷한 신호를 보인다. 17 변수 운영 baseline에 매출 곡선 형상 feature(P1/P2 변곡 슬로프, 변곡 주차) + UDX 코드(Up/Down 패턴) 더미를 더하면 큰 폭 성장 점포 식별의 이항 $F_1$이 RF에서 **0.539→0.642**, XGBoost에서 **0.681→0.818** 로 상승한다 (§\ref{sec:taskA_ablation}). 이는 매출 곡선 **형상** 이 관측구간 성장 결과에 대한 상당한 정보를 담고 있음을 시사한다 (단일 80/20 stratified holdout; UDX 코드가 궤적을 사후 요약하므로 forward predictive power의 직접 향상이 아닌 explanatory로 해석; 해석 범위는 §\ref{sec:limitations}).
- **Contribution 3 — 시즌 정렬 G/S/D 예측의 평가.** 시즌 정렬 삼항 Growth/Stable/Decline task(3개월 feature·target)에서 cluster + change-point hybrid representation은 RF baseline 대비 제한적이지만 부호가 일관된 개선을 제공하며(§\ref{sec:taskB_main}), 모델 선택이 더 분명한 차이를 만든다: **LightGBM 계열** 이 동일 representation 위에서 RF를 일관되게 능가한다(패널별 델타·유의성 검정은 §\ref{sec:rf_vs_lgbm}). 이 우위는 데이터 특성의 관점에서 해석한다.
- **Contribution 4 — robustness와 모델 이식의 경계 조건.** 시즌 정렬 패널 전반에서 모델의 macro-$F_1$이 **0.43–0.54 범위** 로 유지됨(낮은 시기 의존성; §6.1)을 보이고, 제안 representation을 14개 비-LightGBM 비교 모델(§\ref{sec:phase5}) 및 예비 GNN(§6.3)과 비교·평가한다. 이 비교들은 범용 예측 모델과 네트워크 기반 접근이 본 데이터에서 아직 성능을 개선하지 못하는 경계 조건을 드러내며, 이를 데이터 빈도·이질성·그래프 표현의 관점에서 해석한다.

---

## §1.5 Scope and Non-Scope

본 결과는 다음 범위 안에서 해석되어야 한다.

**In Scope.**

- 서울의 외식업 약 59,000개 점포.
- 2021년 1월–2023년 8월, 142주의 주간 카드 매출 시계열.
- 관찰 기간 내 매출 동태의 G/S/D 분류 (**절대적 폐업 시점 예측 아님**).
- representation 단계에서의 hybrid 통합과 분류기 선택의 정량적 비교.

**Out of Scope.**

- **인과 추론.** "영업기간이 G/S/D에 **설명력** 을 가진다"를 보이지, "영업기간이 G/S/D에 **인과적** 으로 영향을 미친다"를 보이지 않는다. 인과 추론은 별도의 식별 전략(IV, RDD, DID)을 요한다.
- **폐업 시점 예측.** G/S/D 라벨은 매출 동태의 분류이며, 절대적 폐업 사건과 1:1로 대응되지 않는다. 폐업 시점 예측은 별도(예: 생존 분석) framework의 후속 연구로 남긴다.
- **비외식·비수도권.** 효과 크기와 모델 비교 결과가 다른 업종·지역으로 일반화되는지는 별도의 external validity 검증을 요한다.
- **현금 및 배달 플랫폼 매출.** 데이터는 카드 매출에 국한되며, 현금·배달 매출은 일부만 반영된다.

---

## §1.6 Terminology

본 논문 전체에서 사용되는 핵심 용어는 다음과 같다.

- **G/S/D 라벨.** target window 내 점포의 매출 동태를 반영하는 (Growth, Stable, Decline) 중 하나이며, 정규화 추세 슬로프를 패널별 임계값($\pm 0.5\sigma$)에 견주어 정의된다 (§3.3).
- **Macro-$F_1$.** 클래스별 $F_1$(precision과 recall의 조화평균)의 산술 평균이며, 모든 클래스에 동일 가중치를 부여한다. 클래스 불균형 하에서 어느 한 클래스가 무시되는 것을 방지한다 (§3.4).
- **Season-Aligned Panel.** 학습 기간과 평가 기간이 동일한 달력 단위(분기 또는 동일 길이 윈도우)로 정렬된 평가 데이터셋. 계절 효과를 통제 변수가 아닌 **설계로** 제거한다 (§6.1).
- **Hybrid Representation.** 매출 시계열 통계량, 점포 메타데이터, 고객 구성 신호를 단일 feature 벡터로 결합한 입력 표현 (§5.2).
- **Fragile Cluster.** Decline 비중이 두꺼우며 cluster 내부 macro-$F_1$이 가장 낮은 KMeans cluster. 정책 및 조기 경보 적용에서 1차 표적이 된다 (§5.5).

---

## §1.7 Organization of the Thesis

남은 부분은 다음과 같이 구성된다. **Chapter 2** 는 소상공인 매출 동태·생애주기 연구, 시계열 예측 방법론, 그래프 신경망, hybrid representation learning에 관한 문헌을 검토하고 본 연구를 그 안에 위치시킨다. **Chapter 3** 은 KCD 카드 매출 데이터의 구조, 서울 외식업으로 한정한 근거, G/S/D 라벨 정의, macro-$F_1$ 채택의 근거, 학습·평가 분할 프로토콜을 기술한다. **Chapter 4 (Phenomenon Analysis)** 는 (i) 점포 수준 요인 분석과 (ii) 업종 × 동 수준 분포 분석을 다룬다. **Chapter 5 (Prediction)** 는 예측 스토리를 하나의 흐름으로 전개한다: 운영 baseline을 세운 뒤 hybrid representation이 예측을 얼마나 개선하는지를 보이며 — 특히 큰 폭 성장 타깃에서 매출 곡선 형상(변곡점 + UDX) feature가 이항 $F_1$을 0.642/0.818로 끌어올린다 (§§5.1–5.2); 이어 시즌 정렬 삼항 G/S/D task에서 cluster + change-point hybrid representation과 구조적 RF vs LightGBM 비교 (§§5.3–5.4), 영업기간 코호트·KMeans cluster 별 마진 분해 (§§5.5–5.6), 14개 비-LightGBM 비교 모델 외부 비교와 cost-sensitive 보조 실험 (§§5.7–5.8)을 보고한다. **Chapter 6 (Robustness)** 은 (i) 시즌 정렬 rolling panels, (ii) 외부 시계열 비교의 robustness 재확인, (iii) 예비 그래프 신경망 비교를 통해 결과 안정성을 검증한다. **큰 폭 성장 결과의 외부 타당성은 한계와 후속 연구 항목(§\ref{sec:limitations})으로 다룬다.** **Chapter 7** 은 결과를 종합하고 학술적·실무적 함의, 한계, 향후 연구 방향(공간-시간 hybrid model, 업종/지역 확장, 멀티모달 신호 통합, 조기 경보 시스템 확장)을 논의한다.
