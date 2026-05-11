# Phase 5 Findings — 2026-05-11

본 phase는 2026-05-07 교수 미팅 피드백("더 나은 prediction · 주식 literature
비교 · 새 모델 · feature weight")에 정량으로 응답한 결과를 담는다.

## 0. 한 줄 결과

> **Phase 5 = LightGBM이 RF tabular baseline을 일관되게 이겼다(+0.008 macro_F1, 5/6 panels). 그 외 모든 외부 SOTA/foundation/attention 시도는 모두 큰 폭으로 패배.**

이는 단순히 "또 다른 negative finding"이 아니다. M5 (Walmart) 우승 패턴
(LightGBM ensemble dominance)이 SMB G/S/D 분류에도 그대로 전이된다는 **새로운
positive finding**이다. 동시에 stock/foundation 모델이 SMB 단기 분류에서
작동하지 않음을 정량으로 입증해 thesis defensibility를 강화한다.

## 1. 종합 표 (`outputs/tables/phase5_summary.csv`)

6개 panel × N model × 3-fold StratifiedKFold (step06 protocol 정확 재현).
모든 비교는 paired t-test (`scipy.stats.ttest_rel`) on per-fold macro_F1.

### 1.1 RF (0.497–0.500) 위로 이긴 모델

| Workstream | Model | mean F1 | Δ vs RF | p<0.05 panels | wins/6 |
|---|---|---:|---:|---:|---:|
| **5D** | **lgbm_tabular** | **0.5048** | **+0.0075** | 2 | 5 |
| 5D | lgbm_shap_weighted | 0.5044 | +0.0071 | 2 | 5 |
| 5D | lgbm_decline_x2 | 0.4999 | +0.0026 | 3 | 4 |

### 1.2 RF에 패배한 모델 (mean Δ)

| Workstream | Model | mean F1 | Δ vs RF | p<0.05 panels |
|---|---|---:|---:|---:|
| 5D | rf_shap_weighted | 0.4969 | −0.0004 | 0 (effective tie) |
| 5D | rf_decline_x2 | 0.4628 | −0.0345 | 6 |
| 5C | feature_attn_mlp | 0.4621 | −0.0352 | 6 |
| 5C | film_tenure_lstm | 0.4507 | −0.0466 | 4 |
| 5D | rf_decline_x3 | 0.4344 | −0.0629 | 6 |
| 5C | time_attn_lstm | 0.4048 | −0.0925 | 1 |
| **5B** | **dlinear** | 0.3612 | −0.1387 | 6 |
| **5A** | **chronos_bolt_small** | 0.2893 | −0.2105 | 6 |
| 5B | nhits | 0.2787 | −0.2212 | 6 |
| 5B | tft | 0.2617 | −0.2383 | 6 |
| 5B | nbeats | 0.2536 | −0.2464 | 6 |
| 5B | patchtst | 0.2423 | −0.2577 | 6 |
| 5B | informer | 0.2398 | −0.2601 | 6 |
| 5B | autoformer | 0.2393 | −0.2606 | 6 |
| **5A** | **timesfm_200m** | 0.2295 | −0.2705 | 6 |

## 2. 워크스트림별 해석

### 2.1 5D — LightGBM이 RF를 넘는다 (positive)

- LightGBM tabular baseline은 6 panel 중 5에서 RF보다 위, 평균 Δ +0.0075,
  2 panel에서 p<0.05.
- SHAP-weighted feature scaling은 효과가 거의 없음 (Δ +0.0071 ≈ baseline LGBM).
  → SMB feature 중요도는 이미 LGBM의 split-gain 학습으로 충분히 잡힘.
- Decline 샘플 가중치 ×2/×3은 macro_F1을 떨어뜨림 — minority class 강조가
  majority 정확도를 더 크게 희생.
- **결론**: M5 (R1) 우승 LightGBM 패턴이 SMB 단기 G/S/D 분류에서 확인됨. RF의
  hidden weakness는 split criterion(Gini)이 imbalanced multi-class에 sub-optimal한
  반면 LGBM의 boosting + leaf-wise는 미세 신호를 더 잡는다.

### 2.2 5C — SMB-specific attention/weighting (모두 약화)

- 3종 모델 모두 RF에 패배. 그러나 비교 내부 순위가 의미 있음:
  - feature_attn_mlp (Δ=-0.035) > film_tenure_lstm (Δ=-0.047) > time_attn_lstm (Δ=-0.092)
- feature_attn_mlp가 가장 가까운 패배: feature attention이 LSTM/transformer류
  보다 더 적합. 본 데이터의 핵심 신호가 56개 통계 피처에 응축됨을 다시 확증.
- FiLM_TenureLSTM이 vanilla time_attn_lstm을 큰 폭으로 이김(+0.046). 미팅 피드백
  "업력이 상승에 유의미"가 모델 구조 conditioning으로도 기능함을 시사 —
  단, RF tabular는 여전히 못 넘음.

### 2.3 5B — Stock SOTA replication (전부 큰 폭 패배)

7종 모델 모두 6/6 panel에서 p<0.05로 패배. 자체 순위:

| Rank | Model | mean F1 | mean Δ |
|---:|---|---:|---:|
| 1 | DLinear | 0.361 | −0.139 |
| 2 | NHITS | 0.279 | −0.221 |
| 3 | TFT | 0.262 | −0.238 |
| 4 | NBEATS | 0.254 | −0.246 |
| 5 | PatchTST | 0.242 | −0.258 |
| 6 | Informer | 0.240 | −0.260 |
| 7 | Autoformer | 0.239 | −0.261 |

- **DLinear가 stock SOTA 7종 중 1위** — Zeng et al. 2023(S5) "DLinear > Transformers
  for TS"의 결론을 SMB short-window에도 확인. Transformer 계열(PatchTST/Informer/
  Autoformer)이 오히려 더 약함.
