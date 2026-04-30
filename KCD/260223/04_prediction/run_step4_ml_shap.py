"""
Step 4: Ablation Study — UDX·변곡점 피처의 설명력(Feature Importance) 증명.

목적: '미래 예측'이 아니라, 우리가 만든 UDX 피처와 변곡점 피처가 업장의 최종 상태(성장/쇠퇴)를
구분하는 데 얼마나 높은 설명력을 가지는지 증명하는 Ablation Study.
- XGBoost와 LightGBM 모두 실행.
- SHAP Summary Plot 필수 출력: UDX_Code, P1_slope 등이 어떻게 기여했는지 시각화.
  (shap 미설치 시 pip install 후 진행)

Output: prediction_metrics.csv, shap_summary_xgb.png, shap_summary_lgb.png

Run from 260223: python 04_prediction/run_step4_ml_shap.py
"""
from pathlib import Path
import subprocess
import sys
import numpy as np
import pandas as pd
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "configs" / "pipeline.yaml"
OUT_DIR = ROOT / "outputs" / "tables"
FIG_DIR = ROOT / "outputs" / "figures"
LOG_DIR = ROOT / "outputs" / "logs"

# ML
try:
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import f1_score, accuracy_score
    from sklearn.ensemble import RandomForestClassifier
    SKLEARN = True
except ImportError:
    SKLEARN = False
try:
    import xgboost as xgb
    XGB = True
except ImportError:
    XGB = False
try:
    import lightgbm as lgb
    LGB = True
except ImportError:
    LGB = False

# SHAP 필수: 없으면 설치 시도 후 재import
def _ensure_shap():
    try:
        import shap
        return shap
    except ImportError:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "shap", "-q"])
            import shap
            return shap
        except Exception:
            return None
SHAP_AVAIL = _ensure_shap() is not None
if SHAP_AVAIL:
    import shap

