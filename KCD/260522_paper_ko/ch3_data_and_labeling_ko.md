<!--
원본: 260516_overleaf_en/chapters/ch3_data_and_labeling.tex
번역일자: 2026-05-22
-->

# Chapter 3 — Data and Labeling (국문 번역)

본 장은 본 학위논문에서 사용한 데이터의 구조, 분석을 서울 외식업으로 한정한 근거, G/S/D 라벨의 정의와 임계값 민감도, 평가 지표 선택의 근거, 분석 단위(점포 / 업종 × 동), 전처리 절차, 학습·평가 분할 프로토콜을 기술한다.

---

## §3.1 데이터 개요

본 논문은 한국신용데이터(KCD)의 카드 매출 데이터 \cite{kcd2024manual}를 사용한다. KCD는 국내 소상공인·자영업자를 주 고객으로 하는 SaaS 플랫폼이며, 가맹점의 카드 결제 거래를 점포 수준에서 식별·집계해 시계열로 제공한다. 본 데이터는 두 개의 축으로 구성된다.

- **주간 매출 시계열** (`original_data/weekly.parquet`). 각 store-week에 대해 매출액, 결제 건수, 신규·재방문 고객 수, 객단가가 포함됨.
- **점포 메타데이터** (`original_data/meta.csv`). 업종 코드, 행정동, 사업 개시일(영업기간 산출용), 사업 형태 등의 tabular 정보.

매출 시계열의 주기는 **주간(중빈도)** 이다. 일 단위의 noise는 smoothing되면서 월 단위보다는 dense하여 변화점 탐지에 유리하며, 본 논문의 평가 윈도우 길이(분기 ≈ 약 13주)와도 자연스럽게 정렬된다.

데이터 접근은 KCD와의 공동연구 협약 하에서 제공되었다. `store_id`, 행정동 코드, 업종 코드는 모두 **비식별 처리된 형태로만** 사용되며, 상호명·사업자등록번호·위치 좌표 같은 직접 식별 정보는 본 분석에 사용되지 않는다.

---

## §3.2 분석 범위 — 서울 외식업

분석 단위는 서울특별시의 외식업 약 59,000개 점포의 주간 매출이며, 관측 기간은 2021년 1월–2023년 8월의 142주이다 \cite{kostat2024smb}. 범위를 서울 외식업으로 한정한 근거는 다음과 같다.

1. **표본 동질성.** 거래 구조(카드 침투율, 객단가 분포, 결제 빈도)가 상권 간 비교 가능 수준으로 유지된다. 비외식 업종(소매·서비스)은 결제 빈도·객단가 분포가 크게 달라, 동일 representation·metric 하에서 결과 정합성이 약해진다.
2. **계절·지역 효과 분리 가능성.** 동일 행정 단위 내에서 동·업종 더미가 적용 가능하여, 공간 효과와 계절 효과를 분석 단위 안에서 분리할 수 있다. 비수도권을 포함하면 metropolitan-vs-provincial tier 상호작용이 추가되어 의도한 *공간 × 산업* 효과 추정이 흐려진다.
3. **충분한 cell 두께.** 업종 × 동 조합 수준 분석(Chapter 4)에서, 통계적 유의성 임계값 이상의 점포 수를 가지는 cell이 충분히 많다. 서울의 약 425개 행정동과 본 논문이 식별하는 약 30개 외식 세부 업종의 조합은 $n \geq 100$ 점포를 갖는 다수의 cell을 산출한다.
4. **외식업의 계절·충격 민감성.** 외식업은 계절성, 이벤트(공휴일, 연말연시), 외부 충격(감염병, 사회적 거리두기)에 가장 민감한 업종이다. 본 G/S/D 분류 문제의 *signal-to-noise ratio* 가 가장 또렷이 드러나는 도메인이며, 시즌 정렬 실험(§6.1)이 가장 큰 의미를 갖는 도메인이다.

본 논문은 이 범위 안에서, 캘린더 정렬된 이전 feature 윈도우로부터 이후 target 윈도우의 G/S/D 매출 동태를 예측·설명한다. feature/target 윈도우 구성·offset·누수 방지 split의 구체적 내용은 §3.7에서 다룬다.

---

