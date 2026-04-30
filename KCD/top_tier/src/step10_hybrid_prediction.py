"""Step 10 — Hybrid Prediction: 30주 시퀀스 + 클러스터 state feature 통합.

논문 outline의 Proposed Model 구현.
기존 46개 feature에 다음을 추가:
  (a) 30주 시퀀스에서 학습한 K-Shape / KMeans cluster 할당 (one-hot)
  (b) 30주 내 change point detection 기반 feature (위치, 전/후 기울기 차, 규모)

Model A: 46 features (baseline = step03)
Model B: A + cluster one-hot
Model C: A + change point features
Model D: A + cluster + change point (Proposed)
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.metrics import f1_score, precision_recall_fscore_support, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg  # noqa: E402

try:
    from tslearn.clustering import KShape
    from tslearn.preprocessing import TimeSeriesScalerMeanVariance
    HAS_TSLEARN = False
except ImportError:
    HAS_TSLEARN = False

import xgboost as xgb


def load_panel_seq():
    panel = pd.read_parquet(cfg.PANEL_PATH)
    panel["public_id"] = panel["public_id"].astype(str)
    panel = panel[panel["observed_week_idx"] < cfg.PREDICTION_WEEKS]
    pivot = panel.pivot_table(index="public_id", columns="observed_week_idx",
                              values="sales_card_mm", aggfunc="mean")
    pivot = pivot.dropna(axis=1, thresh=int(len(pivot) * 0.6))
    pivot = pivot.dropna(axis=0, thresh=int(pivot.shape[1] * 0.85))
    pivot = pivot.fillna(pivot.median(axis=0))
    pivot.index = pivot.index.astype(str)
    return pivot


def assign_clusters(seq_matrix: np.ndarray, k_km: int = 4, k_ks: int = 7):
    scaled = StandardScaler().fit_transform(seq_matrix)
    km = KMeans(n_clusters=k_km, n_init=15, random_state=cfg.SEED, max_iter=500)
    km_labels = km.fit_predict(scaled)
    result = {"kmeans": km_labels}

    if HAS_TSLEARN:
        series = seq_matrix.reshape(seq_matrix.shape[0], seq_matrix.shape[1], 1)
        series = TimeSeriesScalerMeanVariance().fit_transform(series)
        ks = KShape(n_clusters=k_ks, max_iter=30, random_state=cfg.SEED, verbose=0)
        ks_labels = ks.fit_predict(series)
        result["kshape"] = ks_labels
    return result


def extract_change_point_features(seq: np.ndarray) -> dict:
    """30주 시퀀스에서 변곡점(기울기 변화 최대 지점) 기반 feature 추출."""
    x = np.arange(len(seq), dtype=float)
    n = len(seq)
    if n < 10:
        return {"cp_position": -1, "cp_delta_slope": 0.0,
                "cp_pre_slope": 0.0, "cp_post_slope": 0.0,
                "cp_magnitude": 0.0, "has_up_cp": 0, "has_down_cp": 0}

    best_delta = 0.0
    best_pos = -1
    pre_s = post_s = 0.0
    for t in range(5, n - 5):
        s_pre, *_ = stats.linregress(x[:t], seq[:t])
        s_post, *_ = stats.linregress(x[t:], seq[t:])
        delta = abs(s_post - s_pre)
        if delta > best_delta:
            best_delta = delta
            best_pos = t
            pre_s, post_s = s_pre, s_post
    mag = abs(seq[best_pos] - seq[0]) if best_pos > 0 else 0.0
    return {
        "cp_position": best_pos / n,
        "cp_delta_slope": post_s - pre_s,
        "cp_pre_slope": pre_s,
        "cp_post_slope": post_s,
        "cp_magnitude": mag,
        "has_up_cp": int(post_s - pre_s > 0.01),
        "has_down_cp": int(post_s - pre_s < -0.01),
    }


def fast_change_point_features(seq_arr: np.ndarray, ids) -> pd.DataFrame:
    """Vectorized CP approximation for 30-week sequences.

    Uses the split that maximizes the post/pre mean gap and records simple
    pre/post slopes.  This preserves the CP signal while avoiding 49k x 20
    scipy regressions.
    """
    n, t = seq_arr.shape
    splits = np.arange(5, t - 5)
    rows = []
    x_cache = {k: np.arange(k, dtype=float) for k in range(1, t + 1)}

    def _fast_slope(y):
        x = x_cache[len(y)]
        yy = y - y.mean()
        xx = x - x.mean()
        den = np.dot(xx, xx)
        return float(np.dot(xx, yy) / den) if den > 0 else 0.0

    for i, pid in enumerate(ids):
        y = seq_arr[i]
        scores = [abs(np.nanmean(y[s:]) - np.nanmean(y[:s])) for s in splits]
        pos = int(splits[int(np.nanargmax(scores))])
        pre_s = _fast_slope(y[:pos])
        post_s = _fast_slope(y[pos:])
        delta = post_s - pre_s
        rows.append(
            {
                "public_id": pid,
                "cp_position": pos / t,
                "cp_delta_slope": delta,
                "cp_pre_slope": pre_s,
                "cp_post_slope": post_s,
                "cp_magnitude": float(abs(y[pos] - y[0])),
                "has_up_cp": int(delta > 0.01),
                "has_down_cp": int(delta < -0.01),
            }
        )
    return pd.DataFrame(rows)


def train_eval(X_tr, y_tr, X_te, y_te, classes):
    c2i = {c: i for i, c in enumerate(classes)}
    y_tr_e = np.array([c2i[v] for v in y_tr])
    model = xgb.XGBClassifier(
        n_estimators=160, max_depth=4, learning_rate=0.08,
        subsample=0.9, colsample_bytree=0.9, min_child_weight=2,
        objective="multi:softprob", num_class=len(classes),
        eval_metric="mlogloss", tree_method="hist", n_jobs=4,
        random_state=cfg.SEED,
    )
    model.fit(X_tr, y_tr_e)
    proba = model.predict_proba(X_te)
    preds = np.array([classes[i] for i in model.predict(X_te)])
    per = precision_recall_fscore_support(y_te, preds, labels=classes, zero_division=0)
    try:
        auc = roc_auc_score(pd.get_dummies(y_te)[classes].values, proba, multi_class="ovr")
    except Exception:
        auc = np.nan
    return {
        "macro_f1": f1_score(y_te, preds, average="macro", zero_division=0),
        "auc_ovr": auc,
        **{f"recall_{c}": per[1][i] for i, c in enumerate(classes)},
        **{f"f1_{c}": per[2][i] for i, c in enumerate(classes)},
    }


def main():
    feat_df = pd.read_parquet(cfg.TABLE_DIR / "prediction_feature_matrix.parquet")
    feat_df["public_id"] = feat_df["public_id"].astype(str)
    print(f"[10] base feature matrix: {feat_df.shape}")

    seq = load_panel_seq()
    common = seq.index.intersection(feat_df["public_id"])
    seq = seq.loc[common]
    feat_df = feat_df.set_index("public_id").loc[common].reset_index()
    print(f"[10] aligned stores: {len(common):,}")

    print("[10] computing clusters ...")
    cluster_labels = assign_clusters(seq.to_numpy())
    km_df = pd.DataFrame({"public_id": seq.index,
                         "km_cluster": cluster_labels["kmeans"]})
    if "kshape" in cluster_labels:
        km_df["ks_cluster"] = cluster_labels["kshape"]
    km_df.to_csv(cfg.TABLE_DIR / "hybrid_cluster_assignments.csv", index=False, encoding="utf-8-sig")

    print("[10] computing change point features ...")
    seq_arr = seq.to_numpy()
    cp_df = fast_change_point_features(seq_arr, seq.index)
    cp_df.to_csv(cfg.TABLE_DIR / "hybrid_change_point_features.csv", index=False, encoding="utf-8-sig")

    feat_df = feat_df.merge(km_df, on="public_id", how="inner")
    feat_df = feat_df.merge(cp_df, on="public_id", how="inner")
    print(f"[10] enriched feature matrix: {feat_df.shape}")

    classes = cfg.OUTCOME_CLASSES
    base_cols = [c for c in feat_df.columns if c not in {
        "public_id", "outcome_3", "label",
        "km_cluster", "ks_cluster",
        "cp_position", "cp_delta_slope", "cp_pre_slope",
        "cp_post_slope", "cp_magnitude", "has_up_cp", "has_down_cp"}]

    km_onehot = pd.get_dummies(feat_df["km_cluster"], prefix="km")
    ks_onehot = pd.get_dummies(feat_df["ks_cluster"], prefix="ks") if "ks_cluster" in feat_df else None
    cluster_cols = list(km_onehot.columns)
    if ks_onehot is not None:
        cluster_cols += list(ks_onehot.columns)
    cp_cols = ["cp_position", "cp_delta_slope", "cp_pre_slope",
               "cp_post_slope", "cp_magnitude", "has_up_cp", "has_down_cp"]

    X_full = pd.concat([feat_df[base_cols].fillna(0.0), km_onehot], axis=1)
    if ks_onehot is not None:
        X_full = pd.concat([X_full, ks_onehot], axis=1)
    X_full = pd.concat([X_full, feat_df[cp_cols]], axis=1)
    y = feat_df["outcome_3"].values

    feature_sets = {
        "A_base_46": base_cols,
        "B_base_cluster": base_cols + cluster_cols,
        "C_base_cp": base_cols + cp_cols,
        "D_base_cluster_cp_PROPOSED": base_cols + cluster_cols + cp_cols,
    }

    skf = StratifiedKFold(n_splits=cfg.CV_FOLDS, shuffle=True, random_state=cfg.SEED)
    all_rows = []
    for name, cols in feature_sets.items():
        print(f"\n=== {name} | {len(cols)} features ===")
        X = X_full[cols].values.astype(float)
        for fold, (tr, te) in enumerate(skf.split(X, y)):
            scaler = StandardScaler()
            X_tr = scaler.fit_transform(X[tr])
            X_te = scaler.transform(X[te])
            r = train_eval(X_tr, y[tr], X_te, y[te], classes)
            r["model"] = name
            r["fold"] = fold
            all_rows.append(r)
            print(f"  fold={fold} F1={r['macro_f1']:.3f} "
                  f"G_rec={r['recall_Growth']:.3f} D_rec={r['recall_Decline']:.3f} "
                  f"AUC={r['auc_ovr']:.3f}")

    df = pd.DataFrame(all_rows)
    df.to_csv(cfg.TABLE_DIR / "hybrid_prediction_cv_folds.csv", index=False, encoding="utf-8-sig")
    agg = df.groupby("model").agg(["mean", "std"]).round(4)
    agg.to_csv(cfg.TABLE_DIR / "hybrid_prediction_summary.csv", encoding="utf-8-sig")
    print("\n=== Summary (mean ± std) ===")
    cols_show = [("macro_f1", "mean"), ("macro_f1", "std"),
                 ("recall_Growth", "mean"), ("recall_Decline", "mean"),
                 ("auc_ovr", "mean")]
    print(agg[cols_show].to_string())


if __name__ == "__main__":
    main()
