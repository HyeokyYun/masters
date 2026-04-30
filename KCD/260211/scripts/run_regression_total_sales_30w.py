"""
첫 30주 피처로 31주~끝 구간 총 매출(total_sales_after_30w)을 회귀 예측.
- Ridge, XGBRegressor 사용. 8:2 매장 분할, RMSE/MAE/R² 평가.
- M0: 30주 피처만, M1: 30주 피처 + 클러스터 더미(30주로 예측).

실행 전 build_30w_features_and_labels.py 를 먼저 실행해야 함 (total_sales_after_30w 컬럼 필요).
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = ROOT.parent
CONFIG_PATH = ROOT / "configs" / "prediction_30w.yaml"
DATA_PATH = ROOT / "outputs" / "tables" / "features_30w_and_labels.parquet"
TABLES_DIR = ROOT / "outputs" / "tables"
FIGURES_DIR = ROOT / "outputs" / "figures"
LOG_PATH = ROOT / "outputs" / "logs" / "run_regression_total_sales_30w.log"

CLUSTER_PATHS = [
    PROJECT_ROOT / "260204" / "outputs" / "tables" / "store_cluster_labels_K6.parquet",
    PROJECT_ROOT / "260121" / "result_csv" / "cluster_labels.csv",
]
FEATURE_COLS = [
    "avg_sales_card", "std_sales_card", "cv_sales_card",
    "max_sales", "min_sales", "max_min_ratio", "trend_slope", "total_weeks",
]
ID_COL = "public_id"
TARGET_COL = "total_sales_after_30w"
CLUSTER_COL = "cluster"


def load_config():
    try:
        import yaml
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return {"prediction": {"train_ratio": 0.8, "seed": 42}}


def load_cluster_labels():
    for path in CLUSTER_PATHS:
        if not path.exists():
            continue
        try:
            cl = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
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

    df = pd.read_parquet(DATA_PATH)
    if TARGET_COL not in df.columns:
        log(f"ERROR: Need '{TARGET_COL}'. Re-run build_30w_features_and_labels.py to generate it.")
        return

    cols = [c for c in FEATURE_COLS if c in df.columns]
    if len(cols) == 0:
        log("ERROR: No feature columns found.")
        return

    cluster_df, _ = load_cluster_labels()
    if cluster_df is not None:
        cluster_df[CLUSTER_COL] = cluster_df[CLUSTER_COL].astype(int).astype(str)
        df = df.merge(cluster_df, on=ID_COL, how="inner")
        log(f"Merged cluster labels: {len(df)} stores")

    X = df[cols].astype(float).fillna(0)
    y = df[TARGET_COL].astype(float).values

    cfg = load_config()
    pred_cfg = cfg.get("prediction", {})
    train_ratio = float(pred_cfg.get("train_ratio", 0.8))
    seed = int(pred_cfg.get("seed", 42))

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=1 - train_ratio, random_state=seed
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    train_idx = X_train.index

    def to_dummy(arr, uniq):
        out = np.zeros((len(arr), len(uniq)))
        for i, a in enumerate(arr):
            idx = np.where(uniq == a)[0]
            if len(idx):
                out[i, idx[0]] = 1.0
        return out

    results = []

    # M0: 피처만
    for name, model in [
        ("Ridge", Ridge(alpha=1.0, random_state=seed)),
        ("XGBRegressor", None),
    ]:
        if name == "XGBRegressor":
            try:
                from xgboost import XGBRegressor
                model = XGBRegressor(random_state=seed, n_estimators=100, max_depth=5)
            except ImportError:
                continue
        model.fit(X_train_s, y_train)
        pred = model.predict(X_test_s)
        rmse = np.sqrt(mean_squared_error(y_test, pred))
        mae = mean_absolute_error(y_test, pred)
        r2 = r2_score(y_test, pred)
        results.append({"spec": "M0", "model": name, "rmse": rmse, "mae": mae, "r2": r2})
        log(f"M0 {name} — RMSE: {rmse:.0f}, MAE: {mae:.0f}, R²: {r2:.4f}")

    # M1: 피처 + 클러스터 더미
    if cluster_df is not None and CLUSTER_COL in df.columns:
        from sklearn.linear_model import LogisticRegression
        y_cluster_train = df.loc[train_idx, CLUSTER_COL].values
        clf_cluster = LogisticRegression(max_iter=2000, random_state=seed, class_weight="balanced")
        clf_cluster.fit(X_train_s, y_cluster_train)
        cluster_pred_train = clf_cluster.predict(X_train_s)
        cluster_pred_test = clf_cluster.predict(X_test_s)
        u = np.unique(np.concatenate([cluster_pred_train, cluster_pred_test]))
        cluster_dummy_train = to_dummy(cluster_pred_train, u)
        cluster_dummy_test = to_dummy(cluster_pred_test, u)
        X_train_m1 = np.hstack([X_train_s, cluster_dummy_train])
        X_test_m1 = np.hstack([X_test_s, cluster_dummy_test])

        for name, model in [
            ("Ridge", Ridge(alpha=1.0, random_state=seed)),
            ("XGBRegressor", None),
        ]:
            if name == "XGBRegressor":
                try:
                    from xgboost import XGBRegressor
                    model = XGBRegressor(random_state=seed, n_estimators=100, max_depth=5)
                except ImportError:
                    continue
            model.fit(X_train_m1, y_train)
            pred = model.predict(X_test_m1)
            rmse = np.sqrt(mean_squared_error(y_test, pred))
            mae = mean_absolute_error(y_test, pred)
            r2 = r2_score(y_test, pred)
            results.append({"spec": "M1", "model": name, "rmse": rmse, "mae": mae, "r2": r2})
            log(f"M1 {name} — RMSE: {rmse:.0f}, MAE: {mae:.0f}, R²: {r2:.4f}")

    res_df = pd.DataFrame(results)
    out_csv = TABLES_DIR / "regression_total_sales_30w_results.csv"
    res_df.to_csv(out_csv, index=False)
    log(f"Saved {out_csv}")

    if len(res_df) > 0 and "r2" in res_df.columns:
        fig, ax = plt.subplots()
        specs = sorted(res_df["spec"].unique())
        x = np.arange(len(specs))
        w = 0.35
        for i, mod in enumerate(res_df["model"].unique()):
            sub = res_df[res_df["model"] == mod].set_index("spec").reindex(specs).fillna(0)
            off = -w / 2 + (i + 0.5) * w
            ax.bar(x + off, sub["r2"].values, w, label=mod, alpha=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels(specs)
        ax.set_ylabel("R²")
        ax.set_title("Regression (30w → total_sales_after_30w): R² by spec & model")
        ax.legend()
        ax.axhline(y=0, color="gray", linestyle="--")
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "regression_total_sales_30w_r2.png", bbox_inches="tight")
        plt.close(fig)
        log(f"Saved {FIGURES_DIR / 'regression_total_sales_30w_r2.png'}")


if __name__ == "__main__":
    main()
