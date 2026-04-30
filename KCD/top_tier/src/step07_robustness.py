"""Step 07 — Robustness Checks.

(1) Subgroup analysis: 업종별 / 시기별 / 업력별 예측 성능
(2) Bootstrap confidence intervals for model metrics
(3) Temporal validation: 초기 개업 점포 train → 후기 개업 점포 test
(4) Ablation study: feature group별 제거

Output: outputs/tables/robustness_*.csv
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg  # noqa: E402

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False


def load_feat_with_meta():
    feat = pd.read_parquet(cfg.TABLE_DIR / "prediction_feature_matrix.parquet")
    meta = pd.read_csv(cfg.META_PATH)
    meta["public_id"] = meta["public_id"].astype(str)
    meta["open_date"] = pd.to_datetime(meta["open_month"].astype(str), format="%Y-%m", errors="coerce")
    feat["public_id"] = feat["public_id"].astype(str)
    return feat.merge(meta[["public_id", "classification__kcd_v3__depth_2_name", "open_date", "age"]],
                     on="public_id", how="left")


def train_eval(X_tr, y_tr, X_te, y_te, classes):
    model = xgb.XGBClassifier(
        n_estimators=400, max_depth=6, learning_rate=0.05,
        subsample=0.9, colsample_bytree=0.9, min_child_weight=2,
        objective="multi:softprob", num_class=len(classes),
        eval_metric="mlogloss", tree_method="hist", n_jobs=-1,
        random_state=cfg.SEED,
    )
    c2i = {c: i for i, c in enumerate(classes)}
    y_tr_enc = np.array([c2i[v] for v in y_tr])
    y_te_enc = np.array([c2i[v] for v in y_te])
    model.fit(X_tr, y_tr_enc)
    preds_enc = model.predict(X_te)
    preds = np.array([classes[i] for i in preds_enc])
    per_class = precision_recall_fscore_support(y_te, preds, labels=classes, zero_division=0)
    return {
        "macro_f1": f1_score(y_te, preds, average="macro", zero_division=0),
        **{f"recall_{c}": per_class[1][i] for i, c in enumerate(classes)},
        **{f"f1_{c}": per_class[2][i] for i, c in enumerate(classes)},
    }


def subgroup_analysis(df: pd.DataFrame, classes):
    print("[07] Subgroup analysis — by category ...")
    feat_cols = [c for c in df.columns if c not in {
        "public_id", "outcome_3", "label",
        "classification__kcd_v3__depth_2_name", "open_date", "age"}]

    rows = []
    cats = df["classification__kcd_v3__depth_2_name"].value_counts()
    cats = cats[cats >= 1000].index.tolist()

    for cat in cats:
        sub = df[df["classification__kcd_v3__depth_2_name"] == cat]
        X = sub[feat_cols].fillna(0.0)
        y = sub["outcome_3"].values
        if len(np.unique(y)) < 3 or len(sub) < 500:
            continue
        skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=cfg.SEED)
        fold_scores = []
        for tr, te in skf.split(X, y):
            scaler = StandardScaler()
            X_tr = scaler.fit_transform(X.iloc[tr])
            X_te = scaler.transform(X.iloc[te])
            r = train_eval(X_tr, y[tr], X_te, y[te], classes)
            fold_scores.append(r)
        avg = pd.DataFrame(fold_scores).mean().to_dict()
        rows.append({"subgroup": f"category:{cat}", "n": len(sub), **avg})

    return pd.DataFrame(rows)


def temporal_subgroup(df: pd.DataFrame, classes):
    print("[07] Temporal subgroup — by open year ...")
    df = df.dropna(subset=["open_date"]).copy()
    df["open_year"] = df["open_date"].dt.year
    rows = []
    for yr in sorted(df["open_year"].unique()):
        sub = df[df["open_year"] == yr]
        if len(sub) < 500 or sub["outcome_3"].nunique() < 3:
            continue
        feat_cols = [c for c in df.columns if c not in {
            "public_id", "outcome_3", "label",
            "classification__kcd_v3__depth_2_name", "open_date", "age", "open_year"}]
        X = sub[feat_cols].fillna(0.0)
        y = sub["outcome_3"].values
        skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=cfg.SEED)
        fold_scores = []
        for tr, te in skf.split(X, y):
            scaler = StandardScaler()
            r = train_eval(scaler.fit_transform(X.iloc[tr]), y[tr],
                          scaler.transform(X.iloc[te]), y[te], classes)
            fold_scores.append(r)
        avg = pd.DataFrame(fold_scores).mean().to_dict()
        rows.append({"subgroup": f"open_year:{yr}", "n": len(sub), **avg})
    return pd.DataFrame(rows)


def temporal_validation(df: pd.DataFrame, classes):
    print("[07] Temporal validation — early open vs late open ...")
    df = df.dropna(subset=["open_date"]).copy()
    med = df["open_date"].median()
    train = df[df["open_date"] < med]
    test = df[df["open_date"] >= med]
    feat_cols = [c for c in df.columns if c not in {
        "public_id", "outcome_3", "label",
        "classification__kcd_v3__depth_2_name", "open_date", "age"}]
    scaler = StandardScaler()
    X_tr = scaler.fit_transform(train[feat_cols].fillna(0.0))
    X_te = scaler.transform(test[feat_cols].fillna(0.0))
    r = train_eval(X_tr, train["outcome_3"].values, X_te, test["outcome_3"].values, classes)
    r["n_train"] = len(train)
    r["n_test"] = len(test)
    r["train_cutoff"] = str(med.date())
    return pd.DataFrame([r])


def bootstrap_metrics(df: pd.DataFrame, classes, n_boot: int = 200):
    print(f"[07] Bootstrap x {n_boot} ...")
    feat_cols = [c for c in df.columns if c not in {
        "public_id", "outcome_3", "label",
        "classification__kcd_v3__depth_2_name", "open_date", "age"}]
    X_all = df[feat_cols].fillna(0.0).values
    y_all = df["outcome_3"].values

    rng = np.random.RandomState(cfg.SEED)
    scores = []
    n = len(df)
    for b in range(n_boot):
        idx = rng.randint(0, n, n)
        oob = np.setdiff1d(np.arange(n), np.unique(idx))
        if len(oob) < 200:
            continue
        scaler = StandardScaler()
        X_tr = scaler.fit_transform(X_all[idx])
        X_te = scaler.transform(X_all[oob])
        r = train_eval(X_tr, y_all[idx], X_te, y_all[oob], classes)
        scores.append(r)
        if (b + 1) % 50 == 0:
            print(f"   boot {b+1}")
    sc_df = pd.DataFrame(scores)
    ci_rows = []
    for col in sc_df.columns:
        vals = sc_df[col].dropna().values
        ci_rows.append({
            "metric": col,
            "mean": float(vals.mean()),
            "ci_lower_2.5": float(np.quantile(vals, 0.025)),
            "ci_upper_97.5": float(np.quantile(vals, 0.975)),
        })
    return pd.DataFrame(ci_rows)


def ablation(df: pd.DataFrame, classes):
    print("[07] Ablation study ...")
    feat_cols = [c for c in df.columns if c not in {
        "public_id", "outcome_3", "label",
        "classification__kcd_v3__depth_2_name", "open_date", "age"}]
    groups = {
        "all": feat_cols,
        "no_nc": [c for c in feat_cols if not c.startswith("nc_")],
        "no_volatility": [c for c in feat_cols if c not in {"sales_cv", "sales_std", "vol_w4", "vol_w8"}
                          and not c.startswith("ma") and c != "diff_std"],
        "no_slope": [c for c in feat_cols if not c.startswith("slope")],
        "no_delivery_pattern": [c for c in feat_cols if c not in {"del_mean", "del_slope", "bn_mean", "wk_mean"}],
        "only_core_stats": ["sales_mean", "sales_std", "sales_median", "sales_cv", "slope_all",
                            "nc_mean", "cust_mean"],
    }
    rows = []
    for name, cols in groups.items():
        cols = [c for c in cols if c in df.columns]
        X = df[cols].fillna(0.0).values
        y = df["outcome_3"].values
        skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=cfg.SEED)
        fold_scores = []
        for tr, te in skf.split(X, y):
            scaler = StandardScaler()
            r = train_eval(scaler.fit_transform(X[tr]), y[tr],
                          scaler.transform(X[te]), y[te], classes)
            fold_scores.append(r)
        avg = pd.DataFrame(fold_scores).mean().to_dict()
        rows.append({"feature_group": name, "n_features": len(cols), **avg})
    return pd.DataFrame(rows)


def main():
    if not HAS_XGB:
        print("xgboost not available — abort")
        return
    df = load_feat_with_meta()
    classes = cfg.OUTCOME_CLASSES

    sub = subgroup_analysis(df, classes)
    sub.to_csv(cfg.TABLE_DIR / "robustness_subgroup_category.csv", index=False, encoding="utf-8-sig")
    print(sub.to_string(index=False))

    temp = temporal_subgroup(df, classes)
    temp.to_csv(cfg.TABLE_DIR / "robustness_subgroup_year.csv", index=False, encoding="utf-8-sig")
    print(temp.to_string(index=False))

    tval = temporal_validation(df, classes)
    tval.to_csv(cfg.TABLE_DIR / "robustness_temporal_validation.csv", index=False, encoding="utf-8-sig")
    print(tval.to_string(index=False))

    boot = bootstrap_metrics(df, classes, n_boot=200)
    boot.to_csv(cfg.TABLE_DIR / "robustness_bootstrap_ci.csv", index=False, encoding="utf-8-sig")
    print(boot.to_string(index=False))

    abl = ablation(df, classes)
    abl.to_csv(cfg.TABLE_DIR / "robustness_ablation.csv", index=False, encoding="utf-8-sig")
    print(abl.to_string(index=False))


if __name__ == "__main__":
    main()
