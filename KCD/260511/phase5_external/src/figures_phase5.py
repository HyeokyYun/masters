"""Phase 5 figures.

  - phase5_macro_f1_bars.png : 모델별 평균 macro_F1 막대
  - phase5_delta_vs_rf.png   : 모델별 Δ vs RF (paired) 막대 + p<0.05 표시
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common.paths import PHASE5_FIGURE_DIR, PHASE5_TABLE_DIR  # noqa: E402

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.unicode_minus": False,
    "font.size": 10,
})


def _color_for(ws: str) -> str:
    return {
        "5A_foundation": "#d6604d",
        "5B_neuralforecast": "#f4a582",
        "5C_attention": "#92c5de",
        "5D_weighting": "#4393c3",
    }.get(ws, "#888888")


def main():
    sp = PHASE5_TABLE_DIR / "phase5_summary.csv"
    if not sp.exists():
        print(f"missing {sp}; run analysis_paired_phase5.py first")
        return
    summary = pd.read_csv(sp)
    if summary.empty:
        print("empty summary")
        return

    # bar 1: mean F1
    s = summary.sort_values("mean_f1", ascending=True).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(8, max(3, len(s) * 0.35)))
    colors = [_color_for(w) for w in s["workstream"]]
    ax.barh(s["model"], s["mean_f1"], color=colors, edgecolor="black", linewidth=0.5)
    # baseline reference
    rf_rows = s[s["model"] == "rf_tabular"]
    if not rf_rows.empty:
        rf = float(rf_rows["mean_f1"].mean())
        ax.axvline(rf, color="red", linestyle="--", linewidth=1.0, label=f"RF baseline ({rf:.3f})")
        ax.legend(loc="lower right")
    ax.set_xlabel("Mean macro F1 across panels")
    ax.set_title("Phase 5 — macro F1 (Δ vs RF in next chart)")
    fig.tight_layout()
    fig.savefig(PHASE5_FIGURE_DIR / "phase5_macro_f1_bars.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"saved {PHASE5_FIGURE_DIR / 'phase5_macro_f1_bars.png'}")

    # bar 2: Δ vs RF
    deltas = s[s["model"] != "rf_tabular"].copy()
    deltas = deltas.dropna(subset=["mean_delta_vs_rf"]).sort_values("mean_delta_vs_rf")
    if not deltas.empty:
        fig, ax = plt.subplots(figsize=(8, max(3, len(deltas) * 0.35)))
        colors = [_color_for(w) for w in deltas["workstream"]]
        ax.barh(deltas["model"], deltas["mean_delta_vs_rf"],
                color=colors, edgecolor="black", linewidth=0.5)
        ax.axvline(0, color="black", linewidth=0.8)
        # mark p<0.05
        for i, (_, row) in enumerate(deltas.iterrows()):
            if row.get("n_sig_p05", 0) > 0:
                ax.text(row["mean_delta_vs_rf"], i, f" *{int(row['n_sig_p05'])}",
                        va="center", fontsize=9)
        ax.set_xlabel("mean Δ (model − RF) across panels")
        ax.set_title("Phase 5 — paired Δ vs RF baseline (* = #panels p<0.05)")
        fig.tight_layout()
        fig.savefig(PHASE5_FIGURE_DIR / "phase5_delta_vs_rf.png", dpi=200, bbox_inches="tight")
        plt.close(fig)
        print(f"saved {PHASE5_FIGURE_DIR / 'phase5_delta_vs_rf.png'}")


if __name__ == "__main__":
    main()
