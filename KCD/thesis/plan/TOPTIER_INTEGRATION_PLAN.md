# Top-Tier 정합 통합 계획 (v3)

작성일: 2026-04-23
상태: thesis + top_tier 산출물을 단일 논문 서사로 통합하기 위한 설계도

---

## 0. 현재 자산 지도

| 산출물 | 위치 | 상태 | 용도 |
|---|---|---|---|
| KCD 원자료 | `original_data/` | 완료 | 본 연구 모든 분석의 기초 |
| 외부 자료 | `thesis/data_external/` | 완료 | 생활인구, 인허가, 상권분석서비스 |
| top_tier 분석 스크립트 | `top_tier/src/step00-15_*.py` | 완료 | 파이프라인 전체 |
| top_tier 출력물 | `top_tier/outputs/figures/, tables/` | 완료 | Figure 1-18, 수많은 CSV |
| top_tier report | `top_tier/outputs/docs/top_tier_report.md` | 완료 | 17개 섹션 수치 요약 |
| paper_draft | `top_tier/paper_draft/01-04_*.md` | 완료 | 영문 Intro·Theoretical·RelatedWork·Method |
| thesis LEVI 분석 | `thesis/analysis/outputs/` | 완료 | 자치구 LEVI + Macro 상관 |
| thesis 초안 (한글) | `thesis/drafts/ch0-ch7_*.md` | 1차 완료 | 석사논문 한글본 |

---

## 1. Top-tier 포지셔닝을 위한 6대 기여 정리

top_tier 분석에서 실제로 확보된 기여를 번호·약어로 고정한다.

### C1. Survivorship Bias 5배 정량화 (데이터 기반 신규 발견)
- 패널 내 폐업률 **8.9%** vs 패널 바깥 **48.3%** (n_panel 48,980 / n_out 10,027)
- 기존 lifecycle 연구의 설계 편향 규모를 처음으로 정량화
- **Contribution type**: Empirical regularity

### C2. Volatility Paradox 분해 (이론적 조정)
- Cox PH 전체 HR(cv) 1.11이지만 Growth/Stable 내부에서는 cv가 보호요인(HR<1), Decline 내부에서만 위험요인(HR>1)
- 4가설(H1 survivorship, H2 phase-dependent, H3 inverted-U, H4 outcome-specific Cox)로 체계적 분해
- **Contribution type**: Theoretical reconciliation

### C3. Golden Cross 인과효과 triangulation
- Granger: nc→sales 유의 비율 10.5%, 비대칭(nc만) 8.8%
- PSM+DiD: ATT = **+0.1165 log-sales**, t=18.07, p<1e-72
- Panel Two-way FE: nc_l1 계수 0.278 (p<1e-306)
- **Contribution type**: Causal identification via multiple methods

### C4. Hybrid Prediction이 Deep Sequence를 넘음
- A_base_46: F1 0.548 / AUC 0.736
- D_base+cluster+cp (Proposed): F1 **0.639** / AUC **0.824**
- 증분 F1 +0.091, AUC +0.088
- (Deep baseline은 legacy label 기반이라 현재는 classical 대비 비교만 유지)
- **Contribution type**: Methodological — inductive bias at moderate T

### C5. EWS Artifact with Cost-Sensitive Operating Point (DSR)
- Decline risk score ∈ [0,100] per store for 49,007 stores
- Average Precision: Decline 0.688, Growth 0.819
- Cost-sensitive optimal threshold = **0.10**, net utility = **43,626**
- **Contribution type**: Design Science Research artifact

### C6. External Validation via Seoul Administrative / Commercial District Data
- LEVI vs 생활인구 변화율 **Pearson 0.853**, Spearman 0.802 (n=25)
- LEVI vs 인허가 폐업률 **Pearson -0.430** (n=25)
- KCD 추정 폐업률 vs 인허가 폐업률 **Pearson 0.430**
- KCD 분기 매출 vs 서울 상권 추정매출 **Pearson 0.766**, QoQ 변화 **Pearson 0.839**
- **Contribution type**: External validity of a single-vendor panel

