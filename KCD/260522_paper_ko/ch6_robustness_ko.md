<!--
원본: 260516_overleaf_en/chapters/ch6_robustness.tex
번역일자: 2026-05-22
-->

# Chapter 6 — Robustness (국문 번역)

본 장의 모든 결과는 **G/S/D 상태** (삼항 단기 예측, 시즌 정렬 패널 위 store-grouped 5-fold, macro-$F_1$) 상에서 보고된다. 고성장 타깃(이항)의 external validity는 별도 평가 프로토콜을 요하며 향후 연구로 미룬다 (§\ref{sec:limitations}). 본 장은 §\ref{sec:rf_vs_lgbm}·§\ref{sec:phase5}의 메인 G/S/D 결과의 robustness를 평가한다: (i) 시즌·시기를 변화시켜도 안정적인지, (ii) 14 비-LightGBM 비교 모델 및 예비 GNN 대비 경쟁력을 유지하는지.

---

## §6.1 시즌 정렬 Rolling Panels

### 패널 구성

본 절은 두 관련 패널 집합(§3.7)을 쓴다: 패널별 평균·표준편차로 개별 보고하는 **7개 핵심 3개월 패널**(Table 6.1), 그리고 더 넓은 시즌 성능 분포를 기술하는 **19개 3개월 offset-1 패널**. 각 패널은 동일 캘린더 단위(분기 또는 동일 길이 윈도우)로 정렬되어, 학습·평가 기간이 다르더라도 비교가 *같은 시즌 위에서* 일어난다. 이 설계는 계절성을 부차적 효과가 아니라 *통제해야 할 1차 교란 요인* 으로 보는 본 논문의 입장을 구체화한 것이다 \cite{bergmeir2012use,hyndman2021forecasting}.

### 성능 분포

**19개 시즌 정렬 패널 × 2 모델**(LightGBM, RF) 평가에서, macro-$F_1$ 은 **0.435 ~ 0.541 범위 (반올림 0.43–0.54)**. 7개 핵심 3개월 패널의 A_baseline (RF) macro-$F_1$ 만 추리면 Table 6.1.

**Table 6.1 — 7 core 3-month model-ready panels (mean ± std)**

| Panel | Period Match | $n_\text{stores}$ | macro-$F_1$ |
|---|---|---|---|
| sy2021_sm01_w3m_off1 | Jan–Mar 2021 → 2022 | 33,998 | 0.503 ± 0.003 |
| sy2021_sm03_w3m_off1 | Mar–May 2021 → 2022 | 34,884 | 0.495 ± 0.008 |
| sy2021_sm05_w3m_off1 | May–Jul 2021 → 2022 | 35,473 | 0.486 ± 0.004 |
| sy2021_sm09_w3m_off1 | Sep–Nov 2021 → 2022 | 36,013 | 0.510 ± 0.006 |
| sy2022_sm01_w3m_off1 | Jan–Mar 2022 → 2023 | 36,133 | 0.514 ± 0.009 |
| sy2022_sm03_w3m_off1 | Mar–May 2022 → 2023 | 35,984 | 0.467 ± 0.007 |
| sy2022_sm05_w3m_off1 | May–Jul 2022 → 2023 | 35,893 | 0.517 ± 0.008 |

패널 내부 5-fold 표준편차 모두 ≤ 0.009, 어느 패널도 붕괴하거나 비현실적으로 높지 않음. 윈도우 확장(4·6·7개월) 시에도 분포는 0.475 ~ 0.550 범위 유지.

**Figure 6.1** — 19 시즌 정렬 패널(3개월, offset 1) 위 LightGBM·RF macro-$F_1$. 범위 약 0.435 ~ 0.541.

**Figure 6.4** — start-month × window-length 평면의 LightGBM macro-$F_1$ heatmap (보조).

#### 엄격한 out-of-time (OOT) 검증

