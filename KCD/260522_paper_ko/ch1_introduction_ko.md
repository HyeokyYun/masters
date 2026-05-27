<!--
원본: 260516_overleaf_en/chapters/ch1_introduction.tex
번역일자: 2026-05-22
-->

# Chapter 1 — Introduction (국문 번역)

## §1.1 연구 배경 (Research Background)

소상공인은 한국 경제의 사업체 수에서 압도적 다수를 차지하며 거시 충격에 가장 먼저 반응하는 부문이다. 2023년 기준 전국 770만 사업체 중 약 695만 곳(약 90%)이 소상공인으로 분류되며 \cite{kostat2024smb,mossme2024smb}, 총 고용에서도 상당한 비중을 차지한다. 이 부문은 (i) 자본·노동 capacity 제약 \cite{cassar2004financing}, (ii) 외부 충격에 대한 약한 완충, (iii) 폐업·재진입의 빠른 회전 \cite{stinchcombe1965social,bartelsman2005,parker2009economics} 이라는 구조적 특성을 공유한다. 따라서 어느 점포가 성장·안정·쇠퇴할지를 식별하는 것은 표적 정책 지원, 플랫폼 기반 모니터링, 조기 경보 분석에 중요하다.

그러나 이러한 경제적 중요성에도, 개별 점포의 매출 동태 예측은 상당한 기술적 난제다 — 주간 거래 데이터가 극심한 단면 이질성, 국지적 노이즈, 잦은 샘플링 불연속을 보이기 때문이다.

어려움은 제도적일 뿐 아니라 기술적이다. 거시 지표·상장사 성과·대형 유통 체인과 달리, 개별 소상공인 매출은 매우 국지적 규모에서 관측되며 단기 충격에 강하게 좌우된다. 점포 수준 시계열은 업종·구·영업기간·고객 구성에 걸쳐 매우 이질적이고, 주별 변동이 크며, 일시 휴업·공휴일·플랫폼 이벤트 등으로 자주 불연속이다. 이런 데이터 특성은 길고 매끄럽고 비교적 동질적인 시계열을 암묵적으로 기대하는 예측 접근에 미시 점포 매출이 잘 맞지 않게 만든다.

COVID-19는 이 문제를 가시화했다: 위기 시 지원 배분은 결국 회복할 점포와 쇠퇴할 점포를 사전에 구분할 수 있는가에 달려 있으며, 이는 미국 PPP(Paycheck Protection Program) 분석 \cite{granja2022ppp} 같은 소상공인 targeting 연구가 보여준다. 동시에 이러한 동태를 직접 관찰하는 일은 제한된 시계열 길이와 점포 식별자의 부재로 역사적으로 제약돼 왔다. 한국신용데이터(KCD) \cite{kcd2024manual} 등이 다년·점포-주 단위 카드 거래 패널을 최근 누적함으로써 미시 점포 동태를 정량 분석하는 일이 비로소 가능해졌다 \cite{kim2021smb,lee2023kcd}.

본 학위논문은 KCD의 서울 외식업 약 59,000개 점포 주간 카드 매출 패널(2021년 1월–2023년 8월, 142주)을 이용하여, 각 점포의 매출 동태를 **Growth / Stable / Decline (G/S/D)** 로 분류하고, 이 상태와 연관된 점포·시장 수준 요인을 식별하며, 초기 거래 윈도우 feature로 이를 예측할 수 있는지를 평가한다. 핵심 목표는 기존 예측 알고리즘을 새 데이터에 단순 적용하는 것이 아니라, 도메인 특화 현상을 식별해 예측 representation에 직접 반영하는 것이다.

---

## §1.2 Research Gap

본 논문은 기존 문헌의 세 가지 격차를 다룬다. **첫째**, 현상 분석과 예측 모델링이 분리된 연구 전통으로 이어져, 회귀에서 유의한 변수가 예측 모델의 representation 단계로 잘 연결되지 않는 문제(§1.2.1). **둘째**, 범용 시계열 예측 모델이 더 규칙적·동질적 시계열을 위해 개발되어, 주간·이질 단면 소상공인 매출에 대한 유용성이 불확실한 문제(§1.2.2). **셋째**, 같은 상권 내 인접 점포 간의 공간–산업 의존성이 점포 매출 예측에 제한적으로만 활용되어 온 문제(§1.2.3).

