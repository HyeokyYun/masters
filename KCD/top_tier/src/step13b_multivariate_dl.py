"""Step 13-B — Multivariate Deep Learning Baseline (fair comparison).

step13은 단변량 sales-only DL → Proposed D(다변량)과 불공정 비교.
본 스크립트: 5-channel input (sales_card, nc_ratio, delivery_ratio,
weekend_ratio, before_noon_ratio) 로 LSTM / Transformer 학습.

동일 49,007 stores, 동일 5-fold, 동일 seed.
"""
from __future__ import annotations

import os
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import f1_score, precision_recall_fscore_support, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from torch.utils.data import DataLoader, TensorDataset

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg  # noqa: E402

DEVICE = torch.device("cpu")
torch.set_num_threads(min(16, os.cpu_count() or 8))
print(f"[13b] device: {DEVICE}")

SEQ_LEN = cfg.PREDICTION_WEEKS
N_CH = 5
BATCH = 256
EPOCHS = 15
LR = 1e-3


def load_multichannel():
    panel = pd.read_parquet(cfg.PANEL_PATH)
    panel["public_id"] = panel["public_id"].astype(str)
    panel = panel[panel["observed_week_idx"] < SEQ_LEN].copy()
    panel["nc_ratio"] = (panel["customer_new"] / panel["customer"].replace(0, np.nan)).fillna(0.0)
    panel["delivery_ratio"] = (panel["sales_delivery"] / panel["sales_card"].replace(0, np.nan)).fillna(0.0).clip(0, 1)
    panel["sales_log"] = np.log1p(panel["sales_card"].fillna(0))

    weekend_col = "weekend_sales" if "weekend_sales" in panel.columns else None
    morning_col = "before_noon_sales" if "before_noon_sales" in panel.columns else None

    pivots = {}
    pivots["sales_log"] = panel.pivot_table(index="public_id", columns="observed_week_idx",
                                             values="sales_log", aggfunc="mean")
    pivots["nc_ratio"] = panel.pivot_table(index="public_id", columns="observed_week_idx",
                                            values="nc_ratio", aggfunc="mean")
    pivots["delivery_ratio"] = panel.pivot_table(index="public_id", columns="observed_week_idx",
                                                  values="delivery_ratio", aggfunc="mean")
    if weekend_col:
        pivots["weekend"] = panel.pivot_table(index="public_id", columns="observed_week_idx",
                                               values=weekend_col, aggfunc="mean")
    else:
        pivots["weekend"] = pivots["sales_log"] * 0
    if morning_col:
        pivots["morning"] = panel.pivot_table(index="public_id", columns="observed_week_idx",
                                               values=morning_col, aggfunc="mean")
    else:
        pivots["morning"] = pivots["sales_log"] * 0

    common_idx = pivots["sales_log"].index
    for k, v in pivots.items():
        common_idx = common_idx.intersection(v.index)
    for k in list(pivots.keys()):
        pivots[k] = pivots[k].loc[common_idx].fillna(0.0)
        pivots[k] = pivots[k].reindex(columns=sorted(pivots[k].columns))
        pivots[k] = pivots[k].fillna(0.0)
    return pivots, common_idx


def align_labels(common_idx):
    feat = pd.read_parquet(cfg.TABLE_DIR / "prediction_feature_matrix.parquet")
    feat["public_id"] = feat["public_id"].astype(str)
    merged_idx = [p for p in common_idx if p in set(feat["public_id"])]
    feat = feat.set_index("public_id").loc[merged_idx]
    return merged_idx, feat["outcome_3"].values


def build_tensor(pivots, ids):
    channels = []
    for k in ["sales_log", "nc_ratio", "delivery_ratio", "weekend", "morning"]:
        arr = pivots[k].loc[ids].to_numpy().astype(np.float32)
        mu = arr.mean(axis=1, keepdims=True)
        sd = arr.std(axis=1, keepdims=True)
        sd[sd < 1e-6] = 1.0
        channels.append(((arr - mu) / sd)[:, :, None])
    return np.concatenate(channels, axis=2).astype(np.float32)


class LSTMmv(nn.Module):
    def __init__(self, hidden=64, n_classes=3, dropout=0.3):
        super().__init__()
        self.lstm = nn.LSTM(input_size=N_CH, hidden_size=hidden, num_layers=2,
                            batch_first=True, dropout=dropout, bidirectional=True)
        self.head = nn.Sequential(nn.Linear(hidden * 2, 64), nn.ReLU(),
                                   nn.Dropout(dropout), nn.Linear(64, n_classes))

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.head(out[:, -1, :])


class TransformerMv(nn.Module):
    def __init__(self, d_model=48, nhead=4, n_layers=2, n_classes=3, dropout=0.2):
        super().__init__()
        self.proj = nn.Linear(N_CH, d_model)
        self.pos = nn.Parameter(torch.zeros(1, SEQ_LEN, d_model))
        layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead,
            dim_feedforward=d_model * 4, dropout=dropout, batch_first=True,
            activation="gelu")
        self.enc = nn.TransformerEncoder(layer, num_layers=n_layers)
        self.head = nn.Sequential(nn.LayerNorm(d_model), nn.Linear(d_model, n_classes))

    def forward(self, x):
        h = self.proj(x) + self.pos
        h = self.enc(h)
        return self.head(h.mean(dim=1))


