"""Step 10-B — Hybrid Proposed Model, fold-safe (no cross-fold leakage).

step10의 leakage 수정본:
  - K-Means / K-Shape 를 train fold 에만 fit, test fold에 transform 만 적용
  - Change-point feature는 store-internal이므로 leakage 없음 → 그대로
  - 동일 5-fold split 으로 step10과 직접 비교

출력: hybrid_nofold_leak_cv_folds.csv, hybrid_nofold_leak_summary.csv
리뷰: step10의 Proposed D F1=0.648 / AUC=0.830 와 비교.
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
    HAS_TSLEARN = True
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


def fit_kmeans_transform(train_seq: np.ndarray, all_seq: np.ndarray, k=4):
    """KMeans fit on train, predict for all (train+test)."""
    scaler = StandardScaler().fit(train_seq)
    train_scaled = scaler.transform(train_seq)
    all_scaled = scaler.transform(all_seq)
    km = KMeans(n_clusters=k, n_init=15, random_state=cfg.SEED, max_iter=500)
    km.fit(train_scaled)
    return km.predict(all_scaled)


def fit_kshape_transform(train_seq: np.ndarray, all_seq: np.ndarray, k=7, max_train=5000):
    """KShape fit on train (subsample for speed), predict for all."""
    if len(train_seq) > max_train:
        rng = np.random.RandomState(cfg.SEED)
        pick = rng.choice(len(train_seq), max_train, replace=False)
        train_seq_sub = train_seq[pick]
    else:
        train_seq_sub = train_seq
    train_series = train_seq_sub.reshape(train_seq_sub.shape[0], train_seq_sub.shape[1], 1)
    all_series = all_seq.reshape(all_seq.shape[0], all_seq.shape[1], 1)
    scaler = TimeSeriesScalerMeanVariance()
    train_series = scaler.fit_transform(train_series)
    all_series = scaler.transform(all_series)
    ks = KShape(n_clusters=k, max_iter=10, random_state=cfg.SEED, verbose=0)
    ks.fit(train_series)
    return ks.predict(all_series)


def extract_change_point_features(seq: np.ndarray) -> dict:
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
    return {"cp_position": best_pos / n, "cp_delta_slope": post_s - pre_s,
            "cp_pre_slope": pre_s, "cp_post_slope": post_s,
            "cp_magnitude": mag,
            "has_up_cp": int(post_s - pre_s > 0.01),
            "has_down_cp": int(post_s - pre_s < -0.01)}


def train_eval(X_tr, y_tr, X_te, y_te, classes):
    c2i = {c: i for i, c in enumerate(classes)}
    y_tr_e = np.array([c2i[v] for v in y_tr])
    model = xgb.XGBClassifier(
        n_estimators=500, max_depth=6, learning_rate=0.05,
        subsample=0.9, colsample_bytree=0.9, min_child_weight=2,
        objective="multi:softprob", num_class=len(classes),
        eval_metric="mlogloss", tree_method="hist", n_jobs=-1,
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
    return {"macro_f1": f1_score(y_te, preds, average="macro", zero_division=0),
            "auc_ovr": auc,
            **{f"recall_{c}": per[1][i] for i, c in enumerate(classes)},
            **{f"f1_{c}": per[2][i] for i, c in enumerate(classes)}}


def main():
    feat_df = pd.read_parquet(cfg.TABLE_DIR / "prediction_feature_matrix.parquet")
    feat_df["public_id"] = feat_df["public_id"].astype(str)

    seq = load_panel_seq()
    common = seq.index.intersection(feat_df["public_id"])
    seq = seq.loc[common]
    feat_df = feat_df.set_index("public_id").loc[common].reset_index()
    seq_arr = seq.to_numpy()
    print(f"[10b] aligned stores: {len(common):,}, seq shape: {seq_arr.shape}")

    print("[10b] computing change point features (store-internal, no leakage) ...")
    cp_rows = []
    for i, pid in enumerate(seq.index):
        d = extract_change_point_features(seq_arr[i])
        d["public_id"] = pid
        cp_rows.append(d)
    cp_df = pd.DataFrame(cp_rows)
    feat_df = feat_df.merge(cp_df, on="public_id", how="inner")
    print(f"[10b] enriched base matrix: {feat_df.shape}")

    classes = cfg.OUTCOME_CLASSES
    base_cols = [c for c in feat_df.columns if c not in {
        "public_id", "outcome_3", "label",
        "cp_position", "cp_delta_slope", "cp_pre_slope", "cp_post_slope",
        "cp_magnitude", "has_up_cp", "has_down_cp"}]
    cp_cols = ["cp_position", "cp_delta_slope", "cp_pre_slope", "cp_post_slope",
               "cp_magnitude", "has_up_cp", "has_down_cp"]
    y = feat_df["outcome_3"].values
    id_to_rowidx = {pid: i for i, pid in enumerate(seq.index)}
    feat_rowidx = feat_df["public_id"].map(id_to_rowidx).values

    skf = StratifiedKFold(n_splits=cfg.CV_FOLDS, shuffle=True, random_state=cfg.SEED)
    all_rows = []
    for fold, (tr_idx, te_idx) in enumerate(skf.split(feat_df, y)):
        train_seq_rows = feat_rowidx[tr_idx]
        all_seq_rows = feat_rowidx
        train_seq = seq_arr[train_seq_rows]

        print(f"\n[10b] fold {fold}: fit KMeans / KShape on {len(train_seq):,} train stores")
        km_labels = fit_kmeans_transform(train_seq, seq_arr[all_seq_rows], k=4)
        if HAS_TSLEARN:
            ks_labels = fit_kshape_transform(train_seq, seq_arr[all_seq_rows], k=7)
        else:
            ks_labels = None

        feat_df_fold = feat_df.copy()
        feat_df_fold["km_cluster"] = km_labels
        if ks_labels is not None:
            feat_df_fold["ks_cluster"] = ks_labels

        km_onehot = pd.get_dummies(feat_df_fold["km_cluster"], prefix="km")
        ks_onehot = pd.get_dummies(feat_df_fold["ks_cluster"], prefix="ks") if ks_labels is not None else None

        X_full = pd.concat([feat_df_fold[base_cols].fillna(0.0), km_onehot], axis=1)
        if ks_onehot is not None:
            X_full = pd.concat([X_full, ks_onehot], axis=1)
        X_full = pd.concat([X_full, feat_df_fold[cp_cols]], axis=1)

        for config_name, cols in [
            ("A_base_46", base_cols),
            ("B_base_cluster_fold", base_cols + list(km_onehot.columns)
                + (list(ks_onehot.columns) if ks_onehot is not None else [])),
            ("C_base_cp", base_cols + cp_cols),
            ("D_proposed_fold_safe", base_cols
                + list(km_onehot.columns)
                + (list(ks_onehot.columns) if ks_onehot is not None else [])
                + cp_cols),
        ]:
            X = X_full[cols].values.astype(float)
            scaler = StandardScaler()
            X_tr = scaler.fit_transform(X[tr_idx])
            X_te = scaler.transform(X[te_idx])
            r = train_eval(X_tr, y[tr_idx], X_te, y[te_idx], classes)
            r["model"] = config_name
            r["fold"] = fold
            all_rows.append(r)
            print(f"  {config_name}: F1={r['macro_f1']:.3f} AUC={r['auc_ovr']:.3f}")

    df = pd.DataFrame(all_rows)
    df.to_csv(cfg.TABLE_DIR / "hybrid_nofold_leak_cv_folds.csv", index=False, encoding="utf-8-sig")
    agg = df.groupby("model").agg(["mean", "std"]).round(4)
    agg.to_csv(cfg.TABLE_DIR / "hybrid_nofold_leak_summary.csv", encoding="utf-8-sig")
    print("\n=== Fold-safe Summary (mean ± std) ===")
    print(agg[[("macro_f1", "mean"), ("macro_f1", "std"),
               ("recall_Growth", "mean"), ("recall_Decline", "mean"),
               ("auc_ovr", "mean")]].to_string())

    original = pd.read_csv(cfg.TABLE_DIR / "hybrid_prediction_summary.csv", header=[0, 1], index_col=0)
    print("\n=== vs step10 (with leakage) ===")
    for model in ["A_base_46", "D_proposed_fold_safe"]:
        if model in agg.index:
            new_f1 = agg.loc[model, ("macro_f1", "mean")]
            new_auc = agg.loc[model, ("auc_ovr", "mean")]
            orig_model = "A_base_46" if model == "A_base_46" else "D_base_cluster_cp_PROPOSED"
            if orig_model in original.index:
                orig_f1 = original.loc[orig_model, ("macro_f1", "mean")]
                orig_auc = original.loc[orig_model, ("auc_ovr", "mean")]
                print(f"  {model}: F1 {orig_f1:.3f} → {new_f1:.3f} (Δ{new_f1-orig_f1:+.3f}), "
                      f"AUC {orig_auc:.3f} → {new_auc:.3f} (Δ{new_auc-orig_auc:+.3f})")


if __name__ == "__main__":
    main()