## §3.3 라벨 정의: G/S/D 상태와 큰 폭 성장 타깃

본 논문은 서로 관련되나 구별되는 두 라벨 정의를 사용한다. 메인 라벨은 시즌 정렬 예측에 쓰는 삼항 Growth/Stable/Decline(G/S/D) 상태이며, 더 엄격한 이항 큰 폭 성장 타깃은 보완적 설명적 ablation으로 사용한다. 두 라벨은 정의·평가 지표·split 프로토콜이 달라 결과를 분리 보고하며 절대 수치를 직접 비교할 수 없다. 본문 각 인용 시점에 어느 타깃인지 명시한다.

### G/S/D 상태 — 삼항 단기 예측

라벨은 target window 내 매출 추세의 **부호·크기**에 대한 삼항 분류이다. 구체적으로, 각 점포의 1년 후 3개월 target window 주간 카드 매출을 **그 점포 자신의 평균 매출로 정규화**(점포 간 수준 차 제거)한 뒤 OLS 추세선을 적합하고, 그 기울기를 `slope_target_norm` 으로 둔다 — 즉 *점포 평균 주간 매출 대비 주당 매출 변화율*이다. 이 슬로프로 라벨링한다.

- **Growth (G).** 정규화 추세 슬로프가 *양의 임계값* 이상.
- **Stable (S).** 슬로프가 임계값 band 안.
- **Decline (D).** 슬로프가 *음의 임계값* 이하.

임계값은 **각 패널 내** 정규화 슬로프의 *표준편차* $\sigma$ 의 $k$ 배($\pm k\sigma$)로 설정한다. $\sigma$ 가 패널별로 계산되므로 cutoff는 각 패널의 분산에 적응한다. 기본값은 $k = 0.5$이며, "대부분 점포가 Stable로 뭉치지 않으면서 Growth·Decline의 정의가 통계적으로 안정적인" 영역이다. 임계값 민감도는 Table 3.1에 요약한다.

**Table 3.1 — Label threshold sensitivity** (삼항 분류기 macro-$F_1$, 라벨링 패널; 여기서 $k$는 정규화 슬로프의 패널별 표준편차 $\sigma$에 곱하는 배수로, Growth/Decline cutoff는 $\pm k\sigma$)

| $k$ | 삼항 macro-$F_1$ |
|---|---|
| 0.3 | 0.4908 |
| **0.5** | **0.4945** |
| 0.7 | 0.4867 |

세 값 중 $k = 0.5$가 macro-$F_1$에서 가장 안정적이다. $k = 0.3$은 Growth를 키우고 Decline을 줄이며, $k = 0.7$은 Stable을 과대 표현한다. 모든 삼항 G/S/D 결과는 $k = 0.5$로 보고한다. (큰 폭 성장 `growth_type` 임계값은 1.0으로 고정되며 본 sweep에 포함되지 않는다.)

#### 라벨이 크기로 무엇을 뜻하는가

worked-example 라벨링 패널 `sy2021_sm01_w3m_off1` ($n = 34{,}274$, 대표 패널이 아니라 예시용)에서 슬로프 표준편차는 $\sigma = 0.042$, 따라서 임계값은 주당 $\pm 0.5\sigma = \pm 0.021$. 클래스별 슬로프 분포와 그것이 함의하는 13주(분기) 누적 매출 변화폭(슬로프 × 13, 점포 평균 매출 대비)은 다음과 같다. **Growth 점포는 분기에 중앙값 약 +54%, Decline 점포는 약 −47%** 변하며 Stable은 거의 평탄 — 세 클래스가 marginal한 차이가 아니라 경제적으로 실질적인 궤적 차이에 대응함을 보인다.

**Table 3.2 — 클래스별 슬로프 크기** (라벨링 패널, $\sigma=0.042$, 임계값 $\pm0.021$/주)

| Class | Share | Median slope/week | 함의 13주 누적 변화(중앙값) |
|---|---|---|---|
| Growth | 56.6% | +0.041 | **+54%** |
| Stable | 35.6% | +0.006 | +8% |
| Decline | 7.8% | −0.036 | **−47%** |