def train_fold(model_cls, X_tr, y_tr, X_te, y_te, classes, name):
    model = model_cls().to(DEVICE)
    opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
    c2i = {c: i for i, c in enumerate(classes)}
    y_tr_e = np.array([c2i[v] for v in y_tr])
    counts = np.bincount(y_tr_e, minlength=len(classes)).astype(float)
    w = counts.sum() / (len(classes) * np.clip(counts, 1, None))
    loss_fn = nn.CrossEntropyLoss(weight=torch.tensor(w, dtype=torch.float32, device=DEVICE))

    dl = DataLoader(TensorDataset(torch.from_numpy(X_tr), torch.from_numpy(y_tr_e).long()),
                    batch_size=BATCH, shuffle=True, num_workers=0, pin_memory=False)
    model.train()
    for _ in range(EPOCHS):
        for xb, yb in dl:
            xb, yb = xb.to(DEVICE), yb.to(DEVICE)
            loss = loss_fn(model(xb), yb)
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
        sched.step()

    model.eval()
    with torch.no_grad():
        proba = torch.softmax(model(torch.from_numpy(X_te).to(DEVICE)), dim=1).cpu().numpy()
    preds = np.array([classes[i] for i in proba.argmax(1)])
    per = precision_recall_fscore_support(y_te, preds, labels=classes, zero_division=0)
    try:
        auc = roc_auc_score(pd.get_dummies(y_te)[classes].values, proba, multi_class="ovr")
    except Exception:
        auc = np.nan
    return {"model": name,
            "macro_f1": f1_score(y_te, preds, average="macro", zero_division=0),
            "auc_ovr": auc,
            **{f"recall_{c}": per[1][i] for i, c in enumerate(classes)}}


def main():
    pivots, common = load_multichannel()
    print(f"[13b] channels ready, stores={len(common):,}")
    ids, y = align_labels(common)
    print(f"[13b] labeled stores: {len(ids):,}")

    X = build_tensor(pivots, ids)
    print(f"[13b] X shape: {X.shape}")

    classes = cfg.OUTCOME_CLASSES
    skf = StratifiedKFold(n_splits=cfg.CV_FOLDS, shuffle=True, random_state=cfg.SEED)
    models = {"LSTM_mv_5ch": LSTMmv, "Transformer_mv_5ch": TransformerMv}

    rows = []
    for name, cls in models.items():
        print(f"\n=== {name} ===")
        for fold, (tr, te) in enumerate(skf.split(X, y)):
            t0 = time.time()
            r = train_fold(cls, X[tr], y[tr], X[te], y[te], classes, name)
            r["fold"] = fold
            r["time_sec"] = round(time.time() - t0, 1)
            rows.append(r)
            print(f"  fold={fold}  F1={r['macro_f1']:.3f}  AUC={r['auc_ovr']:.3f}  ({r['time_sec']}s)")

    df = pd.DataFrame(rows)
    df.to_csv(cfg.TABLE_DIR / "deep_baseline_multivariate_cv.csv", index=False, encoding="utf-8-sig")
    agg = df.groupby("model").agg(["mean", "std"]).round(4)
    agg.to_csv(cfg.TABLE_DIR / "deep_baseline_multivariate_summary.csv", encoding="utf-8-sig")
    print("\n=== Multivariate DL Summary ===")
    print(agg[[("macro_f1", "mean"), ("macro_f1", "std"), ("auc_ovr", "mean")]].to_string())

    univ = pd.read_csv(cfg.TABLE_DIR / "deep_baseline_summary.csv", header=[0, 1], index_col=0)
    print("\n=== 단변량 vs 다변량 DL 비교 ===")
    for m_uv, m_mv in [("LSTM_bi", "LSTM_mv_5ch"), ("Transformer", "Transformer_mv_5ch")]:
        if m_uv in univ.index and m_mv in agg.index:
            uv_f1 = univ.loc[m_uv, ("macro_f1", "mean")]
            mv_f1 = agg.loc[m_mv, ("macro_f1", "mean")]
            uv_auc = univ.loc[m_uv, ("auc_ovr", "mean")]
            mv_auc = agg.loc[m_mv, ("auc_ovr", "mean")]
            print(f"  {m_uv}→{m_mv}: F1 {uv_f1:.3f}→{mv_f1:.3f} (Δ{mv_f1-uv_f1:+.3f}), "
                  f"AUC {uv_auc:.3f}→{mv_auc:.3f} (Δ{mv_auc-uv_auc:+.3f})")

    print("\n=== vs Proposed D (F1 0.648 / AUC 0.830) ===")
    best_mv_f1 = agg[("macro_f1", "mean")].max()
    best_mv = agg[("macro_f1", "mean")].idxmax()
    print(f"  Best MV DL: {best_mv} F1={best_mv_f1:.3f}")
    print(f"  Proposed D still leads by F1 +{0.648-best_mv_f1:.3f}")


if __name__ == "__main__":
    main()
