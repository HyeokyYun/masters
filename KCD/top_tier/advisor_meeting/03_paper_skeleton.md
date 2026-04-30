# Paper Skeleton — "Data-Driven Early Warning System for Small Business Lifecycle Prediction"

**Target**: HICSS 2027 completed research (10p IEEE) 기준. ICIS 확정 시 12p 확장 용이.

---

## Working Title 후보

1. "A Data-Driven Early Warning System for Small Business Lifecycle Prediction: Evidence from 59K Urban Retail Stores"
2. "Hybrid Clustering and Change-Point Features for 30-Week Lifecycle Prediction of Small Businesses"
3. "Beyond Survival Analysis: Untangling the Volatility Paradox in Small Business Trajectories"

**제1후보 권장** — contribution(artifact) + scale + setting을 한 줄에 응축.

---

## Abstract (150-200 words)

**구조**: [Problem-1] [Gap in literature-1] [Data-1] [Method-2] [Findings-2] [Contribution-1]

초안:
> Small business closure imposes systemic economic and social costs, yet existing lifecycle studies rely on static financial snapshots and are contaminated by survivorship bias. We analyze a weekly card-transaction panel covering 59,089 restaurants in Seoul (2021-2023, 6.58M observations) to develop an **Early Warning System (EWS)** that predicts 30-week-ahead lifecycle outcomes (Growth / Stable / Decline). Our Proposed Model integrates 46 hand-engineered features with hybrid clustering (K-Means + K-Shape) and change-point representations, achieving Macro-F1 **0.648** and AUC **0.830** — a 25% F1 improvement over competitive deep sequence baselines (LSTM / GRU / Transformer). We further quantify survivorship bias (non-panel closure 52% vs panel 10%) and decompose the long-standing volatility paradox via phase-dependent, outcome-specific hazard analysis. Causal evidence on the "new customer → sales rebound" pathway is triangulated via Granger causality, propensity-score matched difference-in-differences (ATT = +0.117 log-sales, p<10⁻⁷²), and two-way fixed-effects panel regression. The resulting EWS artifact, calibrated and cost-aware, offers policy-actionable risk scores for 49K small businesses.

---

## Section 1. Introduction (1.5-2p)

**Paragraph 1 — Problem statement**
- 소상공인 폐업은 개인 파산·고용 충격·지역상권 붕괴로 이어지는 복합 문제
- OECD 통계 / KOSIS 폐업률 근거 제시

**Paragraph 2 — Gap in literature**
- 기존 연구 3가지 한계:
  - (i) 설문·재무제표 기반 static snapshot (Shane 2003, …)
  - (ii) Survivorship bias (Denrell 2003)
  - (iii) 이분법(폐업 vs 비폐업) 한계 — 성장/정체/쇠퇴 다중 경로 무시

**Paragraph 3 — This study**
- 59K 점포 주간 매출 실거래 데이터로 동적 lifecycle 모델링
- 30주 관측만으로 장기 outcome 예측하는 EWS artifact 제안
- Design Science Research (Hevner 2004) 관점에서 방법론·artifact·평가 3축 기여

**Paragraph 4 — Contributions (bullet)**
- **C1**: 대규모 실거래 데이터 기반 소상공인 lifecycle의 최초 동적 실증
- **C2**: Hybrid clustering + change-point representation이 end-to-end DL을 상회하는 inductive bias
- **C3**: Golden Cross (신규고객→매출) 인과효과의 3중 방법 triangulation
- **C4**: Volatility Paradox의 다층 분해 — phase·outcome·survivorship 교란 실증
- **C5**: Calibrated & cost-aware EWS artifact (49K store level deliverable)

**Paragraph 5 — Paper structure**

---

## Section 2. Related Work (1.5p)

**2.1 Small Business Survival & Lifecycle**
- Cooper et al. 1994; Bates 1990; Disney et al. 2003 — 재무·창업가 특성
- Shepherd 2003 — 폐업의 감정·경제적 비용
- **Gap**: 주간 단위 매출 시계열 활용 전무

**2.2 Early Warning Systems in Finance/Business**
- Altman Z-score (1968) → Ohlson O-score → ML 계열 (Barboza et al. 2017)
- **Gap**: 소상공인(SMB)은 재무제표 부재 → 대체 신호 필요

**2.3 Time-Series Clustering for Business Trajectories**
- K-Shape (Paparrizos 2015), DTW 기반 clustering
- **Gap**: 소상공인 매출 cluster의 external validity 검증 전무

**2.4 Causal Inference with Observational Panel Data**
- Granger 1969; DiD Card & Krueger 1994; PSM Rosenbaum & Rubin 1983
- **Gap**: 소상공인 domain에서 nc→sales 인과 경로 실증 전무

---

## Section 3. Data and Setting (1p)

**3.1 Data Source**
- KCD(한국신용데이터) 주간 카드거래 패널 (서울 음식점)
- 2021-01-01 ~ 2023-08-28, 59,089 점포 / 6.58M obs
- 주요 변수: sales_card_mm, new_customer_ratio, delivery_ratio, weekend_ratio, morning_ratio