이 크기는 패널마다 다르며(패널별 $\sigma$·클래스 구성 상이; §6.1), 라벨링 패널은 scale 감을 주기 위한 예시일 뿐이다. 이 패널의 Growth 편중은 해당 캘린더 비교가 post-COVID 회복기에 걸친 결과이며, 다른 패널은 다른 클래스 구성을 보인다(Figure 3.1). 이것이 Chapter 6에서 시즌 정렬 rolling robustness를 보고하는 이유다.

라벨링 윈도우는 시즌 정렬을 위해 동일 길이 분기(약 13주)로 설정하며, 윈도우 길이 변형(4·6·7개월)은 §6.1 robustness에서 함께 검증한다.

### 큰 폭 성장 타깃 — 이항 분류 (보완적)

보완적 설명 ablation으로서, 라벨은 `growth_rate` — 점포 관측구간 첫 분기 대비 마지막 분기 평균 주간 카드 매출의 상대 변화율 $(\text{late\_avg}-\text{early\_avg})/\text{early\_avg}$ — 이 1.0 이상인지(즉, 마지막 분기 평균이 첫 분기 평균의 2배 이상)의 이항 변수:
$$\texttt{growth\_type} = \mathbb{1}[\texttt{growth\_rate} \geq 1.0] \in \{0, 1\}.$$

큰 폭 성장 타깃은 **binary $F_1$** (양성 = 큰 폭 성장)을 평가 지표로, **stratified 80/20 holdout (single seed = 42)** 을 split으로 사용한다.

### 평가 프로토콜 차이 요약

두 타깃은 *설계상* 다르며 절대 수치를 직접 비교해서는 안 된다.

**Table 3.3 — 큰 폭 성장 타깃 vs G/S/D 상태 평가 프로토콜**

| 항목 | 큰 폭 성장 타깃 | G/S/D 상태 |
|---|---|---|
| Label | binary (`growth_rate ≥ 1.0`) | 3-class (G/S/D, $\pm 0.5\sigma$) |
| Input window | 전체 관측 시계열의 운영·shape feature | same-calendar 3 months |
| Target window | 마지막 관측 분기 vs 첫 관측 분기(점포별 span) | same 3 months one year later |
| Metric | binary $F_1$ (positive = 큰 폭 성장) | macro-$F_1$ |
| Split | stratified 80/20 (single seed) | store-grouped 5-fold × **14 panels** |
| Used in | §§5.1–5.2 | §5.3 onward + Chapter 6 |

---

## §3.4 클래스 불균형과 평가 지표

### §3.4.1 클래스 불균형의 정량 진단

G/S/D 세 클래스는 비대칭이며, 불균형은 **패널 내부**에도 **패널 간**에도 존재한다. 3개월(offset-1) 시즌 정렬 패널 19개를 풀링하면(store-panel 관측 $682{,}365$개), **Stable이 다수 클래스(약 57%)** 이고 Growth·Decline은 각각 약 20%다. 게다가 구성은 패널마다 크게 변동한다 — Decline 비중만 해도 패널에 따라 5%~62%, Growth는 4%~57% 범위다(Table 3.4, Figure 3.1).

**Table 3.4 — G/S/D class proportions** (3개월 시즌 정렬 19패널 풀링, offset 1; store-panel 관측 $682{,}365$개)

| Class | 풀링 비율 | 패널별 범위 |
|---|---|---|
| Growth | 0.226 | 0.044–0.566 |
| Stable | 0.569 | 0.333–0.734 |
| Decline | 0.206 | 0.054–0.620 |

약 5.9만 개 서울 외식업 점포 중, 각 패널은 입력 윈도우와 1년 후 target 윈도우에 모두 관측된 점포를 라벨링한다; 라벨링 패널 `sy2021_sm01_w3m_off1` 은 그런 점포 $n=34{,}274$ 개를 포함한다(시작 월에 따라 패널별 수가 달라짐, Table 6.1 참조). 이후 K-Shape 클러스터링·시즌 정렬 예측에 쓰이는 모델용 패널은, shape 기반 feature에 필요한 완전한 주간 시계열이 없는 276개 점포를 제외하여 $n=33{,}998$ 이다.

단순 accuracy로 평가하면 두 함정이 발생한다.