try:
    import yaml
    def load_config():
        with open(CONFIG, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
except ImportError:
    def load_config():
        return {"prediction": {"seed": 42, "test_ratio": 0.2}}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "run_step4_ml_shap.log"

    def log(msg: str):
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    log("Step 4: Ablation Study — UDX & inflection feature importance (not future prediction).")

    cfg = load_config()
    pred_cfg = cfg.get("prediction", {})
    seed = pred_cfg.get("seed", 42)
    test_ratio = pred_cfg.get("test_ratio", 0.2)

    base_path = OUT_DIR / "df_base_features.parquet"
    udx_path = OUT_DIR / "df_udx_labels.parquet"
    if not base_path.exists():
        log("ERROR: Run Step 1 first.")
        return
    df = pd.read_parquet(base_path)
    if udx_path.exists():
        udx = pd.read_parquet(udx_path)
        id_col = "public_id"
        # UDX·변곡점 피처: cluster, slope_P1, slope_P2, inflection_week, final_code(UDX_Code)
        udx_cols = [c for c in udx.columns if c != id_col and c in ["cluster", "final_code", "Pattern_label", "slope_P1", "slope_P2", "inflection_week"]]
        if udx_cols:
            df = df.merge(udx[[id_col] + udx_cols], on=id_col, how="left")
    df["growth_type"] = (df["growth_rate"] >= 1.0).astype(int) if "growth_type" not in df.columns and "growth_rate" in df.columns else df.get("growth_type", (df["growth_rate"] >= 1.0).astype(int))

    # Base numeric
    num_base = ["new_customer_ratio", "cv_sales_card", "business_age_months", "business_density", "business_square_size", "avg_sales_card", "trend_slope", "total_weeks", "weekend_ratio", "avg_customer", "max_sales", "min_sales", "max_min_ratio", "dong_store_count", "dong_avg_sales", "sigungu_store_count", "sigungu_avg_sales"]
    num_base = [c for c in num_base if c in df.columns]
    # UDX·변곡점: 수치 + final_code(더미로 UDX_Code)
    udx_numeric = [c for c in ["cluster", "slope_P1", "slope_P2", "inflection_week"] if c in df.columns]
    cat_cols = [c for c in ["sigungu", "depth_2"] if c in df.columns]
    if "final_code" in df.columns:
        df["final_code"] = df["final_code"].fillna("Unknown").astype(str)
        cat_cols = cat_cols + ["final_code"]

    use = df.dropna(subset=num_base + ["growth_type"]).copy()
    for c in cat_cols:
        if c in use.columns:
            use[c] = use[c].fillna("Unknown").astype(str)
    X_num = use[num_base].astype(float)
    if udx_numeric:
        X_udx = use[udx_numeric].astype(float)
    else:
        X_udx = pd.DataFrame(index=use.index)
    if cat_cols:
        dummies = pd.get_dummies(use[[c for c in cat_cols if c in use.columns]], drop_first=True, dtype=float)
    else:
        dummies = pd.DataFrame(index=use.index)
    y = use["growth_type"].values

    # base_only: 기본 피처만 (UDX·변곡점·final_code 제외)
    base_dummy_cols = [c for c in dummies.columns if not c.startswith("final_code_")]
    X_base_only = pd.concat([X_num, dummies[base_dummy_cols] if base_dummy_cols else pd.DataFrame(index=X_num.index)], axis=1)
    # Full: base + UDX·변곡점 (cluster, slope_P1, slope_P2, inflection_week) + final_code(UDX_Code) 더미
    X_full = pd.concat([X_num, X_udx, dummies], axis=1)

    idx = X_base_only.index.intersection(X_full.index)
    X_base_only = X_base_only.loc[idx]
    X_full = X_full.loc[idx]
    y = use.loc[idx, "growth_type"].values
    X_train_b, X_test_b, y_train, y_test = train_test_split(X_base_only, y, test_size=test_ratio, random_state=seed, stratify=y)
    X_train_f = X_full.loc[X_train_b.index]
    X_test_f = X_full.loc[X_test_b.index]

    log(f"Train {len(y_train)}, Test {len(y_test)}. Base features: {X_base_only.shape[1]}, Full (base+UDX+inflection): {X_full.shape[1]}")

    metrics = []
    models_full = {}  # full model for SHAP

    def eval_clf(name, model, X_te, y_te, spec):
        pred = model.predict(X_te)
        acc = accuracy_score(y_te, pred)
        f1 = f1_score(y_te, pred, zero_division=0)
        metrics.append({"spec": spec, "model": name, "accuracy": acc, "f1_score": f1})
        return acc, f1

    if SKLEARN:
        rf_b = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=seed)
        rf_b.fit(X_train_b, y_train)
        eval_clf("RandomForest", rf_b, X_test_b, y_test, "base_only")
        rf_f = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=seed)
        rf_f.fit(X_train_f, y_train)
        eval_clf("RandomForest", rf_f, X_test_f, y_test, "base_udx_inflection")
        models_full["RandomForest"] = (rf_f, X_test_f)

    # XGBoost: base_only + base_udx_inflection
    if XGB:
        xgb_b = xgb.XGBClassifier(n_estimators=100, max_depth=6, random_state=seed, use_label_encoder=False, eval_metric="logloss")
        xgb_b.fit(X_train_b, y_train)
        eval_clf("XGBoost", xgb_b, X_test_b, y_test, "base_only")
        xgb_f = xgb.XGBClassifier(n_estimators=100, max_depth=6, random_state=seed, use_label_encoder=False, eval_metric="logloss")
        xgb_f.fit(X_train_f, y_train)
        eval_clf("XGBoost", xgb_f, X_test_f, y_test, "base_udx_inflection")
        models_full["XGBoost"] = (xgb_f, X_test_f)

    # LightGBM: base_only + base_udx_inflection
    if LGB:
        lgb_b = lgb.LGBMClassifier(n_estimators=100, max_depth=6, random_state=seed, verbose=-1)
        lgb_b.fit(X_train_b, y_train)
        eval_clf("LightGBM", lgb_b, X_test_b, y_test, "base_only")
        lgb_f = lgb.LGBMClassifier(n_estimators=100, max_depth=6, random_state=seed, verbose=-1)
        lgb_f.fit(X_train_f, y_train)
        eval_clf("LightGBM", lgb_f, X_test_f, y_test, "base_udx_inflection")
        models_full["LightGBM"] = (lgb_f, X_test_f)

    pd.DataFrame(metrics).to_csv(OUT_DIR / "prediction_metrics.csv", index=False, encoding="utf-8-sig")
    log(f"Saved {OUT_DIR / 'prediction_metrics.csv'}")

    # SHAP Summary Plot (설치 시) 또는 Tree Feature Importance로 UDX·P1_slope 기여도 시각화
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    
    # --- 운영체제별 폰트 자동 설정 ---
    import platform
    system_name = platform.system()
    if system_name == 'Darwin':
        plt.rcParams['font.family'] = 'Apple SD Gothic Neo'  # Mac
    elif system_name == 'Windows':
        plt.rcParams['font.family'] = 'Malgun Gothic'        # Windows
    else:
        plt.rcParams['font.family'] = 'NanumGothic'          # Linux (GPU 서버)
    plt.rcParams['axes.unicode_minus'] = False
    
    n_sample = min(500, len(X_test_f))
    X_te_s = X_test_f.iloc[:n_sample]

    if SHAP_AVAIL:
        for model_name, (model, _) in models_full.items():
            try:
                explainer = shap.TreeExplainer(model, X_te_s)
                shv = explainer.shap_values(X_te_s)
                if isinstance(shv, list):
                    shv = shv[1]
                plt.figure(figsize=(10, 8))
                shap.summary_plot(shv, X_te_s, show=False, max_display=25)
                plt.title(f"Ablation Study: SHAP — {model_name} (UDX & inflection features)")
                plt.tight_layout()
                plt.savefig(FIG_DIR / f"shap_summary_{model_name.lower()}.png", bbox_inches="tight", dpi=150)
                plt.close()
                log(f"Saved {FIG_DIR / f'shap_summary_{model_name.lower()}.png'}")
            except Exception as e:
                log(f"SHAP for {model_name} failed: {e}")
        if "XGBoost" in models_full:
            model, _ = models_full["XGBoost"]
            try:
                explainer = shap.TreeExplainer(model, X_te_s)
                shv = explainer.shap_values(X_te_s)
                if isinstance(shv, list):
                    shv = shv[1]
                plt.figure(figsize=(10, 8))
                shap.summary_plot(shv, X_te_s, plot_type="bar", show=False, max_display=25)
                plt.title("Ablation Study: Feature importance (SHAP, XGBoost full)")
                plt.tight_layout()
                plt.savefig(FIG_DIR / "shap_summary_plot.png", bbox_inches="tight", dpi=150)
                plt.close()
                log(f"Saved {FIG_DIR / 'shap_summary_plot.png'}")
            except Exception as e:
                log(f"SHAP bar failed: {e}")
    else:
        log("SHAP not installed. Generating tree feature importance plots (XGB/LGB) for Ablation.")
    # Tree feature importance (XGB/LGB full): UDX_Code, P1_slope 등 설명력 시각화 (SHAP 유무와 무관)
    log(f"Full models for importance: {list(models_full.keys())}")
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    for model_name, (model, X_te) in list(models_full.items()):
        try:
            imp = getattr(model, "feature_importances_", None)
            if imp is None:
                log(f"{model_name}: no feature_importances_, skip")
                continue
            imp = np.asarray(imp)
            names = list(X_te.columns)
            n = min(len(imp), len(names), 25)
            idx = np.argsort(imp)[::-1][:n]
            fig, ax = plt.subplots(figsize=(9, 8))
            ax.barh(range(len(idx)), imp[idx], color="steelblue", alpha=0.85)
            ax.set_yticks(range(len(idx)))
            ax.set_yticklabels([names[i] for i in idx], fontsize=9)
            ax.set_xlabel("Feature importance")
            ax.set_title(f"Ablation Study: {model_name} - UDX and inflection feature importance")
            ax.invert_yaxis()
            plt.tight_layout()
            fname = f"feature_importance_{model_name.lower()}_full.png"
            out_path = FIG_DIR / fname
            fig.savefig(str(out_path), bbox_inches="tight", dpi=150)
            plt.close(fig)
            log(f"Saved {out_path}")
        except Exception as e:
            import traceback
            log(f"Feature importance plot for {model_name} failed: {e}\n{traceback.format_exc()}")


if __name__ == "__main__":
    main()
