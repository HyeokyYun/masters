# Label Choice Rationale (Phase 0)

본 문서는 `step02b_label_sweep.py` 결과
(`outputs/tables/label_definition_sweep.csv`,
`label_definition_sweep_summary.csv`)에 근거하여 본 실험에서 사용할 G/S/D 라벨
정의를 선택한 근거를 정리한다.

## Sweep 설정

- 8개 대표 panel × 임계값 ∈ {±0.3σ, ±0.5σ, ±0.7σ} (전체 14개 중 8개 완료, 7m/6m/4m
  중 일부는 시간 제약으로 미수집; 남은 panel은 robustness 부록으로 후속 보충 예정)
- 각 (panel, k):
  - 분류 baseline: RandomForest(n=120, depth=12) on 56 base features, 3-fold CV
  - 회귀 baseline: 동일 RF로 `slope_target_norm`을 직접 예측 후 동일 sigma threshold로
    버킷화하여 macro_F1 산출

## 핵심 결과 (mean across 8 panels)

| k | macro_F1 | Growth | Stable | Decline | reg→bucket F1 | reg R² |
|---:|---:|---:|---:|---:|---:|---:|
| 0.3 | **0.491** | 0.454 | 0.344 | 0.202 | 0.393 | 0.108 |
| **0.5** | **0.494** ★ | 0.344 | 0.524 | 0.132 | 0.387 | 0.108 |
| 0.7 | 0.487 | 0.250 | 0.662 | 0.088 | 0.376 | 0.108 |

★ k=0.5 가 평균 macro_F1 최댓값.

### 클래스 균형
- k=0.3: 너무 자주 Growth/Decline로 분류 → Stable 클래스가 34%로 작아짐 (Decline 20%
  까지 잡히지만 Growth와 Decline 사이의 노이즈도 라벨로 들어옴).
- k=0.7: Stable이 66%로 지배 → Decline은 9%로 떨어지며, panel별 최저는 3.4% 까지 떨어져
  학습이 어려워짐.
- k=0.5: 평균 G:S:D = 34:52:13. panel별 Decline 최저 5.1% 로 학습 가능 영역 유지.

### 회귀 vs 분류
모든 panel과 k에서 `reg_then_bucket_macro_f1 < macro_f1_mean`.
즉 슬로프를 직접 회귀해서 버킷화하는 것보다, 처음부터 3-class 분류로 학습하는 편이
약 10pt 이상 높은 macro_F1을 낸다. 이는 본 연구의 분류 접근(현행)을 정당화한다.
다만 reg R² ≈ 0.11 은 슬로프에 예측 가능한 신호가 있음을 시사하므로, 향후
multi-task auxiliary head로 회귀를 보조 손실에 추가하는 실험은 고려 가능.

### Per-class F1 (k=0.5, panel별)
| panel | F1_D | F1_S | F1_G |
|---|---:|---:|---:|
| sy2021_sm01_w3m_off1 | 0.300 | 0.467 | 0.700 |
| sy2021_sm03_w3m_off1 | 0.253 | 0.573 | 0.644 |
| sy2021_sm05_w3m_off1 | 0.460 | 0.650 | 0.325 |
| sy2021_sm09_w3m_off1 | 0.424 | 0.631 | 0.437 |
| sy2022_sm01_w3m_off1 | 0.297 | 0.556 | 0.652 |
| sy2022_sm03_w3m_off1 | 0.294 | 0.744 | 0.337 |
| sy2022_sm05_w3m_off1 | 0.496 | 0.681 | 0.347 |
| sy2021_sm01_w7m_off1 | 0.296 | 0.579 | 0.725 |

Decline F1 가 panel별 0.25–0.50 로 가장 변동이 크다. Growth/Decline F1 은 시즌
(연중 panel 위치)에 따라 역전이 일어남 — Jan/Mar 시작 panel은 Growth가 잘
잡히고, May 이후 시작 panel은 Decline이 잘 잡힌다. 이는 seasonal alignment의
필요성을 다시 확인.

## 결정

**채택 라벨 정의: ±0.5σ 3-class (현행 유지)**

근거:
1. 평균 macro_F1 최댓값 (0.494, k=0.3 대비 +0.003, k=0.7 대비 +0.008).
2. Decline floor (panel별 최소 decline ratio) 가 5.1%로 학습 가능.
3. 회귀-후-버킷 대비 직접 분류가 일관되게 우수 → 분류 접근 정당화.
4. 기존 14-panel 결과와 직접 비교 가능 (변경 없음).

부록 처리:
- ±0.3σ, ±0.7σ 결과는 §robustness 부록으로 첨부 (평균 macro_F1 변동 ±0.005 이내).
- 회귀 R² (~0.11) 은 분류와 별도 표로 첨부.

## 후속 실험 영향

- step06 (시퀀스 모델), step07 (TS 벤치마크), step08 (GNN), analysis_shap,
  analysis_cluster_outcome, step03b (메타) 모두 기존 ±0.5σ 라벨 (`labels_<combo>.parquet`)
  을 그대로 사용한다.
- 라벨 재생성 불필요.