1. **Stable이 다수 클래스**이므로, Stable-only 예측만으로도 풀링 기준 약 57%(Stable 편중 패널에선 더) accuracy가 나오며, Growth·Decline 점포는 하나도 식별하지 못한다.
2. 결과적으로 본 논문의 핵심 관심 — *실제 Decline 점포를 Decline으로 정확히 식별하는지* (특히 조기 경보 응용) — 이 흐려진다.

### §3.4.2 지표 선택: Macro-$F_1$

따라서 평가 지표로 **macro-$F_1$** 을 사용한다. macro-$F_1$은 각 클래스의 precision/recall 균형($F_1$)을 클래스당 동일 가중치로 평균하여, 클래스 불균형 하에서 어느 한 클래스도 무시되지 않게 보장한다. 후보 지표 비교는 Table 3.5에 정리한다.

**Table 3.5 — Metric comparison under class imbalance**

| Metric | Property | Suitability |
|---|---|---|
| Accuracy | 강한 다수 클래스 편향 | 부적합 |
| Weighted-$F_1$ | 클래스 크기 가중 | Decline 무시 가능 → 부적합 |
| **Macro-$F_1$** | 클래스 동일 가중 | **본 논문 main metric** |
| Balanced accuracy | recall 동일 가중만 | precision 손실 가능 → 보조 |

**Figure 3.1 — G/S/D label distribution.** 3개월 윈도우·offset 1의 **19 패널** 전반의 Growth/Stable/Decline 비율. 클래스 분포는 패널 시작 월에 따라 상당히 변동한다 (예: 2021년 초 Growth 우세 → 2022년 말 Decline 우세). 이 분포 이질성이 클래스 불균형 보정과 시즌 정렬 평가가 동시에 필요한 이유이다.

---

## §3.5 분석 단위

본 논문은 네 개의 분석 단위를 명시적으로 구분한다.

**Table 3.6 — Units of analysis**

| Unit | Chapters Used | Purpose |
|---|---|---|
| Store | Ch 4.1, Ch 5, Ch 6 | 개별 점포 G/S/D 라벨링·예측 |
| Industry | Ch 4.2 | 업종 수준 G/S/D 분포 비교 |
| Neighborhood | Ch 4.2 | 동 단위 G/S/D 분포 |
| Industry × Neighborhood | Ch 4.2 | 공간 × 산업 조합 패턴 |

특히 업종 × 동 단위는 본 논문이 강조하는 focal analysis로, "어떤 조합이 Growth 비율이 높고 Decline 비율이 높은가" 를 도출하는 데 사용된다 (§\ref{sec:industry_dong}).

### K-Shape 매출 시계열 클러스터

점포 매출 시계열의 *형상(shape)* 도 파생 grouping·예측 feature로 사용된다. K-Shape 알고리즘 \cite{paparrizos2015kshape}을 $K = 6$으로 적용하면 6개의 인식 가능한 궤적 형상이 산출된다(Figure 3.2): 고점→**급락(sharp-drop)**, **지속 고수준(sustained-high)**(주기적 dip), **완만한 하락(gradual-decline)**, **지속 하락(sustained-decline)**, **상승/회복(rising/recovery)**, **완만한 상승(gentle-rise)** 클러스터. $K = 6$은 더 잘게 나누기보다 질적으로 구분되는 소수의 해석 가능한 형상을 얻기 위한 의도적 선택이며, 그 결과 `cluster` 라벨은 모델에 보조 feature 하나로만 들어가고 — Ch5에서 보듯 — 그 증분 기여가 제한적이라 핵심 결론이 클러스터 수에 의존하지 않는다. 이 `cluster` 라벨은 큰 폭 성장 변곡점 + UDX representation (§5.2)과 G/S/D hybrid representation (§5.3) 양쪽에서 feature로 직접 사용된다. UDX 코드용으로는 6개 클러스터를 전체 형상에 따라 세 패턴 글자로 다시 묶는다 — 성장형 클러스터 → X, 안정 클러스터 → Y, 쇠퇴형 클러스터 → Z.

**Figure 3.2** — 6개 K-Shape 클러스터: 멤버 시계열(회색) 위에 클러스터 평균(빨강), 관측 주 전체에 대해 $[0,1]$로 정규화. 각 패턴은 두 예측 타깃의 representation에 `cluster` feature로 들어간다.

