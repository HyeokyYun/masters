"""
Step 05 ─ 생애주기 결정 요인 분석
  ● Multinomial Logit (statsmodels)   — 전통 계량경제
  ● GradientBoosting + SHAP          — 비선형 + 해석가능 AI
  ● Propensity Score 기반 하위분석     — 배달앱 채택 인과효과 추정
"""
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import cross_val_score
from src import config as cfg

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False

try:
    import statsmodels.api as sm
    from statsmodels.discrete.discrete_model import MNLogit
    HAS_SM = True
except ImportError:
    HAS_SM = False


# ─── X/y 준비 ────────────────────────────────────────────
DEFAULT_FEATURE_COLS = [
    "slope_early_mm", "cv", "mdd", "nc_rate", "del_ratio_log",
    "before_noon", "weekend", "trend_slope", "seasonal_strength",
    "noise_ratio", "n_weeks",
]


def _load_selected_vars():
    """Step04b에서 선별된 변수 목록 로드."""
    path = cfg.TABLE_DIR / "selected_variables.csv"
    if path.exists():
        df = pd.read_csv(path)
        if "variable" in df.columns:
            return df["variable"].tolist()
    return None


def _prepare(feat: pd.DataFrame, meta: pd.DataFrame | None = None,
             selected_vars=None):
    df = feat.copy()
    if meta is not None:
        extra = meta[["public_id", "delivery_link"]].copy()
        extra["public_id"] = extra["public_id"].astype(str)
        extra["delivery_link"] = extra["delivery_link"].fillna(0)
        df = df.merge(extra, on="public_id", how="left")
    feature_cols = selected_vars if selected_vars else DEFAULT_FEATURE_COLS
    avail = [c for c in feature_cols + ["delivery_link"] if c in df.columns]
    vc = df["label"].value_counts()
    df = df[df["label"].isin(vc[vc >= 30].index)].copy()
    return df, avail


# ═════════════════════════════════════════════════════════
# 1. Multinomial Logit
# ═════════════════════════════════════════════════════════
def multinomial_logit(feat, meta=None, baseline="UU_X", selected_vars=None):
    if not HAS_SM:
        print("[Step05] statsmodels 미설치 — MNLogit 생략")
        return None

    df, avail = _prepare(feat, meta, selected_vars)
    dm = df.dropna(subset=avail).copy()

    # 카테고리 더미
    if "category" in dm.columns:
        cat_dummies = pd.get_dummies(dm["category"], prefix="cat", drop_first=True, dtype=float)
        X = pd.concat([dm[avail].reset_index(drop=True),
                        cat_dummies.reset_index(drop=True)], axis=1)
    else:
        X = dm[avail].copy()

    X = X.fillna(0)
    X = sm.add_constant(X)
    y = dm["label"].values

    # 기준 카테고리 설정
    labels_sorted = sorted(dm["label"].unique())
    if baseline in labels_sorted:
        labels_sorted.remove(baseline)
        labels_sorted = [baseline] + labels_sorted

    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()
    le.classes_ = np.array(labels_sorted)
    y_enc = le.transform(y)

    print(f"\n[Step05] Multinomial Logit (기준={baseline}, n={len(dm):,})")

    model = MNLogit(y_enc, X.astype(float))
    result = model.fit(method="lbfgs", maxiter=2000, disp=False)

    summary_path = cfg.TABLE_DIR / "mnlogit_summary.txt"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(str(result.summary2()))
    print(f"  Pseudo R²: {result.prsquared:.4f}")
    print(f"  저장 → {summary_path.name}")

    # 계수 + 오즈비
    params = result.params
    pvals  = result.pvalues
    coef_df = pd.DataFrame(params, index=X.columns)
    coef_df.columns = [f"vs_{labels_sorted[0]}_{labels_sorted[j+1]}" for j in range(params.shape[1])]
    coef_df.to_csv(cfg.TABLE_DIR / "mnlogit_coefficients.csv", encoding="utf-8-sig")

    return result


