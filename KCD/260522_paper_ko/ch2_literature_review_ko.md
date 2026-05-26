<!--
원본: 260516_overleaf_en/chapters/ch2_literature_review.tex
번역일자: 2026-05-22
-->

# Chapter 2 — Literature Review (국문 번역)

본 장은 본 학위논문을 네 갈래의 문헌 흐름 안에 위치시킨다: (i) 소상공인 매출 동태와 생애주기 연구, (ii) 시계열 예측 방법론, (iii) 그래프 신경망 기반 시계열 예측, (iv) hybrid representation learning. 각 흐름의 핵심 가정을 식별하고 본 데이터와의 적합성을 평가함으로써, 이후 장에서 내릴 분석적 선택의 근거를 제공한다.

---

## §2.1 소상공인 매출 동태와 생애주기 연구

기존의 소상공인 부문 연구는 이론적 토대와 분석 단위에 따라 세 갈래로 정리할 수 있다.

### §2.1.1 조직 생태학과 사업체 생존

조직 생태학은 새롭게 설립된 조직의 생존 또는 실패를 결정하는 요인에 대한 사회학·경제학 이론으로, *liability of newness* \cite{stinchcombe1965social}와 *density dependence* \cite{hannan1989organizational} 같은 가설을 발전시켜 왔다. liability-of-newness 가설은 *기업이 설립 직후 외부 충격에 더 취약하다*는 입장으로, 본 논문에서 Q1_short(단기 영업기간) 코호트에서 Decline 비중이 두꺼운 결과(§\ref{sec:significant_vars})와 정합한다. density-dependence 가설은 *같은 업종·지역의 기업 밀도가 개별 생존율에 영향을 미친다*는 입장으로, 본 논문의 업종 × 동 G/S/D 분포 이질성(§\ref{sec:industry_dong})의 이론적 배경을 제공한다.

### §2.1.2 생존 분석 기반 폐업·생존 예측

미시 수준의 사업체 데이터가 점차 가용해지면서, OECD 사업체 인구통계 데이터를 횡단면과 시계열로 통합한 국가 간 비교 연구가 등장하였다 \cite{bartelsman2005,parker2009economics}. 이 갈래는 (i) Cox 비례 위험 모형 등으로 신규 사업체의 *생존 함수*와 *위험률(hazard rate)*을 추정하고, (ii) 인적 자본(설립자 학력·경력) \cite{davidsson2003role,gimeno1997survival}, 자본 구조 \cite{cassar2004financing}, 지역 지식 파급 \cite{audretsch2005knowledge}이 사업체 생존에 미치는 영향을 정량화하는 데 초점을 둔다. 최근 정책 응용의 예로는 COVID-19 기간 미국 PPP(Paycheck Protection Program)의 targeting 적합성 분석 \cite{granja2022ppp}이 있다.

이 갈래는 어떤 사업체가 더 오래 생존하는지에 대한 **설명**에는 강하지만, 본 논문이 초점을 두는 단기 매출 동태 변화의 **예측**과 직접 연결되지 않는다. 본 논문의 라벨은 절대적 "폐업" 사건이 아니라 *관찰 윈도우 내 G/S/D 상태*이므로, 본 연구는 생존 분석과 구별되며 폐업 시점 예측은 후속 연구(§\ref{sec:limitations})로 남긴다.

### §2.1.3 한국 소상공인에 대한 미시 수준 시계열 기반 연구

한국에서는 미시 수준 카드 매출 데이터의 가용성 증가에 따라, KCD \cite{kcd2024manual}, 행정안전부·통계청 \cite{kostat2024smb,mossme2024smb}, 서울신용보증재단 \cite{kim2021smb,lee2023kcd}과 같은 데이터를 활용한 자영업자 매출 변동성·추세 연구가 빠르게 확장되어 왔다. 이 갈래는 시계열 자체의 패턴 학습에는 뛰어나지만, *어떤 변수가 그러한 패턴을 만들어내는가*에 대한 설명은 부차적으로 다루는 경향이 있다.

본 논문은 위 세 갈래를 **단일 분석 파이프라인**에서 통합한다. 점포 수준 회귀·코호트 분석으로 매출 성장과 연관된 변수(영업기간, 신규 고객 비율 등)를 식별한 뒤, 이를 예측 모델의 representation 단계에 직접 통합한다. 이 통합은 본 데이터 위에서 조직 생태학의 이론 가설(liability of newness, density dependence)을 정량적으로 재검토함과 동시에 그것을 *예측 feature로 옮긴다(translate)* 는 점에서, 세 갈래의 교차점에 위치한다.

