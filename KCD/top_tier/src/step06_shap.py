"""Step 06 — SHAP 설명 가능성 분석.

step03에서 훈련된 XGBoost 모델(또는 재훈련) 위에서 SHAP TreeExplainer로 feature 기여도 계산.
Growth vs Decline 구분에 기여하는 feature의 class별 SHAP 차이를 시각화.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg  # noqa: E402

plt.rcParams.update(cfg.FIG_STYLE)


def main():
    import shap
    import xgboost as xgb

    feat_path = cfg.TABLE_DIR / "prediction_feature_matrix.parquet"
    if not feat_path.exists():
        print("[06] prediction_feature_matrix.parquet not found — run step03 first.")
        return

    feat_df = pd.read_parquet(feat_path)
    classes = cfg.OUTCOME_CLASSES
    class_to_idx = {c: i for i, c in enumerate(classes)}

    X = feat_df.drop(columns=["public_id", "outcome_3", "label"]).fillna(0.0)
    y = np.array([class_to_idx[v] for v in feat_df["outcome_3"]])
    features = X.columns.tolist()

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=cfg.SEED)
    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_tr)
    X_te_s = scaler.transform(X_te)

    model = xgb.XGBClassifier(
        n_estimators=160, max_depth=4, learning_rate=0.08,
        subsample=0.9, colsample_bytree=0.9, min_child_weight=2,
        objective="multi:softprob", num_class=len(classes),
        eval_metric="mlogloss", tree_method="hist", n_jobs=4,
        random_state=cfg.SEED,
    )
    model.fit(X_tr_s, y_tr)
    print("[06] XGB trained")

    explainer = shap.TreeExplainer(model)
    sample_size = min(3000, X_te_s.shape[0])
    rng = np.random.RandomState(cfg.SEED)
    idx = rng.choice(X_te_s.shape[0], sample_size, replace=False)
    shap_values = explainer.shap_values(X_te_s[idx])

    if isinstance(shap_values, list):
        sv_by_class = shap_values
    else:
        arr = np.asarray(shap_values)
        if arr.ndim == 3:
            sv_by_class = [arr[:, :, i] for i in range(arr.shape[2])]
        else:
            sv_by_class = [arr]

    rows = []
    for ci, cname in enumerate(classes):
        if ci >= len(sv_by_class):
            continue
        sv = sv_by_class[ci]
        mean_abs = np.abs(sv).mean(axis=0)
        for f, v in zip(features, mean_abs):
            rows.append({"class": cname, "feature": f, "mean_abs_shap": float(v)})
    shap_df = pd.DataFrame(rows)
    shap_df.to_csv(cfg.TABLE_DIR / "shap_feature_importance_by_class.csv", index=False, encoding="utf-8-sig")

    overall = shap_df.groupby("feature")["mean_abs_shap"].sum().sort_values(ascending=False)
    overall.to_csv(cfg.TABLE_DIR / "shap_feature_importance_overall.csv", encoding="utf-8-sig")
    print(f"[06] Top 15 SHAP features:\n{overall.head(15)}")

    top15 = overall.head(15).index.tolist()
    fig, ax = plt.subplots(figsize=(10, 6))
    pivot = shap_df[shap_df["feature"].isin(top15)].pivot(index="feature", columns="class", values="mean_abs_shap")
    pivot = pivot.reindex(top15)
    pivot.plot(kind="barh", ax=ax, stacked=False)
    ax.set_xlabel("Mean |SHAP value|")
    ax.set_title("Top 15 Features — SHAP contribution by class")
    ax.invert_yaxis()
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(cfg.FIGURE_DIR / "shap_top15_by_class.png")
    plt.close(fig)
    print("[06] shap_top15_by_class.png saved")

    for ci, cname in enumerate(classes):
        if ci >= len(sv_by_class):
            continue
        fig = plt.figure(figsize=(8, 6))
        shap.summary_plot(sv_by_class[ci], X_te_s[idx], feature_names=features,
                          show=False, max_display=15, plot_size=(8, 6))
        plt.title(f"SHAP Summary — {cname} class")
        plt.savefig(cfg.FIGURE_DIR / f"shap_summary_{cname}.png", dpi=cfg.FIG_DPI, bbox_inches="tight")
        plt.close()


if __name__ == "__main__":
    main()
