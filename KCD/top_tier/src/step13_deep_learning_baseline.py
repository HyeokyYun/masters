"""Step 13 — Deep Learning Baselines (LSTM / GRU / Transformer).

Proposed Model D(hand-crafted 46 feature + hybrid cluster + change-point)를
30주 시퀀스를 직접 입력받는 딥러닝 모델과 비교한다.

동일한 StratifiedKFold 5-fold, 동일한 store 집합, 동일한 평가지표 사용.
"""
from __future__ import annotations

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

import os as _os
_force_cpu = _os.environ.get("FORCE_CPU", "1") == "1"
if not _force_cpu and torch.cuda.is_available():
    try:
        _t = torch.zeros(1, device="cuda") + 1
        DEVICE = torch.device("cuda")
    except Exception as e:
        print(f"[13] CUDA unusable ({e}); falling back to CPU")
        DEVICE = torch.device("cpu")
else:
    DEVICE = torch.device("cpu")
print(f"[13] device: {DEVICE}")
torch.set_num_threads(min(16, _os.cpu_count() or 8))

SEQ_LEN = cfg.PREDICTION_WEEKS
BATCH = 256
EPOCHS = 20
LR = 1e-3


def load_sequences():
    panel = pd.read_parquet(cfg.PANEL_PATH)
    panel["public_id"] = panel["public_id"].astype(str)
    panel = panel[panel["observed_week_idx"] < SEQ_LEN]
    pivot = panel.pivot_table(index="public_id", columns="observed_week_idx",
                              values="sales_card_mm", aggfunc="mean")
    pivot = pivot.dropna(axis=1, thresh=int(len(pivot) * 0.6))
    pivot = pivot.dropna(axis=0, thresh=int(pivot.shape[1] * 0.85))
    pivot = pivot.fillna(pivot.median(axis=0))
    pivot.index = pivot.index.astype(str)
    return pivot


def align_labels(seq_df: pd.DataFrame):
    feat = pd.read_parquet(cfg.TABLE_DIR / "prediction_feature_matrix.parquet")
    feat["public_id"] = feat["public_id"].astype(str)
    common = seq_df.index.intersection(feat["public_id"])
    seq_df = seq_df.loc[common]
    feat = feat.set_index("public_id").loc[common]
    y = feat["outcome_3"].values
    return seq_df, y


def standardize_per_store(X: np.ndarray) -> np.ndarray:
    mu = X.mean(axis=1, keepdims=True)
    sd = X.std(axis=1, keepdims=True)
    sd[sd < 1e-6] = 1.0
    return (X - mu) / sd


class LSTMClassifier(nn.Module):
    def __init__(self, hidden=64, n_classes=3, dropout=0.3):
        super().__init__()
        self.lstm = nn.LSTM(input_size=1, hidden_size=hidden,
                            num_layers=2, batch_first=True,
                            dropout=dropout, bidirectional=True)
        self.head = nn.Sequential(
            nn.Linear(hidden * 2, 64), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(64, n_classes),
        )

    def forward(self, x):
        out, _ = self.lstm(x)
        last = out[:, -1, :]
        return self.head(last)


class GRUClassifier(nn.Module):
    def __init__(self, hidden=64, n_classes=3, dropout=0.3):
        super().__init__()
        self.gru = nn.GRU(input_size=1, hidden_size=hidden,
                          num_layers=2, batch_first=True,
                          dropout=dropout, bidirectional=True)
        self.head = nn.Sequential(
            nn.Linear(hidden * 2, 64), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(64, n_classes),
        )

    def forward(self, x):
        out, _ = self.gru(x)
        return self.head(out[:, -1, :])


class TransformerClassifier(nn.Module):
    def __init__(self, d_model=32, nhead=4, n_layers=2, n_classes=3, dropout=0.2):
        super().__init__()
        self.proj = nn.Linear(1, d_model)
        self.pos_emb = nn.Parameter(torch.zeros(1, SEQ_LEN, d_model))
        layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=nhead, dim_feedforward=d_model * 4,
            dropout=dropout, batch_first=True, activation="gelu",
        )
        self.enc = nn.TransformerEncoder(layer, num_layers=n_layers)
        self.head = nn.Sequential(
            nn.LayerNorm(d_model), nn.Linear(d_model, n_classes),
        )

    def forward(self, x):
        h = self.proj(x) + self.pos_emb
        h = self.enc(h)
        return self.head(h.mean(dim=1))


