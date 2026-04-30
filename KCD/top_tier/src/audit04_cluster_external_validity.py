"""Audit 04 — Cluster external validity의 분리 검증.

기존 step04에서 UDX label vs outcome_3 을 external validation으로 함께 다뤘음.
그러나 UDX 업종 label은 outcome_3와 상관 가능 → cluster-UDX 일치가
"업종 재현" vs "lifecycle 포착" 구분 불가.

본 audit:
  (a) NMI(cluster, UDX) vs NMI(cluster, outcome_3) 분리
  (b) conditional MI: UDX 통제 후 cluster가 outcome에 주는 추가 정보
  (c) Best cluster (K, method)의 outcome 예측력 단독 사용 시 F1
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (adjusted_rand_score, f1_score,
                             normalized_mutual_info_score, roc_auc_score)
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg  # noqa: E402


def conditional_mutual_information(x, y, z):
    """I(X; Y | Z) 근사 (bin-based)."""
    df = pd.DataFrame({"x": x, "y": y, "z": z})
    def _mi(a, b):
        return normalized_mutual_info_score(a, b)
    cond = 0.0
    for zv, sub in df.groupby("z"):
        if len(sub) < 10:
            continue
        w = len(sub) / len(df)
        cond += w * _mi(sub["x"], sub["y"])
    return cond


def main():
    clu = pd.read_csv(cfg.TABLE_DIR / "hybrid_cluster_assignments.csv")
    clu["public_id"] = clu["public_id"].astype(str)
    feat = pd.read_parquet(cfg.TABLE_DIR / "prediction_feature_matrix.parquet")
    feat["public_id"] = feat["public_id"].astype(str)
    meta = pd.read_csv(cfg.META_PATH)
    meta["public_id"] = meta["public_id"].astype(str)
    udx_col = "classification__kcd_v3__depth_2_name"

    df = clu.merge(feat[["public_id", "outcome_3"]], on="public_id", how="inner")
    df = df.merge(meta[["public_id", udx_col]], on="public_id", how="left")
    df = df.dropna(subset=["outcome_3"])
    df["udx"] = df[udx_col].fillna("Unknown")
    print(f"[audit04] merged rows: {len(df):,}")

    rows = []
    for cluster_col in ["km_cluster", "ks_cluster"]:
        if cluster_col not in df.columns:
            continue
        nmi_udx = normalized_mutual_info_score(df[cluster_col], df["udx"])
        nmi_outcome = normalized_mutual_info_score(df[cluster_col], df["outcome_3"])
        ari_udx = adjusted_rand_score(df[cluster_col], df["udx"])
        ari_outcome = adjusted_rand_score(df[cluster_col], df["outcome_3"])
        cond_mi = conditional_mutual_information(df[cluster_col].astype(str),
                                                  df["outcome_3"].astype(str),
                                                  df["udx"].astype(str))
        nmi_outcome_given_udx = cond_mi
        rows.append({
            "cluster": cluster_col,
            "nmi_vs_udx": nmi_udx, "ari_vs_udx": ari_udx,
            "nmi_vs_outcome": nmi_outcome, "ari_vs_outcome": ari_outcome,
            "nmi_cluster_outcome_given_udx": nmi_outcome_given_udx,
        })

    print("\n=== Cluster external validity — UDX와 outcome_3 분리 ===")
    df_ext = pd.DataFrame(rows).round(4)
    df_ext.to_csv(cfg.TABLE_DIR / "audit04_cluster_external_validity.csv",
                   index=False, encoding="utf-8-sig")
    print(df_ext.to_string(index=False))

    print("\n=== Cluster만으로 outcome 예측 (one-hot, logistic 5-fold) ===")
    classes = cfg.OUTCOME_CLASSES
    res = []
    for cluster_col in ["km_cluster", "ks_cluster"]:
        if cluster_col not in df.columns:
            continue
        X = pd.get_dummies(df[cluster_col]).values.astype(float)
        y = df["outcome_3"].values
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=cfg.SEED)
        f1s, aucs = [], []
        c2i = {c: i for i, c in enumerate(classes)}
        y_enc = np.array([c2i[v] for v in y])
        for tr, te in skf.split(X, y):
            sc = StandardScaler(with_mean=False)
            Xtr = sc.fit_transform(X[tr])
            Xte = sc.transform(X[te])
            m = LogisticRegression(max_iter=500, C=1.0).fit(Xtr, y_enc[tr])
            p = m.predict_proba(Xte)
            pred = np.array([classes[i] for i in p.argmax(1)])
            f1s.append(f1_score(y[te], pred, average="macro", zero_division=0))
            try:
                aucs.append(roc_auc_score(pd.get_dummies(y[te])[classes].values,
                                           p, multi_class="ovr"))
            except Exception:
                aucs.append(np.nan)
        res.append({"cluster": cluster_col, "f1_alone": np.mean(f1s),
                   "auc_alone": np.mean(aucs)})
    df_pred = pd.DataFrame(res).round(4)
    df_pred.to_csv(cfg.TABLE_DIR / "audit04_cluster_alone_prediction.csv",
                    index=False, encoding="utf-8-sig")
    print(df_pred.to_string(index=False))

    print("\n=== UDX alone vs cluster alone 비교 ===")
    y = df["outcome_3"].values
    X_udx = pd.get_dummies(df["udx"]).values.astype(float)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=cfg.SEED)
    classes = cfg.OUTCOME_CLASSES
    c2i = {c: i for i, c in enumerate(classes)}
    y_enc = np.array([c2i[v] for v in y])
    f1s, aucs = [], []
    for tr, te in skf.split(X_udx, y):
        sc = StandardScaler(with_mean=False)
        Xtr = sc.fit_transform(X_udx[tr])
        Xte = sc.transform(X_udx[te])
        m = LogisticRegression(max_iter=500, C=1.0).fit(Xtr, y_enc[tr])
        p = m.predict_proba(Xte)
        pred = np.array([classes[i] for i in p.argmax(1)])
        f1s.append(f1_score(y[te], pred, average="macro", zero_division=0))
        try:
            aucs.append(roc_auc_score(pd.get_dummies(y[te])[classes].values, p, multi_class="ovr"))
        except Exception:
            aucs.append(np.nan)
    print(f"  UDX alone: F1={np.mean(f1s):.3f} AUC={np.mean(aucs):.3f}")


if __name__ == "__main__":
    main()
