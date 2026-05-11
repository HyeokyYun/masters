"""Generate summary figures from the 9-phase results.

Outputs (260430_claude/outputs/figures/):
  - phase0_label_sweep.png        — macro_F1 by k_sigma + class balance
  - phase1_seq_models.png         — RF vs sequence models bar
  - phase1_ts_benchmark.png       — TS regression model F1 + MAE
  - phase2_meta_delta.png         — A vs A+meta paired delta
  - phase2_cluster_outcome.png    — cluster × G/S/D heatmap (one panel)
  - phase3_gnn_delta.png          — GCN-MLP delta by graph type
  - phase4_dynamics_summary.png   — final summary bar (RF, RF+meta, GNN best)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg  # noqa: E402

plt.rcParams.update(cfg.FIG_STYLE)
FIG = cfg.FIGURE_DIR
TBL = cfg.TABLE_DIR


def fig_phase0() -> None:
    p = TBL / "label_definition_sweep.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    agg = d.groupby("k_sigma").agg(
        macro_f1=("macro_f1_mean", "mean"),
        growth=("growth_ratio", "mean"),
        stable=("stable_ratio", "mean"),
        decline=("decline_ratio", "mean"),
        reg_bucket=("reg_then_bucket_macro_f1", "mean"),
    ).reset_index()

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    ax = axes[0]
    ax.plot(agg["k_sigma"], agg["macro_f1"], "o-", label="classification F1", color="tab:blue")
    ax.plot(agg["k_sigma"], agg["reg_bucket"], "s--", label="reg→bucket F1", color="tab:gray")
    ax.set_xlabel("k_sigma threshold")
    ax.set_ylabel("mean macro_F1 (8 panels)")
    ax.set_title("Phase 0 — Label threshold sweep")
    ax.legend()
    ax.grid(alpha=0.3)

    ax = axes[1]
    bottom = np.zeros(len(agg))
    for c, color in [("decline", "tab:red"), ("stable", "tab:gray"), ("growth", "tab:green")]:
        ax.bar(agg["k_sigma"].astype(str), agg[c], bottom=bottom, label=c, color=color)
        bottom += agg[c].values
    ax.set_xlabel("k_sigma")
    ax.set_ylabel("class ratio")
    ax.set_title("Class balance by threshold")
    ax.legend()
    fig.tight_layout()
    out = FIG / "phase0_label_sweep.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"[fig] saved {out}")


def fig_phase1_seq() -> None:
    p = TBL / "seq_model_compare.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    agg = d.groupby("model")["macro_f1_mean"].agg(["mean", "std"]).reset_index()
    order = ["rf_tabular", "tcn", "flat_mlp", "lstm", "gru", "transformer"]
    agg = agg.set_index("model").reindex(order).reset_index()

    fig, ax = plt.subplots(figsize=(8, 4.5))
    colors = ["tab:green" if m == "rf_tabular" else "tab:gray" for m in agg["model"]]
    bars = ax.bar(agg["model"], agg["mean"], yerr=agg["std"], color=colors, capsize=4)
    for b, v in zip(bars, agg["mean"]):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.005, f"{v:.3f}",
                 ha="center", fontsize=9)
    ax.set_ylabel("macro_F1 (mean of 6 panels ± std)")
    ax.set_title("Phase 1.1 — Sequence-to-class vs tabular RF")
    ax.set_ylim(0.35, 0.55)
    ax.grid(axis="y", alpha=0.3)
    plt.setp(ax.get_xticklabels(), rotation=15, ha="right")
    fig.tight_layout()
    out = FIG / "phase1_seq_models.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"[fig] saved {out}")


def fig_phase1_ts() -> None:
    p = TBL / "ts_benchmark_compare.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    agg = d.groupby("model").agg(F1=("macro_f1", "mean"), MAE=("mae", "mean")).reset_index()
    order = ["naive_last_slope", "linear_extrap", "mlp_flat", "lstm_reg"]
    agg = agg.set_index("model").reindex(order).reset_index()

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    ax = axes[0]
    ax.bar(agg["model"], agg["F1"], color="tab:gray")
    ax.axhline(0.49, ls="--", color="tab:green", label="RF tabular ≈ 0.49")
    ax.set_ylabel("macro_F1")
    ax.set_title("TS regression → bucket")
    ax.legend()
    plt.setp(ax.get_xticklabels(), rotation=15, ha="right")

    ax = axes[1]
    ax.bar(agg["model"], agg["MAE"], color="tab:purple")
    ax.set_ylabel("MAE on slope_target_norm")
    ax.set_title("Slope regression error")
    plt.setp(ax.get_xticklabels(), rotation=15, ha="right")
    fig.tight_layout()
    out = FIG / "phase1_ts_benchmark.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"[fig] saved {out}")


def fig_phase2_meta() -> None:
    p1 = TBL / "main_model_compare_meta.csv"
    p2 = TBL / "main_model_paired_AvAmeta.csv"
    if not (p1.exists() and p2.exists()):
        return
    d = pd.read_csv(p1)
    paired = pd.read_csv(p2)
    piv = d.pivot_table(index="combo_id", columns="label", values="macro_f1_mean")
    piv = piv[["A_baseline", "A_plus_meta"]]
    piv["delta"] = piv["A_plus_meta"] - piv["A_baseline"]
    piv = piv.merge(paired[["combo_id", "p_value"]], left_index=True, right_on="combo_id")

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    ax = axes[0]
    x = np.arange(len(piv))
    ax.bar(x - 0.2, piv["A_baseline"], width=0.4, label="A_baseline", color="tab:gray")
    ax.bar(x + 0.2, piv["A_plus_meta"], width=0.4, label="A + meta", color="tab:blue")
    ax.set_xticks(x)
    ax.set_xticklabels(piv["combo_id"], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("macro_F1")
    ax.set_title("Phase 2.2 — Meta features vs baseline")
    ax.legend()
    ax.set_ylim(0.40, 0.58)

    ax = axes[1]
    colors = ["tab:green" if pv < 0.05 else "tab:gray" for pv in piv["p_value"]]
    ax.bar(piv["combo_id"], piv["delta"], color=colors)
    ax.axhline(0, color="black", lw=0.6)
    ax.axhline(piv["delta"].mean(), color="tab:blue", ls="--",
                label=f"mean Δ = +{piv['delta'].mean():.4f}")
    ax.set_ylabel("Δ macro_F1 (A+meta - A)")
    ax.set_title("Per-panel uplift; green = p<0.05")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8)
    ax.legend()
    fig.tight_layout()
    out = FIG / "phase2_meta_delta.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"[fig] saved {out}")


def fig_phase2_cluster() -> None:
    p = TBL / "cluster_outcome_xtab.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    panels = d["combo_id"].unique()[:6]
    fig, axes = plt.subplots(2, 3, figsize=(13, 6.5), sharey=True)
    axes = axes.ravel()
    for i, c_id in enumerate(panels):
        sub = d[d["combo_id"] == c_id].sort_values("km_cluster")
        ax = axes[i]
        x = sub["km_cluster"].astype(str)
        ax.bar(x, sub["ratio_Decline"], color="tab:red", label="Decline")
        ax.bar(x, sub["ratio_Stable"], bottom=sub["ratio_Decline"],
                color="tab:gray", label="Stable")
        ax.bar(x, sub["ratio_Growth"], bottom=sub["ratio_Decline"] + sub["ratio_Stable"],
                color="tab:green", label="Growth")
        ax.set_title(c_id, fontsize=8)
        if i == 0:
            ax.legend(fontsize=7, loc="upper right")
        ax.set_ylim(0, 1)
    fig.suptitle("Phase 2.3 — Cluster × G/S/D heterogeneity", y=1.02)
    fig.tight_layout()
    out = FIG / "phase2_cluster_outcome.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"[fig] saved {out}")


def fig_phase3_gnn() -> None:
    p = TBL / "gnn_compare.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    rows = []
    for g in d["graph"].unique():
        if g == "none":
            continue
        sub = d[d["graph"] == g]
        pi = sub.pivot_table(index="combo_id", columns="model", values="macro_f1_mean")
        if "gcn" not in pi or "mlp" not in pi:
            continue
        for c_id in pi.index:
            rows.append({
                "graph": g, "combo_id": c_id,
                "delta": pi.loc[c_id, "gcn"] - pi.loc[c_id, "mlp"],
            })
    if not rows:
        return
    df = pd.DataFrame(rows)
    agg = df.groupby("graph")["delta"].agg(["mean", "std"]).reset_index()
    order = ["dong", "industry", "hybrid_dong_industry"]
    agg = agg.set_index("graph").reindex(order).reset_index()

    fig, ax = plt.subplots(figsize=(7, 4))
    colors = ["tab:red" if v < 0 else "tab:green" for v in agg["mean"]]
    ax.bar(agg["graph"], agg["mean"], yerr=agg["std"], color=colors, capsize=4)
    ax.axhline(0, color="black", lw=0.6)
    for i, v in enumerate(agg["mean"]):
        ax.text(i, v - 0.005, f"{v:+.3f}", ha="center", fontsize=9)
    ax.set_ylabel("Δ macro_F1 (GCN - MLP, same node features)")
    ax.set_title("Phase 3 — GNN spillover effect by graph type")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    out = FIG / "phase3_gnn_delta.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"[fig] saved {out}")


def fig_phase4_summary() -> None:
    """Final summary bar: RF, RF+meta, TCN, GCN(hybrid), Naive — all on macro_F1."""
    bars = []
    seq = TBL / "seq_model_compare.csv"
    meta = TBL / "main_model_compare_meta.csv"
    ts = TBL / "ts_benchmark_compare.csv"
    gnn = TBL / "gnn_compare.csv"
    if seq.exists():
        d = pd.read_csv(seq)
        bars.append(("RF tabular", d[d["model"] == "rf_tabular"]["macro_f1_mean"].mean()))
        bars.append(("TCN seq", d[d["model"] == "tcn"]["macro_f1_mean"].mean()))
        bars.append(("LSTM seq", d[d["model"] == "lstm"]["macro_f1_mean"].mean()))
    if meta.exists():
        d = pd.read_csv(meta)
        bars.append(("RF + meta", d[d["label"] == "A_plus_meta"]["macro_f1_mean"].mean()))
    if ts.exists():
        d = pd.read_csv(ts)
        bars.append(("TS reg→bucket (best)", d.groupby("model")["macro_f1"].mean().max()))
    if gnn.exists():
        d = pd.read_csv(gnn)
        sub = d[(d["graph"] == "hybrid_dong_industry") & (d["model"] == "gcn")]
        if not sub.empty:
            bars.append(("GCN hybrid", sub["macro_f1_mean"].mean()))

    if not bars:
        return
    names, vals = zip(*bars)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    colors = ["tab:green" if v == max(vals) else "tab:gray" for v in vals]
    bars_ = ax.bar(names, vals, color=colors)
    for b, v in zip(bars_, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.005, f"{v:.3f}",
                 ha="center", fontsize=9)
    ax.set_ylabel("macro_F1 (panel mean)")
    ax.set_title("9-phase summary — macro_F1 across approaches")
    ax.set_ylim(0.30, 0.55)
    ax.grid(axis="y", alpha=0.3)
    plt.setp(ax.get_xticklabels(), rotation=15, ha="right")
    fig.tight_layout()
    out = FIG / "phase4_dynamics_summary.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"[fig] saved {out}")


def main() -> None:
    fig_phase0()
    fig_phase1_seq()
    fig_phase1_ts()
    fig_phase2_meta()
    fig_phase2_cluster()
    fig_phase3_gnn()
    fig_phase4_summary()


if __name__ == "__main__":
    main()
