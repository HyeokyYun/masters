"""Phase 5D Analysis 2 — EWS calibration + decile table.

목적: LightGBM Decline-class proba 를 의사결정-지원 (EWS) artifact로
정량 검증.

산출:
  1. reliability diagram (predicted vs observed bin avg) — 6 panels OOF
  2. Brier score per panel
  3. 10-decile table (predicted Decline proba decile × observed Decline rate)
  4. comparison: RF vs LGBM (calibration quality)
  5. (option) Platt scaling / isotonic regression after-calibration

Output:
  outputs/tables/ews_decile_table.csv
  outputs/tables/ews_brier.csv
  outputs/figures/ews_reliability_diagram.png
  outputs/figures/ews_decile_curve.png
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
from lightgbm import LGBMClassifier
from sklearn.calibration import calibration_curve
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import brier_score_loss
from sklearn.model_selection import StratifiedKFold

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.paths import PANELS, PHASE5_TABLE_DIR, PHASE5_FIGURE_DIR, SEED, up  # noqa: E402
from common.seq_loader import load_seq  # noqa: E402


DECLINE_CLS = 0  # Phase 0 OUTCOME_CLASSES = [Decline, Stable, Growth]


def _oof_proba(combo_id: str, ids: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """3-fold OOF P(Decline) for RF and LGBM. Returns (proba_rf, proba_lgbm)."""
    feats = pd.read_parquet(up.feature_path(combo_id))
    feats["public_id"] = feats["public_id"].astype(str)
    df = pd.DataFrame({"public_id": ids}).merge(feats, on="public_id", how="left")
    cols = [c for c in feats.columns if c != "public_id"]
    X = df[cols].fillna(0).reset_index(drop=True)
    y_s = pd.Series(y)
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED)

    p_rf = np.zeros(len(y), dtype=np.float64)
    p_lg = np.zeros(len(y), dtype=np.float64)
    for tr, te in skf.split(X, y_s):
        rf = RandomForestClassifier(n_estimators=120, max_depth=12, min_samples_leaf=20,
                                     n_jobs=-1, random_state=SEED, class_weight="balanced")
        rf.fit(X.iloc[tr], y_s.iloc[tr])
        lg = LGBMClassifier(n_estimators=400, learning_rate=0.05, num_leaves=63,
                             min_child_samples=20, n_jobs=-1, random_state=SEED,
                             class_weight="balanced", verbose=-1)
        lg.fit(X.iloc[tr], y_s.iloc[tr])
        cls_rf = list(rf.classes_)
        cls_lg = list(lg.classes_)
        idx_rf = cls_rf.index(DECLINE_CLS) if DECLINE_CLS in cls_rf else 0
        idx_lg = cls_lg.index(DECLINE_CLS) if DECLINE_CLS in cls_lg else 0
        p_rf[te] = rf.predict_proba(X.iloc[te])[:, idx_rf]
        p_lg[te] = lg.predict_proba(X.iloc[te])[:, idx_lg]
    return p_rf, p_lg


def _decile_table(y_decline: np.ndarray, proba: np.ndarray) -> pd.DataFrame:
    """10 deciles of proba → observed decline rate per decile."""
    df = pd.DataFrame({"y": y_decline.astype(int), "p": proba})
    df["decile"] = pd.qcut(df["p"], q=10, labels=False, duplicates="drop")
    out = (df.groupby("decile")
              .agg(n=("y", "size"),
                   pred_mean=("p", "mean"),
                   observed_decline=("y", "mean"))
              .reset_index())
    return out


def main():
    decile_rows = []
    brier_rows = []
    reliab_data: dict = {}  # combo_id → {(model, mean_pred, obs)}

    for combo_id, desc in PANELS:
        print(f"[ews] === {combo_id} ===", flush=True)
        ids, _, y = load_seq(combo_id)
        if ids is None:
            print(f"[ews] skip {combo_id}")
            continue
        y_decline = (y == DECLINE_CLS).astype(int)
        p_rf, p_lg = _oof_proba(combo_id, ids, y)

        for model, p in [("rf", p_rf), ("lgbm", p_lg)]:
            brier = brier_score_loss(y_decline, p)
            brier_rows.append({"combo_id": combo_id, "model": model, "brier": float(brier),
                                "n": int(len(y)),
                                "base_rate_decline": float(y_decline.mean())})
            d = _decile_table(y_decline, p)
            d["combo_id"] = combo_id
            d["model"] = model
            decile_rows.append(d)

            # reliability curve
            try:
                obs, mean_pred = calibration_curve(y_decline, p, n_bins=10, strategy="quantile")
                reliab_data[(combo_id, model)] = (mean_pred, obs)
            except Exception as e:
                print(f"[ews] {combo_id} {model} calibration_curve error: {e}")

        print(f"[ews] {combo_id} brier RF={brier_rows[-2]['brier']:.4f} LGBM={brier_rows[-1]['brier']:.4f}", flush=True)

    # save tables
    decile_df = pd.concat(decile_rows, ignore_index=True) if decile_rows else pd.DataFrame()
    brier_df = pd.DataFrame(brier_rows)
    decile_df.to_csv(PHASE5_TABLE_DIR / "ews_decile_table.csv",
                      index=False, encoding="utf-8-sig")
    brier_df.to_csv(PHASE5_TABLE_DIR / "ews_brier.csv",
                     index=False, encoding="utf-8-sig")
    print("[ews] saved tables")

    # summary
    if not brier_df.empty:
        summary = brier_df.groupby("model").agg(
            mean_brier=("brier", "mean"),
            std_brier=("brier", "std"),
            n_panels=("combo_id", "nunique")
        ).reset_index()
        print(summary.to_string(index=False))

    # reliability plot — 6 subplots × 2 models overlay
    if reliab_data:
        panels_unique = sorted(set(k[0] for k in reliab_data.keys()))
        n = len(panels_unique)
        cols = 3; rows = (n + cols - 1) // cols
        fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 3.2 * rows), squeeze=False)
        for i, combo in enumerate(panels_unique):
            ax = axes[i // cols, i % cols]
            ax.plot([0, 1], [0, 1], "k--", linewidth=0.8, label="perfect")
            for model, color in [("rf", "#666"), ("lgbm", "#1f77b4")]:
                key = (combo, model)
                if key in reliab_data:
                    mp, obs = reliab_data[key]
                    ax.plot(mp, obs, marker="o", linewidth=1.2, color=color, label=model.upper())
            ax.set_title(combo, fontsize=9)
            ax.set_xlabel("predicted P(Decline)"); ax.set_ylabel("observed Decline rate")
            ax.set_xlim(0, 1); ax.set_ylim(0, 1)
            ax.legend(fontsize=7)
        for j in range(n, rows * cols):
            axes[j // cols, j % cols].axis("off")
        fig.suptitle("EWS reliability diagram — RF vs LGBM (3-fold OOF, 6 panels)", fontsize=11)
        fig.tight_layout()
        out_p = PHASE5_FIGURE_DIR / "ews_reliability_diagram.png"
        fig.savefig(out_p, dpi=200, bbox_inches="tight")
        plt.close(fig)
        print(f"[ews] saved {out_p}")

    # decile curve
    if not decile_df.empty:
        fig, ax = plt.subplots(figsize=(8, 5))
        agg = (decile_df.groupby(["model", "decile"])
                          .agg(obs=("observed_decline", "mean"),
                                pred=("pred_mean", "mean"),
                                n=("n", "sum"))
                          .reset_index())
        for model, color in [("rf", "#666"), ("lgbm", "#1f77b4")]:
            m_sub = agg[agg["model"] == model]
            ax.plot(m_sub["decile"] + 1, m_sub["obs"], marker="o", color=color,
                     label=f"{model.upper()} observed", linewidth=1.6)
            ax.plot(m_sub["decile"] + 1, m_sub["pred"], linestyle="--", marker="x",
                     color=color, alpha=0.6, label=f"{model.upper()} predicted")
        # baseline decline rate
        if not brier_df.empty:
            base = float(brier_df["base_rate_decline"].mean())
            ax.axhline(base, color="red", linestyle=":", linewidth=1.0,
                        label=f"baseline rate ({base:.3f})")
        ax.set_xlabel("Risk decile (1=lowest, 10=highest)")
        ax.set_ylabel("P(Decline)")
        ax.set_title("EWS — observed vs predicted Decline rate by decile (avg of 6 panels)")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
        fig.tight_layout()
        out_p = PHASE5_FIGURE_DIR / "ews_decile_curve.png"
        fig.savefig(out_p, dpi=200, bbox_inches="tight")
        plt.close(fig)
        print(f"[ews] saved {out_p}")


if __name__ == "__main__":
    main()
