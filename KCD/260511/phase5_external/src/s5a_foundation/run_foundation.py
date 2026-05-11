"""Phase 5A — Foundation TS models zero-shot.

전략:
  1. raw weekly로부터 각 store의 sales_card 시계열 context 추출 (≤78주)
  2. Chronos-T5-small (zero-shot) 로 horizon 주 forecast
     - 차후 TimesFM, Moirai 추가
  3. forecast → slope_norm → ±0.5σ bucket → macro_F1 (3-fold paired vs RF)

phase5 conda env 필수.

Outputs:
  outputs/tables/foundation_zeroshot_compare.csv
  outputs/tables/foundation_zeroshot_paired.csv
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import torch

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.paths import PANELS, PHASE5_TABLE_DIR, SEED, up  # noqa: E402
from common.seq_loader import load_seq, spec_from_combo_id  # noqa: E402
from common.cv_harness import rf_baseline_folds, paired_t_test  # noqa: E402
from common.bucket_from_slope import bucket, fit_thresholds  # noqa: E402
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MAX_HISTORY = 78


def _build_context(combo_id: str):
    """returns:
       ids: array of store ids (filtered to those with history>=12)
       contexts: list of np.ndarray of variable length (history)
       y_cls: array of class indices
       horizon: int
    """
    spec = spec_from_combo_id(combo_id)
    weekly = up.load_weekly(use_cols=["public_id", "date_id", "sales_card"])
    weekly["public_id"] = weekly["public_id"].astype(str)
    weekly["date_id"] = pd.to_datetime(weekly["date_id"])

    ctx_start = spec.feature_start - pd.Timedelta(weeks=MAX_HISTORY)
    ctx_end = spec.feature_end + pd.Timedelta(days=1)
    ctx = weekly[(weekly["date_id"] >= ctx_start) & (weekly["date_id"] < ctx_end)].copy()
    ctx = ctx.sort_values(["public_id", "date_id"])

    labels = pd.read_parquet(up.label_path(combo_id))
    labels["public_id"] = labels["public_id"].astype(str)
    labels = labels[labels["outcome_3"].isin(["Decline", "Stable", "Growth"])]
    lbl_map = labels.set_index("public_id")["outcome_3"].to_dict()
    cls_idx = {"Decline": 0, "Stable": 1, "Growth": 2}

    valid = sorted(set(ctx["public_id"]) & set(labels["public_id"]))
    ctx = ctx[ctx["public_id"].isin(valid)]

    grouped = ctx.groupby("public_id")["sales_card"]
    ids = []
    contexts = []
    y_list = []
    for pid in valid:
        s = grouped.get_group(pid).to_numpy(dtype=np.float32)
        if len(s) < 12:
            continue
        ids.append(pid)
        contexts.append(s)
        y_list.append(cls_idx[lbl_map[pid]])

    horizon = int(round((spec.target_end - spec.target_start).days / 7))
    return np.array(ids), contexts, np.array(y_list, dtype=np.int64), horizon


def _slope_norm_from_forecast(fc_mat: np.ndarray) -> np.ndarray:
    """[N,H] forecast → normalized slope."""
    H = fc_mat.shape[1]
    x = np.arange(H, dtype=np.float32)
    x_c = x - x.mean()
    denom = float((x_c * x_c).sum())
    if denom < 1e-12:
        return np.zeros(fc_mat.shape[0], dtype=np.float32)
    means = fc_mat.mean(axis=1, keepdims=True)
    safe_mean = np.where(np.abs(means.squeeze()) > 1e-9, means.squeeze(), 1.0)
    y_c = fc_mat - means
    slope = (x_c * y_c).sum(axis=1) / denom
    return (slope / safe_mean).astype(np.float32)


def _bucket_3fold(slope_norm: np.ndarray, y_cls: np.ndarray) -> list[float]:
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED)
    f1s = []
    for tr, te in skf.split(np.zeros(len(y_cls)), y_cls):
        thr = fit_thresholds(slope_norm[tr], k_sigma=0.5)
        pred = bucket(slope_norm[te], thr)
        f1s.append(f1_score(y_cls[te], pred, average="macro", zero_division=0))
    return f1s


# ---------- Chronos ----------
def chronos_forecast(contexts: list[np.ndarray], horizon: int,
                      model_name: str = "amazon/chronos-bolt-small",
                      batch_size: int = 256) -> np.ndarray:
    from chronos import BaseChronosPipeline
    pipe = BaseChronosPipeline.from_pretrained(model_name, device_map=DEVICE,
                                                torch_dtype=torch.float32)
    out = np.zeros((len(contexts), horizon), dtype=np.float32)
    # chronos-bolt: pipe.predict_quantiles → returns median + quantiles
    for start in range(0, len(contexts), batch_size):
        batch = contexts[start:start + batch_size]
        tensors = [torch.tensor(c, dtype=torch.float32) for c in batch]
        try:
            qfc, mean_fc = pipe.predict_quantiles(
                context=tensors, prediction_length=horizon,
                quantile_levels=[0.5],
            )
            arr = mean_fc.numpy() if hasattr(mean_fc, "numpy") else np.asarray(mean_fc)
        except Exception as e:
            print(f"[5A chronos] batch {start} ERROR: {e}", flush=True)
            arr = np.zeros((len(batch), horizon), dtype=np.float32)
        out[start:start + len(batch)] = arr[:, :horizon]
    return out


# ---------- TimesFM ----------
def timesfm_forecast(contexts: list[np.ndarray], horizon: int) -> np.ndarray:
    import timesfm
    tfm = timesfm.TimesFm(
        hparams=timesfm.TimesFmHparams(
            backend="gpu" if DEVICE == "cuda" else "cpu",
            per_core_batch_size=32,
            horizon_len=horizon,
            input_patch_len=32,
            output_patch_len=128,
            num_layers=20,
            model_dims=1280,
        ),
        checkpoint=timesfm.TimesFmCheckpoint(huggingface_repo_id="google/timesfm-1.0-200m-pytorch"),
    )
    out = np.zeros((len(contexts), horizon), dtype=np.float32)
    # timesfm forecast_on_df 또는 forecast: List[ndarray] → List[forecast ndarray]
    # 큰 batch 한번에 — 적당히 chunking
    chunk = 256
    for start in range(0, len(contexts), chunk):
        batch = contexts[start:start + chunk]
        try:
            fc, _ = tfm.forecast(batch, freq=[0] * len(batch))
            arr = np.stack([f[:horizon] for f in fc], axis=0)
        except Exception as e:
            print(f"[5A timesfm] batch {start} ERROR: {e}", flush=True)
            arr = np.zeros((len(batch), horizon), dtype=np.float32)
        out[start:start + len(batch)] = arr.astype(np.float32)
    return out


# ---------- Moirai ----------
def moirai_forecast(contexts: list[np.ndarray], horizon: int,
                     model_name: str = "Salesforce/moirai-1.0-R-small") -> np.ndarray:
    from uni2ts.model.moirai import MoiraiForecast, MoiraiModule
    module = MoiraiModule.from_pretrained(model_name)
    model = MoiraiForecast(
        module=module, prediction_length=horizon,
        context_length=64, patch_size="auto",
        num_samples=20, target_dim=1, feat_dynamic_real_dim=0,
        past_feat_dynamic_real_dim=0,
    )
    predictor = model.create_predictor(batch_size=64, device=DEVICE)
    out = np.zeros((len(contexts), horizon), dtype=np.float32)

    # build a simple iterable dataset
    from gluonts.dataset.common import ListDataset
    ds_list = []
    for c in contexts:
        ds_list.append({"target": c.astype(np.float32),
                          "start": pd.Period("2021-01-04", freq="W")})
    ds = ListDataset(ds_list, freq="W")
    forecast_it = predictor.predict(ds)
    for i, fc in enumerate(forecast_it):
        # fc has .median (probabilistic forecast); use mean as point
        try:
            arr = fc.median[:horizon]
        except AttributeError:
            arr = fc.mean[:horizon]
        out[i] = np.asarray(arr, dtype=np.float32)
    return out


MODELS = [
    ("chronos_bolt_small", lambda ctxs, h: chronos_forecast(ctxs, h, "amazon/chronos-bolt-small")),
    ("chronos_t5_small", lambda ctxs, h: chronos_forecast(ctxs, h, "amazon/chronos-t5-small")),
    ("timesfm_200m", lambda ctxs, h: timesfm_forecast(ctxs, h)),
    ("moirai_small", lambda ctxs, h: moirai_forecast(ctxs, h, "Salesforce/moirai-1.0-R-small")),
]


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="*", default=None,
                        help="subset of model names, e.g. chronos_bolt_small timesfm_200m")
    parser.add_argument("--panels", nargs="*", default=None,
                        help="subset of combo_ids")
    args = parser.parse_args()

    sel_models = MODELS
    if args.models:
        sel_models = [m for m in MODELS if m[0] in args.models]
    sel_panels = PANELS
    if args.panels:
        sel_panels = [p for p in PANELS if p[0] in args.panels]

    rows, paired = [], []
    for combo_id, desc in sel_panels:
        print(f"[5A] === {combo_id} ===", flush=True)
        ids, ctxs, y_cls, horizon = _build_context(combo_id)
        print(f"[5A] {combo_id} {len(ids):,} stores, H={horizon}", flush=True)

        # RF baseline on the load_seq id set for paired comparison
        seq_ids, _, y_seq = load_seq(combo_id)
        if seq_ids is None:
            print(f"[5A] skip {combo_id}: load_seq failed")
            continue
        rf_f1 = rf_baseline_folds(combo_id, seq_ids, y_seq)
        rows.append({"combo_id": combo_id, "description": desc, "model": "rf_tabular",
                     "macro_f1_mean": float(np.mean(rf_f1)),
                     "macro_f1_std": float(np.std(rf_f1)),
                     "n_stores": int(len(seq_ids)), "horizon_weeks": int(horizon)})

        # align to common ids
        common = np.array(sorted(set(ids.astype(str)) & set(seq_ids.astype(str))))
        if len(common) < 500:
            print(f"[5A] skip {combo_id}: only {len(common)} common ids")
            continue
        pid_to_ctx = dict(zip(ids.astype(str), ctxs))
        pid_to_y = dict(zip(seq_ids.astype(str), y_seq))
        ctxs_use = [pid_to_ctx[pid] for pid in common]
        y_use = np.array([pid_to_y[pid] for pid in common], dtype=np.int64)

        for name, fn in sel_models:
            try:
                fc_mat = fn(ctxs_use, horizon)
                slope = _slope_norm_from_forecast(fc_mat)
                f1s = _bucket_3fold(slope, y_use)
            except Exception as e:
                print(f"[5A] {combo_id} {name} ERROR: {e}", flush=True)
                continue
            rows.append({"combo_id": combo_id, "description": desc, "model": name,
                         "macro_f1_mean": float(np.mean(f1s)),
                         "macro_f1_std": float(np.std(f1s)),
                         "n_stores": int(len(common)), "horizon_weeks": int(horizon)})
            d, t, p = paired_t_test(rf_f1, f1s)
            paired.append({"combo_id": combo_id, "model": name,
                            "delta_mean": d, "t_stat": t, "p_value": p})
            print(f"[5A] {combo_id} {name:22s} F1={np.mean(f1s):.3f} Δ={d:+.4f} p={p:.3f}", flush=True)

            pd.DataFrame(rows).to_csv(PHASE5_TABLE_DIR / "foundation_zeroshot_compare.csv",
                                       index=False, encoding="utf-8-sig")
            pd.DataFrame(paired).to_csv(PHASE5_TABLE_DIR / "foundation_zeroshot_paired.csv",
                                         index=False, encoding="utf-8-sig")

    cmp_df = pd.DataFrame(rows)
    print(f"[5A] done. rows={len(cmp_df)}")
    if not cmp_df.empty:
        agg = (cmp_df.groupby("model").agg(macro_f1=("macro_f1_mean", "mean"),
                                            n_panels=("combo_id", "nunique"))
               .reset_index().sort_values("macro_f1", ascending=False))
        print(agg.to_string(index=False))


if __name__ == "__main__":
    main()