### §1.2.1 현상 분석과 예측 모델링의 분리

기존 소상공인 연구는 *매출 성장·쇠퇴에 어떤 변수가 관련되는가* 의 질문을 횡단면 회귀 또는 생존 분석으로 접근해 왔다 \cite{gimeno1997survival,davidsson2003role,audretsch2005knowledge}. 이들은 인적 자본·자본 구조·입지·업종이 사업체 생존에 미치는 영향에 대해 강한 증거를 제공하지만, **확인된 변수가 예측 모델의 representation 단계로 그대로 이어진 사례** 는 드물다. 반대로 시계열 기반 매출 예측 연구 \cite{salinas2020deepar,fawaz2019deeplearning}는 series 자체의 패턴 학습에 뛰어나지만, 그 패턴의 **원인 해석** 은 부차적으로 다루는 경향이 있다.

본 논문은 두 흐름을 **단일 파이프라인** 에서 통합한다. 점포 수준 회귀·코호트 분석으로 매출 성장과 연관된 변수(영업기간, 신규 고객 비율 등)를 식별한 뒤, 이 변수를 예측 모델의 representation 단계에 **직접** 투입한다. 이로써 *"설명력이 있는 변수가 예측에도 유용한가?"* 라는 오랜 질문에 본 데이터셋 기준의 정량적 증거를 제공한다.

### §1.2.2 미시 규모 예측에서의 architecture–data 불일치(Mismatch)

최신 시계열 예측 모델 — Temporal Fusion Transformer \cite{lim2021tft}, N-BEATS \cite{oreshkin2020nbeats}, PatchTST \cite{nie2023patchtst}, Chronos-Bolt \cite{ansari2024chronos}, Moirai \cite{woo2024moirai} 등 — 은 표준 예측 벤치마크에서 강력하지만, 그 벤치마크와 모델 가정은 본 연구의 데이터 환경과 완전히 맞지는 않는다. 주간 점포 매출은 짧은 이력, 큰 단면 이질성, 불규칙한 국지 충격, 잦은 불연속을 결합하므로 정상성·잡음 구조·불연속 빈도가 범용 forecaster가 흔히 평가되는 더 매끄럽거나 규칙적인 시계열과 다르다 \cite{hyndman2021forecasting,bergmeir2012use,elsayed2021dlmodels}. 본 논문은 이 불일치를 가정이 아니라 실증 문제로 다룬다. 동일 G/S/D task 위에서 도메인 특징 tabular representation을 14개 비-LightGBM 비교 모델과 비교한다(§5.7). 이 비교는 그 모델들이 보편적으로 약하다고 주장하기 위함이 아니라, off-the-shelf 시간 구조 모델이 이 특정한 노이즈·불연속·점포 수준 환경에서 가치를 더하는지를 검증하기 위함이다. 범용 시간 모델은 신규 고객 유입·영업기간·국지 상권 구성 같은 도메인 운영 맥락이 명시적으로 표현되지 않으면 이를 충분히 활용하지 못할 수 있다. 그 결과는 본 논문의 핵심 강조점을 뒷받침한다: 본 데이터에서는 관측된 사업 현상에 근거한 representation 설계가 모델 architecture 자체보다 더 중요할 수 있다.

### §1.2.3 공간–산업 확장에 대한 제한된 증거

기존 점포 수준 매출 예측은 일반적으로 각 점포의 *시간적* 시계열만을 본다. 그러나 같은 동네의 점포들은 유동인구·상권 충격을 공유하고, 같은 업종의 점포들은 트렌드·계절성을 공유한다 \cite{jacobs1969economy,glaeser2010agglomeration}. 이 *공간–산업 의존성* 이 점포 매출 예측에 추가 마진을 줄 수 있는지는 엄밀하게 검증되지 않았다.

