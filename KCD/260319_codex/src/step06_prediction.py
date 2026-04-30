from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

from src import config as cfg

warnings.filterwarnings("ignore")

try:
    import lightgbm as lgb

    HAS_LGB = True
except ImportError:
    HAS_LGB = False

try:
    import shap

    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False


def build_early_features(ts: pd.DataFrame, window: int | None = None) -> pd.DataFrame:
    window = window or cfg.EARLY_WEEKS
    records: list[dict[str, object]] = []
    for public_id, group in ts.groupby("public_id"):
        group = (
            group.sort_values("weeks_since_open")
            .drop_duplicates("weeks_since_open")
            .reset_index(drop=True)
        )
        early = group[group["weeks_since_open"] < window]
        full = group[group["weeks_since_open"] < cfg.MAX_WEEKS]
        if len(early) < 10 or len(full) < window + 20:
            continue

        y = early["sales_card_mm"].fillna(0).to_numpy(dtype=float)
        if not np.isfinite(y).all() or y.std() < 1e-9:
            continue

        t = np.arange(len(y), dtype=float)
        h = len(y) // 2
        s_all, _, r_all, _, _ = stats.linregress(t, y)
        if h > 2:
            s_early, _, _, _, _ = stats.linregress(t[:h], y[:h])
            s_late, _, _, _, _ = stats.linregress(t[h:] - h, y[h:])
        else:
            s_early = 0.0
            s_late = 0.0

        start_mean = float(np.mean(y[: min(cfg.PATTERN_EDGE_WEEKS, max(4, len(y) // 4))]))
        end_mean = float(np.mean(y[-min(cfg.PATTERN_EDGE_WEEKS, max(4, len(y) // 4)) :]))
        if abs(start_mean) < 1e-9:
            change_rate = 0.0 if abs(end_mean) < 1e-9 else (1.0 if end_mean > 0 else -1.0)
        else:
            change_rate = float((end_mean - start_mean) / abs(start_mean))

        cv = float(min(y.std() / (y.mean() + 1e-9), 2.0))
        mdd = float(((np.maximum.accumulate(y) - y) / (np.maximum.accumulate(y) + 1e-9)).max())

        nc_rate = np.nan
        if {"customer_new", "customer"}.issubset(early.columns):
            denom = early["customer"].replace(0, np.nan) + 1
            nc = early["customer_new"] / denom
            nc_rate = float(nc.mean()) if nc.notna().any() else np.nan

        records.append(
            {
                "public_id": public_id,
                "e_slope_all": float(s_all),
                "e_slope_early": float(s_early),
                "e_slope_late": float(s_late),
                "e_r2": float(r_all**2),
                "e_mean": float(y.mean()),
                "e_cv": cv,
                "e_mdd": mdd,
                "e_nc_rate": nc_rate,
                "e_start_mean": start_mean,
                "e_end_mean": end_mean,
                "e_overall_change_rate": change_rate,
            }
        )
    early_df = pd.DataFrame(records)
    early_df.to_csv(cfg.TABLE_DIR / "early_features.csv", index=False, encoding="utf-8-sig")
    return early_df


def _get_models():
    models = {
        "RF": RandomForestClassifier(
            n_estimators=200, class_weight="balanced", max_depth=8, random_state=cfg.SEED
        ),
        "GBM": GradientBoostingClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.1, subsample=0.8, random_state=cfg.SEED
        ),
    }
    if HAS_LGB:
        models["LightGBM"] = lgb.LGBMClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            class_weight="balanced",
            random_state=cfg.SEED,
            verbose=-1,
        )
    return models


def ablation_study(early_df: pd.DataFrame, labeled: pd.DataFrame) -> pd.DataFrame:
    merged = early_df.merge(labeled[["public_id", "final_code"]], on="public_id", how="inner")
    vc = merged["final_code"].value_counts()
    merged = merged[merged["final_code"].isin(vc[vc >= 30].index)].copy()

    feature_sets = {
        "Base": ["e_cv", "e_mdd", "e_mean"],
        "+Shape": ["e_cv", "e_mdd", "e_mean", "e_slope_all", "e_slope_early", "e_slope_late", "e_r2"],
        "+Customer": [
            "e_cv",
            "e_mdd",
            "e_mean",
            "e_slope_all",
            "e_slope_early",
            "e_slope_late",
            "e_r2",
            "e_nc_rate",
            "e_overall_change_rate",
        ],
    }

    rows = []
    for feature_name, columns in feature_sets.items():
        avail = [col for col in columns if col in merged.columns]
        X = merged[avail].to_numpy()
        y = merged["final_code"].to_numpy()
        for model_name, clf in _get_models().items():
            pipe = Pipeline(
                [("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler()), ("clf", clf)]
            )
            scores = cross_val_score(pipe, X, y, cv=cfg.CV_FOLDS, scoring="f1_weighted", error_score=0)
            rows.append(
                {
                    "Feature Set": feature_name,
                    "Model": model_name,
                    "F1_mean": float(scores.mean()),
                    "F1_std": float(scores.std()),
                }
            )
    ablation = pd.DataFrame(rows)
    ablation.to_csv(cfg.TABLE_DIR / "ablation_early_prediction_final_code.csv", index=False, encoding="utf-8-sig")
    return ablation


def full_evaluation(early_df: pd.DataFrame, labeled: pd.DataFrame) -> pd.DataFrame:
    merged = early_df.merge(labeled[["public_id", "final_code"]], on="public_id", how="inner")
    vc = merged["final_code"].value_counts()
    merged = merged[merged["final_code"].isin(vc[vc >= 30].index)].copy()

    feature_cols = [col for col in early_df.columns if col.startswith("e_")]
    X = merged[feature_cols].to_numpy()
    y = merged["final_code"].to_numpy()

    encoder = LabelEncoder().fit(y)
    y_enc = encoder.transform(y)
    skf = StratifiedKFold(n_splits=cfg.CV_FOLDS, shuffle=True, random_state=cfg.SEED)

    rows = []
    best_name = None
    best_score = -1.0
    best_pipe = None
    for model_name, clf in _get_models().items():
        pipe = Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler()), ("clf", clf)])
        pred = np.zeros_like(y_enc)
        for train_idx, test_idx in skf.split(X, y_enc):
            pipe.fit(X[train_idx], y[train_idx])
            pred[test_idx] = encoder.transform(pipe.predict(X[test_idx]))

        f1 = f1_score(y_enc, pred, average="weighted")
        acc = accuracy_score(y_enc, pred)
        prec = precision_score(y_enc, pred, average="weighted", zero_division=0)
        rec = recall_score(y_enc, pred, average="weighted", zero_division=0)
        rows.append({"Model": model_name, "F1_weighted": f1, "Accuracy": acc, "Precision": prec, "Recall": rec})
        if f1 > best_score:
            best_score = f1
            best_name = model_name
            best_pipe = pipe

    result = pd.DataFrame(rows)
    result.to_csv(cfg.TABLE_DIR / "prediction_full_evaluation_final_code.csv", index=False, encoding="utf-8-sig")

    if best_pipe is not None and best_name is not None:
        best_pipe.fit(X, y)
        final_pred = best_pipe.predict(X)
        with open(cfg.TABLE_DIR / "classification_report_final_code.txt", "w", encoding="utf-8") as f:
            f.write(f"Best model: {best_name}\n{'=' * 50}\n")
            f.write(classification_report(y, final_pred))
        cm = confusion_matrix(y, final_pred, labels=encoder.classes_)
        pd.DataFrame(cm, index=encoder.classes_, columns=encoder.classes_).to_csv(
            cfg.TABLE_DIR / "confusion_matrix_final_code.csv", encoding="utf-8-sig"
        )

        if HAS_SHAP and best_name in ("RF", "GBM", "LightGBM"):
            X_t = best_pipe[:-1].transform(X)
            fitted = best_pipe.named_steps["clf"]
            try:
                explainer = shap.TreeExplainer(fitted)
                shap_values = explainer.shap_values(X_t)
            except Exception:
                background = shap.kmeans(X_t, min(100, len(X_t)))
                explainer = shap.KernelExplainer(fitted.predict_proba, background)
                X_t = X_t[: min(500, len(X_t))]
                shap_values = explainer.shap_values(X_t)
            plt = cfg.setup_matplotlib()
            shap.summary_plot(shap_values, X_t, feature_names=feature_cols, plot_type="bar", show=False, max_display=12)
            plt.tight_layout()
            plt.savefig(cfg.FIGURE_DIR / "shap_early_prediction_final_code.png", dpi=150, bbox_inches="tight")
            plt.close("all")

    return result


def run_prediction(ts: pd.DataFrame, labeled: pd.DataFrame):
    print("[Step06] final_code 조기 예측")
    early_df = build_early_features(ts, cfg.EARLY_WEEKS)
    ablation = ablation_study(early_df, labeled)
    evaluation = full_evaluation(early_df, labeled)
    return {"early_features": early_df, "ablation": ablation, "evaluation": evaluation}
