from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "thesis_figures"
MAIN = OUT / "main_figures"
SUPPORT = OUT / "supporting_figures"

AGE_ORDER = ["0_12m", "12_24m", "24_36m", "36_60m", "60_120m", "120m_plus"]
AGE_LABELS = ["0-12m", "12-24m", "24-36m", "36-60m", "60-120m", "120m+"]

FEATURE_LABELS = {
    "trend_slope": "Sales trend",
    "mdd": "Max drawdown",
    "nc_rate": "New-customer ratio",
    "cv": "CV volatility",
    "del_ratio_log": "Delivery share",
    "business_square_size": "Store size",
    "before_noon": "Morning sales share",
    "weekend": "Weekend sales share",
    "delivery_link": "Delivery app link",
}


def configure_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titleweight": "bold",
            "axes.labelsize": 10,
            "axes.titlesize": 12,
            "figure.titlesize": 15,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 9,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
        }
    )


def save_figure(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path.with_suffix(".png"))
    fig.savefig(path.with_suffix(".pdf"))
    plt.close(fig)


def add_panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(
        -0.015,
        1.03,
        label,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=13,
        fontweight="bold",
    )


def figure_1_two_lenses() -> None:
    img_a_path = ROOT / "260319_cur/outputs/figures/fig01_trajectories.png"
    img_b_path = ROOT / "260326_fullsample/outputs/figures/fullsample_age_overview.png"

    img_a = Image.open(img_a_path)
    img_b = Image.open(img_b_path)

    fig = plt.figure(figsize=(14, 12), constrained_layout=True)
    gs = fig.add_gridspec(2, 1, height_ratios=[2.2, 1])
    axes = [fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[1, 0])]

    axes[0].imshow(img_a)
    axes[0].axis("off")
    axes[0].set_title("Post-entry trajectories among recently opened stores", pad=10)
    add_panel_label(axes[0], "A")

    axes[1].imshow(img_b)
    axes[1].axis("off")
    axes[1].set_title("Observed-window states in the full surviving-store sample", pad=10)
    add_panel_label(axes[1], "B")

    fig.suptitle("Figure 1. Two empirical lenses for small-business life cycles")
    save_figure(fig, MAIN / "figure1_two_lenses_lifecycle")


def figure_2_age_drivers() -> None:
    df = pd.read_csv(ROOT / "260326_fullsample/outputs/tables/fullsample_age_bucket_feature_importance.csv")
    df["bucket_code"] = pd.Categorical(df["bucket_code"], AGE_ORDER, ordered=True)
    df["feature_name"] = df["feature"].map(FEATURE_LABELS).fillna(df["feature"])

    selected_features = [
        "trend_slope",
        "mdd",
        "nc_rate",
        "cv",
        "del_ratio_log",
        "business_square_size",
        "before_noon",
        "weekend",
        "delivery_link",
    ]
    heat = (
        df[df["feature"].isin(selected_features)]
        .pivot(index="feature", columns="bucket_code", values="importance_score")
        .reindex(selected_features)
        .reindex(columns=AGE_ORDER)
        .fillna(0.0)
    )
    heat_log = np.log1p(heat)
    feature_axis_labels = [FEATURE_LABELS.get(f, f) for f in heat_log.index]

    fig = plt.figure(figsize=(14, 9), constrained_layout=True)
    gs = fig.add_gridspec(2, 3, height_ratios=[1.2, 1], width_ratios=[1, 1, 1])

    ax_heat = fig.add_subplot(gs[0, :])
    im = ax_heat.imshow(heat_log.values, aspect="auto", cmap="YlGnBu")
    ax_heat.set_xticks(np.arange(len(AGE_LABELS)), labels=AGE_LABELS)
    ax_heat.set_yticks(np.arange(len(feature_axis_labels)), labels=feature_axis_labels)
    ax_heat.set_title("Top drivers by business-age bucket, log(1 + importance score)")
    add_panel_label(ax_heat, "A")

    for i in range(heat_log.shape[0]):
        for j in range(heat_log.shape[1]):
            raw = heat.iloc[i, j]
            if raw > 0:
                ax_heat.text(j, i, f"{raw:.1f}", ha="center", va="center", fontsize=8, color="#1f2933")

    cbar = fig.colorbar(im, ax=ax_heat, fraction=0.025, pad=0.02)
    cbar.set_label("log(1 + importance)")

    focal_features = ["trend_slope", "mdd", "nc_rate"]
    colors = {"Growth": "#1b9e77", "Decline": "#d95f02"}
    for idx, feature in enumerate(focal_features):
        ax = fig.add_subplot(gs[1, idx])
        sub = (
            df[df["feature"].eq(feature)]
            .sort_values("bucket_code")
            .set_index("bucket_code")
            .reindex(AGE_ORDER)
        )
        x = np.arange(len(AGE_LABELS))
        ax.axhline(0, color="#6b7280", lw=0.8)
        ax.plot(x, sub["growth_coef"], marker="o", color=colors["Growth"], label="Growth")
        ax.plot(x, sub["decline_coef"], marker="s", color=colors["Decline"], label="Decline")
        ax.set_xticks(x, labels=AGE_LABELS, rotation=30, ha="right")
        ax.set_title(FEATURE_LABELS[feature])
        ax.set_ylabel("Coefficient")
        ax.grid(axis="y", color="#e5e7eb", linewidth=0.8)
        if idx == 0:
            add_panel_label(ax, "B")
        if idx == 2:
            ax.legend(frameon=False, loc="best")

    fig.suptitle("Figure 2. Age-specific drivers of Growth and Decline")
    save_figure(fig, MAIN / "figure2_age_bucket_drivers")


