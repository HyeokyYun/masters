"""260514/ 미팅용 그림 4 장 생성 스크립트.

fig01: prediction-first 3 contribution 다이어그램
fig02: 시즌 진폭 (시작월 × macro-F1 box) + 진폭 비교
fig03: improvement ladder (외부 SOTA + LightGBM + hybrid + cost-sensitive)
fig04: cohort × ΔF1, cluster × ΔF1 좌우 패널

실행: python /home/hyeoky98/kcd/260514/src/make_figures.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path("/home/hyeoky98/kcd")
OUT_DIR = ROOT / "260514" / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEASONAL_CSV = ROOT / "260430_claude" / "outputs" / "tables" / "seasonal_results_summary.csv"
PHASE5_CSV = ROOT / "260511" / "phase5_external" / "outputs" / "tables" / "phase5_summary.csv"
COHORT_CSV = ROOT / "260511" / "phase5_external" / "outputs" / "tables" / "lgbm_per_cohort_summary.csv"
PAIRED_CSV = ROOT / "260430_claude" / "outputs" / "tables" / "main_model_paired_AvD.csv"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.unicode_minus": False,
    "font.size": 10,
    "figure.dpi": 110,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
})


def make_fig01_three_contributions() -> Path:
    fig, ax = plt.subplots(figsize=(13, 7))
    ax.axis("off")
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 7)

    ax.text(6.5, 6.6, "Upper RQ: How well can early card-transaction patterns predict G/S/D,",
            ha="center", fontsize=13, fontweight="bold")
    ax.text(6.5, 6.15, "and which factors / representations / models improve that prediction?",
            ha="center", fontsize=13, fontweight="bold")
    ax.annotate("", xy=(6.5, 5.4), xytext=(6.5, 5.95),
                arrowprops=dict(arrowstyle="->", lw=2))

    boxes = [
        (0.4, "C1. Prediction baseline\n  & factor decomposition",
         ["Baseline macro-F1: 0.43-0.55", "Q4_long LGB ΔF1: +0.019",
          "Fragile cluster ΔF1: +0.044", "(§5.7-§5.8)"]),
        (4.7, "C2. Seasonal alignment\n  label robustness",
         ["Start-month amplitude: 0.10", "Window length:    0.02-0.04",
          "Start year:            <0.01", "(§5.2-§5.4)"]),
        (9.0, "C3. Three improvement\n  attempts + SMB diff.",
         ["Hybrid ΔF1: +0.0017 (1/14 sig)", "Cost-sens.: RF -0.035 to -0.063",
          "SOTA: 1/14 only LGB wins", "(§5.5, §5.9, §5.6)"]),
    ]
    for x, title, lines in boxes:
        box = mpatches.FancyBboxPatch((x, 0.6), 3.6, 4.4,
                                       boxstyle="round,pad=0.05,rounding_size=0.15",
                                       linewidth=1.5, edgecolor="#1f4f7a",
                                       facecolor="#e6f0fa")
        ax.add_patch(box)
        ax.text(x + 1.8, 4.5, title, ha="center", fontsize=11.5,
                fontweight="bold", color="#1f4f7a")
        for i, ln in enumerate(lines):
            ax.text(x + 0.2, 3.6 - i * 0.55, ln, ha="left", fontsize=10)

    ax.text(6.5, 0.2,
            "Future work (§6.5, §7.2): LEVI, EWS, GNN expansion, Golden-cross "
            "causal check, external public data",
            ha="center", fontsize=9, color="#666666", style="italic")

    out = OUT_DIR / "fig01_three_contributions.png"
    fig.suptitle("Final thesis — Three contributions under prediction-first framing",
                 fontsize=14, y=0.98)
    fig.savefig(out)
    plt.close(fig)
    print(f"[fig01] {out}")
    return out


def make_fig02_seasonal_amplitude() -> Path:
    df = pd.read_csv(SEASONAL_CSV)
    df = df[(df["model"] == "rf") & (df["target_offset"] == 1)]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6),
                                    gridspec_kw={"width_ratios": [2.6, 1]})

    # Left: macro_f1 by start_month, box plots
    months = sorted(df["start_month"].unique())
    data_by_month = [df[df["start_month"] == m]["macro_f1_mean"].values for m in months]
    bp = ax1.boxplot(data_by_month, positions=months, widths=0.6, patch_artist=True,
                     boxprops=dict(facecolor="#cfe2f3", edgecolor="#1f4f7a"),
                     medianprops=dict(color="#1f4f7a", linewidth=1.5),
                     whiskerprops=dict(color="#1f4f7a"),
                     capprops=dict(color="#1f4f7a"),
                     flierprops=dict(marker="o", markersize=3, markerfacecolor="#888"))
    ax1.set_xticks(months)
    ax1.set_xticklabels(months)
    ax1.set_xlabel("Start month (feature window start)")
    ax1.set_ylabel("macro-F1 (RF baseline, 145 specifications)")
    ax1.set_title("Seasonal amplitude in macro-F1 by start month")
    ax1.grid(axis="y", linestyle=":", alpha=0.6)

    # annotate amplitude
    overall_min = df["macro_f1_mean"].min()
    overall_max = df["macro_f1_mean"].max()
    ax1.axhline(overall_max, ls="--", color="#c0392b", lw=0.8)
    ax1.axhline(overall_min, ls="--", color="#c0392b", lw=0.8)
    ax1.text(12.4, (overall_min + overall_max) / 2,
             f"Δ = {overall_max - overall_min:.2f}",
             color="#c0392b", fontsize=11, fontweight="bold")

    # Right: amplitude comparison bar
    factor_names = ["Start month\n(amplitude)", "Window length\n(1m → 7m)",
                    "Start year\n(2021 vs 2022)"]
    factor_amps = [overall_max - overall_min, 0.04, 0.01]
    colors = ["#c0392b", "#e67e22", "#27ae60"]
    bars = ax2.bar(factor_names, factor_amps, color=colors, edgecolor="black", lw=0.6)
    ax2.set_ylabel("macro-F1 amplitude")
    ax2.set_title("Variation source magnitude")
    ax2.grid(axis="y", linestyle=":", alpha=0.6)
    for b, v in zip(bars, factor_amps):
        ax2.text(b.get_x() + b.get_width() / 2, v + 0.005,
                 f"{v:.2f}", ha="center", fontsize=10, fontweight="bold")
    ax2.set_ylim(0, max(factor_amps) * 1.25)

    fig.suptitle("Fig 2 — Seasonal alignment baseline: label timing dominates (Contribution 2)",
                 fontsize=13, y=1.02)
    out = OUT_DIR / "fig02_seasonal_amplitude.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"[fig02] {out}")
    return out


def make_fig03_improvement_ladder() -> Path:
    p5 = pd.read_csv(PHASE5_CSV)
    # phase5_summary has multiple workstreams; pick rows where mean_delta_vs_rf is not NaN
    p5 = p5.dropna(subset=["mean_delta_vs_rf"]).copy()
    # remove duplicate rf_tabular entries
    p5 = p5[p5["model"] != "rf_tabular"]
    # Drop duplicates by model name keeping the first
    p5 = p5.sort_values("mean_delta_vs_rf", ascending=True).drop_duplicates("model", keep="first")

    # Add hybrid representation row from paired CSV (14 panel mean)
    paired = pd.read_csv(PAIRED_CSV)
    hybrid_delta = paired["delta_mean"].mean()
    extra = pd.DataFrame([{
        "workstream": "thesis_hybrid",
        "model": "hybrid (cluster+CP)",
        "mean_delta_vs_rf": hybrid_delta,
        "n_sig_p05": int((paired["p_value"] < 0.05).sum()),
        "wins_vs_rf": int((paired["delta_mean"] > 0).sum()),
        "n_panels": len(paired),
    }])
    p5 = pd.concat([p5, extra], ignore_index=True)
    p5 = p5.sort_values("mean_delta_vs_rf", ascending=True)

    fig, ax = plt.subplots(figsize=(12, 7))
    colors = []
    for _, r in p5.iterrows():
        m = r["model"]
        if "lgbm" in m or m == "hybrid (cluster+CP)":
            colors.append("#27ae60" if r["mean_delta_vs_rf"] > 0 else "#888")
        else:
            colors.append("#c0392b")
    ypos = np.arange(len(p5))
    bars = ax.barh(ypos, p5["mean_delta_vs_rf"], color=colors, edgecolor="black", lw=0.5)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_yticks(ypos)
    ax.set_yticklabels(p5["model"])
    ax.set_xlabel("Mean ΔmacroF1 vs RF baseline (positive = beats RF)")
    ax.set_title("Fig 3 — Three improvement attempts x 14 external models: only LightGBM family wins\n"
                 "(green = LightGBM family or hybrid, red = stock-prediction SOTA / attention / cost-sensitive)")
    ax.grid(axis="x", linestyle=":", alpha=0.6)
    for b, v, n_sig, wins in zip(bars, p5["mean_delta_vs_rf"], p5["n_sig_p05"], p5["wins_vs_rf"]):
        label = f" Δ={v:+.3f}, sig {int(n_sig)}/6, wins {int(wins)}/6"
        offset = 0.005 if v >= 0 else -0.005
        ha = "left" if v >= 0 else "right"
        ax.text(v + offset, b.get_y() + b.get_height() / 2,
                label, va="center", ha=ha, fontsize=9)

    out = OUT_DIR / "fig03_three_improvement_ladder.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"[fig03] {out}")
    return out


def make_fig04_cohort_cluster_lift() -> Path:
    df = pd.read_csv(COHORT_CSV)
    tenure = df[df["cohort_kind"] == "tenure_q"].sort_values("cohort")
    cluster = df[df["cohort_kind"] == "cluster"].sort_values("cohort")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6))

    # Left: tenure
    t_labels = tenure["cohort"].tolist()
    t_delta = tenure["mean_delta"].tolist()
    bars1 = ax1.bar(t_labels, t_delta,
                    color=["#a6c8e1", "#7eb0d3", "#5499c5", "#1f6dab"],
                    edgecolor="black", lw=0.6)
    ax1.set_ylabel("Mean ΔmacroF1 (LightGBM − RF)")
    ax1.set_title("(a) Tenure cohort × LGB lift\nQ4_long ≈ 2.5× of overall average")
    ax1.axhline(0, color="black", lw=0.6)
    ax1.axhline(0.0075, ls="--", color="#888", lw=0.8, label="overall mean +0.0075")
    ax1.grid(axis="y", linestyle=":", alpha=0.6)
    ax1.legend(loc="upper left", fontsize=9)
    for b, v in zip(bars1, t_delta):
        ax1.text(b.get_x() + b.get_width() / 2,
                 v + (0.001 if v >= 0 else -0.001),
                 f"{v:+.4f}", ha="center", va="bottom" if v >= 0 else "top",
                 fontsize=10)
    # mark Q4_long star
    ax1.annotate("★", xy=(3, t_delta[-1]), xytext=(3, t_delta[-1] + 0.0035),
                 ha="center", fontsize=18, color="#c0392b")

    # Right: cluster
    c_labels = [c.replace("cluster_", "C") for c in cluster["cohort"]]
    c_delta = cluster["mean_delta"].tolist()
    c_dec = cluster["mean_decline_rate"].tolist()
    fragile_idx = int(np.argmax(c_dec))  # cluster with highest decline rate
    colors2 = ["#1f6dab" if i != fragile_idx else "#c0392b" for i in range(len(c_labels))]
    bars2 = ax2.bar(c_labels, c_delta, color=colors2, edgecolor="black", lw=0.6)
    ax2.set_ylabel("Mean ΔmacroF1 (LightGBM − RF)")
    ax2.set_title("(b) KMeans cluster × LGB lift\nfragile cluster (red) ≈ 5.9× of overall")
    ax2.axhline(0, color="black", lw=0.6)
    ax2.axhline(0.0075, ls="--", color="#888", lw=0.8, label="overall mean +0.0075")
    ax2.grid(axis="y", linestyle=":", alpha=0.6)
    ax2.legend(loc="upper left", fontsize=9)
    for b, v, dr in zip(bars2, c_delta, c_dec):
        ax2.text(b.get_x() + b.get_width() / 2,
                 v + (0.001 if v >= 0 else -0.001),
                 f"{v:+.3f}\n(D={dr:.2f})",
                 ha="center", va="bottom" if v >= 0 else "top", fontsize=8.5)
    ax2.annotate("★ fragile", xy=(fragile_idx, c_delta[fragile_idx]),
                 xytext=(fragile_idx, c_delta[fragile_idx] + 0.008),
                 ha="center", fontsize=11, color="#c0392b", fontweight="bold")

    fig.suptitle("Fig 4 — Prediction improvement concentrates on Q4_long tenure and fragile cluster (Contribution 1)",
                 fontsize=13, y=1.02)
    out = OUT_DIR / "fig04_cohort_cluster_lift.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"[fig04] {out}")
    return out


def main():
    make_fig01_three_contributions()
    make_fig02_seasonal_amplitude()
    make_fig03_improvement_ladder()
    make_fig04_cohort_cluster_lift()
    print(f"[done] 4 figures saved to {OUT_DIR}")


if __name__ == "__main__":
    main()
