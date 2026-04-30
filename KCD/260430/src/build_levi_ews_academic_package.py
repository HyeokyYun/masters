"""Build LEVI/EWS academic-positioning package for the 260430 follow-up.

The script only reads existing KCD/top_tier/thesis outputs and writes derived
summaries under `/home/hyeoky98/kcd/260430`.
"""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


ROOT = Path("/home/hyeoky98/kcd")
BASE = ROOT / "260430"
TABLE_DIR = BASE / "outputs" / "tables"
FIG_DIR = BASE / "outputs" / "figures"
DOC_DIR = BASE / "docs"

THESIS_OUT = ROOT / "thesis" / "analysis" / "outputs"
TOP_OUT = ROOT / "top_tier" / "outputs" / "tables"


LEVI_COLS = [
    "levi_v1_balance",
    "levi_v2_log_odds",
    "levi_v3_trend_mean",
    "levi_v4_trend_median",
    "levi_v5_shrinkage20",
]


def _read_csv(path: Path, **kwargs) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path, **kwargs)


def load_inputs() -> dict[str, pd.DataFrame]:
    return {
        "levi_macro_correlations": _read_csv(THESIS_OUT / "levi_macro_correlations.csv"),
        "levi_macro_gu": _read_csv(THESIS_OUT / "levi_macro_gu.csv"),
        "external_validation_correlations": _read_csv(TOP_OUT / "external_validation_correlations.csv"),
        "external_validation_gu": _read_csv(TOP_OUT / "external_validation_gu.csv"),
        "external_temporal_correlations": _read_csv(TOP_OUT / "external_temporal_correlations.csv"),
        "ews_calibration": _read_csv(TOP_OUT / "ews_calibration_metrics.csv"),
        "ews_operating": _read_csv(TOP_OUT / "ews_operating_points_decline.csv"),
        "ews_cost": _read_csv(TOP_OUT / "ews_cost_benefit.csv"),
        "ews_segment": _read_csv(TOP_OUT / "ews_segment_score_distribution.csv"),
        "ews_scores": _read_csv(TOP_OUT / "ews_scores_per_store.csv"),
        "hybrid_summary": pd.read_csv(TOP_OUT / "hybrid_prediction_summary.csv", header=[0, 1], index_col=0),
        "seasonal_summary": _read_csv(TABLE_DIR / "seasonal_prediction_summary.csv"),
        "granger_summary": _read_csv(TOP_OUT / "granger_summary.csv"),
        "did_psm_ate": _read_csv(TOP_OUT / "did_psm_ate.csv"),
        "fe_panel": _read_csv(TOP_OUT / "fe_panel_regression.csv"),
    }


def get_corr(df: pd.DataFrame, metric: str, external: str) -> tuple[float, float, int | None]:
    row = df[(df["kcd_metric"] == metric) & (df["external_metric"] == external)]
    if row.empty:
        return float("nan"), float("nan"), None
    r = row.iloc[0]
    return float(r["pearson"]), float(r["spearman"]), int(r["n"]) if "n" in r else None