---

## §3.6 데이터 전처리

표준 전처리는 다음과 같다.

- **결측 주 처리.** 일시적 결측은 인접 값의 선형 보간으로 채우고, 연속 결측 구간은 가능한 폐업 기간으로 마스킹한다.
- **폐업·신규 개업 구간 식별.** 임계값 이상의 연속 0 매출 주가 있거나 명시적으로 폐업일로 기록된 구간은 입력 윈도우에서 제외한다.
- **시즌 정렬을 위한 캘린더 매칭.** 학습·평가 패널을 동일 캘린더 단위(예: 1–3월 = 겨울 분기)로 정렬한다. Chapter 6의 시즌 rolling 평가의 기반이다.
- **점포 단위 정규화.** 점포별 매출 수준 차를 제거하기 위해 매출 시계열을 within-store 또는 within-quarter 평균으로 정규화한다.
- **outlier 처리.** 0 매출 또는 비현실적으로 큰 값(예: 단일 주 매출이 점포 평균의 100배 초과)은 winsorize 또는 마스킹한다.

시즌 정렬은 "기간별 성능이 비슷하다"라는 robustness 주장의 핵심 전처리 단계이며 \cite{bergmeir2012use,hyndman2021forecasting}, 통제 변수가 아닌 **설계로** 계절성을 제거하는 방법론적 선택이다. 특히 점포별 평균 정규화는 라벨링 시점(§3.3)에 적용된다.

---

## §3.7 학습·평가 분할

temporal leakage 방지를 위해 split 시점 기반의 future-hold-out 평가를 채택한다. 각 패널은 다음과 같이 구성된다.

- **Feature window.** 점포 거래의 캘린더 정렬된 1–7개월 매출/고객 시계열. 패널의 `feature_start` – `feature_end` 사이.
- **Target window.** 설정된 offset 위치의 같은 길이 윈도우(기본값: 1년 후 동일 캘린더 윈도우; 아래 Offset 참조). G/S/D 라벨은 `target_start` – `target_end` 사이 매출 추세 슬로프로 정의.
- **Offset.** 1 = 다음 해 동일 캘린더 윈도우; 2 = 2년 후 동일 캘린더 윈도우. 시즌 정렬의 핵심 설계 변수.

동일 split 프로토콜이 baseline·hybrid representation·14개 비-LightGBM 비교 모델·GNN 모두에 일관되게 적용되어, 모델 간 비교가 평가 프로토콜 차이로 왜곡되지 않도록 보장한다.

### Train/validation/evaluation 분할

각 패널 내에서 train/validation 분할은 점포 수준 5-fold cross-validation으로 구성하며, fold 간 점포 leakage 방지를 위해 `store_id` group splitting을 적용한다. 결과는 **5-fold 평균과 표준편차**로 보고한다. 일부 보조 분석은 single-trial (seed=42) 결과로 보고하며, 이는 본문에 명시한다.

### 본 논문에서 사용하는 패널 집합

여러 분석이 서로 다른 패널 선택 위에서 동작하므로, 다음 용어를 (포함 관계가 아니라 **목적별로**) 고정한다.

- **14 메인 패널.** 메인 삼항 G/S/D 평가(store-grouped 5-fold)에 사용되는 시즌 정렬 패널. Chapter 5–6 전반에서 인용 (Table 3.3).
- **19 분포 패널.** 추가 시작 월을 포괄하는 모든 3개월·offset-1 시즌 정렬 패널. macro-$F_1$ *분포* 와 시즌 robustness 보고에 사용 (§6.1, Figure 3.1). macro-$F_1$ 0.43–0.54 범위는 이 집합에서 산출.
- **7 핵심 패널.** 점포 coverage가 가장 충분한 7개 3개월 패널. 패널별 평균·표준편차로 개별 보고 (Table 6.1).
- **6 비교 패널.** 계산 비용이 큰 실험 — 외부 비교(§5.7), 코호트별 LightGBM-vs-RF 비교(§5.5), cost-sensitive 실험(§5.8) — 을 돌린 subset. 이 실험들의 모든 $\Delta$macro-$F_1$ 값은 이 집합의 패널 평균이다.