**3.2 Closure Detection**
- `is_closed = (last_observation < 2023-08-28 - 4weeks)` — 9,764 stores (16.5%)

**3.3 Outcome Labeling**
- 31-60주차 평균 대비 1-30주차 평균 비율로 outcome_3 정의
  - Growth: ratio ≥ 1.10 (n=20,273)
  - Stable: 0.90 ≤ ratio < 1.10 (n=17,848)
  - Decline: ratio < 0.90 (n=8,242)

**3.4 Descriptive statistics table** — Table 1

---

## Section 4. Method (2.5-3p)

**4.1 Survivorship Bias Quantification**
- 패널 inclusion criterion과 outside population 비교

**4.2 Survival Analysis**
- Kaplan-Meier curves by outcome/category
- Cox PH with 5 covariates

**4.3 Hybrid Proposed Model**
- 46 feature engineering (statistics, slopes, MA, volatility, nc trends, patterns, distribution, differences)
- K-Means (K=4) + K-Shape (K=7) one-hot (~11 dims)
- Change-point features (slope break detection, 7 dims)
- XGBoost classifier, 5-fold stratified CV

**4.4 Deep Sequence Baselines**
- Bidirectional LSTM (2-layer, hidden 64)
- Bidirectional GRU (2-layer, hidden 64)
- Transformer Encoder (d_model=32, 2 heads, 2 layers)
- 동일 CV fold, 동일 store 집합, per-store normalization

**4.5 Causal Identification**
- Granger VAR(1) store-level bidirectional
- PSM nearest-neighbor (caliper 0.1, 10 covariates) + DiD
- Two-way FE panel regression with lagged nc_rate

**4.6 Volatility Paradox Decomposition**
- H1: Survivorship sub-sample
- H2: Phase-split (w1-15, w16-30, w31+)
- H3: Decile-based inverted-U test
- H4: Outcome-stratified Cox PH

**4.7 EWS Design**
- OOF probability → 0-100 risk score
- Calibration (Brier, reliability curve)
- Cost-sensitive threshold optimization (B/C matrix)

---

## Section 5. Results (3p)

### 5.1 Survivorship Bias (F1) — Figure 2 + Table 2

### 5.2 Proposed Model vs Baselines (F4, F5) — Table 3
| Model | F1 | AUC | Gr_Recall | Dec_Recall |
|---|---|---|---|---|
| Proposed D | 0.648 | 0.830 | 0.785 | 0.573 |
| B_base_cluster | 0.635 | 0.821 | … | … |
| C_base_cp | 0.614 | 0.805 | … | … |
| A_base_46 | 0.547 | 0.734 | … | … |
| GRU_bi | 0.517 | 0.709 | 0.630 | 0.574 |
| LSTM_bi | 0.517 | 0.707 | 0.620 | 0.565 |
| Transformer | 0.513 | 0.708 | 0.617 | 0.570 |

### 5.3 Causal Evidence (F2) — Table 4, Figure 4 (event study)

### 5.4 Volatility Paradox Decomposition (F3) — Figure 9 (4-panel)

### 5.5 SHAP Explanation — Figure 7

### 5.6 EWS Operating Points & Cost-Benefit (F6) — Figure 10-12, Table 5

### 5.7 Robustness
- Subgroup consistency (업종별, 업력별, 코로나 vs 회복기)
- Bootstrap CI (200 rounds)
- Temporal train/test split (2021-2022 train / 2023 test)

---

## Section 6. Discussion (1.5p)

**6.1 Theoretical Implications**
- Lifecycle literature에 "동적 관측-기반" 관점 추가
- Volatility paradox의 교란 효과 실증 → 기존 "risk-taking leads to growth" 주장 재검토

**6.2 Methodological Implications**
- 소규모 시퀀스(T=30)에서는 end-to-end DL보다 도메인 지식 기반 feature engineering이 우월
- Hybrid clustering이 single-method clustering 대비 downstream prediction에 기여

**6.3 Practical Implications for DSS**
- EWS가 실제 정책 의사결정에 주는 값
- 카테고리별 risk 분포 → 타깃 지원 정책 설계

**6.4 Limitations**
- 단일 도메인(서울 음식점), 단일 기간(2021-2023) → 외적 타당도 한계
- PSM의 unmeasured confounding
- Clustering silhouette 낮음 (이산 cluster 약함)
- 배포·사용자 실험 부재

---

## Section 7. Conclusion (0.5p)

- 3줄 요약: data + method + contribution
- Future work: cross-domain 검증, 파일럿 배포, 실시간 update

---

## References

- Altman 1968, Hevner 2004, Granger 1969, Card & Krueger 1994, Rosenbaum & Rubin 1983, Paparrizos 2015, Shepherd 2003, Cooper et al. 1994, Bates 1990, Lundberg & Lee 2017 (SHAP), 등 ~40편

---

## 논문 부록 (Appendix)

- A. Feature list (46 + 11 + 7)
- B. Hyperparameter settings
- C. Extended robustness tables
- D. EWS deployment API skeleton (optional)