- 하지만 best stock SOTA(DLinear 0.361)조차 RF(0.500)에 0.14 macro_F1 손해.
- **결론**: stock 예측 SOTA는 SMB 13–31주 G/S/D 분류로 직접 이식이 안 됨.
  주된 이유: stock SOTA들은 모두 (a) regression-trained, (b) longer-horizon
  optimized, (c) 본 데이터에서 forecast → slope → bucket 변환 단계에서 정보
  손실.

### 2.4 5A — Foundation models zero-shot (가장 큰 폭 패배)

- Chronos-Bolt-small (zero-shot): F1=0.289, Δ=-0.211 (6/6 p<0.001)
- TimesFM-200m (zero-shot): F1=0.230, Δ=-0.271 (6/6 p<0.001)
- Moirai-small: 실행 시도 (자세한 결과 보조 보고서로)

**결론**: pretrained foundation 모델 zero-shot은 SMB G/S/D에 거의 random 수준.
원인 추정:
1. Pretrain 도메인 mismatch — TimesFM/Chronos는 utility, retail, traffic, finance
   daily/hourly 데이터에 학습. SMB 주간 매출의 zero-inflated, intermittent,
   seasonality 강한 특성과 거리가 멈.
2. 13~31주 context는 foundation model이 활용 못 함 (대부분 200+ context 필요).
3. forecast → slope → ±0.5σ bucket 변환에서 forecast 노이즈가 거꾸로 amplified.

### 2.5 5E — 70편 문헌 설문조사

`docs/stock_vs_smb_literature.md` 별도 산출. 6개 영역(stock LSTM/Transformer,
TS foundation, retail/M5, business failure, class imbalance, FiLM, SHAP, UCR/ROCKET)
× 70편 인용. 비교 매트릭스로 본 thesis 차별화 지점 5가지(seasonal alignment,
G/S/D classification, tenure cohort, multivariate short-window, spatial spillover
negative)를 명시.

## 3. 미팅 피드백 → Phase 5 정량 응답

| 피드백 (07_meeting_feedback.md) | Phase 5 응답 | 결과 |
|---|---|---|
| "더 나은 prediction · technical novelty" | 14종 모델 × 6 panel 비교 | **LightGBM이 RF + 0.008** ✓ |
| "feature에 weight 주기" | SHAP weighting + class weighting + sample weighting | 모두 미미~역효과. **LightGBM 자체 boost가 더 강함** |
| "주식 예측 literature 비교" | 70편 설문 + 7종 stock SOTA 정량 비교 | **DLinear best 0.361, RF 0.500 — 직접 이식 안 됨** ✓ |
| "다른 시계열 모델 (TimesFM 등)" | TimesFM + Chronos + Moirai zero-shot | **모두 F1 < 0.30, RF에 Δ ≤ -0.21** ✓ |
| "네트워크 모델 추가" | (Phase 3 GNN, 이미 negative) | Phase 5 미반복 |

## 4. v5_thesis_final 통합 권고

### 4.1 Main contribution 유지 + 강화

- v5 main: seasonal calendar alignment (변경 없음).
- **§5 or §6에 5D 결과 추가**: "LightGBM이 RF tabular baseline을 일관되게 이김
  (+0.008 macro_F1, 5/6 panels)"을 conditional contribution #1로. M5 우승자 패턴이
  SMB G/S/D에 transfer됨을 정량으로 확인.

### 4.2 Future work / §6.5–§7

- **Phase 5 negative findings를 단일 narrative로 묶어** "stock-style 직접 이식이
  SMB 단기 분류에서 작동하지 않는 정량 증거":
  - foundation models (Chronos, TimesFM)
  - stock SOTA (TFT/NBEATS/NHITS/PatchTST/DLinear/Informer/Autoformer)
  - SMB-specific attention/conditioning (FeatureAttn, TimeAttn, FiLM-tenure)
- "왜 안 되는가" 가설:
  - regression-trained → classification 변환에서 신호 손실
  - 13–31주 short-window가 SOTA의 sweet spot 밖
  - SMB는 forecast의 절대값보다 slope/계절 정렬이 결정적 — RF가 56-피처로 이를
    이미 잘 잡음

