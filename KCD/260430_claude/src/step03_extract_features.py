"""Step 03 — Variable-window feature extraction (feature segment only).

Adapted from top_tier/src/step03_prediction_model.py:build_feature_matrix,
but uses date_id-based pivoting and length-conditional features (skips
slope_1_10 / ma15_slope etc. when feature window is too short).

Outputs:
  outputs/tables/features/features_<combo_id>.parquet
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg  # noqa: E402
import utils_panel as up  # noqa: E402


def _pivot(panel: pd.DataFrame, value: str) -> pd.DataFrame:
    return panel.pivot_table(index="public_id", columns="date_id", values=value, aggfunc="mean")


def _row_slope_slice(arr: np.ndarray, start: int, end: int) -> np.ndarray:
    return up.row_slopes(arr[:, start:end])


def _build_features(panel_feat: pd.DataFrame) -> pd.DataFrame:
    panel_feat = panel_feat.sort_values(["public_id", "date_id"])

    sales = _pivot(panel_feat, "sales_card").sort_index(axis=1)
    cust = _pivot(panel_feat, "customer").reindex_like(sales)
    cust_new = _pivot(panel_feat, "customer_new").reindex_like(sales)
    delivery = _pivot(panel_feat, "sales_delivery").reindex_like(sales)
    before_noon = _pivot(panel_feat, "before_noon_sales").reindex_like(sales)
    weekend = _pivot(panel_feat, "weekend_sales").reindex_like(sales)

    n_cols = sales.shape[1]
    valid = sales.notna().sum(axis=1) >= max(2, int(np.ceil(n_cols * 0.5)))
    sales = sales.loc[valid]
    cust = cust.loc[valid]
    cust_new = cust_new.loc[valid]
    delivery = delivery.loc[valid]
    before_noon = before_noon.loc[valid]
    weekend = weekend.loc[valid]

    if sales.empty:
        return pd.DataFrame()

    s = np.log1p(np.where(np.isfinite(sales.to_numpy()), sales.to_numpy(), 0.0))
    s = np.where(np.isfinite(sales.to_numpy()), s, np.nan)
    raw = sales.to_numpy(dtype=float)
    c = cust.to_numpy(dtype=float)
    cn = cust_new.to_numpy(dtype=float)
    d = delivery.fillna(0).to_numpy(dtype=float)
    bn = before_noon.to_numpy(dtype=float)
    wk = weekend.to_numpy(dtype=float)
    ids = sales.index.astype(str).to_numpy()
    n = s.shape[1]

    with np.errstate(divide="ignore", invalid="ignore"):
        nc_ratio = np.where(c > 0, cn / c, np.nan)
        del_ratio = np.where(raw > 0, d / raw, 0.0)
        bn_ratio = np.where(raw > 0, bn / raw, 0.0)
        wk_ratio = np.where(raw > 0, wk / raw, 0.0)

    out: dict[str, np.ndarray] = {"public_id": ids}

    out["sales_mean"] = np.nanmean(s, axis=1)
    out["sales_std"] = np.nanstd(s, axis=1)
    out["sales_median"] = np.nanmedian(s, axis=1)
    out["sales_min"] = np.nanmin(s, axis=1)
    out["sales_max"] = np.nanmax(s, axis=1)
    out["sales_range"] = out["sales_max"] - out["sales_min"]
    out["sales_cv"] = out["sales_std"] / (np.abs(out["sales_mean"]) + 1e-9)

    out["slope_all"] = up.row_slopes(s)

    if n >= 6:
        third = max(2, n // 3)
        out["slope_1_3"] = _row_slope_slice(s, 0, third)
        out["slope_2_3"] = _row_slope_slice(s, third, 2 * third)
        out["slope_3_3"] = _row_slope_slice(s, 2 * third, n)
        out["slope_accel"] = out["slope_3_3"] - out["slope_1_3"]

    half = max(1, n // 2)
    out["slope_first_half"] = _row_slope_slice(s, 0, half)
    out["slope_second_half"] = _row_slope_slice(s, half, n)
    out["slope_half_diff"] = out["slope_second_half"] - out["slope_first_half"]

    for win in [4, 8]:
        if n >= win:
            ma = pd.DataFrame(s).rolling(win, axis=1, min_periods=max(1, win // 2)).mean().to_numpy()
            out[f"ma{win}_slope"] = up.row_slopes(ma)
            out[f"ma{win}_std"] = np.nanstd(ma, axis=1)
            roll_std = pd.DataFrame(s).rolling(win, axis=1, min_periods=max(1, win // 2)).std().to_numpy()
            denom = np.nanmean(s, axis=1) + 1e-9
            out[f"vol_w{win}"] = np.nanmean(roll_std, axis=1) / denom

    out["nc_mean"] = np.nanmean(nc_ratio, axis=1)
    out["nc_std"] = np.nanstd(nc_ratio, axis=1)
    out["nc_slope"] = up.row_slopes(nc_ratio)
    if n >= 4:
        out["nc_last_q"] = np.nanmean(nc_ratio[:, -max(1, n // 4):], axis=1)
        out["nc_first_q"] = np.nanmean(nc_ratio[:, : max(1, n // 4)], axis=1)
        out["nc_delta"] = out["nc_last_q"] - out["nc_first_q"]

    cust_log = np.log1p(c)
    out["cust_slope"] = up.row_slopes(cust_log)
    out["cust_mean"] = np.nanmean(cust_log, axis=1)
    out["cust_cv"] = np.nanstd(cust_log, axis=1) / (np.nanmean(cust_log, axis=1) + 1e-9)

    out["del_mean"] = np.nanmean(del_ratio, axis=1)
    out["del_slope"] = up.row_slopes(del_ratio)
    out["bn_mean"] = np.nanmean(bn_ratio, axis=1)
    out["wk_mean"] = np.nanmean(wk_ratio, axis=1)

    out["q25"] = np.nanquantile(s, 0.25, axis=1)
    out["q50"] = np.nanquantile(s, 0.50, axis=1)
    out["q75"] = np.nanquantile(s, 0.75, axis=1)
    out["iqr"] = out["q75"] - out["q25"]

    if n >= 3:
        diff = np.diff(s, axis=1)
        out["diff_mean"] = np.nanmean(diff, axis=1)
        out["diff_std"] = np.nanstd(diff, axis=1)
        out["diff_max_abs"] = np.nanmax(np.abs(diff), axis=1)
        zc = np.sum(np.diff(np.sign(np.nan_to_num(diff, nan=0.0)), axis=1) != 0, axis=1)
        out["zero_cross"] = zc

    out["n_feat_weeks"] = np.isfinite(s).sum(axis=1)

    df = pd.DataFrame(out)
    for c in df.columns:
        if c == "public_id":
            continue
        df[c] = df[c].replace([np.inf, -np.inf], np.nan)
    df = df.fillna(0)
    return df


def _process(spec: up.WindowSpec) -> int:
    p_path = up.panel_path(spec.combo_id)
    if not p_path.exists():
        return 0
    panel = pd.read_parquet(p_path)
    feat_panel = panel[panel["segment"] == "feature"]
    feats = _build_features(feat_panel)
    if feats.empty:
        return 0
    feats.to_parquet(up.feature_path(spec.combo_id), index=False)
    return len(feats)


def main() -> None:
    combos = up.enumerate_combos()
    rows = []
    for i, spec in enumerate(combos):
        n = _process(spec)
        if n == 0:
            continue
        rows.append({"combo_id": spec.combo_id, "n_stores": n})
        print(f"[03] {i+1:3d}/{len(combos)} {spec.combo_id} n={n:,}")
    summary = pd.DataFrame(rows)
    summary.to_csv(cfg.TABLE_DIR / "feature_summary.csv", index=False, encoding="utf-8-sig")
    print(f"[03] saved: {cfg.TABLE_DIR / 'feature_summary.csv'}")


if __name__ == "__main__":
    main()
