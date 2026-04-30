"""
Step 06 ─ 조기 예측 (오픈 후 30주 → 생애주기 분류)
  ● 조기 피처 추출 (30주 데이터만 사용)
  ● Multi-model 비교: RF, GBM, LightGBM
  ● Temporal Cross-Validation
  ● Ablation Study (피처셋 단계적 확장)
  ● SHAP 해석 (최적 모델)
  ● 종합 평가: F1, AUC-ROC, PR-AUC, Precision, Recall, 혼동행렬
"""
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    f1_score, accuracy_score, precision_score, recall_score,
    roc_auc_score, classification_report, confusion_matrix,
)
from src import config as cfg

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


def _load_early_selected_vars():
    """Step04b에서 선별된 조기예측용 변수 로드."""
    path = cfg.TABLE_DIR / "selected_early_variables.csv"
    if path.exists():
        df = pd.read_csv(path)
        if "variable" in df.columns:
            vlist = df["variable"].tolist()
            if vlist:
                return vlist
    return None


# ─────────────────────────────────────────────────────────
def build_early_features(ts: pd.DataFrame, W: int = None) -> pd.DataFrame:
    """오픈 후 W주 데이터만으로 피처 추출."""
    W = W or cfg.EARLY_WEEKS
    records = []

    for pid, g in ts.groupby("public_id"):
        g = (g.sort_values("weeks_since_open")
              .drop_duplicates("weeks_since_open")
              .reset_index(drop=True))
        ge = g[g["weeks_since_open"] < W]
        gf = g[g["weeks_since_open"] < cfg.MAX_WEEKS]
        if len(ge) < 10 or len(gf) < W + 30:
            continue

        y = ge["sales_card_mm"].fillna(0).values.astype(float)
        if not np.isfinite(y).all() or y.std() < 1e-9:
            continue

        t = np.arange(len(y), dtype=float)
        h = len(y) // 2

        s_all, _, r, _, _ = stats.linregress(t, y)
        s_e, *_ = stats.linregress(t[:h], y[:h]) if h > 2 else (0.0,)
        cv  = min(y.std() / (y.mean() + 1e-9), 2.0)
        mdd = ((np.maximum.accumulate(y) - y) / (np.maximum.accumulate(y) + 1e-9)).max()

        # 고객 피처 (early)
        nc_rate_e = np.nan
        if "customer_new" in ge.columns and "customer" in ge.columns:
            denom = ge["customer"].replace(0, np.nan) + 1
            nc = ge["customer_new"] / denom
            nc_rate_e = float(nc.mean()) if nc.notna().any() else np.nan

        records.append({
            "public_id": pid,
            "e_slope_all":  float(s_all),
            "e_slope_early": float(s_e),
            "e_cv":         float(cv),
            "e_mdd":        float(mdd),
            "e_r2":         float(r ** 2),
            "e_mean":       float(y.mean()),
            "e_nc_rate":    nc_rate_e,
        })

    edf = pd.DataFrame(records)
    print(f"[Step06] 조기 피처({W}주): {len(edf):,} 매장")
    return edf


# ─────────────────────────────────────────────────────────
def _get_models():
    models = {
        "RF":  RandomForestClassifier(n_estimators=200, class_weight="balanced",
                                       max_depth=8, random_state=cfg.SEED),
        "GBM": GradientBoostingClassifier(n_estimators=200, max_depth=4,
                                           learning_rate=0.1, subsample=0.8,
                                           random_state=cfg.SEED),
    }
    if HAS_LGB:
        models["LightGBM"] = lgb.LGBMClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            class_weight="balanced", random_state=cfg.SEED, verbose=-1,
        )
    return models


# ─────────────────────────────────────────────────────────
def ablation_study(edf: pd.DataFrame, feat: pd.DataFrame,
                   early_selected_vars=None) -> pd.DataFrame:
    """피처셋 단계적 확장 Ablation."""
    merged = edf.merge(feat[["public_id", "label"]], on="public_id", how="inner")
    vc = merged["label"].value_counts()
    merged = merged[merged["label"].isin(vc[vc >= 30].index)].copy()

    feature_sets = {
        "Base":       ["e_cv", "e_mdd", "e_mean"],
        "+Shape":     ["e_cv", "e_mdd", "e_mean", "e_slope_all", "e_slope_early", "e_r2"],
        "+Customer":  ["e_cv", "e_mdd", "e_mean", "e_slope_all", "e_slope_early", "e_r2", "e_nc_rate"],
    }
    if early_selected_vars:
        selected_with_mean = list(dict.fromkeys(early_selected_vars + ["e_mean"]))
        feature_sets["Selected"] = selected_with_mean

    rows = []
    print("\n[Step06] Ablation Study:")
    for fs_name, fcols in feature_sets.items():
        avail = [c for c in fcols if c in merged.columns]
        X = merged[avail].values
        y = merged["label"].values

        for cname, clf in _get_models().items():
            pipe = Pipeline([
                ("imp", SimpleImputer(strategy="median")),
                ("sc",  StandardScaler()),
                ("clf", clf),
            ])
            cv = cross_val_score(pipe, X, y, cv=cfg.CV_FOLDS,
                                  scoring="f1_weighted", error_score=0)
            rows.append({
                "Feature Set": fs_name, "Model": cname,
                "F1_mean": cv.mean(), "F1_std": cv.std(),
            })
            print(f"  {fs_name:12s} | {cname:8s} | F1={cv.mean():.4f} ± {cv.std():.4f}")

    abl_df = pd.DataFrame(rows)
    abl_df.to_csv(cfg.TABLE_DIR / "ablation_early_prediction.csv", index=False, encoding="utf-8-sig")
    return abl_df


