# 2026-05-14 개별 미팅 메모

> **목적**: framing 재정의 보고·합의 + 새 본문화 결과 공유 + 3 가지
> 의사결정 (prediction-first 적절성 / hybrid 톤 / GNN 일정). 자세한
> 표·그림·옵션은 첨부 (tables/, figures/, decisions/) 참조.

## 1. 진행 상황

`final_thesis/` 본문 9 챕터 + 6 front_matter + 9 절 신설(§5.6 보강 + §5.7
cohort + §5.8 cluster + §5.9 cost-sensitive + §5.10 요약 + §6.1.6/§6.1.7
+ §6.2.5 + §6.5 GNN 추가) 작성 완료. ch5 의 14 panel 결과 재실행 완료
(`260430_claude/outputs/tables/main_model_compare.csv` 56 행 갱신).
ch0 초록 한 485/500 자, 영 290/300 단어 한도 검증.

## 2. Framing 재정의 (v5 → final_thesis)

**문제**: v5_thesis_final 은 seasonal calendar alignment 를 main
methodological contribution 으로, hybrid 와 14-model SOTA 를 그 아래로
배치했다. 2026-05-13 점검에서 본 framing 이 advisor 의 4/30 미팅
발언 ("원래 목적은 예측", "신규 유입·업력 = 주요 요인", "주식 예측
literature 와의 관련성") 과 일치하지 않음을 확인.

**새 framing**: 상위 RQ = "초기 거래 패턴으로 G/S/D 를 얼마나 잘
예측할 수 있고, 어떤 요인·표현·모델이 그 예측을 개선시키는가."
**3 본문 contribution** (figures/fig01 참조):

1. **Prediction baseline 과 요인 분해** — cohort × G/S/D + cluster × G/S/D.
2. **Seasonal alignment 의 label robustness 전제** — 145 specification.
3. **세 갈래 improvement + SMB-specific 차별화** — hybrid / cost-sens. /
   외부 SOTA 14 종.

## 3. 새 본문화 결과 3 묶음

### (a) Cohort × cluster 요인 분해 (기여 1, §5.7 ~ §5.8)
- 업력 cohort × LightGBM ΔF1: Q1_short +0.0021 → Q4_long **+0.019**
  (전체 평균 +0.0075 의 약 2.5 배). 신규고객 → Growth 의 logit β 도
  Q4_long 에서 가장 안정 (분산 작음).
- KMeans cluster × LightGBM ΔF1: fragile cluster (Decline 35–60%) 에서
  **+0.044** (평균의 약 5.9 배). 정책 우선 영역과 모델 향상 영역 일치.
- 첨부: `tables/cohort_lgbm_delta.md`, `tables/cluster_lgbm_delta.md`,
  `figures/fig04_cohort_cluster_lift.png`.

### (b) Seasonal alignment 진폭 (기여 2, §5.2 ~ §5.4)
- 145 specification 의 RF baseline macro-F1 분포 0.43 ~ 0.55. 시작월
  진폭 **0.10** ≫ 윈도우 길이 효과 0.02–0.04 ≫ 시작연도 효과 < 0.01.
- label timing 이 model 결론의 dominant 변수.
- 첨부: `figures/fig02_seasonal_amplitude.png`.

### (c) 외부 SOTA 14 종 + Hybrid + Cost-sensitive (기여 3, §5.5/§5.9/§5.6)
- Hybrid (cluster + change-point): 14 panel 평균 ΔF1 = **+0.0017**, 5%
  유의 1/14, Bonferroni 후 0/14. 7 개월 윈도우의 라벨 편중 panel
  에서만 잔존.
- Cost-sensitive RF (Decline×2, ×3): 6/6 panel 에서 RF baseline 대비
  5% 유의 *하락* (ΔF1 = −0.035 ~ −0.063). Sample weighting 만으로는
  prediction 향상 불가.
- 외부 SOTA 14 종 중 LightGBM 1 종만 RF 능가 (**+0.0075**, 5/6 wins).
  Foundation zero-shot (Chronos, Moirai) −0.19 ~ −0.21, stock SOTA
  (TFT, N-BEATS, N-HiTS) −0.22 ~ −0.25 의 일관 패배.
- 첨부: `tables/ext_sota14_summary.md`,
  `figures/fig03_three_improvement_ladder.png`.

## 4. 의사결정 3 항목 (`decisions/decisions_to_discuss.md` 상세)

| # | 항목 | 학생 권고 |
| --- | --- | --- |
| D1 | Prediction-first framing 적절성 | **현재 안 유지** (advisor 4/30 발언과 정합) |
| D2 | Hybrid representation 결론 톤 | **대안 A** — "조건부 contribution" 에서 "입증적 한계" 로 강화 검토 |
| D3 | GNN 본격 확장 일정 | **옵션 B** — 학위논문 본문은 future-work 1 문단 유지, paper-track 으로 분리 |

## 5. 남은 학생 입력 / 의사결정

- **학위명 영문 (MBA / MS)** — 학과 행정실 확인 필요 (front_matter 04).
- **한·영 논문 제목** — prediction-first framing 위에서 학생이 3–5 개
  후보 작성해 advisor 검토 요청.
- **심사일·심사위원·심사 통과일** — 일정 협의.
- **본문/서문 쪽 수** — 조판 후 front_matter 05 채움.
- **repeated CV (10-fold × 10 repeats)** 수행 여부 — 1 일 작업. 검정력
  보강 효과는 ΔF1 ±0.002 정도의 panel 에 한정될 가능성.

---

**부속 자료 위치**:
- 표 4 종: `tables/three_contributions.md`, `ext_sota14_summary.md`,
  `cohort_lgbm_delta.md`, `cluster_lgbm_delta.md`.
- 그림 4 장: `figures/fig01_three_contributions.png`,
  `fig02_seasonal_amplitude.png`, `fig03_three_improvement_ladder.png`,
  `fig04_cohort_cluster_lift.png`.
- 의사결정 옵션 상세: `decisions/decisions_to_discuss.md`.
- 본문 자체: `/home/hyeoky98/kcd/final_thesis/thesis/ch0_abstract.md` ~
  `ch7_conclusion.md`.
