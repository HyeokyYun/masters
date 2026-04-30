# 주별 거래 데이터로 본 소상공인의 성장·하락과 도시 경제의 연결:
# 서울시 외식업 사례 연구

석사학위논문 초안 (v2 통합본)
KAIST 경영대학 기술경영학부
작성일: 2026-04-22

---

이 통합 문서는 다음 순서로 구성된다. 각 장은 `thesis/drafts/` 하위의 개별 파일에 보관되며, 본 파일은 단일 열람을 위한 연결본이다.

1. **Ch.0 — 초록·목차**: `ch0_abstract_and_frontmatter.md`
2. **Ch.1 — 서론**: `ch1_introduction.md`
3. **Ch.2 — 이론적 배경 및 선행연구**: `ch2_literature.md`
4. **Ch.3 — 데이터**: `ch3_data.md`
5. **Ch.4 — 연구방법**: `ch4_methodology.md`
6. **Ch.5 — 분석 결과**: `ch5_results.md`
7. **Ch.6 — 토의**: `ch6_discussion.md`
8. **Ch.7 — 결론**: `ch7_conclusion.md`
9. **참고문헌**: `references.md`

---

## 논문 핵심 수치 (Quick Reference)

| 범주 | 수치 |
|---|---|
| KCD 점포 수 | 59,089개 |
| 관측 기간 | 2021-01-01 ~ 2023-08-28 (142주) |
| 총 점포-주 관측치 | 6,582,263건 |
| Post-entry 표본 | 24,278개 점포 |
| Observed-window 표본 | 50,635개 점포 (최소 52주 관측) |
| Post-entry 주 궤적 DDZ | 62.4% (지속 하락+퇴로) |
| Post-entry 종 모양 UDY | 0.8% |
| Observed-window 상태 분포 | Growth 40.04% / Stable 38.24% / Decline 21.72% |
| nc_rate importance 증가 | 12-24m: 2.19 → 60-120m: 7.47 (약 3.4배) |
| 30주 관측 3-class 예측 F1 | 0.669 (feature block 전체) |
| 30주 관측 12-class 예측 F1 | 0.260 |
| LEVI_V1 vs 생활인구 변화율 | Pearson 0.855, Spearman 0.805 |
| LEVI_V1 vs 생활인구 수준 | Pearson -0.049 (무관) |
| LEVI_V1 vs 폐업률 평균 | Pearson -0.428, Spearman -0.255 |
| LEVI 공식 간 상관 | r ≥ 0.83 (robust) |

---

## Figure 파일 경로

- **Figure 5.1 Two lenses**: `docs/thesis_figures/main_figures/figure1_two_lenses_lifecycle.pdf`
- **Figure 5.2 Age-bucket drivers**: `docs/thesis_figures/main_figures/figure2_age_bucket_drivers.pdf`
- **Figure 5.3 Prediction windows and ablation**: `docs/thesis_figures/main_figures/figure3_prediction_windows_and_ablation.pdf`
- **Figure 5.4 LEVI vs macro scatter**: `thesis/figures/fig_macro_levi_scatter.pdf`
- **Figure 5.5 LEVI top/bottom timeseries**: `thesis/figures/fig_macro_levi_timeseries.pdf`
- **Figure S1 (supporting) New customer + volatility**: `docs/thesis_figures/supporting_figures/figureS1_new_customer_and_volatility.pdf`

## Source table 경로

Micro (기존 자산):
- `docs/thesis_figures/source_tables/*.csv`
- `260326_fullsample/outputs/tables/*.csv`

Macro (본 연구 V2 신규):
- `thesis/analysis/outputs/levi_gu.csv`
- `thesis/analysis/outputs/levi_dong.csv`
- `thesis/analysis/outputs/macro_gu_panel.csv`
- `thesis/analysis/outputs/levi_macro_gu.csv`
- `thesis/analysis/outputs/levi_macro_correlations.csv`

---

## 체크리스트: 심사 전 점검

### 내용

- [ ] 표본 버전 불일치 명시: KCD_FINAL 66,667점포/2019-2023 vs 본 논문 59,089점포/2021-2023 (§3.1.2)
- [ ] 생존편향 명시: "surviving-store observed-window pattern" 수식어 누락 없는지 확인 (§3.4.1, §5.1.3, §6.4.3)
- [ ] 인과 단어 사용 금지: "leads to", "causes", "precedes"가 본문에 없는지 확인
- [ ] Golden cross는 본문에 없고, 있다면 appendix 참조로만 남기기
- [ ] "K-shape 혁신" 주장 없음 확인 (Euclidean K-Means 주 방법)
- [ ] "30주로 F1 0.84" 과장 수치 없음 확인 (올바른 수치는 0.669)

### 형식

- [ ] 국문 초록 350-500자 맞춤
- [ ] 영문 Abstract 200-300 words 맞춤
- [ ] 모든 Figure에 번호·제목·출처 주기
- [ ] 모든 Table에 번호·제목·주(note) 달기
- [ ] 참고문헌 국내·국외 APA 7판 양식 통일

### 지도교수 검토 포인트

- [ ] 논문 제목 최종 확정 (가제 → 확정안)
- [ ] 3대 기여 순서(C1→C2→C3) 심사 기준으로 적절한지
- [ ] Macro 결과(LEVI vs 생활인구)의 main figure 위치 — 5.5절 단독 vs 서론 말미 teaser
- [ ] 부록 분량(A,B,C,D) 본문 대비 비율
- [ ] 향후 저널 확장 전략 (KER, 한국경영학회지, Small Business Economics, Regional Studies 중 타깃)