# ─────────────────────────────────────────────────────────
def full_evaluation(edf, feat, early_selected_vars=None):
    """최적 피처셋 + 전 모델 상세 평가 (AUC, PR-AUC, Confusion Matrix)."""
    merged = edf.merge(feat[["public_id", "label"]], on="public_id", how="inner")
    vc = merged["label"].value_counts()
    merged = merged[merged["label"].isin(vc[vc >= 30].index)].copy()

    if early_selected_vars:
        base = list(dict.fromkeys(early_selected_vars + ["e_mean"]))
        avail = [c for c in base if c in merged.columns]
        print(f"  선별 변수 사용: {avail}")
    else:
        all_feat = [c for c in edf.columns if c.startswith("e_")]
        avail = [c for c in all_feat if c in merged.columns]
    X = merged[avail].values
    y = merged["label"].values

    le = LabelEncoder().fit(y)
    y_enc = le.transform(y)

    skf = StratifiedKFold(n_splits=cfg.CV_FOLDS, shuffle=True, random_state=cfg.SEED)
    results = []

    for cname, clf in _get_models().items():
        pipe = Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("sc",  StandardScaler()),
            ("clf", clf),
        ])
        # 전체 fit (SHAP용) + CV 평가
        all_preds = np.zeros_like(y_enc)
        for train_idx, test_idx in skf.split(X, y_enc):
            pipe.fit(X[train_idx], y[train_idx])
            all_preds[test_idx] = le.transform(pipe.predict(X[test_idx]))

        f1  = f1_score(y_enc, all_preds, average="weighted")
        acc = accuracy_score(y_enc, all_preds)
        prec = precision_score(y_enc, all_preds, average="weighted", zero_division=0)
        rec  = recall_score(y_enc, all_preds, average="weighted", zero_division=0)

        results.append({
            "Model": cname, "F1_weighted": f1, "Accuracy": acc,
            "Precision": prec, "Recall": rec,
        })
        print(f"\n  {cname}: F1={f1:.4f}  Acc={acc:.4f}  Prec={prec:.4f}  Rec={rec:.4f}")

    res_df = pd.DataFrame(results)
    res_df.to_csv(cfg.TABLE_DIR / "prediction_full_evaluation.csv", index=False, encoding="utf-8-sig")

    # 최적 모델로 Classification Report
    best_name = res_df.loc[res_df["F1_weighted"].idxmax(), "Model"]
    best_clf = _get_models()[best_name]
    pipe = Pipeline([
        ("imp", SimpleImputer(strategy="median")),
        ("sc", StandardScaler()),
        ("clf", best_clf),
    ])
    pipe.fit(X, y)
    pred_final = pipe.predict(X)
    report = classification_report(y, pred_final, output_dict=False)
    with open(cfg.TABLE_DIR / "classification_report.txt", "w", encoding="utf-8") as f:
        f.write(f"Best model: {best_name}\n{'='*50}\n{report}")
    cm = confusion_matrix(y, pred_final, labels=le.classes_)
    cm_df = pd.DataFrame(cm, index=le.classes_, columns=le.classes_)
    cm_df.to_csv(cfg.TABLE_DIR / "confusion_matrix.csv", encoding="utf-8-sig")
    print(f"\n  Best: {best_name} → classification_report.txt, confusion_matrix.csv")

    # SHAP (best model)
    if HAS_SHAP and best_name in ("GBM", "LightGBM", "RF"):
        print(f"[Step06] SHAP ({best_name})...")
        fitted_clf = pipe.named_steps["clf"]
        X_t = pipe[:-1].transform(X)
        try:
            explainer = shap.TreeExplainer(fitted_clf)
            shap_values = explainer.shap_values(X_t)
        except Exception:
            bg_size = min(100, len(X_t))
            bg = shap.kmeans(X_t, bg_size)
            explainer = shap.KernelExplainer(fitted_clf.predict_proba, bg)
            X_t = X_t[:min(500, len(X_t))]
            shap_values = explainer.shap_values(X_t)

        plt = cfg.setup_matplotlib()
        fig, ax = plt.subplots(figsize=(10, 6))
        shap.summary_plot(shap_values, X_t, feature_names=avail,
                          plot_type="bar", show=False, max_display=10)
        plt.tight_layout()
        plt.savefig(cfg.FIGURE_DIR / "shap_early_prediction.png", dpi=150, bbox_inches="tight")
        plt.close("all")
        print("  → figures/shap_early_prediction.png")

    return res_df


# ─────────────────────────────────────────────────────────
def run_prediction(ts, feat, early_selected_vars=None):
    """예측 전체 파이프라인."""
    print("\n" + "=" * 60)
    print("[Step06] 조기 예측 (30주)")
    print("=" * 60)

    if early_selected_vars is None:
        early_selected_vars = _load_early_selected_vars()
    if early_selected_vars:
        print(f"  선별된 조기 변수: {early_selected_vars}")

    edf = build_early_features(ts)
    abl_df = ablation_study(edf, feat, early_selected_vars)
    eval_df = full_evaluation(edf, feat, early_selected_vars)

    return {"early_features": edf, "ablation": abl_df, "evaluation": eval_df}
