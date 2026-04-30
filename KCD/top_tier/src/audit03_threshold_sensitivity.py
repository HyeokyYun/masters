"""Audit 03 — Closure cutoff 및 outcome threshold의 sensitivity.

리뷰어 공격 예방: 현재 4주 (closure) / slope_all_std × factor (outcome) 를
다양한 값으로 바꿔도 결과가 robust한가?

Test:
  (a) Closure cutoff: 2w / 4w / 6w / 8w
  (b) Outcome slope threshold multiplier: 0.5 / 1.0 / 1.5 / 2.0 (× std)
  (c) 각 조합별 outcome_3 분포 및 Proposed A (logistic) 성능
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg  # noqa: E402


def define_outcome(slope_all, factor):
    std = np.std(slope_all)
    thr = std * factor
    outcome = np.where(slope_all > thr, "Growth",
               np.where(slope_all < -thr, "Decline", "Stable"))
    return outcome


def quick_cv(X, y, classes):
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=cfg.SEED)
    c2i = {c: i for i, c in enumerate(classes)}
    y_enc = np.array([c2i[v] for v in y])
    f1s, aucs = [], []
    for tr, te in skf.split(X, y):
        sc = StandardScaler()
        Xtr = sc.fit_transform(X[tr])
        Xte = sc.transform(X[te])
        m = LogisticRegression(max_iter=800, C=1.0).fit(Xtr, y_enc[tr])
        p = m.predict_proba(Xte)
        pred = np.array([classes[i] for i in p.argmax(1)])
        f1s.append(f1_score(y[te], pred, average="macro", zero_division=0))
        try:
            aucs.append(roc_auc_score(pd.get_dummies(y[te])[classes].values,
                                       p, multi_class="ovr"))
        except Exception:
            aucs.append(np.nan)
    return np.mean(f1s), np.mean(aucs)


def main():
    feats_labeled = pd.read_csv(cfg.FEATURES_PATH)
    feats_labeled["public_id"] = feats_labeled["public_id"].astype(str)
    unified = pd.read_parquet(cfg.TABLE_DIR / "unified_store_table.parquet")
    unified["public_id"] = unified["public_id"].astype(str)
    feat_mat = pd.read_parquet(cfg.TABLE_DIR / "prediction_feature_matrix.parquet")
    feat_mat["public_id"] = feat_mat["public_id"].astype(str)
    print(f"[audit03] data loaded: unified={len(unified):,}, feats_labeled={len(feats_labeled):,}, "
          f"feat_mat={len(feat_mat):,}")

    classes = cfg.OUTCOME_CLASSES

    print("\n=== (a) Closure cutoff sensitivity ===")
    results_a = []
    for cutoff in [2, 4, 6, 8]:
        is_closed_new = (unified["weeks_to_obs_end"] >= cutoff).astype(int)
        n_closed = int(is_closed_new.sum())
        n_total = len(unified)
        n_panel = int(unified["in_panel"].sum())
        panel_ids = unified.loc[unified["in_panel"] == 1, "public_id"]
        n_panel_closed = int(is_closed_new[unified["in_panel"] == 1].sum())
        non_panel_closure = (1 - n_panel_closed / n_panel) if n_panel > 0 else 0
        results_a.append({
            "cutoff_weeks": cutoff,
            "n_closed_total": n_closed,
            "closure_rate_total": n_closed / n_total,
            "panel_closure_rate": n_panel_closed / n_panel,
            "non_panel_closure_rate": (n_closed - n_panel_closed) / max(n_total - n_panel, 1),
        })
    df_a = pd.DataFrame(results_a).round(4)
    df_a.to_csv(cfg.TABLE_DIR / "audit03_closure_sensitivity.csv", index=False, encoding="utf-8-sig")
    print(df_a.to_string(index=False))

    print("\n=== (b) Outcome slope threshold sensitivity ===")
    results_b = []
    base_cols = [c for c in feat_mat.columns if c not in {"public_id", "outcome_3", "label"}]
    merged = feat_mat.merge(feats_labeled[["public_id", "slope_all_mm"]], on="public_id", how="inner")
    for factor in [0.25, 0.5, 0.75, 1.0]:
        outcome_new = define_outcome(merged["slope_all_mm"].values, factor)
        dist = pd.Series(outcome_new).value_counts(normalize=True)
        X = merged[base_cols].fillna(0.0).values.astype(float)
        f1, auc = quick_cv(X, outcome_new, classes)
        results_b.append({
            "slope_factor": factor,
            "n": len(merged),
            "Growth_pct": dist.get("Growth", 0),
            "Stable_pct": dist.get("Stable", 0),
            "Decline_pct": dist.get("Decline", 0),
            "A46_macro_f1": f1,
            "A46_auc": auc,
        })
    df_b = pd.DataFrame(results_b).round(4)
    df_b.to_csv(cfg.TABLE_DIR / "audit03_outcome_threshold_sensitivity.csv",
                index=False, encoding="utf-8-sig")
    print(df_b.to_string(index=False))

    print("\n=== 해석 ===")
    print("  Closure rate @ 2w vs 8w:",
          f"{df_a.iloc[0]['closure_rate_total']:.3f} vs {df_a.iloc[-1]['closure_rate_total']:.3f} "
          f"— 차이 {(df_a.iloc[0]['closure_rate_total'] - df_a.iloc[-1]['closure_rate_total']):+.3f}")
    print("  A46 F1 @ factor 0.25 vs 1.0:",
          f"{df_b.iloc[0]['A46_macro_f1']:.3f} vs {df_b.iloc[-1]['A46_macro_f1']:.3f}")
    print("  → threshold 변화가 결과 robust 함을 확인하기 위한 sensitivity table 확보")


if __name__ == "__main__":
    main()
