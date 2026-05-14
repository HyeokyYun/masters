# 첨부 표 2 — 외부 SOTA 14 모델 vs RF baseline (6 panel 평균)

원본: `/home/hyeoky98/kcd/260511/phase5_external/outputs/tables/phase5_summary.csv`.
RF baseline (rf_tabular) 의 6 panel 평균 macro-F1 = 0.4999. n_panels = 6
(`sy2021_sm01_w3m_off1`, `sy2021_sm05_w3m_off1`, `sy2022_sm01_w3m_off1`,
`sy2022_sm05_w3m_off1`, `sy2021_sm01_w7m_off1`, `sy2022_sm01_w7m_off1`).

| 그룹 | 모델 | ΔF1 vs RF | 5% 유의 (n_sig_p05) | RF 대비 wins |
| --- | --- | ---: | :---: | :---: |
| LightGBM family | **lgbm_tabular** | **+0.0075** | 2 / 6 | **5 / 6** |
| LightGBM family | lgbm_shap_weighted | +0.0071 | 2 / 6 | 5 / 6 |
| LightGBM family | lgbm_decline_x2 | +0.0026 | 3 / 6 | 4 / 6 |
| Cost-sensitive | rf_shap_weighted | −0.0004 | 0 / 6 | 2 / 6 |
| SMB attention | feature_attn_mlp | −0.035 | 6 / 6 | 0 / 6 |
| Cost-sensitive | rf_decline_x2 | −0.035 | 6 / 6 | 0 / 6 |
| SMB attention | film_tenure_lstm | −0.047 | 4 / 6 | 0 / 6 |
| Cost-sensitive | rf_decline_x3 | −0.063 | 6 / 6 | 0 / 6 |
| SMB attention | time_attn_lstm | −0.092 | 1 / 6 | 0 / 6 |
| Stock SOTA | dlinear | −0.139 | 6 / 6 | 0 / 6 |
| Foundation | moirai_small (n=1) | −0.187 | 1 / 1 | 0 / 1 |
| Foundation | chronos_bolt_small | −0.211 | 6 / 6 | 0 / 6 |
| Stock SOTA | nhits | −0.221 | 6 / 6 | 0 / 6 |
| Stock SOTA | tft | −0.238 | 6 / 6 | 0 / 6 |
| Stock SOTA | nbeats | −0.246 | 6 / 6 | 0 / 6 |

## 핵심 요약

- LightGBM 패밀리 3 종만 RF 능가. 나머지 외부 SOTA 11 종 (foundation 2 + stock SOTA 7 + SMB attention 3 - 패배 측만) 은 모두 패배.
- 특히 foundation zero-shot (chronos_bolt, moirai) 과 stock SOTA (tft, nbeats, nhits) 는 거의 random guess 수준 (macro-F1 ≈ 0.25 ~ 0.31).
- 4 mechanism 가설 (§6.2.4): short window / regression-to-classification 변환 손실 / multivariate channel compression / calendar season confound dominance 가 본 negative 패턴을 구조적으로 설명.

추가 출처:
- `foundation_zeroshot_compare.csv` (Chronos, Moirai)
- `neuralforecast_compare.csv` (TFT/N-BEATS/N-HiTS/PatchTST/DLinear/Informer/Autoformer)
- `attention_compare.csv` (SMB attention 3 종)
- `weighting_compare.csv` (cost-sensitive / SHAP-weighted)
