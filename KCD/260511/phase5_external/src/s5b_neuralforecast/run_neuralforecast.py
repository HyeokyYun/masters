"""Phase 5B — Stock SOTA via Nixtla neuralforecast.

모델 7종: TFT, NBEATS, NHITS, PatchTST, DLinear, Informer, Autoformer.

전략:
  1. raw weekly에서 각 store의 sales_card 시계열 추출
     - context: max_history_weeks(예: 52주) before feature_end
     - target window: target_start ~ target_end
  2. neuralforecast.cross_validation 으로 fit + forecast
  3. forecast → slope_norm → ±0.5σ bucket (train slope σ로 thresholds 계산)
  4. y_pred vs y_true (G/S/D) → macro_F1
  5. 동일 store 집합에서 RF baseline 3-fold rerun → paired delta

필수: phase5 conda env (torch 2.3.1+cu118, neuralforecast 1.7.5).

Outputs:
  outputs/tables/neuralforecast_compare.csv
  outputs/tables/neuralforecast_paired.csv
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.paths import PANELS, PHASE5_TABLE_DIR, SEED, up  # noqa: E402
from common.seq_loader import load_seq, spec_from_combo_id  # noqa: E402
from common.cv_harness import rf_baseline_folds, paired_t_test  # noqa: E402
from common.bucket_from_slope import bucket, fit_thresholds, forecast_slope  # noqa: E402

# neuralforecast imports (heavy)
from neuralforecast import NeuralForecast
from neuralforecast.models import (
    NBEATS, NHITS, TFT, PatchTST, DLinear, Informer, Autoformer,
)
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold

MAX_HISTORY_WEEKS = 78


def _build_long_df(combo_id: str) -> tuple[pd.DataFrame, dict, np.ndarray, np.ndarray]:
    """Returns:
      df_long: 'unique_id', 'ds', 'y' (neuralforecast format) — feature segment only
      spec dict
      ids (np.ndarray of store id strings, sorted)
      y_cls (np.ndarray of class index aligned to ids)
    """
    spec = spec_from_combo_id(combo_id)
    weekly = up.load_weekly(use_cols=["public_id", "date_id", "sales_card"])
    weekly["public_id"] = weekly["public_id"].astype(str)
    weekly["date_id"] = pd.to_datetime(weekly["date_id"])

    # context window: feature window 시작 전 MAX_HISTORY_WEEKS 부터 feature_end 까지
    ctx_start = spec.feature_start - pd.Timedelta(weeks=MAX_HISTORY_WEEKS)
    ctx_end = spec.feature_end + pd.Timedelta(days=1)  # inclusive
    ctx = weekly[(weekly["date_id"] >= ctx_start) & (weekly["date_id"] < ctx_end)].copy()
    ctx = ctx.sort_values(["public_id", "date_id"])

    # labels
    labels = pd.read_parquet(up.label_path(combo_id))
    labels["public_id"] = labels["public_id"].astype(str)
    labels = labels[labels["outcome_3"].isin(["Decline", "Stable", "Growth"])]
    lbl_map = labels.set_index("public_id")["outcome_3"].to_dict()
    cls_idx = {"Decline": 0, "Stable": 1, "Growth": 2}

    valid_ids = sorted(set(ctx["public_id"]) & set(labels["public_id"]))
    ctx = ctx[ctx["public_id"].isin(valid_ids)]
    # require ≥ 12 weeks history
    counts = ctx.groupby("public_id").size()
    keep = counts[counts >= 12].index
    ctx = ctx[ctx["public_id"].isin(keep)]
    valid_ids = sorted(ctx["public_id"].unique())

    df_long = ctx.rename(columns={"public_id": "unique_id", "date_id": "ds", "sales_card": "y"})
    df_long = df_long[["unique_id", "ds", "y"]].reset_index(drop=True)
    df_long["y"] = df_long["y"].astype("float32")
    # NeuralForecast 는 NaN 절대 불허 → ffill→bfill→0 fallback
    df_long = (df_long.sort_values(["unique_id", "ds"])
                       .reset_index(drop=True))
    df_long["y"] = (df_long.groupby("unique_id")["y"]
                          .transform(lambda s: s.ffill().bfill().fillna(0.0)))
    df_long["y"] = df_long["y"].fillna(0.0).astype("float32")

    y_cls = np.array([cls_idx[lbl_map[pid]] for pid in valid_ids], dtype=np.int64)
    horizon = int(round((spec.target_end - spec.target_start).days / 7))
    spec_dict = {
        "feature_start": spec.feature_start, "feature_end": spec.feature_end,
        "target_start": spec.target_start, "target_end": spec.target_end,
        "horizon_weeks": horizon,
    }
    return df_long, spec_dict, np.array(valid_ids), y_cls


def _train_forecast(df_long: pd.DataFrame, horizon: int, model_cls,
                     model_kwargs: dict) -> pd.DataFrame:
    """Single-shot fit on entire history, forecast next `horizon` weeks per series."""
    # input_size: feature 윈도우만 사용 (13~31주). 너무 짧은 store도 있어 padding 허용.
    model = model_cls(h=horizon, input_size=max(8, horizon),
                      max_steps=200, scaler_type="standard",
                      start_padding_enabled=True,
                      random_seed=SEED, **model_kwargs)
    nf = NeuralForecast(models=[model], freq="W")
    nf.fit(df=df_long, val_size=0)
    fc = nf.predict()
    return fc  # columns: unique_id, ds, model_name


def _forecast_to_slope(fc: pd.DataFrame, model_col: str, ids: np.ndarray) -> np.ndarray:
    """forecast df → per-store normalized slope array (aligned to ids)."""
    pv = fc.pivot_table(index="unique_id", columns="ds", values=model_col, aggfunc="first")
    pv = pv.reindex(ids.astype(str))
    arr = pv.to_numpy(dtype=np.float32)
    # forecast 의 평균을 scale로 사용
    scale = np.nanmean(arr, axis=1)
    safe = np.where(np.abs(scale) > 1e-9, scale, 1.0)
    H = arr.shape[1]
    x = np.arange(H, dtype=np.float32)
    x_c = x - x.mean()
    denom = (x_c * x_c).sum()
    if denom < 1e-12:
        return np.zeros(len(ids), dtype=np.float32)
    means = np.nanmean(arr, axis=1, keepdims=True)
    y_c = arr - means
    slope = np.nansum(x_c * y_c, axis=1) / denom
    return (slope / safe).astype(np.float32)


def _bucket_3fold(slope_norm: np.ndarray, y_cls: np.ndarray) -> list[float]:
    """For paired comparison with RF: 3-fold StratifiedKFold,
    각 fold의 train으로 threshold 산출 → test predict → F1."""
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED)
    f1s = []
    for tr, te in skf.split(np.zeros(len(y_cls)), y_cls):
        thr = fit_thresholds(slope_norm[tr], k_sigma=0.5)
        pred = bucket(slope_norm[te], thr)
        f1s.append(f1_score(y_cls[te], pred, average="macro", zero_division=0))
    return f1s


MODELS = [
    ("nbeats", NBEATS, {}),
    ("nhits", NHITS, {}),
    ("dlinear", DLinear, {}),
    ("patchtst", PatchTST, {}),
    ("tft", TFT, {}),
    ("informer", Informer, {"hidden_size": 64}),
    ("autoformer", Autoformer, {"hidden_size": 64}),
]


def main():
    rows, paired = [], []
    for combo_id, desc in PANELS:
        print(f"[5B] === {combo_id} ===", flush=True)
        df_long, spec, ids, y_cls = _build_long_df(combo_id)
        horizon = spec["horizon_weeks"]
        print(f"[5B] {combo_id} long df: {len(df_long):,} rows, {len(ids):,} stores, H={horizon}",
              flush=True)

        # RF baseline (same store id set; use load_seq to align with step06's filter)
        # NOTE: ids from _build_long_df can differ slightly from load_seq filter (n>=500).
        # Re-run RF on the load_seq id set for direct comparability.
        seq_ids, _, y_seq = load_seq(combo_id)
        if seq_ids is None:
            print(f"[5B] skip {combo_id}: load_seq failed")
            continue
        rf_f1 = rf_baseline_folds(combo_id, seq_ids, y_seq)
        rows.append({
            "combo_id": combo_id, "description": desc, "model": "rf_tabular",
            "macro_f1_mean": float(np.mean(rf_f1)),
            "macro_f1_std": float(np.std(rf_f1)),
            "n_stores": int(len(seq_ids)), "horizon_weeks": int(horizon),
        })
        print(f"[5B] {combo_id} rf_tabular F1={np.mean(rf_f1):.3f} (paired-RF reference)",
              flush=True)

        # forecast 결과에서 slope만 추출 → 같은 ids subset에 맞춰 align
        # neuralforecast 사용한 ids ∩ seq_ids 로 평가
        common_ids = np.array(sorted(set(ids.astype(str)) & set(seq_ids.astype(str))))
        if len(common_ids) < 500:
            print(f"[5B] skip {combo_id}: too few common ids ({len(common_ids)})")
            continue
        # filter df_long to common ids
        df_use = df_long[df_long["unique_id"].astype(str).isin(common_ids)].copy()
        # align y_seq → common_ids
        seq_pid_to_y = dict(zip(seq_ids.astype(str), y_seq))
        y_common = np.array([seq_pid_to_y[pid] for pid in common_ids], dtype=np.int64)

        for name, cls, kwargs in MODELS:
            try:
                fc = _train_forecast(df_use, horizon, cls, kwargs)
                model_col = name if name in fc.columns else cls.__name__
                slope = _forecast_to_slope(fc, model_col, common_ids)
                f1s = _bucket_3fold(slope, y_common)
            except Exception as e:
                print(f"[5B] {combo_id} {name} ERROR: {e}", flush=True)
                continue
            rows.append({
                "combo_id": combo_id, "description": desc, "model": name,
                "macro_f1_mean": float(np.mean(f1s)),
                "macro_f1_std": float(np.std(f1s)),
                "n_stores": int(len(common_ids)), "horizon_weeks": int(horizon),
            })
            d, t, p = paired_t_test(rf_f1, f1s)
            paired.append({"combo_id": combo_id, "model": name,
                            "delta_mean": d, "t_stat": t, "p_value": p})
            print(f"[5B] {combo_id} {name:10s} F1={np.mean(f1s):.3f} Δ={d:+.4f} p={p:.3f}", flush=True)

            pd.DataFrame(rows).to_csv(PHASE5_TABLE_DIR / "neuralforecast_compare.csv",
                                       index=False, encoding="utf-8-sig")
            pd.DataFrame(paired).to_csv(PHASE5_TABLE_DIR / "neuralforecast_paired.csv",
                                         index=False, encoding="utf-8-sig")

    cmp_df = pd.DataFrame(rows)
    print(f"[5B] done. compare={len(cmp_df)} paired={len(paired)}")
    if not cmp_df.empty:
        agg = (cmp_df.groupby("model").agg(macro_f1=("macro_f1_mean", "mean"),
                                            n_panels=("combo_id", "nunique"))
               .reset_index().sort_values("macro_f1", ascending=False))
        print("[5B] avg macro_F1 across panels:")
        print(agg.to_string(index=False))


if __name__ == "__main__":
    main()
