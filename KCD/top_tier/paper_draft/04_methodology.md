# 4. Methodology

*Target: ~2.5 pages in final paper (~1500 words). Equations in LaTeX notation.*

---

## 4.1 Data and Setting

We use the KCD weekly card-transaction panel covering $N = 59{,}089$ independent restaurants in the Seoul metropolitan area, observed over $T = 137$ weeks from 2021-01-01 to 2023-08-28 (6.58M store-weeks). For each store–week, we observe card sales amount ($\texttt{sales\_card}$), transaction counts, new-customer counts ($\texttt{customer\_new}$), delivery sales share, and morning/weekend sales share. We augment these behavioral signals with KCD's internal business classification (UDX category) and store geo-identifiers (administrative dong).

**Observation window and prediction target.** We define the *observation window* as the first $T_{\text{obs}} = 30$ weeks of each store's panel. The *prediction target* is the store's overall trend slope $s_i^{\text{all}}$ computed on monthly-mean-smoothed log-sales across the full observed period. Following established stage-model conventions (Churchill & Lewis, 1983), we trichotomize:
$$
y_i = \begin{cases}
\text{Growth} & \text{if } s_i^{\text{all}} > 0.5 \cdot \sigma(s^{\text{all}}) \\
\text{Decline} & \text{if } s_i^{\text{all}} < -0.5 \cdot \sigma(s^{\text{all}}) \\
\text{Stable} & \text{otherwise}
\end{cases}
$$
yielding class proportions $\{$Growth: 40.0%, Stable: 38.2%, Decline: 21.7%$\}$. Sensitivity to the $0.5\sigma$ cutoff is reported in Section 5 (Robustness §19).

**Closure detection.** A store $i$ is classified as *closed* if its last observation date precedes the panel end minus a cutoff $c_{\text{closure}}$: $\text{closed}_i = \mathbb{1}[d_i^{\text{last}} < d_{\text{end}} - c_{\text{closure}}]$. We set $c_{\text{closure}} = 4$ weeks in the primary specification; sensitivity to $c_{\text{closure}} \in \{2, 4, 6, 8\}$ is reported in Robustness §19.

## 4.2 Survival Analysis and Survivorship Bias Quantification

We estimate Kaplan-Meier survival functions stratified by outcome class and UDX category, supplemented by log-rank tests for homogeneity. To assess covariate-adjusted closure hazard, we fit a Cox proportional-hazards model:
$$
h_i(t) = h_0(t) \exp\left(\beta_1 \text{slope\_early}_i + \beta_2 \text{cv}_i + \beta_3 \text{nc\_rate}_i + \beta_4 \text{mdd}_i + \beta_5 r^2_i\right)
$$
where $\text{cv}$ is the weekly-sales coefficient of variation, $\text{nc\_rate}$ is the mean new-customer ratio, and $\text{mdd}$ is the maximum drawdown. We test the proportional-hazards assumption via Schoenfeld residuals with rank time-transformation (Grambsch & Therneau, 1994); covariates failing the test ($p < 0.05$) are flagged for stratified-Cox reinterpretation (§18).

**Survivorship bias quantification.** We compare closure rates between the lifecycle-panel subset ($n^{\text{panel}} = 50{,}635$ stores with $\geq 52$-week observation) and the panel-exterior set ($n^{\text{ext}} = 8{,}454$). The ratio $\text{closure}^{\text{ext}} / \text{closure}^{\text{panel}}$ quantifies the bias magnitude.

## 4.3 Hybrid Representation Learning

We propose a **three-component representation** for each store $i$:

1. **Engineered features** $\mathbf{x}_i^{\text{eng}} \in \mathbb{R}^{46}$: computed from the 30-week observation window, including: slope at early/mid/late subwindows; rolling statistics (5/10/15-week MA, std); new-customer ratio trend; delivery, weekend, morning ratios; volatility (coefficient of variation); maximum drawdown; and difference features between adjacent subwindows.
2. **Cluster-state features** $\mathbf{x}_i^{\text{clu}} \in \{0, 1\}^{K_{\text{km}} + K_{\text{ks}}}$: one-hot encoding of K-Means ($K_{\text{km}}=4$) and K-Shape ($K_{\text{ks}}=7$) cluster assignments fitted on standardized 30-week sales sequences.
3. **Change-point features** $\mathbf{x}_i^{\text{cp}} \in \mathbb{R}^7$: for each sequence, we identify the position $t^*$ maximizing the slope break $|s^{\text{pre}}_t - s^{\text{post}}_t|$ via exhaustive split; we record $t^*/T_{\text{obs}}$, $s^{\text{pre}}$, $s^{\text{post}}$, their difference, pre-to-CP magnitude, and binary up/down indicators.

The Proposed Model (D) concatenates these: $\mathbf{x}_i = [\mathbf{x}_i^{\text{eng}}, \mathbf{x}_i^{\text{clu}}, \mathbf{x}_i^{\text{cp}}] \in \mathbb{R}^{64}$. To avoid cross-fold information leakage, K-Means and K-Shape are refit on each training fold's data only; test-fold cluster assignments are obtained by applying the trained centroids (Robustness §17 shows this fold-safe protocol yields $\Delta \text{F1} = -0.002$ vs full-data fitting, confirming no material leakage).

**Prediction.** We train an XGBoost multi-class classifier (500 trees, depth 6, learning rate 0.05) with StandardScaler-normalized inputs under stratified 5-fold cross-validation. Class balance is handled via inverse-frequency sample weighting. Evaluation metrics: Macro-F1, per-class recall, and AUC-OvR.

