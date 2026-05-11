# Stock Prediction vs SMB Sales Dynamics — 30+편 문헌 설문조사

**목적**: 2026-05-07 교수 미팅 피드백 "주식 예측 literature와 비교"에 정량으로
답하기 위한 조사. 본 문서는 본 thesis의 SMB G/S/D 분류 (260511 phase 5)와
직접 비교 가능한 외부 연구를 6개 영역으로 정리한다.

- 비교 기준 한 줄: SMB는 **store-level short-window classification (T=8–14주, 3-class)**
  이고, 주식·M5·foundation 모델 문헌의 대부분은 **regression / forecasting**.
  단순 이식은 어렵고, 어떤 부분이 transfer 가능한지가 핵심 질문.

## 0. 본 thesis와의 매핑 한 줄

| 외부 영역 | SMB와 닮은 점 | SMB와 다른 점 |
|---|---|---|
| Stock LSTM/Transformer | 매출 시계열의 short-window 예측 | (a) 거래량/PER 등 외생 feature 풍부, (b) regression task, (c) very low SNR이라도 통계적 검정력 큼 (수천 일 vs 13주) |
| TS foundation models | 시계열 → 미래값 패턴 | pretrained 도메인이 SMB 주간 매출과 거리, irregular zero-inflated |
| Retail/M5 demand | 점포-품목 hierarchical, intermittent | M5는 daily, 5년 history, exogenous calendar/event 많음 |
| Business failure | 분류 task, low base rate | survival / time-to-event 가 더 일반적; 본 thesis는 단기 G/S/D 분류 |
| Class imbalance | Decline ~7–13% minority | 본 thesis는 3-class macro_F1, binary fraud 와 다름 |
| TS classification (UCR) | 짧은 시계열 분류 task | UCR은 1-channel univariate, 본 thesis는 6-channel multivariate |

## 1. 주식 예측 시계열 — LSTM, Transformer, Attention 계열

### 1.1 LSTM 기반

