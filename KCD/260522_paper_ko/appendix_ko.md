<!--
원본: 260516_overleaf_en/chapters/appendix.tex
번역일자: 2026-05-22
-->

# Appendix (국문 번역)

## Appendix A — 업종별 입지에 따른 궤적 형상 변동

§4.2.4는 업종 × 동 궤적 형상 구성이 입지에 따라 다름을 보인다. 본 appendix는 그 확장 view로, $n \geq 150$ 점포를 3개 이상 구에서 관측한 각 식당 업종에 대해 성장형(X) 비중이 가장 낮은 구·가장 높은 구와 업종 내 span을 싣는다(Table A.1). span은 한 업종의 형상 구성이 입지에 따라 얼마나 달라지는지를 정량화한다 — 일반 한식은 0.18(종로구 0.23 → 강북구 0.41)에 달하며, 이는 marginal이 가리는 공간 × 산업 상호작용이다.

**Table A.1 — 업종별 구간 성장형(X) 비중 변동** (전구간 K=6; $n \geq 150$·3개 구 이상 업종)

| Industry | 성장형 최저 구 | 성장형 최고 구 | Span |
|---|---|---|---|
| 한식 일반 | 종로구 (0.23) | 강북구 (0.41) | 0.18 |
| 커피 전문점 | 종로구 (0.40) | 중랑구 (0.57) | 0.16 |
| 중식 | 영등포구 (0.27) | 구로구 (0.43) | 0.16 |
| 기타 주점 | 서초구 (0.25) | 은평구 (0.41) | 0.16 |
| 한식 육류/BBQ | 강남구 (0.25) | 송파구 (0.39) | 0.14 |
| 치킨 | 강서구 (0.51) | 강동구 (0.57) | 0.07 |

전체 업종 × 동 형상 행렬은 thesis 분석 파이프라인에서 재생산 가능하다.

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
