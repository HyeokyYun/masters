"""3-fold StratifiedKFold harness — step06와 동일.

핵심 함수:
  - rf_baseline_folds(combo_id, sample_ids, y): RF tabular 56-feature를 동일
    fold split로 재학습해 fold별 macro_F1 list 반환. paired delta 계산용.
  - seq_train_eval(make_model, X, y, ...): step06의 _train_eval 일반화.
  - paired_t_test(rf_f1s, model_f1s): t_stat, p_value.
  - write_compare_paired(rows, paired_rows, base_name): CSV 두 개 저장.
"""
from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold
from torch.utils.data import DataLoader, TensorDataset

from .paths import PHASE5_TABLE_DIR, SEED, up

def _safe_device() -> str:
    """현재 torch가 sm_61 GPU를 지원 못 하면 CPU로 fallback."""
    if not torch.cuda.is_available():
        return "cpu"
    try:
        cap = torch.cuda.get_device_capability(0)
    except Exception:
        return "cpu"
    supported = getattr(torch.cuda, "get_arch_list", lambda: [])()
    arch = f"sm_{cap[0]}{cap[1]}"
    if supported and arch not in supported:
        return "cpu"
    # smoke test — sm_61 같은 미지원 GPU는 여기서 잡힘
    try:
        torch.randn(2, 3, device="cuda:0").sum().item()
    except Exception:
        return "cpu"
    return "cuda"


DEVICE = _safe_device()


def rf_baseline_folds(combo_id: str, sample_ids: np.ndarray, y: np.ndarray) -> list[float]:
    """step06 _rf_baseline와 동일 protocol — RF 120/12/20, class_weight=balanced."""
    feats = pd.read_parquet(up.feature_path(combo_id))
    feats["public_id"] = feats["public_id"].astype(str)
    df = pd.DataFrame({"public_id": sample_ids}).merge(feats, on="public_id", how="left")
    base_cols = [c for c in feats.columns if c != "public_id"]
    X = df[base_cols].fillna(0).reset_index(drop=True)
    y_s = pd.Series(y).reset_index(drop=True)
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED)
    f1s = []
    for tr, te in skf.split(X, y_s):
        m = RandomForestClassifier(
            n_estimators=120, max_depth=12, min_samples_leaf=20,
            n_jobs=-1, random_state=SEED, class_weight="balanced",
        )
        m.fit(X.iloc[tr], y_s.iloc[tr])
        pred = m.predict(X.iloc[te])
        f1s.append(f1_score(y_s.iloc[te], pred, average="macro", zero_division=0))
    return f1s


def seq_train_eval(
    make_model: Callable[[int, int], nn.Module],
    X: np.ndarray,
    y: np.ndarray,
    *,
    epochs: int = 8,
    patience: int = 3,
    lr: float = 2e-3,
    weight_decay: float = 1e-4,
    batch_size: int = 2048,
    loss_fn: Callable | None = None,
) -> list[float]:
    """3-fold per-fold macro_F1. step06와 동일."""
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED)
    counts = np.bincount(y, minlength=3).astype(float)
    weights = 1.0 / np.maximum(counts, 1.0)
    weights = weights / weights.sum() * 3.0
    T, C = X.shape[1], X.shape[2]
    f1s = []
    for tr, te in skf.split(np.zeros(len(y)), y):
        torch.manual_seed(SEED)
        model = make_model(T, C).to(DEVICE)
        opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
        if loss_fn is None:
            crit = nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float32, device=DEVICE))
        else:
            crit = loss_fn
        Xtr = torch.from_numpy(X[tr]); ytr = torch.from_numpy(y[tr])
        Xte = torch.from_numpy(X[te]); yte = torch.from_numpy(y[te])
        loader = DataLoader(TensorDataset(Xtr, ytr), batch_size=batch_size, shuffle=True, drop_last=False)
        best_f1 = -1.0
        bad = 0
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
                for i in range(0, len(Xte), 1024):
                    preds.append(model(Xte[i:i+1024].to(DEVICE)).argmax(1).cpu())
                pred = torch.cat(preds).numpy()
            f1 = f1_score(yte.numpy(), pred, average="macro", zero_division=0)
            if f1 > best_f1 + 1e-4:
                best_f1 = f1; bad = 0
            else:
                bad += 1
                if bad >= patience:
                    break
        f1s.append(best_f1)
    return f1s


def paired_t_test(rf_f1s: list[float], model_f1s: list[float]) -> tuple[float, float, float]:
    """returns (delta_mean, t_stat, p_value). std(b-a)==0 이면 (Δ, nan, nan)."""
    a = np.array(rf_f1s, dtype=float)
    b = np.array(model_f1s, dtype=float)
    delta = float((b - a).mean())
    if np.std(b - a) < 1e-12:
        return delta, float("nan"), float("nan")
    t, p = stats.ttest_rel(b, a)
    return delta, float(t), float(p)


def write_compare_paired(rows: list[dict], paired_rows: list[dict], base_name: str) -> tuple:
    cmp_df = pd.DataFrame(rows)
    pair_df = pd.DataFrame(paired_rows)
    cmp_path = PHASE5_TABLE_DIR / f"{base_name}_compare.csv"
    pair_path = PHASE5_TABLE_DIR / f"{base_name}_paired.csv"
    cmp_df.to_csv(cmp_path, index=False, encoding="utf-8-sig")
    pair_df.to_csv(pair_path, index=False, encoding="utf-8-sig")
    return cmp_path, pair_path
