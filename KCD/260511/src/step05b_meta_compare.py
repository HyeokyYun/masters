"""Step 05b — Compare baseline (A) vs A+meta on the 14 panels (Phase 2.2 / A2).

Reuses step05's RF setup but adds the meta features extracted in step03b
(tenure_log, has_delivery, sqsize_log, prop_age_*).

We do NOT include `sigungu` and `kostat_class` directly because they are
high-cardinality categoricals; for those we add fold-aware target
encoding (mean of slope_target_norm in train fold; smoothed by global
prior). This avoids leakage.

Outputs:
  outputs/tables/main_model_compare_meta.csv
  outputs/tables/main_model_paired_AvAmeta.csv
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg  # noqa: E402
import utils_panel as up  # noqa: E402

PANELS = [
    ("sy2021_sm01_w3m_off1", "Jan-Mar 2021 → Jan-Mar 2022"),
    ("sy2021_sm05_w3m_off1", "May-Jul 2021 → May-Jul 2022"),
    ("sy2021_sm09_w3m_off1", "Sep-Nov 2021 → Sep-Nov 2022"),
    ("sy2022_sm01_w3m_off1", "Jan-Mar 2022 → Jan-Mar 2023"),
    ("sy2022_sm03_w3m_off1", "Mar-May 2022 → Mar-May 2023"),
    ("sy2022_sm05_w3m_off1", "May-Jul 2022 → May-Jul 2023"),
    ("sy2021_sm01_w7m_off1", "Jan-Jul 2021 → Jan-Jul 2022 (7m)"),
    ("sy2022_sm01_w7m_off1", "Jan-Jul 2022 → Jan-Jul 2023 (7m)"),
]
CLASSES = cfg.OUTCOME_CLASSES
NUMERIC_META = ["tenure_log", "tenure_months", "has_delivery", "sqsize_log",
                 "prop_age_30대", "prop_age_40대", "prop_age_50대",
                 "prop_age_20대", "prop_age_60대", "prop_age_unknown"]


def _target_encode(train_y_slope: pd.Series, train_cat: pd.Series,
                    full_cat: pd.Series, smoothing: float = 50.0) -> np.ndarray:
    """Mean of slope_target_norm per category (train fold), smoothed by global prior.
    Returns array aligned with full_cat order."""
    global_mean = float(train_y_slope.mean())
    grp = pd.DataFrame({"cat": train_cat, "y": train_y_slope}).groupby("cat")["y"]
    cnt = grp.count()
    s = grp.sum()
    smoothed = (s + global_mean * smoothing) / (cnt + smoothing)
    return full_cat.map(smoothed).fillna(global_mean).to_numpy(dtype=np.float32)


def _eval(combo_id: str, description: str) -> tuple[list[dict], dict]:
    f_path = up.feature_path(combo_id)
    l_path = up.label_path(combo_id)
    m_path = cfg.TABLE_DIR / "features_meta" / f"features_meta_{combo_id}.parquet"
    if not (f_path.exists() and l_path.exists() and m_path.exists()):
        return [], {}
    feats = pd.read_parquet(f_path)
    labels = pd.read_parquet(l_path)
    meta = pd.read_parquet(m_path)
    feats["public_id"] = feats["public_id"].astype(str)
    labels["public_id"] = labels["public_id"].astype(str)
    meta["public_id"] = meta["public_id"].astype(str)

    df = (feats.merge(labels[["public_id", "outcome_3", "slope_target_norm"]], on="public_id", how="inner")
                .merge(meta, on="public_id", how="left"))
    df = df[df["outcome_3"].isin(CLASSES)].reset_index(drop=True)
    if len(df) < 500 or (df["outcome_3"].value_counts() < 10).any():
        return [], {}
    base_cols = [c for c in feats.columns if c != "public_id"]
    meta_num_cols = [c for c in NUMERIC_META if c in df.columns]
    cat_cols = [c for c in ["sigungu", "kostat_class"] if c in df.columns]

    y = df["outcome_3"]
    y_slope = df["slope_target_norm"]

    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=cfg.SEED)
    fold_f1s = {"A_baseline": [], "A_plus_meta": []}
    per_class_f1 = {f"A_baseline:{c}": [] for c in CLASSES}
    per_class_f1.update({f"A_plus_meta:{c}": [] for c in CLASSES})

    for tr, te in skf.split(df, y):
        # baseline A: only base feats
        Xa_tr = df.iloc[tr][base_cols].fillna(0)
        Xa_te = df.iloc[te][base_cols].fillna(0)
        m_a = RandomForestClassifier(n_estimators=120, max_depth=12, min_samples_leaf=20,
                                       n_jobs=8, random_state=cfg.SEED, class_weight="balanced")
        m_a.fit(Xa_tr, y.iloc[tr])
        pa = m_a.predict(Xa_te)
        fold_f1s["A_baseline"].append(f1_score(y.iloc[te], pa, average="macro", zero_division=0))
        per = precision_recall_fscore_support(y.iloc[te], pa, labels=CLASSES, zero_division=0)
        for i, c in enumerate(CLASSES):
            per_class_f1[f"A_baseline:{c}"].append(per[2][i])

        # A + meta numeric + target-encoded categoricals
        Xb_tr = df.iloc[tr][base_cols + meta_num_cols].fillna(0).copy()
        Xb_te = df.iloc[te][base_cols + meta_num_cols].fillna(0).copy()
        for c in cat_cols:
            te_train = _target_encode(y_slope.iloc[tr], df.iloc[tr][c], df.iloc[tr][c])
            te_test = _target_encode(y_slope.iloc[tr], df.iloc[tr][c], df.iloc[te][c])
            Xb_tr[f"{c}_te"] = te_train
            Xb_te[f"{c}_te"] = te_test
        m_b = RandomForestClassifier(n_estimators=120, max_depth=12, min_samples_leaf=20,
                                       n_jobs=8, random_state=cfg.SEED, class_weight="balanced")
        m_b.fit(Xb_tr, y.iloc[tr])
        pb = m_b.predict(Xb_te)
        fold_f1s["A_plus_meta"].append(f1_score(y.iloc[te], pb, average="macro", zero_division=0))
        per = precision_recall_fscore_support(y.iloc[te], pb, labels=CLASSES, zero_division=0)
        for i, c in enumerate(CLASSES):
            per_class_f1[f"A_plus_meta:{c}"].append(per[2][i])

    rows = []
    for label in ["A_baseline", "A_plus_meta"]:
        row = {
            "combo_id": combo_id, "description": description, "label": label,
            "macro_f1_mean": float(np.mean(fold_f1s[label])),
            "macro_f1_std": float(np.std(fold_f1s[label])),
            "n_stores": int(len(df)),
        }
        for c in CLASSES:
            row[f"f1_{c}"] = float(np.mean(per_class_f1[f"{label}:{c}"]))
        rows.append(row)

    a = np.array(fold_f1s["A_baseline"])
    b = np.array(fold_f1s["A_plus_meta"])
    if np.std(b - a) > 0:
        t, p = stats.ttest_rel(b, a)
        paired = {
            "combo_id": combo_id, "description": description,
            "delta_mean": float((b - a).mean()),
            "t_stat": float(t), "p_value": float(p),
        }
    else:
        paired = {"combo_id": combo_id, "delta_mean": float((b - a).mean()),
                  "t_stat": np.nan, "p_value": np.nan}
    return rows, paired


def main() -> None:
    rows, paired = [], []
    out1 = cfg.TABLE_DIR / "main_model_compare_meta.csv"
    out2 = cfg.TABLE_DIR / "main_model_paired_AvAmeta.csv"
    for combo_id, desc in PANELS:
        r, p = _eval(combo_id, desc)
        rows.extend(r)
        if p:
            paired.append(p)
        for x in r:
            print(f"[05b] {combo_id} {x['label']:14s} macroF1={x['macro_f1_mean']:.3f}±{x['macro_f1_std']:.3f}",
                   flush=True)
        if p:
            print(f"[05b] {combo_id} delta_meta={p['delta_mean']:+.4f} p={p.get('p_value', np.nan):.3f}",
                   flush=True)
        pd.DataFrame(rows).to_csv(out1, index=False, encoding="utf-8-sig")
        pd.DataFrame(paired).to_csv(out2, index=False, encoding="utf-8-sig")

    print(f"[05b] saved: {out1} (rows={len(rows)})")
    print(f"[05b] saved: {out2} (rows={len(paired)})")
    if paired:
        agg = pd.DataFrame(paired).agg({"delta_mean": "mean", "p_value": "mean"}).to_dict()
        print(f"[05b] avg delta_macro_f1 (A+meta - A) = {agg['delta_mean']:+.4f}, "
               f"avg p = {agg['p_value']:.3f}")


if __name__ == "__main__":
    main()
