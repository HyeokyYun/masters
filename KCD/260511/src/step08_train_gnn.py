"""Step 08 — GNN spatial spillover (Phase 3).

For each panel we build several store-level graphs and run a small GCN
classifier to test whether the *neighbor structure* adds predictive
information over and above the per-store features themselves.

Graphs (all undirected, self-loops added before normalization):
  - G_dong       : edge if both stores share `dong`
  - G_sigungu    : edge if both share `sigungu` (denser; per-node degree cap)
  - G_industry   : edge if both share `kostat_class` (per-node degree cap)
  - G_hybrid     : edge if both share `dong` AND `kostat_class`

Node features  = the existing 56-D tabular feature vector + meta features
(tenure_log, has_delivery, sqsize_log, prop_age one-hots).
Models         = 2-layer GCN (32 hidden, dropout 0.3), Symmetric norm.
Comparison     = same node features, same train/val/test split, but with
                 graph replaced by the identity (= "no neighbors" MLP).

Outputs:
  outputs/tables/gnn_compare.csv        (panel × graph × model rows)
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg  # noqa: E402
import utils_panel as up  # noqa: E402

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

PANELS = [
    ("sy2021_sm01_w3m_off1", "Jan-Mar 2021 → Jan-Mar 2022"),
    ("sy2022_sm01_w3m_off1", "Jan-Mar 2022 → Jan-Mar 2023"),
    ("sy2021_sm01_w7m_off1", "Jan-Jul 2021 → Jan-Jul 2022 (7m)"),
]

CLASSES = cfg.OUTCOME_CLASSES
CLS_TO_IDX = {c: i for i, c in enumerate(CLASSES)}
DEG_CAP = 30  # cap per-node degree for dense graphs


def _load(combo_id: str, meta_full: pd.DataFrame):
    f_path = up.feature_path(combo_id)
    l_path = up.label_path(combo_id)
    if not (f_path.exists() and l_path.exists()):
        return None
    feats = pd.read_parquet(f_path)
    labels = pd.read_parquet(l_path)
    feats["public_id"] = feats["public_id"].astype(str)
    labels["public_id"] = labels["public_id"].astype(str)

    df = feats.merge(labels[["public_id", "outcome_3"]], on="public_id", how="inner")
    df = df[df["outcome_3"].isin(CLASSES)].reset_index(drop=True)

    meta_p = cfg.TABLE_DIR / "features_meta" / f"features_meta_{combo_id}.parquet"
    if meta_p.exists():
        meta = pd.read_parquet(meta_p)
        meta["public_id"] = meta["public_id"].astype(str)
        keep_meta = ["public_id", "tenure_log", "has_delivery", "sqsize_log",
                      "prop_age_30대", "prop_age_40대", "prop_age_50대"]
        meta = meta[[c for c in keep_meta if c in meta.columns]]
        df = df.merge(meta, on="public_id", how="left")
    df = df.fillna(0)

    df = df.merge(meta_full[["public_id", "dong", "sigungu", "kostat_class"]],
                  on="public_id", how="left")

    base_cols = [c for c in df.columns
                 if c not in ("public_id", "outcome_3", "dong", "sigungu", "kostat_class")]
    X = df[base_cols].to_numpy(dtype=np.float32)
    # standardize
    mu = X.mean(axis=0); sd = X.std(axis=0); sd = np.where(sd > 1e-9, sd, 1.0)
    X = (X - mu) / sd
    y = df["outcome_3"].map(CLS_TO_IDX).to_numpy(dtype=np.int64)
    return df, X, y, base_cols


def _build_edges(df: pd.DataFrame, key_cols: list[str], deg_cap: int) -> tuple[np.ndarray, np.ndarray]:
    """Build edge_index using shared categorical keys with per-node degree cap.
    Vectorized: for each group, randomly permute member order and use a
    sliding window of size deg_cap to assign neighbors. This produces a graph
    with degree exactly min(group_size-1, deg_cap) per node, very fast."""
    rng = np.random.default_rng(cfg.SEED)
    src_chunks, dst_chunks = [], []
    valid = df[key_cols].notna().all(axis=1)
    sub = df[valid][["public_id"] + key_cols].copy()
    if sub.empty:
        return np.array([], dtype=np.int64), np.array([], dtype=np.int64)
    sub["__idx"] = sub.index
    grouped = sub.groupby(key_cols)["__idx"].apply(np.asarray)
    for members in grouped:
        m = members.astype(np.int64)
        if len(m) < 2:
            continue
        k = min(deg_cap, len(m) - 1)
        # for each node, pick the next k members in a random permutation (cyclic)
        perm = rng.permutation(m)
        for shift in range(1, k + 1):
            # node i connects to perm[(i+shift) % len]
            shifted = np.roll(perm, -shift)
            src_chunks.append(perm)
            dst_chunks.append(shifted)
    if not src_chunks:
        return np.array([], dtype=np.int64), np.array([], dtype=np.int64)
    src = np.concatenate(src_chunks)
    dst = np.concatenate(dst_chunks)
    return src, dst


def _norm_adj(n: int, src: np.ndarray, dst: np.ndarray) -> torch.Tensor:
    """Build sym-normalized adjacency (with self-loops) as torch sparse coo.
    Direct edge-wise computation: w_uv = 1 / sqrt(deg_u * deg_v)."""
    if len(src) == 0:
        idx = np.arange(n, dtype=np.int64)
        src = idx; dst = idx
    self_idx = np.arange(n, dtype=np.int64)
    src_full = np.concatenate([src, self_idx])
    dst_full = np.concatenate([dst, self_idx])
    # degree
    deg = np.bincount(src_full, minlength=n).astype(np.float32)
    d_inv_sqrt = np.where(deg > 0, deg ** -0.5, 0.0)
    values = (d_inv_sqrt[src_full] * d_inv_sqrt[dst_full]).astype(np.float32)
    indices = torch.from_numpy(np.stack([src_full, dst_full]).astype(np.int64))
    vals = torch.from_numpy(values)
    return torch.sparse_coo_tensor(indices, vals, (n, n))


class GCN(nn.Module):
    def __init__(self, in_d: int, h: int = 32, n_cls: int = 3, dropout: float = 0.3):
        super().__init__()
        self.W1 = nn.Linear(in_d, h)
        self.W2 = nn.Linear(h, h)
        self.head = nn.Linear(h, n_cls)
        self.dropout = dropout

    def forward(self, X: torch.Tensor, A: torch.Tensor) -> torch.Tensor:
        h = torch.sparse.mm(A, X)
        h = F.relu(self.W1(h))
        h = F.dropout(h, p=self.dropout, training=self.training)
        h = torch.sparse.mm(A, h)
        h = F.relu(self.W2(h))
        return self.head(h)


class MLP(nn.Module):
    def __init__(self, in_d: int, h: int = 32, n_cls: int = 3, dropout: float = 0.3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_d, h), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(h, h), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(h, n_cls),
        )

    def forward(self, X: torch.Tensor, A: torch.Tensor = None) -> torch.Tensor:
        return self.net(X)


def _train_eval(model_cls, X: np.ndarray, y: np.ndarray, A: torch.Tensor,
                splits, epochs: int = 25) -> list[float]:
    f1s = []
    counts = np.bincount(y, minlength=3).astype(float)
    weights = (1.0 / np.maximum(counts, 1.0))
    weights = weights / weights.sum() * 3
    Xt = torch.from_numpy(X).to(DEVICE)
    yt = torch.from_numpy(y).to(DEVICE)
    A = A.to(DEVICE)
    for tr, te in splits:
        torch.manual_seed(cfg.SEED)
        m = model_cls(X.shape[1]).to(DEVICE)
        opt = torch.optim.AdamW(m.parameters(), lr=5e-3, weight_decay=1e-4)
        crit = nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float32, device=DEVICE))
        tr_t = torch.from_numpy(tr).to(DEVICE)
        te_t = torch.from_numpy(te).to(DEVICE)
        best = -1.0
        patience = 0
        for ep in range(epochs):
            m.train()
            opt.zero_grad()
            logits = m(Xt, A)
            loss = crit(logits[tr_t], yt[tr_t])
            loss.backward()
            opt.step()
            if ep % 2 == 0:
                m.eval()
                with torch.no_grad():
                    pred = m(Xt, A)[te_t].argmax(1).cpu().numpy()
                f1 = f1_score(y[te], pred, average="macro", zero_division=0)
                if f1 > best + 1e-4:
                    best = f1; patience = 0
                else:
                    patience += 1
                    if patience >= 6:
                        break
        f1s.append(best)
    return f1s


def main() -> None:
    meta = pd.read_csv(cfg.META_PATH, dtype={"public_id": str},
                        usecols=["public_id", "dong", "sigungu", "kostat_class"])

    rows = []
    out_path = cfg.TABLE_DIR / "gnn_compare.csv"

    GRAPH_DEFS = [
        ("dong", ["dong"]),
        ("industry", ["kostat_class"]),
        ("hybrid_dong_industry", ["dong", "kostat_class"]),
    ]

    for combo_id, desc in PANELS:
        bundle = _load(combo_id, meta)
        if bundle is None:
            print(f"[08] skip {combo_id}", flush=True)
            continue
        df, X, y, base_cols = bundle
        n = len(df)
        print(f"[08] {combo_id} n={n} F={X.shape[1]}", flush=True)

        skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=cfg.SEED)
        splits = list(skf.split(X, y))

        # MLP baseline (no graph) — done once per panel
        A_eye_idx = np.arange(n, dtype=np.int64)
        A_eye = _norm_adj(n, A_eye_idx, A_eye_idx)
        f1s = _train_eval(MLP, X, y, A_eye, splits)
        rows.append({"combo_id": combo_id, "graph": "none", "model": "mlp",
                     "macro_f1_mean": float(np.mean(f1s)), "macro_f1_std": float(np.std(f1s)),
                     "n_stores": n, "n_edges": 0})
        print(f"[08]   mlp(no graph)   macroF1={np.mean(f1s):.3f}±{np.std(f1s):.3f}", flush=True)

        for gname, keys in GRAPH_DEFS:
            print(f"[08]   building graph {gname} keys={keys}...", flush=True)
            src, dst = _build_edges(df, keys, deg_cap=DEG_CAP)
            n_edges = len(src)
            print(f"[08]   {gname} edges={n_edges}, normalizing...", flush=True)
            import time
            t0 = time.time()
            A = _norm_adj(n, src, dst)
            print(f"[08]   {gname} norm took {time.time()-t0:.1f}s", flush=True)
            for mname, mcls in [("gcn", GCN), ("mlp", MLP)]:
                print(f"[08]   {gname} training {mname}...", flush=True)
                t1 = time.time()
                f1s = _train_eval(mcls, X, y, A, splits)
                rows.append({"combo_id": combo_id, "graph": gname, "model": mname,
                             "macro_f1_mean": float(np.mean(f1s)),
                             "macro_f1_std": float(np.std(f1s)),
                             "n_stores": n, "n_edges": int(n_edges)})
                print(f"[08]   {gname:22s} {mname:4s} edges={n_edges:>9} "
                      f"macroF1={np.mean(f1s):.3f}±{np.std(f1s):.3f} ({time.time()-t1:.0f}s)",
                      flush=True)
        pd.DataFrame(rows).to_csv(out_path, index=False, encoding="utf-8-sig")

    out = pd.DataFrame(rows)
    print(f"[08] saved: {out_path} (rows={len(out)})")
    if not out.empty:
        agg = (out.groupby(["graph", "model"])
               .agg(macro_f1=("macro_f1_mean", "mean"))
               .reset_index().sort_values("macro_f1", ascending=False))
        print(agg.to_string(index=False))


if __name__ == "__main__":
    main()
