<!--
원본: 260516_overleaf_en/chapters/appendix.tex
번역일자: 2026-05-22
-->

# Appendix (국문 번역)

## Appendix A — 업종 × 동 조합 확장 표

§4.2.4는 본문에 업종 × 동 조합의 상위 일부만 보고한다. 본 appendix는 7개 시즌 정렬 패널 pooled 점포 수가 보고 임계값($n_\text{total} \geq 90$)을 넘는 조합의 확장 순위를 싣는다. Table A.1은 Growth 비율 상위 20개 조합이며, Growth·Decline 비율을 함께 보여 고-Growth 업종 내 양극화(예: 생맥주 전문점은 동에 따라 양 극단에 모두 등장)가 드러나게 한다. Source: `260430_claude/outputs/tables/industry_region_top.csv`.

**Table A.1 — 업종 × 동 조합 Growth 비율 순위** (7-패널 pooled, $n_\text{total} \geq 90$; `n_panels` = 조합이 패널별 cell 임계값을 넘은 패널 수)

| Industry | District | Growth | Decline | $n_\text{total}$ | n_panels |
|---|---|---|---|---|---|
| 생맥주 전문점 | 은평구 | 0.690 | 0.067 | 92 | 3 |
| 생맥주 전문점 | 강서구 | 0.467 | 0.189 | 90 | 3 |
| 한식 면류 | 중랑구 | 0.465 | 0.091 | 249 | 7 |
| 한식 면류 | 강동구 | 0.463 | 0.061 | 293 | 7 |
| 생맥주 전문점 | 관악구 | 0.458 | 0.141 | 233 | 7 |
| 한식 면류 | 광진구 | 0.457 | 0.083 | 263 | 7 |
| 생맥주 전문점 | 강남구 | 0.454 | 0.108 | 360 | 7 |
| 한식 면류 | 마포구 | 0.454 | 0.073 | 281 | 7 |
| 생맥주 전문점 | 구로구 | 0.446 | 0.120 | 258 | 7 |
| 생맥주 전문점 | 송파구 | 0.446 | 0.108 | 243 | 7 |
| 한식 면류 | 은평구 | 0.446 | 0.099 | 344 | 7 |
| 치킨 | 중구 | 0.445 | 0.076 | 272 | 7 |
| 한식 면류 | 노원구 | 0.438 | 0.133 | 266 | 7 |
| 생맥주 전문점 | 종로구 | 0.438 | 0.107 | 244 | 7 |
| 생맥주 전문점 | 영등포구 | 0.430 | 0.122 | 293 | 7 |
| 한식 면류 | 강서구 | 0.428 | 0.089 | 266 | 7 |
| 기타 주점 | 양천구 | 0.426 | 0.135 | 742 | 7 |
| 기타 주점 | 서대문구 | 0.421 | 0.158 | 908 | 7 |
| 기타 주점 | 성북구 | 0.420 | 0.181 | 796 | 7 |
| 한식 면류 | 영등포구 | 0.417 | 0.031 | 347 | 7 |

전체 조합(임계값 미만 포함) 분포는 `260430_claude/outputs/tables/industry_region_growth_rate.csv` 에서 재생산 가능하다.

---

## Appendix B — Manual Class-Reweighting 실험

§5.7은 Decline 클래스 손실 가중이 macro-$F_1$을 낮춘다는 cost-sensitive 결과를 보고한다. 이것이 특정 가중 구현의 artifact가 아님을 확인하기 위해, 6개 시즌 정렬 패널에서 *manual* 클래스 재균형 변형을 추가로 돌렸다: Decline 클래스에 scalar class weight $w \in \{2,3,5\}$, 그리고 sample-duplication weight $w \in \{2,3,5\}$ (Decline 행을 2·3·5회 복제). 결과는 일관된 null — 6 변형 × 6 패널 모두에서 RF baseline 대비 패널별 paired $\Delta\text{macro-}F_1$ 이 $-0.0013$ ~ $+0.0008$, paired-$t$-test $p > 0.42$ (대개 $> 0.6$) — baseline과 통계적으로 구별 불가 (Table B.1).

**Table B.1 — Manual class-reweighting 실험** (6 변형 × 6 패널). Source: `260514/manual_weight_exp/outputs/tables/manual_weight_compare.csv`, `manual_weight_paired.csv`.

| Variant | Mean $\Delta\text{macro-}F_1$ vs RF | Mean $p$-value |
|---|---|---|
| rf_scalar_w2 | +0.000074 | ≈0.78 |
| rf_scalar_w3 | +0.000093 | ≈0.81 |
| rf_scalar_w5 | +0.000091 | ≈0.81 |
| rf_dup_w2 | −0.000074 | ≈0.55 |
| rf_dup_w3 | −0.000044 | ≈0.66 |
| rf_dup_w5 | +0.000040 | ≈0.71 |

§5.7의 손실 가중 결과와 함께, 이 null 발견은 본 데이터에서 G/S/D 경계가 *representation*(신규 고객 비율, 영업기간, 매출 곡선 형상)으로 설정되지 손실·샘플링 단계의 class weighting으로 설정되지 않음을 뒷받침한다.
