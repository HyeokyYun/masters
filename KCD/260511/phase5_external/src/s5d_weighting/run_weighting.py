"""Phase 5D — feature weighting / cost-sensitive 실험.

변형:
  1. rf_tabular       : step06와 동일 RF baseline (paired delta 기준)
  2. rf_shap_weighted : SHAP per-class |mean| 평균을 feature 가중치로 입력에 곱함
  3. rf_decline_x2    : sample weight = 2 if Decline else 1 (cost-sensitive)
  4. rf_decline_x3    : sample weight = 3 if Decline else 1
  5. lgbm_tabular     : LightGBM baseline
  6. lgbm_shap_weighted: LGBM + SHAP feature weight
  7. lgbm_decline_x2  : LGBM + sample weight

CSV: outputs/tables/weighting_compare.csv, weighting_paired.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.paths import PANELS, PHASE5_TABLE_DIR, SEED, up  # noqa: E402
from common.seq_loader import load_seq  # noqa: E402
from common.cv_harness import paired_t_test  # noqa: E402

SHAP_PATH = Path("/home/hyeoky98/kcd/260430_claude/outputs/tables/shap_class_contrib.csv")


def _load_features(combo_id: str, ids: np.ndarray) -> tuple[pd.DataFrame, list[str]]:
    feats = pd.read_parquet(up.feature_path(combo_id))
    feats["public_id"] = feats["public_id"].astype(str)
    df = pd.DataFrame({"public_id": ids}).merge(feats, on="public_id", how="left")
    cols = [c for c in feats.columns if c != "public_id"]
    return df[cols].fillna(0).reset_index(drop=True), cols


def _shap_weights(combo_id: str, feature_cols: list[str]) -> np.ndarray:
    """SHAP per-class mean_abs_shap → 3-class 평균 → feature weight (정규화)."""
    if not SHAP_PATH.exists():
        return np.ones(len(feature_cols), dtype=np.float32)
    shap = pd.read_csv(SHAP_PATH)
    shap = shap[shap["combo_id"] == combo_id]
    if shap.empty:
        return np.ones(len(feature_cols), dtype=np.float32)
    agg = (shap.groupby("feature")["mean_abs_shap"].mean().reindex(feature_cols).fillna(0.0))
    w = agg.to_numpy(dtype=np.float32)
    if w.max() < 1e-12:
        return np.ones(len(feature_cols), dtype=np.float32)
    # normalize to mean=1 (so absolute scale stays comparable)
    w = w / w.mean()
    # clip extreme small (so unimportant features don't completely zero out)
    w = np.clip(w, 0.1, None)
    return w


def _rf_fit_predict(X, y, tr, te, sample_weight=None, **rf_kwargs):
    defaults = dict(n_estimators=120, max_depth=12, min_samples_leaf=20,
                    n_jobs=-1, random_state=SEED, class_weight="balanced")
    defaults.update(rf_kwargs)
    m = RandomForestClassifier(**defaults)
    if sample_weight is not None:
        m.fit(X.iloc[tr], y.iloc[tr], sample_weight=sample_weight[tr])
    else:
        m.fit(X.iloc[tr], y.iloc[tr])
    return m.predict(X.iloc[te])


def _lgbm_fit_predict(X, y, tr, te, sample_weight=None, **lgbm_kwargs):
    defaults = dict(n_estimators=400, learning_rate=0.05, num_leaves=63,
                    min_child_samples=20, n_jobs=-1, random_state=SEED,
                    class_weight="balanced", verbose=-1)
    defaults.update(lgbm_kwargs)
    m = LGBMClassifier(**defaults)
    if sample_weight is not None:
        m.fit(X.iloc[tr], y.iloc[tr], sample_weight=sample_weight[tr])
    else:
        m.fit(X.iloc[tr], y.iloc[tr])
    return m.predict(X.iloc[te])


def _run_variants(combo_id: str, X: pd.DataFrame, y: np.ndarray,
                   cols: list[str]) -> dict[str, list[float]]:
    """returns {model_name: [fold f1s]}"""
    results: dict[str, list[float]] = {}
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED)
    folds = list(skf.split(X, y))

    # sample weight variants
    sw_x2 = np.where(y == 0, 2.0, 1.0).astype(np.float32)  # Decline class = 0
    sw_x3 = np.where(y == 0, 3.0, 1.0).astype(np.float32)

    # SHAP feature weights
    w_shap = _shap_weights(combo_id, cols)
    X_shap = X * w_shap

    y_s = pd.Series(y)

    for name, fn in [
        ("rf_tabular",
         lambda tr, te: _rf_fit_predict(X, y_s, tr, te)),
        ("rf_shap_weighted",
         lambda tr, te: _rf_fit_predict(X_shap, y_s, tr, te)),
        ("rf_decline_x2",
         lambda tr, te: _rf_fit_predict(X, y_s, tr, te, sample_weight=sw_x2)),
        ("rf_decline_x3",
         lambda tr, te: _rf_fit_predict(X, y_s, tr, te, sample_weight=sw_x3)),
        ("lgbm_tabular",
         lambda tr, te: _lgbm_fit_predict(X, y_s, tr, te)),
        ("lgbm_shap_weighted",
         lambda tr, te: _lgbm_fit_predict(X_shap, y_s, tr, te)),
        ("lgbm_decline_x2",
         lambda tr, te: _lgbm_fit_predict(X, y_s, tr, te, sample_weight=sw_x2)),
    ]:
        f1s = []
        for tr, te in folds:
            pred = fn(tr, te)
            f1s.append(f1_score(y_s.iloc[te], pred, average="macro", zero_division=0))
        results[name] = f1s
    return results


def main():
    rows, paired = [], []
    for combo_id, desc in PANELS:
        print(f"[5D] === {combo_id} ===", flush=True)
        ids, X_seq, y = load_seq(combo_id)
        if ids is None:
            print(f"[5D] skip {combo_id}")
            continue
        X, cols = _load_features(combo_id, ids)

        res = _run_variants(combo_id, X, y, cols)
        rf_f1 = res["rf_tabular"]

        for name, f1s in res.items():
            rows.append({
                "combo_id": combo_id, "description": desc, "model": name,
                "macro_f1_mean": float(np.mean(f1s)),
                "macro_f1_std": float(np.std(f1s)),
                "n_stores": int(len(ids)), "T": int(X_seq.shape[1]), "C": int(X_seq.shape[2]),
            })
            if name != "rf_tabular":
                d, t, p = paired_t_test(rf_f1, f1s)
                paired.append({"combo_id": combo_id, "model": name,
                                "delta_mean": d, "t_stat": t, "p_value": p})
                print(f"[5D] {combo_id} {name:22s} F1={np.mean(f1s):.3f} Δ={d:+.4f} p={p:.3f}", flush=True)
            else:
                print(f"[5D] {combo_id} {name:22s} F1={np.mean(f1s):.3f} (baseline)", flush=True)

        pd.DataFrame(rows).to_csv(PHASE5_TABLE_DIR / "weighting_compare.csv",
                                   index=False, encoding="utf-8-sig")
        pd.DataFrame(paired).to_csv(PHASE5_TABLE_DIR / "weighting_paired.csv",
                                     index=False, encoding="utf-8-sig")

    cmp_df = pd.DataFrame(rows)
    print(f"[5D] saved compare ({len(cmp_df)} rows)")
    if not cmp_df.empty:
        agg = (cmp_df.groupby("model").agg(macro_f1=("macro_f1_mean", "mean"),
                                            n_panels=("combo_id", "nunique"))
               .reset_index().sort_values("macro_f1", ascending=False))
        print("[5D] avg macro_F1 across panels:")
        print(agg.to_string(index=False))


if __name__ == "__main__":
    main()
