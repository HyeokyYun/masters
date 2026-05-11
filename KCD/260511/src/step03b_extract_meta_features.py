"""Step 03b — Meta feature extraction for each panel (Phase 2.2 / A2).

Joins each panel's stores with `meta.csv` and produces:
  - tenure_months  : feature-window-aligned 업력 (months between open_month and panel.feature_start)
  - tenure_log     : log1p(tenure_months) for skewness
  - prop_age_*     : one-hot of proprietor age bucket (10대/20대/30대/40대/50대/60대)
  - has_delivery   : 0/1 from delivery_link
  - sqsize_log     : log1p(business_square_size), winsorized 99th percentile within panel
  - sigungu_te     : target-encoded sigungu (mean-encoding of slope_target_norm, smoothed)
  - kclass_te      : target-encoded kostat_class

Per-panel features are saved as parquet next to features_<combo_id>.parquet.

Outputs:
  outputs/tables/features_meta/features_meta_<combo_id>.parquet
  outputs/tables/feature_meta_summary.csv

Note: sigungu_te / kclass_te use leave-one-fold-out style smoothed mean later
in step05b. For now we save *raw* slope_target_norm-conditioned mean per
sigungu computed from the full panel — for downstream this becomes a soft
prior; we will refit per-fold inside the modeling step to avoid leakage.
Here we save the categorical column itself so step05b can target-encode
properly.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg  # noqa: E402
import utils_panel as up  # noqa: E402

META_OUT = cfg.TABLE_DIR / "features_meta"
META_OUT.mkdir(parents=True, exist_ok=True)

AGE_BUCKETS = ["10대", "20대", "30대", "40대", "50대", "60대"]


def _months_between(later: pd.Timestamp, earlier: pd.Series) -> np.ndarray:
    earl = pd.to_datetime(earlier, errors="coerce")
    delta = (later.to_numpy() - earl.values) / np.timedelta64(1, "D")
    return (delta / 30.4375).astype(float)


def _winsor_log(x: pd.Series, q: float = 0.99) -> np.ndarray:
    arr = pd.to_numeric(x, errors="coerce").to_numpy(dtype=float)
    cap = np.nanquantile(arr, q) if np.isfinite(arr).any() else 0.0
    arr = np.where(np.isfinite(arr), np.clip(arr, 0.0, cap), 0.0)
    return np.log1p(arr)


def _build_one(combo_id: str, meta: pd.DataFrame) -> dict | None:
    p_path = up.panel_path(combo_id)
    l_path = up.label_path(combo_id)
    if not (p_path.exists() and l_path.exists()):
        return None
    panel = pd.read_parquet(p_path, columns=["public_id", "date_id", "segment"])
    panel["public_id"] = panel["public_id"].astype(str)
    feat_seg = panel[panel["segment"] == "feature"]
    if feat_seg.empty:
        return None
    feature_start = pd.Timestamp(feat_seg["date_id"].min())
    ids = pd.DataFrame({"public_id": feat_seg["public_id"].unique()})

    df = ids.merge(meta, on="public_id", how="left")
    tenure = _months_between(feature_start, df["open_month"])
    df["tenure_months"] = np.where(np.isfinite(tenure) & (tenure > 0), tenure, 0.0)
    df["tenure_log"] = np.log1p(df["tenure_months"])

    for b in AGE_BUCKETS:
        df[f"prop_age_{b}"] = (df["age"] == b).astype(int)
    df["prop_age_unknown"] = df["age"].isna().astype(int)

    df["has_delivery"] = pd.to_numeric(df["delivery_link"], errors="coerce").fillna(0).astype(int)
    df["sqsize_log"] = _winsor_log(df["business_square_size"])

    keep = [
        "public_id", "tenure_months", "tenure_log",
        *[f"prop_age_{b}" for b in AGE_BUCKETS], "prop_age_unknown",
        "has_delivery", "sqsize_log",
        # categorical kept for fold-aware target encoding downstream
        "sigungu", "kostat_class",
    ]
    out = df[keep].copy()

    out_path = META_OUT / f"features_meta_{combo_id}.parquet"
    out.to_parquet(out_path, index=False)
    return {
        "combo_id": combo_id,
        "n_stores": int(len(out)),
        "tenure_mean": float(out["tenure_months"].mean()),
        "tenure_p50": float(out["tenure_months"].median()),
        "has_delivery_ratio": float(out["has_delivery"].mean()),
        "missing_age_ratio": float(out["prop_age_unknown"].mean()),
        "missing_sigungu_ratio": float(out["sigungu"].isna().mean()),
    }


def main() -> None:
    meta = up.load_meta()
    meta["public_id"] = meta["public_id"].astype(str)
    rows = []
    combos = up.enumerate_combos()
    for i, spec in enumerate(combos):
        info = _build_one(spec.combo_id, meta)
        if info is None:
            continue
        rows.append(info)
        if (i + 1) % 20 == 0:
            print(f"[03b] {i+1}/{len(combos)} done")
    df = pd.DataFrame(rows)
    summary_path = cfg.TABLE_DIR / "feature_meta_summary.csv"
    df.to_csv(summary_path, index=False, encoding="utf-8-sig")
    print(f"[03b] saved: {summary_path} (rows={len(df)})")
    if not df.empty:
        print(df.head().to_string(index=False))


if __name__ == "__main__":
    main()
