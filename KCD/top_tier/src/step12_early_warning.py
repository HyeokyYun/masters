"""Step 12 — Early Warning System (EWS) 점수화.

DSS 저널 / 정책 적용을 위한 의사결정 지원 산출물:
  (a) Proposed 모델(D)의 클래스별 예측 확률을 0-100 risk score로 변환
  (b) operating-point 분석: threshold별 recall/precision trade-off
  (c) Calibration (Brier score, reliability diagram, Platt scaling 옵션)
  (d) 의사결정 비용행렬 — 잘못된 Decline 예측의 비용 vs 놓친 Growth 비용 시뮬
  (e) 업종/지역별 segment score 분포
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.cluster import KMeans
from sklearn.metrics import (average_precision_score, brier_score_loss,
                             precision_recall_curve, roc_curve)
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg  # noqa: E402

plt.rcParams.update(cfg.FIG_STYLE)

import xgboost as xgb

try:
    from tslearn.clustering import KShape
    from tslearn.preprocessing import TimeSeriesScalerMeanVariance
    HAS_TSLEARN = True
except ImportError:
    HAS_TSLEARN = False


def load_data():
    feat = pd.read_parquet(cfg.TABLE_DIR / "prediction_feature_matrix.parquet")
    feat["public_id"] = feat["public_id"].astype(str)
    meta = pd.read_csv(cfg.META_PATH)
    meta["public_id"] = meta["public_id"].astype(str)
    panel = pd.read_parquet(cfg.PANEL_PATH)
    panel["public_id"] = panel["public_id"].astype(str)

    cluster_path = cfg.TABLE_DIR / "hybrid_cluster_assignments.csv"
    cp_path = cfg.TABLE_DIR / "hybrid_change_point_features.csv"
    clu = pd.read_csv(cluster_path)
    clu["public_id"] = clu["public_id"].astype(str)
    cp = pd.read_csv(cp_path)
    cp["public_id"] = cp["public_id"].astype(str)

    df = feat.merge(clu, on="public_id", how="inner").merge(cp, on="public_id", how="inner")
    df = df.merge(meta[["public_id", "classification__kcd_v3__depth_2_name", "dong"]],
                  on="public_id", how="left")
    print(f"[12] merged feature matrix: {df.shape}")
    return df


def build_X_y(df: pd.DataFrame, classes):
    base_cols = [c for c in df.columns if c not in {
        "public_id", "outcome_3", "label",
        "km_cluster", "ks_cluster",
        "cp_position", "cp_delta_slope", "cp_pre_slope", "cp_post_slope",
        "cp_magnitude", "has_up_cp", "has_down_cp",
        "classification__kcd_v3__depth_2_name", "dong"}]

    km_onehot = pd.get_dummies(df["km_cluster"], prefix="km")
    ks_onehot = pd.get_dummies(df["ks_cluster"], prefix="ks") if "ks_cluster" in df.columns else None
    cp_cols = ["cp_position", "cp_delta_slope", "cp_pre_slope", "cp_post_slope",
               "cp_magnitude", "has_up_cp", "has_down_cp"]

    parts = [df[base_cols].fillna(0.0), km_onehot]
    if ks_onehot is not None:
        parts.append(ks_onehot)
    parts.append(df[cp_cols])
    X = pd.concat(parts, axis=1)
    y = df["outcome_3"].values
    return X, y, X.columns.tolist()


def cv_probabilities(df: pd.DataFrame, X: pd.DataFrame, y: np.ndarray, classes, n_folds=5):
    """Out-of-fold prediction probabilities."""
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=cfg.SEED)
    c2i = {c: i for i, c in enumerate(classes)}
    y_enc = np.array([c2i[v] for v in y])
    proba_all = np.zeros((len(y), len(classes)))

    for fold, (tr, te) in enumerate(skf.split(X, y)):
        scaler = StandardScaler()
        X_tr = scaler.fit_transform(X.iloc[tr])
        X_te = scaler.transform(X.iloc[te])
        model = xgb.XGBClassifier(
            n_estimators=160, max_depth=4, learning_rate=0.08,
            subsample=0.9, colsample_bytree=0.9, min_child_weight=2,
            objective="multi:softprob", num_class=len(classes),
            eval_metric="mlogloss", tree_method="hist", n_jobs=4,
            random_state=cfg.SEED,
        )
        model.fit(X_tr, y_enc[tr])
        proba_all[te] = model.predict_proba(X_te)
        print(f"  fold {fold} done")
    return proba_all


def risk_score_and_operating_points(df: pd.DataFrame, proba: np.ndarray, classes):
    """Decline 예측확률 → 0-100 risk score. Threshold별 성능 트레이드오프."""
    decline_idx = classes.index("Decline")
    growth_idx = classes.index("Growth")

    decline_p = proba[:, decline_idx]
    growth_p = proba[:, growth_idx]

    df["risk_score_decline"] = (decline_p * 100).round(1)
    df["opportunity_score_growth"] = (growth_p * 100).round(1)

    y_decline = (df["outcome_3"] == "Decline").astype(int).values
    y_growth = (df["outcome_3"] == "Growth").astype(int).values

    rows = []
    for thr in np.arange(0.05, 1.0, 0.05):
        pred_decline = (decline_p >= thr).astype(int)
        tp = int(((pred_decline == 1) & (y_decline == 1)).sum())
        fp = int(((pred_decline == 1) & (y_decline == 0)).sum())
        fn = int(((pred_decline == 0) & (y_decline == 1)).sum())
        tn = int(((pred_decline == 0) & (y_decline == 0)).sum())
        precision = tp / (tp + fp) if (tp + fp) else 0
        recall = tp / (tp + fn) if (tp + fn) else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
        rows.append({
            "threshold": round(thr, 2),
            "decline_precision": precision,
            "decline_recall": recall,
            "decline_f1": f1,
            "flagged_pct": (tp + fp) / len(y_decline),
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        })
    op = pd.DataFrame(rows)
    op.to_csv(cfg.TABLE_DIR / "ews_operating_points_decline.csv", index=False, encoding="utf-8-sig")
    print("[12] ews operating points (decline):")
    print(op.to_string(index=False))

    ap_decline = average_precision_score(y_decline, decline_p)
    ap_growth = average_precision_score(y_growth, growth_p)
    brier_decline = brier_score_loss(y_decline, decline_p)
    brier_growth = brier_score_loss(y_growth, growth_p)
    print(f"\n[12] Average Precision — Decline: {ap_decline:.3f}, Growth: {ap_growth:.3f}")
    print(f"[12] Brier — Decline: {brier_decline:.4f}, Growth: {brier_growth:.4f}")

    pd.DataFrame([{
        "ap_decline": ap_decline, "ap_growth": ap_growth,
        "brier_decline": brier_decline, "brier_growth": brier_growth,
        "baseline_decline_rate": y_decline.mean(),
        "baseline_growth_rate": y_growth.mean(),
    }]).to_csv(cfg.TABLE_DIR / "ews_calibration_metrics.csv", index=False, encoding="utf-8-sig")

    return op


def calibration_plot(df: pd.DataFrame, proba: np.ndarray, classes):
    decline_idx = classes.index("Decline")
    growth_idx = classes.index("Growth")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, idx, name in [(axes[0], decline_idx, "Decline"), (axes[1], growth_idx, "Growth")]:
        y_true = (df["outcome_3"] == name).astype(int).values
        fop, mpv = calibration_curve(y_true, proba[:, idx], n_bins=10)
        ax.plot([0, 1], [0, 1], "k--", alpha=0.5, label="Perfectly calibrated")
        ax.plot(mpv, fop, "o-", label=f"EWS — {name}")
        ax.set_xlabel("Mean predicted probability")
        ax.set_ylabel("Fraction of positives")
        ax.set_title(f"Calibration — {name}")
        ax.legend()
        ax.grid(True, alpha=0.3)
    fig.suptitle("Figure 10. EWS Probability Calibration")
    fig.tight_layout()
    fig.savefig(cfg.FIGURE_DIR / "fig10_calibration.png")
    plt.close(fig)


def pr_roc_plot(df: pd.DataFrame, proba: np.ndarray, classes):
    decline_idx = classes.index("Decline")
    growth_idx = classes.index("Growth")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, idx, name in [(axes[0], decline_idx, "Decline"), (axes[1], growth_idx, "Growth")]:
        y_true = (df["outcome_3"] == name).astype(int).values
        precision, recall, _ = precision_recall_curve(y_true, proba[:, idx])
        ap = average_precision_score(y_true, proba[:, idx])
        ax.plot(recall, precision, label=f"AP={ap:.3f}")
        ax.axhline(y_true.mean(), linestyle="--", color="gray",
                  label=f"Baseline={y_true.mean():.3f}")
        ax.set_xlabel("Recall")
        ax.set_ylabel("Precision")
        ax.set_title(f"PR — {name}")
        ax.legend()
        ax.grid(True, alpha=0.3)
    fig.suptitle("Figure 11. EWS Precision-Recall Curves")
    fig.tight_layout()
    fig.savefig(cfg.FIGURE_DIR / "fig11_pr_curves.png")
    plt.close(fig)


def cost_sensitive_decision(df: pd.DataFrame, proba: np.ndarray, classes):
    """가상의 정책 시나리오별 기대비용 비교.
    시나리오: 정부가 Decline 위험 점포에 조기 지원 프로그램(비용 C_support) 투입.
      - TP: 지원이 실제 decline 예방에 기여 (가정 기대편익 B_prevent)
      - FP: 정상 점포에 불필요 지원 (비용 C_support, 편익 0)
      - FN: 미지원 decline (비용 C_miss = 폐업 손실)
    단위는 상대치.
    """
    decline_idx = classes.index("Decline")
    decline_p = proba[:, decline_idx]
    y_decline = (df["outcome_3"] == "Decline").astype(int).values

    B_prevent = 10   # 단위 편익
    C_support = 2    # 지원 1점포 비용
    C_miss = 8       # 미지원 decline 손실

    rows = []
    for thr in np.arange(0.05, 1.0, 0.05):
        pred = (decline_p >= thr).astype(int)
        tp = int(((pred == 1) & (y_decline == 1)).sum())
        fp = int(((pred == 1) & (y_decline == 0)).sum())
        fn = int(((pred == 0) & (y_decline == 1)).sum())
        net = tp * (B_prevent - C_support) - fp * C_support - fn * C_miss
        rows.append({
            "threshold": round(thr, 2),
            "tp": tp, "fp": fp, "fn": fn,
            "net_utility": net,
        })
    df_cost = pd.DataFrame(rows)
    df_cost.to_csv(cfg.TABLE_DIR / "ews_cost_benefit.csv", index=False, encoding="utf-8-sig")

    best = df_cost.loc[df_cost["net_utility"].idxmax()]
    print(f"\n[12] Cost-sensitive optimal threshold: {best['threshold']:.2f} "
          f"(net_utility={best['net_utility']})")

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(df_cost["threshold"], df_cost["net_utility"], "o-")
    ax.axvline(best["threshold"], color="red", linestyle="--",
              label=f"optimal @ {best['threshold']:.2f}")
    ax.set_xlabel("Risk score threshold")
    ax.set_ylabel("Net utility")
    ax.set_title("Figure 12. EWS Cost-Benefit Analysis (policy intervention)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(cfg.FIGURE_DIR / "fig12_cost_benefit.png")
    plt.close(fig)

    return best


def segment_score_distribution(df: pd.DataFrame):
    """업종별 EWS score 분포."""
    sub = df.dropna(subset=["classification__kcd_v3__depth_2_name"])
    grp = sub.groupby("classification__kcd_v3__depth_2_name")["risk_score_decline"]
    summary = grp.agg(["count", "mean", "median", "std"]).reset_index()
    summary = summary[summary["count"] >= 500].sort_values("mean", ascending=False)
    summary.to_csv(cfg.TABLE_DIR / "ews_segment_score_distribution.csv", index=False, encoding="utf-8-sig")
    print("\n[12] Top-5 high-risk categories (by mean decline score):")
    print(summary.head(5).to_string(index=False))
    print("\n[12] Top-5 low-risk categories:")
    print(summary.tail(5).to_string(index=False))

    fig, ax = plt.subplots(figsize=(10, 5))
    top = summary.head(8)
    ax.bar(top["classification__kcd_v3__depth_2_name"], top["mean"], yerr=top["std"] / np.sqrt(top["count"]))
    ax.set_ylabel("Mean EWS risk score")
    ax.set_title("Figure 13. EWS Score Distribution by Category (top-8 high risk)")
    ax.tick_params(axis='x', rotation=30)
    fig.tight_layout()
    fig.savefig(cfg.FIGURE_DIR / "fig13_ews_by_category.png")
    plt.close(fig)


def main():
    df = load_data()
    classes = cfg.OUTCOME_CLASSES
    X, y, feat_names = build_X_y(df, classes)

    print("[12] 5-fold OOF prediction ...")
    proba = cv_probabilities(df, X, y, classes)

    np.save(cfg.TABLE_DIR / "ews_oof_proba.npy", proba)

    risk_score_and_operating_points(df, proba, classes)
    calibration_plot(df, proba, classes)
    pr_roc_plot(df, proba, classes)
    cost_sensitive_decision(df, proba, classes)
    segment_score_distribution(df)

    df[["public_id", "outcome_3", "risk_score_decline", "opportunity_score_growth"]].to_csv(
        cfg.TABLE_DIR / "ews_scores_per_store.csv", index=False, encoding="utf-8-sig"
    )
    print("\n[12] EWS pipeline complete")


if __name__ == "__main__":
    main()
