"""Step 02 — Calendar-aligned G/S/D relabeling.

For each combo panel from step01, compute the per-store slope of the
target-window sales sequence (normalized by the store's overall mean across
feature+target windows so slope magnitudes are comparable). Then bucket into
Growth / Stable / Decline using ±0.5 * cross-store sigma.

Outputs:
  outputs/tables/labels/labels_<combo_id>.parquet  (public_id, slope_target_norm,
                                                     outcome_3, n_target_weeks)
  outputs/tables/label_distribution.csv  (combo_id × class counts/ratios)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg  # noqa: E402
import utils_panel as up  # noqa: E402


def _label_one(spec: up.WindowSpec) -> dict | None:
    p_path = up.panel_path(spec.combo_id)
    if not p_path.exists():
        return None
    panel = pd.read_parquet(p_path)
    if panel.empty:
        return None

    # per-store overall mean (feature+target) for normalization scale
    store_mean = panel.groupby("public_id")["sales_card"].mean().replace(0, np.nan)
    store_mean = store_mean.replace(0, np.nan)

    target = panel[panel["segment"] == "target"].copy()
    if target.empty:
        return None

    target = target.sort_values(["public_id", "date_id"])
    target["sales_norm"] = target["sales_card"] / target["public_id"].map(store_mean)

    pivot = target.pivot_table(
        index="public_id",
        columns="date_id",
        values="sales_norm",
        aggfunc="mean",
    ).sort_index(axis=1)

    arr = pivot.to_numpy(dtype=float)
    n_weeks = np.isfinite(arr).sum(axis=1)
    slopes = up.row_slopes(arr)

    sigma = float(np.nanstd(slopes))
    thr = cfg.SLOPE_THRESHOLD_SIGMA * sigma if sigma > 0 else 0.0
    outcome = np.where(slopes > thr, "Growth", np.where(slopes < -thr, "Decline", "Stable"))

    labels = pd.DataFrame(
        {
            "public_id": pivot.index.astype(str),
            "slope_target_norm": slopes,
            "outcome_3": outcome,
            "n_target_weeks": n_weeks,
        }
    )
    labels = labels[labels["n_target_weeks"] >= 3].reset_index(drop=True)
    labels.to_parquet(up.label_path(spec.combo_id), index=False)

    counts = labels["outcome_3"].value_counts()
    return {
        "combo_id": spec.combo_id,
        "n_stores": int(len(labels)),
        "sigma_slope": sigma,
        "threshold": thr,
        "Growth": int(counts.get("Growth", 0)),
        "Stable": int(counts.get("Stable", 0)),
        "Decline": int(counts.get("Decline", 0)),
        "growth_ratio": float(counts.get("Growth", 0) / max(1, len(labels))),
        "stable_ratio": float(counts.get("Stable", 0) / max(1, len(labels))),
        "decline_ratio": float(counts.get("Decline", 0) / max(1, len(labels))),
    }


def main() -> None:
    combos = up.enumerate_combos()
    rows = []
    for i, spec in enumerate(combos):
        info = _label_one(spec)
        if info is None:
            continue
        rows.append(info)
        print(
            f"[02] {i+1:3d}/{len(combos)} {spec.combo_id} "
            f"n={info['n_stores']:,} thr={info['threshold']:.4f} "
            f"G={info['growth_ratio']:.3f} S={info['stable_ratio']:.3f} D={info['decline_ratio']:.3f}"
        )

    dist = pd.DataFrame(rows)
    dist.to_csv(cfg.TABLE_DIR / "label_distribution.csv", index=False, encoding="utf-8-sig")
    print(f"[02] saved: {cfg.TABLE_DIR / 'label_distribution.csv'}")
    print(dist[["combo_id", "n_stores", "growth_ratio", "stable_ratio", "decline_ratio"]].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