14-패널 시즌 정렬 rolling 프로토콜은 각 패널 *내부* store-grouped 5-fold CV 사용. 추가적인 더 엄격한 robustness 층으로 **strict out-of-time (OOT) split** 을 평가: 2021 패널로 학습하고 *다음 해* 같은 캘린더 윈도우로 테스트 (예: Jan–Mar 2021→2022 학습, Jan–Mar 2022→2023 테스트), train/test 패널 시간 slice 간 점포 공유 없음. 이는 메인 LightGBM 파이프라인의 재현이 아니라 전이성(transferability) 스트레스 테스트이므로, balanced-logistic baseline 을 `most_frequent` dummy 에 견주어 사용한다. Figure 6.5 는 start month (1~12) × window length (4,8,12,16,20,30주) 모든 조합의 macro-$F_1$ 을 보고한다.

**Figure 6.5** — strict OOT macro-$F_1$ heatmap. 모델은 모든 구성에서 0.34–0.46 범위, `most_frequent` dummy (0.21–0.27) 보다 일관되게 위.

strict-OOT macro-$F_1$ (0.34–0.46) 은 year-specific calibration 활용이 차단되므로 within-panel 5-fold (0.43–0.54) 보다 자연히 낮음. 그러나 모든 start-month·window-length 조합에서 `most_frequent` dummy (0.21–0.27) 를 0.10–0.20 macro-$F_1$ 만큼 일관되게 상회 — G/S/D 분류기가 연도별 클래스 분포를 넘어서는 *전이 가능한 신호* 를 포착함을 확인.

#### start-month 효과가 window-length 효과를 압도

macro-$F_1$ 분산을 start-month 성분과 window-length 성분으로 분해하면 뚜렷한 비대칭: start-month amplitude 약 0.10, window-length amplitude 0.02–0.04 (Figure 6.3). 즉 입력 윈도우를 *언제* 시작하는지가 *얼마나 긴지* 보다 **2.5–5배** 더 중요. 이는 본 논문 전반의 시즌 정렬 패널 설계의 핵심 경험적 정당화 — 패널을 같은 캘린더 분기로 정렬하지 않으면 start-month nuisance 가 진정한 모델 비교를 압도한다.

**Figure 6.3** — 19 패널 구성의 macro-$F_1$ 변동을 start-month 성분(amplitude ≈ 0.10) 과 window-length 성분(0.02–0.04) 으로 분해.

### 해석

두 함의:

1. **두 prediction 타깃은 직접 비교 불가.** 고성장 binary $F_1$ 0.795 ~ 0.844 (§5.2, 단일 80/20 holdout) 와 G/S/D macro-$F_1$ 0.43–0.54 (본 절, 19 시즌 정렬 패널 store-grouped 5-fold) 는 label·metric·split 이 다름. 직접 비교 금지. 본 논문은 타깃 내 향상·안정성만 주장.
2. 그 한계 내에서, G/S/D 의 LightGBM vs RF 상대 순위는 시즌·시기 변화에 걸쳐 일관됨.

---

## §6.2 External 비교: 14 비-LightGBM 모델

§\ref{sec:phase5}의 경계 조건 비교를 동일 매출 데이터·라벨·split 위에서 robustness 재확인으로 재검토한다. 결론은 동일하다: LightGBM 계열 3종만 Random Forest reference를 상회하고(+0.003 ~ +0.0075, 최대 6패널 중 5승), 14개 비-LightGBM 비교 변형(cost-sensitive RF 2, SMB-attention 3, foundation 2, neural forecasting 7)은 모두 일관된 음의 마진(−0.0345 ~ −0.2705)을 보인다. 모델별 값은 Table 5.6 참조.

### 데이터 특성 해석

이는 예측 모델 자체의 결함이 아니라 *데이터 특성 mismatch*:

