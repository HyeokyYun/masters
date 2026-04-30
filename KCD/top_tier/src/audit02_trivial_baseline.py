"""Audit 02 — "Trivial" baseline 성능 측정.

audit01에서 slope_early가 outcome_3을 강하게 예측함을 확인.
"30주 조기 예측"이라는 framing의 실질적 novelty를 측정:
  - Baseline B0: slope_early 하나만으로 logistic regression
  - Baseline B1: slope_early + slope_early sign (3 feature)
  - Baseline B2: slope_early + cv + nc_rate (3 feature)
  - Proposed A (46 feature), D (61 feature) 과 비교

"trivial baseline 대비 incremental lift"를 정량화해야 "조기 예측 모델의 가치" 주장이 성립.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg  # noqa: E402


def compute_slope_on_30w(panel: pd.DataFrame) -> pd.DataFrame:
    """점포별 첫 30주 log-sales slope 계산 (prediction 시나리오 준수)."""
    panel = panel[panel["observed_week_idx"] < cfg.PREDICTION_WEEKS].copy()
    panel["sales_log"] = np.log1p(panel["sales_card"].fillna(0))
    rows = []
    for pid, g in panel.groupby("public_id", observed=True, sort=False):
        g = g.sort_values("observed_week_idx")
        y = g["sales_log"].to_numpy()
        x = g["observed_week_idx"].to_numpy().astype(float)
        if len(y) < 10 or np.std(y) < 1e-9:
            rows.append({"public_id": pid, "slope_early_30w": 0.0, "cv_30w": 0.0,
                         "mean_log_30w": float(np.mean(y)) if len(y) else 0.0})
            continue
        s, *_ = stats.linregress(x, y)
        cv_30 = float(np.std(y) / (abs(np.mean(y)) + 1e-9))
        rows.append({"public_id": pid, "slope_early_30w": float(s),
                     "cv_30w": cv_30, "mean_log_30w": float(np.mean(y))})
    return pd.DataFrame(rows)


def run_cv(X, y, classes, label):
    skf = StratifiedKFold(n_splits=cfg.CV_FOLDS, shuffle=True, random_state=cfg.SEED)
    c2i = {c: i for i, c in enumerate(classes)}
    y_enc = np.array([c2i[v] for v in y])
    f1s, aucs, rec_g, rec_d = [], [], [], []
    for fold, (tr, te) in enumerate(skf.split(X, y)):
        scaler = StandardScaler()
        Xtr = scaler.fit_transform(X[tr])
        Xte = scaler.transform(X[te])
        model = LogisticRegression(max_iter=1000, C=1.0)
        model.fit(Xtr, y_enc[tr])
        proba = model.predict_proba(Xte)
        preds = np.array([classes[i] for i in proba.argmax(1)])
        f1s.append(f1_score(y[te], preds, average="macro", zero_division=0))
        try:
            aucs.append(roc_auc_score(pd.get_dummies(y[te])[classes].values,
                                      proba, multi_class="ovr"))
        except Exception:
            aucs.append(np.nan)
        rec_g.append(((preds == "Growth") & (y[te] == "Growth")).sum() / max((y[te] == "Growth").sum(), 1))
        rec_d.append(((preds == "Decline") & (y[te] == "Decline")).sum() / max((y[te] == "Decline").sum(), 1))
    return {"label": label, "f1_mean": np.mean(f1s), "f1_std": np.std(f1s),
            "auc_mean": np.mean(aucs), "rec_g_mean": np.mean(rec_g),
            "rec_d_mean": np.mean(rec_d), "n_features": X.shape[1]}


def main():
    panel = pd.read_parquet(cfg.PANEL_PATH)
    panel["public_id"] = panel["public_id"].astype(str)
    feats_labeled = pd.read_csv(cfg.FEATURES_PATH)
    feats_labeled["public_id"] = feats_labeled["public_id"].astype(str)
    feat_matrix = pd.read_parquet(cfg.TABLE_DIR / "prediction_feature_matrix.parquet")
    feat_matrix["public_id"] = feat_matrix["public_id"].astype(str)

    print("[audit02] computing slope on first 30w ...")
    s30 = compute_slope_on_30w(panel)
    print(f"[audit02] slope_30w computed for {len(s30):,} stores")

    merged = feat_matrix.merge(s30, on="public_id", how="inner")
    merged = merged.dropna(subset=["outcome_3"])
    y = merged["outcome_3"].values
    classes = cfg.OUTCOME_CLASSES

    print(f"[audit02] merged: {len(merged):,} stores, outcome_3 dist:")
    print(merged["outcome_3"].value_counts().to_string())

    results = []

    X_b0 = merged[["slope_early_30w"]].values.astype(float)
    results.append(run_cv(X_b0, y, classes, "B0_slope_early_only"))

    X_b1 = merged[["slope_early_30w", "cv_30w", "mean_log_30w"]].values.astype(float)
    results.append(run_cv(X_b1, y, classes, "B1_slope_cv_mean_30w"))

    proposed_cols = [c for c in feat_matrix.columns if c not in {"public_id", "outcome_3", "label"}]
    X_a = merged[proposed_cols].fillna(0.0).values.astype(float)
    results.append(run_cv(X_a, y, classes, "A_base_46"))

    df = pd.DataFrame(results)
    df = df.round(4)
    df.to_csv(cfg.TABLE_DIR / "audit02_trivial_baseline.csv", index=False, encoding="utf-8-sig")
    print("\n=== Trivial vs Full Feature Baselines (Logistic Regression 5-fold CV) ===")
    print(df.to_string(index=False))
    print()
    b0 = df.iloc[0]
    a = df.iloc[-1]
    print(f"[audit02] Incremental lift A vs B0: F1 +{a['f1_mean']-b0['f1_mean']:+.3f}, "
          f"AUC +{a['auc_mean']-b0['auc_mean']:+.3f}")
    print(f"[audit02] 즉, 46 features는 slope-only 대비 F1/AUC 개선 이만큼이 'novelty' 의 수치적 증거.")


if __name__ == "__main__":
    main()
