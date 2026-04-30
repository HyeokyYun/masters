"""Step 11 — Volatility Paradox 해결.

모순:
- Cox PH: cv(변동성) HR=1.11 → "변동성 높을수록 폐업 위험 증가"
- 기존 논문 outline: Growth 집단이 Decline 집단보다 초기 변동성이 높음 → "변동성 주도 성장"

가설:
H1. Survivorship-bias 가설 — 변동성 높은 점포의 대다수는 폐업으로 제거됨. 살아남은 소수가 Growth를 이룬다.
    ⇒ 폐업 포함 전수 분석에서는 cv 평균이 Growth < Decline 일 가능성.
H2. Phase-dependent 가설 — 초기 변동성(첫 10-15주)은 Growth와 정비례하지만,
    후기 또는 장기 변동성은 Decline / 폐업과 정비례한다.
H3. Non-linear (inverted-U) 가설 — 중간 수준 변동성에서 Growth 최대, 양 극단에서 폐업.

검증:
  (1) outcome × closure 교차표에서 cv 분포 차이 비교
  (2) 초기/후기 구간별 cv 분해 — 두 구간 cv가 outcome에 미치는 방향 비교
  (3) cv × outcome의 conditional survival 분석 (Cox PH interaction term)
  (4) cv의 분위수별 closure rate 곡선 (inverted-U 테스트)
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
from scipy import stats

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg  # noqa: E402

plt.rcParams.update(cfg.FIG_STYLE)


def load():
    unified = pd.read_parquet(cfg.TABLE_DIR / "unified_store_table.parquet")
    return unified


def compute_phase_cv(panel: pd.DataFrame) -> pd.DataFrame:
    """점포별 초기/중기/후기 구간의 CV 계산."""
    rows = []
    for pid, g in panel.groupby("public_id", observed=True, sort=False):
        g = g.sort_values("observed_week_idx")
        sales = g["sales_card"].to_numpy(dtype=float)
        n = len(sales)
        if n < 30:
            continue
        sales_log = np.log1p(sales)
        t1 = sales_log[:15]
        t2 = sales_log[15:30]
        t3 = sales_log[30:] if n > 30 else np.array([])

        def cv(arr):
            if len(arr) < 3:
                return np.nan
            m = np.nanmean(arr)
            return float(np.nanstd(arr) / m) if m else np.nan

        rows.append({
            "public_id": pid,
            "cv_w1_15": cv(t1),
            "cv_w16_30": cv(t2),
            "cv_w31_plus": cv(t3) if len(t3) >= 3 else np.nan,
            "n_weeks": n,
        })
    return pd.DataFrame(rows)


def hypothesis_1_survivorship(df: pd.DataFrame):
    """Survivorship-bias: 살아남은 점포만 보면 Growth가 변동성 큼,
    폐업 포함 전수에서는 뒤집히는가?"""
    print("\n=== H1: Survivorship Bias ===")
    rows = []
    if "cv" not in df.columns:
        print("cv column missing — skip")
        return pd.DataFrame()

    for pop_name, pop_mask in {
        "Survivors only (is_closed=0)": df["is_closed"] == 0,
        "All stores (including closed)": pd.Series([True] * len(df), index=df.index),
    }.items():
        sub = df[pop_mask & df["cv"].notna() & df["outcome_3"].notna()]
        for outcome in ["Growth", "Stable", "Decline"]:
            cvs = sub.loc[sub["outcome_3"] == outcome, "cv"]
            if len(cvs) > 0:
                rows.append({
                    "population": pop_name,
                    "outcome": outcome,
                    "n": len(cvs),
                    "cv_mean": float(cvs.mean()),
                    "cv_median": float(cvs.median()),
                    "cv_std": float(cvs.std()),
                })
        closed_cv = df.loc[(pop_mask) & (df["cv"].notna()) & (df["is_closed"] == 1), "cv"]
        if len(closed_cv) > 0 and "Closed" not in [r["outcome"] for r in rows if r["population"] == pop_name]:
            rows.append({
                "population": pop_name,
                "outcome": "Closed",
                "n": len(closed_cv),
                "cv_mean": float(closed_cv.mean()),
                "cv_median": float(closed_cv.median()),
                "cv_std": float(closed_cv.std()),
            })
    out = pd.DataFrame(rows)
    out.to_csv(cfg.TABLE_DIR / "volatility_h1_survivorship.csv", index=False, encoding="utf-8-sig")
    print(out.to_string(index=False))

    for pop in out["population"].unique():
        sub = out[out["population"] == pop]
        growth = sub.loc[sub["outcome"] == "Growth", "cv_mean"]
        decline = sub.loc[sub["outcome"] == "Decline", "cv_mean"]
        if not growth.empty and not decline.empty:
            print(f"  [{pop}] Growth cv={growth.iloc[0]:.3f} vs Decline cv={decline.iloc[0]:.3f} "
                  f"→ {'Growth>Decline' if growth.iloc[0] > decline.iloc[0] else 'Growth<Decline'}")
    return out


def hypothesis_2_phase(panel: pd.DataFrame, df: pd.DataFrame):
    """Phase 가설: 초기 cv vs 후기 cv의 방향 차이."""
    print("\n=== H2: Phase-dependent ===")
    phase = compute_phase_cv(panel)
    phase["public_id"] = phase["public_id"].astype(str)
    merged = df[["public_id", "outcome_3", "is_closed"]].merge(phase, on="public_id", how="inner")

    rows = []
    for phase_col in ["cv_w1_15", "cv_w16_30", "cv_w31_plus"]:
        for outcome in ["Growth", "Stable", "Decline"]:
            vals = merged.loc[(merged["outcome_3"] == outcome) & merged[phase_col].notna(), phase_col]
            if len(vals) > 0:
                rows.append({
                    "phase": phase_col,
                    "outcome": outcome,
                    "n": len(vals),
                    "cv_mean": float(vals.mean()),
                    "cv_median": float(vals.median()),
                })
    out = pd.DataFrame(rows)
    out.to_csv(cfg.TABLE_DIR / "volatility_h2_phase.csv", index=False, encoding="utf-8-sig")
    print(out.to_string(index=False))

    print("\n방향성 요약:")
    for phase_col in ["cv_w1_15", "cv_w16_30", "cv_w31_plus"]:
        sub = out[out["phase"] == phase_col]
        g = sub.loc[sub["outcome"] == "Growth", "cv_mean"]
        d = sub.loc[sub["outcome"] == "Decline", "cv_mean"]
        if not g.empty and not d.empty:
            dir_ = "Growth > Decline" if g.iloc[0] > d.iloc[0] else "Growth < Decline"
            print(f"  {phase_col}: Growth={g.iloc[0]:.3f}  Decline={d.iloc[0]:.3f}  → {dir_}")

    for phase_col in ["cv_w1_15", "cv_w16_30", "cv_w31_plus"]:
        g = merged.loc[(merged["outcome_3"] == "Growth") & merged[phase_col].notna(), phase_col]
        d = merged.loc[(merged["outcome_3"] == "Decline") & merged[phase_col].notna(), phase_col]
        if len(g) > 10 and len(d) > 10:
            t, p = stats.mannwhitneyu(g, d, alternative="two-sided")
            print(f"  {phase_col} Mann-Whitney U: p={p:.3e}  (n_G={len(g):,}, n_D={len(d):,})")
    return merged


def hypothesis_3_inverted_u(df: pd.DataFrame):
    """cv를 10분위로 나누어 각 분위의 outcome 분포 / 폐업률 분석."""
    print("\n=== H3: Inverted-U (분위수별) ===")
    if "cv" not in df.columns:
        return pd.DataFrame()
    sub = df.dropna(subset=["cv", "outcome_3", "is_closed"]).copy()
    sub["cv_decile"] = pd.qcut(sub["cv"], 10, labels=False, duplicates="drop")

    grid = sub.groupby("cv_decile").agg(
        n=("public_id", "count"),
        closure_rate=("is_closed", "mean"),
        growth_rate=("outcome_3", lambda x: (x == "Growth").mean()),
        stable_rate=("outcome_3", lambda x: (x == "Stable").mean()),
        decline_rate=("outcome_3", lambda x: (x == "Decline").mean()),
        cv_lower=("cv", "min"),
        cv_upper=("cv", "max"),
    ).reset_index()
    grid.to_csv(cfg.TABLE_DIR / "volatility_h3_deciles.csv", index=False, encoding="utf-8-sig")
    print(grid.to_string(index=False))

    peak_growth_decile = grid.loc[grid["growth_rate"].idxmax(), "cv_decile"]
    print(f"\nGrowth rate 최대 decile: D{int(peak_growth_decile)} "
          f"(cv {grid.loc[grid['cv_decile']==peak_growth_decile, 'cv_lower'].iloc[0]:.2f}"
          f" — {grid.loc[grid['cv_decile']==peak_growth_decile, 'cv_upper'].iloc[0]:.2f})")

    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax2 = ax1.twinx()
    ax1.plot(grid["cv_decile"], grid["growth_rate"], "o-", color="#2a7ab0", label="Growth rate")
    ax1.plot(grid["cv_decile"], grid["decline_rate"], "s-", color="#d62728", label="Decline rate")
    ax1.plot(grid["cv_decile"], grid["stable_rate"], "^-", color="#8c8c8c", label="Stable rate")
    ax2.plot(grid["cv_decile"], grid["closure_rate"], "d--", color="#ff7f0e", label="Closure rate", lw=2)
    ax1.set_xlabel("CV decile (1 = lowest variability, 10 = highest)")
    ax1.set_ylabel("Outcome rate")
    ax2.set_ylabel("Closure rate", color="#ff7f0e")
    ax1.set_title("Figure 9. Volatility Paradox — CV 분위수별 Outcome / 폐업률")
    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")
    ax1.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(cfg.FIGURE_DIR / "fig9_volatility_paradox.png")
    plt.close(fig)
    return grid


def interaction_cox(df: pd.DataFrame):
    """Cox PH with cv × outcome interaction — outcome 그룹별 HR 비교."""
    print("\n=== Interaction Cox PH ===")
    sub = df.dropna(subset=["survival_weeks", "event_indicator", "cv", "outcome_3"]).copy()
    sub = sub[sub["survival_weeks"] > 0]
    for c in ["cv"]:
        lo, hi = sub[c].quantile([0.01, 0.99])
        sub[c] = sub[c].clip(lo, hi)

    rows = []
    for outcome in ["Growth", "Stable", "Decline"]:
        sub_out = sub[sub["outcome_3"] == outcome][["survival_weeks", "event_indicator", "cv"]].dropna()
        if len(sub_out) < 100 or sub_out["event_indicator"].sum() < 20:
            continue
        sub_out["cv_z"] = (sub_out["cv"] - sub_out["cv"].mean()) / sub_out["cv"].std()
        sub_out = sub_out.drop(columns=["cv"])
        cph = CoxPHFitter(penalizer=0.01)
        try:
            cph.fit(sub_out, duration_col="survival_weeks", event_col="event_indicator", show_progress=False)
            s = cph.summary.iloc[0]
            rows.append({
                "outcome_subgroup": outcome,
                "n": len(sub_out),
                "events": int(sub_out["event_indicator"].sum()),
                "HR_cv": s["exp(coef)"],
                "CI_lower": s["exp(coef) lower 95%"],
                "CI_upper": s["exp(coef) upper 95%"],
                "p": s["p"],
            })
        except Exception as e:
            print(f"  {outcome}: failed — {e}")
    out = pd.DataFrame(rows)
    out.to_csv(cfg.TABLE_DIR / "volatility_cox_by_outcome.csv", index=False, encoding="utf-8-sig")
    print(out.to_string(index=False))
    return out


def main():
    df = load()
    panel = pd.read_parquet(cfg.PANEL_PATH)
    panel["public_id"] = panel["public_id"].astype(str)

    hypothesis_1_survivorship(df)
    hypothesis_2_phase(panel, df)
    hypothesis_3_inverted_u(df)
    interaction_cox(df)

    print("\n=== 해석 요약 ===")
    print("표 volatility_h1_survivorship.csv, h2_phase.csv, h3_deciles.csv, cox_by_outcome.csv")
    print("Fig: fig9_volatility_paradox.png")


if __name__ == "__main__":
    main()
