# 260511 — 2026-05-07 미팅 피드백 후속 작업 스냅샷

본 폴더는 `260430_claude/`에서 진행된 작업 중 **2026-05-07 교수 미팅 피드백**
(`260430_claude/meeting/07_meeting_feedback.md`)에 대응하여 추가로 실행한
9개 phase의 코드/결과/문서를 별도 폴더로 모아둔 스냅샷이다.

- 원본은 `260430_claude/`에 보존되어 있다 (v5_thesis_final 경로 인용은 깨지지
  않는다).
- 본 폴더 안의 스크립트들은 `config.py`가 여전히 `260430_claude/`를
  베이스로 가리킨다. 재실행 시 출력은 `260430_claude/outputs/`에 쓰인다.
  260511은 **결과 보존/리뷰용 스냅샷**으로 사용한다.

## 피드백 → 본 폴더 매핑

원문 피드백 (`260430_claude/meeting/07_meeting_feedback.md`) 항목과 본 폴더
산출물의 대응:

| 피드백 한 줄 | 대응 phase | 산출물 |
|---|---|---|
| "small business dynamics를 설명하고 더 잘 prediction" | 전체 종합 | `docs/260430_claude_dynamics_explanation.md` |
| "클러스터링이 무의미해지면 안 됨 → G/S/D 요인 파악" | Phase 2.3 (A3) | `analysis_cluster_outcome.py`, `cluster_outcome_xtab.csv`, `per_cluster_feature_importance.csv`, `v4_category_outcome.csv`, `phase2_cluster_outcome.png` |
| "신규 유입, 업력이 상승에 유의미" | Phase 2.2 (A2), 2.4 (C3) | `step03b_extract_meta_features.py`, `step05b_meta_compare.py`, `main_model_compare_meta.csv`, `main_model_paired_AvAmeta.csv`, `feature_meta_summary.csv`, `features_meta/`, `analysis_urban_econ.py`, `age_cohort_nc_effect.csv`, `phase2_meta_delta.png` |
| "예측 모델 강화 / technical novelty" | Phase 1 (B1, B3) | `step06_train_seq_models.py`, `step07_ts_benchmark.py`, `seq_model_compare.csv`, `seq_model_paired.csv`, `ts_benchmark_compare.csv`, `phase1_seq_models.png`, `phase1_ts_benchmark.png` |
| "주식 예측 literature 대조" | Phase 4 | `docs/stock_vs_smb_dynamics.md`, `phase4_dynamics_summary.png` |
| "네트워크 모델(GNN) 추가" | Phase 3 | `step08_train_gnn.py`, `gnn_compare.csv`, `phase3_gnn_delta.png` |
| "라벨 정의 robustness" (사전 정리) | Phase 0 | `step02b_label_sweep.py`, `label_definition_sweep.csv`, `label_definition_sweep_summary.csv`, `docs/label_choice_rationale.md`, `phase0_label_sweep.png` |
| SHAP per-class 해석 | Phase 2.1 (A1) | `analysis_shap.py`, `shap_class_contrib.csv`, `shap_class_rank_long.csv` |
| 업종×지역 G/S/D 매트릭스 | Phase 2.4 (C2) | `analysis_urban_econ.py`, `industry_region_growth_rate.csv`, `industry_region_top.csv` |
| step05 14-panel 재집계 (CLAUDE.md gap) | §5.5 추가 | `main_model_compare.csv`, `main_model_paired_AvD.csv` |

## 폴더 구조

```
260511/
├── README.md                       # 본 문서
├── src/                            # 피드백 후속 스크립트 (12개)
│   ├── config.py                   # 공통 경로 — BASE=260430_claude (변경 없음)
│   ├── utils_panel.py
│   ├── step02b_label_sweep.py       # Phase 0
│   ├── step03b_extract_meta_features.py
│   ├── step05b_meta_compare.py      # Phase 2.2 A2
│   ├── step06_train_seq_models.py   # Phase 1.1 B1
│   ├── step07_ts_benchmark.py       # Phase 1.2 B3
│   ├── step08_train_gnn.py          # Phase 3
│   ├── analysis_shap.py             # Phase 2.1 A1
│   ├── analysis_cluster_outcome.py  # Phase 2.3 A3
│   ├── analysis_urban_econ.py       # Phase 2.4 C2/C3
│   └── figures_summary.py           # phase0–4 figure 생성
├── docs/
│   ├── 260430_claude_dynamics_explanation.md   # 9-phase 종합 보고서
│   ├── label_choice_rationale.md
│   └── stock_vs_smb_dynamics.md
└── outputs/
    ├── tables/                     # 20 CSV + features_meta/ (146 parquet)
    └── figures/                    # phase0–4 PNG (7장)
```

## 핵심 결과 (한 줄)

- **설명**: meta features(업력 등) 추가가 cluster+CP 대비 4× 큰 효과
  (+0.0082 vs +0.0022 macro_F1).
- **예측**: tabular RF가 LSTM/GRU/Transformer/TCN을 모두 이김
  — 56-피처 통계가 raw 시계열 신호를 거의 다 포착.
- **공간 GNN**: dong/industry/hybrid 모두 negative — 단순 spatial spillover
  가설은 약함. **honest negative finding**.

자세한 내용은 `docs/260430_claude_dynamics_explanation.md` 참고.

## 원본 파이프라인과의 관계

- `260430_claude/src/step01–05_*.py`: 2026-04-30 원본 메인 파이프라인
  (seasonal calendar alignment). v5_thesis_final 본문이 직접 인용. **본 폴더에는
  복사하지 않았다** — 원본 위치 그대로 사용.
- 본 폴더의 step02b/05b/06/07/08, analysis_*: 원본 파이프라인 위에 얹은 후속
  실험. 입력 panel/label/feature는 모두 원본 step01–03가 만든 산출물에 의존.
