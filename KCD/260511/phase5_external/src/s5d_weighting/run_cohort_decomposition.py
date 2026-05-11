"""Phase 5D Analysis 1 — Per-cohort LightGBM Δ decomposition.

목적: LGBM > RF (+0.008 macro_F1) 효과가 어느 sub-population에서 강한가 분해.

가설:
  H1. Q4_long (업력 ≥9년) tenure cohort 에서 Δ가 더 크다 (미팅 피드백 "업력이 상승에 유의미")
  H2. fragile cluster (cluster 3, Decline 36%) 에서 Δ가 더 크다

방법:
  1. 동일 6 panels, 3-fold StratifiedKFold (seed=42) — phase 5와 동일
  2. 각 fold에서 RF와 LGBM 모두 학습 → OOF predictions per store
  3. tenure_log를 quartile (Q1–Q4) 로 분할 (panel 내 분위수)
  4. analysis_cluster_outcome 와 동일 KMeans k=6 cluster 재현
  5. 각 cohort subset 별로 macro_F1 (RF, LGBM) 및 Δ = LGBM − RF 계산
  6. cohort × panel matrix + summary

Output:
  outputs/tables/lgbm_per_cohort_compare.csv
  outputs/tables/lgbm_per_cohort_paired.csv
  outputs/tables/lgbm_per_cohort_summary.csv
  outputs/figures/lgbm_per_cohort_heatmap.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.paths import PANELS, PHASE5_TABLE_DIR, PHASE5_FIGURE_DIR, SEED, up  # noqa: E402
from common.seq_loader import load_seq  # noqa: E402


def _load_features_meta(combo_id: str, ids: np.ndarray) -> tuple[pd.DataFrame, np.ndarray, list[str]]:
    """Returns features 56-D + tenure_log array (for cohort stratification)."""
    base = pd.read_parquet(up.feature_path(combo_id))
    base["public_id"] = base["public_id"].astype(str)
    meta_path = up.cfg.TABLE_DIR / "features_meta" / f"features_meta_{combo_id}.parquet"
    if meta_path.exists():
        meta = pd.read_parquet(meta_path)
        meta["public_id"] = meta["public_id"].astype(str)
        # drop non-numeric meta columns from feature set
        drop = [c for c in meta.columns if meta[c].dtype == object and c != "public_id"]
        meta_num = meta.drop(columns=drop)
    else:
        meta_num = pd.DataFrame({"public_id": []})

    df = pd.DataFrame({"public_id": ids}).merge(base, on="public_id", how="left")
    if not meta_num.empty:
        df = df.merge(meta_num, on="public_id", how="left")
    cols = [c for c in df.columns if c != "public_id"]
    X = df[cols].fillna(0.0).reset_index(drop=True)

    # tenure_log for cohort
    if meta_path.exists():
        meta_full = pd.read_parquet(meta_path)
        meta_full["public_id"] = meta_full["public_id"].astype(str)
        tlog = pd.DataFrame({"public_id": ids}).merge(meta_full[["public_id", "tenure_log"]],
                                                       on="public_id", how="left")
        tenure_log = tlog["tenure_log"].fillna(tlog["tenure_log"].median()).to_numpy(dtype=np.float32)
    else:
        tenure_log = np.zeros(len(ids), dtype=np.float32)
    return X, tenure_log, cols


def _make_clusters(X_seq: np.ndarray, k: int = 6) -> np.ndarray:
    """KMeans k=6 on sequence (same as analysis_cluster_outcome.py)."""
    N = X_seq.shape[0]
    flat = X_seq.reshape(N, -1)  # [N, T*C]
    scaled = StandardScaler().fit_transform(flat)
    km = KMeans(n_clusters=k, n_init=10, random_state=SEED, max_iter=300)
    return km.fit_predict(scaled)


def _tenure_quartile(tenure_log: np.ndarray) -> np.ndarray:
    """0..3 quartile assignment based on tenure_log (panel-internal)."""
    qs = np.quantile(tenure_log, [0.25, 0.5, 0.75])
    out = np.zeros(len(tenure_log), dtype=np.int64)
    out[tenure_log > qs[0]] = 1
    out[tenure_log > qs[1]] = 2
    out[tenure_log > qs[2]] = 3
    return out


def _run_panel(combo_id: str, description: str) -> dict:
    print(f"[cohort] === {combo_id} ===", flush=True)
    ids, X_seq, y = load_seq(combo_id)
    if ids is None:
        return {}
    X, tenure_log, cols = _load_features_meta(combo_id, ids)
    cluster = _make_clusters(X_seq, k=6)
    tenq = _tenure_quartile(tenure_log)

    # 3-fold OOF predictions for RF and LGBM
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED)
    oof_rf = np.full(len(y), -1, dtype=np.int64)
    oof_lgbm = np.full(len(y), -1, dtype=np.int64)
    rf_kwargs = dict(n_estimators=120, max_depth=12, min_samples_leaf=20,
                     n_jobs=-1, random_state=SEED, class_weight="balanced")
    lgbm_kwargs = dict(n_estimators=400, learning_rate=0.05, num_leaves=63,
                       min_child_samples=20, n_jobs=-1, random_state=SEED,
                       class_weight="balanced", verbose=-1)

    # use 43 base features (matching step06 RF) — exclude meta for like-for-like.
    base_cols_only = [c for c in cols if c in pd.read_parquet(up.feature_path(combo_id)).columns
                       and c != "public_id"]
    X_base = X[base_cols_only].fillna(0).reset_index(drop=True)
    y_s = pd.Series(y)

    for tr, te in skf.split(X_base, y_s):
        rf = RandomForestClassifier(**rf_kwargs).fit(X_base.iloc[tr], y_s.iloc[tr])
        oof_rf[te] = rf.predict(X_base.iloc[te])
        lgbm = LGBMClassifier(**lgbm_kwargs).fit(X_base.iloc[tr], y_s.iloc[tr])
        oof_lgbm[te] = lgbm.predict(X_base.iloc[te])

    # full macro_F1
    rf_full = f1_score(y, oof_rf, average="macro", zero_division=0)
    lgbm_full = f1_score(y, oof_lgbm, average="macro", zero_division=0)
    print(f"[cohort] {combo_id} full: RF={rf_full:.3f} LGBM={lgbm_full:.3f} Δ={lgbm_full-rf_full:+.4f}", flush=True)

    # per-cohort macro_F1
    rows = []
    for cohort_kind, cohort_arr, labels in [
        ("tenure_q", tenq, ["Q1_short", "Q2", "Q3", "Q4_long"]),
        ("cluster", cluster, [f"cluster_{i}" for i in range(6)]),
    ]:
        for idx, lab in enumerate(labels):
            mask = cohort_arr == idx
            n = int(mask.sum())
            if n < 200 or len(np.unique(y[mask])) < 2:
                rows.append({"combo_id": combo_id, "cohort_kind": cohort_kind,
                              "cohort": lab, "n": n,
                              "rf_f1": np.nan, "lgbm_f1": np.nan, "delta": np.nan,
                              "decline_rate": float((y[mask] == 0).mean()) if n > 0 else np.nan})
                continue
            rf_f = f1_score(y[mask], oof_rf[mask], average="macro", zero_division=0)
            lg_f = f1_score(y[mask], oof_lgbm[mask], average="macro", zero_division=0)
            rows.append({"combo_id": combo_id, "cohort_kind": cohort_kind,
                          "cohort": lab, "n": n,
                          "rf_f1": float(rf_f), "lgbm_f1": float(lg_f),
                          "delta": float(lg_f - rf_f),
                          "decline_rate": float((y[mask] == 0).mean())})
    rows.append({"combo_id": combo_id, "cohort_kind": "_overall",
                  "cohort": "all", "n": int(len(y)),
                  "rf_f1": float(rf_full), "lgbm_f1": float(lgbm_full),
                  "delta": float(lgbm_full - rf_full),
                  "decline_rate": float((y == 0).mean())})
    return {"rows": rows, "rf_full": rf_full, "lgbm_full": lgbm_full}


def main():
    all_rows = []
    for combo_id, desc in PANELS:
        out = _run_panel(combo_id, desc)
        if out and "rows" in out:
            all_rows.extend(out["rows"])
            # incremental save
            pd.DataFrame(all_rows).to_csv(
                PHASE5_TABLE_DIR / "lgbm_per_cohort_compare.csv",
                index=False, encoding="utf-8-sig")

    df = pd.DataFrame(all_rows)
    if df.empty:
        print("[cohort] no rows")
        return

    # summary: cohort_kind × cohort → mean Δ across panels
    summary = (df[df["cohort_kind"].isin(["tenure_q", "cluster"])]
               .groupby(["cohort_kind", "cohort"])
               .agg(n_panels=("combo_id", "nunique"),
                    mean_n=("n", "mean"),
                    mean_rf=("rf_f1", "mean"),
                    mean_lgbm=("lgbm_f1", "mean"),
                    mean_delta=("delta", "mean"),
                    std_delta=("delta", "std"),
                    mean_decline_rate=("decline_rate", "mean"))
               .reset_index())
    summary.to_csv(PHASE5_TABLE_DIR / "lgbm_per_cohort_summary.csv",
                    index=False, encoding="utf-8-sig")
    print("[cohort] summary saved")
    print(summary.to_string(index=False))

    # heatmap (panel × cohort)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        for kind in ["tenure_q", "cluster"]:
            sub = df[df["cohort_kind"] == kind]
            pv = sub.pivot_table(index="combo_id", columns="cohort", values="delta", aggfunc="mean")
            fig, ax = plt.subplots(figsize=(max(5, 0.7 * pv.shape[1] + 2), max(3, 0.4 * pv.shape[0] + 2)))
            vmax = max(0.05, np.nanmax(np.abs(pv.values)))
            im = ax.imshow(pv.values, aspect="auto", cmap="RdBu_r",
                           vmin=-vmax, vmax=vmax)
            ax.set_xticks(range(pv.shape[1])); ax.set_xticklabels(pv.columns, rotation=45, ha="right")
            ax.set_yticks(range(pv.shape[0])); ax.set_yticklabels(pv.index)
            for i in range(pv.shape[0]):
                for j in range(pv.shape[1]):
                    v = pv.values[i, j]
                    if not np.isnan(v):
                        ax.text(j, i, f"{v:+.3f}", ha="center", va="center",
                                fontsize=8, color="black" if abs(v) < vmax * 0.6 else "white")
            ax.set_title(f"LGBM−RF Δ macro_F1 by {kind}")
            plt.colorbar(im, ax=ax, label="Δ macro_F1")
            fig.tight_layout()
            out_p = PHASE5_FIGURE_DIR / f"lgbm_per_cohort_{kind}.png"
            fig.savefig(out_p, dpi=200, bbox_inches="tight")
            plt.close(fig)
            print(f"[cohort] saved {out_p}")
    except Exception as e:
        print(f"[cohort] figure error: {e}")


if __name__ == "__main__":
    main()