우리는 그래프 신경망 \cite{kipf2017semi,velickovic2018graph}을 이용한 **예비적** 비교 분석(§6.3)으로 이를 다루며, 이는 메인 예측 프레임워크가 아니라 확장·robustness 차원의 실험이다. 비교 결과 자체를 넘어, *어떤 그래프 구성과 가중치 학습 방법이 본 데이터의 공간 신호를 포착할 수 있는가* 에 대한 정량적 출발점을 제공하는 것이 목표다.

---

## §1.3 Research Questions

위 격차를 다루기 위해 네 개의 RQ를 제기한다.

- **RQ1 (현상 분석 — 점포 수준).** 어느 점포가 Growth/Stable/Decline으로 분류되는가? 영업기간, 신규 고객 비율, 고객 구성 등 어떤 요인이 통계적으로 유의한가? 그 효과의 방향·크기·일관성은 영업기간 코호트 별로 어떠한가?
- **RQ2 (현상 분석 — 업종 × 구).** 업종 × 구 조합 수준에서 Growth 비율이 높은 조합과 Decline 비율이 높은 조합의 분포는 어떠한가? 단순 업종 평균 또는 구 평균에 의해 가려지는 *공간 × 산업 상호작용* 은 얼마나 큰가?
- **RQ3 (예측).** 점포의 초기 거래 윈도우 feature로부터 Growth/Stable/Decline 상태를 얼마나 정확히 예측할 수 있으며, 운영·고객 구성·**패널 내부 시퀀스 cluster**·change-point feature를 결합한 hybrid representation이 추가로 주는 마진은(있다면) 얼마인가? 동일 representation 위에서 Random Forest vs LightGBM 중 어느 분류기가 더 적합한가? 보완적 설명 ablation으로, **전구간(full-span) 궤적 형상 feature**가 더 엄격한 이항 큰 폭 성장 결과(관측구간 첫/끝 분기 매출 2배)를 식별하는지도 검토한다.
- **RQ4 (Robustness).** 예측 결과가 (a) 다양한 시즌·시기의 시즌 정렬 rolling panel 위에서, (b) 14개 비-LightGBM 비교 모델 + 예비 GNN 대비 안정적인가? 불안정 지점이 있다면 어떻게 해석되는가?

---

## §1.4 Contributions

기여는 네 가지로 요약된다.

