"""
LEVI (Local Economic Vitality Index) candidate formulas.

Inputs:
  - original_data/meta.csv : store metadata (public_id, sigungu, dong)
  - 260326_fullsample/outputs/tables/observed_window_features_labeled.csv
      : per-store outcome_3 (Growth/Stable/Decline) and continuous slopes

Outputs (written to thesis/analysis/outputs/):
  - levi_dong.csv : dong-level LEVI candidates
  - levi_gu.csv   : gu-level LEVI candidates
  - levi_summary.txt : sample stats and inter-candidate correlation
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/hyeoky98/kcd")
OUT = ROOT / "thesis" / "analysis" / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

meta = pd.read_csv(ROOT / "original_data/meta.csv")
labeled = pd.read_csv(
    ROOT / "260326_fullsample/outputs/tables/observed_window_features_labeled.csv"
)

df = labeled.merge(
    meta[["public_id", "sigungu", "dong"]], on="public_id", how="left"
)
print(f"merged: {df.shape}, dong NA: {df['dong'].isna().sum()}, "
      f"sigungu NA: {df['sigungu'].isna().sum()}")


def levi_candidates(grp):
    n = len(grp)
    g = (grp["outcome_3"] == "Growth").sum()
    s = (grp["outcome_3"] == "Stable").sum()
    d = (grp["outcome_3"] == "Decline").sum()
    return pd.Series({
        "n_stores": n,
        "n_growth": g, "n_stable": s, "n_decline": d,
        "share_growth": g / n if n else np.nan,
        "share_stable": s / n if n else np.nan,
        "share_decline": d / n if n else np.nan,
        # V1: Growth share - Decline share (raw balance)
        "levi_v1_balance": (g - d) / n if n else np.nan,
        # V2: log-odds of Growth vs Decline (excludes stable)
        "levi_v2_log_odds": np.log((g + 0.5) / (d + 0.5)),
        # V3: mean of continuous trend_slope (standardized later)
        "levi_v3_trend_mean": grp["trend_slope"].mean(),
        # V4: median trend (robust to outliers)
        "levi_v4_trend_median": grp["trend_slope"].median(),
        # V5: weighted balance (shrinkage toward 0 when n small)
        #     k=20: dong with fewer than ~20 stores shrunk heavily
        "levi_v5_shrinkage20": (g - d) / (n + 20) if n else np.nan,
    })


# --- DONG LEVEL ---
dong = (
    df.dropna(subset=["dong"])
      .groupby(["sigungu", "dong"], as_index=False)
      .apply(levi_candidates, include_groups=False)
      .reset_index(drop=False)
)
dong.to_csv(OUT / "levi_dong.csv", index=False)
print(f"dong-level: {dong.shape[0]} dongs")

# --- GU LEVEL ---
gu = (
    df.dropna(subset=["sigungu"])
      .groupby("sigungu")
      .apply(levi_candidates, include_groups=False)
      .reset_index()
)
gu.to_csv(OUT / "levi_gu.csv", index=False)
print(f"gu-level: {gu.shape[0]} gus")

# --- SUMMARY ---
lines = []
lines.append("=== LEVI CANDIDATE SUMMARY ===\n")
lines.append(f"Stores joined : {len(df):,}  (with dong: {df['dong'].notna().sum():,})")
lines.append(f"Dongs         : {dong.shape[0]}")
lines.append(f"Sigungus      : {gu.shape[0]}")
lines.append("")
lines.append("Stores per dong quantiles (0.10, 0.25, 0.50, 0.75, 0.90):")
q = dong["n_stores"].quantile([0.10, 0.25, 0.50, 0.75, 0.90]).round(1).to_dict()
lines.append(f"  {q}")
lines.append("")
lines.append("Gu-level LEVI table (sorted by levi_v1_balance):")
lines.append(gu.sort_values("levi_v1_balance", ascending=False).to_string(index=False))
lines.append("")

# Correlation between candidates at dong level (restricted to dongs with n>=10)
dense = dong.query("n_stores >= 10").copy()
cand_cols = ["levi_v1_balance", "levi_v2_log_odds",
             "levi_v3_trend_mean", "levi_v4_trend_median",
             "levi_v5_shrinkage20"]
corr = dense[cand_cols].corr().round(3)
lines.append(f"Inter-candidate correlation (Pearson, dongs with >=10 stores, n={len(dense)}):")
lines.append(corr.to_string())
lines.append("")

with open(OUT / "levi_summary.txt", "w") as f:
    f.write("\n".join(lines))

print("\n" + "\n".join(lines))
