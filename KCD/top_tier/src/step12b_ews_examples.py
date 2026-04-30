"""Step 12b - EWS example stores for meeting/demo use.

This script turns the store-level EWS scores into a small set of concrete,
reviewable examples. It does not retrain the EWS model. It reads the existing
scores and observed-window panel, then writes:

  outputs/tables/ews_example_stores.csv
  outputs/figures/fig19_ews_example_stores.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg  # noqa: E402

plt.rcParams.update(cfg.FIG_STYLE)

SCORES_PATH = cfg.TABLE_DIR / "ews_scores_per_store.csv"
FEATURES_PATH = cfg.TABLE_DIR / "observed_window_features_labeled.csv"
PANEL_PATH = cfg.TABLE_DIR / "observed_window_panel.parquet"
OUT_TABLE = cfg.TABLE_DIR / "ews_example_stores.csv"
OUT_FIG = cfg.FIGURE_DIR / "fig19_ews_example_stores.png"


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    scores = pd.read_csv(SCORES_PATH)
    scores["public_id"] = scores["public_id"].astype(str)

    features = pd.read_csv(
        FEATURES_PATH,
        usecols=[
            "public_id",
            "category",
            "outcome_3",
            "slope_all_mm",
            "mdd",
            "nc_rate",
            "n_observed_weeks_used",
        ],
    )
    features["public_id"] = features["public_id"].astype(str)

    panel = pd.read_parquet(
        PANEL_PATH,
        columns=[
            "public_id",
            "observed_week_idx",
            "sales_card",
            "customer",
            "customer_new",
            "category",
        ],
    )
    panel["public_id"] = panel["public_id"].astype(str)
    return scores, features, panel


def _select_one(
    df: pd.DataFrame,
    label: str,
    rule: str,
    query: str,
    sort_col: str,
    ascending: bool,
    used: set[str],
) -> pd.Series:
    cand = df.query(query).sort_values(sort_col, ascending=ascending)
    cand = cand[~cand["public_id"].isin(used)]
    if cand.empty:
        raise RuntimeError(f"No EWS example candidate found for {label}: {query}")
    row = cand.iloc[0].copy()
    row["case_label"] = label
    row["case_type"] = rule
    used.add(str(row["public_id"]))
    return row


def select_examples(scores: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    df = scores.merge(
        features.drop(columns=["outcome_3"]),
        on="public_id",
        how="left",
    )

    used: set[str] = set()
    rows = [
        _select_one(
            df,
            "Case A",
            "High-risk alert, true Decline",
            "outcome_3 == 'Decline'",
            "risk_score_decline",
            False,
            used,
        ),
        _select_one(
            df,
            "Case B",
            "High-risk alert, true Decline",
            "outcome_3 == 'Decline'",
            "risk_score_decline",
            False,
            used,
        ),
        _select_one(
            df,
            "Case C",
            "Watchlist, actual Stable",
            "outcome_3 == 'Stable'",
            "risk_score_decline",
            False,
            used,
        ),
        _select_one(
            df,
            "Case D",
            "Growth opportunity",
            "outcome_3 == 'Growth'",
            "opportunity_score_growth",
            False,
            used,
        ),
        _select_one(
            df,
            "Case E",
            "Growth opportunity",
            "outcome_3 == 'Growth'",
            "opportunity_score_growth",
            False,
            used,
        ),
        _select_one(
            df,
            "Case F",
            "Missed Decline caveat",
            "outcome_3 == 'Decline'",
            "risk_score_decline",
            True,
            used,
        ),
    ]

    out = pd.DataFrame(rows)
    out["recommended_action"] = out["case_type"].map(
        {
            "High-risk alert, true Decline": "Priority monitoring/support candidate",
            "Watchlist, actual Stable": "Watchlist; avoid treating score as final label",
            "Growth opportunity": "Low decline risk; possible growth/opportunity case",
            "Missed Decline caveat": "Model limitation; inspect raw trajectory before excluding",
        }
    )
    cols = [
        "case_label",
        "case_type",
        "recommended_action",
        "public_id",
        "outcome_3",
        "category",
        "risk_score_decline",
        "opportunity_score_growth",
        "slope_all_mm",
        "mdd",
        "nc_rate",
        "n_observed_weeks_used",
    ]
    return out[cols]


def make_plot(examples: pd.DataFrame, panel: pd.DataFrame) -> None:
    example_ids = examples["public_id"].astype(str).tolist()
    sub = panel[
        (panel["public_id"].isin(example_ids))
        & (panel["observed_week_idx"] < cfg.PREDICTION_WEEKS)
    ].copy()
    sub["nc_ratio"] = np.where(
        sub["customer"] > 0,
        sub["customer_new"] / sub["customer"],
        np.nan,
    )
    sub["sales_index"] = sub.groupby("public_id")["sales_card"].transform(
        lambda s: s / (s.dropna().iloc[0] if s.notna().any() and s.dropna().iloc[0] else np.nan)
    )

    fig, axes = plt.subplots(3, 2, figsize=(13.5, 11), sharex=True)
    axes = axes.ravel()

    for ax, (_, ex) in zip(axes, examples.iterrows()):
        pid = str(ex["public_id"])
        g = sub[sub["public_id"] == pid].sort_values("observed_week_idx")
        if g.empty:
            ax.text(0.5, 0.5, "No panel data", ha="center", va="center", transform=ax.transAxes)
            continue

        x = g["observed_week_idx"].to_numpy() + 1
        sales = g["sales_index"].to_numpy(dtype=float)
        nc = g["nc_ratio"].rolling(3, min_periods=1).mean().to_numpy(dtype=float)

        ax.plot(x, sales, color="#1f5f99", lw=2.2, label="Sales index")
        ax.set_ylabel("Sales index")
        ax.grid(True, alpha=0.25)
        ax.set_title(
            f"{ex['case_label']} | {ex['outcome_3']} | "
            f"Risk {ex['risk_score_decline']:.1f}, Opp {ex['opportunity_score_growth']:.1f}",
            fontsize=11,
        )

        ax2 = ax.twinx()
        ax2.plot(x, nc, color="#d47a1f", lw=1.8, alpha=0.85, label="New-customer ratio")
        ax2.set_ylabel("NC ratio")
        ax2.set_ylim(0, max(1.0, np.nanmax(nc) * 1.1 if np.isfinite(nc).any() else 1.0))

        ax.text(
            0.02,
            0.04,
            f"{ex['case_type']} | {ex['category']}",
            transform=ax.transAxes,
            fontsize=9,
            color="#333333",
            bbox={"facecolor": "white", "alpha": 0.72, "edgecolor": "#dddddd", "pad": 3},
        )

        lines, labels = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines + lines2, labels + labels2, loc="upper left", fontsize=8, frameon=False)

    for ax in axes[-2:]:
        ax.set_xlabel("Observed week")

    fig.suptitle("Figure 19. Example Store-Level EWS Scores and 30-Week Trajectories", y=0.995)
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    fig.savefig(OUT_FIG)
    plt.close(fig)


def main() -> None:
    scores, features, panel = load_inputs()
    examples = select_examples(scores, features)
    examples.to_csv(OUT_TABLE, index=False, encoding="utf-8-sig")
    make_plot(examples, panel)
    print(f"[12b] saved: {OUT_TABLE}")
    print(f"[12b] saved: {OUT_FIG}")
    print(examples.to_string(index=False))


if __name__ == "__main__":
    main()
