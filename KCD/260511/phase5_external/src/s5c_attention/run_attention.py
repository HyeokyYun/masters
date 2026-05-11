"""Phase 5C runner — FeatureAttnMLP / TimeAttnLSTM / FiLM_TenureLSTM.

3-fold StratifiedKFold (step06와 동일) + RF baseline re-run for paired t-test.

Outputs:
  outputs/tables/attention_compare.csv
  outputs/tables/attention_paired.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.paths import PANELS, PHASE5_TABLE_DIR, SEED, up  # noqa: E402
from common.seq_loader import load_seq  # noqa: E402
from common.cv_harness import rf_baseline_folds, paired_t_test, DEVICE  # noqa: E402
from s5c_attention.models import FeatureAttnMLP, TimeAttnLSTM, FiLM_TenureLSTM  # noqa: E402


def _load_tab_features(combo_id: str, ids: np.ndarray) -> np.ndarray:
    """43 base + 13 meta = 56 features, fill NaN with 0."""
    base = pd.read_parquet(up.feature_path(combo_id))
    base["public_id"] = base["public_id"].astype(str)
    meta_path = up.cfg.TABLE_DIR / "features_meta" / f"features_meta_{combo_id}.parquet"
    if meta_path.exists():
        meta = pd.read_parquet(meta_path)
        meta["public_id"] = meta["public_id"].astype(str)
        # drop non-numeric meta columns
        drop = [c for c in meta.columns if meta[c].dtype == object and c != "public_id"]
        meta = meta.drop(columns=drop)
        joined = base.merge(meta, on="public_id", how="left")
    else:
        joined = base
    df = pd.DataFrame({"public_id": ids}).merge(joined, on="public_id", how="left")
    cols = [c for c in joined.columns if c != "public_id"]
    arr = df[cols].fillna(0.0).to_numpy(dtype=np.float32)
    return arr, cols


def _load_tenure(combo_id: str, ids: np.ndarray) -> np.ndarray:
    """[N, 1] tenure_log (standardized within panel)."""
    meta_path = up.cfg.TABLE_DIR / "features_meta" / f"features_meta_{combo_id}.parquet"
    if not meta_path.exists():
        return np.zeros((len(ids), 1), dtype=np.float32)
    meta = pd.read_parquet(meta_path)
    meta["public_id"] = meta["public_id"].astype(str)
    df = pd.DataFrame({"public_id": ids}).merge(meta[["public_id", "tenure_log"]], on="public_id", how="left")
    t = df["tenure_log"].fillna(0.0).to_numpy(dtype=np.float32)
    mu, sigma = float(t.mean()), float(t.std())
    if sigma < 1e-9:
        sigma = 1.0
    return ((t - mu) / sigma).reshape(-1, 1).astype(np.float32)


def _train_eval_tabular(model_cls, n_feat: int, X_tab: np.ndarray, y: np.ndarray,
                         epochs: int = 12, patience: int = 3, lr: float = 2e-3) -> list[float]:
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED)
    counts = np.bincount(y, minlength=3).astype(float)
    w = 1.0 / np.maximum(counts, 1.0); w = w / w.sum() * 3.0
    f1s = []
    # standardize tabular per-fold (avoid leakage)
    for tr, te in skf.split(np.zeros(len(y)), y):
        torch.manual_seed(SEED)
        mu = X_tab[tr].mean(0); sd = X_tab[tr].std(0) + 1e-6
        Xtr = ((X_tab[tr] - mu) / sd).astype(np.float32)
        Xte = ((X_tab[te] - mu) / sd).astype(np.float32)
        model = model_cls(n_feat=n_feat).to(DEVICE)
        opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
        crit = nn.CrossEntropyLoss(weight=torch.tensor(w, dtype=torch.float32, device=DEVICE))
        ds = TensorDataset(torch.from_numpy(Xtr), torch.from_numpy(y[tr]))
        loader = DataLoader(ds, batch_size=2048, shuffle=True, drop_last=False)
        Xte_t = torch.from_numpy(Xte); yte = y[te]
        best = -1.0; bad = 0
        for _ in range(epochs):
            model.train()
            for xb, yb in loader:
                xb = xb.to(DEVICE); yb = yb.to(DEVICE)
                opt.zero_grad()
                loss = crit(model(xb), yb)
                loss.backward()
                opt.step()
            model.eval()
            with torch.no_grad():
                preds = []
                for i in range(0, len(Xte_t), 1024):
                    preds.append(model(Xte_t[i:i+1024].to(DEVICE)).argmax(1).cpu())
                pred = torch.cat(preds).numpy()
            f1 = f1_score(yte, pred, average="macro", zero_division=0)
            if f1 > best + 1e-4: best = f1; bad = 0
            else:
                bad += 1
                if bad >= patience: break
        f1s.append(best)
    return f1s


def _train_eval_seq(model_factory, X: np.ndarray, y: np.ndarray,
                    cond: np.ndarray | None = None,
                    epochs: int = 12, patience: int = 3, lr: float = 2e-3) -> list[float]:
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED)
    counts = np.bincount(y, minlength=3).astype(float)
    w = 1.0 / np.maximum(counts, 1.0); w = w / w.sum() * 3.0
    T, C = X.shape[1], X.shape[2]
    f1s = []
    for tr, te in skf.split(np.zeros(len(y)), y):
        torch.manual_seed(SEED)
        model = model_factory(T, C).to(DEVICE)
        opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
        crit = nn.CrossEntropyLoss(weight=torch.tensor(w, dtype=torch.float32, device=DEVICE))
        if cond is None:
            ds = TensorDataset(torch.from_numpy(X[tr]), torch.from_numpy(y[tr]))
            Xte_t = torch.from_numpy(X[te])
        else:
            ds = TensorDataset(torch.from_numpy(X[tr]), torch.from_numpy(cond[tr]),
                               torch.from_numpy(y[tr]))
            Xte_t = torch.from_numpy(X[te])
            Cte_t = torch.from_numpy(cond[te])
        loader = DataLoader(ds, batch_size=2048, shuffle=True, drop_last=False)
        yte = y[te]
        best = -1.0; bad = 0
        for _ in range(epochs):
            model.train()
            for batch in loader:
                if cond is None:
                    xb, yb = batch
                    xb = xb.to(DEVICE); yb = yb.to(DEVICE)
                    logits = model(xb)
                else:
                    xb, cb, yb = batch
                    xb = xb.to(DEVICE); cb = cb.to(DEVICE); yb = yb.to(DEVICE)
                    logits = model(xb, cb)
                opt.zero_grad()
                loss = crit(logits, yb)
                loss.backward()
                opt.step()
            model.eval()
            with torch.no_grad():
                preds = []
                for i in range(0, len(Xte_t), 1024):
                    if cond is None:
                        out = model(Xte_t[i:i+1024].to(DEVICE))
                    else:
                        out = model(Xte_t[i:i+1024].to(DEVICE),
                                    Cte_t[i:i+1024].to(DEVICE))
                    preds.append(out.argmax(1).cpu())
                pred = torch.cat(preds).numpy()
            f1 = f1_score(yte, pred, average="macro", zero_division=0)
            if f1 > best + 1e-4: best = f1; bad = 0
            else:
                bad += 1
                if bad >= patience: break
        f1s.append(best)
    return f1s


def main():
    rows, paired = [], []
    for combo_id, desc in PANELS:
        print(f"[5C] === {combo_id} ===", flush=True)
        ids, X, y = load_seq(combo_id)
        if ids is None:
            print(f"[5C] skip {combo_id}")
            continue
        X_tab, _ = _load_tab_features(combo_id, ids)
        cond = _load_tenure(combo_id, ids)

        # RF baseline (same split) for paired delta
        rf_f1 = rf_baseline_folds(combo_id, ids, y)
        rows.append({
            "combo_id": combo_id, "description": desc, "model": "rf_tabular",
            "macro_f1_mean": float(np.mean(rf_f1)),
            "macro_f1_std": float(np.std(rf_f1)),
            "n_stores": int(len(ids)), "T": int(X.shape[1]), "C": int(X.shape[2]),
        })
        print(f"[5C] {combo_id} rf_tabular   F1={np.mean(rf_f1):.3f}", flush=True)

        # 1. FeatureAttnMLP on tabular 56-D
        n_feat = X_tab.shape[1]
        f1s = _train_eval_tabular(lambda n_feat=n_feat: FeatureAttnMLP(n_feat=n_feat),
                                   n_feat, X_tab, y)
        rows.append({"combo_id": combo_id, "description": desc, "model": "feature_attn_mlp",
                     "macro_f1_mean": float(np.mean(f1s)),
                     "macro_f1_std": float(np.std(f1s)),
                     "n_stores": int(len(ids)), "T": int(X.shape[1]), "C": int(X.shape[2])})
        d, t, p = paired_t_test(rf_f1, f1s)
        paired.append({"combo_id": combo_id, "model": "feature_attn_mlp",
                        "delta_mean": d, "t_stat": t, "p_value": p})
        print(f"[5C] {combo_id} feat_attn_mlp F1={np.mean(f1s):.3f} Δ={d:+.4f} p={p:.3f}", flush=True)

        # 2. TimeAttnLSTM on sequence
        f1s = _train_eval_seq(lambda T, C: TimeAttnLSTM(c=C), X, y)
        rows.append({"combo_id": combo_id, "description": desc, "model": "time_attn_lstm",
                     "macro_f1_mean": float(np.mean(f1s)),
                     "macro_f1_std": float(np.std(f1s)),
                     "n_stores": int(len(ids)), "T": int(X.shape[1]), "C": int(X.shape[2])})
        d, t, p = paired_t_test(rf_f1, f1s)
        paired.append({"combo_id": combo_id, "model": "time_attn_lstm",
                        "delta_mean": d, "t_stat": t, "p_value": p})
        print(f"[5C] {combo_id} time_attn_lstm F1={np.mean(f1s):.3f} Δ={d:+.4f} p={p:.3f}", flush=True)

        # 3. FiLM_TenureLSTM on sequence + tenure
        f1s = _train_eval_seq(lambda T, C: FiLM_TenureLSTM(c=C, cond_dim=cond.shape[1]),
                              X, y, cond=cond)
        rows.append({"combo_id": combo_id, "description": desc, "model": "film_tenure_lstm",
                     "macro_f1_mean": float(np.mean(f1s)),
                     "macro_f1_std": float(np.std(f1s)),
                     "n_stores": int(len(ids)), "T": int(X.shape[1]), "C": int(X.shape[2])})
        d, t, p = paired_t_test(rf_f1, f1s)
        paired.append({"combo_id": combo_id, "model": "film_tenure_lstm",
                        "delta_mean": d, "t_stat": t, "p_value": p})
        print(f"[5C] {combo_id} film_tenure_lstm F1={np.mean(f1s):.3f} Δ={d:+.4f} p={p:.3f}", flush=True)

        # incremental save
        pd.DataFrame(rows).to_csv(PHASE5_TABLE_DIR / "attention_compare.csv",
                                   index=False, encoding="utf-8-sig")
        pd.DataFrame(paired).to_csv(PHASE5_TABLE_DIR / "attention_paired.csv",
                                     index=False, encoding="utf-8-sig")

    cmp_df = pd.DataFrame(rows)
    pair_df = pd.DataFrame(paired)
    print(f"[5C] saved compare ({len(cmp_df)} rows), paired ({len(pair_df)} rows)")
    if not cmp_df.empty:
        agg = (cmp_df.groupby("model").agg(macro_f1=("macro_f1_mean", "mean"),
                                            n_panels=("combo_id", "nunique"))
               .reset_index().sort_values("macro_f1", ascending=False))
        print("[5C] avg macro_F1 across panels:")
        print(agg.to_string(index=False))


if __name__ == "__main__":
    main()
