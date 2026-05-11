"""Phase 2.1 — Per-class SHAP analysis on G/S/D.

For each of the 14 representative panels, refits a RandomForest on the
existing 56-feature tabular set + the meta-feature additions from step03b
(if available), then computes SHAP values via TreeExplainer and ranks
features by mean(|SHAP|) per class.

We expect to confirm the meeting finding that nc_* (신규 유입) and
tenure_log (업력) are top contributors to the *Growth* class, and that
slope_* dominates *Decline*.

Outputs:
  outputs/tables/shap_class_contrib.csv      (panel × class × feature top-N)
  outputs/tables/shap_class_rank_long.csv    (full ranking)
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg  # noqa: E402
import utils_panel as up  # noqa: E402

try:
    import shap  # noqa: F401
    HAVE_SHAP = True
except Exception as e:
    HAVE_SHAP = False
    print(f"[shap] not available: {e}")

PANELS = [
    "sy2021_sm01_w3m_off1", "sy2021_sm05_w3m_off1",
    "sy2021_sm09_w3m_off1", "sy2022_sm01_w3m_off1",
    "sy2022_sm05_w3m_off1",
    "sy2021_sm01_w7m_off1", "sy2022_sm01_w7m_off1",
]

CLASSES = cfg.OUTCOME_CLASSES
TOP_N = 15
SAMPLE_FOR_SHAP = 1500  # cap for SHAP speed


def _build_xy(combo_id: str) -> tuple[pd.DataFrame, pd.Series] | None:
    f_path = up.feature_path(combo_id)
    l_path = up.label_path(combo_id)
    if not (f_path.exists() and l_path.exists()):
        return None
    feats = pd.read_parquet(f_path)
    labels = pd.read_parquet(l_path)
    feats["public_id"] = feats["public_id"].astype(str)
    labels["public_id"] = labels["public_id"].astype(str)
    df = feats.merge(labels[["public_id", "outcome_3"]], on="public_id", how="inner")
    df = df[df["outcome_3"].isin(CLASSES)]

    meta_p = cfg.TABLE_DIR / "features_meta" / f"features_meta_{combo_id}.parquet"
    if meta_p.exists():
        meta = pd.read_parquet(meta_p)
        meta["public_id"] = meta["public_id"].astype(str)
        # only numeric meta cols
        num_cols = [c for c in meta.columns
                    if c != "public_id" and pd.api.types.is_numeric_dtype(meta[c])]
        df = df.merge(meta[["public_id"] + num_cols], on="public_id", how="left")
    if len(df) < 500:
        return None
    base_cols = [c for c in df.columns if c not in ("public_id", "outcome_3")]
    X = df[base_cols].fillna(0)
    y = df["outcome_3"]
    return X, y


def _shap_one(combo_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    Xy = _build_xy(combo_id)
    if Xy is None:
        return pd.DataFrame(), pd.DataFrame()
    X, y = Xy
    Xtr, Xte, ytr, yte = train_test_split(X, y, stratify=y, test_size=0.2, random_state=cfg.SEED)
    m = RandomForestClassifier(n_estimators=120, max_depth=10, min_samples_leaf=20,
                                n_jobs=8, random_state=cfg.SEED, class_weight="balanced")
    m.fit(Xtr, ytr)
    classes_order = list(m.classes_)

    # Subsample test set for SHAP
    if len(Xte) > SAMPLE_FOR_SHAP:
        Xte_s = Xte.sample(SAMPLE_FOR_SHAP, random_state=cfg.SEED)
    else:
        Xte_s = Xte

    if not HAVE_SHAP:
        # fallback: per-class permutation-style importance via predict_proba contribution
        return pd.DataFrame(), pd.DataFrame()

    import shap as _shap
    expl = _shap.TreeExplainer(m, feature_perturbation="tree_path_dependent")
    sv = expl.shap_values(Xte_s, check_additivity=False)
    # sv shape: (n_classes, n_samples, n_features) for sklearn RF
    if isinstance(sv, list):
        arr = np.stack(sv, axis=0)  # (C, N, F)
    else:
        # newer SHAP returns (N, F, C)
        arr = np.transpose(sv, (2, 0, 1))
    long_rows = []
    top_rows = []
    feat_names = list(X.columns)
    for ci, cname in enumerate(classes_order):
        mean_abs = np.abs(arr[ci]).mean(axis=0)
        rank = pd.Series(mean_abs, index=feat_names).sort_values(ascending=False)
        for r, (feat, val) in enumerate(rank.items()):
            long_rows.append({
                "combo_id": combo_id, "class": cname,
                "rank": r + 1, "feature": feat, "mean_abs_shap": float(val),
            })
            if r < TOP_N:
                top_rows.append({
                    "combo_id": combo_id, "class": cname,
                    "rank": r + 1, "feature": feat, "mean_abs_shap": float(val),
                })
    return pd.DataFrame(top_rows), pd.DataFrame(long_rows)


def main() -> None:
    if not HAVE_SHAP:
        print("[shap] please `pip install shap`; aborting", flush=True)
        return
    tops, longs = [], []
    for combo_id in PANELS:
        print(f"[shap] start {combo_id}", flush=True)
        t, l = _shap_one(combo_id)
        if not t.empty:
            tops.append(t)
        if not l.empty:
            longs.append(l)
        print(f"[shap] {combo_id} done", flush=True)
        # incremental save
        if tops:
            pd.concat(tops, ignore_index=True).to_csv(
                cfg.TABLE_DIR / "shap_class_contrib.csv",
                index=False, encoding="utf-8-sig")
        if longs:
            pd.concat(longs, ignore_index=True).to_csv(
                cfg.TABLE_DIR / "shap_class_rank_long.csv",
                index=False, encoding="utf-8-sig")
    if tops:
        td = pd.concat(tops, ignore_index=True)
        td.to_csv(cfg.TABLE_DIR / "shap_class_contrib.csv",
                  index=False, encoding="utf-8-sig")
        print(f"[shap] saved shap_class_contrib.csv (rows={len(td)})")
    if longs:
        ld = pd.concat(longs, ignore_index=True)
        ld.to_csv(cfg.TABLE_DIR / "shap_class_rank_long.csv",
                  index=False, encoding="utf-8-sig")
        print(f"[shap] saved shap_class_rank_long.csv (rows={len(ld)})")


if __name__ == "__main__":
    main()
