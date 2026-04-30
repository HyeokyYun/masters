"""Step 02-B — Cox PH proportional hazards 가정 검증.

step02에서 Cox HR을 보고했으나 proportional hazards assumption 미검증.
lifelines의 check_assumptions로 Schoenfeld residuals test 수행.

Output: cox_ph_assumption_check.csv, fig16_cox_residuals.png
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
from lifelines import CoxPHFitter
from lifelines.statistics import proportional_hazard_test

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg  # noqa: E402


def main():
    df = pd.read_parquet(cfg.TABLE_DIR / "unified_store_table.parquet")
    print(f"[02b] unified table: {df.shape}")

    cols = ["survival_weeks", "event_indicator", "slope_early_mm", "cv",
            "nc_rate", "mdd", "r2_early"]
    cols = [c for c in cols if c in df.columns]
    data = df[cols].dropna().copy()
    data = data[(data["survival_weeks"] > 0) & (data["survival_weeks"] < 500)]
    print(f"[02b] cox-ready rows: {len(data):,}")

    cph = CoxPHFitter()
    cph.fit(data, duration_col="survival_weeks", event_col="event_indicator")
    print("\n[02b] Cox PH summary:")
    print(cph.summary[["coef", "exp(coef)", "exp(coef) lower 95%",
                       "exp(coef) upper 95%", "p"]].round(4).to_string())

    print("\n[02b] Proportional hazards test (Schoenfeld residuals):")
    results = proportional_hazard_test(cph, data, time_transform="rank")
    summary = results.summary
    summary.to_csv(cfg.TABLE_DIR / "cox_ph_assumption_check.csv", encoding="utf-8-sig")
    print(summary[["test_statistic", "p"]].round(4).to_string())

    violated = summary[summary["p"] < 0.05].index.tolist()
    print(f"\n[02b] Violating PH assumption (p<0.05): {violated}")
    print(f"[02b] → 이 covariates는 time-varying 처리 또는 stratified Cox 재검토 권장")

    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    axes = axes.flatten()
    covs = [c for c in cph.params_.index if c in data.columns]
    for i, cov in enumerate(covs[:6]):
        ax = axes[i]
        try:
            cph.plot_partial_effects_on_outcome(
                covariates=cov,
                values=list(data[cov].quantile([0.1, 0.5, 0.9]).values),
                cmap="coolwarm", ax=ax)
            ax.set_title(f"{cov} — PH p={summary.loc[cov, 'p']:.3f}")
        except Exception as e:
            ax.text(0.1, 0.5, f"plot error: {e}", fontsize=8)
    for j in range(len(covs), 6):
        axes[j].axis("off")
    fig.suptitle("Figure 16. Cox PH Partial Effects (with PH test p)")
    fig.tight_layout()
    fig.savefig(cfg.FIGURE_DIR / "fig16_cox_residuals.png")
    plt.close(fig)
    print(f"[02b] saved fig16")


if __name__ == "__main__":
    main()
