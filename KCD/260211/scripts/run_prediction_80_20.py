"""
매장 기준 8:2 분할 후, 80%로 학습·20%로 성장/하락 예측 평가.
- M0: 첫 30주 피처만 사용.
- M1: 첫 30주 피처 + (첫 30주로 예측한) 클러스터 더미.
- 테스트 시 클러스터는 30주 기반 예측값만 사용(데이터 누수 방지).

Run from 260211: python scripts/run_prediction_80_20.py
실행 전 build_30w_features_and_labels.py 를 먼저 실행해야 함.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from sklearn.preprocessing import StandardScaler, OneHotEncoder

ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = ROOT.parent  # 26-1
CONFIG_PATH = ROOT / "configs" / "prediction_30w.yaml"
DATA_PATH = ROOT / "outputs" / "tables" / "features_30w_and_labels.parquet"
TABLES_DIR = ROOT / "outputs" / "tables"
FIGURES_DIR = ROOT / "outputs" / "figures"
LOG_PATH = ROOT / "outputs" / "logs" / "run_prediction_80_20.log"

# 클러스터 라벨 후보 (260204 K-Shape K6 우선, 없으면 260121)
CLUSTER_PATHS = [
    PROJECT_ROOT / "260204" / "outputs" / "tables" / "store_cluster_labels_K6.parquet",
    PROJECT_ROOT / "260121" / "result_csv" / "cluster_labels.csv",
]

FEATURE_COLS = [
    "avg_sales_card", "std_sales_card", "cv_sales_card",
    "max_sales", "min_sales", "max_min_ratio", "trend_slope", "total_weeks",
]
META_CAT_COLS = ["sigungu", "dong", "depth_1", "depth_2", "depth_3"]
ID_COL = "public_id"
TARGET_COL = "growth"
CLUSTER_COL = "cluster"


def get_xgb_device():
    """CUDA 사용 가능하면 'cuda', 아니면 None (CPU). torch 또는 CUDA_VISIBLE_DEVICES로 판단."""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    return None


def load_config():
    try:
        import yaml
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return {
            "prediction": {"train_ratio": 0.8, "seed": 42},
        }


def load_cluster_labels():
    """클러스터 라벨 로드. (DataFrame, path) 또는 (None, None)."""
    for path in CLUSTER_PATHS:
        if not path.exists():
            continue
        try:
            if path.suffix == ".parquet":
                cl = pd.read_parquet(path)
            else:
                cl = pd.read_csv(path)
            if CLUSTER_COL not in cl.columns:
                for c in cl.columns:
                    if c != ID_COL and str(cl[c].dtype).startswith(("int", "float")):
                        cl = cl.rename(columns={c: CLUSTER_COL})
                        break
            if ID_COL in cl.columns and CLUSTER_COL in cl.columns:
                return cl[[ID_COL, CLUSTER_COL]].drop_duplicates(), path
        except Exception:
            continue
    return None, None


def main():
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    def log(msg: str):
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    if not DATA_PATH.exists():
        log(f"ERROR: Run build_30w_features_and_labels.py first. Not found: {DATA_PATH}")
        return

    cfg = load_config()
    pred_cfg = cfg.get("prediction", {})
    train_ratio = float(pred_cfg.get("train_ratio", 0.8))
    seed = int(pred_cfg.get("seed", 42))

    df = pd.read_parquet(DATA_PATH)
    cols = [c for c in FEATURE_COLS if c in df.columns]
    if len(cols) == 0:
        log("ERROR: No feature columns found.")
        return
    if ID_COL not in df.columns or TARGET_COL not in df.columns:
        log(f"ERROR: Need columns {ID_COL}, {TARGET_COL}. Got: {df.columns.tolist()}")
        return

    # 클러스터 병합 (있으면 M1 수행)
    cluster_df, cluster_path = load_cluster_labels()
    if cluster_df is not None:
        cluster_df[CLUSTER_COL] = cluster_df[CLUSTER_COL].astype(int).astype(str)
        df = df.merge(cluster_df, on=ID_COL, how="inner")
        log(f"Merged cluster labels: {len(df)} stores (from {cluster_path})")
    else:
        log("No cluster labels found; running M0 only.")

    X = df[cols].astype(float).fillna(0)
    y = df[TARGET_COL].astype(int)

    # 매장 기준 8:2 분할
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=1 - train_ratio,
        random_state=seed,
        stratify=y,
    )

    log(f"Train stores: {len(X_train)}, Test stores: {len(X_test)}")
    xgb_device = get_xgb_device()
    if xgb_device:
        log(f"XGBoost: using device={xgb_device} (CUDA)")

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    results = []
    train_idx = X_train.index
    test_idx = X_test.index
    # 클래스 불균형 대응 가중치 (하락 소수 클래스 반영)
    neg = (y_train == 0).sum()
    pos = (y_train == 1).sum()
    scale_pos_weight = neg / max(pos, 1)

    def run_spec(spec_name, X_tr, X_te):
        """LR·XGB 학습·평가 (class_weight balanced로 예측률 개선)."""
        lr = LogisticRegression(max_iter=2000, random_state=seed, class_weight="balanced")
        lr.fit(X_tr, y_train)
        pred_lr = lr.predict(X_te)
        acc = accuracy_score(y_test, pred_lr)
        f1 = f1_score(y_test, pred_lr, zero_division=0)
        results.append({"spec": spec_name, "model": "LogisticRegression", "accuracy": acc, "f1": f1})
        log(f"{spec_name} LogisticRegression — Acc: {acc:.4f}, F1: {f1:.4f}")

        try:
            from xgboost import XGBClassifier
            xgb_kw = dict(random_state=seed, eval_metric="logloss", scale_pos_weight=scale_pos_weight)
            if xgb_device:
                xgb_kw["device"] = xgb_device
            xgb = XGBClassifier(**xgb_kw)
            xgb.fit(X_tr, y_train)
            pred_xgb = xgb.predict(X_te)
            acc = accuracy_score(y_test, pred_xgb)
            f1 = f1_score(y_test, pred_xgb, zero_division=0)
            results.append({"spec": spec_name, "model": "XGBClassifier", "accuracy": acc, "f1": f1})
            log(f"{spec_name} XGBClassifier — Acc: {acc:.4f}, F1: {f1:.4f}")
        except ImportError:
            pass

    # M0: 첫 30주 피처만 (260204 ablation과 동일 스펙명)
    run_spec("M0", X_train_s, X_test_s)

    # M2: M0 + 지역·업종(메타) — 클러스터 없이 메타만 (260204 M2에 대응)
    meta_cat = [c for c in META_CAT_COLS if c in df.columns]
    X_train_m2 = X_test_m2 = None
    if meta_cat:
        df_meta = df[meta_cat].fillna("Unknown").astype(str)
        enc = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        meta_train = enc.fit_transform(df_meta.loc[train_idx])
        meta_test = enc.transform(df_meta.loc[test_idx])
        X_train_m2 = np.hstack([X_train_s, meta_train])
        X_test_m2 = np.hstack([X_test_s, meta_test])
        run_spec("M2", X_train_m2, X_test_m2)
        log(f"M2: M0 + {len(meta_cat)} meta cat cols → {meta_train.shape[1]} dummies")

    # M1: M0 + 클러스터 더미 (30주로 예측한 클러스터만 사용, 누수 없음)
    cluster_dummy_train = cluster_dummy_test = None
    if cluster_df is not None and CLUSTER_COL in df.columns:
        y_cluster_train = df.loc[train_idx, CLUSTER_COL].values
        clf_cluster = LogisticRegression(max_iter=2000, random_state=seed, class_weight="balanced")
        clf_cluster.fit(X_train_s, y_cluster_train)
        cluster_pred_train = clf_cluster.predict(X_train_s)
        cluster_pred_test = clf_cluster.predict(X_test_s)
        u = np.unique(np.concatenate([cluster_pred_train, cluster_pred_test]))
        def to_dummy(arr):
            out = np.zeros((len(arr), len(u)))
            for i, a in enumerate(arr):
                idx = np.where(u == a)[0]
                if len(idx): out[i, idx[0]] = 1.0
            return out
        cluster_dummy_train = to_dummy(cluster_pred_train)
        cluster_dummy_test = to_dummy(cluster_pred_test)
        X_train_m1 = np.hstack([X_train_s, cluster_dummy_train])
        X_test_m1 = np.hstack([X_test_s, cluster_dummy_test])
        run_spec("M1", X_train_m1, X_test_m1)
        log("M1: M0 + cluster (predicted from first-30w only, no leakage).")

        # M3: M1 + 메타 (클러스터 + 메타, 260204 M3에 대응)
        if meta_cat is not None and len(meta_cat) > 0:
            X_train_m3 = np.hstack([X_train_m1, meta_train])
            X_test_m3 = np.hstack([X_test_m1, meta_test])
            run_spec("M3", X_train_m3, X_test_m3)
            log("M3: M1 + meta.")

    res_df = pd.DataFrame(results)
    res_df.to_csv(TABLES_DIR / "prediction_80_20_results.csv", index=False)
    log(f"Saved {TABLES_DIR / 'prediction_80_20_results.csv'}")

    # Figure: M0 / M1 / M2 / M3 비교 (모델별·스펙별)
    models = res_df["model"].unique().tolist()
    n_models = len(models)
    specs = sorted(res_df["spec"].unique().tolist())
    n_specs = max(len(specs), 1)
    w = (0.8 / n_specs) * 0.9
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, metric in zip(axes, ["accuracy", "f1"]):
        x = np.arange(n_models)
        for i, spec in enumerate(specs):
            sub = res_df[res_df["spec"] == spec].set_index("model").reindex(models)
            vals = sub[metric].values
            if np.any(np.isnan(vals)):
                vals = np.nan_to_num(vals, nan=0.0)
            off = -0.4 + (i + 0.5) * (0.8 / n_specs)
            ax.bar(x + off, vals, w, label=spec, alpha=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels(models)
        ax.set_ylabel(metric)
        ax.set_title(metric.capitalize())
        ax.legend()
        ax.set_ylim(0, 1.05)
    fig.suptitle("성장/하락 예측: M0~M3 spec별 Accuracy·F1 (balanced weight)")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "prediction_80_20_M0_vs_M1.png", bbox_inches="tight")
    plt.close(fig)
    log(f"Saved {FIGURES_DIR / 'prediction_80_20_M0_vs_M1.png'}")


if __name__ == "__main__":
    main()