---

## 2. 두 산출물의 역할 분할

### 산출물 A: Top-tier 영문 논문 (HICSS 2027 10p / ICIS 2026 12p)

- **중심 기여**: C1–C5 (artifact + causal + paradox + survivorship)
- **보조 기여**: C6를 §Evaluation의 External Validity 섹션으로 2-3단락만 배치
- **서사 톤**: DSR (Hevner et al. 2004; Peffers et al. 2007) artifact 중심
- **현재 상태**: `top_tier/paper_draft/01-04_*.md`가 이미 작성되어 있으며, 01_introduction은 DSR·EWS 위주로 잘 잡혀 있음
- **남은 작업**: Results, Discussion, Conclusion 영문 작성 + figure/table 번호 고정 + 40편 reference BibTeX

### 산출물 B: KAIST 석사 학위논문 (한글, 60-90쪽)

- **중심 기여**: C6 (도시 경제 LEVI 연결)을 본문 메인에 배치 + C1-C5를 균형 있게 결합
- **서사 톤**: 기술경영적 "거래 데이터 → 지역 경제 모니터링" 관점. DSR 언어는 제한적으로 사용
- **현재 상태**: `thesis/drafts/ch0-ch7_*.md` 1차 초안 있음. 단, C1-C5 반영 부족
- **남은 작업**: Ch.1·Ch.5에 C1-C5 통합, Ch.6에 top-tier 담론 반영, Ch.4 방법론 섹션 확장, 초록 업데이트

### 두 산출물의 공유 자원

- 동일한 figure 파일군: `top_tier/outputs/figures/fig01-18_*.png`
- 동일한 수치: `top_tier/outputs/docs/top_tier_report.md` §1-17
- 동일한 scripts: `top_tier/src/step00-15_*.py`

---

## 3. 석사논문(B)의 Top-tier 정합 업데이트 작업

### 3.1 Ch.1 서론 — 전면 재작성

현행 ch1_introduction.md는 LEVI·micro·meso·macro 3단 구조를 중심으로 하나, top-tier 정합을 위해 **5대 기여를 명시**하는 형태로 재작성한다.

변경 핵심:
- "단일 곡선 부정" + "신규 고객·업력 드라이버"만 다루던 서사를 **survivorship bias, volatility paradox, Golden Cross causal, Hybrid prediction, EWS, LEVI** 순서로 확장
- Research questions를 3개(RQ1/2/3)에서 **5개(RQ1-5)**로 확장:
  - RQ1: 관측된 거래 궤적은 기존 생애주기 이론과 얼마나 다른가?
  - RQ2: 패널 구성 편향이 기존 결론을 얼마나 왜곡하는가?(Survivorship)
  - RQ3: 변동성은 성장과 하락 중 어디와 연결되는가?(Volatility paradox)
  - RQ4: 신규 고객 유입은 매출 반등을 선행하는가?(Golden Cross causal)
  - RQ5: 30주 관측만으로 장기 상태를 예측할 수 있는가? EWS의 운영 한계는?(Prediction + Artifact)
  - RQ6: 이 진단은 서울시 도시 경제·인구 동태와 일관되는가?(External validity)
- 기여 5개 + LEVI로 총 6개를 약어(C1-C6)로 고정

### 3.2 Ch.4 방법론 — 대폭 확장

현행 ch4_methodology.md는 Micro/Meso/Macro 3층으로 단순하나, top-tier 정합을 위해 다음 절을 **추가**한다.

