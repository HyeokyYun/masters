"""
FEATURE-CSV pipeline (track A) — success by cluster + ablation M0..M3 (LR + XGB).
Run from 260204: python scripts/run_04_storyline_ablation.py
Self-contained: no project src imports.
"""
from pathlib import Path
import yaml
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score
from xgboost import XGBClassifier
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent

DATA_CLEAN = ROOT / "outputs" / "data_features_clean.parquet"
LOG_PATH = ROOT / "outputs" / "logs" / "run_04_storyline_ablation.log"
TABLES_DIR = ROOT / "outputs" / "tables"
FIGURES_DIR = ROOT / "outputs" / "figures"


def load_config():
    with open(ROOT / "configs" / "base.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    def log(msg: str):
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    if not DATA_CLEAN.exists():
        log(f"ERROR: Run run_01 first. Not found: {DATA_CLEAN}")
        return

    cfg = load_config()
    data_cfg = cfg.get("data", {})
    cluster_col = data_cfg.get("cluster_col", "cluster")
    threshold = cfg.get("targets", {}).get("success_threshold", 1.0)
    categoricals = cfg.get("categoricals", [])
    pred_cfg = cfg.get("prediction", {})
    seed = pred_cfg.get("seed", 42)
    test_size = pred_cfg.get("test_size", 0.2)
    m0_cols = pred_cfg.get("m0_numeric_cols", [])
    x_numeric_cols = pred_cfg.get("x_numeric_cols", [])

    df = pd.read_parquet(DATA_CLEAN)
    if "growth_rate" not in df.columns:
        log("ERROR: 'growth_rate' not in data.")
        return

    # Binary success
    df["success"] = (df["growth_rate"] >= threshold).astype(int)

    # Success rate by cluster
    by_cluster = df.groupby(cluster_col, dropna=False).agg(
        n=("success", "count"),
        success_sum=("success", "sum"),
    ).reset_index()
    by_cluster["success_rate"] = by_cluster["success_sum"] / by_cluster["n"]
    by_cluster = by_cluster[[cluster_col, "n", "success_sum", "success_rate"]]
    by_cluster.to_csv(TABLES_DIR / "success_rate_by_cluster.csv", index=False)
    log(f"Saved {TABLES_DIR / 'success_rate_by_cluster.csv'}")

    fig, ax = plt.subplots()
    ax.bar(by_cluster[cluster_col].astype(str), by_cluster["success_rate"], color="steelblue", edgecolor="black")
    ax.axhline(y=threshold, color="gray", linestyle="--", label=f"threshold={threshold}")
    ax.set_ylabel("Success rate")
    ax.set_xlabel(cluster_col)
    ax.set_title("Success rate by cluster")
    ax.legend()
    fig.savefig(FIGURES_DIR / "success_rate_by_cluster.png", bbox_inches="tight")
    plt.close(fig)
    log(f"Saved {FIGURES_DIR / 'success_rate_by_cluster.png'}")

    # Ablation: build feature sets
    m0_cols = [c for c in m0_cols if c in df.columns]
    x_numeric_cols = [c for c in x_numeric_cols if c in df.columns]
    cat_in_df = [c for c in categoricals if c in df.columns]

    use = df.dropna(subset=["success"] + m0_cols + x_numeric_cols + cat_in_df + ([cluster_col] if cluster_col in df.columns else []))
    if len(use) < 20:
        log("ERROR: Too few rows for ablation after dropna.")
        return

    y = np.asarray(use["success"], dtype=int)

    def make_X(spec: str):
        """spec in M0, M1, M2, M3."""
        parts = [use[m0_cols].astype(float)]
        if spec in ("M1", "M3"):
            cl = use[[cluster_col]].copy()
            cl[cluster_col] = cl[cluster_col].fillna(-1).astype(str)
            parts.append(pd.get_dummies(cl, drop_first=True, dtype=float))
        if spec in ("M2", "M3"):
            parts.append(use[x_numeric_cols].astype(float))
            if cat_in_df:
                parts.append(pd.get_dummies(use[cat_in_df], drop_first=True, dtype=float))
        X = pd.concat(parts, axis=1)
        return np.asarray(X, dtype=float)

    X_m0 = make_X("M0")
    X_m1 = make_X("M1")
    X_m2 = make_X("M2")
    X_m3 = make_X("M3")

    specs = {"M0": X_m0, "M1": X_m1, "M2": X_m2, "M3": X_m3}

    results = []
    for model_name, model_factory in [
        ("LogisticRegression", lambda: LogisticRegression(max_iter=1000, random_state=seed)),
        ("XGBClassifier", lambda: XGBClassifier(random_state=seed, eval_metric="logloss")),
    ]:
        for spec, X in specs.items():
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=seed, stratify=y)
            clf = model_factory()
            clf.fit(X_train, y_train)
            pred = clf.predict(X_test)
            f1 = f1_score(y_test, pred, zero_division=0)
            results.append({"model": model_name, "spec": spec, "f1": f1})

    res_df = pd.DataFrame(results)
    res_df.to_csv(TABLES_DIR / "ablation_results.csv", index=False)
    log(f"Saved {TABLES_DIR / 'ablation_results.csv'}")

    # Figure: ablation F1 — grouped bars by spec (M0..M3), two bars per spec (LR, XGB)
    fig, ax = plt.subplots()
    x = np.arange(4)
    width = 0.35
    for i, model_name in enumerate(res_df["model"].unique()):
        sub = res_df[res_df["model"] == model_name].sort_values("spec")
        offset = -width / 2 + (i + 0.5) * width
        ax.bar(x + offset, sub["f1"].values, width, label=model_name, alpha=0.8)
    ax.set_ylabel("F1")
    ax.set_xlabel("Spec")
    ax.set_title("Ablation F1 by model and spec")
    ax.set_xticks(x)
    ax.set_xticklabels(["M0", "M1", "M2", "M3"])
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "ablation_f1.png", bbox_inches="tight")
    plt.close(fig)
    log(f"Saved {FIGURES_DIR / 'ablation_f1.png'}")

    # Best setting and improvement over M0 (same model)
    best_row = res_df.loc[res_df["f1"].idxmax()]
    best_f1 = best_row["f1"]
    m0_same_model = res_df[(res_df["model"] == best_row["model"]) & (res_df["spec"] == "M0")]["f1"].iloc[0]
    improvement = best_f1 - m0_same_model
    log(f"Best setting: {best_row['model']} / {best_row['spec']} (F1={best_f1:.4f})")
    log(f"Improvement over M0 ({best_row['model']}): {improvement:.4f}")


if __name__ == "__main__":
    main()
