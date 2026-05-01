"""Step 04 — Seasonal baseline evaluation.

For each combo (panel + label + features), train RandomForest and (if available)
LightGBM with stratified 5-fold CV. Report macro-F1, per-class precision/recall.

Outputs:
  outputs/tables/seasonal_results_long.csv  (per fold)
  outputs/tables/seasonal_results_summary.csv  (mean/std per combo×model)
  outputs/figures/heatmap_decline_recall_<model>.png  (start_month × window_months)
  outputs/figures/heatmap_macro_f1_<model>.png
  outputs/figures/yearly_compare_2021_vs_2022.png
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg  # noqa: E402
import utils_panel as up  # noqa: E402

try:
    import lightgbm as lgb
    HAS_LGB = True
except Exception:
    HAS_LGB = False

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

plt.rcParams.update(cfg.FIG_STYLE)


CLASSES = cfg.OUTCOME_CLASSES


def _load_combo(spec: up.WindowSpec) -> tuple[pd.DataFrame, pd.Series] | None:
    f_path = up.feature_path(spec.combo_id)
    l_path = up.label_path(spec.combo_id)
    if not f_path.exists() or not l_path.exists():
        return None
    feats = pd.read_parquet(f_path)
    labels = pd.read_parquet(l_path)
    feats["public_id"] = feats["public_id"].astype(str)
    labels["public_id"] = labels["public_id"].astype(str)
    df = feats.merge(labels[["public_id", "outcome_3"]], on="public_id", how="inner")
    df = df[df["outcome_3"].isin(CLASSES)]
    if len(df) < 200:
        return None
    counts = df["outcome_3"].value_counts()
    if (counts < 5).any():
        return None
    y = df["outcome_3"]
    X = df.drop(columns=["public_id", "outcome_3"])
    return X, y


def _eval_one(X: pd.DataFrame, y: pd.Series, model_name: str) -> list[dict]:
    skf = StratifiedKFold(n_splits=cfg.CV_FOLDS, shuffle=True, random_state=cfg.SEED)
    rows = []
    for fold, (tr, te) in enumerate(skf.split(X, y)):
        if model_name == "rf":
            model = RandomForestClassifier(
                n_estimators=150, max_depth=12, min_samples_leaf=15,
                n_jobs=-1, random_state=cfg.SEED, class_weight="balanced",
            )
        elif model_name == "lgb":
            if not HAS_LGB:
                continue
            model = lgb.LGBMClassifier(
                n_estimators=200, learning_rate=0.05, num_leaves=63,
                min_child_samples=30, subsample=0.9, colsample_bytree=0.9,
                random_state=cfg.SEED, n_jobs=-1, verbosity=-1,
                class_weight="balanced",
            )
        else:
            continue
        model.fit(X.iloc[tr], y.iloc[tr])
        pred = model.predict(X.iloc[te])
        per = precision_recall_fscore_support(
            y.iloc[te], pred, labels=CLASSES, zero_division=0
        )
        rows.append({
            "model": model_name,
            "fold": fold,
            "macro_f1": f1_score(y.iloc[te], pred, average="macro", zero_division=0),
            **{f"precision_{c}": per[0][i] for i, c in enumerate(CLASSES)},
            **{f"recall_{c}": per[1][i] for i, c in enumerate(CLASSES)},
            **{f"f1_{c}": per[2][i] for i, c in enumerate(CLASSES)},
        })
    return rows


def _heatmap(df: pd.DataFrame, value: str, model: str, target_year_offset: int, out_path: Path) -> None:
    sub = df[(df["model"] == model) & (df["target_offset"] == target_year_offset)]
    if sub.empty:
        return
    pivot_2021 = sub[sub["start_year"] == 2021].pivot_table(
        index="start_month", columns="window_months", values=value, aggfunc="mean"
    )
    pivot_2022 = sub[sub["start_year"] == 2022].pivot_table(
        index="start_month", columns="window_months", values=value, aggfunc="mean"
    )
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    for ax, pivot, title in zip(axes, [pivot_2021, pivot_2022], ["start_year=2021", "start_year=2022"]):
        if pivot.empty:
            ax.set_title(f"{title} (no data)")
            ax.axis("off")
            continue
        im = ax.imshow(pivot.to_numpy(), aspect="auto", cmap="viridis")
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels([f"{c}m" for c in pivot.columns])
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels([f"{m:02d}" for m in pivot.index])
        ax.set_xlabel("window_months")
        ax.set_ylabel("start_month")
        ax.set_title(f"{title} | offset={target_year_offset}")
        for i, m in enumerate(pivot.index):
            for j, w in enumerate(pivot.columns):
                v = pivot.loc[m, w]
                if pd.notna(v):
                    ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                            color="white" if v < 0.5 else "black", fontsize=8)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.suptitle(f"{value} | model={model} | target_offset={target_year_offset}")
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def main() -> None:
    panel_summary = pd.read_csv(cfg.TABLE_DIR / "panel_summary.csv")
    panel_summary = panel_summary[panel_summary["n_stores"] > 0]
    combos = up.enumerate_combos()
    spec_lookup = {s.combo_id: s for s in combos}

    long_rows = []
    for i, row in enumerate(panel_summary.itertuples(index=False)):
        spec = spec_lookup.get(row.combo_id)
        if spec is None:
            continue
        loaded = _load_combo(spec)
        if loaded is None:
            print(f"[04] {i+1:3d} {spec.combo_id} skip (no data)")
            continue
        X, y = loaded
        for model_name in ["rf"] + (["lgb"] if HAS_LGB else []):
            fold_rows = _eval_one(X, y, model_name)
            for r in fold_rows:
                r.update({
                    "combo_id": spec.combo_id,
                    "start_year": spec.start_year,
                    "start_month": spec.start_month,
                    "window_months": spec.window_months,
                    "target_offset": spec.target_offset,
                    "n_stores": len(X),
                })
                long_rows.append(r)
            if fold_rows:
                avg_f1 = np.mean([r["macro_f1"] for r in fold_rows])
                avg_dec = np.mean([r["recall_Decline"] for r in fold_rows])
                print(
                    f"[04] {i+1:3d} {spec.combo_id} {model_name} "
                    f"n={len(X):,} macroF1={avg_f1:.3f} dec_recall={avg_dec:.3f}"
                )

    long = pd.DataFrame(long_rows)
    long.to_csv(cfg.TABLE_DIR / "seasonal_results_long.csv", index=False, encoding="utf-8-sig")

    group_cols = ["combo_id", "start_year", "start_month", "window_months",
                  "target_offset", "model"]
    metrics = ["macro_f1"] + [f"recall_{c}" for c in CLASSES] + [f"f1_{c}" for c in CLASSES] + [f"precision_{c}" for c in CLASSES]
    agg_dict = {m: ["mean", "std"] for m in metrics}
    agg_dict["n_stores"] = ["first"]
    summary = long.groupby(group_cols).agg(agg_dict)
    summary.columns = [f"{m}_{stat}" if stat != "first" else m for (m, stat) in summary.columns]
    summary = summary.reset_index()
    summary.to_csv(cfg.TABLE_DIR / "seasonal_results_summary.csv", index=False, encoding="utf-8-sig")

    summary_flat = (
        long.groupby(group_cols, as_index=False)
        .agg(macro_f1=("macro_f1", "mean"),
             recall_Decline=("recall_Decline", "mean"),
             recall_Growth=("recall_Growth", "mean"),
             recall_Stable=("recall_Stable", "mean"),
             f1_Decline=("f1_Decline", "mean"),
             n_stores=("n_stores", "first"))
    )

    for model in summary_flat["model"].unique():
        for off in summary_flat["target_offset"].unique():
            _heatmap(summary_flat, "recall_Decline", model, off,
                     cfg.FIGURE_DIR / f"heatmap_decline_recall_{model}_off{off}.png")
            _heatmap(summary_flat, "macro_f1", model, off,
                     cfg.FIGURE_DIR / f"heatmap_macro_f1_{model}_off{off}.png")
            _heatmap(summary_flat, "f1_Decline", model, off,
                     cfg.FIGURE_DIR / f"heatmap_f1_decline_{model}_off{off}.png")

    fig, ax = plt.subplots(figsize=(10, 5))
    for model in summary_flat["model"].unique():
        sub = summary_flat[summary_flat["model"] == model]
        for sy, marker in [(2021, "o"), (2022, "s")]:
            pp = sub[(sub["start_year"] == sy) & (sub["target_offset"] == 1) & (sub["window_months"] == 3)]
            if pp.empty:
                continue
            pp = pp.sort_values("start_month")
            ax.plot(pp["start_month"], pp["macro_f1"], marker=marker,
                    label=f"{model} sy={sy}")
    ax.set_xlabel("start_month")
    ax.set_ylabel("macro_F1 (3-month feature window, target_offset=1)")
    ax.set_xticks(range(1, 13))
    ax.legend()
    ax.set_title("Seasonal macro-F1 across calendar start months")
    fig.tight_layout()
    fig.savefig(cfg.FIGURE_DIR / "yearly_compare_2021_vs_2022.png")
    plt.close(fig)

    print(f"[04] saved long  : {cfg.TABLE_DIR / 'seasonal_results_long.csv'}")
    print(f"[04] saved summary: {cfg.TABLE_DIR / 'seasonal_results_summary.csv'}")
    print(f"[04] figures: {cfg.FIGURE_DIR}")


if __name__ == "__main__":
    main()