---

## §2.2 시계열 예측 방법론

두 번째 흐름은 시계열 예측 및 분류 방법론이다. 다섯 갈래로 정리한다: (i) 트리 기반 앙상블, (ii) 신경망 기반 시계열 모델, (iii) Transformer 기반 예측 모델, (iv) foundation model, (v) 평가 방법론. 각 갈래마다 본 데이터의 특성과 어긋나는 가정을 함께 식별한다.

### §2.2.1 트리 기반 앙상블 (Random Forest, GBM, LightGBM)

트리 기반 앙상블은 tabular feature와 시계열 통계량을 함께 사용하는 본 연구 setting에 부합한다. Random Forest \cite{breiman2001random}는 깊은 트리의 bagging 앙상블로, feature 간 비선형 상호작용을 안정적으로 포착한다. LightGBM \cite{ke2017lightgbm}은 boosting에 leaf-wise growth와 histogram-based splitting을 결합한 모델로, 다수의 약한 신호와 상호작용이 누적될 때 효율적이다. XGBoost \cite{chen2016xgboost}는 같은 계열의 대표 알고리즘이다.

M5 \cite{makridakis2022m5}와 같은 대규모 예측 경진의 실증적 합의 — 트리-부스팅 계열이 신경망 시계열 모델을 능가 — 는 *tabular representation이 충분히 풍부할 때* gradient-boosted tree가 매우 강한 baseline이라는 점이다. 이 문헌은 본 논문이 트리 기반 앙상블을 강한 tabular baseline으로 삼아, 소상공인 특화 hybrid representation이 예측 가치를 더하는지 평가하도록 동기를 부여한다 (§5.7).

이는 Random Forest와 LightGBM을 동일 평가 프로토콜 하에서 비교하도록 동기를 부여하며, 상세는 Chapter 5(§\ref{sec:rf_vs_lgbm})에서 전개한다.

### §2.2.2 신경망 기반 시계열 모델 (RNN, DLinear, N-BEATS, N-HiTS)

RNN은 순차 의존성 학습의 고전적 접근이며, 그 확률적 확장 DeepAR \cite{salinas2020deepar}는 점포별 메타데이터를 공유 파라미터 공간에 융합하는 패널 시계열 학습의 표준 모델이 되었다. 한편 "Transformer가 시계열 예측에 정말 효과적인가?" 라는 비판 \cite{zeng2023dlinear}은 DLinear 같은 단순 선형 모델이 강한 baseline임을 재확인하였고, N-BEATS \cite{oreshkin2020nbeats}와 N-HiTS \cite{challu2023nhits}는 신경 기저 전개와 계층적 보간을 통한 해석 가능한 시계열 분해를 제공한다.

이들 모델은 관찰 시계열이 충분히 길고 규칙적으로 샘플링되며, 단면 이질성이 공변량이나 공유 파라미터로 포착될 때 가장 잘 작동하는 경향이 있다. 본 setting은 더 까다롭다: 패널이 주간·점포 단위이고, 매출 수준·변동 패턴에서 점포 간 이질성이 크며, 빈번한 불연속(휴무, 영업시간 변경)을 동반한다.

### §2.2.3 Transformer 기반 예측 모델 (TFT, PatchTST, Informer, Autoformer)

Transformer 아키텍처 \cite{vaswani2017attention}의 도입 이후, self-attention 기반 시계열 예측 모델이 다수 개발되었다. TFT \cite{lim2021tft}는 정적·동적 공변량과 시간 feature를 gating과 attention으로 통합하여 해석 가능성을 제공한다. PatchTST \cite{nie2023patchtst}는 시계열을 patch로 토큰화하여 NLP 스타일 Transformer 아키텍처를 적용한다. Informer \cite{zhou2021informer}는 ProbSparse self-attention으로 장기 시계열의 시간 복잡도를 감소시킨다. Autoformer \cite{wu2021autoformer}는 auto-correlation decomposition 블록을 도입하여 추세와 계절성을 직접 학습 가능한 성분으로 통합한다.

이 모델들은 본 논문의 14-모델 외부 비교(§6.2)에 포함되며, *주간* 데이터에서 일관된 음의 마진을 보였다. 이는 규칙적 시퀀스 학습을 위해 설계된 모델이 추가적 도메인 특화 표현 없이 주간 소상공인 매출의 이질적·불연속적 구조를 직접 포착할 수 있는지를 검증할 동기를 부여한다.