- **Contribution 1 — G/S/D 동태의 현상→예측 통합.** 회귀로 점포 수준에서 영업기간과 신규 고객 비율을 유의 변수로 식별하고, 이를 업종 × 구 수준 G/S/D 분포로 확장해 해석 가능한 현상 맵을 제시한다. 신규 고객 슬로프의 Growth 로짓 계수는 단기-영업기간 코호트에서 **+2.026**, 모든 코호트에서 양의 부호를 유지한다(§\ref{sec:significant_vars}). 패널 고정효과 분석은 신규 고객 유입이 평균적으로 이후 매출 반등과 양으로 연관됨(lag1 계수 +0.278)을 보여 이 연관에 시간적 패턴을 부여한다(§\ref{sec:golden_cross}). 이 발견들은 별도의 기술적 작업으로 남기지 않고, 예측 representation에 쓰이는 고객 구성·영업기간·업종·구 변수의 근거가 된다.
- **Contribution 2 — G/S/D 예측에서 representation 대 architecture 증거.** 시즌 정렬 삼항 G/S/D task(3개월 feature·target)에서 도메인 특징 baseline이 이미 가용 신호 대부분을 포착한다. 패널 내부 cluster·change-point feature 추가는 RF baseline 대비 제한적 평균 이득에 그치는 반면(§\ref{sec:taskB_main}), 모델 선택의 차이는 더 분명하다: LightGBM 계열이 동일 representation에서 RF 대비 양의 평균 마진을 보인다(§\ref{sec:rf_vs_lgbm}). 더 넓은 비교에서 14개 비-LightGBM 비교 모델은 RF reference를 넘지 못한다(§\ref{sec:phase5}). 이를 도메인 특화 representation 설계가 더 복잡한 범용 시간 architecture 채택만큼 중요하다는 데이터 특정적 증거로 해석한다.
- **Contribution 3 — 보완적 설명 ablation으로서의 궤적 형상 feature.** 보완적 큰 폭 성장 ablation(관측구간 첫/끝 분기 매출 2배, G/S/D 본 과제와 분리 평가)에서 전구간 궤적 형상 feature가 가장 뚜렷한 신호를 보인다. 17 변수 운영 baseline에 매출 곡선 형상 feature(P1/P2 변곡 슬로프, 변곡 주차) + UDX 코드(Up/Down 패턴) 더미를 더하면 큰 폭 성장 식별 이항 $F_1$이 RF에서 **0.539→0.642**, XGBoost에서 **0.681→0.818** 로 상승한다(§\ref{sec:taskA_ablation}). UDX 코드가 궤적을 사후 요약하므로 이는 forward predictive power의 직접 향상이 아니라 explanatory로 해석한다(해석 범위 §\ref{sec:limitations}).
- **Contribution 4 — 시즌 정렬 robustness와 경계 조건.** 메인 G/S/D 결과를 시즌 정렬 rolling panel, 외부 비교 모델, 예비 그래프 신경망으로 평가한다. 시즌 정렬 패널 전반 macro-$F_1$이 **0.43–0.54 범위** 로 유지되며(§\ref{sec:seasonal_rolling}), 그래프 비교는 메인 예측 프레임워크가 아니라 경계 조건 점검으로 쓴다(§6.3). §\ref{sec:phase5}의 비-LightGBM 비교와 함께, 이 분석들은 제안한 tabular representation이 안정적인 지점과 추가적 시공간 모델링이 향후 과제로 남는 지점을 밝힌다.

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
- **Fragile Cluster.** Decline 비중이 두꺼우며 cluster 내부 macro-$F_1$이 가장 낮은 매출 궤적 cluster. 정책 및 조기 경보 적용에서 1차 표적이 된다 (§5.5).

---

## §1.7 Organization of the Thesis

남은 부분은 다음과 같이 구성된다. **Chapter 2** 는 소상공인 매출 동태·생애주기 연구, 시계열 예측 방법론, 그래프 신경망, hybrid representation learning에 관한 문헌을 검토하고 본 연구를 그 안에 위치시킨다. **Chapter 3** 은 KCD 카드 매출 데이터의 구조, 서울 외식업으로 한정한 근거, G/S/D 라벨 정의, macro-$F_1$ 채택의 근거, 학습·평가 분할 프로토콜을 기술한다. **Chapter 4 (Phenomenon Analysis)** 는 (i) 점포 수준 요인 분석과 (ii) 업종 × 구 수준 분포 분석을 다룬다. **Chapter 5 (Prediction)** 는 예측 스토리를 하나의 흐름으로 전개한다: 운영 baseline을 세운 뒤 hybrid representation이 예측을 얼마나 개선하는지를 보이며 — 특히 큰 폭 성장 타깃에서 매출 곡선 형상(변곡점 + UDX) feature가 이항 $F_1$을 0.642/0.818로 끌어올린다 (§§5.1–5.2); 이어 시즌 정렬 삼항 G/S/D task에서 cluster + change-point hybrid representation과 구조적 RF vs LightGBM 비교 (§§5.3–5.4), 영업기간 코호트·매출 궤적 cluster 별 마진 분해 (§§5.5–5.6), 14개 비-LightGBM 비교 모델 외부 비교와 cost-sensitive 보조 실험 (§§5.7–5.8)을 보고한다. **Chapter 6 (Robustness)** 은 (i) 시즌 정렬 rolling panels, (ii) 외부 시계열 비교의 robustness 재확인, (iii) 예비 그래프 신경망 비교를 통해 결과 안정성을 검증한다. **큰 폭 성장 결과의 외부 타당성은 한계와 후속 연구 항목(§\ref{sec:limitations})으로 다룬다.** **Chapter 7** 은 결과를 종합하고 학술적·실무적 함의, 한계, 향후 연구 방향(공간-시간 hybrid model, 업종/지역 확장, 멀티모달 신호 통합, 조기 경보 시스템 확장)을 논의한다.
