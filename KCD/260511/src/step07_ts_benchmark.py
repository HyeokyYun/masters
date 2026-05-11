"""Step 07 — Time-series regression benchmark for G/S/D prediction (Phase 1.2 / B3).

Predicts the *next* (target-window) sales slope from the feature-window
weekly sequence using several time-series models, then bucketizes the
predictions with the same per-panel sigma threshold the labels use, so we
can compare classification macro_F1 directly to the tabular baseline.

Models:
  - naive_last_slope : the last 4-week slope of the feature window itself
                       (no next-window prediction, but a fair "no model"
                       baseline that uses the same info content)
  - linear_extrap    : linear regression on the entire feature window,
                       extrapolated for target-window length
  - mlp_seq          : MLP on flattened weekly sales_card sequence
  - lstm_reg         : 1-layer LSTM regressor → predicts target-window
                       average normalized sales, then we compute slope from
                       (predicted_target_avg - feature_last_avg)
Why bucketize: the labeling protocol uses ±0.5σ on slope_target_norm, so
classification macro_F1 is the right yardstick.

Outputs:
  outputs/tables/ts_benchmark_compare.csv
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.linear_model import LinearRegression
from sklearn.metrics import f1_score, mean_absolute_error, r2_score
from sklearn.model_selection import KFold
from torch.utils.data import DataLoader, TensorDataset

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg  # noqa: E402
import utils_panel as up  # noqa: E402

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

PANELS = [
    ("sy2021_sm01_w3m_off1", "Jan-Mar 2021 → Jan-Mar 2022"),
    ("sy2021_sm03_w3m_off1", "Mar-May 2021 → Mar-May 2022"),
    ("sy2021_sm05_w3m_off1", "May-Jul 2021 → May-Jul 2022"),
    ("sy2021_sm09_w3m_off1", "Sep-Nov 2021 → Sep-Nov 2022"),
    ("sy2022_sm01_w3m_off1", "Jan-Mar 2022 → Jan-Mar 2023"),
    ("sy2022_sm03_w3m_off1", "Mar-May 2022 → Mar-May 2023"),
    ("sy2022_sm05_w3m_off1", "May-Jul 2022 → May-Jul 2023"),
    ("sy2021_sm01_w7m_off1", "Jan-Jul 2021 → Jan-Jul 2022 (7m)"),
    ("sy2021_sm01_w7m_off2", "Jan-Jul 2021 → Jan-Jul 2023 (7m, 2y)"),
    ("sy2022_sm01_w7m_off1", "Jan-Jul 2022 → Jan-Jul 2023 (7m)"),
    ("sy2021_sm03_w6m_off1", "Mar-Aug 2021 → Mar-Aug 2022 (6m)"),
    ("sy2021_sm09_w6m_off1", "Sep 2021-Feb 2022 → Sep 2022-Feb 2023 (6m)"),
    ("sy2021_sm01_w4m_off1", "Jan-Apr 2021 → Jan-Apr 2022 (4m)"),
    ("sy2022_sm03_w4m_off1", "Mar-Jun 2022 → Mar-Jun 2023 (4m)"),
]
CLASSES = cfg.OUTCOME_CLASSES


def _load(combo_id: str):
    p_path = up.panel_path(combo_id)
    l_path = up.label_path(combo_id)
    if not (p_path.exists() and l_path.exists()):
        return None
    panel = pd.read_parquet(p_path, columns=["public_id", "date_id", "sales_card", "segment"])
    panel["public_id"] = panel["public_id"].astype(str)
    labels = pd.read_parquet(l_path)
    labels["public_id"] = labels["public_id"].astype(str)

    feat_seg = panel[panel["segment"] == "feature"]
    tgt_seg = panel[panel["segment"] == "target"]
    valid = labels.loc[labels["outcome_3"].isin(CLASSES), "public_id"].unique()
    feat_seg = feat_seg[feat_seg["public_id"].isin(valid)]
    tgt_seg = tgt_seg[tgt_seg["public_id"].isin(valid)]

    f_pivot = feat_seg.pivot_table(index="public_id", columns="date_id",
                                     values="sales_card", aggfunc="mean").sort_index(axis=1)
    t_pivot = tgt_seg.pivot_table(index="public_id", columns="date_id",
                                    values="sales_card", aggfunc="mean").sort_index(axis=1)
    common = f_pivot.index.intersection(t_pivot.index)
    f_pivot = f_pivot.loc[common]
    t_pivot = t_pivot.loc[common]
    if len(common) < 500 or f_pivot.shape[1] < 4 or t_pivot.shape[1] < 4:
        return None

    F = f_pivot.to_numpy(dtype=float)
    T = t_pivot.to_numpy(dtype=float)
    means = np.nanmean(F, axis=1, keepdims=True)
    means = np.where(np.isfinite(means) & (means > 1e-9), means, 1.0)
    Fn = np.where(np.isfinite(F), F / means, 0.0).astype(np.float32)
    Tn = np.where(np.isfinite(T), T / means, 0.0).astype(np.float32)

    # ground-truth slope of target window normalized
    y_slope = up.row_slopes(Tn).astype(np.float32)
    sigma = float(np.nanstd(y_slope))
    thr = 0.5 * sigma if sigma > 0 else 0.0
    y_cls = np.where(y_slope > thr, "Growth",
                     np.where(y_slope < -thr, "Decline", "Stable"))

    return {
        "ids": np.array(common.astype(str)),
        "F": Fn, "T_avg": Tn.mean(axis=1).astype(np.float32),
        "y_slope": y_slope, "y_cls": y_cls, "thr": thr,
    }


def _bucketize(yhat: np.ndarray, thr: float) -> np.ndarray:
    return np.where(yhat > thr, "Growth", np.where(yhat < -thr, "Decline", "Stable"))


def _naive_last_slope(F: np.ndarray, w: int = 4) -> np.ndarray:
    return up.row_slopes(F[:, -w:])


def _linear_extrap(F: np.ndarray) -> np.ndarray:
    return up.row_slopes(F)


def _mlp_seq(F: np.ndarray, y_target: np.ndarray, splits) -> np.ndarray:
    yhat = np.zeros(len(y_target), dtype=np.float32)
    for tr, te in splits:
        torch.manual_seed(cfg.SEED)
        Xtr = torch.from_numpy(F[tr]); ytr = torch.from_numpy(y_target[tr])
        Xte = torch.from_numpy(F[te])
        T = F.shape[1]
        net = nn.Sequential(
            nn.Linear(T, 64), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1),
        ).to(DEVICE)
        opt = torch.optim.AdamW(net.parameters(), lr=1e-3, weight_decay=1e-4)
        ds = TensorDataset(Xtr, ytr)
        dl = DataLoader(ds, batch_size=512, shuffle=True)
        for _ in range(15):
            net.train()
            for xb, yb in dl:
                xb = xb.to(DEVICE); yb = yb.to(DEVICE)
                opt.zero_grad()
                pred = net(xb).squeeze(-1)
                loss = nn.functional.mse_loss(pred, yb)
                loss.backward()
                opt.step()
        net.eval()
        with torch.no_grad():
            chunks = []
            for i in range(0, len(Xte), 1024):
                chunks.append(net(Xte[i:i+1024].to(DEVICE)).squeeze(-1).cpu())
            yhat[te] = torch.cat(chunks).numpy()
    return yhat


def _lstm_reg(F: np.ndarray, y_target: np.ndarray, splits) -> np.ndarray:
    yhat = np.zeros(len(y_target), dtype=np.float32)
    for tr, te in splits:
        torch.manual_seed(cfg.SEED)
        Xtr = torch.from_numpy(F[tr]).unsqueeze(-1); ytr = torch.from_numpy(y_target[tr])
        Xte = torch.from_numpy(F[te]).unsqueeze(-1)
        rnn = nn.LSTM(1, 32, batch_first=True).to(DEVICE)
        head = nn.Sequential(nn.Linear(32, 16), nn.ReLU(), nn.Linear(16, 1)).to(DEVICE)
        opt = torch.optim.AdamW(list(rnn.parameters()) + list(head.parameters()),
                                  lr=1e-3, weight_decay=1e-4)
        ds = TensorDataset(Xtr, ytr)
        dl = DataLoader(ds, batch_size=512, shuffle=True)
        for _ in range(15):
            rnn.train(); head.train()
            for xb, yb in dl:
                xb = xb.to(DEVICE); yb = yb.to(DEVICE)
                opt.zero_grad()
                out, _ = rnn(xb)
                pred = head(out[:, -1, :]).squeeze(-1)
                loss = nn.functional.mse_loss(pred, yb)
                loss.backward()
                opt.step()
        rnn.eval(); head.eval()
        with torch.no_grad():
            chunks = []
            for i in range(0, len(Xte), 1024):
                xb = Xte[i:i+1024].to(DEVICE)
                out, _ = rnn(xb)
                chunks.append(head(out[:, -1, :]).squeeze(-1).cpu())
            yhat[te] = torch.cat(chunks).numpy()
    return yhat


def _eval(name: str, yhat: np.ndarray, y_slope: np.ndarray,
          y_cls: np.ndarray, thr: float) -> dict:
    pred_cls = _bucketize(yhat, thr)
    return {
        "model": name,
        "mae": float(mean_absolute_error(y_slope, yhat)),
        "r2": float(r2_score(y_slope, yhat)),
        "macro_f1": float(f1_score(y_cls, pred_cls, average="macro", zero_division=0)),
    }


def main() -> None:
    rows = []
    out_path = cfg.TABLE_DIR / "ts_benchmark_compare.csv"
    for combo_id, desc in PANELS:
        bundle = _load(combo_id)
        if bundle is None:
            print(f"[07] skip {combo_id}", flush=True)
            continue
        F = bundle["F"]; y_slope = bundle["y_slope"]
        y_cls = bundle["y_cls"]; thr = bundle["thr"]
        n = len(F)

        # naive baselines (no fold-splitting needed)
        for nm, yh in [("naive_last_slope", _naive_last_slope(F)),
                        ("linear_extrap", _linear_extrap(F))]:
            r = _eval(nm, yh.astype(np.float32), y_slope, y_cls, thr)
            r.update({"combo_id": combo_id, "description": desc, "n_stores": n})
            rows.append(r)
            print(f"[07] {combo_id} {nm:20s} mae={r['mae']:.4f} r2={r['r2']:.3f} F1={r['macro_f1']:.3f}",
                  flush=True)

        kf = KFold(n_splits=5, shuffle=True, random_state=cfg.SEED)
        splits = list(kf.split(F))

        for nm, fn in [("mlp_flat", _mlp_seq), ("lstm_reg", _lstm_reg)]:
            yh = fn(F, y_slope, splits)
            r = _eval(nm, yh, y_slope, y_cls, thr)
            r.update({"combo_id": combo_id, "description": desc, "n_stores": n})
            rows.append(r)
            print(f"[07] {combo_id} {nm:20s} mae={r['mae']:.4f} r2={r['r2']:.3f} F1={r['macro_f1']:.3f}",
                  flush=True)

        pd.DataFrame(rows).to_csv(out_path, index=False, encoding="utf-8-sig")

    out = pd.DataFrame(rows)
    print(f"[07] saved: {out_path} (rows={len(out)})")
    if not out.empty:
        agg = out.groupby("model").agg(macro_f1=("macro_f1", "mean"),
                                         mae=("mae", "mean"),
                                         n=("combo_id", "nunique")).reset_index()
        print(agg.to_string(index=False))


if __name__ == "__main__":
    main()
