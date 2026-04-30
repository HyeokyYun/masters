# 통합 색인 — Top-tier 정합 석사학위논문

작성일: 2026-04-23 (v3 재작성) / 2026-04-24 (P2 통합 완료, 파일명 일원화)
상태: 전 장 V3 정합 완료

V3 본문은 suffix 없는 정식 파일명으로 통일되었다. 구 V2 초안은 [../v2/](../v2/)에 보관한다.

---

## 버전 서사 변화 (참고)

| 항목 | V2 | V3 (현행) |
|---|---|---|
| 중심 서사 | LEVI 중심 3단(Micro-Meso-Macro) | 6대 기여(C1-C6) 중심 DSR build-evaluate |
| 기여 수 | 3 (LEVI, 업력별 driver, 조기 예측) | **6** (생존편향·변동성역설·Golden Cross 인과·hybrid·EWS·LEVI) |
| 프레이밍 | 기술경영 진단·예측 | **DSR artifact + 이론 반증·조정** |
| 주요 수치 | LEVI r=0.855 | +Cox HR, PSM+DiD ATT, Hybrid F1/AUC, EWS utility, 4가설 분해 |
| 영문 초록 | 3-paragraph description | 6-contribution numbered list |

---

## 본문 파일 (V3 정합, 전 장 현행)

- [ch0_abstract.md](ch0_abstract.md) — 국문·영문 초록 + 목차
- [ch1_introduction.md](ch1_introduction.md) — 서론 (6 contributions, 6 RQs)
- [ch2_literature.md](ch2_literature.md) — 선행 연구 (§2.4.3 DSR, §2.4.4 생존·인과 포함, §2.5 C1-C6 매핑)
- [ch3_data.md](ch3_data.md) — 데이터 (§3.3.3 상권분석서비스 포함)
- [ch4_methodology.md](ch4_methodology.md) — 방법론 (DSR 프레임 + C1-C6 방법)
- [ch5_results.md](ch5_results.md) — 결과 (C1-C6 순차 보고)
- [ch6_discussion.md](ch6_discussion.md) — 토의 (DSR artifact 평가)
- [ch7_conclusion.md](ch7_conclusion.md) — 결론 (C1-C6 기여별 재요약)
- [references.md](references.md) — 참고문헌

## V3 P2 통합 체크리스트 — 완료 2026-04-24

- [x] Ch.2: DSR(§2.4.3)·생존분석 및 인과식별(§2.4.4) 소절 추가 + §2.5를 6대 기여 C1-C6 매핑으로 재작성
- [x] Ch.3: §3.3.3 서울시 상권분석서비스 신설(기존 자치구 매칭은 §3.3.4로 이동) + §3.4.1에 C1 survivorship bias 5.4배 수치 언급
- [x] Ch.7: 6대 기여 C1-C6 기준으로 전면 재작성 (V3 수치 반영: Cox HR, PSM+DiD ATT, Hybrid F1/AUC, EWS AP·net utility, LEVI 상관)
- [x] References: Cox 1972, Kaplan-Meier 1958, Granger 1969, Rosenbaum-Rubin 1983, Chen-Guestrin 2016, Card-Krueger 1994 추가 (Denrell 2003, Hevner 2004, Peffers 2007, Grambsch-Therneau 1994, Nisbett-Wilson 1977은 기존 수록)
- [x] 파일명 일원화: `chN_*_v3.md` → `chN_*.md`로 rename, 구 V2 초안은 [../v2/](../v2/)로 이동

---

## 핵심 수치 Quick Reference (V3)