### §2.2.4 Foundation 모델 (Chronos, Moirai)

시계열 foundation model은 대규모 사전 학습을 활용해 임의의 새로운 데이터에 zero-shot 또는 few-shot 으로 적응하는 일반화를 목표로 한다. Chronos \cite{ansari2024chronos}는 시계열을 토큰 시퀀스로 변환하여 언어 모델 패러다임을 시계열에 이식한다. Moirai \cite{woo2024moirai}는 다양한 주기와 변수 구조를 단일 Transformer 안에서 학습하는 universal forecasting framework를 제안한다. TimesFM \cite{das2024timesfm}은 범용 시계열 예측을 위해 학습된 decoder-only foundation model이다.

따라서 시계열 foundation model은 주 모델링 프레임워크가 아니라 외부 비교 벤치마크로 다룬다 (§6.2). 구조적 차이가 관련된다: foundation model은 시계열의 *값/추세 예측*을 학습하지만, 본 논문의 G/S/D 분류는 *단기 horizon 분류 라벨에 대한 임계값 기반 결정*을 다룬다.

### §2.2.5 시계열 분류 및 평가 방법론

시계열 *분류*(TSC)는 시계열 예측과 별개의 분야로, "great bake-off" 비교 \cite{bagnall2017great}와 딥러닝 기반 TSC 리뷰 \cite{fawaz2019deeplearning}가 표준 참고문헌이다. 본 논문의 G/S/D 라벨링은 시계열의 *값 예측*이 아니라 *상태 분류*이므로 TSC에 더 가깝다. 다만 입력에 매출 시계열뿐 아니라 메타데이터·고객 구성·계절성 변수가 함께 들어가 *멀티모달 tabular representation* 을 구성한다는 점에서, 단일 모달 시계열 입력만 사용하는 전형적 TSC와 구별된다.

평가 방법론 측면에서는 시계열 cross-validation의 한계 \cite{bergmeir2012use}와 계절성·정상성·불연속 처리의 어려움 \cite{hyndman2021forecasting,elsayed2021dlmodels}이 핵심 쟁점이다. 본 논문은 두 방향에서 평가 프로토콜의 robustness를 검증한다: 시즌 정렬 rolling panel (§6.1)과 14개 비-LightGBM 비교 모델과의 동일 split 비교 (§6.2).

---

## §2.3 공간–산업 의존성을 위한 그래프 기반 확장

점포의 공간·산업적 근접성이 매출 동태에 영향을 준다는 가설은 경제지리학 \cite{jacobs1969economy,glaeser2010agglomeration}의 관점에서 자연스럽다. 같은 동네 점포는 유동인구·상권·정책 효과를 공유하고, 같은 업종 점포는 추세·계절성을 공유한다. 그래프 신경망(GNN)은 이러한 공간·산업 의존성을 명시적으로 모델링하는 한 방법이다.

### §2.3.1 GCN, GAT, 시계열 응용

GNN의 표준 아키텍처는 GCN \cite{kipf2017semi}과 GAT \cite{velickovic2018graph} 둘이다. GCN은 이웃 표현을 평균(또는 정규화 합)으로 집계하는 1차 근사 graph convolution이며, GAT는 attention 메커니즘으로 이웃별 가중치를 학습한다. 이를 시계열과 결합한 STGCN \cite{yu2018stgcn}은 temporal convolution 블록과 spatial graph convolution 블록을 교대로 쌓아 시공간 의존성을 학습한다. 그래프 표현 학습의 일반 이론은 \cite{hamilton2020graph}와 GNN 서베이 \cite{wu2021survey}에 정리되어 있다.

### §2.3.2 본 논문의 GNN 구성과 한계

본 논문에서 그래프 기반 모델링은 공간–산업 의존성이 tabular·궤적 feature를 넘어 추가 예측 마진을 주는지 검증하는 *예비적 확장*으로 다룬다. 두 엣지 유형 — *동(공간 근접성)* 과 *업종* — 을 결합한 이종 그래프 위에 GCN 변형을 적용하고 SHAP 값 \cite{lundberg2017unified}으로 feature별 엣지 가중치를 할당하며, 구성과 실증 비교는 Chapter 6에서 보고한다. STGCN \cite{yu2018stgcn} 같은 시공간 모델로의 확장은 향후 연구로 남긴다.

---

## §2.4 Hybrid Representation Learning