- **빈도·샘플링.** 이 모델들은 규칙적으로 샘플링된, 안정적·균등 간격의 신호에 대한 장기 예측 벤치마크에서 강점을 보인다. 본 데이터는 주간 점포 매출로, noise 구조·정상성·자기상관 구조가 그런 벤치마크 환경과 다름.
- **단면 이질성.** 이 모델들이 강한 벤치마크는 보통 비교적 동질적인 단면을 다룬다. 본 점포는 업종·동·영업기간·고객 구성이 이질, 점포별 *수준* 차이 큼.
- **불연속.** 점포는 빈번한 불연속(휴무, 영업시간 변경, 부분 상호 변경)을 가지나, 이 모델들은 일반적으로 그런 불연속이 드문 연속적 시계열을 가정.

### 함의

이 결과는 본 논문의 *현상 분석 + 도메인 신호 통합* 접근의 정당성을 뒷받침한다. 외부 예측 모델의 단순 이식이 작동하지 않는 영역에서는 *데이터 특성을 반영한 representation 설계* 가 1차이며, 본 논문의 hybrid representation 이 그 대안.

---

## §6.3 Graph Neural Network 비교

### 그래프 구성

점포 간 상호작용을 두 엣지 유형으로 표현:

- **동(공간 근접) 엣지**: 같은/인접 동 점포 간 연결.
- **업종 엣지**: 같은/유사 업종 점포 간 연결.

### SHAP 기반 엣지 가중치

GNN \cite{kipf2017semi,velickovic2018graph} 의 동·업종 관계 가중에, tabular 모델의 SHAP \cite{lundberg2017unified} feature-attribution 점수를 heuristic 가중 신호로 사용한다 — 별도로 학습된 graph-attention 메커니즘이 아니라.

### 결과와 해석

패널 `sy2021_sm01_w3m_off1` (RF baseline 0.490) 에서:

**Table 6.4 — 그래프 구성별 GNN macro-$F_1$**

| Graph | Model | macro-$F_1$ | $\Delta F_1$ vs RF |
|---|---|---|---|
| none | mlp | 0.415 | −0.076 |
| dong | gcn | 0.355 | −0.135 |
| industry | gcn | 0.376 | −0.114 |
| hybrid_dong_industry | gcn | 0.394 | −0.096 |

세 그래프 구성(동, 업종, hybrid) 모두에서 GNN(GCN) 이 *MLP baseline 0.415 보다도 낮은* macro-$F_1$, RF 0.490 대비 −0.10 ~ −0.14 로 일관되게 열위. 패널을 `sy2022_sm01_w3m_off1` 또는 `sy2021_sm01_w7m_off1` 로 바꿔도 같은 부호 관계 유지.

- 이 그래프 구성에서 GNN macro-$F_1$ 은 RF 보다 *일관되게 낮음*.
- 이는 본 데이터에 점포 간 상호작용 신호가 없다는 결론이 아니라, *현재의 그래프 구성(동·업종 인접) 과 가중치 학습(SHAP) 이 그것을 충분히 포착하지 못함* 을 의미.

이 결과는 본 논문의 한계와 *향후 연구* (Chapter 7 시공간 확장 \cite{yu2018stgcn}) 를 직접 동기 부여.

---

## §6.4 챕터 요약

G/S/D 에 대해 세 가지 확립:

1. 19 시즌 정렬 패널에 걸쳐 G/S/D 성능은 macro-$F_1$ 0.43–0.54 범위에서 붕괴 없이 유지되나, strict OOT 분석은 start month 가 여전히 주요 변동원임을 보인다.
2. 더 넓은 외부 비교에서 LightGBM 계열 3종만 RF 상회, 14 비-LightGBM 비교 변형은 모두 성능 하락 — *데이터 특성 mismatch* 로 해석. 본 논문의 데이터 특화 representation 설계의 정당성 뒷받침.
3. 동-업종 결합 그래프 + SHAP-가중 GNN 은 본 데이터에서 추가 마진 없음. 공간 신호가 무의미하다는 결론이 아니라 현재 그래프 구성·가중치 학습이 불충분함을 시사 — *시공간 확장을 향후 연구로* 동기 부여.

고성장 타깃의 external validity(inflection + UDX representation 의 $\Delta F_1$ 이 타 도시·업종에서 재현되는지) 는 향후 연구 항목 (§\ref{sec:limitations}).
