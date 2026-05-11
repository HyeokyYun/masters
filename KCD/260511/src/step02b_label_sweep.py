"""Step 02b — Label definition sweep (Phase 0).

For each of the 14 representative panels (PANELS_TO_RUN), re-bucket the
existing slope_target_norm into G/S/D under multiple sigma thresholds and
also train a tiny RF baseline so we can pick the labeling that gives the
best (macro_F1, class balance, cross-panel stability) trade-off.

Also runs a regression baseline (predict slope_target_norm directly) so we
can compare regression-then-bucket vs direct classification.

Outputs:
  outputs/tables/label_definition_sweep.csv
  outputs/tables/label_stability_pairs.csv
  docs/label_choice_rationale.md
"""
from __future__ import annotations

import sys
import warnings
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import f1_score, mean_absolute_error, r2_score
from sklearn.model_selection import KFold, StratifiedKFold

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg  # noqa: E402
import utils_panel as up  # noqa: E402

PANELS = [
    ("sy2021_sm01_w3m_off1", "Jan-Mar 2021 → Jan-Mar 2022"),
    ("sy2021_sm03_w3m_off1", "Mar-May 2021 → Mar-May 2022"),
    ("sy2021_sm05_w3m_off1", "May-Jul 2021 → May-Jul 2022"),
    ("sy2021_sm09_w3m_off1", "Sep-Nov 2021 → Sep-Nov 2022"),
    ("sy2022_sm01_w3m_off1", "Jan-Mar 2022 → Jan-Mar 2023"),
    ("sy2022_sm03_w3m_off1", "Mar-May 2022 → Mar-May 2023"),
    ("sy2022_sm05_w3m_off1", "May-Jul 2022 → May-Jul 2023"),
    ("sy2021_sm01_w7m_off1", "Jan-Jul 2021 → Jan-Jul 2022 (7m)"),
    ("sy2021_sm01_w7m_off2", "Jan-Jul 2021 → Jan-Jul 2023 (7m, 2y)"),
    ("sy2022_sm01_w7m_off1", "Jan-Jul 2022 → Jan-Jul 2023 (7m)"),
    ("sy2021_sm03_w6m_off1", "Mar-Aug 2021 → Mar-Aug 2022 (6m)"),
    ("sy2021_sm09_w6m_off1", "Sep 2021-Feb 2022 → Sep 2022-Feb 2023 (6m)"),
    ("sy2021_sm01_w4m_off1", "Jan-Apr 2021 → Jan-Apr 2022 (4m)"),
    ("sy2022_sm03_w4m_off1", "Mar-Jun 2022 → Mar-Jun 2023 (4m)"),
]

THRESHOLDS = [0.3, 0.5, 0.7]
CLASSES = cfg.OUTCOME_CLASSES  # [Decline, Stable, Growth]


def _bucket(slopes: np.ndarray, k: float) -> tuple[np.ndarray, float]:
    sigma = float(np.nanstd(slopes))
    thr = k * sigma if sigma > 0 else 0.0
    out = np.where(slopes > thr, "Growth", np.where(slopes < -thr, "Decline", "Stable"))
    return out, thr


def _rf_classify(X: pd.DataFrame, y: pd.Series) -> dict:
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=cfg.SEED)
    f1s, per_f1 = [], {c: [] for c in CLASSES}
    for tr, te in skf.split(X, y):
        m = RandomForestClassifier(
            n_estimators=120, max_depth=12, min_samples_leaf=20,
            n_jobs=-1, random_state=cfg.SEED, class_weight="balanced",
        )
        m.fit(X.iloc[tr], y.iloc[tr])
        pred = m.predict(X.iloc[te])
        f1s.append(f1_score(y.iloc[te], pred, average="macro", zero_division=0))
        cf = f1_score(y.iloc[te], pred, average=None, labels=CLASSES, zero_division=0)
        for i, c in enumerate(CLASSES):
            per_f1[c].append(cf[i])
    out = {"macro_f1_mean": float(np.mean(f1s)), "macro_f1_std": float(np.std(f1s))}
    for c in CLASSES:
        out[f"f1_{c}"] = float(np.mean(per_f1[c]))
    return out


def _rf_regress(X: pd.DataFrame, y_slope: pd.Series, k: float) -> dict:
    """Regression-then-bucket. We fit RF regressor on slope_target_norm, then
    bucket the OOF predictions with the same k*sigma threshold the panel uses,
    then compare against the *true* class labels at the same k.
    """
    kf = KFold(n_splits=3, shuffle=True, random_state=cfg.SEED)
    yhat = np.zeros(len(y_slope), dtype=float)
    for tr, te in kf.split(X):
        m = RandomForestRegressor(
            n_estimators=120, max_depth=12, min_samples_leaf=20,
            n_jobs=-1, random_state=cfg.SEED,
        )
        m.fit(X.iloc[tr], y_slope.iloc[tr])
        yhat[te] = m.predict(X.iloc[te])
    mae = float(mean_absolute_error(y_slope, yhat))
    r2 = float(r2_score(y_slope, yhat))
    pred_cls, _ = _bucket(yhat, k)
    true_cls, _ = _bucket(y_slope.to_numpy(), k)
    macro = float(f1_score(true_cls, pred_cls, average="macro", zero_division=0))
    return {"reg_mae": mae, "reg_r2": r2, "reg_then_bucket_macro_f1": macro}