representation learning의 일반 원리 \cite{bengio2013representation}는 *입력 데이터를 학습에 적합한 잠재 공간으로 변환*하는 것이다. 시계열 예측·분류에서 이 원리는 시계열 통계량, 변곡점 \cite{truong2020changepoint}, shape 기반 클러스터링 \cite{paparrizos2015kshape} 같은 보조 신호를 결합하는 방향으로 진화해 왔다.

본 논문에서 "hybrid representation"은 (i) 시계열 통계량, (ii) tabular 메타데이터, (iii) 도메인 신호를 단일 feature 벡터로 결합하여 예측 모델에 투입하는 접근을 의미한다 \cite{fawaz2019deeplearning,salinas2020deepar}. 본 논문은 두 라벨 정의에 대해 두 가지 구분되는 hybrid 형태를 평가한다:

- **고성장 변곡점 + UDX representation**: 17개 운영 baseline 변수(신규 고객 비율, 매출 변동계수, 영업 개월 수, 사업 밀도, 평방미터, 평균 매출, 추세 슬로프, 총 관찰 주, 주말 매출 비율, 평균 고객 수, 최대/최소 매출, 동·시군구 카운트와 평균) + `sigungu`·`depth_2` 더미에, K-Shape cluster 라벨, 변곡점 슬로프(`slope_P1`, `slope_P2`), 변곡 주차, UDX 코드 더미(`final_code` — DUY/DDZ/UU 등)를 추가 (§5.2).
- **G/S/D hybrid representation**: 매출 시계열 통계량, 점포 메타데이터, 고객 구성 신호, KMeans cluster 라벨, change-point feature를 결합하여 A_baseline / B_base+cluster / C_base+cp / D_full 의 hybrid feature set 구성 (§5.3).

이 구성은 *현상 분석에서 식별된 요인*과 *매출 곡선 형상 신호*를 직접 반영할 수 있어, 단일 모달 입력(예: 매출 시계열만) 대비 우위를 가진다. 또한 더 풍부한 표현은 macro-$F_1$ 평가 하에서 소수 클래스 경계를 더 분리 가능하게 만들 수 있으나, 클래스 불균형 \cite{chawla2002smote,johnson2019survey}은 실증 분석에서 여전히 핵심 과제로 남는다.

---

## §2.5 본 논문의 위치 설정

위 네 흐름을 종합하면, 본 논문의 위치는 다음과 같다.

1. **소상공인 매출 동태 연구**로서, 현상 분석을 통해 조직 생태학의 가설(liability of newness, density dependence)과 일관된 실증 패턴을 제시하고, 그 발견을 예측 feature로 옮김으로써, 설명적 분석과 예측 모델링의 흔한 분리를 다룬다 (Chapter 4 + Chapter 5).
2. **시계열 예측 연구**로서, 14-모델 벤치마크 실험을 통해 범용 시계열 예측 모델이 주간 매출 데이터에 전이되는지를 평가하고, 그 결과를 데이터 특성의 관점에서 해석한다 (§6.2). 트리 기반 앙상블 \cite{breiman2001random,ke2017lightgbm}의 우위를 본 데이터의 *feature 이질성, 강한 소수 클래스 신호, 큰 categorical cardinality* 와의 적합성으로 구조적으로 해석한다.
3. **그래프 기반 확장 연구**로서, 공간 신호가 본 데이터와 그래프 구성에서 추가 마진을 주는지에 대한 예비적 실증 검증을 제공하며 (§6.3), 이는 시공간 hybrid model \cite{yu2018stgcn}으로의 확장 동기를 제공한다.
4. **Hybrid representation learning 연구**로서, 운영·고객 구성·궤적 형상·cluster·change-point feature의 결합이 운영 baseline을 넘어 분류를 개선하는지 검토한다. 나아가 동일 feature set 위에서 Random Forest와 LightGBM 계열을 비교하여 representation의 역할과 분류기 선택의 역할을 분리한다 (§\ref{sec:taskA_ablation}, §\ref{sec:taskB_main}, §\ref{sec:rf_vs_lgbm}).

이 네 위치는, 본 논문이 단일 모델 성능 benchmarking이 아니라 *현상 분석 → 예측 representation → 모델 비교 → robustness* 의 일관된 흐름을 학술적 기여로 제시함을 의미한다. Chapter 3은 KCD 데이터의 구조, G/S/D 라벨 정의, 평가 지표의 근거 기술로 이어진다.
