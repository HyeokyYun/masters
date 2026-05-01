"""Step 05 — Main model retraining (논문 1번 contribution).

Pick a small set of representative seasonal panels, then compare:
  A. Baseline: feature-window matrix only.
  B. + Cluster (KMeans on normalized feature-window sequence).
  C. + Change-point features (max-mean-gap split, pre/post slope).
  D. B + C.

Stratified 5-fold CV, RandomForest. Paired t-test on per-fold macro_F1
across A vs D for each panel.

Outputs:
  outputs/tables/main_model_compare.csv
  outputs/figures/main_model_delta.png
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg  # noqa: E402
import utils_panel as up  # noqa: E402

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

plt.rcParams.update(cfg.FIG_STYLE)


CLASSES = cfg.OUTCOME_CLASSES

PANELS_TO_RUN = [
    ("sy2021_sm01_w3m_off1", "Jan-Mar 2021 → Jan-Mar 2022"),
    ("sy2021_sm03_w3m_off1", "Mar-May 2021 → Mar-May 2022"),
    ("sy2021_sm05_w3m_off1", "May-Jul 2021 → May-Jul 2022"),
    ("sy2021_sm09_w3m_off1", "Sep-Nov 2021 → Sep-Nov 2022"),
    ("sy2022_sm01_w3m_off1", "Jan-Mar 2022 → Jan-Mar 2023"),
    ("sy2022_sm03_w3m_off1", "Mar-May 2022 → Mar-May 2023"),
    ("sy2022_sm05_w3m_off1", "May-Jul 2022 → May-Jul 2023"),
]


def _seq_matrix(panel_feat: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    pivot = panel_feat.pivot_table(
        index="public_id", columns="date_id", values="sales_card", aggfunc="mean"
    ).sort_index(axis=1)
    arr = pivot.to_numpy(dtype=float)
    means = np.nanmean(arr, axis=1, keepdims=True)
    means = np.where(np.isfinite(means) & (means > 1e-9), means, 1.0)
    norm = arr / means
    norm = np.where(np.isfinite(norm), norm, 0.0)
    ids = pivot.index.astype(str).to_numpy()
    return ids, norm


def _change_point_features(seq: np.ndarray, ids: np.ndarray) -> pd.DataFrame:
    """Max mean-gap split point + pre/post slopes. Vectorized per row."""
    n_rows, n_cols = seq.shape
    rows = []
    if n_cols < 5:
        for pid in ids:
            rows.append({
                "public_id": pid,
                "cp_position": -1, "cp_pre_slope": 0.0, "cp_post_slope": 0.0,
                "cp_delta_slope": 0.0, "cp_magnitude": 0.0,
                "has_up_cp": 0, "has_down_cp": 0,
            })
        return pd.DataFrame(rows)

    splits = np.arange(2, n_cols - 2)
    for i, pid in enumerate(ids):
        y = seq[i]
        scores = [abs(np.nanmean(y[s:]) - np.nanmean(y[:s])) for s in splits]
        if not scores:
            pos = -1; pre_s = post_s = 0.0; mag = 0.0
        else:
            pos = int(splits[int(np.nanargmax(scores))])
            pre_s, _ = up.linregress_slope(y[:pos])
            post_s, _ = up.linregress_slope(y[pos:])
            mag = float(abs(y[pos] - y[0]))
        delta = post_s - pre_s
        rows.append({
            "public_id": pid,
            "cp_position": pos / max(n_cols, 1),
            "cp_pre_slope": pre_s,
            "cp_post_slope": post_s,
            "cp_delta_slope": delta,
            "cp_magnitude": mag,
            "has_up_cp": int(delta > 0.01),
            "has_down_cp": int(delta < -0.01),
        })
    return pd.DataFrame(rows)


def _cluster(seq: np.ndarray, ids: np.ndarray, k: int = 6) -> pd.DataFrame:
    if len(ids) < k * 5:
        return pd.DataFrame({"public_id": ids, "km_cluster": np.zeros(len(ids), dtype=int)})
    scaled = StandardScaler().fit_transform(seq)
    km = KMeans(n_clusters=k, n_init=10, random_state=cfg.SEED, max_iter=300)
    labels = km.fit_predict(scaled)
    return pd.DataFrame({"public_id": ids, "km_cluster": labels})


def _eval(X: pd.DataFrame, y: pd.Series, label: str) -> tuple[list[float], dict]:
    skf = StratifiedKFold(n_splits=cfg.CV_FOLDS, shuffle=True, random_state=cfg.SEED)
    f1s = []
    metric_buf = {f"recall_{c}": [] for c in CLASSES}
    metric_buf.update({f"f1_{c}": [] for c in CLASSES})
    for fold, (tr, te) in enumerate(skf.split(X, y)):
        m = RandomForestClassifier(
            n_estimators=240, max_depth=14, min_samples_leaf=10,
            n_jobs=-1, random_state=cfg.SEED, class_weight="balanced",
        )
        m.fit(X.iloc[tr], y.iloc[tr])
        pred = m.predict(X.iloc[te])
        f1s.append(f1_score(y.iloc[te], pred, average="macro", zero_division=0))
        per = precision_recall_fscore_support(y.iloc[te], pred, labels=CLASSES, zero_division=0)
        for i, c in enumerate(CLASSES):
            metric_buf[f"recall_{c}"].append(per[1][i])
            metric_buf[f"f1_{c}"].append(per[2][i])
    summary = {"label": label, "macro_f1_mean": float(np.mean(f1s)),
               "macro_f1_std": float(np.std(f1s))}
    for k, v in metric_buf.items():
        summary[f"{k}_mean"] = float(np.mean(v))
    return f1s, summary


def _process_panel(combo_id: str, description: str) -> tuple[list[dict], dict]:
    p_path = up.panel_path(combo_id)
    f_path = up.feature_path(combo_id)
    l_path = up.label_path(combo_id)
    if not (p_path.exists() and f_path.exists() and l_path.exists()):
        return [], {}

    panel = pd.read_parquet(p_path)
    feats = pd.read_parquet(f_path)
    labels = pd.read_parquet(l_path)
    feats["public_id"] = feats["public_id"].astype(str)
    labels["public_id"] = labels["public_id"].astype(str)

    # Cluster + CP from feature-segment normalized sales
    feat_panel = panel[panel["segment"] == "feature"]
    ids, seq = _seq_matrix(feat_panel)
    cluster_df = _cluster(seq, ids)
    cp_df = _change_point_features(seq, ids)

    df = (
        feats.merge(labels[["public_id", "outcome_3"]], on="public_id", how="inner")
             .merge(cluster_df, on="public_id", how="left")
             .merge(cp_df, on="public_id", how="left")
    )
    df = df[df["outcome_3"].isin(CLASSES)]
    if len(df) < 500:
        return [], {}
    counts = df["outcome_3"].value_counts()
    if (counts < 10).any():
        return [], {}

    cluster_oh = pd.get_dummies(df["km_cluster"], prefix="km").astype(int)
    cp_cols = ["cp_position", "cp_pre_slope", "cp_post_slope",
               "cp_delta_slope", "cp_magnitude", "has_up_cp", "has_down_cp"]

    base_cols = [c for c in feats.columns if c != "public_id"]

    y = df["outcome_3"]

    feature_sets = {
        "A_baseline": df[base_cols],
        "B_base+cluster": pd.concat([df[base_cols].reset_index(drop=True),
                                      cluster_oh.reset_index(drop=True)], axis=1),
        "C_base+cp": df[base_cols + cp_cols],
        "D_base+cluster+cp": pd.concat([df[base_cols + cp_cols].reset_index(drop=True),
                                          cluster_oh.reset_index(drop=True)], axis=1),
    }

    rows = []
    fold_f1 = {}
    for name, X in feature_sets.items():
        X = X.fillna(0)
        f1s, summary = _eval(X, y.reset_index(drop=True), name)
        summary["combo_id"] = combo_id
        summary["description"] = description
        summary["n_stores"] = int(len(df))
        summary["n_features"] = int(X.shape[1])
        rows.append(summary)
        fold_f1[name] = f1s
        print(
            f"[05] {combo_id} {name:22s} n={len(df):,} feats={X.shape[1]:3d} "
            f"macroF1={summary['macro_f1_mean']:.3f}±{summary['macro_f1_std']:.3f} "
            f"dec_recall={summary['recall_Decline_mean']:.3f}"
        )

    paired = {}
    if "A_baseline" in fold_f1 and "D_base+cluster+cp" in fold_f1:
        a = np.array(fold_f1["A_baseline"])
        d = np.array(fold_f1["D_base+cluster+cp"])
        if len(a) == len(d) and np.std(d - a) > 0:
            t, p = stats.ttest_rel(d, a)
            paired = {
                "combo_id": combo_id, "description": description,
                "delta_mean": float((d - a).mean()),
                "t_stat": float(t), "p_value": float(p),
            }

    return rows, paired


def main() -> None:
    all_rows = []
    paired = []
    for combo_id, desc in PANELS_TO_RUN:
        rows, p = _process_panel(combo_id, desc)
        all_rows.extend(rows)
        if p:
            paired.append(p)

    df = pd.DataFrame(all_rows)
    df.to_csv(cfg.TABLE_DIR / "main_model_compare.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(paired).to_csv(cfg.TABLE_DIR / "main_model_paired_AvD.csv",
                                 index=False, encoding="utf-8-sig")
    print(f"[05] saved: {cfg.TABLE_DIR / 'main_model_compare.csv'}")

    if df.empty:
        print("[05] no panels processed; exit")
        return

    pivot = df.pivot_table(index="combo_id", columns="label", values="macro_f1_mean")
    pivot = pivot.reindex(columns=["A_baseline", "B_base+cluster",
                                     "C_base+cp", "D_base+cluster+cp"])
    fig, ax = plt.subplots(figsize=(10, 5))
    pivot.plot(kind="bar", ax=ax)
    ax.set_ylabel("macro_F1 (5-fold CV mean)")
    ax.set_title("Main model: A vs B vs C vs D across seasonal panels")
    ax.set_xticklabels(pivot.index, rotation=30, ha="right")
    fig.tight_layout()
    fig.savefig(cfg.FIGURE_DIR / "main_model_compare_bars.png")
    plt.close(fig)

    delta = (pivot["D_base+cluster+cp"] - pivot["A_baseline"]).rename("D - A")
    fig, ax = plt.subplots(figsize=(8, 4))
    delta.plot(kind="bar", color=delta.apply(lambda v: "tab:green" if v >= 0 else "tab:red"),
               ax=ax)
    ax.axhline(0, color="black", lw=0.6)
    ax.set_ylabel("ΔmacroF1 (D - A)")
    ax.set_title("Cluster + change-point uplift over baseline")
    ax.set_xticklabels(delta.index, rotation=30, ha="right")
    fig.tight_layout()
    fig.savefig(cfg.FIGURE_DIR / "main_model_delta.png")
    plt.close(fig)

    print(f"[05] figures: {cfg.FIGURE_DIR}")


if __name__ == "__main__":
    main()
