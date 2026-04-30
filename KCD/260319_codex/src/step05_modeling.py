from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

from src import config as cfg

warnings.filterwarnings("ignore")

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


DEFAULT_FEATURE_COLS = [
    "slope_early_mm",
    "slope_late_mm",
    "slope_all_mm",
    "trend_slope",
    "overall_change_rate",
    "cv",
    "mdd",
    "nc_rate",
    "before_noon",
    "weekend",
    "seasonal_strength",
    "noise_ratio",
    "n_weeks",
]


def _safe_mnlogit_summary_text(result, labels_sorted: list[str], x_columns: list[str]) -> str:
    try:
        return str(result.summary2())
    except Exception as exc:
        lines = [
            "MNLogit summary2() unavailable",
            f"reason: {type(exc).__name__}: {exc}",
            f"converged: {getattr(result, 'mle_retvals', {}).get('converged', 'unknown')}",
            f"llf: {getattr(result, 'llf', 'unknown')}",
            f"prsquared: {getattr(result, 'prsquared', 'unknown')}",
            "",
            "Coefficient estimates only (standard errors / p-values unavailable):",
            "",
        ]
        params = pd.DataFrame(result.params, index=x_columns)
        params.columns = [f"vs_{labels_sorted[0]}_{labels_sorted[j + 1]}" for j in range(params.shape[1])]
        lines.append(params.to_string())
        lines.append("")
        lines.append(
            "Note: covariance matrix could not be computed. "
            "This usually indicates singularity, quasi-separation, or non-convergence."
        )
        return "\n".join(lines)


def _prepare(
    feat: pd.DataFrame,
    meta: pd.DataFrame | None = None,
    target: str = "final_code",
    add_cluster: bool = True,
):
    df = feat.copy()
    if meta is not None and "delivery_link" in meta.columns:
        extra = meta[["public_id", "delivery_link"]].copy()
        extra["public_id"] = extra["public_id"].astype(str)
        extra["delivery_link"] = extra["delivery_link"].fillna(0)
        df = df.merge(extra, on="public_id", how="left")

    cluster_path = cfg.TABLE_DIR / "cluster_labels.csv"
    if add_cluster and cluster_path.exists():
        cluster_df = pd.read_csv(cluster_path)
        cluster_df["public_id"] = cluster_df["public_id"].astype(str)
        df = df.merge(cluster_df, on="public_id", how="left")

    avail = [c for c in DEFAULT_FEATURE_COLS if c in df.columns]
    if "traj_cluster" in df.columns:
        avail.append("traj_cluster")
    if "delivery_link" in df.columns:
        avail.append("delivery_link")

    vc = df[target].value_counts()
    keep = vc[vc >= 30].index
    df = df[df[target].isin(keep)].copy()
    return df, avail


def multinomial_logit(feat: pd.DataFrame, meta: pd.DataFrame | None = None, target: str = "final_code"):
    if not HAS_SM:
        print("[Step05] statsmodels 미설치 - MNLogit 생략")
        return None

    df, avail = _prepare(feat, meta, target=target)
    dm = df.dropna(subset=avail).copy()
    if dm.empty:
        return None

    baseline = "UUX" if "UUX" in dm[target].unique() else dm[target].value_counts().idxmax()

    X = dm[avail].copy()
    if "category" in dm.columns:
        dummies = pd.get_dummies(dm["category"], prefix="cat", drop_first=True, dtype=float)
        X = pd.concat([X.reset_index(drop=True), dummies.reset_index(drop=True)], axis=1)
    X = sm.add_constant(X.fillna(0))

    labels_sorted = sorted(dm[target].unique())
    if baseline in labels_sorted:
        labels_sorted.remove(baseline)
        labels_sorted = [baseline] + labels_sorted
    encoder = LabelEncoder()
    encoder.classes_ = np.array(labels_sorted)
    y_enc = encoder.transform(dm[target].to_numpy())

    result = MNLogit(y_enc, X.astype(float)).fit(method="lbfgs", maxiter=2000, disp=False)
    with open(cfg.TABLE_DIR / "mnlogit_summary.txt", "w", encoding="utf-8") as f:
        f.write(_safe_mnlogit_summary_text(result, labels_sorted, list(X.columns)))

    coef_df = pd.DataFrame(result.params, index=X.columns)
    coef_df.columns = [f"vs_{labels_sorted[0]}_{labels_sorted[j + 1]}" for j in range(result.params.shape[1])]
    coef_df.to_csv(cfg.TABLE_DIR / "mnlogit_coefficients.csv", encoding="utf-8-sig")
    print(f"[Step05] MNLogit 저장 → mnlogit_summary.txt (baseline={baseline})")
    return result


