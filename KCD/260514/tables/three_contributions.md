# 첨부 표 1 — 본문 3 contribution 요약

`final_thesis/thesis/ch1_introduction.md` §1.4 기반.

| # | Contribution | 핵심 수치 | 본문 위치 / CSV | 한계 |
| --- | --- | --- | --- | --- |
| 1 | **Prediction baseline 과 요인 분해** | baseline macro-F1 0.43 ~ 0.55 (145 specification). Q1_short → Q4_long LGB ΔF1: +0.0021 → +0.019. fragile cluster (Decline 35–60%) ΔF1: +0.044. | §5.2 ~ §5.5 + §5.7 (cohort) + §5.8 (cluster). `260430_claude/outputs/tables/age_cohort_nc_effect.csv`, `cluster_outcome_xtab.csv`, `260511/phase5_external/outputs/tables/lgbm_per_cohort_summary.csv`. | logit 회귀는 관찰적, 인과 아님. cluster 수 k=6 단일 선택. |
| 2 | **Seasonal calendar alignment 의 label robustness 전제** | 시작월 진폭 0.10 ≫ 윈도우 길이 효과 0.02–0.04 ≫ 시작연도 효과 < 0.01. 145 specification 모두 측정. | §5.2 ~ §5.4. `260430_claude/outputs/tables/seasonal_results_summary.csv`. | 외식업 한정. cash 결제 누락. 2y target 은 컷오프로 일부 panel 제외. |
| 3 | **세 갈래 prediction-improvement 시도 + SMB-specific 차별화** | (a) hybrid +0.0017 (5% 유의 1/14, Bonferroni 후 0/14). (b) cost-sensitive RF Δ = −0.035 ~ −0.063, LGB Δ ≈ −0.005. (c) 외부 SOTA 14 종 중 LightGBM 1 종만 RF 능가 (+0.0075). | §5.5 (hybrid), §5.9 (cost-sens.), §5.6 (SOTA 14). `main_model_paired_AvD.csv`, `weighting_compare.csv`, `phase5_summary.csv`. | 5-fold seed=42 단일 시도. SOTA hyperparam grid 미수행. 4 mechanism 가설은 가설 단계. |

## Supplementary (본문 contribution 아님, future work)

- LEVI 도시경제 활력 지수 → §6.5, §7.2
- EWS 조기 쇠퇴 경보 → §6.5, §7.2
- GNN 본격 확장 → §6.5, §7.2 (pilot 만 본문)
- 외부 공공 데이터 외적 타당도 → §6.5, §7.2
- Golden Cross 시즌 정렬 재검증 → §6.5
- Cost-sensitive policy sweep → §6.5
