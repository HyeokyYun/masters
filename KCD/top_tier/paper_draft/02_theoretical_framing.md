# 2. Theoretical Framing Memo

**목적**: 논문의 이론적 contribution을 어느 lineage에 심어 심사 수용성을 극대화할지 결정.
**결정권자**: 김지희 교수님 + 학생

---

## Candidate Framings

### Frame A — Design Science Research (Hevner et al. 2004; Peffers et al. 2007)
**구조**: Build–Evaluate cycle. Artifact = EWS system. Kernel theories = lifecycle + information economics.

**장점**:
- HICSS 심사 톤과 완벽 일치 ("ICT artifact that solves real problem")
- ICIS에서 DSR 세션이 꾸준히 존재 (Track 12 Implementation, Track 5 DM&A)
- **"우리가 만든 것"과 "우리가 배운 것"을 동시에 주장 가능**
- Evaluation rigor 기준이 명확 (utility, efficacy, internal/external validity)
- Reviewer가 "so what about theory" 공격 시 "artifact-first + design principles" 반격 가능

**단점**:
- DSR은 최근 "superficial" 비판 있음 (artifact 뒤에 진짜 이론 기여가 없다는)
- Kernel theory를 명시해야 함 — 단순 ML 기법 나열은 DSR 아님
- Design principle statement를 구체적으로 뽑아내야 함

**Contribution 문장 예시**:
> We contribute (1) a novel EWS artifact for urban small-business lifecycle prediction, (2) design principles linking temporal-clustering state features to supervised prediction under short observation windows, and (3) empirical evidence that engineered inductive biases outperform end-to-end deep learning at this scale.

### Frame B — Data-Driven Entrepreneurship Research (Cooper, Bates, Shepherd lineage)
**구조**: Existing theory → empirical refinement. "선행 연구가 놓친 것을 실거래 데이터로 보인다."

**장점**:
- Theoretical contribution이 분명함 — 기존 SMB survival 이론을 확장/수정
- Survivorship bias 5× quantification과 volatility paradox decomposition이 자연스럽게 contribution이 됨
- "59K stores × weekly granularity"라는 scale이 이 frame에서는 methodological novelty로 읽힘

**단점**:
- Artifact (EWS) 기여가 2차적 — "so what about EWS" 공격 받을 수 있음
- Track 15 Innovation & Entrepreneurship로 가야 하는데 IS 톤과 거리
- Korean domain을 전세계 generalizable하게 defend해야 함 (Shane/Bates 문헌은 US)

**Contribution 문장 예시**:
> We contribute (1) the first large-scale, behaviorally-observed evidence on small business lifecycle trajectories, (2) a quantification of survivorship bias in entrepreneurship panels (10% vs 52% closure rate gap), and (3) decomposition of the empirical volatility paradox into phase-, outcome-, and survival-dependent components.

### Frame C — Methodological Innovation (ML + IS)
**구조**: Hybrid representation learning이 주인공. Theory는 inductive bias + no-free-lunch 관점에서 정당화.

**장점**:
- "DL이 hand-crafted feature에 진다"가 저자 surprise finding → methodologically interesting
- 재현성·코드·artifact sharing 관점 강조 가능
- Track 5 Data management and analytics와 fit

**단점**:
- Theory 기여 약함 — "method paper"라는 인상 → major revision 위험
- Reviewer가 "ablation은 empirical result일 뿐 theory 아님" 공격 가능

**Contribution 문장 예시**:
> We contribute (1) a hybrid time-series representation combining K-Means/K-Shape clustering with change-point detection for short-window lifecycle prediction, (2) benchmarking evidence that engineered representations dominate end-to-end sequence learning at T=30, and (3) a deployment-ready EWS artifact with calibration and cost-sensitive threshold analysis.

---

## 제 권장: **Frame A + Frame B 혼합 (DSR + Lifecycle Refinement)**

### 권장 Positioning 문장 (Abstract용)

> Using the Design Science Research paradigm (Hevner et al. 2004), we build and evaluate an Early Warning System (EWS) artifact for small business lifecycle prediction, grounded in entrepreneurship lifecycle theory (Cooper et al. 1994; Shepherd 2003). Applied to 59,089 urban restaurants over 31 months of card-transaction data, our artifact (i) achieves Macro-F1 = 0.648 in 30-week-ahead classification — a 25% improvement over end-to-end deep sequence learning — and (ii) produces calibrated, cost-aware risk scores ready for policy deployment. Beyond the artifact, we contribute empirical refinements to lifecycle theory: quantification of survivorship bias (5-fold closure gap), causal evidence of new-customer inflow as a leading indicator (DiD ATT = +0.099, 11.35σ above placebo), and decomposition of the empirical volatility paradox across phase, outcome, and survivorship mechanisms.

