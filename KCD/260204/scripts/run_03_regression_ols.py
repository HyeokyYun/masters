"""
FEATURE-CSV pipeline (track A) — OLS on growth_rate.
Run from 260204: python scripts/run_03_regression_ols.py
Self-contained: no project src imports.
"""
from pathlib import Path
import yaml
import numpy as np
import pandas as pd
import statsmodels.api as sm
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent

DATA_CLEAN = ROOT / "outputs" / "data_features_clean.parquet"
LOG_PATH = ROOT / "outputs" / "logs" / "run_03_regression_ols.log"
OUT_CSV = ROOT / "outputs" / "tables" / "ols_growth_rate.csv"


def load_config():
    with open(ROOT / "configs" / "base.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    def log(msg: str):
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    if not DATA_CLEAN.exists():
        log(f"ERROR: Run run_01 first. Not found: {DATA_CLEAN}")
        return

    cfg = load_config()
    data_cfg = cfg.get("data", {})
    id_col = data_cfg.get("id_col_store", "public_id")
    cluster_col = data_cfg.get("cluster_col", "cluster")
    categoricals = cfg.get("categoricals", [])

    df = pd.read_parquet(DATA_CLEAN)
    y_col = "growth_rate"
    if y_col not in df.columns:
        log(f"ERROR: '{y_col}' not in data.")
        return

    exclude = {id_col, cluster_col, y_col}
    feature_cols = [c for c in df.columns if c not in exclude]
    cat_in_df = [c for c in categoricals if c in df.columns and c in feature_cols]
    num_cols = [c for c in feature_cols if c not in cat_in_df]

    use = df[[y_col] + feature_cols].dropna()
    if len(use) < 10:
        log("ERROR: Too few rows after dropna.")
        return

    y = np.asarray(use[y_col], dtype=float)
    X_num = use[num_cols].astype(float)
    if cat_in_df:
        dummies = pd.get_dummies(use[cat_in_df], drop_first=True, dtype=float)
        X = pd.concat([X_num, dummies], axis=1)
    else:
        X = X_num.copy()
    X_dense = np.asarray(X, dtype=float)
    X_const = sm.add_constant(X_dense, has_constant="add")

    res = sm.OLS(y, X_const).fit()

    out_df = pd.DataFrame({
        "variable": ["const"] + X.columns.tolist(),
        "coef": res.params,
        "std_err": res.bse,
        "t": res.tvalues,
        "pvalue": res.pvalues,
    })
    out_df = out_df.sort_values("pvalue").reset_index(drop=True)
    out_df.to_csv(OUT_CSV, index=False)
    log(f"Saved {OUT_CSV}")

    log(f"R2 = {res.rsquared:.6f}")


if __name__ == "__main__":
    main()
