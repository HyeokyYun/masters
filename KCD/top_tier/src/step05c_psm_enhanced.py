"""Step 05-C — PSM enhancement: pre-period sales level matching.

step05b에서 pre-trend parallelism 기각(t=-24.99, p<10⁻⁴). 원인: treated가 pre-period
log-sales 수준에서 -0.39 낮음 → matching 실패.

개선:
  (a) PSM covariates에 pre_sales_log_mean, pre_sales_log_std 추가
  (b) Caliper = 0.05 (엄격) + exact matching on 초기 가격대 quartile
  (c) Event study 재수행 후 parallel trends 재검정

출력: did_psm_enhanced_summary.csv, did_event_study_enhanced.csv,
      fig15_psm_enhanced.png
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
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg  # noqa: E402

plt.rcParams.update(cfg.FIG_STYLE)
WINDOW = 8


def load_inputs():
    panel = pd.read_parquet(cfg.PANEL_PATH)
    panel["public_id"] = panel["public_id"].astype(str)
    panel["sales_log"] = np.log1p(panel["sales_card"].fillna(0))
    panel["nc_ratio"] = (panel["customer_new"] /
                         panel["customer"].replace(0, np.nan)).fillna(0.0)
    panel = panel.sort_values(["public_id", "observed_week_idx"])

    gc = pd.read_csv(cfg.TABLE_DIR / "golden_cross_detection.csv")
    gc["public_id"] = gc["public_id"].astype(str)
    feats = pd.read_csv(cfg.FEATURES_PATH)
    feats["public_id"] = feats["public_id"].astype(str)
    return panel, gc, feats


def compute_pre_period_features(panel, gc):
    """각 점포별 gc_week 이전 8주의 매출 수준/변동성을 공변량으로."""
    panel = panel[["public_id", "observed_week_idx", "sales_log"]].copy()
    panel["public_id"] = panel["public_id"].astype(str)
    gc_idx = gc.set_index("public_id")["gc_week"].to_dict()

    def _agg(sub):
        pid = sub.name
        gw = gc_idx.get(str(pid))
        if gw is None:
            return pd.Series({"pre_sales_mean": np.nan, "pre_sales_std": np.nan,
                             "pre_sales_slope": np.nan})
        mask = (sub["observed_week_idx"] >= gw - WINDOW) & (sub["observed_week_idx"] < gw)
        pre = sub.loc[mask, "sales_log"]
        if len(pre) < 3:
            return pd.Series({"pre_sales_mean": np.nan, "pre_sales_std": np.nan,
                             "pre_sales_slope": np.nan})
        x = sub.loc[mask, "observed_week_idx"].astype(float).to_numpy()
        y = pre.to_numpy()
        if np.std(y) < 1e-9:
            slope = 0.0
        else:
            slope = float(stats.linregress(x, y)[0])
        return pd.Series({"pre_sales_mean": float(pre.mean()),
                         "pre_sales_std": float(pre.std()),
                         "pre_sales_slope": slope})

    out = panel.groupby("public_id", observed=True).apply(_agg).reset_index()
    return out


def enhanced_matched_pairs(gc, feats, pre_feats, caliper=0.05):
    """강화된 PSM: 기존 공변량 + pre-period level/variance/slope + exact match on quartile."""
    merged = gc.merge(feats[["public_id", "slope_early_mm", "cv", "nc_rate",
                              "r2_early", "mdd"]], on="public_id", how="inner")
    merged = merged.merge(pre_feats, on="public_id", how="inner")
    merged = merged.dropna()
    print(f"[05c] merged after pre-period enrichment: {len(merged):,}")

    merged["pre_sales_quartile"] = pd.qcut(merged["pre_sales_mean"], q=4,
                                            labels=["Q1", "Q2", "Q3", "Q4"]).astype(str)

    covariates = ["slope_early_mm", "cv", "nc_rate", "r2_early", "mdd",
                  "pre_sales_mean", "pre_sales_std", "pre_sales_slope"]
    scaler = StandardScaler()
    Xc = scaler.fit_transform(merged[covariates])
    lr = LogisticRegression(max_iter=2000, C=0.5).fit(Xc, merged["has_gc"].values)
    merged["pscore"] = lr.predict_proba(Xc)[:, 1]

    treated_all = merged[merged["has_gc"] == 1].copy()
    control_all = merged[merged["has_gc"] == 0].copy()
    print(f"[05c] treated: {len(treated_all)}, control pool: {len(control_all)}")

    matched_rows_t, matched_rows_c = [], []
    for q in merged["pre_sales_quartile"].unique():
        tr_q = treated_all[treated_all["pre_sales_quartile"] == q].reset_index(drop=True)
        ct_q = control_all[control_all["pre_sales_quartile"] == q].reset_index(drop=True)
        if len(tr_q) == 0 or len(ct_q) == 0:
            continue
        nn = NearestNeighbors(n_neighbors=1).fit(ct_q[["pscore"]].values)
        dist, idx = nn.kneighbors(tr_q[["pscore"]].values)
        keep = dist.flatten() < caliper
        if keep.sum() == 0:
            continue
        tr_kept = tr_q[keep].reset_index(drop=True)
        ct_kept = ct_q.iloc[idx.flatten()[keep]].reset_index(drop=True)
        matched_rows_t.append(tr_kept)
        matched_rows_c.append(ct_kept)
        print(f"  quartile {q}: tr={len(tr_q)} ct={len(ct_q)} → matched {len(tr_kept)} within caliper {caliper}")

    if not matched_rows_t:
        raise RuntimeError("no matches within caliper — caliper too tight")
    treated_m = pd.concat(matched_rows_t, ignore_index=True)
    matched_c = pd.concat(matched_rows_c, ignore_index=True)
    print(f"[05c] total matched: {len(treated_m)} pairs")
    return treated_m, matched_c


def build_event_panel(panel, treated, matched_control):
    tr_ids = treated["public_id"].astype(str).values
    ct_ids = matched_control["public_id"].astype(str).values
    gc_weeks = treated["gc_week"].astype(int).values

    mapping = pd.DataFrame({
        "public_id": np.concatenate([tr_ids, ct_ids]),
        "gc_week": np.concatenate([gc_weeks, gc_weeks]),
        "group": ["treated"] * len(tr_ids) + ["control"] * len(ct_ids),
    })
    mapping["public_id"] = mapping["public_id"].astype(str)

    panel_sub = panel[panel["public_id"].isin(mapping["public_id"].unique())][
        ["public_id", "observed_week_idx", "sales_log"]].copy()
    panel_sub["public_id"] = panel_sub["public_id"].astype(str)

    m = panel_sub.merge(mapping, on="public_id", how="inner")
    m["event_time"] = m["observed_week_idx"].astype(int) - m["gc_week"]
    m = m[(m["event_time"] >= -WINDOW) & (m["event_time"] < WINDOW)]
    return m


def event_study(event_df, out_fig):
    grp = event_df.groupby(["event_time", "group"]).agg(
        mean_log=("sales_log", "mean"),
        sem_log=("sales_log", lambda x: x.std() / np.sqrt(len(x))),
    ).reset_index()
    grp.to_csv(cfg.TABLE_DIR / "did_event_study_enhanced.csv", index=False, encoding="utf-8-sig")

    pivot = grp.pivot(index="event_time", columns="group", values="mean_log")
    pivot["diff"] = pivot["treated"] - pivot["control"]
    pre = pivot.loc[pivot.index < 0, "diff"]
    post = pivot.loc[pivot.index >= 0, "diff"]
    pre_mean, post_mean, did = pre.mean(), post.mean(), post.mean() - pre.mean()
    t_pre, p_pre = stats.ttest_1samp(pre, 0.0)

    print(f"\n[05c] Enhanced PSM — event study results")
    print(f"  Pre-period mean (treated - control): {pre_mean:+.4f}")
    print(f"  Post-period mean: {post_mean:+.4f}")
    print(f"  DiD (post - pre): {did:+.4f}")
    print(f"  Pre-trend parallelism: t={t_pre:.3f}, p={p_pre:.4f}  "
          f"({'PASS' if p_pre > 0.05 else 'FAIL'} parallel trends)")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    ax = axes[0]
    for grp_name, marker, color in [("treated", "o", "#1f77b4"), ("control", "s", "#ff7f0e")]:
        sub = grp[grp["group"] == grp_name]
        ax.errorbar(sub["event_time"], sub["mean_log"], yerr=sub["sem_log"],
                    label=grp_name, marker=marker, capsize=3, color=color)
    ax.axvline(0, color="red", linestyle="--", alpha=0.5, label="GC week")
    ax.set_xlabel("Event time")
    ax.set_ylabel("Mean log-sales")
    ax.set_title("Enhanced PSM Event Study")
    ax.legend()
    ax.grid(alpha=0.3)

    ax = axes[1]
    ax.bar(pivot.index, pivot["diff"], color=["#d62728" if i < 0 else "#1f77b4" for i in pivot.index])
    ax.axhline(0, color="k", linewidth=0.8)
    ax.set_xlabel("Event time")
    ax.set_ylabel("Treated − Control")
    ax.set_title(f"Diff (pre-trend p={p_pre:.3f})")
    ax.grid(alpha=0.3)

    fig.suptitle("Figure 15. Enhanced PSM + Event Study")
    fig.tight_layout()
    fig.savefig(out_fig)
    plt.close(fig)
    return {"pre_mean_diff": pre_mean, "post_mean_diff": post_mean,
            "did_estimate": did, "pre_trend_t": t_pre, "pre_trend_p": p_pre,
            "n_pairs": len(event_df["public_id"].unique()) // 2}


def main():
    panel, gc, feats = load_inputs()
    print("[05c] computing pre-period sales features ...")
    pre_feats = compute_pre_period_features(panel, gc)
    print(f"[05c] pre-period features computed: {len(pre_feats):,}")

    treated, matched_c = enhanced_matched_pairs(gc, feats, pre_feats, caliper=0.05)

    if len(treated) > 3000:
        rng = np.random.RandomState(cfg.SEED)
        pick = rng.choice(len(treated), 3000, replace=False)
        treated = treated.iloc[pick].reset_index(drop=True)
        matched_c = matched_c.iloc[pick].reset_index(drop=True)

    event_df = build_event_panel(panel, treated, matched_c)
    print(f"[05c] event panel: {event_df.shape}")
    result = event_study(event_df, cfg.FIGURE_DIR / "fig15_psm_enhanced.png")

    pd.DataFrame([result]).to_csv(cfg.TABLE_DIR / "did_psm_enhanced_summary.csv",
                                   index=False, encoding="utf-8-sig")
    print(f"\n[05c] saved summary: {result}")

    print("\n=== 비교 (step05b vs step05c enhanced) ===")
    try:
        orig = pd.read_csv(cfg.TABLE_DIR / "did_event_study_summary.csv").iloc[0]
        print(f"  Pre-diff:       {orig['pre_mean_diff']:+.4f} → {result['pre_mean_diff']:+.4f}")
        print(f"  DiD estimate:   {orig['did_estimate']:+.4f} → {result['did_estimate']:+.4f}")
        print(f"  Pre-trend p:    {orig['pre_trend_pvalue']:.4g} → {result['pre_trend_p']:.4g}")
    except Exception as e:
        print(f"  (orig summary load skipped: {e})")


if __name__ == "__main__":
    main()