| 카테고리 | 수치 | 출처 |
|---|---|---|
| KCD 점포 | 59,089 | `original_data/meta.csv` |
| 관측 기간 | 2021-01 ~ 2023-08 (142주) | 동 |
| 분석 패널 | 48,980 (Decline 10,917 / Stable 18,003 / Growth 20,087) | `top_tier_report` §1 |
| **Survivorship bias** | 패널내 8.9% vs 바깥 48.3% (5.4x) | `top_tier_report` §3 |
| Cox PH concordance | 0.819 | `top_tier_report` §5 |
| Cox HR (cv) | 1.092 전체 / Growth 0.839 / Stable 0.612 / Decline 1.183 | `top_tier_report` §5, §14 |
| Growth peak cv decile | D5 (cv 0.36-0.41) | `top_tier_report` §14 H3 |
| **Golden Cross ATT** | +0.1165 log-sales (t=18.07, p<1e-72) | `top_tier_report` §9 |
| Panel FE nc_l1 | 0.278 (p<1e-306) | `top_tier_report` §10 |
| **Hybrid D F1 / AUC** | 0.639 / 0.824 | `top_tier_report` §13 |
| Base 46 F1 / AUC | 0.548 / 0.736 | 동 |
| **EWS AP (Decline)** | 0.688 (baseline 0.223) | `top_tier_report` §15 |
| EWS cost-opt threshold | 0.10, net utility 43,626 | 동 |
| **LEVI vs 생활인구 변화율** | Pearson 0.853, Spearman 0.802 | `thesis/analysis/outputs/levi_macro_correlations.csv` |
| LEVI vs 인허가 폐업률 | Pearson -0.430 | 동 |
| KCD QoQ vs 외부 QoQ | Pearson 0.839 | `top_tier_report` §2 |

---

## Figure 파일 (V3 기준 본문 배치)

| 본문 위치 | Figure | 파일 | 설명 |
|---|---|---|---|
| §5.1 | Fig 5.1 | `docs/thesis_figures/main_figures/figure1_two_lenses_lifecycle.png` | two-lens lifecycle |
| §5.2 | Fig 5.2 (신규) | TBD | survivorship bias 5-fold comparison bar chart |
| §5.3 | Fig 5.3 | `top_tier/outputs/figures/fig2_km_outcome.png` | KM curves by outcome |
| §5.4 | Fig 5.4 | `top_tier/outputs/figures/fig9_volatility_paradox.png` | 4-panel paradox decomposition |
| §5.5 | Fig 5.5 | `top_tier/outputs/figures/fig14_did_event_study.png` | DiD event study |
| §5.6 | Fig 5.6 | `top_tier/outputs/figures/fig6_prediction_performance.png` | Hybrid comparison |
| §5.7 | Fig 5.7 | `top_tier/outputs/figures/fig11_pr_curves.png` + `fig12_cost_benefit.png` | EWS PR + cost |
| §5.8 | Fig 5.8 | `docs/thesis_figures/main_figures/figure2_age_bucket_drivers.png` | age-bucket drivers |
| §5.9 | Fig 5.9 | `thesis/figures/fig_macro_levi_scatter.png` + `top_tier/outputs/figures/fig17_external_gu_validation.png` | LEVI external |
| §5.9 보조 | Fig 5.10 | `thesis/figures/fig_macro_levi_timeseries.png` + `top_tier/outputs/figures/fig18_external_temporal_validation.png` | LEVI timeseries |

---

## 심사·투고 전략 (요약)

| 시나리오 | 경로 | 타임라인 | 리스크 |
|---|---|---|---|
| KAIST MoT 석사 본 논문 | V3 그대로 완성 | 4-6주 | 낮음 |
| HICSS 2027 (10p IEEE) | `top_tier/paper_draft/` 영문화 | 2026-06-15 마감 | 중간(60일) |
| ICIS 2026 (12p) | 동, 마감 2026-05-01 | **남은 D-10** | 높음(이중 심사 부담) |
| KER / 한국경영학회지 | V3 한글 본문 압축 | 4개월 | 낮음 |
| DSS / Information & Management | HICSS 본 논문 확장 | 2027 하반기 | 중상 |

**권장 경로**: (1) KAIST 석사 V3 완성 → 학위 우선 → (2) 동시에 HICSS 2027 영문 paper draft 완성 → 제출.