def train_one_fold(model_cls, X_tr, y_tr, X_te, y_te, classes, name):
    model = model_cls().to(DEVICE)
    opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)

    c2i = {c: i for i, c in enumerate(classes)}
    y_tr_e = np.array([c2i[v] for v in y_tr])

    counts = np.bincount(y_tr_e, minlength=len(classes)).astype(float)
    weights = counts.sum() / (len(classes) * np.clip(counts, 1, None))
    loss_fn = nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float32, device=DEVICE))

    X_tr_t = torch.from_numpy(X_tr).float().unsqueeze(-1)
    y_tr_t = torch.from_numpy(y_tr_e).long()
    dl = DataLoader(TensorDataset(X_tr_t, y_tr_t), batch_size=BATCH, shuffle=True,
                    num_workers=0, pin_memory=True)

    model.train()
    for ep in range(EPOCHS):
        ep_loss = 0.0
        for xb, yb in dl:
            xb, yb = xb.to(DEVICE, non_blocking=True), yb.to(DEVICE, non_blocking=True)
            logits = model(xb)
            loss = loss_fn(logits, yb)
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            ep_loss += loss.item() * xb.size(0)
        sched.step()

    model.eval()
    with torch.no_grad():
        X_te_t = torch.from_numpy(X_te).float().unsqueeze(-1).to(DEVICE)
        logits = model(X_te_t)
        proba = torch.softmax(logits, dim=1).cpu().numpy()
    preds = np.array([classes[i] for i in proba.argmax(1)])

    per = precision_recall_fscore_support(y_te, preds, labels=classes, zero_division=0)
    try:
        auc = roc_auc_score(pd.get_dummies(y_te)[classes].values, proba, multi_class="ovr")
    except Exception:
        auc = np.nan
    return {
        "model": name,
        "macro_f1": f1_score(y_te, preds, average="macro", zero_division=0),
        "auc_ovr": auc,
        **{f"recall_{c}": per[1][i] for i, c in enumerate(classes)},
        **{f"f1_{c}": per[2][i] for i, c in enumerate(classes)},
    }


def main():
    seq_df = load_sequences()
    seq_df, y = align_labels(seq_df)
    X = standardize_per_store(seq_df.to_numpy().astype(np.float32))
    classes = cfg.OUTCOME_CLASSES
    print(f"[13] aligned: {X.shape}, y classes {np.unique(y, return_counts=True)}")

    skf = StratifiedKFold(n_splits=cfg.CV_FOLDS, shuffle=True, random_state=cfg.SEED)
    models = {
        "LSTM_bi": LSTMClassifier,
        "GRU_bi": GRUClassifier,
        "Transformer": TransformerClassifier,
    }

    all_rows = []
    for name, cls in models.items():
        print(f"\n=== {name} ===")
        for fold, (tr, te) in enumerate(skf.split(X, y)):
            t0 = time.time()
            r = train_one_fold(cls, X[tr], y[tr], X[te], y[te], classes, name)
            r["fold"] = fold
            r["time_sec"] = round(time.time() - t0, 1)
            all_rows.append(r)
            print(f"  fold={fold}  F1={r['macro_f1']:.3f}  "
                  f"G_rec={r['recall_Growth']:.3f}  "
                  f"D_rec={r['recall_Decline']:.3f}  "
                  f"AUC={r['auc_ovr']:.3f}  ({r['time_sec']}s)")

    df = pd.DataFrame(all_rows)
    df.to_csv(cfg.TABLE_DIR / "deep_baseline_cv_folds.csv", index=False, encoding="utf-8-sig")

    agg = df.groupby("model").agg(["mean", "std"]).round(4)
    agg.to_csv(cfg.TABLE_DIR / "deep_baseline_summary.csv", encoding="utf-8-sig")
    print("\n=== Summary (mean ± std) ===")
    print(agg[[("macro_f1", "mean"), ("macro_f1", "std"),
               ("recall_Growth", "mean"), ("recall_Decline", "mean"),
               ("auc_ovr", "mean")]].to_string())

    hyb = pd.read_csv(cfg.TABLE_DIR / "hybrid_prediction_summary.csv", header=[0, 1], index_col=0)
    rows = []
    for m in hyb.index:
        rows.append({
            "model": m,
            "family": "classical/hybrid",
            "macro_f1_mean": hyb.loc[m, ("macro_f1", "mean")],
            "macro_f1_std": hyb.loc[m, ("macro_f1", "std")],
            "recall_Growth": hyb.loc[m, ("recall_Growth", "mean")],
            "recall_Decline": hyb.loc[m, ("recall_Decline", "mean")],
            "auc_ovr": hyb.loc[m, ("auc_ovr", "mean")],
        })
    for m in agg.index:
        rows.append({
            "model": m,
            "family": "deep_sequence",
            "macro_f1_mean": agg.loc[m, ("macro_f1", "mean")],
            "macro_f1_std": agg.loc[m, ("macro_f1", "std")],
            "recall_Growth": agg.loc[m, ("recall_Growth", "mean")],
            "recall_Decline": agg.loc[m, ("recall_Decline", "mean")],
            "auc_ovr": agg.loc[m, ("auc_ovr", "mean")],
        })
    cmp_df = pd.DataFrame(rows).sort_values("macro_f1_mean", ascending=False)
    cmp_df.to_csv(cfg.TABLE_DIR / "deep_vs_hybrid_comparison.csv", index=False, encoding="utf-8-sig")
    print("\n=== Deep vs Hybrid/Classical ===")
    print(cmp_df.to_string(index=False))


if __name__ == "__main__":
    main()