def build_levi_tables(inputs: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    ext = inputs["external_validation_correlations"]
    temporal = inputs["external_temporal_correlations"]

    lp_dyn = get_corr(ext, "kcd_levi", "lp_pct_change")
    lp_level = get_corr(ext, "kcd_levi", "lp_mean")
    closure_mean = get_corr(ext, "kcd_levi", "permit_closure_rate_mean")
    closure_med = get_corr(ext, "kcd_levi", "permit_closure_rate_median")

    temporal_rows = []
    for _, row in temporal.iterrows():
        temporal_rows.append(
            {
                "test_family": "temporal_external_validity",
                "claim": f"{row['kcd_metric']} tracks {row['external_metric']}",
                "evidence": f"Pearson={row['pearson']:.3f}, Spearman={row['spearman']:.3f}, n={int(row['n'])}",
                "pearson": row["pearson"],
                "spearman": row["spearman"],
                "n": int(row["n"]),
                "academic_use": "Shows KCD transaction series aligns with independent Seoul commercial indicators.",
                "risk": "Temporal validation supports data credibility but is not a causal test.",
            }
        )

    validity = pd.DataFrame(
        [
            {
                "test_family": "convergent_validity",
                "claim": "LEVI captures dynamic neighborhood vitality rather than only store-level noise.",
                "evidence": f"LEVI vs living-population change Pearson={lp_dyn[0]:.3f}, Spearman={lp_dyn[1]:.3f}, n={lp_dyn[2]}",
                "pearson": lp_dyn[0],
                "spearman": lp_dyn[1],
                "n": lp_dyn[2],
                "academic_use": "Use as construct-validation evidence for local business vitality.",
                "risk": "n=25 districts; treat as external validity evidence, not causal identification.",
            },
            {
                "test_family": "discriminant_check",
                "claim": "LEVI is not merely a proxy for neighborhood size.",
                "evidence": f"LEVI vs living-population level Pearson={lp_level[0]:.3f}, Spearman={lp_level[1]:.3f}, n={lp_level[2]}",
                "pearson": lp_level[0],
                "spearman": lp_level[1],
                "n": lp_level[2],
                "academic_use": "Use to argue the construct is about change/vitality, not area scale.",
                "risk": "This is a negative-control style check; it does not prove full discriminant validity.",
            },
            {
                "test_family": "criterion_validity",
                "claim": "LEVI moves opposite to administrative closure risk.",
                "evidence": f"LEVI vs permit closure rate mean Pearson={closure_mean[0]:.3f}, Spearman={closure_mean[1]:.3f}, n={closure_mean[2]}",
                "pearson": closure_mean[0],
                "spearman": closure_mean[1],
                "n": closure_mean[2],
                "academic_use": "Use as criterion validity against independent administrative data.",
                "risk": "Closure-register timing and KCD outcome definitions are not identical.",
            },
            {
                "test_family": "criterion_validity_robustness",
                "claim": "LEVI-closure direction survives an alternative closure-rate statistic.",
                "evidence": f"LEVI vs permit closure rate median Pearson={closure_med[0]:.3f}, Spearman={closure_med[1]:.3f}, n={closure_med[2]}",
                "pearson": closure_med[0],
                "spearman": closure_med[1],
                "n": closure_med[2],
                "academic_use": "Use as robustness for criterion validity.",
                "risk": "Spearman magnitude is weaker, so frame as directional support.",
            },
            *temporal_rows,
        ]
    )

    gu = inputs["levi_macro_gu"]
    robust_rows = []
    for a, b in combinations(LEVI_COLS, 2):
        robust_rows.append(
            {
                "levi_formula_a": a,
                "levi_formula_b": b,
                "pearson": gu[a].corr(gu[b], method="pearson"),
                "spearman": gu[a].corr(gu[b], method="spearman"),
                "n": gu[[a, b]].dropna().shape[0],
            }
        )
    robustness = pd.DataFrame(robust_rows).sort_values("pearson")
    return validity, robustness


def build_levi_leave_one_out(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    gu = inputs["external_validation_gu"].copy()
    tests = [
        ("lp_pct_change", "living_population_change"),
        ("permit_closure_rate_mean", "permit_closure_rate_mean"),
        ("permit_closure_rate_median", "permit_closure_rate_median"),
    ]
    rows = []
    for dropped in sorted(gu["sigungu"].astype(str).unique()):
        sub = gu[gu["sigungu"].astype(str) != dropped]
        for col, label in tests:
            rows.append(
                {
                    "dropped_sigungu": dropped,
                    "external_metric": label,
                    "pearson": sub["kcd_levi"].corr(sub[col], method="pearson"),
                    "spearman": sub["kcd_levi"].corr(sub[col], method="spearman"),
                    "n": len(sub),
                }
            )
    return pd.DataFrame(rows)


def build_ews_tables(inputs: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    cal = inputs["ews_calibration"].iloc[0]
    operating = inputs["ews_operating"]
    cost = inputs["ews_cost"]
    seg = inputs["ews_segment"]
    hybrid = inputs["hybrid_summary"]
    seasonal = inputs["seasonal_summary"]

    best_cost = cost.sort_values("net_utility", ascending=False).iloc[0]
    best_threshold = float(best_cost["threshold"])
    best_op = operating.loc[(operating["threshold"] - best_threshold).abs().idxmin()]

    proposed = hybrid.loc["D_base_cluster_cp_PROPOSED"]
    base = hybrid.loc["A_base_46"]
    seasonal_best = seasonal.sort_values("macro_f1", ascending=False).iloc[0]

    ews_eval = pd.DataFrame(
        [
            {
                "evaluation_dimension": "ranking_quality_decline",
                "claim": "EWS ranks future decline risk far above the base prevalence.",
                "evidence": f"Decline AP={cal['ap_decline']:.3f}; baseline decline rate={cal['baseline_decline_rate']:.3f}; lift={cal['ap_decline']/cal['baseline_decline_rate']:.2f}x",
                "metric_value": cal["ap_decline"],
                "baseline": cal["baseline_decline_rate"],
                "academic_use": "Use as the primary decision-support ranking metric.",
                "risk": "AP is a predictive metric; connect it to intervention decisions through threshold utility.",
            },
            {
                "evaluation_dimension": "ranking_quality_growth",
                "claim": "The same artifact can also rank growth opportunities.",
                "evidence": f"Growth AP={cal['ap_growth']:.3f}; baseline growth rate={cal['baseline_growth_rate']:.3f}; lift={cal['ap_growth']/cal['baseline_growth_rate']:.2f}x",
                "metric_value": cal["ap_growth"],
                "baseline": cal["baseline_growth_rate"],
                "academic_use": "Use as secondary evidence for opportunity targeting.",
                "risk": "Do not over-center growth targeting if the paper is about decline warning.",
            },
            {
                "evaluation_dimension": "calibration",
                "claim": "EWS probabilities are usable as risk scores rather than only class labels.",
                "evidence": f"Brier decline={cal['brier_decline']:.3f}; Brier growth={cal['brier_growth']:.3f}",
                "metric_value": cal["brier_decline"],
                "baseline": None,
                "academic_use": "Use to justify risk-score output for decision support.",
                "risk": "Add reliability-bin table if a journal reviewer asks for calibration detail.",
            },
            {
                "evaluation_dimension": "operating_point",
                "claim": "The artifact supports explicit policy trade-offs between missing decline and over-flagging.",
                "evidence": f"Optimal threshold={best_threshold:.2f}; net utility={int(best_cost['net_utility'])}; precision={best_op['decline_precision']:.3f}; recall={best_op['decline_recall']:.3f}; flagged={best_op['flagged_pct']:.1%}",
                "metric_value": best_cost["net_utility"],
                "baseline": None,
                "academic_use": "Use as DSR-style artifact evaluation beyond accuracy.",
                "risk": "Cost weights are assumed; report sensitivity over thresholds and costs.",
            },
            {
                "evaluation_dimension": "representation_value",
                "claim": "Hybrid trajectory representation improves the EWS input model.",
                "evidence": f"Base Macro-F1={float(base[('macro_f1','mean')]):.3f}, AUC={float(base[('auc_ovr','mean')]):.3f}; Proposed Macro-F1={float(proposed[('macro_f1','mean')]):.3f}, AUC={float(proposed[('auc_ovr','mean')]):.3f}",
                "metric_value": float(proposed[("macro_f1", "mean")]),
                "baseline": float(base[("macro_f1", "mean")]),
                "academic_use": "Use to show the artifact is not only a dashboard wrapper around a generic model.",
                "risk": "Keep leakage and seasonal-window robustness clearly separated.",
            },
            {
                "evaluation_dimension": "seasonality_robustness",
                "claim": "The core early signal survives calendar-matched rolling-window checks, though weaker than full hybrid.",
                "evidence": f"Best seasonal Macro-F1={seasonal_best['macro_f1']:.3f}; Decline recall={seasonal_best['recall_Decline']:.3f}; spec={seasonal_best['spec_id']}",
                "metric_value": seasonal_best["macro_f1"],
                "baseline": float(base[("macro_f1", "mean")]),
                "academic_use": "Use as a methodological response to the 260430 meeting concern.",
                "risk": "Seasonal check uses a simpler balanced logistic model; present it as robustness, not replacement.",
            },
        ]
    )

    operating_selected = operating[
        operating["threshold"].isin([0.05, 0.10, 0.20, 0.30, 0.50, 0.70, 0.90])
    ].merge(cost, on=["threshold", "tp", "fp", "fn"], how="left")
    high_risk_segments = seg.sort_values("mean", ascending=False).head(8).copy()
    return ews_eval, operating_selected, high_risk_segments


def build_ews_calibration_bins(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    scores = inputs["ews_scores"].copy()
    scores["decline_prob"] = scores["risk_score_decline"] / 100.0
    scores["is_decline"] = (scores["outcome_3"] == "Decline").astype(int)
    scores["risk_decile"] = pd.qcut(scores["decline_prob"], 10, labels=False, duplicates="drop") + 1
    bins = (
        scores.groupby("risk_decile", observed=True)
        .agg(
            n=("public_id", "count"),
            mean_predicted_decline=("decline_prob", "mean"),
            observed_decline_rate=("is_decline", "mean"),
            decline_cases=("is_decline", "sum"),
        )
        .reset_index()
    )
    total_decline = bins["decline_cases"].sum()
    bins["calibration_gap"] = bins["observed_decline_rate"] - bins["mean_predicted_decline"]
    bins["decline_capture_share"] = bins["decline_cases"] / total_decline
    return bins


def build_ews_cost_scenarios(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    operating = inputs["ews_operating"].copy()
    scenarios = [
        {
            "scenario": "conservative_support",
            "benefit_tp": 6,
            "cost_fp": 3,
            "cost_fn": 8,
            "interpretation": "Support resources are expensive; false positives matter more.",
        },
        {
            "scenario": "balanced_prevention",
            "benefit_tp": 10,
            "cost_fp": 2,
            "cost_fn": 8,
            "interpretation": "Baseline policy scenario used for balanced preventive support.",
        },
        {
            "scenario": "aggressive_prevention",
            "benefit_tp": 12,
            "cost_fp": 1,
            "cost_fn": 10,
            "interpretation": "Missing true decline is costly; broad early support is acceptable.",
        },
    ]
    rows = []
    for scenario in scenarios:
        for _, row in operating.iterrows():
            utility = (
                row["tp"] * scenario["benefit_tp"]
                - row["fp"] * scenario["cost_fp"]
                - row["fn"] * scenario["cost_fn"]
            )
            rows.append(
                {
                    **scenario,
                    "threshold": row["threshold"],
                    "tp": row["tp"],
                    "fp": row["fp"],
                    "fn": row["fn"],
                    "decline_precision": row["decline_precision"],
                    "decline_recall": row["decline_recall"],
                    "flagged_pct": row["flagged_pct"],
                    "scenario_net_utility": utility,
                }
            )
    out = pd.DataFrame(rows)
    out["is_best_in_scenario"] = out.groupby("scenario")["scenario_net_utility"].transform("max").eq(
        out["scenario_net_utility"]
    )
    return out


def build_framing_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    evidence_ledger = pd.DataFrame(
        [
            {
                "component": "LEVI",
                "weak_version": "We made a local vitality index.",
                "academic_version": "LEVI operationalizes local business vitality and is validated against independent population, closure, and commercial-sales indicators.",
                "minimum_evidence_needed": "Formula robustness, convergent validity, criterion validity, and scope cautions.",
                "current_status": "Mostly available from existing external-validation outputs.",
            },
            {
                "component": "EWS",
                "weak_version": "We predict declining stores.",
                "academic_version": "A calibrated, cost-sensitive early-warning artifact prioritizes intervention targets under explicit false-positive/false-negative trade-offs.",
                "minimum_evidence_needed": "AP, calibration, operating thresholds, cost utility, subgroup stability, examples.",
                "current_status": "Mostly available from existing EWS outputs.",
            },
            {
                "component": "Hybrid representation",
                "weak_version": "Cluster and change point improve accuracy.",
                "academic_version": "Trajectory-state and change-point representations encode lifecycle dynamics that improve decision-support predictions.",
                "minimum_evidence_needed": "Ablation against base features plus robustness to leakage and seasonality.",
                "current_status": "Available for main top_tier run; seasonal robustness now available in 260430.",
            },
            {
                "component": "Golden Cross",
                "weak_version": "New customers rise before sales rebound.",
                "academic_version": "New-customer inflow is a plausible leading mechanism for rebound, triangulated by Granger, matched DiD, and fixed-effects evidence.",
                "minimum_evidence_needed": "Triangulated tests with careful non-causal or cautiously causal wording.",
                "current_status": "Available as support, not necessary as the central paper contribution.",
            },
        ]
    )

    venue = pd.DataFrame(
        [
            {
                "venue": "HICSS",
                "fit": "High",
                "best_framing": "Decision-support artifact for small-business vitality monitoring.",
                "lead_component": "EWS + LEVI",
                "what_to_emphasize": "Artifact design, external validation, policy-use threshold, explainable risk scores.",
                "risk": "Needs a clean paper narrative; avoid trying to include every thesis analysis.",
            },
            {
                "venue": "DSS",
                "fit": "Medium-high after polish",
                "best_framing": "Calibrated and cost-sensitive early-warning system from transaction traces.",
                "lead_component": "EWS + Hybrid",
                "what_to_emphasize": "Decision analytics, calibration, operating points, cost utility, representation ablation.",
                "risk": "Must strengthen artifact evaluation and reviewer-facing methodology.",
            },
            {
                "venue": "Information & Management",
                "fit": "Medium",
                "best_framing": "Data-driven small-business lifecycle intelligence.",
                "lead_component": "Hybrid + EWS",
                "what_to_emphasize": "Managerial relevance, digital trace data, actionable analytics.",
                "risk": "Needs tighter theory of digital trace-based decision support.",
            },
            {
                "venue": "Small Business Economics",
                "fit": "Medium, different framing",
                "best_framing": "Micro transaction traces as indicators of urban small-business vitality.",
                "lead_component": "LEVI + external data",
                "what_to_emphasize": "Small-business dynamics, local economic vitality, closure/growth distribution.",
                "risk": "Needs stronger economic theory and cautious claims; EWS should be secondary.",
            },
            {
                "venue": "ICIS",
                "fit": "Possible but risky",
                "best_framing": "IS artifact translating private transaction traces into public/economic decision intelligence.",
                "lead_component": "EWS + theory",
                "what_to_emphasize": "Digital trace, decision support, public-value analytics, DSR rigor.",
                "risk": "Theory framing must be much stronger than a performance report.",
            },
        ]
    )
    return evidence_ledger, venue


def make_figures(
    levi_validity: pd.DataFrame,
    ews_eval: pd.DataFrame,
    ews_calibration_bins: pd.DataFrame,
    ews_cost_scenarios: pd.DataFrame,
) -> None:
    sns.set_theme(style="whitegrid")
    levi_plot = levi_validity[
        levi_validity["test_family"].isin(
            [
                "convergent_validity",
                "discriminant_check",
                "criterion_validity",
                "criterion_validity_robustness",
                "temporal_external_validity",
            ]
        )
    ].copy()
    levi_plot["short_claim"] = levi_plot["claim"].str.slice(0, 45)
    plt.figure(figsize=(10, 5.5))
    sns.barplot(data=levi_plot, y="short_claim", x="pearson", hue="test_family", dodge=False)
    plt.axvline(0, color="black", linewidth=0.8)
    plt.xlabel("Pearson correlation")
    plt.ylabel("")
    plt.title("LEVI and KCD External Validity Evidence")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "levi_academic_validity_evidence.png", dpi=220)
    plt.close()

    ews_plot = ews_eval[ews_eval["evaluation_dimension"].isin(["ranking_quality_decline", "ranking_quality_growth", "representation_value", "seasonality_robustness"])].copy()
    ews_plot["lift_or_value"] = ews_plot.apply(
        lambda r: r["metric_value"] / r["baseline"] if pd.notna(r["baseline"]) and r["evaluation_dimension"].startswith("ranking") else r["metric_value"],
        axis=1,
    )
    plt.figure(figsize=(9, 4.8))
    sns.barplot(data=ews_plot, y="evaluation_dimension", x="lift_or_value", color="#4C78A8")
    plt.xlabel("Metric value or AP lift")
    plt.ylabel("")
    plt.title("EWS Academic Evaluation Evidence")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "ews_academic_evaluation_evidence.png", dpi=220)
    plt.close()

    cal = ews_calibration_bins.copy()
    plt.figure(figsize=(8, 5))
    plt.plot(cal["risk_decile"], cal["mean_predicted_decline"], marker="o", label="Mean predicted risk")
    plt.plot(cal["risk_decile"], cal["observed_decline_rate"], marker="s", label="Observed decline rate")
    plt.xlabel("Risk decile")
    plt.ylabel("Decline probability")
    plt.title("EWS Decline Calibration by Risk Decile")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "ews_calibration_deciles.png", dpi=220)
    plt.close()

    plt.figure(figsize=(9, 5))
    sns.lineplot(
        data=ews_cost_scenarios,
        x="threshold",
        y="scenario_net_utility",
        hue="scenario",
        marker="o",
    )
    plt.axhline(0, color="black", linewidth=0.8)
    plt.xlabel("Decline threshold")
    plt.ylabel("Scenario net utility")
    plt.title("EWS Cost-Sensitivity Scenarios")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "ews_cost_sensitivity_scenarios.png", dpi=220)
    plt.close()


def write_docs(
    levi_validity: pd.DataFrame,
    levi_robustness: pd.DataFrame,
    ews_eval: pd.DataFrame,
    operating: pd.DataFrame,
    segments: pd.DataFrame,
    levi_leave_one_out: pd.DataFrame,
    ews_calibration_bins: pd.DataFrame,
    ews_cost_scenarios: pd.DataFrame,
    ledger: pd.DataFrame,
    venue: pd.DataFrame,
) -> None:
    top_levi = levi_validity.head(8)
    min_formula_corr = levi_robustness["pearson"].min()
    ews_primary = ews_eval[["evaluation_dimension", "claim", "evidence", "academic_use", "risk"]]
    loo_summary = (
        levi_leave_one_out.groupby("external_metric", observed=True)
        .agg(
            pearson_min=("pearson", "min"),
            pearson_median=("pearson", "median"),
            pearson_max=("pearson", "max"),
            spearman_min=("spearman", "min"),
            spearman_median=("spearman", "median"),
            spearman_max=("spearman", "max"),
        )
        .reset_index()
    )
    cost_best = ews_cost_scenarios[ews_cost_scenarios["is_best_in_scenario"]].copy()

    strategy = f"""# LEVI and EWS Academic Strategy

## Bottom Line

LEVI and EWS can be academically meaningful, but only if they are framed as
validated measurement and decision-support artifacts rather than as convenient
labels added after the main prediction work.

The recommended split is:

- **Thesis main line**: store-level lifecycle prediction with the new
  seasonality-corrected rolling-window check.
- **Paper extension**: LEVI + EWS as an evaluated decision-support package for
  local small-business vitality.

## LEVI: Make It a Construct-Validation Contribution

Weak claim:

> We created LEVI.

Academic claim:

> LEVI operationalizes local business vitality from micro transaction outcomes
> and is externally validated against independent urban-economic indicators.

Evidence currently available:

{top_levi[['test_family', 'evidence', 'academic_use', 'risk']].to_markdown(index=False)}

Formula robustness:

- Minimum pairwise Pearson correlation across the five LEVI formulas:
  **{min_formula_corr:.3f}**
- This supports the claim that the result is not dependent on one arbitrary
  index formula.

Leave-one-district-out sensitivity:

{loo_summary.to_markdown(index=False)}

Recommended wording:

> LEVI is not presented as a causal index. It is a district-level measurement
> artifact that aggregates store-level Growth and Decline outcomes and is
> validated against independent indicators of population change, closure
> pressure, and commercial activity.

## EWS: Make It a Decision-Support Artifact

Weak claim:

> The model predicts decline.

Academic claim:

> The EWS converts lifecycle prediction into calibrated, cost-sensitive
> intervention priorities under explicit trade-offs between false alarms and
> missed decline cases.

Evidence currently available:

{ews_primary.to_markdown(index=False)}

Selected operating points:

{operating[['threshold','decline_precision','decline_recall','decline_f1','flagged_pct','net_utility']].to_markdown(index=False)}

Calibration by risk decile:

{ews_calibration_bins.to_markdown(index=False)}

Best threshold by cost scenario:

{cost_best[['scenario','threshold','scenario_net_utility','decline_precision','decline_recall','flagged_pct','interpretation']].to_markdown(index=False)}

High-risk segment profile:

{segments.to_markdown(index=False)}

## How To Write This Academically

Use a Design Science / decision analytics structure:

1. Problem: small-business distress is hard to observe early with conventional
   public statistics.
2. Artifact: transaction-based EWS plus LEVI local-vitality monitor.
3. Evaluation: predictive ranking, calibration, threshold utility, subgroup
   profile, external validity, and seasonality robustness.
4. Boundary: this is not a causal policy-impact evaluation unless an actual
   intervention is observed.

## What Not To Claim

- Do not say LEVI proves population change causes store growth.
- Do not say EWS has been field deployed.
- Do not treat cost-sensitive utility as a real welfare estimate; it is a
  decision-scenario evaluation.
- Do not merge every analysis into the MSc thesis main line.
"""

    outline = """# LEVI/EWS Paper Outline

## Working Title

Transaction-Based Early Warning and Local Vitality Monitoring for Small
Businesses

## Research Questions

RQ1. Can early transaction traces identify stores at risk of later decline?

RQ2. Can a calibrated EWS translate these predictions into actionable
intervention priorities?

RQ3. Do aggregated lifecycle outcomes align with independent indicators of
local economic vitality?

## Contribution Structure

1. **Measurement contribution**: LEVI aggregates store-level lifecycle outcomes
   into a district-level local business vitality measure and validates it
   against external public data.
2. **Artifact contribution**: EWS converts predictive probabilities into
   calibrated, cost-sensitive risk scores and operating thresholds.
3. **Representation contribution**: hybrid trajectory states and change-point
   features improve lifecycle prediction over base features.
4. **Robustness contribution**: calendar-matched rolling windows address the
   seasonality concern raised in the 260430 meeting.

## Recommended Paper Boundary

Main paper:

- Data foundation
- Hybrid prediction
- EWS evaluation
- LEVI external validation
- Seasonality robustness

Appendix or future work:

- Full Cox/survival package
- Deep-learning baselines
- Extended causal Golden Cross triangulation
- Field deployment mock-up/API

## One-Paragraph Abstract Draft

Small businesses generate high-frequency digital traces, yet public monitoring
systems often observe local distress only after closures occur. We develop a
transaction-based decision-support artifact that predicts store-level
Growth/Stable/Decline outcomes and translates decline probabilities into a
calibrated early-warning score. The proposed hybrid representation combines
early transaction features with trajectory-state and change-point information,
improving predictive performance over base feature models. We further aggregate
store-level lifecycle outcomes into a Local Economic Vitality Index (LEVI) and
validate it against independent Seoul public indicators, including
living-population change and administrative closure rates. The results show how
private transaction traces can support both store-level risk prioritization and
district-level vitality monitoring, while calendar-matched rolling-window checks
address seasonality concerns in lifecycle prediction.
"""

    checklist = f"""# Next Analysis Checklist for LEVI/EWS Academic Submission

## Already Done

{ledger.to_markdown(index=False)}

## Still Worth Adding Before Submission

1. **LEVI leave-one-district-out sensitivity**
   - Completed in `levi_leave_one_district_out_sensitivity.csv`.
   - Summary is embedded in `260430_levi_ews_academic_strategy.md`.

2. **LEVI alternative formula table**
   - Already feasible from the five LEVI formulas.
   - Put V1-V5 external correlations in one table.

3. **EWS calibration bins**
   - Completed in `ews_calibration_deciles.csv`.

4. **EWS cost sensitivity**
   - Completed in `ews_cost_sensitivity_scenarios.csv`.

5. **EWS subgroup stability**
   - For major food-service categories, report AP or recall if available.
   - Current segment table shows risk-score distribution only.

6. **Seasonality connection**
   - Use `260430` rolling-window result as robustness, not as the main model.
   - State clearly that seasonal Macro-F1 is lower than full hybrid, but signal
     survives calendar matching.

## Venue Positioning

{venue.to_markdown(index=False)}
"""

    (DOC_DIR / "260430_levi_ews_academic_strategy.md").write_text(strategy, encoding="utf-8")
    (DOC_DIR / "260430_levi_ews_paper_outline.md").write_text(outline, encoding="utf-8")
    (DOC_DIR / "260430_levi_ews_next_analysis_checklist.md").write_text(checklist, encoding="utf-8")


def main() -> None:
    for path in [TABLE_DIR, FIG_DIR, DOC_DIR]:
        path.mkdir(parents=True, exist_ok=True)

    inputs = load_inputs()
    levi_validity, levi_robustness = build_levi_tables(inputs)
    levi_leave_one_out = build_levi_leave_one_out(inputs)
    ews_eval, operating, segments = build_ews_tables(inputs)
    ews_calibration_bins = build_ews_calibration_bins(inputs)
    ews_cost_scenarios = build_ews_cost_scenarios(inputs)
    ledger, venue = build_framing_tables()

    levi_validity.to_csv(TABLE_DIR / "levi_academic_validity_summary.csv", index=False, encoding="utf-8-sig")
    levi_robustness.to_csv(TABLE_DIR / "levi_formula_robustness.csv", index=False, encoding="utf-8-sig")
    ews_eval.to_csv(TABLE_DIR / "ews_academic_evaluation_summary.csv", index=False, encoding="utf-8-sig")
    operating.to_csv(TABLE_DIR / "ews_selected_operating_points.csv", index=False, encoding="utf-8-sig")
    segments.to_csv(TABLE_DIR / "ews_high_risk_segments.csv", index=False, encoding="utf-8-sig")
    levi_leave_one_out.to_csv(
        TABLE_DIR / "levi_leave_one_district_out_sensitivity.csv", index=False, encoding="utf-8-sig"
    )
    ews_calibration_bins.to_csv(TABLE_DIR / "ews_calibration_deciles.csv", index=False, encoding="utf-8-sig")
    ews_cost_scenarios.to_csv(TABLE_DIR / "ews_cost_sensitivity_scenarios.csv", index=False, encoding="utf-8-sig")
    ledger.to_csv(TABLE_DIR / "levi_ews_evidence_ledger.csv", index=False, encoding="utf-8-sig")
    venue.to_csv(TABLE_DIR / "levi_ews_venue_positioning.csv", index=False, encoding="utf-8-sig")

    summary = {
        "levi_validity_rows": len(levi_validity),
        "levi_min_formula_corr": float(levi_robustness["pearson"].min()),
        "ews_evaluation_rows": len(ews_eval),
        "ews_calibration_bins": len(ews_calibration_bins),
        "best_ews_threshold": float(operating.sort_values("net_utility", ascending=False).iloc[0]["threshold"]),
        "cost_scenarios": int(ews_cost_scenarios["scenario"].nunique()),
        "venue_count": len(venue),
    }
    (TABLE_DIR / "levi_ews_academic_package_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    make_figures(levi_validity, ews_eval, ews_calibration_bins, ews_cost_scenarios)
    write_docs(
        levi_validity,
        levi_robustness,
        ews_eval,
        operating,
        segments,
        levi_leave_one_out,
        ews_calibration_bins,
        ews_cost_scenarios,
        ledger,
        venue,
    )

    print("[260430] LEVI/EWS academic package complete")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