- §4.2.6 **생존 편향 정량화 설계** — panel 내부 vs 외부 폐업률 비교
- §4.2.7 **Kaplan-Meier 생존 함수 + log-rank + Cox PH** — concordance, Schoenfeld 잔차 검증
- §4.2.8 **Golden Cross 인과 식별 — Granger + PSM + DiD + Panel FE** — 3중 삼각 검증
- §4.2.9 **Volatility Paradox 분해 4가설 설계**
- §4.2.10 **Hybrid Proposed Model D 아키텍처** — 46 engineered + KMeans cluster(K=4) one-hot + change-point feature
- §4.2.11 **Deep sequence baseline** — LSTM/GRU/Transformer (legacy label 기반, 보조)
- §4.2.12 **EWS 점수화 및 cost-sensitive threshold** — B=10, C_support=2, C_miss=8

### 3.3 Ch.5 결과 — C1-C6 반영 재구성

섹션 번호를 바꿔 top-tier 구조와 정합:
- §5.1 Canonical life-cycle curve 반증 (post-entry + observed-window)
- §5.2 **Survivorship bias 정량화** (C1)
- §5.3 Kaplan-Meier · Cox PH · 생존·hazard 패턴
- §5.4 **Volatility paradox 분해** (C2) — H1-H4
- §5.5 **Golden Cross 인과 triangulation** (C3) — Granger + PSM+DiD + FE
- §5.6 **Hybrid prediction 비교** (C4) — A-D 모델 + deep baseline
- §5.7 **EWS operating point + cost-benefit** (C5)
- §5.8 업력 bucket driver + 신규고객 importance (기존 thesis §5.2)
- §5.9 **LEVI + 외부 검증** (C6) — 현행 §5.4-5.5 압축·통합
- §5.10 Robustness

### 3.4 Ch.6 토의 — DSR·이론 반영

- §6.1 이론적 함의: 조직 생애주기 이론 + Volatility paradox 재해석
- §6.2 방법론적 함의: Hybrid inductive bias vs deep sequence at moderate T
- §6.3 **DSR artifact 평가**: EWS utility, external validity
- §6.4 정책·플랫폼 함의
- §6.5 한계 + 향후 연구

### 3.5 Ch.0/7 및 초록 업데이트

- 국문 초록: 6대 기여를 명시적으로 인용 (약 500자로 확장)
- Abstract: top_tier paper_draft 01_introduction.md의 contribution paragraph 영문 번역 활용
- 목차: §5에 10개 소절, §4에 12개 소절로 업데이트

---

## 4. 작업 우선순위와 예상 시간

| 우선 | 작업 | 예상 | 의존 |
|---|---|---|---|
| P0 | Ch.1 서론 재작성 | 1.5h | 본 플랜 |
| P0 | Ch.5 결과 재구성 (C1-C6 반영) | 3.5h | top_tier_report |
| P1 | Ch.4 방법론 §4.2.6-12 추가 | 2.5h | Ch.5 확정 후 |
| P1 | Ch.6 토의 업데이트 | 1.5h | Ch.5 확정 후 |
| P1 | 국문·영문 초록 재작성 | 1.0h | Ch.1·Ch.5 확정 후 |
| P2 | Ch.0 목차 업데이트 | 0.5h | 모든 장 확정 후 |
| P2 | 참고문헌 확장 (DSR·causal·survival 추가) | 1.0h | - |

총 예상 작업 시간: **약 11.5시간**

---

## 5. 본 계획에서 하지 않을 것

- top_tier/paper_draft/ 영문 논문을 새로 작성 — 이미 4장 존재, 추가 Results/Discussion은 별도 작업
- Deep sequence baseline 재실행 — legacy label 기반 유지, 본문 비교표에서 제외
- Audit01-04, fold-safe leakage, enhanced PSM, multivariate DL robustness 재실행 — 최종 투고 전 단계로 유보

---

## 6. 다음 단계

본 플랜 확정 후, Ch.1 재작성부터 착수한다. 각 장은 재작성 시 기존 파일에 **덮어쓰기**하지 않고 `_v3` suffix로 별도 저장한 뒤, 수정이 완결되면 rename한다.
