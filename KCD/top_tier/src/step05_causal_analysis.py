"""Step 05 — 골든 크로스 인과 분석.

(A) Granger causality: 점포별 신규 고객 유입률 → 매출의 선행 관계 검정 (VAR)
(B) Propensity Score Matching + Difference-in-Differences:
    Treatment = 변곡점 전 골든 크로스(신규고객 급등) 발생 점포
    Control   = 유사 pre-trend를 가지지만 골든 크로스 미발생 점포
(C) Panel Two-way Fixed Effects Regression: lagged nc_rate → sales growth

Output:
  outputs/tables/granger_store_level.csv
  outputs/tables/granger_summary.csv
  outputs/tables/did_psm_ate.csv
  outputs/tables/fe_panel_regression.csv
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from statsmodels.tools.sm_exceptions import InfeasibleTestError
from statsmodels.tsa.stattools import grangercausalitytests

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg  # noqa: E402


def load_panel():
    panel = pd.read_parquet(cfg.PANEL_PATH)
    panel["public_id"] = panel["public_id"].astype(str)
    panel = panel.sort_values(["public_id", "observed_week_idx"])
    return panel


def compute_nc_ratio(panel: pd.DataFrame) -> pd.DataFrame:
    panel = panel.copy()
    denom = panel["customer"].replace(0, np.nan)
    panel["nc_ratio"] = panel["customer_new"] / denom
    return panel


def granger_store_level(panel: pd.DataFrame, min_weeks: int = 40, maxlag: int = 4, sample: int = 3000):
    """Pick stores with enough weeks, run bidirectional Granger tests."""
    panel = panel[panel["customer"] > 0].copy()
    panel["sales_log"] = np.log1p(panel["sales_card"])
    panel["nc_ratio"] = panel["nc_ratio"].fillna(0.0)

    counts = panel.groupby("public_id").size()
    eligible = counts[counts >= min_weeks].index
    print(f"[05-A] Eligible stores for Granger test: {len(eligible)}")

    rng = np.random.RandomState(cfg.SEED)
    if len(eligible) > sample:
        pick = rng.choice(eligible, sample, replace=False)
    else:
        pick = eligible.values

    rows = []
    for pid in pick:
        sub = panel[panel["public_id"] == pid]
        if sub["nc_ratio"].std() < 1e-6 or sub["sales_log"].std() < 1e-6:
            continue
        try:
            ts_nc_to_sales = sub[["sales_log", "nc_ratio"]].dropna().diff().dropna()
            ts_sales_to_nc = sub[["nc_ratio", "sales_log"]].dropna().diff().dropna()
            if len(ts_nc_to_sales) < maxlag + 5:
                continue
            res1 = grangercausalitytests(ts_nc_to_sales, maxlag=maxlag, verbose=False)
            res2 = grangercausalitytests(ts_sales_to_nc, maxlag=maxlag, verbose=False)
            p1 = res1[maxlag][0]["ssr_ftest"][1]
            p2 = res2[maxlag][0]["ssr_ftest"][1]
            rows.append({"public_id": pid, "p_nc_to_sales": p1, "p_sales_to_nc": p2})
        except (InfeasibleTestError, ValueError, np.linalg.LinAlgError):
            continue

    df = pd.DataFrame(rows)
    df.to_csv(cfg.TABLE_DIR / "granger_store_level.csv", index=False, encoding="utf-8-sig")

    if df.empty:
        return df

    summary = {
        "n_stores_tested": len(df),
        "nc_causes_sales_sig_pct": (df["p_nc_to_sales"] < 0.05).mean() * 100,
        "sales_causes_nc_sig_pct": (df["p_sales_to_nc"] < 0.05).mean() * 100,
        "asymmetry_nc_only_pct": ((df["p_nc_to_sales"] < 0.05) & (df["p_sales_to_nc"] >= 0.05)).mean() * 100,
        "asymmetry_sales_only_pct": ((df["p_nc_to_sales"] >= 0.05) & (df["p_sales_to_nc"] < 0.05)).mean() * 100,
        "both_sig_pct": ((df["p_nc_to_sales"] < 0.05) & (df["p_sales_to_nc"] < 0.05)).mean() * 100,
    }
    pd.DataFrame([summary]).to_csv(cfg.TABLE_DIR / "granger_summary.csv", index=False, encoding="utf-8-sig")
    print(f"[05-A] Granger summary: {summary}")
    return df


def detect_golden_cross(panel: pd.DataFrame, percentile: float = 0.3) -> pd.DataFrame:
    """점포 내부에서 nc_ratio의 상승 규모를 측정한 뒤 상위 percentile 분위의 점포를 treated로.
    측정치: (post-peak 4w mean) - (pre 8w mean) 를 pre 8w mean+ε 으로 정규화.
    """
    panel = panel.copy()
    panel["nc_ratio"] = panel["nc_ratio"].fillna(0.0)

    rows = []
    for pid, g in panel.groupby("public_id", observed=True, sort=False):
        g = g.sort_values("observed_week_idx")
        if len(g) < 25:
            continue
        nc = g["nc_ratio"].to_numpy()
        weeks = g["observed_week_idx"].to_numpy()
        base = np.nanmean(nc[:8]) + 1e-6
        roll4 = pd.Series(nc).rolling(4, min_periods=2).mean().to_numpy()
        search = roll4[10:]
        if len(search) == 0 or np.all(np.isnan(search)):
            continue
        gc_idx_local = int(np.nanargmax(search))
        gc_idx = gc_idx_local + 10
        peak = float(roll4[gc_idx])
        delta = (peak - base) / base
        rows.append({
            "public_id": pid,
            "gc_delta": float(delta),
            "gc_week": int(weeks[gc_idx]),
            "pre_nc_avg": float(base),
            "peak_nc_avg": peak,
        })
    df = pd.DataFrame(rows)
    if df.empty:
        print("[05-B] no valid stores for GC detection")
        return df
    thr = df["gc_delta"].quantile(1 - percentile)
    df["has_gc"] = (df["gc_delta"] >= thr).astype(int)
    df.to_csv(cfg.TABLE_DIR / "golden_cross_detection.csv", index=False, encoding="utf-8-sig")
    print(f"[05-B] Golden cross (top {percentile*100:.0f}% by delta≥{thr:.2f}): "
          f"{df['has_gc'].mean()*100:.1f}% of {len(df)} stores")
    return df


def run_psm_did(panel: pd.DataFrame, gc_df: pd.DataFrame, feats: pd.DataFrame,
                window: int = 8):
    """매칭 + DiD: gc 발생 전 8주(pre) vs 발생 후 8주(post) 매출 로그 변화.
    Control 그룹은 매칭된 비발생 점포들의 same relative weeks."""
    print("[05-B] PSM + DiD analysis ...")
    feats = feats.copy()
    feats["public_id"] = feats["public_id"].astype(str)

    merged = gc_df.merge(feats[["public_id", "slope_early_mm", "cv", "nc_rate",
                                 "r2_early", "mdd"]], on="public_id", how="inner")
    merged = merged.dropna()

    covariates = ["slope_early_mm", "cv", "nc_rate", "r2_early", "mdd"]
    scaler = StandardScaler()
    Xc = scaler.fit_transform(merged[covariates])
    y = merged["has_gc"].values
    lr = LogisticRegression(max_iter=1000)
    lr.fit(Xc, y)
    merged["pscore"] = lr.predict_proba(Xc)[:, 1]

    treated = merged[merged["has_gc"] == 1]
    control = merged[merged["has_gc"] == 0]
    if len(treated) == 0 or len(control) == 0:
        print("[05-B] treatment/control empty — abort PSM")
        return None

    nn = NearestNeighbors(n_neighbors=1)
    nn.fit(control[["pscore"]].values)
    _, idx = nn.kneighbors(treated[["pscore"]].values)
    matched_control = control.iloc[idx.flatten()].reset_index(drop=True)
    treated_r = treated.reset_index(drop=True)

    def sales_change(pid, gc_week, w=window):
        g = panel[panel["public_id"] == pid].sort_values("observed_week_idx")
        sales = np.log1p(g["sales_card"].to_numpy())
        weeks = g["observed_week_idx"].to_numpy()
        if gc_week < 0:
            gc_week = int(np.median(weeks))
        pre_mask = (weeks >= gc_week - w) & (weeks < gc_week)
        post_mask = (weeks >= gc_week) & (weeks < gc_week + w)
        if pre_mask.sum() < 3 or post_mask.sum() < 3:
            return np.nan, np.nan
        return float(np.nanmean(sales[pre_mask])), float(np.nanmean(sales[post_mask]))

    rows = []
    for _, tr in treated_r.iterrows():
        pre_t, post_t = sales_change(tr["public_id"], int(tr["gc_week"]))
        if np.isnan(pre_t):
            continue
        rows.append({"public_id": tr["public_id"], "group": "treated",
                    "pre_sales_log": pre_t, "post_sales_log": post_t})
    for i, (_, ct) in enumerate(matched_control.iterrows()):
        gc_week_for_ct = int(treated_r.iloc[i]["gc_week"])
        pre_c, post_c = sales_change(ct["public_id"], gc_week_for_ct)
        if np.isnan(pre_c):
            continue
        rows.append({"public_id": ct["public_id"], "group": "control",
                    "pre_sales_log": pre_c, "post_sales_log": post_c})

    did_df = pd.DataFrame(rows)
    did_df["delta"] = did_df["post_sales_log"] - did_df["pre_sales_log"]
    att = (did_df[did_df["group"] == "treated"]["delta"].mean()
           - did_df[did_df["group"] == "control"]["delta"].mean())
    from scipy import stats as _stats
    tt, pp = _stats.ttest_ind(
        did_df[did_df["group"] == "treated"]["delta"].dropna(),
        did_df[did_df["group"] == "control"]["delta"].dropna(),
        equal_var=False,
    )

    result = {"ATT": float(att), "t_stat": float(tt), "p_value": float(pp),
              "n_treated": int((did_df["group"] == "treated").sum()),
              "n_control": int((did_df["group"] == "control").sum())}
    pd.DataFrame([result]).to_csv(cfg.TABLE_DIR / "did_psm_ate.csv", index=False, encoding="utf-8-sig")
    print(f"[05-B] DiD ATT = {att:+.4f} (log-sales), t={tt:.3f}, p={pp:.4g}")
    return result


def panel_fe_regression(panel: pd.DataFrame, max_stores: int = 10000):
    """Two-way FE with lagged nc_ratio."""
    print("[05-C] Panel FE regression ...")
    panel = panel.copy()
    panel["sales_log"] = np.log1p(panel["sales_card"])
    panel["nc_ratio"] = panel["nc_ratio"].fillna(0.0)
    panel = panel.sort_values(["public_id", "observed_week_idx"])

    panel["nc_l1"] = panel.groupby("public_id")["nc_ratio"].shift(1)
    panel["nc_l2"] = panel.groupby("public_id")["nc_ratio"].shift(2)
    panel["nc_l4"] = panel.groupby("public_id")["nc_ratio"].shift(4)
    panel["sales_lag1"] = panel.groupby("public_id")["sales_log"].shift(1)
    panel = panel.dropna(subset=["nc_l1", "nc_l2", "nc_l4", "sales_lag1"])

    store_ids = panel["public_id"].unique()
    rng = np.random.RandomState(cfg.SEED)
    if len(store_ids) > max_stores:
        pick = rng.choice(store_ids, max_stores, replace=False)
        panel = panel[panel["public_id"].isin(pick)]

    panel["sales_demean"] = panel.groupby("public_id")["sales_log"].transform(lambda x: x - x.mean())
    panel["time_demean"] = panel.groupby("observed_week_idx")["sales_log"].transform(lambda x: x - x.mean())
    panel["y_twoway"] = panel["sales_log"] - panel.groupby("public_id")["sales_log"].transform("mean") \
        - panel.groupby("observed_week_idx")["sales_log"].transform("mean") + panel["sales_log"].mean()

    X_cols = ["nc_l1", "nc_l2", "nc_l4", "sales_lag1"]
    for c in X_cols:
        panel[f"{c}_fe"] = panel[c] - panel.groupby("public_id")[c].transform("mean") \
            - panel.groupby("observed_week_idx")[c].transform("mean") + panel[c].mean()

    import statsmodels.api as sm
    X = sm.add_constant(panel[[f"{c}_fe" for c in X_cols]])
    y = panel["y_twoway"]
    model = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": panel["public_id"]})
    summary = pd.DataFrame({
        "coef": model.params, "std_err": model.bse,
        "t": model.tvalues, "p": model.pvalues,
        "ci_lower": model.conf_int()[0], "ci_upper": model.conf_int()[1],
    })
    summary["n_obs"] = len(panel)
    summary["n_stores"] = panel["public_id"].nunique()
    summary.to_csv(cfg.TABLE_DIR / "fe_panel_regression.csv", encoding="utf-8-sig")
    print(summary)
    return summary


def main():
    panel = load_panel()
    panel = compute_nc_ratio(panel)
    feats = pd.read_csv(cfg.FEATURES_PATH)

    granger_store_level(panel)
    gc_df = detect_golden_cross(panel)
    run_psm_did(panel, gc_df, feats)
    panel_fe_regression(panel)


if __name__ == "__main__":
    main()
