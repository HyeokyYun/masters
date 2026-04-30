"""
Macro-level figures for thesis V2.

Outputs:
  - figures/fig_macro_levi_scatter.pdf/.png
      scatter: LEVI_v1 vs LP pct_change, LEVI_v1 vs closure_rate
  - figures/fig_macro_levi_timeseries.pdf/.png
      monthly LEVI panel: top-5 vs bottom-5 gu means of closure rate
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import rcParams

# Korean font (NanumGothic / AppleGothic / Noto Sans CJK KR)
import matplotlib.font_manager as fm
candidates = ["NanumGothic", "Noto Sans CJK KR", "Noto Sans KR",
              "Malgun Gothic", "AppleGothic"]
chosen = None
available = {f.name for f in fm.fontManager.ttflist}
for c in candidates:
    if c in available:
        chosen = c
        break
if chosen:
    rcParams["font.family"] = chosen
rcParams["axes.unicode_minus"] = False
rcParams["font.size"] = 10

ROOT = Path("/home/hyeoky98/kcd")
OUT_FIG = ROOT / "thesis" / "figures"
OUT_FIG.mkdir(parents=True, exist_ok=True)
A_OUT = ROOT / "thesis" / "analysis" / "outputs"

levi_macro = pd.read_csv(A_OUT / "levi_macro_gu.csv")
panel = pd.read_csv(A_OUT / "macro_gu_panel.csv")
panel["date"] = pd.to_datetime(panel["date"])

# -------- Figure A: two scatter panels --------
fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.6))

ax = axes[0]
x = levi_macro["lp_pct_change"] * 100
y = levi_macro["levi_v1_balance"]
ax.scatter(x, y, s=30, alpha=0.85, color="#1f77b4", edgecolor="white")
# regression line
m, b = np.polyfit(x, y, 1)
xr = np.linspace(x.min(), x.max(), 50)
ax.plot(xr, m * xr + b, color="black", linewidth=1, linestyle="--")
r = x.corr(y)
ax.set_xlabel("구별 생활인구 변화율 (2021-2023, %)")
ax.set_ylabel("LEVI V1 (Growth - Decline share)")
ax.set_title(f"(a) LEVI vs 생활인구 변화율\nPearson r = {r:.3f}", fontsize=11)
# annotate top and bottom
for _, row in levi_macro.iterrows():
    if row["levi_v1_balance"] >= 0.26 or row["levi_v1_balance"] <= 0.075:
        ax.annotate(row["sigungu"],
                    (row["lp_pct_change"] * 100, row["levi_v1_balance"]),
                    fontsize=8, xytext=(3, 3), textcoords="offset points")
ax.grid(alpha=0.3)

ax = axes[1]
x = levi_macro["closure_rate_mean"] * 100
y = levi_macro["levi_v1_balance"]
ax.scatter(x, y, s=30, alpha=0.85, color="#d62728", edgecolor="white")
m, b = np.polyfit(x, y, 1)
xr = np.linspace(x.min(), x.max(), 50)
ax.plot(xr, m * xr + b, color="black", linewidth=1, linestyle="--")
r = x.corr(y)
ax.set_xlabel("구별 월평균 외식업 폐업률 (%)")
ax.set_ylabel("LEVI V1 (Growth - Decline share)")
ax.set_title(f"(b) LEVI vs 폐업률\nPearson r = {r:.3f}", fontsize=11)
for _, row in levi_macro.iterrows():
    if row["levi_v1_balance"] >= 0.26 or row["levi_v1_balance"] <= 0.075:
        ax.annotate(row["sigungu"],
                    (row["closure_rate_mean"] * 100, row["levi_v1_balance"]),
                    fontsize=8, xytext=(3, 3), textcoords="offset points")
ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig(OUT_FIG / "fig_macro_levi_scatter.pdf", bbox_inches="tight")
plt.savefig(OUT_FIG / "fig_macro_levi_scatter.png", dpi=200, bbox_inches="tight")
plt.close()
print(f"saved: {OUT_FIG / 'fig_macro_levi_scatter.pdf'}")

# -------- Figure B: time-series of macro indicators by LEVI strata --------
levi_sorted = levi_macro.sort_values("levi_v1_balance", ascending=False)
top5 = set(levi_sorted.head(5)["sigungu"])
bot5 = set(levi_sorted.tail(5)["sigungu"])

def stratum(x):
    if x in top5: return "LEVI Top 5"
    if x in bot5: return "LEVI Bottom 5"
    return "Middle 15"

panel["stratum"] = panel["sigungu"].map(stratum)
gb = (
    panel.groupby(["date", "stratum"], as_index=False)
         .agg(lp_mean=("lp_mean", "mean"),
              closure_rate=("closure_rate", "mean"))
)

fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharex=True)
colors = {"LEVI Top 5": "#2ca02c", "LEVI Bottom 5": "#d62728",
          "Middle 15": "#7f7f7f"}

ax = axes[0]
for s in ["LEVI Top 5", "Middle 15", "LEVI Bottom 5"]:
    sub = gb[gb["stratum"] == s]
    ax.plot(sub["date"], sub["lp_mean"] / 1000,
            label=s, color=colors[s],
            linewidth=1.6 if s != "Middle 15" else 1.0,
            alpha=0.95 if s != "Middle 15" else 0.55)
ax.set_ylabel("월평균 생활인구 (천 명)")
ax.set_title("(a) 월별 생활인구 — LEVI 상·하위 5구 비교")
ax.grid(alpha=0.3)
ax.legend(frameon=False, fontsize=9)

ax = axes[1]
for s in ["LEVI Top 5", "Middle 15", "LEVI Bottom 5"]:
    sub = gb[gb["stratum"] == s]
    ax.plot(sub["date"], sub["closure_rate"] * 100,
            label=s, color=colors[s],
            linewidth=1.6 if s != "Middle 15" else 1.0,
            alpha=0.95 if s != "Middle 15" else 0.55)
ax.set_ylabel("월 폐업률 (%)")
ax.set_title("(b) 월별 외식업 폐업률 — LEVI 상·하위 5구 비교")
ax.grid(alpha=0.3)
ax.legend(frameon=False, fontsize=9)

plt.tight_layout()
plt.savefig(OUT_FIG / "fig_macro_levi_timeseries.pdf", bbox_inches="tight")
plt.savefig(OUT_FIG / "fig_macro_levi_timeseries.png", dpi=200, bbox_inches="tight")
plt.close()
print(f"saved: {OUT_FIG / 'fig_macro_levi_timeseries.pdf'}")

print(f"\nFont used: {chosen}")
print(f"Available Korean fonts candidates present: {[c for c in candidates if c in available]}")
