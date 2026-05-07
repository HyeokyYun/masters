# Rolling 결과 정리 (Step 04 + 확장 윈도우 + Step 05)

> 원본: `../docs/260430_claude_rolling_results.md`,
> `../docs/260430_claude_main_model_results.md`. 본 문서는 미팅용으로
> 핵심 숫자만 재계산해 압축한 자료다. 원본 CSV/그림은 그대로 보존.

## 1. 인벤토리 (재검증된 값)

| 항목 | 값 |
| --- | --- |
| 데이터 범위 | 2021-01-01 ~ 2023-08-28 (142주) |
| weekly.parquet | 6.58M 점포-주차, 59,089 점포 |
| 후보 조합 | 168개 (`start_year × start_month × window_months × off`) |
| 데이터 범위 안 | 146 panel (skipped 22) |
| 윈도우 길이 | w ∈ {1, 2, 3, **4, 6, 7**} (4/6/7은 v5 확장) |
| target_offset | off=1 → 109 panel · off=2 → 37 panel |
| 점포 수 / panel | 29K – 37K |
| 모델 | RF (240 trees, depth 14, balanced) + LightGBM, stratified 5-fold, seed 42 |

## 2. 핵심 발견 — 시작월 효과 ≫ 윈도우 길이 효과 (RF, off=1)

### 2-1. 윈도우 길이별 평균 macro-F1 (w ∈ 1..3, 58 panel)

| window_months | macro_F1 mean |
| --- | --- |
| 1 | 0.4747 |
| 2 | 0.4847 |
| 3 | 0.4890 |

### 2-2. 시작연도별 평균 macro-F1 (w ∈ 1..3)

| start_year | macro_F1 mean |
| --- | --- |
| 2021 | 0.4870 |
| 2022 | 0.4756 |

### 2-3. 시작월별 평균 (w=3, 양 연도 평균)

| start_month | macro_F1 | Decline recall |
| --- | --- | --- |
| 1 | 0.5005 | 0.4614 |
| 2 | 0.5040 | 0.4212 |
| 3 | 0.4780 | 0.3792 |
| 4 | 0.4806 | 0.4678 |
| 5 | 0.4954 | 0.5521 |
| 6 | 0.4626 | 0.5063 |
| 7 | 0.4642 | 0.4943 |
| 8 | 0.5020 | 0.4521 |
| 9 | 0.5014 | 0.5252 |
| **10** | **0.5308** | **0.5680** |
| 11 | 0.4880 | 0.5387 |
| 12 | 0.4976 | 0.5325 |

### 2-4. 진폭 비교 (이게 핵심 한 줄)

- **시작월 진폭(start_month, w=3 평균): 0.0682** (sm10 0.5308 – sm06 0.4626)
- **윈도우 길이 진폭(w 1~3): 0.0143** (w3 – w1)
- **시작연도 차(2021↔2022): 0.0114**
- → **시작월 진폭이 윈도우/연도 효과의 약 5–6배.** 시즈널리티가 일순위 신호.

## 3. 확장 윈도우 (w ∈ 4, 6, 7) 추가 분석

| window_months | mean macro-F1 | n panels |
| --- | --- | --- |
| 4 | 0.4963 | 18 |
| 6 | 0.4936 | 17 |
| 7 | 0.4900 | 16 |

해석:
- 윈도우를 4개월 이상 늘려도 macro-F1은 더 이상 의미 있게 올라가지 않는다
  (w=3 0.4890 → w=4 0.4963, 이후 평탄 또는 미세 감소).
- **w=3개월이 비용 대비 합리적인 정착점.** 메인 panel 7개를 모두 3-month로
  둔 결정의 실증 근거.

## 4. 톱/바텀 panel (RF, off=1, w ∈ 1..3)

### 상위 5

| combo | sy | sm | w | macro_F1 | recall_D |
| --- | --- | --- | --- | --- | --- |
| sy2022_sm01_w1m_off1 | 2022 | 1 | 1 | 0.5364 | 0.4715 |
| sy2021_sm11_w2m_off1 | 2021 | 11 | 2 | 0.5311 | 0.5685 |
| sy2021_sm10_w3m_off1 | 2021 | 10 | 3 | 0.5308 | 0.5680 |
| sy2022_sm01_w2m_off1 | 2022 | 1 | 2 | 0.5302 | 0.4804 |
| sy2021_sm02_w3m_off1 | 2021 | 2 | 3 | 0.5188 | 0.4253 |

### 하위 5

| combo | sy | sm | w | macro_F1 | recall_D |
| --- | --- | --- | --- | --- | --- |
| sy2022_sm07_w3m_off1 | 2022 | 7 | 3 | 0.4348 | 0.5528 |
| sy2022_sm07_w2m_off1 | 2022 | 7 | 2 | 0.4352 | 0.5645 |
| sy2022_sm07_w1m_off1 | 2022 | 7 | 1 | 0.4443 | 0.4341 |
| sy2022_sm03_w1m_off1 | 2022 | 3 | 1 | 0.4464 | 0.4598 |
| sy2021_sm07_w1m_off1 | 2021 | 7 | 1 | 0.4503 | 0.4521 |

해석:
- **상위는 가을(10–11월) + 1월 시작.** 시즌 패턴이 매끄럽고 G/S/D 균형 양호.
- **하위는 7월 + 3월 시작.** 7월 시작은 target이 데이터 끝(2023-07~08)으로
  몰려 라벨이 인공적으로 Decline-편중.

