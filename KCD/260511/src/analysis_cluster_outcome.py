"""Phase 2.3 — Cluster × G/S/D heterogeneity analysis.

Recreates the panel-internal KMeans clustering used in step05 (k=6 on the
normalized feature-segment sales_card sequence), joins it with the outcome
labels, and quantifies:

  1. cluster × outcome_3 contingency (counts + ratios) per panel
  2. cluster-stratified macro_F1 of an RF on tabular features (does the
     model rely on different signals across clusters?)
  3. per-cluster top-feature importance (so we can say e.g. "in cluster 3
     nc_slope dominates Growth, in cluster 5 weekend_sales dominates")
  4. external/v4 cluster overlap: also joins original_data/cluster_labels_v4.csv
     where coverage exists, and reports growth_ratio per category.

Outputs:
  outputs/tables/cluster_outcome_xtab.csv
  outputs/tables/cluster_outcome_summary.csv
  outputs/tables/per_cluster_feature_importance.csv
  outputs/tables/v4_category_outcome.csv  (only where overlap exists)
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg  # noqa: E402
import utils_panel as up  # noqa: E402

PANELS = [
    ("sy2021_sm01_w3m_off1", "Jan-Mar 2021 → Jan-Mar 2022"),
    ("sy2021_sm05_w3m_off1", "May-Jul 2021 → May-Jul 2022"),
    ("sy2021_sm09_w3m_off1", "Sep-Nov 2021 → Sep-Nov 2022"),
    ("sy2022_sm01_w3m_off1", "Jan-Mar 2022 → Jan-Mar 2023"),
    ("sy2022_sm05_w3m_off1", "May-Jul 2022 → May-Jul 2023"),
    ("sy2021_sm01_w7m_off1", "Jan-Jul 2021 → Jan-Jul 2022 (7m)"),
    ("sy2022_sm01_w7m_off1", "Jan-Jul 2022 → Jan-Jul 2023 (7m)"),
]

CLASSES = cfg.OUTCOME_CLASSES


def _seq_matrix(panel_feat: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    pivot = panel_feat.pivot_table(
        index="public_id", columns="date_id", values="sales_card", aggfunc="mean"
    ).sort_index(axis=1)
    arr = pivot.to_numpy(dtype=float)
    means = np.nanmean(arr, axis=1, keepdims=True)
    means = np.where(np.isfinite(means) & (means > 1e-9), means, 1.0)
    norm = arr / means
    norm = np.where(np.isfinite(norm), norm, 0.0)
    ids = pivot.index.astype(str).to_numpy()
    return ids, norm


def _cluster(seq: np.ndarray, ids: np.ndarray, k: int = 6) -> pd.DataFrame:
    if len(ids) < k * 5:
        return pd.DataFrame({"public_id": ids, "km_cluster": np.zeros(len(ids), dtype=int)})
    scaled = StandardScaler().fit_transform(seq)
    km = KMeans(n_clusters=k, n_init=10, random_state=cfg.SEED, max_iter=300)
    labels = km.fit_predict(scaled)
    return pd.DataFrame({"public_id": ids, "km_cluster": labels})


def _per_cluster_importance(df: pd.DataFrame, base_cols: list[str]) -> pd.DataFrame:
    rows = []
    for c, sub in df.groupby("km_cluster"):
        if sub["outcome_3"].nunique() < 2 or len(sub) < 100:
            continue
        Xc = sub[base_cols].fillna(0)
        yc = sub["outcome_3"]
        if (yc.value_counts() < 5).any():
            continue
        m = RandomForestClassifier(n_estimators=120, max_depth=12, min_samples_leaf=20,
                                    n_jobs=8, random_state=cfg.SEED, class_weight="balanced")
        m.fit(Xc, yc)
        imp = pd.Series(m.feature_importances_, index=base_cols).sort_values(ascending=False)
        # also approximate growth-vs-decline direction by per-cluster mean of top features
        top = imp.head(8)
        for feat, imp_v in top.items():
            mean_g = sub.loc[sub["outcome_3"] == "Growth", feat].mean()
            mean_d = sub.loc[sub["outcome_3"] == "Decline", feat].mean()
            mean_s = sub.loc[sub["outcome_3"] == "Stable", feat].mean()
            rows.append({
                "km_cluster": int(c),
                "feature": feat,
                "importance": float(imp_v),
                "mean_growth": float(mean_g) if pd.notna(mean_g) else np.nan,
                "mean_decline": float(mean_d) if pd.notna(mean_d) else np.nan,
                "mean_stable": float(mean_s) if pd.notna(mean_s) else np.nan,
            })
    return pd.DataFrame(rows)


def _process(combo_id: str, description: str, v4: pd.DataFrame) -> dict:
    p_path = up.panel_path(combo_id)
    f_path = up.feature_path(combo_id)
    l_path = up.label_path(combo_id)
    if not (p_path.exists() and f_path.exists() and l_path.exists()):
        return {"xtab": pd.DataFrame(), "imp": pd.DataFrame(),
                "summary": [], "v4_match": pd.DataFrame()}
    panel = pd.read_parquet(p_path)
    feats = pd.read_parquet(f_path)
    labels = pd.read_parquet(l_path)
    feats["public_id"] = feats["public_id"].astype(str)
    labels["public_id"] = labels["public_id"].astype(str)

    feat_seg = panel[panel["segment"] == "feature"]
    ids, seq = _seq_matrix(feat_seg)
    cl = _cluster(seq, ids, k=6)

    df = (feats.merge(labels[["public_id", "outcome_3"]], on="public_id", how="inner")
                .merge(cl, on="public_id", how="left"))
    df = df[df["outcome_3"].isin(CLASSES)]
    if len(df) < 500:
        return {"xtab": pd.DataFrame(), "imp": pd.DataFrame(),
                "summary": [], "v4_match": pd.DataFrame()}

    base_cols = [c for c in feats.columns if c != "public_id"]

    # 1. xtab
    xtab = (df.groupby(["km_cluster", "outcome_3"]).size()
              .unstack(fill_value=0).reset_index())
    for c in CLASSES:
        if c not in xtab.columns:
            xtab[c] = 0
    tot = xtab[CLASSES].sum(axis=1).replace(0, 1)
    for c in CLASSES:
        xtab[f"ratio_{c}"] = xtab[c] / tot
    xtab["combo_id"] = combo_id

    # 2. cluster-stratified macro_F1 (single RF on whole, but break down recall by cluster)
    summary_rows = []
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=cfg.SEED)
    X = df[base_cols].fillna(0).reset_index(drop=True)
    y = df["outcome_3"].reset_index(drop=True)
    cl_arr = df["km_cluster"].to_numpy()
    pred_all = np.empty(len(y), dtype=object)
    for tr, te in skf.split(X, y):
        m = RandomForestClassifier(n_estimators=120, max_depth=12, min_samples_leaf=20,
                                    n_jobs=8, random_state=cfg.SEED, class_weight="balanced")
        m.fit(X.iloc[tr], y.iloc[tr])
        pred_all[te] = m.predict(X.iloc[te])
    overall = f1_score(y, pred_all, average="macro", zero_division=0)
    for c in sorted(np.unique(cl_arr)):
        mask = cl_arr == c
        if mask.sum() < 50 or len(np.unique(y[mask])) < 2:
            continue
        f1c = f1_score(y[mask], pred_all[mask], average="macro", zero_division=0)
        summary_rows.append({
            "combo_id": combo_id, "km_cluster": int(c),
            "n_stores": int(mask.sum()), "macro_f1_within_cluster": float(f1c),
            "overall_macro_f1": float(overall),
            **{f"ratio_{cl}": float((y[mask] == cl).mean()) for cl in CLASSES},
        })

    # 3. per-cluster importance
    imp = _per_cluster_importance(df, base_cols)
    if not imp.empty:
        imp.insert(0, "combo_id", combo_id)

    # 4. v4 overlap
    v4_match = pd.DataFrame()
    if not v4.empty:
        joined = df.merge(v4, on="public_id", how="inner")
        if len(joined) >= 100:
            v4x = (joined.groupby(["category", "outcome_3"]).size()
                          .unstack(fill_value=0).reset_index())
            for c in CLASSES:
                if c not in v4x.columns:
                    v4x[c] = 0
            tt = v4x[CLASSES].sum(axis=1).replace(0, 1)
            for c in CLASSES:
                v4x[f"ratio_{c}"] = v4x[c] / tt
            v4x["combo_id"] = combo_id
            v4x["n_overlap"] = int(len(joined))
            v4_match = v4x

    return {"xtab": xtab, "imp": imp, "summary": summary_rows, "v4_match": v4_match}


def main() -> None:
    v4 = pd.DataFrame()
    v4_path = Path("/home/hyeoky98/kcd/original_data/cluster_labels_v4.csv")
    if v4_path.exists():
        v4 = pd.read_csv(v4_path)
        v4["public_id"] = v4["public_id"].astype(str)
        v4 = v4[["public_id", "category"]]

    xtabs, imps, summaries, v4ms = [], [], [], []
    for combo_id, desc in PANELS:
        out = _process(combo_id, desc, v4)
        if not out["xtab"].empty:
            xtabs.append(out["xtab"])
        if not out["imp"].empty:
            imps.append(out["imp"])
        summaries.extend(out["summary"])
        if not out["v4_match"].empty:
            v4ms.append(out["v4_match"])
        print(f"[ck] {combo_id} done")

    if xtabs:
        x = pd.concat(xtabs, ignore_index=True)
        x.to_csv(cfg.TABLE_DIR / "cluster_outcome_xtab.csv", index=False, encoding="utf-8-sig")
        print(f"[ck] saved cluster_outcome_xtab.csv (rows={len(x)})")
    if imps:
        i = pd.concat(imps, ignore_index=True)
        i.to_csv(cfg.TABLE_DIR / "per_cluster_feature_importance.csv",
                 index=False, encoding="utf-8-sig")
        print(f"[ck] saved per_cluster_feature_importance.csv (rows={len(i)})")
    if summaries:
        s = pd.DataFrame(summaries)
        s.to_csv(cfg.TABLE_DIR / "cluster_outcome_summary.csv",
                 index=False, encoding="utf-8-sig")
        print(f"[ck] saved cluster_outcome_summary.csv (rows={len(s)})")
    if v4ms:
        v = pd.concat(v4ms, ignore_index=True)
        v.to_csv(cfg.TABLE_DIR / "v4_category_outcome.csv",
                 index=False, encoding="utf-8-sig")
        print(f"[ck] saved v4_category_outcome.csv (rows={len(v)})")


if __name__ == "__main__":
    main()