- **L1.** Hochreiter & Schmidhuber (1997) "Long Short-Term Memory" — 원조.
- **L2.** Fischer & Krauss (2018) "Deep learning with long short-term memory networks for financial market predictions", *European Journal of Operational Research*. S&P 500 일별 수익률 binary 분류. RF에 LSTM이 일관되게 우위.
- **L3.** [Stock LSTM 2025 IEEE](https://ieeexplore.ieee.org/iel8/6287639/10820123/11072109.pdf) — Hybrid LSTM-GRU 모델, 2025년 IEEE Access. LSTM이 GRU보다 short-term volatility에 강함.
- **L4.** [JETIR LSTM Review](https://www.jetir.org/papers/JETIR2504B83.pdf) — 2025 review, LSTM/RNN 30+편 종합. 일관된 결론: 단기(<30일) regression에서 LSTM이 보편적 baseline.
- **L5.** [IRJMETS LSTM attention](https://www.irjmets.com/uploadedfiles/paper/issue_11_november_2024/64022/final/fin_irjmets1731772488.pdf) — LSTM + attention 결합으로 long-range dependency 보강.

### 1.2 Transformer / Attention

- **T1.** Vaswani et al. (2017) "Attention is All You Need" — Transformer 원조.
- **T2.** [Predictive Modeling Transformer (2024)](https://dl.acm.org/doi/fullHtml/10.1145/3674029.3674037) — ACM 2024, encoder-decoder Transformer가 주식 short-window 예측에서 RNN/LSTM을 일관되게 능가.
- **T3.** [Hybrid LSTM-Transformer 2026](https://ui.adsabs.harvard.edu/abs/2026IEEEA..14.3926N/abstract) — IEEE Access 2026, LSTM(temporal) + Transformer(attention) + Federated Learning + Sentiment 결합.
- **T4.** [LLM-Generated Features Springer](https://link.springer.com/chapter/10.1007/978-981-95-4445-5_38) — LLM이 만든 사후 feature를 attention 기반으로 결합.
- **T5.** [Bangladesh Transformer](https://www.worldscientific.com/doi/10.1142/S146902682350013X) — emerging market 적용 사례. 데이터 부족 시 Transformer 자체로는 outperform 못함, 외부 sentiment 필요.
- **T6.** [Attention Mechanism Stock (2023)](https://dl.acm.org/doi/10.1145/3659154.3659157) — CNN-BiLSTM-attention 조합, multi-task 학습.
- **T7.** [Sentiment + LSTM Anser](https://www.anserpress.org/journal/jea/4/3/109/pdf) — FinBERT sentiment를 LSTM에 주입. 외부 modality 없으면 attention의 우위는 좁아짐.

**본 thesis 시사점**: Phase 1에서 transformer가 LSTM/GRU에 패배. 본 결과는
T2/T3의 일반 결론과 모순이지만, 본 데이터는 (a) 13–31주 매우 짧고, (b) 외부
sentiment 등 multimodal 보강이 없음. → "stock-style 직접 이식이 SMB에서 안 통하는"
이유의 정량 증거 (Phase 4 negative finding 강화).

## 2. 시계열 Foundation Model

- **F1.** [Chronos (Ansari et al., 2024, arxiv 2403.07815)](https://arxiv.org/abs/2403.07815) — Amazon. T5 기반 (20M~710M), tokenize→cross-entropy. 42 dataset zero-shot에서 supervised baseline 초과/근접.
- **F2.** [TimesFM (Das et al., 2024)](https://towardsdatascience.com/timesfm-the-boom-of-foundation-models-in-time-series-forecasting-29701e0b20b5/) — Google. 200M decoder-only, point forecast. Statistical baseline 일관 능가.
- **F3.** [Moirai (Woo et al., 2024)](https://towardsdatascience.com/moirai-time-series-foundation-models-for-universal-forecasting-dc93f74b330f/) — Salesforce. Mixture distribution → probabilistic forecast. LOTSA (27B points) pretrain.
- **F4.** [TimeGPT (Nixtla, 2023)](https://www.turingpost.com/p/timegpt) — first commercial TS foundation model.
- **F5.** [Lag-Llama (2024)](https://time-series-foundation-models.github.io/lag-llama.pdf) — probabilistic, lag feature injection. Open-source univariate.
- **F6.** [Moirai 2.0 (2025)](https://arxiv.org/html/2511.11698v1) — Salesforce 후속, "less is more" 단순 architecture가 더 강함.
- **F7.** [Chronos-2 (2025)](https://arxiv.org/pdf/2510.15821) — univariate→universal, multi-series + covariate 지원.
- **F8.** [TTM Tiny Time Mixer (IBM, 2024)](https://arxiv.org/pdf/2401.03955) — 1M~5M parameters, edge 적합.
- **F9.** [TSFM Benchmark Challenge (2025)](https://arxiv.org/html/2510.13654v1) — 벤치마크 누설 문제. 일부 모델이 평가셋을 pretrain 데이터에 포함시켜 47~184% 인플레.
- **F10.** [FPP3 Foundation Models chapter](https://otexts.com/fpppy/nbs/15-foundation-models.html) — Hyndman의 교과서적 정리.
- **F11.** [Databricks 2024 TS GenAI intro](https://www.databricks.com/blog/introduction-time-series-forecasting-generative-ai) — production 관점.

**본 thesis 시사점**: 본 데이터는 (a) T<32, (b) seasonality 한정, (c) 매출
zero-inflated. F1/F2/F3는 모두 raw value forecast로 학습된 모델이므로 SMB 단기
G/S/D 분류에서 zero-shot이 RF 56-feature보다 우위일 보장이 없다. 본 Phase 5
5A는 정확히 이 가설을 검증한다.

## 3. Stock-style 장기 Transformer 계열 (long-horizon TS)

- **S1.** [Informer (Zhou et al., AAAI 2021, arxiv 2012.07436)](https://arxiv.org/abs/2012.07436) — ProbSparse attention O(L log L), generative decoder.
- **S2.** Wu et al. (2021) "Autoformer", NeurIPS — series decomposition + auto-correlation.
- **S3.** [TFT (Lim et al., 2021, IJF)](https://www.sciencedirect.com/science/article/pii/S0169207021000637) — Temporal Fusion Transformer, multi-horizon + interpretable variable selection.
- **S4.** [PatchTST (Nie et al., ICLR 2023)](https://github.com/yuqinie98/PatchTST) — "A Time Series is Worth 64 Words". Channel-independence + patching. PatchTST/64: 21% MSE↓, 16.7% MAE↓.
- **S5.** Zeng et al. (2023) "Are Transformers Effective for TS Forecasting?" — **DLinear**가 단일 layer로 Informer/Autoformer/FEDformer 초과. Transformer 무용론 논쟁 점화.
- **S6.** Oreshkin et al. (2020) "N-BEATS", ICLR — basis expansion blocks. M4 우승.
- **S7.** Challu et al. (2023) "N-HiTS" — multi-rate sampling으로 N-BEATS 개선.
- **S8.** [Hybrid DLinear-PatchTST (2024)](https://www.researchgate.net/publication/391134489_Enhancing_Long-Term_Time_Series_Forecasting_via_Hybrid_DLinear-PatchTST_Ensemble_Framework) — 두 모델 ensemble.

**본 thesis 시사점**: S5의 "DLinear 가 Transformer 무용론" 결과가 본 데이터의 phase 1
finding(LSTM/GRU/TCN/TF 모두 RF 패배)과 정신적으로 일치. 본 Phase 5 5B에서
TFT/NBEATS/PatchTST/DLinear/Informer/Autoformer를 SMB에 모두 적용하여
"어느 stock SOTA도 SMB에서 RF를 못 이긴다"를 정량으로 입증할지 검증.

## 4. Retail · SMB · 상권 예측

- **R1.** [Makridakis et al. (2022) "M5 Accuracy Competition", IJF](https://www.sciencedirect.com/science/article/pii/S0169207021001874) — Walmart 42,840 series. 우승자 한국 학부생, LightGBM 220개 앙상블. 모든 top-50이 LightGBM 계열.
- **R2.** [M5 transfer learning (Spiliotis et al., 2022)](https://www.sciencedirect.com/science/article/abs/pii/S0169207021001606) — M5 우승자 방법을 transfer로 60× 가속.
- **R3.** [M5 Special Issue intro (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9232271/) — competition 종합.
- **R4.** [Sales forecasting Artefact](https://medium.com/artefact-engineering-and-data-science/sales-forecasting-in-retail-what-we-learned-from-the-m5-competition-445c5911e2f6) — production 적용 관점.
- **R5.** [Seoul commercial district survival LSTM (PLOS ONE 2024)](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0326307) — 3M개 서울 상점 2004–2018, LSTM으로 survival rate 예측 + 상권 8-class 재분류. **본 thesis와 가장 직접 비교 대상**.
- **R6.** [Seoul stores number/sales DL (DKE 2024)](https://www.sciencedirect.com/science/article/pii/S0169023X24000016) — DL로 상권 점포 수/평균 매출 예측.
- **R7.** [Seoul retail clustering (KOR 2025)](https://koreascience.kr/article/JAKO202518936002973.pub?lang=en) — large vs small retail 분리 ML clustering.
- **R8.** [Seoul retail boundary dataset (Sci Data 2025)](https://www.nature.com/articles/s41597-025-04958-1) — CV 기반 open retail boundary.

**본 thesis 시사점**: R1 → LightGBM이 retail의 정석. 본 thesis도 phase 5 5D에서
LightGBM + SHAP-weight + cost-sensitive 적용 → 본 데이터에 retail SOTA를 정직히
이식. R5 (Seoul LSTM survival)는 가장 직접 비교 대상이며 본 phase 5
findings는 R5와의 차이(short window, calendar alignment 도입)를 강조해야 함.

## 5. 사업 실패 / 부도 / 생존 예측

- **B1.** [Modeling business success survey (AI Review 2024)](https://link.springer.com/article/10.1007/s10462-023-10664-4) — 종합 review.
- **B2.** [Business failure with website text + DL (EJOR 2023)](https://www.sciencedirect.com/science/article/pii/S0377221722005495) — text + tabular 결합.
- **B3.** [Deep learning survival review (AI Review 2024)](https://link.springer.com/article/10.1007/s10462-023-10681-3) — DL survival 종합.
- **B4.** [Financial distress ML review (Wiley 2024)](https://onlinelibrary.wiley.com/doi/10.1111/exsy.13485) — 진화 review.
- **B5.** [Korean shipping bankruptcy (MEL 2026)](https://link.springer.com/article/10.1057/s41278-026-00353-8) — ensemble (LightGBM/CatBoost/XGBoost) > linear/DL.
- **B6.** [Corporate bankruptcy XAI (Korea Science 2023)](https://koreascience.kr/article/JAKO202320757748809.page) — SHAP feature selection.
- **B7.** Altman (1968) "Z-score" — 고전 baseline.
- **B8.** Mai et al. (2019) "Deep learning models for bankruptcy prediction using textual disclosures", *EJOR* — text disclosure + DL.

**본 thesis 시사점**: 본 데이터는 closing event(B 도메인)가 아닌 매출 slope의
G/S/D 분류. B 도메인 결과 — ensemble (LightGBM)이 DL보다 강함, SHAP이 핵심
설명 도구, 외부 modality(text)가 큰 boost — 가 본 thesis의 phase 5에 그대로
적용된다.

## 6. Class imbalance · Cost-sensitive · Focal loss

- **I1.** Lin et al. (2017) "Focal Loss for Dense Object Detection" — focal 원조. γ=2가 robust default.
- **I2.** [Enhanced Focal Loss insurance fraud (arxiv 2508.02283)](https://arxiv.org/html/2508.02283v2) — class imbalance + XAI 결합.
- **I3.** [Hybrid SMOTE-GAN credit fraud (MDPI 2023)](https://www.mdpi.com/2227-7072/11/3/110) — synthetic minority + GAN.
- **I4.** [Credit card fraud DL + imbalance (Frontiers 2025)](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1643292/full) — traditional + DL.
- **I5.** [Listed companies fraud SMOTE (PMC 2022)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9407419/) — SMOTE + ML.
- **I6.** Chawla et al. (2002) "SMOTE", JAIR — SMOTE 원조.
- **I7.** [Cost-sensitive deep features (arxiv 1508.03422)](https://arxiv.org/pdf/1508.03422) — cost-sensitive DL.
- **I8.** [Cost-sensitive medical (CBM 2021)](https://www.sciencedirect.com/science/article/pii/S235291482100174X) — medical imbalance.
- **I9.** [Churn SMOTE ensemble (Sci Reports 2025)](https://www.nature.com/articles/s41598-025-01031-0) — SMOTE + ensemble for churn.
- **I10.** Ling & Sheng (2008) "Cost-Sensitive Learning and the Class Imbalance Problem" — classic.

**본 thesis 시사점**: 본 데이터 Decline은 ~13%(stable이 majority). Phase 0에서
±0.5σ로 균형을 일부 회복했지만 5D에서 focal loss(γ 스윕) + class_weight +
per-cluster cost(fragile cluster Decline ×2)로 minority 회수율을 더 끌어올릴 수
있는지가 핵심.

## 7. Conditioning / FiLM (5C용)

- **C1.** [FiLM (Perez et al., AAAI 2018, arxiv 1709.07871)](https://arxiv.org/abs/1709.07871) — Feature-wise Linear Modulation 원조 (visual reasoning).
- **C2.** [Temporal FiLM (NeurIPS 2019)](http://papers.neurips.cc/paper/9217-temporal-film-capturing-long-range-sequence-dependencies-with-feature-wise-modulations.pdf) — sequence 데이터에 BN parameter를 RNN으로 조건부 변조.
- **C3.** [Feature-wise transformations Distill](https://distill.pub/2018/feature-wise-transformations/) — review tutorial.
- **C4.** [FiLM-Ensemble (OpenReview)](https://openreview.net/pdf?id=7vDt4_ulNyB) — FiLM으로 probabilistic ensemble.

**본 thesis 시사점**: 5C에서 tenure_log(업력)로 FiLM gate를 학습 → 같은 시계열이라도
"업력 9년 이상" 점포의 신호 처리를 conditionally 강조. 미팅 피드백
"신규 유입·업력이 상승에 유의미"를 모델 구조로 직접 인코딩.

## 8. SHAP / Interpretability

- **X1.** Lundberg & Lee (2017) "A Unified Approach to Interpreting Model Predictions" (NeurIPS) — SHAP 원조.
- **X2.** Lundberg et al. (2020) "From local explanations to global understanding with explainable AI for trees", *Nature MI* — TreeSHAP.
- **X3.** [SHAP practical drug dev (PMC 2024)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11513550/) — 실용 가이드.
- **X4.** [SHAP tree models intro (ML Mastery)](https://machinelearningmastery.com/a-gentle-introduction-to-shap-for-tree-based-models/) — tree-based SHAP 정리.

**본 thesis 시사점**: 5D에서 |mean SHAP|를 정적 feature weight으로 사용. Phase 2.1
shap_class_contrib.csv 결과를 활용.

## 9. Time-series classification (UCR/ROCKET 계열) — 보조 baseline

- **K1.** [ROCKET (Dempster et al., DMKD 2020, arxiv 1910.13051)](https://arxiv.org/abs/1910.13051) — 10K random conv kernels + linear classifier. UCR SOTA accuracy.
- **K2.** [MiniRocket (Dempster et al., KDD 2021, arxiv 2012.08791)](https://arxiv.org/pdf/2012.08791) — 75× faster than Rocket.
- **K3.** [Detach-ROCKET (DMKD 2024)](https://link.springer.com/article/10.1007/s10618-024-01062-7) — SFD로 ROCKET feature pruning.
- **K4.** Fawaz et al. (2020) "InceptionTime", DMKD — TSC용 inception ensemble.

**본 thesis 시사점**: 본 thesis는 multivariate(6채널) + 짧은(13–31주) sequence.
ROCKET 계열은 univariate UCR에서 빛나지만 6-channel + 17K~34K 점포 규모에서는
적합성 검증 필요. 본 phase 5는 5C/5B에 집중하고 ROCKET은 future work.

## 10. 비교 매트릭스

| Model family | Domain | Data scale | Architecture | SMB G/S/D 적용 가능? | Phase 5 plan |
|---|---|---|---|---|---|
| LSTM/GRU/TCN/Transformer (vanilla) | Stock, general TS | 수천 timestep | RNN / attention | 이미 시도, **RF 패배** | (skip) |
| TFT | Multi-horizon retail | 30–730d | attention + variable sel. | yes | **5B** |
| N-BEATS / N-HiTS | M4/M5 forecast | 30–730d | basis expansion | yes | **5B** |
| PatchTST | ETT/Weather long-horizon | 96–720d | patch + channel-indep | yes | **5B** |
| DLinear | ETT/Weather | 96–720d | single linear | yes | **5B** |
| Informer / Autoformer | Long-horizon | 96–720d | sparse attention | yes (overkill) | **5B** |
| Chronos | Universal TS | universal | T5 + tokenize | zero-shot 시도 가치 | **5A** |
| TimesFM | Universal TS | universal | decoder-only | zero-shot 시도 가치 | **5A** |
| Moirai | Universal TS | LOTSA | mixture dist | zero-shot 시도 가치 | **5A** |
| TimeGPT | Universal TS | Nixtla | proprietary | API only, skip | (future) |
| LightGBM (M5 winner) | Retail | 5y daily | GBDT | **이미 강력 baseline** | (compare baseline) |
| SHAP-weighted GBDT | XAI | tabular | post-hoc weight | yes | **5D** |
| Focal Loss / Class weight | Fraud, imbalance | tabular/seq | loss mod | yes | **5D** |
| FiLM (tenure-cond) | Multi-task / VQA | varied | conditioning | yes (custom) | **5C** |
| ROCKET / MiniRocket | UCR univariate | 1-channel | random kernels | partial (multivariate→) | (future) |
| Survival LSTM (Seoul) | Korean commercial district | 14y, 3M stores | LSTM survival | direct compare | **R5 cite, no replicate** |

## 11. 본 thesis가 차별화해야 할 5가지

1. **계절성 캘린더 정렬**: stock/M5 어디에도 없는 SMB-specific 처리 (v5 main contribution).
2. **G/S/D 3-class 분류 + 회귀-후-버킷 비교**: 주식 literature는 거의 regression. 본 thesis는 분류가 더 적합함을 정량 입증.
3. **업력(tenure) cohort 효과**: 주식에는 없는 개념. Phase 2.4 C3 + Phase 5 5C FiLM.
4. **6-channel multivariate, very short window**: UCR/M5와 차원이 다른 setup. RF가 강한 이유.
5. **Spatial spillover negative finding**: 같은 동/업종 GNN이 작동 안 함 (Phase 3). Stock 문헌에서 inter-stock correlation은 효과적이지만 SMB에서는 그렇지 않음을 honest 보고.

## 12. 참고: 본 phase 5 산출물에서 cross-reference 필요

- `260511/docs/260430_claude_dynamics_explanation.md` — 9-phase 종합
- `260511/docs/stock_vs_smb_dynamics.md` — Phase 4 정성 비교 (본 설문이 보강)
- `260511/phase5_external/outputs/tables/*` — 5A/5B/5C/5D 정량 결과 (예정)

## 13. 인용 카운트

총 인용: 6 (LSTM) + 7 (Transformer) + 11 (Foundation) + 8 (long-horizon TS) +
8 (retail/Seoul) + 8 (failure/survival) + 10 (imbalance) + 4 (FiLM) + 4 (SHAP) +
4 (ROCKET) = **70편** (목표 30~50 초과 달성).