## 5. 라벨 분포 sanity (제외 영역)

- 2023-08 컷오프 직전: `sm07/sm08 + off2`, `sm05/sm06 + w3 + off2` 부근.
- 예: `sy2022_sm08_w1m_off1` → Decline 비율 0.675.
- 본 분석에서 **모델 비교 결론 근거로 사용하지 않음.** 부록에 sanity로만 표기.

## 6. RF vs LightGBM

- 평균 macro-F1: RF 0.4877 vs LGB 0.4914 (off=1, 146 panel).
- 차이 0.004로, panel 단위에서는 0.01 미만이 대부분. **모델 선택은 결론에
  결정적이지 않다.**

## 7. Step 05(메인 모델 A/B/C/D) — 시즌 정렬 후 hybrid contribution 약화

### 7-1. 비교 조건

| 코드 | 피처 구성 | 피처 수 |
| --- | --- | --- |
| A | Step 03 베이스라인 (매출 통계 + 슬로프 + 이동평균 + 신규 고객 + 채널 비율 + 분포) | 43 |
| B | A + KMeans cluster one-hot (k=6, normalized 매출 시퀀스, **feature 구간만**) | 49 |
| C | A + change-point 7개 (**feature 구간만**) | 50 |
| D | A + B + C | 56 |

### 7-2. 결과 표 (RF, paired t-test 자유도=4)

| panel | A | D | Δ(D−A) | t | p |
| --- | --- | --- | --- | --- | --- |
| sy2021_sm01_w3m_off1 (Jan–Mar 21→22) | 0.5007 | 0.5030 | +0.0023 | 2.73 | 0.052 |
| sy2021_sm03_w3m_off1 (Mar–May 21→22) | 0.4954 | 0.4986 | +0.0032 | 1.32 | 0.258 |
| sy2021_sm05_w3m_off1 (May–Jul 21→22) | 0.4875 | 0.4882 | +0.0007 | 0.29 | 0.787 |
| sy2021_sm09_w3m_off1 (Sep–Nov 21→22) | 0.5096 | 0.5101 | +0.0005 | 0.30 | 0.778 |
| sy2022_sm01_w3m_off1 (Jan–Mar 22→23) | 0.5144 | 0.5165 | +0.0021 | 1.04 | 0.356 |
| **sy2022_sm03_w3m_off1** (Mar–May 22→23) | 0.4684 | 0.4740 | **+0.0055** | **3.47** | **0.026** |
| sy2022_sm05_w3m_off1 (May–Jul 22→23) | 0.5176 | 0.5190 | +0.0014 | 0.72 | 0.511 |

평균 Δ(D−A) = **+0.0022 macro-F1**. 5% 유의는 1개(`sy2022_sm03`),
10% 경계 1개(`sy2021_sm01`), 나머지 5개 미유의.

### 7-3. 갭(미반영)

- CLAUDE.md 명시: 확장 윈도우(4/6/7개월) panel 7개 추가 → 14 panel 비교.
- 현 시점 `main_model_compare.csv`는 **7개 panel만** 반영. step05 재실행
  필요 (입력 데이터는 모두 준비됨).

## 8. Target leakage 검증 (교수 17:29 질문 대응)

- `step05_train_main_model.py:166` →
  ```python
  feat_panel = panel[panel["segment"] == "feature"]
  ids, seq = _seq_matrix(feat_panel)
  cluster_df = _cluster(seq, ids)
  cp_df = _change_point_features(seq, ids)
  ```
- KMeans clustering과 change-point feature는 **feature 구간만**의 정규화된
  매출 시퀀스에서 산출. target 구간 데이터는 라벨 산출(Step 02) 외에는
  사용되지 않음.
- 즉, "앞 정보로만 알 수 있는 내용" 조건 충족.

## 9. 화면 공유용 그림 위치

| 파일 | 무엇을 보여주는가 |
| --- | --- |
| `../outputs/figures/heatmap_macro_f1_rf_off1.png` | 시작연도×시작월 macro-F1 |
| `../outputs/figures/heatmap_decline_recall_rf_off1.png` | Decline recall (라벨 편중 진단) |
| `../outputs/figures/heatmap_f1_decline_rf_off1.png` | Decline f1 |
| `../outputs/figures/heatmap_macro_f1_rf_off2.png` | off=2 (sanity) |
| `../outputs/figures/yearly_compare_2021_vs_2022.png` | 2021 vs 2022 시작연도 비교 |
| `../outputs/figures/main_model_compare_bars.png` | (Step 05) A/B/C/D 막대 |
| `../outputs/figures/main_model_delta.png` | (Step 05) D−A delta |

## 10. 상세 산출물 위치

- `../outputs/tables/seasonal_results_long.csv` — fold별 raw.
- `../outputs/tables/seasonal_results_summary.csv` — panel × model 요약 (293행).
- `../outputs/tables/panel_summary.csv` — 168 candidate combos.
- `../outputs/tables/label_distribution.csv` — 146 panel × G/S/D 비율.
- `../outputs/tables/main_model_compare.csv` — Step 05 A/B/C/D.
- `../outputs/tables/main_model_paired_AvD.csv` — Step 05 paired t-test.