def nonlinear_shap_analysis(feat: pd.DataFrame, meta: pd.DataFrame | None = None, target: str = "final_code"):
    df, avail = _prepare(feat, meta, target=target)
    dm = df.dropna(subset=[target]).copy()
    X = dm[avail].to_numpy()
    y = dm[target].to_numpy()

    prep = Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())])
    X_t = prep.fit_transform(X)
    model = GradientBoostingClassifier(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=4,
        subsample=0.8,
        random_state=cfg.SEED,
    )
    model.fit(X_t, y)

    cv = cross_val_score(
        Pipeline(
            [
                ("imp", SimpleImputer(strategy="median")),
                ("sc", StandardScaler()),
                (
                    "clf",
                    GradientBoostingClassifier(
                        n_estimators=200,
                        learning_rate=0.1,
                        max_depth=4,
                        subsample=0.8,
                        random_state=cfg.SEED,
                    ),
                ),
            ]
        ),
        X,
        y,
        cv=cfg.CV_FOLDS,
        scoring="f1_weighted",
    )
    print(f"[Step05] GBM CV F1-weighted: {cv.mean():.4f} ± {cv.std():.4f}")

    importance = pd.DataFrame({"feature": avail, "importance": model.feature_importances_}).sort_values(
        "importance", ascending=False
    )
    importance.to_csv(cfg.TABLE_DIR / "gbm_feature_importance.csv", index=False, encoding="utf-8-sig")

    if HAS_SHAP:
        try:
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_t)
        except Exception:
            background = shap.kmeans(X_t, min(100, len(X_t)))
            explainer = shap.KernelExplainer(model.predict_proba, background)
            X_t = X_t[: min(500, len(X_t))]
            shap_values = explainer.shap_values(X_t)

        plt = cfg.setup_matplotlib()
        shap.summary_plot(shap_values, X_t, feature_names=avail, plot_type="bar", show=False, max_display=15)
        plt.tight_layout()
        plt.savefig(cfg.FIGURE_DIR / "shap_summary_bar.png", dpi=150, bbox_inches="tight")
        plt.close("all")
    else:
        print("[Step05] shap 미설치 - SHAP 생략")

    return {"model": model, "importance": importance}


def propensity_score_analysis(feat: pd.DataFrame, meta: pd.DataFrame | None):
    if meta is None or "delivery_link" not in meta.columns:
        print("[Step05] delivery_link 없음 - PSM 생략")
        return None

    from sklearn.linear_model import LogisticRegression
    from sklearn.neighbors import NearestNeighbors

    extra = meta[["public_id", "delivery_link"]].copy()
    extra["public_id"] = extra["public_id"].astype(str)
    df = feat.merge(extra, on="public_id", how="inner")
    df = df.dropna(subset=["delivery_link"]).copy()
    df["treated"] = (df["delivery_link"] >= 1).astype(int)

    covariates = [c for c in ["cv", "mdd", "nc_rate", "n_weeks", "slope_early_mm"] if c in df.columns]
    dm = df.dropna(subset=covariates).copy()
    X = dm[covariates].fillna(0).to_numpy()

    ps_model = LogisticRegression(max_iter=1000, random_state=cfg.SEED)
    ps_model.fit(X, dm["treated"].to_numpy())
    dm["propensity"] = ps_model.predict_proba(X)[:, 1]

    treated = dm[dm["treated"] == 1].reset_index(drop=True)
    control = dm[dm["treated"] == 0].reset_index(drop=True)
    if treated.empty or control.empty:
        return None

    nn = NearestNeighbors(n_neighbors=1, metric="euclidean")
    nn.fit(control[["propensity"]].to_numpy())
    _, indices = nn.kneighbors(treated[["propensity"]].to_numpy())
    matched_control = control.iloc[indices.ravel()].reset_index(drop=True)

    summary = pd.DataFrame(
        {
            "Pattern_label": ["X", "Y", "Z"],
            "treated_pct": [
                treated["Pattern_label"].value_counts(normalize=True).get(label, 0) * 100 for label in ["X", "Y", "Z"]
            ],
            "control_pct": [
                matched_control["Pattern_label"].value_counts(normalize=True).get(label, 0) * 100
                for label in ["X", "Y", "Z"]
            ],
        }
    )
    summary["diff_pp"] = summary["treated_pct"] - summary["control_pct"]
    summary.to_csv(cfg.TABLE_DIR / "psm_pattern_effect.csv", index=False, encoding="utf-8-sig")
    return summary


def run_factor_analysis(feat: pd.DataFrame, meta: pd.DataFrame | None = None):
    print("[Step05] final_code 요인 분석")
    mnl = multinomial_logit(feat, meta, target="final_code")
    shap_bundle = nonlinear_shap_analysis(feat, meta, target="final_code")
    psm = propensity_score_analysis(feat, meta)
    return {"mnlogit": mnl, "gbm": shap_bundle, "psm": psm}