def figure_3_prediction() -> None:
    weeks = pd.read_csv(ROOT / "260321_cur/outputs/tables/forecast_weeks_comparison.csv")
    weeks_gbm = weeks[weeks["model"].eq("GBM")].copy()
    ab = pd.read_csv(ROOT / "260325/outputs/tables/forecast_feature_ablation_classification_gain.csv")

    fig = plt.figure(figsize=(14, 6), constrained_layout=True)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.05, 1.25])
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])

    label_map = {"label": "12-class trajectory", "outcome3": "3-class state"}
    colors = {"label": "#7570b3", "outcome3": "#1b9e77"}
    for label_type, sub in weeks_gbm.groupby("label_type"):
        sub = sub.sort_values("W")
        ax1.plot(
            sub["W"],
            sub["F1_weighted"],
            marker="o",
            linewidth=2,
            color=colors[label_type],
            label=label_map[label_type],
        )
        for _, row in sub.iterrows():
            ax1.text(row["W"], row["F1_weighted"] + 0.012, f"{row['F1_weighted']:.3f}", ha="center", fontsize=8)
    ax1.set_title("Forecasting performance by early observation window")
    ax1.set_xlabel("Early observation window, weeks")
    ax1.set_ylabel("Weighted F1, GBM")
    ax1.set_xticks(sorted(weeks_gbm["W"].unique()))
    ax1.set_ylim(0.15, 0.68)
    ax1.grid(axis="y", color="#e5e7eb", linewidth=0.8)
    ax1.legend(frameon=False, loc="upper left")
    add_panel_label(ax1, "A")

    display_names = [
        "Level\nonly",
        "+ Trend /\nvolatility",
        "+ Customer\nbehavior",
        "+ Local\ncontext",
        "+ Cluster",
    ]
    x = np.arange(len(ab))
    bar_colors = ["#8da0cb", "#1b9e77", "#66a61e", "#e6ab02", "#a6761d"]
    ax2.bar(x, ab["weighted_f1"], color=bar_colors, width=0.68)
    ax2.plot(x, ab["weighted_f1"], color="#1f2933", marker="o", linewidth=1.5)
    for i, row in ab.reset_index(drop=True).iterrows():
        delta = row["delta_from_prev"]
        label = f"{row['weighted_f1']:.3f}" if pd.isna(delta) else f"{row['weighted_f1']:.3f}\n({delta:+.3f})"
        ax2.text(i, row["weighted_f1"] + 0.006, label, ha="center", va="bottom", fontsize=8)
    ax2.set_title("Feature-block ablation for 3-class state prediction")
    ax2.set_ylabel("Weighted F1, Random Forest")
    ax2.set_xticks(x, labels=display_names)
    ax2.set_ylim(0.53, 0.70)
    ax2.grid(axis="y", color="#e5e7eb", linewidth=0.8)
    ax2.yaxis.set_major_locator(mticker.MultipleLocator(0.025))
    add_panel_label(ax2, "B")

    fig.suptitle("Figure 3. Early prediction improves with temporal dynamics and context")
    save_figure(fig, MAIN / "figure3_prediction_windows_and_ablation")


def figure_s1_supporting() -> None:
    nc = pd.read_csv(ROOT / "260325/outputs/tables/new_customer_quantile_summary.csv")
    vol = pd.read_csv(ROOT / "260325/outputs/tables/volatility_metric_screening.csv")

    fig = plt.figure(figsize=(14, 6), constrained_layout=True)
    gs = fig.add_gridspec(1, 2)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])

    qx = np.arange(len(nc))
    ax1.plot(qx, nc["growth_share"], marker="o", color="#1b9e77", label="Growth share")
    ax1.plot(qx, nc["decline_share"], marker="s", color="#d95f02", label="Decline share")
    ax1.set_xticks(qx, labels=nc["nc_rate_quintile"])
    ax1.set_ylabel("Share")
    ax1.set_title("Outcome shares by new-customer-ratio quintile")
    ax1.grid(axis="y", color="#e5e7eb", linewidth=0.8)
    ax1.legend(frameon=False)
    add_panel_label(ax1, "A")

    rows = vol[vol["metric"].isin(["vol_cv_mean", "vol_resid_rolling12"])].copy()
    if rows.empty:
        rows = vol.head(2).copy()
    rows["metric_label"] = rows["metric"].replace(
        {
            "vol_cv_mean": "Conventional CV",
            "vol_resid_rolling12": "Trend-adjusted\nresidual vol.",
        }
    )
    measures = ["stable_mean", "growth_mean", "decline_mean"]
    outcome_labels = ["Stable", "Growth", "Decline"]
    outcome_colors = ["#4c78a8", "#1b9e77", "#d95f02"]
    x = np.arange(len(rows))
    width = 0.22
    for k, (measure, outcome_label, color) in enumerate(zip(measures, outcome_labels, outcome_colors)):
        ax2.bar(x + (k - 1) * width, rows[measure], width=width, label=outcome_label, color=color)
    ax2.set_xticks(x, labels=rows["metric_label"])
    ax2.set_ylabel("Mean volatility")
    ax2.set_title("Volatility definitions change the interpretation")
    ax2.grid(axis="y", color="#e5e7eb", linewidth=0.8)
    ax2.legend(frameon=False)
    add_panel_label(ax2, "B")

    fig.suptitle("Figure S1. Supporting evidence on customer mix and volatility")
    save_figure(fig, SUPPORT / "figureS1_new_customer_and_volatility")


def main() -> None:
    configure_style()
    MAIN.mkdir(parents=True, exist_ok=True)
    SUPPORT.mkdir(parents=True, exist_ok=True)
    figure_1_two_lenses()
    figure_2_age_drivers()
    figure_3_prediction()
    figure_s1_supporting()


if __name__ == "__main__":
    main()
