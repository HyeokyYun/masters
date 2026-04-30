"""
Step 3a: Econometric Regression — Model 1 (기본) / Model 2 (+통제) / Model 3 (+고정효과).
Output: regression_tables.csv (논문용), regression_tables_formatted.csv (학회 표 형식).

Run from 260223: python 03_econometrics/run_step3_regression.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime
from scipy import stats as scipy_stats

try:
    import statsmodels.api as sm
    from statsmodels.discrete.discrete_model import Logit
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "configs" / "pipeline.yaml"
OUT_DIR = ROOT / "outputs" / "tables"
FIG_DIR = ROOT / "outputs" / "figures"
LOG_DIR = ROOT / "outputs" / "logs"

try:
    import yaml
    def load_config():
        with open(CONFIG, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
except ImportError:
    def load_config():
        return {"data": {"id_col": "public_id"}, "regression": {"target_binary": "growth_type", "target_continuous": "growth_rate", "main_x": ["new_customer_ratio", "cv_sales_card"], "controls": ["business_age_months", "business_density", "business_square_size"], "fixed_effects": ["sigungu", "depth_2"], "min_samples": 1000}}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "run_step3_regression.log"

    def log(msg: str):
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    cfg = load_config()
    reg_cfg = cfg.get("regression", {})
    id_col = cfg.get("data", {}).get("id_col", "public_id")

    # Load merged base + udx (or base only)
    base_path = OUT_DIR / "df_base_features.parquet"
    udx_path = OUT_DIR / "df_udx_labels.parquet"
    if not base_path.exists():
        log("ERROR: Run Step 1 first. df_base_features.parquet not found.")
        return
    df = pd.read_parquet(base_path)
    if udx_path.exists():
        udx = pd.read_parquet(udx_path)
        merge_col = id_col if id_col in udx.columns else "public_id"
        df = df.merge(udx[[c for c in udx.columns if c in [merge_col, "cluster", "final_code", "Pattern_label", "slope_P1", "slope_P2", "inflection_week"]]], on=merge_col, how="left")
        log(f"Merged df_udx_labels: {len(df)} rows")

    # Y: binary growth_type (1=성장, 0=쇠퇴) and continuous growth_rate
    if "growth_type" not in df.columns and "growth_rate" in df.columns:
        df["growth_type"] = (df["growth_rate"] >= 1.0).astype(int)
    y_bin = reg_cfg.get("target_binary", "growth_type")
    y_cont = reg_cfg.get("target_continuous", "growth_rate")
    main_x = reg_cfg.get("main_x", ["new_customer_ratio", "cv_sales_card"])
    controls = reg_cfg.get("controls", ["business_age_months", "business_density", "business_square_size"])
    fe_cols = reg_cfg.get("fixed_effects", ["sigungu", "depth_2"])
    min_samples = reg_cfg.get("min_samples", 1000)

    # Use only rows with valid Y and key X
    use = df.dropna(subset=[y_bin, y_cont] + main_x).copy()
    if len(use) < min_samples:
        log(f"WARNING: Only {len(use)} rows after dropna (min={min_samples}). Proceeding anyway.")
    log(f"Analysis sample: {len(use)} stores. growth_type 1={use[y_bin].sum()}, 0={(use[y_bin]==0).sum()}")

    results_ols = []
    results_logit = []

    for model_name, add_controls, add_fe in [
        ("Model1", False, False),
        ("Model2", True, False),
        ("Model3", True, True),
    ]:
        X_cols = list(main_x)
        if add_controls:
            X_cols += [c for c in controls if c in use.columns]
        if add_fe:
            for c in fe_cols:
                if c in use.columns:
                    X_cols.append(c)

        # Numeric only for design matrix
        num_cols = [c for c in X_cols if use[c].dtype in ["float64", "int64"] or (use[c].dtype == "object" and c not in fe_cols)]
        cat_cols = [c for c in X_cols if c in fe_cols and c in use.columns]
        use_sub = use[[y_bin, y_cont] + num_cols + cat_cols].dropna()
        if len(use_sub) < 100:
            log(f"Skip {model_name}: too few rows after dropna")
            continue

        y_o = use_sub[y_cont].values
        y_b = use_sub[y_bin].values
        X_num = use_sub[num_cols].astype(float)
        if cat_cols:
            dummies = pd.get_dummies(use_sub[cat_cols], drop_first=True, dtype=float)
            X_design = pd.concat([X_num.reset_index(drop=True), dummies.reset_index(drop=True)], axis=1)
        else:
            X_design = X_num.copy()
        # Add constant if not present (for numpy path)
        if "const" not in X_design.columns:
            X_design = pd.concat([pd.DataFrame({"const": np.ones(len(X_design))}, index=X_design.index), X_design], axis=1)
        X_mat = np.asarray(X_design.astype(float), dtype=float)
        var_names = list(X_design.columns)

        # OLS (numpy fallback if no statsmodels)
        try:
            if HAS_STATSMODELS:
                ols = sm.OLS(y_o, X_mat).fit()
                for i, var in enumerate(var_names[:ols.params.size]):
                    results_ols.append({"model": model_name, "variable": var, "coef": ols.params[i], "std_err": ols.bse[i], "t": ols.tvalues[i], "pvalue": ols.pvalues[i]})
                log(f"OLS {model_name}: R2={ols.rsquared:.4f}, N={int(ols.nobs)}")
            else:
                beta, _, rank, s = np.linalg.lstsq(X_mat, y_o, rcond=None)
                resid = y_o - X_mat @ beta
                n, k = X_mat.shape
                sig2 = (resid ** 2).sum() / (n - k) if n > k else np.nan
                try:
                    var_beta = sig2 * np.linalg.inv(X_mat.T @ X_mat)
                    se = np.sqrt(np.diag(var_beta))
                    t = beta / se
                    p = 2 * (1 - scipy_stats.t.cdf(np.abs(t), n - k))
                except Exception:
                    se, t, p = np.nan * np.ones_like(beta), np.nan * np.ones_like(beta), np.nan * np.ones_like(beta)
                r2 = 1 - (resid ** 2).sum() / ((y_o - y_o.mean()) ** 2).sum() if np.var(y_o) > 0 else 0
                for i, var in enumerate(var_names[:len(beta)]):
                    results_ols.append({"model": model_name, "variable": var, "coef": float(beta[i]), "std_err": float(se[i]) if i < len(se) else np.nan, "t": float(t[i]) if i < len(t) else np.nan, "pvalue": float(p[i]) if i < len(p) else np.nan})
                log(f"OLS {model_name}: R2={r2:.4f}, N={n} (numpy fallback)")
        except Exception as e:
            log(f"OLS {model_name} failed: {e}")

        # Logit
        try:
            if HAS_STATSMODELS:
                logit = Logit(y_b, X_mat).fit(disp=0)
                for i, var in enumerate(var_names[:logit.params.size]):
                    results_logit.append({"model": model_name, "variable": var, "coef": logit.params[i], "std_err": logit.bse[i], "z": logit.tvalues[i], "pvalue": logit.pvalues[i]})
                log(f"Logit {model_name}: Pseudo-R2={logit.prsquared:.4f}, N={int(logit.nobs)}")
            else:
                from sklearn.linear_model import LogisticRegression
                lr = LogisticRegression(max_iter=1000, solver="lbfgs", random_state=42).fit(X_mat, y_b)
                for i, var in enumerate(var_names[:len(lr.coef_[0]) + 1]):
                    c = lr.intercept_[0] if i == 0 else lr.coef_[0][i - 1]
                    results_logit.append({"model": model_name, "variable": var, "coef": float(c), "std_err": np.nan, "z": np.nan, "pvalue": np.nan})
                log(f"Logit {model_name}: N={len(y_b)} (sklearn fallback; install statsmodels for p-values)")
        except Exception as e:
            log(f"Logit {model_name} failed: {e}")

    # Save
    if results_ols:
        pd.DataFrame(results_ols).to_csv(OUT_DIR / "regression_tables_ols.csv", index=False, encoding="utf-8-sig")
        log(f"Saved {OUT_DIR / 'regression_tables_ols.csv'}")
    if results_logit:
        pd.DataFrame(results_logit).to_csv(OUT_DIR / "regression_tables_logit.csv", index=False, encoding="utf-8-sig")
        log(f"Saved {OUT_DIR / 'regression_tables_logit.csv'}")

    # Single table for paper: key variables only (Model 1/2/3 side by side)
    def wide_table(rows, value_col="coef", name="regression_tables"):
        keys = ["variable"]
        piv = pd.DataFrame(rows).pivot_table(index="variable", columns="model", values=value_col)
        piv.to_csv(OUT_DIR / f"{name}_{value_col}.csv", encoding="utf-8-sig")
        log(f"Saved {OUT_DIR / f'{name}_{value_col}.csv'}")

    if results_ols:
        wide_table(results_ols, "coef", "regression_ols_wide")
        wide_table(results_ols, "pvalue", "regression_ols_wide")
    if results_logit:
        wide_table(results_logit, "coef", "regression_logit_wide")
        wide_table(results_logit, "pvalue", "regression_logit_wide")


if __name__ == "__main__":
    main()