def _eval_one(combo_id: str, description: str) -> tuple[list[dict], pd.DataFrame | None]:
    f_path = up.feature_path(combo_id)
    l_path = up.label_path(combo_id)
    if not (f_path.exists() and l_path.exists()):
        return [], None
    feats = pd.read_parquet(f_path)
    labels = pd.read_parquet(l_path)
    feats["public_id"] = feats["public_id"].astype(str)
    labels["public_id"] = labels["public_id"].astype(str)
    df = feats.merge(labels[["public_id", "slope_target_norm"]], on="public_id", how="inner")
    if len(df) < 500:
        return [], None
    base_cols = [c for c in feats.columns if c != "public_id"]
    X = df[base_cols].fillna(0)
    slopes = df["slope_target_norm"].to_numpy(dtype=float)

    rows = []
    keep_for_pairs = pd.DataFrame({"public_id": df["public_id"]})
    for k in THRESHOLDS:
        cls, thr = _bucket(slopes, k)
        if any(((cls == c).sum() < 30) for c in CLASSES):
            # skip degenerate
            continue
        y = pd.Series(cls).reset_index(drop=True)
        clf = _rf_classify(X.reset_index(drop=True), y)
        reg = _rf_regress(X.reset_index(drop=True),
                          pd.Series(slopes).reset_index(drop=True), k)
        n = len(df)
        counts = pd.Series(cls).value_counts()
        row = {
            "combo_id": combo_id,
            "description": description,
            "k_sigma": k,
            "threshold": thr,
            "n_stores": int(n),
            "growth_ratio": float(counts.get("Growth", 0) / n),
            "stable_ratio": float(counts.get("Stable", 0) / n),
            "decline_ratio": float(counts.get("Decline", 0) / n),
        }
        row.update(clf)
        row.update(reg)
        rows.append(row)
        keep_for_pairs[f"label_k{k}"] = cls
    return rows, keep_for_pairs


def _stability(per_panel_labels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """For each pair of panels in PANELS, compute fraction of *shared* stores
    whose label is the same under each k. Strong stability across panels is
    desirable: it means the labeling is not just noise.
    """
    rows = []
    items = list(per_panel_labels.items())
    for (a_id, a_df), (b_id, b_df) in combinations(items, 2):
        merged = a_df.merge(b_df, on="public_id", suffixes=("_a", "_b"))
        if len(merged) < 200:
            continue
        for k in THRESHOLDS:
            ca = f"label_k{k}_a"
            cb = f"label_k{k}_b"
            if ca not in merged or cb not in merged:
                continue
            same = (merged[ca] == merged[cb]).mean()
            rows.append({
                "panel_a": a_id, "panel_b": b_id, "k_sigma": k,
                "n_shared_stores": int(len(merged)),
                "same_label_ratio": float(same),
            })
    return pd.DataFrame(rows)


def main() -> None:
    all_rows = []
    per_panel = {}
    out_path = cfg.TABLE_DIR / "label_definition_sweep.csv"
    for combo_id, desc in PANELS:
        rows, keep = _eval_one(combo_id, desc)
        all_rows.extend(rows)
        if keep is not None:
            per_panel[combo_id] = keep
        for r in rows:
            print(
                f"[02b] {combo_id} k={r['k_sigma']} n={r['n_stores']:,} "
                f"G={r['growth_ratio']:.3f} S={r['stable_ratio']:.3f} D={r['decline_ratio']:.3f} "
                f"macroF1={r['macro_f1_mean']:.3f} regMAE={r['reg_mae']:.4f} "
                f"regR2={r['reg_r2']:.3f} regBucketF1={r['reg_then_bucket_macro_f1']:.3f}",
                flush=True,
            )
        # incremental save so partial runs aren't lost
        pd.DataFrame(all_rows).to_csv(out_path, index=False, encoding="utf-8-sig")

    out = pd.DataFrame(all_rows)
    out_path = cfg.TABLE_DIR / "label_definition_sweep.csv"
    out.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[02b] saved sweep: {out_path} (rows={len(out)})")

    stab = _stability(per_panel)
    stab_path = cfg.TABLE_DIR / "label_stability_pairs.csv"
    stab.to_csv(stab_path, index=False, encoding="utf-8-sig")
    print(f"[02b] saved stability: {stab_path} (rows={len(stab)})")

    if not out.empty:
        agg = (out.groupby("k_sigma")
               .agg(macro_f1_mean=("macro_f1_mean", "mean"),
                    growth=("growth_ratio", "mean"),
                    stable=("stable_ratio", "mean"),
                    decline=("decline_ratio", "mean"),
                    reg_bucket_f1=("reg_then_bucket_macro_f1", "mean"))
               .reset_index())
        agg_path = cfg.TABLE_DIR / "label_definition_sweep_summary.csv"
        agg.to_csv(agg_path, index=False, encoding="utf-8-sig")
        print(f"[02b] saved summary: {agg_path}")
        print(agg.to_string(index=False))

    if not stab.empty:
        agg2 = stab.groupby("k_sigma")["same_label_ratio"].mean().reset_index()
        print("[02b] cross-panel label stability (mean same-label ratio):")
        print(agg2.to_string(index=False))


if __name__ == "__main__":
    main()
