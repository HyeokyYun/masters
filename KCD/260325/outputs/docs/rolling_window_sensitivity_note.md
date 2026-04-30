# Rolling Window Sensitivity

`rolling8`, `rolling10`, `rolling12`, `rolling13`을 같은 표본에서 비교했다.

## 집단 구분력 기준

가장 작은 ANOVA p-value와 가장 큰 F값을 보인 창은 `rolling8`였다.

- best metric: `vol_resid_rolling8`
- Stable mean: `0.2862`
- Growth mean: `0.2190`
- Decline mean: `0.2712`
- ANOVA F: `269.9949`

## 설명모형 적합도 기준

가장 높은 pseudo R²와 낮은 AIC를 보인 창은 `rolling12`였다.

- best metric: `vol_resid_rolling12`
- pseudo R²: `0.578790`
- AIC: `18816.7890`
