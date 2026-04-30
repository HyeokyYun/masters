"""
Correlate gu-level LEVI with external macro indicators.

Inputs:
  - outputs/levi_gu.csv
  - outputs/macro_gu_panel.csv

Outputs:
  - outputs/levi_macro_gu.csv : gu-level merged table
  - outputs/levi_macro_correlations.csv
  - outputs/levi_macro_summary.txt
"""

from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path("/home/hyeoky98/kcd/thesis/analysis/outputs")

levi = pd.read_csv(OUT / "levi_gu.csv")
panel = pd.read_csv(OUT / "macro_gu_panel.csv")
panel["date"] = pd.to_datetime(panel["date"])

# Gu-level macro aggregates over 2021-01 ~ 2023-08 (matches KCD window)
panel_win = panel[(panel["date"] >= "2021-01-01") &
                  (panel["date"] <= "2023-08-31")].copy()

# Living population
lp_agg = (
    panel_win.groupby("sigungu")
             .agg(lp_mean=("lp_mean", "mean"),
                  lp_first=("lp_mean", "first"),
                  lp_last=("lp_mean", "last"))
             .reset_index()
)
lp_agg["lp_pct_change"] = (lp_agg["lp_last"] - lp_agg["lp_first"]) / lp_agg["lp_first"]

# Closure: mean monthly closure rate (macro)
cl_agg = (
    panel_win.groupby("sigungu")
             .agg(closure_rate_mean=("closure_rate", "mean"),
                  closure_rate_median=("closure_rate", "median"),
                  closures_total=("n_closures", "sum"),
                  active_mean=("n_active", "mean"))
             .reset_index()
)

macro = lp_agg.merge(cl_agg, on="sigungu")
merged = levi.merge(macro, on="sigungu", how="inner")
merged.to_csv(OUT / "levi_macro_gu.csv", index=False)
print(f"merged: {merged.shape[0]} gus")

# --- Correlations (Pearson + Spearman) ---
levi_cols = ["levi_v1_balance", "levi_v2_log_odds",
             "levi_v3_trend_mean", "levi_v4_trend_median",
             "levi_v5_shrinkage20"]
macro_cols = ["lp_mean", "lp_pct_change",
              "closure_rate_mean", "closure_rate_median"]

rows = []
for lv in levi_cols:
    for mc in macro_cols:
        p = merged[[lv, mc]].corr(method="pearson").iloc[0, 1]
        s = merged[[lv, mc]].corr(method="spearman").iloc[0, 1]
        rows.append({"levi": lv, "macro": mc,
                     "pearson": round(p, 3),
                     "spearman": round(s, 3)})
corr = pd.DataFrame(rows)
corr.to_csv(OUT / "levi_macro_correlations.csv", index=False)

# --- Summary text ---
lines = []
lines.append("=== LEVI x MACRO INDICATORS (gu level, n=25) ===\n")
lines.append("Window: 2021-01 ~ 2023-08 (KCD data window)\n")
lines.append("Living population source: Seoul Open Data LOCAL_PEOPLE_GU\n")
lines.append("Closure source: Seoul Open Data Food Service Permit Register\n")
lines.append("")
lines.append("--- Gu-level merged table (sorted by LEVI V1) ---")
view = merged[["sigungu", "n_stores", "levi_v1_balance",
               "lp_mean", "lp_pct_change",
               "closure_rate_mean"]].copy()
view.columns = ["sigungu", "kcd_n_stores", "LEVI_v1",
                "LP_mean", "LP_pct_change", "ClosureRate_mean"]
view = view.sort_values("LEVI_v1", ascending=False)
view["LP_mean"] = view["LP_mean"].round(0).astype(int)
view["LP_pct_change"] = (view["LP_pct_change"] * 100).round(2)
view["ClosureRate_mean"] = (view["ClosureRate_mean"] * 100).round(3)
view["LEVI_v1"] = view["LEVI_v1"].round(3)
lines.append(view.to_string(index=False))
lines.append("")

lines.append("--- Correlation matrix (Pearson) ---")
piv_p = corr.pivot(index="levi", columns="macro", values="pearson")
lines.append(piv_p.round(3).to_string())
lines.append("")
lines.append("--- Correlation matrix (Spearman) ---")
piv_s = corr.pivot(index="levi", columns="macro", values="spearman")
lines.append(piv_s.round(3).to_string())
lines.append("")

# Headline numbers for thesis
v1 = merged["levi_v1_balance"]
closure = merged["closure_rate_mean"]
lp_chg = merged["lp_pct_change"]
lp_lvl = merged["lp_mean"]
lines.append("--- Headline correlations ---")
lines.append(f"LEVI_v1 vs closure_rate_mean : Pearson {v1.corr(closure):.3f}, Spearman {v1.corr(closure, method='spearman'):.3f}")
lines.append(f"LEVI_v1 vs lp_mean           : Pearson {v1.corr(lp_lvl):.3f}, Spearman {v1.corr(lp_lvl, method='spearman'):.3f}")
lines.append(f"LEVI_v1 vs lp_pct_change     : Pearson {v1.corr(lp_chg):.3f}, Spearman {v1.corr(lp_chg, method='spearman'):.3f}")

out = "\n".join(lines)
(OUT / "levi_macro_summary.txt").write_text(out)
print(out)
