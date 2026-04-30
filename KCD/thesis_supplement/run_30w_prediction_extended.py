"""
논문 보강: 30주 예측 평가 확장
────────────────────────────────────────────────────────────────────
기존 run_step5_real_prediction.py와 동일한 로직으로 예측하되,
추가 평가 지표 산출: AUC-ROC, PR-AUC, Precision, Recall, 혼동행렬
클래스 불균형 대응: class_weight="balanced" 적용

실행: python thesis_supplement/run_30w_prediction_extended.py
출력: thesis_supplement/outputs/
────────────────────────────────────────────────────────────────────
"""
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from scipy.stats import linregress

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "thesis_supplement" / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

try:
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import (
        f1_score, accuracy_score, precision_score, recall_score,
        roc_auc_score, average_precision_score, confusion_matrix,
        classification_report
    )
    from sklearn.ensemble import RandomForestClassifier
except ImportError:
    print("ERROR: pip install scikit-learn")
    exit(1)


def load_config():
    cfg_path = ROOT / "260223" / "configs" / "pipeline.yaml"
    if cfg_path.exists():
        try:
            import yaml
            with open(cfg_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception:
            pass
    return {
        "data": {
            "features_csv": "basic_data/store_features_for_analysis.csv",
            "weekly_parquet": "original_data/weekly_processed.parquet",
            "weekly_parquet_fallback": "original_data/weekly.parquet",
            "id_col": "public_id",
            "time_col_week": "day_after1",
            "sales_col": "sales_card",
        }
    }


def get_target_df(cfg):
    id_col = cfg.get("id_col", "public_id")
    for base_path in [
        ROOT / "260223" / "outputs" / "tables" / "df_base_features.parquet",
        ROOT / "260223" / "outputs" / "tables" / "df_base_features.csv",
        ROOT / "260301" / "outputs" / "tables" / "df_base_features.csv",
        ROOT / "basic_data" / "store_features_for_analysis.csv",
    ]:
        if base_path.exists():
            df = pd.read_parquet(base_path) if str(base_path).endswith(".parquet") else pd.read_csv(base_path)
            if "growth_type" in df.columns:
                return df[[id_col, "growth_type"]].dropna()
            if "growth_rate" in df.columns:
                df = df.copy()
                df["growth_type"] = (df["growth_rate"] >= 1.0).astype(int)
                return df[[id_col, "growth_type"]].dropna()
    raise FileNotFoundError("Target (growth_type) not found. Run 260301 or 260223 first.")


def get_weekly_path(cfg):
    candidates = [
        ROOT / "original_data" / "weekly_processed.parquet",
        ROOT / "original_data" / "weekly.parquet",
        ROOT / "original_data" / "weekly_reduced.parquet",
    ]
    for p in candidates:
        if p.exists():
            return p
    val = cfg.get("weekly_parquet") or cfg.get("weekly_parquet_fallback", "")
    if val:
        return (ROOT / val.replace("../", "")).resolve()
    return candidates[0]


def calculate_early_features(weekly_df, weeks=30, time_col="day_after1", sales_col="sales_card", id_col="public_id"):
    cols = set(weekly_df.columns)
    tw = time_col if time_col in cols else ("day_after1" if "day_after1" in cols else "date_id")
    sid = id_col if id_col in cols else "public_id"
    sv = sales_col if sales_col in cols else "sales_card"
    weekly_df = weekly_df.sort_values([sid, tw])
    if tw == "day_after1":
        early_df = weekly_df[weekly_df[tw].between(1, weeks)].copy()
    else:
        early_df = weekly_df.groupby(sid).head(weeks)
    features = []
    for pid, group in early_df.groupby(sid):
        sales = group[sv].values
        if len(sales) < 2:
            continue
        avg_sales = np.mean(sales)
        sum_sales = np.sum(sales)
        slope, _, _, _, _ = linregress(np.arange(len(sales)), sales)
        cv = np.std(sales) / (np.mean(sales) + 1e-8)
        features.append({
            sid: pid, "early_avg": avg_sales, "early_sum": sum_sales,
            "early_slope": slope, "early_cv": cv,
        })
    return pd.DataFrame(features)


def get_early_sequence(weekly_df, store_ids, weeks=30, time_col="day_after1", sales_col="sales_card", id_col="public_id"):
    cols = set(weekly_df.columns)
    tw = time_col if time_col in cols else "day_after1"
    sid = id_col if id_col in cols else "public_id"
    sv = sales_col if sales_col in cols else "sales_card"
    weekly_df = weekly_df.sort_values([sid, tw])
    if tw == "day_after1":
        early = weekly_df[weekly_df[tw].between(1, weeks)][[sid, tw, sv]].copy()
    else:
        early = weekly_df.groupby(sid).head(weeks)[[sid, tw, sv]].copy()
    store_to_seq = {}
    for pid, group in early.groupby(sid):
        sales = group.sort_values(tw)[sv].values.astype(float)
        seq = np.zeros(weeks, dtype=float)
        seq[:min(len(sales), weeks)] = sales[:weeks]
        store_to_seq[pid] = seq
    return np.array([store_to_seq.get(pid, np.zeros(weeks, dtype=float)) for pid in store_ids], dtype=float)


def main():
    cfg = load_config()
    data_cfg = cfg.get("data", {})
    id_col = data_cfg.get("id_col", "public_id")
    time_col = data_cfg.get("time_col_week", "day_after1")
    sales_col = data_cfg.get("sales_col", "sales_card")
    seed = 42

    print("=" * 60)
    print("논문 보강: 30주 예측 확장 평가 (AUC, PR-AUC, 혼동행렬)")
    print("=" * 60)

    df_target = get_target_df(data_cfg)
    df_target[id_col] = df_target[id_col].astype(str)
    n_pos = (df_target["growth_type"] == 1).sum()
    n_neg = (df_target["growth_type"] == 0).sum()
    print(f"Target: {len(df_target)} stores | 성장(1)={n_pos:,} | 쇠퇴(0)={n_neg:,}")

    wp = get_weekly_path(data_cfg)
    if not wp.exists():
        print(f"ERROR: Weekly not found: {wp}")
        return
    df_weekly = pd.read_parquet(wp)
    df_weekly[id_col] = df_weekly[id_col].astype(str)
    print(f"Weekly: {len(df_weekly):,} rows")

    df_early = calculate_early_features(df_weekly, weeks=30, time_col=time_col, sales_col=sales_col, id_col=id_col)
    df_early[id_col] = df_early[id_col].astype(str)
    df_final = df_early.merge(df_target, on=id_col, how="inner").dropna()
    print(f"Final: {len(df_final):,} stores")

    X = df_final.drop([id_col, "growth_type"], axis=1)
    y = df_final["growth_type"].values

    idx = np.arange(len(df_final))
    train_idx, test_idx = train_test_split(idx, test_size=0.2, random_state=seed, stratify=y)
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    X_seq = get_early_sequence(df_weekly, df_final[id_col].values, weeks=30, time_col=time_col, sales_col=sales_col, id_col=id_col)
    X_seq_train, X_seq_test = X_seq[train_idx], X_seq[test_idx]

    # class_weight="balanced" 적용
    rf_balanced = RandomForestClassifier(n_estimators=100, random_state=seed, class_weight="balanced")

    results = []
    models = [
        ("Model A (Base)", ["early_avg", "early_sum"], X_train[["early_avg", "early_sum"]], X_test[["early_avg", "early_sum"]]),
        ("Model B (+Pattern)", ["early_avg", "early_sum", "early_slope", "early_cv"], X_train, X_test),
        ("Model C (Sequence)", None, X_seq_train, X_seq_test),
    ]

    for name, feats, X_tr, X_te in models:
        rf_balanced.fit(X_tr, y_train)
        pred = rf_balanced.predict(X_te)
        proba = rf_balanced.predict_proba(X_te)[:, 1] if hasattr(rf_balanced, "predict_proba") else pred.astype(float)

        acc = accuracy_score(y_test, pred)
        f1 = f1_score(y_test, pred, zero_division=0)
        prec = precision_score(y_test, pred, zero_division=0)
        rec = recall_score(y_test, pred, zero_division=0)

        auc_roc = roc_auc_score(y_test, proba) if len(np.unique(y_test)) > 1 else 0.0
        pr_auc = average_precision_score(y_test, proba) if len(np.unique(y_test)) > 1 else 0.0
        cm = confusion_matrix(y_test, pred)

        results.append({
            "Model": name,
            "Accuracy": acc, "F1": f1, "Precision": prec, "Recall": rec,
            "AUC_ROC": auc_roc, "PR_AUC": pr_auc,
            "Confusion_Matrix": str(cm.tolist()),
        })
        print(f"\n{name}:")
        print(f"  F1={f1:.4f}  Precision={prec:.4f}  Recall={rec:.4f}")
        print(f"  AUC-ROC={auc_roc:.4f}  PR-AUC={pr_auc:.4f}")
        print(f"  Confusion Matrix:\n{cm}")

    df_results = pd.DataFrame(results)
    df_results.to_csv(OUT_DIR / "30w_prediction_extended_metrics.csv", index=False, encoding="utf-8-sig")
    print(f"\nSaved: {OUT_DIR / '30w_prediction_extended_metrics.csv'}")

    # 혼동행렬 상세 (Model B)
    rf_balanced.fit(X_train, y_train)
    pred_b = rf_balanced.predict(X_test)
    report = classification_report(y_test, pred_b, target_names=["쇠퇴(0)", "성장(1)"])
    with open(OUT_DIR / "30w_prediction_classification_report.txt", "w", encoding="utf-8") as f:
        f.write("Model B (class_weight=balanced) Classification Report\n")
        f.write("=" * 50 + "\n")
        f.write(report)
        f.write("\nConfusion Matrix:\n")
        f.write(str(confusion_matrix(y_test, pred_b)))
    print(f"Saved: {OUT_DIR / '30w_prediction_classification_report.txt'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
