"""Step 14 — Figure 1: Conceptual Framework diagram.

DSR build–evaluate cycle + theoretical refinement lineage의 one-figure summary.
논문 첫 페이지에 들어갈 publication-quality framework.

구조 (3-column layout):
  Left   : Problem (Small business closure, survivorship bias, lifecycle heterogeneity)
  Middle : Method (Data foundation → Hybrid prediction → Causal identification → EWS)
  Right  : Contributions (4개 논문 contribution)

아래는 matplotlib 기반 구현 — TikZ/Lucidchart 대체용.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg  # noqa: E402


def draw_box(ax, x, y, w, h, text, facecolor="#e8f0f7", edgecolor="#1f4e79",
             fontsize=9, fontweight="normal", wrap=True):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                         linewidth=1.2, edgecolor=edgecolor, facecolor=facecolor)
    ax.add_patch(box)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fontsize, fontweight=fontweight, wrap=wrap)


def draw_arrow(ax, x1, y1, x2, y2, color="#555555", lw=1.4):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color, lw=lw))


def main():
    fig, ax = plt.subplots(figsize=(14, 9))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 9)
    ax.axis("off")

    ax.text(7, 8.65, "Figure 1. Conceptual Framework — Data-Driven EWS for Small Business Lifecycle",
            ha="center", va="center", fontsize=13, fontweight="bold")

    ax.text(2, 8.2, "Problem Space", ha="center", fontsize=11, fontweight="bold", color="#8B0000")
    ax.text(7, 8.2, "Research Method (DSR: Build + Evaluate)", ha="center", fontsize=11,
            fontweight="bold", color="#1f4e79")
    ax.text(12, 8.2, "Contributions", ha="center", fontsize=11, fontweight="bold", color="#0B5345")

    draw_box(ax, 0.3, 6.9, 3.4, 1.0,
             "P1. SMB closure at scale\n(~800K cases / year in KR, 2023)",
             facecolor="#fce4e4", edgecolor="#8B0000", fontsize=9, fontweight="bold")
    draw_box(ax, 0.3, 5.6, 3.4, 1.0,
             "P2. Survivorship bias\n(panel design biases outcomes)",
             facecolor="#fce4e4", edgecolor="#8B0000", fontsize=9)
    draw_box(ax, 0.3, 4.3, 3.4, 1.0,
             "P3. Binary survival framing\n(ignores multi-path trajectories)",
             facecolor="#fce4e4", edgecolor="#8B0000", fontsize=9)
    draw_box(ax, 0.3, 3.0, 3.4, 1.0,
             "P4. No financial statements\n(classic EWS inapplicable to micro-SMB)",
             facecolor="#fce4e4", edgecolor="#8B0000", fontsize=9)
    draw_box(ax, 0.3, 1.5, 3.4, 1.2,
             "Kernel Theories\n(1) Lifecycle theory\n  (Cooper 1994; Shepherd 2003)\n(2) EWS / Info economics\n  (Altman 1968; Elkan 2001)",
             facecolor="#fff4e6", edgecolor="#B8860B", fontsize=8)

    draw_box(ax, 4.5, 7.2, 5.0, 0.9,
             "Data Foundation\n59,089 stores × 137 weeks × weekly card transaction (KCD)",
             facecolor="#e8f0f7", edgecolor="#1f4e79", fontsize=9, fontweight="bold")
    draw_box(ax, 4.5, 5.9, 5.0, 1.0,
             "Survival + Causal Identification\nKaplan-Meier · Cox PH · Granger · PSM+DiD\n(enhanced: placebo 11.35σ, ATT=+0.099)",
             facecolor="#e8f0f7", edgecolor="#1f4e79", fontsize=9)
    draw_box(ax, 4.5, 4.6, 5.0, 1.0,
             "Hybrid Prediction (Proposed D)\n46 engineered + K-Means/K-Shape + change-point\nvs Deep baselines (LSTM/GRU/Transformer 5ch)",
             facecolor="#e8f0f7", edgecolor="#1f4e79", fontsize=9)
    draw_box(ax, 4.5, 3.3, 5.0, 1.0,
             "Volatility Paradox Decomposition\nPhase × outcome × survivorship layers\n(H1–H4 four-way decomposition)",
             facecolor="#e8f0f7", edgecolor="#1f4e79", fontsize=9)
    draw_box(ax, 4.5, 1.9, 5.0, 1.1,
             "EWS Artifact\n49K store risk scores · calibration · cost-benefit\n(AP=0.699 for Decline, 3.1× baseline)",
             facecolor="#d5e8d4", edgecolor="#2E7D32", fontsize=9, fontweight="bold")
    draw_box(ax, 4.5, 0.4, 5.0, 1.2,
             "Robustness self-audit (§16-22)\nCluster leakage · Cox PH · threshold sensitivity\n· Enhanced PSM · UDX vs outcome · MV DL fair comparison",
             facecolor="#fff9e6", edgecolor="#B8860B", fontsize=8)

    draw_box(ax, 10.4, 7.2, 3.4, 0.9,
             "C1. Survivorship bias\n5-fold closure gap\n(10% vs 52%)",
             facecolor="#d5f5e3", edgecolor="#0B5345", fontsize=9, fontweight="bold")
    draw_box(ax, 10.4, 5.9, 3.4, 1.0,
             "C2. Volatility Paradox\n4-way decomposition\n(phase × outcome × survival)",
             facecolor="#d5f5e3", edgecolor="#0B5345", fontsize=9)
    draw_box(ax, 10.4, 4.6, 3.4, 1.0,
             "C3. Hybrid wins over DL\nF1 0.648 vs 0.529\n(+22% at T=30)",
             facecolor="#d5f5e3", edgecolor="#0B5345", fontsize=9)
    draw_box(ax, 10.4, 3.0, 3.4, 1.2,
             "C4. Deployable EWS artifact\nCalibrated · cost-aware\n· policy-ready risk score",
             facecolor="#d5f5e3", edgecolor="#0B5345", fontsize=9, fontweight="bold")
    draw_box(ax, 10.4, 1.2, 3.4, 1.4,
             "Design Principles\nDP1: Inductive bias via\n  temporal clustering\nDP2: Causal triangulation\n  (Granger+DiD+FE)\nDP3: Cost-sensitive EWS\n  operating points",
             facecolor="#e8dcf0", edgecolor="#5B2C6F", fontsize=8)

    draw_arrow(ax, 3.7, 7.4, 4.5, 7.65)
    draw_arrow(ax, 3.7, 6.1, 4.5, 6.4)
    draw_arrow(ax, 3.7, 4.8, 4.5, 5.1)
    draw_arrow(ax, 3.7, 3.5, 4.5, 3.8)
    draw_arrow(ax, 3.7, 2.1, 4.5, 2.45)
    draw_arrow(ax, 9.5, 7.65, 10.4, 7.65)
    draw_arrow(ax, 9.5, 6.4, 10.4, 6.4)
    draw_arrow(ax, 9.5, 5.1, 10.4, 5.1)
    draw_arrow(ax, 9.5, 2.45, 10.4, 3.6)
    draw_arrow(ax, 9.5, 3.8, 10.4, 3.6)

    legend_patches = [
        mpatches.Patch(facecolor="#fce4e4", edgecolor="#8B0000", label="Problem / Gap"),
        mpatches.Patch(facecolor="#e8f0f7", edgecolor="#1f4e79", label="Research artifact component"),
        mpatches.Patch(facecolor="#d5f5e3", edgecolor="#0B5345", label="Contribution"),
        mpatches.Patch(facecolor="#fff4e6", edgecolor="#B8860B", label="Kernel theory / Self-audit"),
        mpatches.Patch(facecolor="#e8dcf0", edgecolor="#5B2C6F", label="DSR Design Principle"),
    ]
    ax.legend(handles=legend_patches, loc="lower center", bbox_to_anchor=(0.5, -0.04),
              ncol=5, fontsize=8.5, frameon=False)

    out = cfg.FIGURE_DIR / "fig1_conceptual_framework.png"
    fig.tight_layout()
    fig.savefig(out, dpi=300)
    plt.close(fig)
    print(f"saved: {out}")


if __name__ == "__main__":
    main()
