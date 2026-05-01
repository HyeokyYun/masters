"""Step 01 — Build calendar-aligned feature/target panels.

For each WindowSpec(start_year, start_month, window_months, target_offset),
emit a parquet at outputs/tables/panels/panel_<combo_id>.parquet containing:

  public_id  segment  date_id  observed_week_idx  sales_card  customer
  customer_new  sales_delivery  before_noon_sales  weekend_sales

  segment ∈ {"feature", "target"}.

Also writes outputs/tables/panel_summary.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg  # noqa: E402
import utils_panel as up  # noqa: E402


USE_COLS = [
    "public_id",
    "date_id",
    "sales_card",
    "customer",
    "customer_new",
    "sales_delivery",
    "before_noon_sales",
    "weekend_sales",
]


def _build_one(weekly: pd.DataFrame, spec: up.WindowSpec) -> dict:
    feat_panel = up.slice_window(weekly, spec.feature_start, spec.feature_end).copy()
    tgt_panel = up.slice_window(weekly, spec.target_start, spec.target_end).copy()
    if feat_panel.empty or tgt_panel.empty:
        return {"combo_id": spec.combo_id, "n_stores": 0, "skipped": "empty_window"}

    exp_feat = up.expected_weeks_in(spec.feature_start, spec.feature_end)
    exp_tgt = up.expected_weeks_in(spec.target_start, spec.target_end)
    min_feat = max(2, int(np.ceil(exp_feat * cfg.MIN_FEATURE_WEEKS_RATIO)))
    min_tgt = max(2, int(np.ceil(exp_tgt * cfg.MIN_TARGET_WEEKS_RATIO)))

    feat_cnt = feat_panel.groupby("public_id")["date_id"].nunique()
    tgt_cnt = tgt_panel.groupby("public_id")["date_id"].nunique()

    feat_sales = feat_panel.groupby("public_id")["sales_card"].sum()
    tgt_sales = tgt_panel.groupby("public_id")["sales_card"].sum()

    keep = (feat_cnt >= min_feat) & (tgt_cnt >= min_tgt)
    keep = keep & (feat_sales > 0) & (tgt_sales > 0)
    keep_ids = keep[keep].index

    if len(keep_ids) == 0:
        return {"combo_id": spec.combo_id, "n_stores": 0, "skipped": "no_stores"}

    feat_panel = feat_panel[feat_panel["public_id"].isin(keep_ids)].copy()
    tgt_panel = tgt_panel[tgt_panel["public_id"].isin(keep_ids)].copy()
    feat_panel["segment"] = "feature"
    tgt_panel["segment"] = "target"

    panel = pd.concat([feat_panel, tgt_panel], ignore_index=True)
    panel = panel.sort_values(["public_id", "segment", "date_id"]).reset_index(drop=True)
    panel["observed_week_idx"] = panel.groupby(["public_id", "segment"]).cumcount()

    panel["sales_card"] = panel["sales_card"].clip(lower=0)
    for c in ["customer", "customer_new", "sales_delivery", "before_noon_sales", "weekend_sales"]:
        if c in panel.columns:
            panel[c] = panel[c].fillna(0)

    panel.to_parquet(up.panel_path(spec.combo_id), index=False)

    return {
        "combo_id": spec.combo_id,
        "start_year": spec.start_year,
        "start_month": spec.start_month,
        "window_months": spec.window_months,
        "target_offset": spec.target_offset,
        "feature_start": str(spec.feature_start.date()),
        "feature_end": str(spec.feature_end.date()),
        "target_start": str(spec.target_start.date()),
        "target_end": str(spec.target_end.date()),
        "n_stores": int(len(keep_ids)),
        "exp_feat_weeks": int(exp_feat),
        "exp_tgt_weeks": int(exp_tgt),
        "skipped": "",
    }


def main() -> None:
    print("[01] loading weekly ...")
    weekly = up.load_weekly(USE_COLS)
    weekly = weekly[(weekly["date_id"] >= cfg.DATA_START) & (weekly["date_id"] <= cfg.DATA_END)]
    n_stores = weekly["public_id"].nunique()
    n_weeks = weekly["date_id"].nunique()
    print(f"[01] weekly rows={len(weekly):,} stores={n_stores:,} weeks={n_weeks}")

    combos = up.enumerate_combos()
    print(f"[01] enumerated combos={len(combos)}")

    rows = []
    for i, spec in enumerate(combos):
        info = _build_one(weekly, spec)
        rows.append(info)
        marker = "skip" if info.get("skipped") else "ok  "
        print(
            f"[01] {marker} {i+1:3d}/{len(combos)} {spec.combo_id} "
            f"feat={info.get('feature_start','-')}..{info.get('feature_end','-')} "
            f"tgt={info.get('target_start','-')}..{info.get('target_end','-')} "
            f"stores={info.get('n_stores', 0):,}"
        )

    summary = pd.DataFrame(rows)
    summary.to_csv(cfg.TABLE_DIR / "panel_summary.csv", index=False, encoding="utf-8-sig")
    kept = summary[summary["n_stores"] > 0]
    print(f"[01] kept combos: {len(kept)} / {len(summary)}")
    print(f"[01] saved: {cfg.TABLE_DIR / 'panel_summary.csv'}")


if __name__ == "__main__":
    main()
