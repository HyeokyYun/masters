# HICSS 2027 Paper Outline (10 pages)

본 paper 의 정확한 섹션 구성과 각 섹션의 핵심 content. 본 thesis 자료의 어디서
가져올지 명시.

## 0. Title page (HICSS template)

Title, authors, affiliations, abstract (paper_track/abstract_draft_v1.md).

## 1. Introduction (1.5 pages)

### Hook
- SMB closure: 한국 통계 (2년 내 60% 폐업) → economic relevance
- stock prediction 의 ML 진보 (LSTM/Transformer/foundation models) → 본 영역도 가능할까?
- 본 paper 의 첫 답: **"No (현재 stock-style 방법으로는)"**

### Gap
- prior work: stock LSTM/Transformer, foundation model benchmark, M5 retail forecast.
- 본 연구의 차이: **SMB short-window G/S/D 분류** 에 stock SOTA 직접 적용한 benchmark 부재.

### Contribution (4가지)

1. First systematic benchmark of 14 external models on SMB G/S/D.
2. 70-paper literature survey mapping stock ↔ SMB methodological gap.
3. Quantitative finding: LightGBM + tenure meta = only methods to beat RF.
4. 4 mechanism hypotheses for stock-style transfer failure → SMB EWS design implications.

### Roadmap
한 단락.

**Source**: `260511/phase5_external/docs/phase5_findings.md` 의 §0 한 줄 결과 + §3 미팅 피드백 매핑.

## 2. Related Work (1.5 pages)

### 2.1 Stock-prediction deep learning
- LSTM (Hochreiter), Fischer & Krauss 2018, recent CNN-BiLSTM-attention
- Source: `stock_vs_smb_literature.md` §1 (12편)

### 2.2 Time-series foundation models
- TimesFM (Das 2024), Chronos (Ansari 2024), Moirai (Woo 2024), TimeGPT, Lag-Llama
- benchmark challenge (TSFM 누설 문제)
- Source: §2 (11편)

### 2.3 Long-horizon Transformer / GBDT
- Informer, Autoformer, TFT, PatchTST, DLinear, N-BEATS, N-HiTS
- M5 competition LightGBM 우승 패턴
- Source: §3, §4 (16편)

### 2.4 Business failure / survival
- Altman Z-score, deep survival, Korean shipping bankruptcy
- Source: §5 (8편)

### 2.5 Class imbalance / cost-sensitive
- Focal loss, SMOTE, cost matrix
- Source: §6 (10편)

### 2.6 Methodological gap (key contribution)
**핵심 표**: stock literature vs SMB short-window의 차이 매트릭스 (5 영역 × dimension).
Source: `stock_vs_smb_literature.md` §11 의 5가지 차별화.

## 3. Method (2.0 pages)

### 3.1 Data
- 59,089 stores, 2021–2023, weekly card transactions
- 6 channels: sales_card, customer, customer_new, before_noon, weekend, sales_delivery
- Source: `260511/phase5_external/src/common/seq_loader.py`

### 3.2 Calendar-aligned panel construction
- feature window vs target window
- 6 panels: sy2021_sm01_w3m_off1, sm05, sm09, sy2022_sm01, sm05, sy2021_sm01_w7m, sm09
- Source: thesis Ch4 Method

### 3.3 G/S/D label definition (±0.5σ)
- slope_target_norm, ±0.5σ threshold
- Source: `260511/docs/label_choice_rationale.md`

### 3.4 14 model categories
Brief description of each:
- **Foundation (3)**: TimesFM-200m, Chronos-Bolt-small, Moirai-small (zero-shot)
- **Stock SOTA (7)**: TFT, N-BEATS, N-HiTS, PatchTST, DLinear, Informer, Autoformer (neuralforecast)
- **SMB-attention (3)**: FeatureAttnMLP, TimeAttnLSTM, FiLM-tenure
- **Cost-sensitive (1)**: LightGBM with class weights

### 3.5 Evaluation protocol
- 3-fold StratifiedKFold (seed=42)
- macro_F1
- forecast → slope_norm → ±0.5σ bucket (train fold threshold)
- paired t-test vs RF baseline

## 4. Results (3.0 pages)

### 4.1 Headline result
Figure 1: Phase 5 bar chart (`phase5_delta_vs_rf.png`). Captioned with each model's Δ.

### 4.2 Stock SOTA (Phase 5B)
Table 1: 7 models × 6 panels macro_F1 + paired t-test.
Source: `phase5_external/outputs/tables/neuralforecast_compare.csv`, `neuralforecast_paired.csv`.

### 4.3 Foundation models (Phase 5A)
Table 2: 3 models × 6 panels.
Source: `foundation_zeroshot_compare.csv`.

### 4.4 SMB-attention (Phase 5C)
Table 3: 3 models. Note FiLM-tenure > TimeAttn (tenure conditioning helps).
Source: `attention_compare.csv`.

### 4.5 LightGBM + tenure meta (positive)
Table 4: LGBM vs RF; tenure meta vs base; combined.
Sources: `weighting_compare.csv`, `260511/outputs/tables/main_model_compare_meta.csv`.

### 4.6 Summary table
Table 5: 14 models ranked. RF(0.500) vs others.
Source: `phase5_summary.csv`.

## 5. Discussion (1.5 pages)

### 5.1 Four mechanism hypotheses
1. Short window
2. Regression → classification gap
3. Multivariate channel compression
4. Calendar season confound

(보강): `additional_analyses_plan.md` 의 synthetic long-history ablation 결과로 mechanism (1) 정량 입증 가능.

Source: `thesis_track/ch6_integration.md` §6.x.1.

### 5.2 SMB-specific design template for EWS
- Start with GBDT baseline
- Feature engineering > architecture novelty
- Feature attention > temporal attention
- Tenure cohort > spatial spillover

### 5.3 Limitations
- Korean single-city, 2021-2023, 13-31 week windows
- Foundation models zero-shot only (no finetune)
- Moirai 1/6 panels complete

## 6. Conclusion + Future Work (0.5 pages)

- 한 단락 contribution recap
- Next: DSS extension (EWS calibration), LEVI external validation, other cities transfer

## References (별도 페이지)

70편 lit + 본 thesis 직접 인용. 약 60–70 references.

---

## 작성 plan

| 주차 | 진도 |
|---|---|
| Week 1 (2026-05-12 ~ 18) | §3 Method draft + 4가지 additional 분석 시작 |
| Week 2 (~ 25) | §4 Results draft + 추가 분석 완료 |
| Week 3 (~ 06-01) | §1, §2, §5 draft |
| Week 4 (~ 08) | revise + co-author input + figures final |
| Week 5 (~ 15) | **abstract submit** + full paper draft v2 |
| Week 6–10 | full paper draft → review → submit Aug 17 |