**Deep-learning baselines.** For fair comparison, we implement LSTM, GRU, and Transformer encoders taking either (i) univariate log-sales sequence or (ii) a 5-channel multivariate input (sales, nc-ratio, delivery, weekend, morning). All deep models use identical 5-fold splits, per-store standardization, class-weighted cross-entropy, AdamW with cosine annealing, and 15–20 epochs. Architecture details are in Appendix A.

## 4.4 Causal Identification: Granger, PSM+DiD, Panel FE

To identify whether new-customer inflow is a *leading* cause of sales dynamics (the "Golden Cross" hypothesis), we triangulate three methods.

**Granger causality.** For each eligible store ($\geq 40$ weekly observations, $\sigma > 0$), we fit bidirectional VAR(4) on first-differenced $\{\log \texttt{sales}, \texttt{nc\_ratio}\}$ and record the Wald $F$-test $p$-value in each direction. We report the percentage of stores with $p_{\text{nc}\to\text{sales}} < 0.05$ vs $p_{\text{sales}\to\text{nc}} < 0.05$ and the asymmetry gap.

**Propensity-Score-Matched Difference-in-Differences.** We define a *Golden Cross* treatment for store $i$ as a substantial upward shift in its new-customer ratio:
$$
\text{gc\_delta}_i = \frac{\overline{\texttt{nc\_ratio}}_i^{\text{peak}\pm2} - \overline{\texttt{nc\_ratio}}_i^{\text{pre}(1..8)}}{\overline{\texttt{nc\_ratio}}_i^{\text{pre}(1..8)} + \epsilon}
$$
Stores above the 70th percentile on $\text{gc\_delta}$ are treated ($T=1$). We estimate propensity scores via logistic regression on 8 covariates including pre-GC sales level, variance, slope, initial slope, CV, and drawdown:
$$
\pi_i = P(T_i = 1 \mid \mathbf{z}_i)
$$
Nearest-neighbor matching within caliper 0.05 and exact-match on pre-sales quartile yields 15,189 treated-control pairs. The DiD estimator is
$$
\widehat{\text{ATT}} = \mathbb{E}[\Delta y_i^{\text{post-pre}} \mid T=1] - \mathbb{E}[\Delta y_i^{\text{post-pre}} \mid T=0, \text{matched}]
$$
where $y_i$ is log-sales averaged over the 8-week pre/post window around each treated unit's GC week. We test the parallel-trends assumption via a 1-sample $t$-test on weekly pre-period differences; when violated, we supplement with an **event study** (week-by-week diff plot) and a **placebo test** (random fake GC-week reassignment, 20 rounds) to assess whether $\widehat{\text{ATT}}$ is mechanically driven.

**Panel two-way fixed-effects regression.** As a third check independent of treatment definition:
$$
\log \text{sales}_{it} = \alpha_i + \lambda_t + \sum_{\ell \in \{1, 2, 4\}} \gamma_\ell \, \texttt{nc\_ratio}_{i, t-\ell} + \delta \log \text{sales}_{i, t-1} + \varepsilon_{it}
$$
with cluster-robust standard errors at the store level.

## 4.5 Early Warning System: Calibration and Cost-Sensitive Operating Points

From 5-fold out-of-fold predictions of the Proposed Model (D), we extract per-store class probabilities $P(y_i = \text{Decline} \mid \mathbf{x}_i)$ and transform to a 0–100 risk score: $r_i^{\text{dec}} = 100 \cdot P(y_i = \text{Decline} \mid \mathbf{x}_i)$ (analogously for Growth opportunity score).

**Calibration** is assessed via Brier score and reliability curves (10 equal-width probability bins).

**Cost-sensitive threshold analysis.** Assuming a stylized policy where decline-flagged stores receive a support intervention of cost $C_{\text{support}} = 2$ (unit), with prevention benefit $B_{\text{prevent}} = 10$ for true positives (averting a closure) and loss $C_{\text{miss}} = 8$ for false negatives (missed decline), we compute net utility at threshold $\tau$:
$$
U(\tau) = |TP(\tau)|(B_{\text{prevent}} - C_{\text{support}}) - |FP(\tau)| C_{\text{support}} - |FN(\tau)| C_{\text{miss}}
$$
The optimal $\tau^*$ is reported alongside precision/recall/F1 at the full operating-point curve (§14).

## 4.6 Robustness Protocol

We execute a seven-fold self-audit (§16–22): (i) outcome-definition sanity against trivial slope-only baseline; (ii) cluster cross-fold leakage via fold-safe refitting; (iii) Cox PH assumption via Schoenfeld residuals; (iv) threshold sensitivity across closure cutoffs and outcome slope multipliers; (v) enhanced PSM with pre-period level matching and placebo testing; (vi) cluster external validity separating UDX category from outcome; (vii) multivariate deep-learning fair comparison. Each audit addresses a specific reviewer concern and is reported with full numerical support in Section 5.

---

## Notes for revision

- **Word count**: ~1500 words
- **Equations**: LaTeX block format. Consider compressing in final version if space tight
- **Appendix A** needs full deep-learning architecture details (LSTM: bi-directional 2-layer hidden=64 dropout=0.3; Transformer: d_model=48 nhead=4 layers=2)
- **Subsection ordering**: Could swap 4.4 and 4.3 if causal-inference is primary contribution story. Currently prediction-first ordering matches artifact-focused framing (DSR).
- **Table reference**: cross-reference Robustness §16-22 results — add "see §19" etc. in final paper.