# ═════════════════════════════════════════════════════════
# 2. GradientBoosting + SHAP
# ═════════════════════════════════════════════════════════
def nonlinear_shap_analysis(feat, meta=None, selected_vars=None):
    df, avail = _prepare(feat, meta, selected_vars)
    dm = df.dropna(subset=avail).copy()

    X = dm[avail].values
    y = dm["label"].values

    pipe = Pipeline([
        ("imp", SimpleImputer(strategy="median")),
        ("sc",  StandardScaler()),
    ])
    X_t = pipe.fit_transform(X)

    gbm = GradientBoostingClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.1,
        subsample=0.8, random_state=cfg.SEED,
    )
    gbm.fit(X_t, y)

    # CV 성능
    cv = cross_val_score(
        Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("sc", StandardScaler()),
            ("clf", GradientBoostingClassifier(
                n_estimators=200, max_depth=4, learning_rate=0.1,
                subsample=0.8, random_state=cfg.SEED)),
        ]),
        X, y, cv=cfg.CV_FOLDS, scoring="f1_weighted",
    )
    print(f"\n[Step05] GBM CV F1-weighted: {cv.mean():.4f} ± {cv.std():.4f}")

    # Feature importance (built-in)
    imp_df = pd.DataFrame({
        "feature": avail,
        "importance": gbm.feature_importances_,
    }).sort_values("importance", ascending=False)
    imp_df.to_csv(cfg.TABLE_DIR / "gbm_feature_importance.csv", index=False)
    print(f"  Top features: {imp_df.head(5)['feature'].tolist()}")

    # SHAP
    if HAS_SHAP:
        try:
            print("[Step05] SHAP 분석 중 (TreeExplainer)...")
            explainer = shap.TreeExplainer(gbm)
            shap_values = explainer.shap_values(X_t)
        except Exception as e:
            n_classes = len(np.unique(y))
            print(f"  TreeExplainer 미지원 (classes={n_classes}): {e}")
            print("  → KernelExplainer로 전환합니다...")
            bg_size = min(100, len(X_t))
            bg = shap.kmeans(X_t, bg_size)
            explainer = shap.KernelExplainer(gbm.predict_proba, bg)
            sample_size = min(500, len(X_t))
            X_sample = X_t[:sample_size]
            shap_values = explainer.shap_values(X_sample)
            X_t = X_sample

        plt = cfg.setup_matplotlib()
        # Summary plot (bar)
        fig, ax = plt.subplots(figsize=(10, 6))
        shap.summary_plot(shap_values, X_t, feature_names=avail,
                          plot_type="bar", show=False, max_display=15)
        plt.tight_layout()
        plt.savefig(cfg.FIGURE_DIR / "shap_summary_bar.png", dpi=150, bbox_inches="tight")
        plt.close("all")

        # Beeswarm (첫 클래스)
        if isinstance(shap_values, list) and len(shap_values) > 0:
            fig, ax = plt.subplots(figsize=(10, 6))
            shap.summary_plot(shap_values[0], X_t, feature_names=avail,
                              show=False, max_display=15)
            plt.tight_layout()
            plt.savefig(cfg.FIGURE_DIR / "shap_beeswarm_class0.png", dpi=150, bbox_inches="tight")
            plt.close("all")

        print(f"  SHAP 그래프 → figures/shap_*.png")
    else:
        print("  shap 미설치 — SHAP 분석 생략")

    return gbm, imp_df


# ═════════════════════════════════════════════════════════
# 3. 배달앱 채택 효과 (Propensity Score Matching)
# ═════════════════════════════════════════════════════════
def propensity_score_analysis(feat, meta):
    """배달앱 채택(delivery_link==1)이 생애주기에 미치는 인과적 효과 추정."""
    if meta is None or "delivery_link" not in meta.columns:
        print("[Step05] delivery_link 없음 — PSM 생략")
        return None

    from sklearn.linear_model import LogisticRegression
    from sklearn.neighbors import NearestNeighbors

    extra = meta[["public_id", "delivery_link"]].copy()
    extra["public_id"] = extra["public_id"].astype(str)
    df = feat.merge(extra, on="public_id", how="inner")
    df = df.dropna(subset=["delivery_link"])
    df["treated"] = (df["delivery_link"] >= 1).astype(int)

    covariates = ["cv", "mdd", "nc_rate", "n_weeks", "slope_early_mm"]
    avail = [c for c in covariates if c in df.columns]
    dm = df.dropna(subset=avail).copy()
    X = dm[avail].fillna(0).values

    # Propensity score
    ps_model = LogisticRegression(max_iter=1000, random_state=cfg.SEED)
    ps_model.fit(X, dm["treated"].values)
    dm["propensity"] = ps_model.predict_proba(X)[:, 1]

    # 1:1 nearest-neighbor matching
    treated  = dm[dm["treated"] == 1].reset_index(drop=True)
    control  = dm[dm["treated"] == 0].reset_index(drop=True)
    nn = NearestNeighbors(n_neighbors=1, metric="euclidean")
    nn.fit(control[["propensity"]].values)
    dists, indices = nn.kneighbors(treated[["propensity"]].values)
    matched_control = control.iloc[indices.ravel()].reset_index(drop=True)

    # 결과 비교: label 분포
    for group_name, group_df in [("Treated", treated), ("Matched-Control", matched_control)]:
        dist = group_df["label"].value_counts(normalize=True).sort_index() * 100
        print(f"\n  [{group_name}] n={len(group_df):,}")
        for lbl, pct in dist.items():
            print(f"    {lbl}: {pct:.1f}%")

    # 요약 저장
    summary = pd.DataFrame({
        "label": cfg.LIFECYCLE_LABELS,
        "treated_pct": [treated["label"].value_counts(normalize=True).get(l, 0) * 100 for l in cfg.LIFECYCLE_LABELS],
        "control_pct": [matched_control["label"].value_counts(normalize=True).get(l, 0) * 100 for l in cfg.LIFECYCLE_LABELS],
    })
    summary["diff_pp"] = summary["treated_pct"] - summary["control_pct"]
    summary.to_csv(cfg.TABLE_DIR / "psm_delivery_effect.csv", index=False, encoding="utf-8-sig")
    print(f"\n[Step05] PSM 결과 → psm_delivery_effect.csv")
    return summary


# ─────────────────────────────────────────────────────────
def run_factor_analysis(feat, meta=None, selected_vars=None):
    """요인 분석 전체 파이프라인."""
    print("\n" + "=" * 60)
    print("[Step05] 요인 분석")
    print("=" * 60)

    if selected_vars is None:
        selected_vars = _load_selected_vars()
    if selected_vars:
        print(f"  데이터 기반 선별 변수 ({len(selected_vars)}개): {selected_vars}")
    else:
        print(f"  기본 변수 사용: {DEFAULT_FEATURE_COLS}")

    mnl_result = multinomial_logit(feat, meta, selected_vars=selected_vars)
    gbm, imp_df = nonlinear_shap_analysis(feat, meta, selected_vars=selected_vars)
    psm_result = propensity_score_analysis(feat, meta)

    return {"mnlogit": mnl_result, "gbm": gbm, "importance": imp_df, "psm": psm_result}