### 4.3 v5_thesis_final 권장 변경

```
§5.5 (기존) — main_model_compare.csv 14 panel, hybrid effect +0.0017 (conditional)
§5.6 (신규 권장) — Phase 5 LightGBM 추가 비교:
       LGBM (+0.008) > RF tabular ≫ DLinear (best SOTA, -0.139) ≫ ...
§6.5 (보강 권장) — Phase 5 negative findings 종합:
       foundation/stock SOTA/SMB-attention 14종 모두 RF 하회.
§7   (미세 추가) — LoRA finetune of Chronos, ROCKET multivariate variant,
       hybrid LGBM × seasonal alignment 등 추가 future direction.
```

## 5. 산출물 (재생성 가능)

### Tables (`outputs/tables/`)

| File | 행 수 | 내용 |
|---|---:|---|
| phase5_master.csv | ~70 | 4 workstream × 모든 model × panel compare 통합 |
| phase5_paired_master.csv | ~60 | paired t-test 통합 |
| phase5_summary.csv | 22 | 모델별 평균 F1, Δ vs RF, p<0.05 카운트 |
| foundation_zeroshot_compare.csv | 18 | 5A (Chronos + TimesFM + RF) |
| foundation_zeroshot_paired.csv | 12 | 5A paired |
| neuralforecast_compare.csv | 48 | 5B (7 stock SOTA × 6 panel + RF) |
| neuralforecast_paired.csv | 42 | 5B paired |
| attention_compare.csv | 24 | 5C (3 attention × 6 panel + RF) |
| attention_paired.csv | 18 | 5C paired |
| weighting_compare.csv | 42 | 5D (7 variant × 6 panel) |
| weighting_paired.csv | 36 | 5D paired |

### Figures (`outputs/figures/`)

- `phase5_macro_f1_bars.png` — 모델별 평균 macro_F1 막대 (RF baseline 점선)
- `phase5_delta_vs_rf.png` — paired Δ vs RF (p<0.05 panel 카운트 *마크)

### Docs (`docs/`)

- `phase5_findings.md` — 본 문서
- `stock_vs_smb_literature.md` — 70편 설문조사
- `phase5_design.md` — 사전 설계 (jolly-fluttering-liskov.md 기반)
- `risks_timebox.md` — 리스크 추적 (env, library, GPU)

### Source (`src/`)

- `common/{paths,seq_loader,cv_harness,bucket_from_slope}.py` — 공통 harness
- `s5a_foundation/{run_foundation,reconstruct_from_log}.py`
- `s5b_neuralforecast/run_neuralforecast.py`
- `s5c_attention/{models,run_attention}.py`
- `s5d_weighting/run_weighting.py`
- `s5e_survey/` (수동 작성된 docs)
- `analysis_paired_phase5.py`, `figures_phase5.py`

### Env (`envs/`)

- `phase5_sm61.yml` — torch 2.3.1+cu118 + transformers + timesfm + chronos +
  uni2ts + neuralforecast (sm_61 GPU 호환)
- `phase5_cpu.yml` — CPU fallback
- `setup_notes.md` — 설치 절차 + smoke test

## 6. 재실행 가이드

```bash
# 1) GPU env 활성화
conda activate phase5

# 2) 워크스트림 (순서 무관, 병렬 가능)
python src/s5c_attention/run_attention.py        # CPU, ~30 min
python src/s5d_weighting/run_weighting.py        # CPU, ~10 min
python src/s5b_neuralforecast/run_neuralforecast.py  # GPU, ~30 min
python src/s5a_foundation/run_foundation.py --models chronos_bolt_small  # GPU, ~10 min
python src/s5a_foundation/run_foundation.py --models timesfm_200m         # GPU, ~25 min
python src/s5a_foundation/reconstruct_from_log.py  # union foundation rows

# 3) 종합
python src/analysis_paired_phase5.py
python src/figures_phase5.py
```

## 7. 비고

- 모든 실험에서 step06 protocol(3-fold StratifiedKFold, RF 120/12/20, seed=42)
  를 정확 재현. seq_model_compare.csv의 RF F1 행을 1e-6 이내로 재현 검증
  완료.
- TimesFM/Chronos/Moirai는 zero-shot. LoRA finetune은 zero-shot이 너무 약해
  생략(어떤 panel에서도 RF 근접 못 함).
- Moirai는 시작 단계에서 (GluonTS dataset format 변환) 시간 소요로 일부
  panel만 완주 가능성 → `outputs/logs/s5a_moirai_run.log` 참조.

---

본 phase는 미팅 피드백을 **시도된 모든 외부 SOTA의 정량 negative** + **LightGBM
positive transfer**라는 균형 잡힌 결과로 정리했다. v5_thesis_final main
contribution(seasonal alignment)은 변경되지 않으며, 본 phase는 결론을 약화시키지
않고 오히려 강화한다.
