# Phase 5 Design — 사전 계획 (참조)

본 phase의 사전 설계는 `~/.claude-account2/plans/jolly-fluttering-liskov.md`에
원본이 있고, 본 문서는 그 요약본이다.

## 목적

2026-05-07 교수 미팅 피드백(`260430_claude/meeting/07_meeting_feedback.md`)에
정량 응답:

1. 더 나은 prediction (technical novelty)
2. 주식 예측 literature와의 비교
3. 다른 시계열 모델 (TimesFM 등)
4. feature에 weight 주기 / cost-sensitive 학습

## 5 워크스트림

| # | 워크스트림 | 모델 수 | 비고 |
|---|---|---:|---|
| 5A | Foundation models | 2–3 | Chronos-Bolt-small / TimesFM-200m / (Moirai-small) |
| 5B | Stock SOTA | 7 | TFT / NBEATS / NHITS / PatchTST / DLinear / Informer / Autoformer |
| 5C | SMB attention | 3 | FeatureAttnMLP / TimeAttnLSTM / FiLM_TenureLSTM |
| 5D | Feature weighting | 7 | RF/LGBM × {tabular, shap_weighted, decline_x2, decline_x3} |
| 5E | 문헌 설문조사 | — | 70편, 6 영역 |

## 평가 protocol

- 6 panel: step06와 동일 (`PANELS` in `common/paths.py`)
- 3-fold StratifiedKFold, seed=42
- 메트릭: macro_F1 (`zero_division=0`)
- paired: scipy.stats.ttest_rel on per-fold F1
- 모든 sequence/foundation forecast → slope_norm → ±0.5σ bucket (Phase 0
  threshold). σ는 train fold에서 매번 새로 산출 (leakage 방지).
- CSV schema: `(combo_id, description, model, macro_f1_mean, macro_f1_std,
  n_stores, T or horizon_weeks, [C])` for compare; `(combo_id, model,
  delta_mean, t_stat, p_value)` for paired.

## 재사용

| 항목 | 출처 |
|---|---|
| `WindowSpec`, `panel_path`, `label_path`, `feature_path`, `load_weekly` | `260430_claude/src/utils_panel.py` |
| `cfg.SEED`, `cfg.OUTCOME_CLASSES`, `cfg.CV_FOLDS` | `260430_claude/src/config.py` |
| `_load_seq`, `_rf_baseline`, training loop schema | `260430_claude/src/step06_train_seq_models.py` |
| SHAP weights | `260430_claude/outputs/tables/shap_class_contrib.csv` |

## Risk 매트릭스 (사전 평가)

| Risk | Likelihood | Impact | 완화 |
|---|---|---|---|
| sm_61 GPU 비호환 | High | High | torch 2.3.1+cu118 env 별도 빌드 |
| Foundation model 너무 느림 | Med | Med | batch_size 256, max_history=78 제한 |
| Stock SOTA library 안정성 | Med | High | neuralforecast 1.7.5 (검증된 stable) |
| TimesFM API 변동 | Med | Med | timesfm 1.2.0 고정 |
| Moirai GluonTS adapter 복잡 | High | Low | 실패 시 skip, chronos+timesfm로 충분 |

## 실행 결과 (사후)

- 모든 워크스트림 완주 (Moirai만 부분)
- LightGBM이 RF에 +0.008 macro_F1로 positive (5/6 panels)
- 그 외 외부 SOTA/foundation 14종은 모두 큰 폭 negative
- 자세한 결과는 `phase5_findings.md` 참조