### 논문 구조에서의 반영

- **§1 Introduction** — DSR 선언 + lifecycle refinement 목적 (이미 draft에 반영)
- **§2 Related Work** — 세 lineage 흐름 (SMB survival, EWS in finance, time-series repr learning) 후 gap 진술
- **§3 Theoretical Background** (NEW subsection 필요) —
  - 3.1 Small business lifecycle theory: stage models (Greiner 1972; Churchill & Lewis 1983) → behavioral signal theory
  - 3.2 Information Economics perspective: leading vs lagging indicators for decision support
  - 3.3 DSR principles applied: build + evaluate + design principles
- **§4 Methodology** — 각 분석을 DSR evaluation의 어떤 rigor에 대응하는지 명시
  - Internal validity → Cox PH assumption check, cluster leakage test
  - External validity → temporal validation, subgroup robustness
  - Construct validity → outcome definition sensitivity
  - Statistical conclusion validity → bootstrap, placebo test
- **§6 Discussion** — Artifact design principles (3개 뽑기):
  - **DP1**: Short-window lifecycle prediction should augment raw sequences with temporal-clustering state features to inject inductive bias on shape similarity
  - **DP2**: Causal identification of leading indicators should triangulate Granger + DiD + FE regression to rule out reverse causality
  - **DP3**: EWS risk scores should be accompanied by cost-sensitive threshold analysis to enable policy-actionable decisions

---

## 키 문헌 lineage 3x5 (= 최소 15편 인용 필요)

### A. Design Science Research
1. Hevner, March, Park & Ram (2004) — DSR in Information Systems Research (MISQ) — **seminal**
2. Peffers, Tuunanen, Rothenberger & Chatterjee (2007) — DSRM methodology (JMIS) — **process**
3. Gregor & Hevner (2013) — Positioning and presenting DSR (MISQ) — **how to write**
4. Baskerville, Baiyere, Gregor, Hevner & Rossi (2018) — DSR contributions — **taxonomy**
5. Simon (1996) — Sciences of the Artificial — **foundational**

### B. Small Business Lifecycle & Survival
6. Cooper, Gimeno-Gascon & Woo (1994) — Initial human and financial capital — **seminal**
7. Bates (1990) — Entrepreneur human capital inputs — **survival determinants**
8. Shepherd (2003) — Self-employed losing business — **emotional cost**
9. Denrell (2003) — Vicarious learning, undersampling failure — **survivorship bias**
10. Greiner (1972) or Churchill & Lewis (1983) — Stage models — **lifecycle theory**

### C. Early Warning Systems & Prediction
11. Altman (1968) — Z-score for bankruptcy — **financial EWS origin**
12. Ohlson (1980) — O-score extension
13. Barboza, Kimura & Altman (2017) — ML for bankruptcy prediction — **recent ML lineage**
14. Paparrizos & Gravano (2015) — K-Shape time-series clustering (SIGMOD) — **method**
15. Lundberg & Lee (2017) — SHAP unified approach (NeurIPS) — **interpretability**

### D. Causal Inference
16. Granger (1969) — Investigating causal relations by econometric models — **seminal**
17. Rosenbaum & Rubin (1983) — Central role of propensity score — **PSM foundation**
18. Card & Krueger (1994) — Minimum wages and employment — **DiD modern application**

### E. Information Systems for Social Good
19. Majchrzak, Markus & Wareham (2016) — Designing for digital transformation and socio-technical systems (MISQ) — **IS4SG**
20. Pan, Pan & Leidner (2012) — IS and social inclusion — **applied perspective**

---

## 결정 체크리스트 (교수님 확인 필요)

- [ ] Frame A+B 혼합이 적합한가? 아니면 Frame A 또는 B 단일?
- [ ] Design Principles 3개 정의가 적절한가? 본문에서 어떤 수준으로 명시할지
- [ ] Lifecycle theory lineage 중 Greiner(1972) vs Churchill & Lewis(1983) 중 어느 것을 primary reference로?
- [ ] Korean SMB domain의 외적 타당성 주장 수위 — conservative (Korean SMB only) vs aspirational (urban retail SMB in high-frequency data environments)
- [ ] Kernel theory 명시 필요 여부 — 만약 DSR 프레임이면 "lifecycle + information economics"로 선언할지
- [ ] KCD와의 출판 관련 합의사항에 "EWS artifact release" 조항이 있는지 — 없으면 "proof-of-concept within academic scope"로 서술
