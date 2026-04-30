"""Step 03 — 30주 조기 예측 모델 재설계.

기존 모델의 Growth Recall 7.3% 한계 극복을 위한 feature engineering · class imbalance 대응 · 다모형 벤치마크.

Pipeline:
  1) 30주 주간 매출 시퀀스에서 30+개 공학적 feature 추출
  2) Logistic, RF, XGBoost, LightGBM (+ optionally LSTM) 비교
  3) Stratified 5-fold CV; Macro-F1 / per-class Recall / AUC-OvR
  4) 결과 저장
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (classification_report, confusion_matrix, f1_score,
                             precision_recall_fscore_support, roc_auc_score)
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
try:
    import lightgbm as lgb
    HAS_LGB = False
except ImportError:
    HAS_LGB = False


def load_panel_with_labels():
    panel = pd.read_parquet(cfg.PANEL_PATH)
    panel["public_id"] = panel["public_id"].astype(str)
    feats = pd.read_csv(cfg.FEATURES_PATH)
    feats["public_id"] = feats["public_id"].astype(str)
    return panel, feats


def _slope(y: np.ndarray) -> float:
    x = np.arange(len(y), dtype=float)
    if np.isnan(y).all() or np.nanstd(y) == 0:
        return 0.0
    mask = ~np.isnan(y)
    if mask.sum() < 3:
        return 0.0
    s, *_ = stats.linregress(x[mask], y[mask])
    return float(s)


def _volatility(y: np.ndarray, window: int = 4) -> float:
    if len(y) < window or np.isnan(y).all():
        return 0.0
    rolling_std = pd.Series(y).rolling(window, min_periods=window // 2).std()
    mean = np.nanmean(y)
    return float(np.nanmean(rolling_std) / mean) if mean else 0.0


def extract_features_for_store(g: pd.DataFrame, weeks: int = 30) -> dict | None:
    g = g.sort_values("observed_week_idx")
    g = g[g["observed_week_idx"] < weeks]
    if len(g) < weeks // 2:
        return None

    sales = g["sales_card"].to_numpy(dtype=float)
    cust = g["customer"].to_numpy(dtype=float)
    cust_new = g.get("customer_new", pd.Series(np.zeros(len(g)))).to_numpy(dtype=float)
    before_noon = g.get("before_noon_sales", pd.Series(np.zeros(len(g)))).to_numpy(dtype=float)
    weekend = g.get("weekend_sales", pd.Series(np.zeros(len(g)))).to_numpy(dtype=float)
    delivery = g.get("sales_delivery", pd.Series(np.zeros(len(g)))).to_numpy(dtype=float)

    sales_log = np.log1p(sales)
    feats: dict[str, float] = {}

    feats["sales_mean"] = float(np.nanmean(sales_log))
    feats["sales_std"] = float(np.nanstd(sales_log))
    feats["sales_median"] = float(np.nanmedian(sales_log))
    feats["sales_cv"] = float(feats["sales_std"] / (feats["sales_mean"] + 1e-9))
    feats["sales_min"] = float(np.nanmin(sales_log))
    feats["sales_max"] = float(np.nanmax(sales_log))
    feats["sales_range"] = feats["sales_max"] - feats["sales_min"]
    feats["sales_skew"] = float(stats.skew(sales_log, nan_policy="omit"))
    feats["sales_kurt"] = float(stats.kurtosis(sales_log, nan_policy="omit"))

    feats["slope_all"] = _slope(sales_log)
    n = len(sales_log)
    third = max(3, n // 3)
    feats["slope_1_10"] = _slope(sales_log[:third])
    feats["slope_11_20"] = _slope(sales_log[third:2 * third])
    feats["slope_21_30"] = _slope(sales_log[2 * third:])
    feats["slope_accel"] = feats["slope_21_30"] - feats["slope_1_10"]

    for win in [5, 10, 15]:
        if len(sales_log) >= win:
            ma = pd.Series(sales_log).rolling(win, min_periods=win // 2).mean().to_numpy()
            feats[f"ma{win}_slope"] = _slope(ma)
            feats[f"ma{win}_std"] = float(np.nanstd(ma))
    feats["vol_w4"] = _volatility(sales_log, 4)
    feats["vol_w8"] = _volatility(sales_log, 8)

    with np.errstate(divide="ignore", invalid="ignore"):
        nc_ratio = np.where(cust > 0, cust_new / cust, np.nan)
    feats["nc_mean"] = float(np.nanmean(nc_ratio))
    feats["nc_std"] = float(np.nanstd(nc_ratio))
    feats["nc_slope"] = _slope(nc_ratio[~np.isnan(nc_ratio)])
    feats["nc_last4"] = float(np.nanmean(nc_ratio[-4:])) if len(nc_ratio) >= 4 else feats["nc_mean"]
    feats["nc_first4"] = float(np.nanmean(nc_ratio[:4])) if len(nc_ratio) >= 4 else feats["nc_mean"]
    feats["nc_delta"] = feats["nc_last4"] - feats["nc_first4"]

    cust_log = np.log1p(cust)
    feats["cust_slope"] = _slope(cust_log)
    feats["cust_mean"] = float(np.nanmean(cust_log))
    feats["cust_cv"] = float(np.nanstd(cust_log) / (np.nanmean(cust_log) + 1e-9))

    with np.errstate(divide="ignore", invalid="ignore"):
        del_ratio = np.where(sales > 0, delivery / sales, 0.0)
        bn_ratio = np.where(sales > 0, before_noon / sales, 0.0)
        wk_ratio = np.where(sales > 0, weekend / sales, 0.0)
    feats["del_mean"] = float(np.nanmean(del_ratio))
    feats["del_slope"] = _slope(del_ratio)
    feats["bn_mean"] = float(np.nanmean(bn_ratio))
    feats["wk_mean"] = float(np.nanmean(wk_ratio))

    q1, q2, q3 = np.nanquantile(sales_log, [0.25, 0.5, 0.75])
    feats["q25"] = float(q1)
    feats["q50"] = float(q2)
    feats["q75"] = float(q3)
    feats["iqr"] = float(q3 - q1)

    if len(sales_log) > 4:
        diff = np.diff(sales_log)
        feats["diff_mean"] = float(np.nanmean(diff))
        feats["diff_std"] = float(np.nanstd(diff))
        feats["diff_max_abs"] = float(np.nanmax(np.abs(diff)))
        feats["zero_cross"] = int(np.sum(np.diff(np.sign(diff)) != 0))

    return feats


def build_feature_matrix(panel: pd.DataFrame, feats_labeled: pd.DataFrame):
    print("[03] Extracting 30-week features (vectorized) ...")
    panel = panel[panel["observed_week_idx"] < cfg.PREDICTION_WEEKS].copy()
    panel = panel.sort_values(["public_id", "observed_week_idx"])

    sales = panel.pivot_table(index="public_id", columns="observed_week_idx", values="sales_card", aggfunc="mean")
    cust = panel.pivot_table(index="public_id", columns="observed_week_idx", values="customer", aggfunc="mean").reindex_like(sales)
    cust_new = panel.pivot_table(index="public_id", columns="observed_week_idx", values="customer_new", aggfunc="mean").reindex_like(sales)
    delivery = panel.pivot_table(index="public_id", columns="observed_week_idx", values="sales_delivery", aggfunc="mean").reindex_like(sales)
    before_noon = panel.pivot_table(index="public_id", columns="observed_week_idx", values="before_noon_sales", aggfunc="mean").reindex_like(sales)
    weekend = panel.pivot_table(index="public_id", columns="observed_week_idx", values="weekend_sales", aggfunc="mean").reindex_like(sales)

    valid = sales.notna().sum(axis=1) >= (cfg.PREDICTION_WEEKS // 2)
    sales = sales.loc[valid].sort_index(axis=1)
    cust = cust.loc[valid].sort_index(axis=1)
    cust_new = cust_new.loc[valid].sort_index(axis=1)
    delivery = delivery.loc[valid].sort_index(axis=1)
    before_noon = before_noon.loc[valid].sort_index(axis=1)
    weekend = weekend.loc[valid].sort_index(axis=1)

    s = np.log1p(sales.to_numpy(dtype=float))
    c = cust.to_numpy(dtype=float)
    cn = cust_new.to_numpy(dtype=float)
    d = delivery.fillna(0.0).to_numpy(dtype=float)
    bn = before_noon.to_numpy(dtype=float)
    wk = weekend.to_numpy(dtype=float)
    raw = sales.to_numpy(dtype=float)
    ids = sales.index.astype(str).to_numpy()
    x = np.arange(s.shape[1], dtype=float)

    def row_slope(mat: np.ndarray) -> np.ndarray:
        out = np.zeros(mat.shape[0], dtype=float)
        for i in range(mat.shape[0]):
            mask = np.isfinite(mat[i])
            if mask.sum() < 3 or np.nanstd(mat[i, mask]) < 1e-12:
                continue
            out[i] = stats.linregress(x[mask], mat[i, mask]).slope
        return out

    def row_slope_slice(mat: np.ndarray, start: int, end: int) -> np.ndarray:
        sub = mat[:, start:end]
        xx = np.arange(sub.shape[1], dtype=float)
        out = np.zeros(sub.shape[0], dtype=float)
        for i in range(sub.shape[0]):
            mask = np.isfinite(sub[i])
            if mask.sum() < 3 or np.nanstd(sub[i, mask]) < 1e-12:
                continue
            out[i] = stats.linregress(xx[mask], sub[i, mask]).slope
        return out

    n = s.shape[1]
    third = max(3, n // 3)
    with np.errstate(divide="ignore", invalid="ignore"):
        nc_ratio = np.where(c > 0, cn / c, np.nan)
        del_ratio = np.where(raw > 0, d / raw, 0.0)

    diff = np.diff(s, axis=1)
    zero_cross = np.sum(np.diff(np.sign(np.nan_to_num(diff, nan=0.0)), axis=1) != 0, axis=1)

    ma_features = {}
    for win in [5, 10, 15]:
        ma = pd.DataFrame(s).rolling(win, axis=1, min_periods=win // 2).mean().to_numpy()
        ma_features[f"ma{win}_slope"] = row_slope(ma)
        ma_features[f"ma{win}_std"] = np.nanstd(ma, axis=1)

    feat_df = pd.DataFrame({
        "public_id": ids,
        "sales_mean": np.nanmean(s, axis=1),
        "sales_std": np.nanstd(s, axis=1),
        "sales_median": np.nanmedian(s, axis=1),
        "sales_min": np.nanmin(s, axis=1),
        "sales_max": np.nanmax(s, axis=1),
        "sales_skew": stats.skew(s, axis=1, nan_policy="omit"),
        "sales_kurt": stats.kurtosis(s, axis=1, nan_policy="omit"),
        "slope_all": row_slope(s),
        "slope_1_10": row_slope_slice(s, 0, third),
        "slope_11_20": row_slope_slice(s, third, 2 * third),
        "slope_21_30": row_slope_slice(s, 2 * third, n),
        "vol_w4": pd.DataFrame(s).rolling(4, axis=1, min_periods=2).std().mean(axis=1).to_numpy() / (np.nanmean(s, axis=1) + 1e-9),
        "vol_w8": pd.DataFrame(s).rolling(8, axis=1, min_periods=4).std().mean(axis=1).to_numpy() / (np.nanmean(s, axis=1) + 1e-9),
        "nc_mean": np.nanmean(nc_ratio, axis=1),
        "nc_std": np.nanstd(nc_ratio, axis=1),
        "nc_slope": row_slope(nc_ratio),
        "nc_last4": np.nanmean(nc_ratio[:, -4:], axis=1),
        "nc_first4": np.nanmean(nc_ratio[:, :4], axis=1),
        "cust_slope": row_slope(np.log1p(c)),
        "cust_mean": np.nanmean(np.log1p(c), axis=1),
        "cust_cv": np.nanstd(np.log1p(c), axis=1) / (np.nanmean(np.log1p(c), axis=1) + 1e-9),
        "del_mean": np.nanmean(del_ratio, axis=1),
        "del_slope": row_slope(del_ratio),
        "bn_mean": np.nanmean(bn, axis=1),
        "wk_mean": np.nanmean(wk, axis=1),
        "q25": np.nanquantile(s, 0.25, axis=1),
        "q50": np.nanquantile(s, 0.50, axis=1),
        "q75": np.nanquantile(s, 0.75, axis=1),
        "diff_mean": np.nanmean(diff, axis=1),
        "diff_std": np.nanstd(diff, axis=1),
        "diff_max_abs": np.nanmax(np.abs(diff), axis=1),
        "zero_cross": zero_cross,
    })
    feat_df["sales_cv"] = feat_df["sales_std"] / (feat_df["sales_mean"] + 1e-9)
    feat_df["sales_range"] = feat_df["sales_max"] - feat_df["sales_min"]
    feat_df["slope_accel"] = feat_df["slope_21_30"] - feat_df["slope_1_10"]
    feat_df["nc_delta"] = feat_df["nc_last4"] - feat_df["nc_first4"]
    feat_df["iqr"] = feat_df["q75"] - feat_df["q25"]
    for k, v in ma_features.items():
        feat_df[k] = v

    ordered = [
        "sales_mean", "sales_std", "sales_median", "sales_cv", "sales_min", "sales_max",
        "sales_range", "sales_skew", "sales_kurt", "slope_all", "slope_1_10",
        "slope_11_20", "slope_21_30", "slope_accel", "ma5_slope", "ma5_std",
        "ma10_slope", "ma10_std", "ma15_slope", "ma15_std", "vol_w4", "vol_w8",
        "nc_mean", "nc_std", "nc_slope", "nc_last4", "nc_first4", "nc_delta",
        "cust_slope", "cust_mean", "cust_cv", "del_mean", "del_slope", "bn_mean",
        "wk_mean", "q25", "q50", "q75", "iqr", "diff_mean", "diff_std",
        "diff_max_abs", "zero_cross", "public_id",
    ]
    feat_df = feat_df[ordered]
    feat_df = feat_df.merge(feats_labeled[["public_id", "outcome_3", "label"]], on="public_id", how="inner")
    feat_df = feat_df.dropna(subset=["outcome_3"])
    print(f"[03] Feature matrix: {feat_df.shape}")
    return feat_df


def evaluate_model(name: str, model, X_train, y_train, X_test, y_test, classes):
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X_test)
    else:
        proba = None

    per_class = precision_recall_fscore_support(y_test, preds, labels=classes, zero_division=0)
    macro_f1 = f1_score(y_test, preds, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_test, preds, average="weighted", zero_division=0)

    auc = np.nan
    if proba is not None and len(classes) > 1:
        try:
            auc = roc_auc_score(pd.get_dummies(y_test)[classes].values, proba, multi_class="ovr")
        except Exception:
            auc = np.nan

    row = {
        "model": name,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "auc_ovr": auc,
    }
    for i, c in enumerate(classes):
        row[f"precision_{c}"] = per_class[0][i]
        row[f"recall_{c}"] = per_class[1][i]
        row[f"f1_{c}"] = per_class[2][i]
    return row, preds, proba


def run_cv(feat_df: pd.DataFrame):
    classes = cfg.OUTCOME_CLASSES
    X = feat_df.drop(columns=["public_id", "outcome_3", "label"]).fillna(0.0)
    y = feat_df["outcome_3"].values

    feature_names = X.columns.tolist()
    json.dump(feature_names, open(cfg.TABLE_DIR / "prediction_features.json", "w"), indent=2)

    skf = StratifiedKFold(n_splits=cfg.CV_FOLDS, shuffle=True, random_state=cfg.SEED)

    models_factory: dict[str, callable] = {
        "Logistic": lambda: LogisticRegression(max_iter=2000, class_weight="balanced", random_state=cfg.SEED),
        "RandomForest": lambda: RandomForestClassifier(
            n_estimators=400, max_depth=12, class_weight="balanced",
            n_jobs=-1, random_state=cfg.SEED),
    }
    if HAS_XGB:
        cw = {c: 1.0 for c in classes}
        cnt = pd.Series(y).value_counts()
        for c in classes:
            cw[c] = len(y) / (len(classes) * cnt.get(c, 1))

        def make_xgb():
            return xgb.XGBClassifier(
                n_estimators=160, max_depth=4, learning_rate=0.08,
                subsample=0.9, colsample_bytree=0.9, min_child_weight=2,
                objective="multi:softprob", num_class=len(classes),
                eval_metric="mlogloss", tree_method="hist", n_jobs=4,
                random_state=cfg.SEED,
            )
        models_factory["XGBoost"] = make_xgb
    if HAS_LGB:
        models_factory["LightGBM"] = lambda: lgb.LGBMClassifier(
            n_estimators=500, max_depth=-1, num_leaves=63, learning_rate=0.05,
            subsample=0.9, colsample_bytree=0.9, class_weight="balanced",
            n_jobs=-1, random_state=cfg.SEED, verbosity=-1,
        )

    class_to_idx = {c: i for i, c in enumerate(classes)}
    y_enc = np.array([class_to_idx[v] for v in y])

    all_rows = []
    fold_conf_mats = {name: np.zeros((len(classes), len(classes)), dtype=int) for name in models_factory}
    fold_feat_imp = {name: np.zeros(len(feature_names)) for name in models_factory if name in {"RandomForest", "XGBoost", "LightGBM"}}

    for fold, (tr, te) in enumerate(skf.split(X, y_enc)):
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X.iloc[tr])
        X_test = scaler.transform(X.iloc[te])
        y_train_enc, y_test_enc = y_enc[tr], y_enc[te]
        y_train, y_test = y[tr], y[te]

        for name, factory in models_factory.items():
            model = factory()
            if name == "XGBoost":
                model.fit(X_train, y_train_enc)
                preds_enc = model.predict(X_test)
                preds = np.array([classes[i] for i in preds_enc])
                proba = model.predict_proba(X_test)
                per_class = precision_recall_fscore_support(y_test, preds, labels=classes, zero_division=0)
                macro_f1 = f1_score(y_test, preds, average="macro", zero_division=0)
                weighted_f1 = f1_score(y_test, preds, average="weighted", zero_division=0)
                try:
                    auc = roc_auc_score(pd.get_dummies(y_test)[classes].values, proba, multi_class="ovr")
                except Exception:
                    auc = np.nan
                row = {
                    "model": name, "fold": fold, "macro_f1": macro_f1,
                    "weighted_f1": weighted_f1, "auc_ovr": auc,
                }
                for i, c in enumerate(classes):
                    row[f"precision_{c}"] = per_class[0][i]
                    row[f"recall_{c}"] = per_class[1][i]
                    row[f"f1_{c}"] = per_class[2][i]
                fold_feat_imp[name] += model.feature_importances_
            else:
                row, preds, proba = evaluate_model(name, model, X_train, y_train, X_test, y_test, classes)
                row["fold"] = fold
                if hasattr(model, "feature_importances_") and name in fold_feat_imp:
                    fold_feat_imp[name] += model.feature_importances_

            cm = confusion_matrix(y_test, preds, labels=classes)
            fold_conf_mats[name] += cm
            all_rows.append(row)
            print(f"  fold={fold} {name:12s} macro_F1={row['macro_f1']:.3f} "
                  f"growth_recall={row.get('recall_Growth', 0):.3f} "
                  f"decline_recall={row.get('recall_Decline', 0):.3f}")

    fold_df = pd.DataFrame(all_rows)
    fold_df.to_csv(cfg.TABLE_DIR / "prediction_cv_folds.csv", index=False, encoding="utf-8-sig")

    agg = fold_df.groupby("model").agg(["mean", "std"]).round(4)
    agg.to_csv(cfg.TABLE_DIR / "prediction_cv_summary.csv", encoding="utf-8-sig")

    for name, cm in fold_conf_mats.items():
        pd.DataFrame(cm, index=classes, columns=classes).to_csv(
            cfg.TABLE_DIR / f"confusion_{name}.csv", encoding="utf-8-sig"
        )

    for name, imp in fold_feat_imp.items():
        imp_df = pd.DataFrame({"feature": feature_names, "importance": imp / cfg.CV_FOLDS})
        imp_df = imp_df.sort_values("importance", ascending=False)
        imp_df.to_csv(cfg.TABLE_DIR / f"feature_importance_{name}.csv", index=False, encoding="utf-8-sig")

    return fold_df, agg


def main():
    panel, feats_labeled = load_panel_with_labels()
    mat_path = cfg.TABLE_DIR / "prediction_feature_matrix.parquet"
    rebuild = True
    if mat_path.exists():
        print(f"[03] Loading cached feature matrix: {mat_path}")
        feat_df = pd.read_parquet(mat_path)
        cached_ids = set(feat_df["public_id"].astype(str))
        current_ids = set(feats_labeled.dropna(subset=["outcome_3"])["public_id"].astype(str))
        rebuild = cached_ids != current_ids
        if rebuild:
            print(
                "[03] cached matrix does not match current labels "
                f"(cached={len(cached_ids):,}, current={len(current_ids):,}); rebuilding"
            )
    if rebuild:
        feat_df = build_feature_matrix(panel, feats_labeled)
        feat_df.to_parquet(mat_path, index=False)
        print(f"[03] Saved feature matrix: {mat_path}")

    fold_df, agg = run_cv(feat_df)
    print("\n=== Summary (mean ± std across folds) ===")
    print(agg[[("macro_f1", "mean"), ("macro_f1", "std"),
               ("recall_Growth", "mean"), ("recall_Decline", "mean"),
               ("auc_ovr", "mean")]].to_string())


if __name__ == "__main__":
    main()
