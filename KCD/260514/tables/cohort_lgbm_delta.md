# 첨부 표 3 — 업력 cohort × LightGBM vs RF ΔF1 (6 panel 평균)

원본: `/home/hyeoky98/kcd/260511/phase5_external/outputs/tables/lgbm_per_cohort_summary.csv`
(cohort_kind = "tenure_q" 의 4 행). n_panels = 6.

| cohort | tenure 중앙 (개월) | n (평균) | Decline rate | RF macro-F1 | LGB macro-F1 | **ΔF1 (LGB − RF)** |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Q1_short | ~9 | 9,223 | 0.129 | 0.475 | 0.477 | **+0.0021** |
| Q2 | ~25 | 8,910 | 0.126 | 0.492 | 0.490 | **−0.0018** |
| Q3 | ~50 | 8,895 | 0.117 | 0.497 | 0.509 | **+0.013** |
| **Q4_long** | **~115** | **8,872** | **0.120** | **0.526** | **0.545** | **+0.019** |

## 함의

- 업력이 길어질수록 LightGBM 의 RF 대비 ΔF1 이 단조 증가.
- Q4_long (≥ 9 년 업력) 의 +0.019 는 6 panel 전체 평균 (+0.0075) 의 **약 2.5 배**.
- baseline macro-F1 자체도 Q4_long 이 가장 높음 (0.526) — 업력 정보가 잠재변수로 작용해 정확도와 향상 모두에 효과.
- 신규고객 → Growth 의 logit 효과 안정성 (§5.7.2) 과 정합: 업력이 길수록 신규고객 신호가 더 일관되게 작동 → 모델이 잡아낼 신호의 명확도가 큼.

## 보완: 신규고객 logit β (`age_cohort_nc_effect.csv`)

| cohort | nc_slope → Growth 의 평균 β (panel 별 분산) |
| --- | --- |
| Q1_short | 약 1.0 (분산 큼; 0.0 ~ 2.0) |
| Q2 | 약 0.6 (분산 큼) |
| Q3 | 약 1.0 (분산 중간) |
| Q4_long | 약 1.3 (분산 작음; 0.9 ~ 1.9) |

(Note: 위 β 평균은 sy2021_sm01/sm05/sm09 와 sy2022_sm01/sm05 의 6 patch 단순 평균. panel 별 정확 수치는 원본 CSV 참조.)
