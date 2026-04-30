"""Step 08 — Publication-quality figures for the paper.

상위 단계의 결과물을 읽어 논문용 그림(Fig 1-8)을 생성한다.
이미 개별 step에서 그려진 그림은 여기서 보강/재정렬한다.

Output: outputs/figures/fig*.png (각 300 DPI)
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg  # noqa: E402

plt.rcParams.update(cfg.FIG_STYLE)


def fig2_km_outcome():
    path = cfg.TABLE_DIR / "km_by_outcome.csv"
    if not path.exists():
        return
    df = pd.read_csv(path)
    fig, ax = plt.subplots(figsize=(8, 5))
    for col in df.columns:
        if col.startswith("S_"):
            ax.step(df["timeline_weeks"], df[col], where="post", label=col.replace("S_", ""))
    ax.set_xlabel("Weeks since open")
    ax.set_ylabel("Survival probability S(t)")
    ax.set_title("Figure 2. Kaplan-Meier Survival by Outcome")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.02)
    ax.legend()
    fig.savefig(cfg.FIGURE_DIR / "fig2_km_outcome.png")
    plt.close()


def fig3_clustering_metrics():
    path = cfg.TABLE_DIR / "clustering_comparison.csv"
    if not path.exists():
        return
    df = pd.read_csv(path)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for m, ax, title in zip(
        ["silhouette", "davies_bouldin", "calinski_harabasz"],
        axes,
        ["Silhouette (↑)", "Davies-Bouldin (↓)", "Calinski-Harabasz (↑)"],
    ):
        for method in df["method"].unique():
            sub = df[df["method"] == method].sort_values("K")
            ax.plot(sub["K"], sub[m], "o-", label=method)
        ax.set_title(title)
        ax.set_xlabel("K")
        ax.grid(True, alpha=0.3)
        ax.legend()
    fig.suptitle("Figure 3. Clustering Quality: K-Means vs GMM vs K-Shape")
    fig.tight_layout()
    fig.savefig(cfg.FIGURE_DIR / "fig3_clustering_metrics.png")
    plt.close()


def fig6_prediction_performance():
    path = cfg.TABLE_DIR / "prediction_cv_folds.csv"
    if not path.exists():
        return
    df = pd.read_csv(path)
    agg = df.groupby("model").agg(
        macro_f1_mean=("macro_f1", "mean"),
        macro_f1_std=("macro_f1", "std"),
        recall_growth=("recall_Growth", "mean"),
        recall_decline=("recall_Decline", "mean"),
        auc=("auc_ovr", "mean"),
    ).reset_index()
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(agg))
    w = 0.2
    ax.bar(x - 1.5 * w, agg["macro_f1_mean"], w, yerr=agg["macro_f1_std"], label="Macro-F1", capsize=3)
    ax.bar(x - 0.5 * w, agg["recall_growth"], w, label="Recall (Growth)")
    ax.bar(x + 0.5 * w, agg["recall_decline"], w, label="Recall (Decline)")
    ax.bar(x + 1.5 * w, agg["auc"], w, label="AUC (OvR)")
    ax.set_xticks(x)
    ax.set_xticklabels(agg["model"])
    ax.set_ylabel("Score")
    ax.set_title("Figure 6. 30-week Early Prediction Performance (5-fold CV)")
    ax.legend(loc="lower right")
    ax.grid(True, axis="y", alpha=0.3)
    fig.savefig(cfg.FIGURE_DIR / "fig6_prediction_performance.png")
    plt.close()


def fig5_causal_result():
    did_path = cfg.TABLE_DIR / "did_psm_ate.csv"
    fe_path = cfg.TABLE_DIR / "fe_panel_regression.csv"
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    if did_path.exists():
        did = pd.read_csv(did_path)
        ax = axes[0]
        ax.bar(["ATT"], did["ATT"], color="#2a7ab0")
        ax.errorbar(["ATT"], did["ATT"], yerr=1.96 * did["ATT"].abs() / np.maximum(did["t_stat"].abs(), 1e-6),
                   fmt="none", color="black", capsize=6)
        ax.set_title(f"DiD (PSM) ATT = {did['ATT'].iloc[0]:+.3f}\np = {did['p_value'].iloc[0]:.3g}")
        ax.set_ylabel("Δ log-sales (treated − control)")
        ax.axhline(0, color="gray", lw=0.8)
        ax.grid(True, axis="y", alpha=0.3)

    if fe_path.exists():
        fe = pd.read_csv(fe_path, index_col=0)
        ax = axes[1]
        coefs = fe[fe.index.str.startswith("nc_")]
        ax.errorbar(coefs.index, coefs["coef"],
                   yerr=[coefs["coef"] - coefs["ci_lower"], coefs["ci_upper"] - coefs["coef"]],
                   fmt="o", capsize=4)
        ax.axhline(0, color="gray", lw=0.8)
        ax.set_title("Two-way FE panel regression\n(lagged nc_ratio → log-sales)")
        ax.set_ylabel("Coefficient (± 95% CI)")
        ax.grid(True, alpha=0.3)

    fig.suptitle("Figure 5. Causal Evidence for Golden Cross Effect")
    fig.tight_layout()
    fig.savefig(cfg.FIGURE_DIR / "fig5_causal.png")
    plt.close()


def fig8_robustness():
    paths = {
        "Category": cfg.TABLE_DIR / "robustness_subgroup_category.csv",
        "Open year": cfg.TABLE_DIR / "robustness_subgroup_year.csv",
    }
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for i, (name, path) in enumerate(paths.items()):
        if not path.exists():
            continue
        df = pd.read_csv(path)
        axes[i].barh(df["subgroup"], df["macro_f1"], color="#4c72b0")
        axes[i].set_title(f"{name} — Macro-F1")
        axes[i].grid(True, axis="x", alpha=0.3)
    fig.suptitle("Figure 8. Robustness Check — Subgroup Performance")
    fig.tight_layout()
    fig.savefig(cfg.FIGURE_DIR / "fig8_robustness.png")
    plt.close()


def fig7_shap():
    path = cfg.TABLE_DIR / "shap_feature_importance_by_class.csv"
    if not path.exists():
        return
    df = pd.read_csv(path)
    top15 = df.groupby("feature")["mean_abs_shap"].sum().nlargest(15).index.tolist()
    pivot = df[df["feature"].isin(top15)].pivot(index="feature", columns="class", values="mean_abs_shap").reindex(top15)
    fig, ax = plt.subplots(figsize=(9, 6))
    pivot.plot(kind="barh", ax=ax)
    ax.invert_yaxis()
    ax.set_xlabel("Mean |SHAP value|")
    ax.set_title("Figure 7. Top-15 Features (SHAP by outcome class)")
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(cfg.FIGURE_DIR / "fig7_shap.png")
    plt.close()


def table1_descriptive():
    df = pd.read_parquet(cfg.TABLE_DIR / "unified_store_table.parquet")
    rows = [{
        "Statistic": "Total stores", "Value": len(df),
    }, {
        "Statistic": "Closed stores", "Value": int(df["is_closed"].sum()),
    }, {
        "Statistic": "Panel stores (≥52 obs weeks)", "Value": int(df["in_panel"].sum()),
    }, {
        "Statistic": "Median survival (weeks, all)", "Value": float(df["survival_weeks"].median()),
    }, {
        "Statistic": "Median survival (closed)",
        "Value": float(df.loc[df["is_closed"] == 1, "survival_weeks"].median()),
    }, {
        "Statistic": "Median survival (survived)",
        "Value": float(df.loc[df["is_closed"] == 0, "survival_weeks"].median()),
    }]
    for c in ["Growth", "Stable", "Decline"]:
        rows.append({"Statistic": f"Outcome={c}",
                    "Value": int((df["outcome_3"] == c).sum())})
    pd.DataFrame(rows).to_csv(cfg.TABLE_DIR / "table1_descriptive.csv", index=False, encoding="utf-8-sig")


def main():
    fig2_km_outcome()
    fig3_clustering_metrics()
    fig5_causal_result()
    fig6_prediction_performance()
    fig7_shap()
    fig8_robustness()
    table1_descriptive()
    print("[08] figures/tables generated")


if __name__ == "__main__":
    main()
