"""Step 05-B — DiD Event Study (parallel trends 검증).

step05의 PSM+DiD는 ATT=+0.117만 보고함 → 리뷰어가 parallel trends 공격 가능.
본 스크립트는:
  (a) Event study: gc_week 기준 -8 ~ +8주 매주 log-sales mean for treated vs matched control
  (b) Pre-trend 평행성 검정 (t-test on week-by-week diff in pre-period)
  (c) Placebo test: 랜덤 "가짜 GC" week 지정 후 ATT 측정 → 유의하면 내생성 강력 증거

출력: did_event_study.csv, did_placebo.csv, fig14_did_event_study.png
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


def matched_pairs(gc: pd.DataFrame, feats: pd.DataFrame):
    merged = gc.merge(feats[["public_id", "slope_early_mm", "cv", "nc_rate",
                              "r2_early", "mdd"]], on="public_id", how="inner")
    merged = merged.dropna()
    covariates = ["slope_early_mm", "cv", "nc_rate", "r2_early", "mdd"]
    scaler = StandardScaler()
    Xc = scaler.fit_transform(merged[covariates])
    lr = LogisticRegression(max_iter=1000).fit(Xc, merged["has_gc"].values)
    merged["pscore"] = lr.predict_proba(Xc)[:, 1]

    treated = merged[merged["has_gc"] == 1].reset_index(drop=True)
    control = merged[merged["has_gc"] == 0].reset_index(drop=True)
    nn = NearestNeighbors(n_neighbors=1).fit(control[["pscore"]].values)
    _, idx = nn.kneighbors(treated[["pscore"]].values)
    matched_control = control.iloc[idx.flatten()].reset_index(drop=True)
    return treated, matched_control


def build_event_panel(panel: pd.DataFrame, treated: pd.DataFrame,
                      matched_control: pd.DataFrame, label_gc_week_source: str = "treated"):
    """Returns event-time panel: (public_id, group, event_time, sales_log).
    벡터화: treated/control pid별 assignment 테이블을 만들고 panel과 한 번 join."""
    tr_ids = treated["public_id"].astype(str).values
    gc_weeks = treated["gc_week"].astype(int).values
    ct_ids = matched_control["public_id"].astype(str).values

    mapping = pd.DataFrame({
        "public_id": np.concatenate([tr_ids, ct_ids]),
        "gc_week": np.concatenate([gc_weeks, gc_weeks]),
        "group": ["treated"] * len(tr_ids) + ["control"] * len(ct_ids),
    })
    mapping["public_id"] = mapping["public_id"].astype(str)

    panel_sub = panel[panel["public_id"].isin(mapping["public_id"].unique())][
        ["public_id", "observed_week_idx", "sales_log", "nc_ratio"]
    ].copy()
    panel_sub["public_id"] = panel_sub["public_id"].astype(str)

    merged = panel_sub.merge(mapping, on="public_id", how="inner")
    merged["event_time"] = merged["observed_week_idx"].astype(int) - merged["gc_week"]
    merged = merged[(merged["event_time"] >= -WINDOW) & (merged["event_time"] < WINDOW)]
    return merged[["public_id", "group", "event_time", "sales_log", "nc_ratio"]].reset_index(drop=True)


def event_study_plot(event_df: pd.DataFrame, out_path: Path):
    grp = event_df.groupby(["event_time", "group"]).agg(
        mean_log=("sales_log", "mean"),
        sem_log=("sales_log", lambda x: x.std() / np.sqrt(len(x))),
        n=("sales_log", "size"),
        mean_nc=("nc_ratio", "mean"),
    ).reset_index()
    grp.to_csv(cfg.TABLE_DIR / "did_event_study.csv", index=False, encoding="utf-8-sig")

    pivot = grp.pivot(index="event_time", columns="group", values="mean_log")
    pivot["diff"] = pivot["treated"] - pivot["control"]
    print("=== Event-time mean log-sales ===")
    print(pivot.round(4).to_string())

    pre_diffs = pivot.loc[pivot.index < 0, "diff"]
    post_diffs = pivot.loc[pivot.index >= 0, "diff"]
    pre_mean = pre_diffs.mean()
    post_mean = post_diffs.mean()
    did = post_mean - pre_mean
    print(f"\nPre-period mean diff (treated - control): {pre_mean:+.4f}")
    print(f"Post-period mean diff: {post_mean:+.4f}")
    print(f"DiD (post - pre diff): {did:+.4f}")

    t_pre, p_pre = stats.ttest_1samp(pre_diffs, 0.0)
    print(f"Pre-trend parallelism test (H0: pre-diff=0): t={t_pre:.3f}, p={p_pre:.4f}  "
          f"(p>0.05 = parallel trends hold)")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ax = axes[0]
    tr = grp[grp["group"] == "treated"]
    ct = grp[grp["group"] == "control"]
    ax.errorbar(tr["event_time"], tr["mean_log"], yerr=tr["sem_log"],
                label="Treated (GC)", marker="o", capsize=3)
    ax.errorbar(ct["event_time"], ct["mean_log"], yerr=ct["sem_log"],
                label="Matched control", marker="s", capsize=3)
    ax.axvline(0, color="red", linestyle="--", alpha=0.5, label="GC week")
    ax.set_xlabel("Event time (weeks relative to Golden Cross)")
    ax.set_ylabel("Mean log-sales")
    ax.set_title("Event Study: Sales around GC")
    ax.legend()
    ax.grid(alpha=0.3)

    ax = axes[1]
    ax.bar(pivot.index, pivot["diff"], color=["#d62728" if i < 0 else "#1f77b4" for i in pivot.index])
    ax.axhline(0, color="k", linewidth=0.8)
    ax.axvline(-0.5, color="red", linestyle="--", alpha=0.5)
    ax.set_xlabel("Event time")
    ax.set_ylabel("Treated − Control (log-sales)")
    ax.set_title(f"Week-by-week diff (pre-trend p={p_pre:.3f})")
    ax.grid(alpha=0.3)

    fig.suptitle("Figure 14. DiD Event Study — Parallel Trends Check")
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[05b] saved figure to {out_path}")
    return pre_mean, post_mean, did, p_pre


def placebo_test(panel: pd.DataFrame, treated: pd.DataFrame,
                 matched_control: pd.DataFrame, n_rounds: int = 20):
    """랜덤하게 가짜 GC week 지정 후 ATT 계산. 벡터화."""
    print("\n=== Placebo Test (random GC week) ===")
    rng = np.random.RandomState(cfg.SEED)

    all_ids = (list(treated["public_id"].astype(str))
               + list(matched_control["public_id"].astype(str)))
    panel_sub = panel[panel["public_id"].isin(set(all_ids))][
        ["public_id", "observed_week_idx", "sales_log"]
    ].copy()
    panel_sub["public_id"] = panel_sub["public_id"].astype(str)

    results = []
    for r in range(n_rounds):
        fake_weeks = rng.randint(12, 40, size=len(treated))
        mapping = pd.DataFrame({
            "public_id": np.concatenate([treated["public_id"].astype(str).values,
                                         matched_control["public_id"].astype(str).values]),
            "fake_week": np.concatenate([fake_weeks, fake_weeks]),
            "group": ["treated"] * len(treated) + ["control"] * len(matched_control),
        })
        m = panel_sub.merge(mapping, on="public_id", how="inner")
        m["event_time"] = m["observed_week_idx"].astype(int) - m["fake_week"]
        m = m[(m["event_time"] >= -WINDOW) & (m["event_time"] < WINDOW)]
        m["period"] = np.where(m["event_time"] < 0, "pre", "post")
        agg = m.groupby(["public_id", "group", "period"])["sales_log"].mean().unstack("period")
        if "pre" not in agg.columns or "post" not in agg.columns:
            continue
        agg = agg.dropna(subset=["pre", "post"]).reset_index()
        agg["delta"] = agg["post"] - agg["pre"]
        att = (agg[agg["group"] == "treated"]["delta"].mean()
               - agg[agg["group"] == "control"]["delta"].mean())
        results.append({"round": r, "att_placebo": att})
    dfp = pd.DataFrame(results)
    dfp.to_csv(cfg.TABLE_DIR / "did_placebo.csv", index=False, encoding="utf-8-sig")

    print(f"Placebo ATT mean: {dfp['att_placebo'].mean():+.4f}")
    print(f"Placebo ATT std:  {dfp['att_placebo'].std():.4f}")
    print(f"Placebo ATT range: [{dfp['att_placebo'].min():+.4f}, {dfp['att_placebo'].max():+.4f}]")
    real_att = 0.117
    z = (real_att - dfp['att_placebo'].mean()) / (dfp['att_placebo'].std() + 1e-9)
    print(f"Real ATT vs placebo distribution: z = {z:.2f}σ  (>2 = real effect is robust)")
    return dfp


def main():
    panel, gc, feats = load_inputs()
    print(f"[05b] panel {panel.shape}, gc {gc.shape}, feats {feats.shape}")

    treated, matched_control = matched_pairs(gc, feats)
    print(f"[05b] matched: {len(treated)} treated, {len(matched_control)} control")

    if len(treated) > 3000:
        rng = np.random.RandomState(cfg.SEED)
        pick = rng.choice(len(treated), 3000, replace=False)
        treated = treated.iloc[pick].reset_index(drop=True)
        matched_control = matched_control.iloc[pick].reset_index(drop=True)
        print(f"[05b] subsampled to {len(treated)} for event study efficiency")

    event_df = build_event_panel(panel, treated, matched_control)
    print(f"[05b] event panel: {event_df.shape}")
    pre, post, did, p_pre = event_study_plot(event_df, cfg.FIGURE_DIR / "fig14_did_event_study.png")

    placebo_df = placebo_test(panel, treated, matched_control)

    summary = pd.DataFrame([{
        "pre_mean_diff": pre,
        "post_mean_diff": post,
        "did_estimate": did,
        "pre_trend_pvalue": p_pre,
        "placebo_mean": placebo_df["att_placebo"].mean(),
        "placebo_std": placebo_df["att_placebo"].std(),
        "real_att_zscore_vs_placebo": (did - placebo_df["att_placebo"].mean()) /
                                       (placebo_df["att_placebo"].std() + 1e-9),
    }])
    summary.to_csv(cfg.TABLE_DIR / "did_event_study_summary.csv", index=False, encoding="utf-8-sig")
    print("\n=== Summary ===")
    print(summary.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
