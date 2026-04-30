"""
Step 5: 초기 30주 데이터 기반 실질적 미래 예측 (Real Forecasting)

목적: "초기 7개월(30주)의 데이터만으로 2년 뒤의 성패를 맞출 수 있는가?"
      -> 요약 통계 vs 시퀀스 학습 비교.

비교:
1. Model A (Baseline): 초기 평균 매출, 초기 매출 합계 (단순 수치)
2. Model B (Pattern): Model A + 초기 추세 기울기(Slope), 초기 변동성(CV)
3. Model C (Sequence): 초기 30주 매출 시퀀스(주별 30개 값)를 그대로 입력 — 시계열 학습

Run from 260223: python 04_prediction/run_step5_real_prediction.py
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from scipy.stats import linregress

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
        return {
            "data": {
                "project_root": "..",
                "features_csv": "../basic_data/store_features_for_analysis.csv",
                "weekly_parquet": "../original_data/weekly_processed.parquet",
                "weekly_parquet_fallback": "../original_data/weekly.parquet",
                "id_col": "public_id",
                "time_col_week": "day_after1",
                "sales_col": "sales_card",
            }
        }

try:
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import f1_score, accuracy_score
    from sklearn.ensemble import RandomForestClassifier
    SKLEARN = True
except ImportError:
    SKLEARN = False

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(x, **kwargs):
        return x


def get_weekly_path(cfg):
    """260223 기준: 프로젝트 루트(26-1) 기준 경로로 해석."""
    wp = cfg.get("weekly_parquet", "../original_data/weekly_processed.parquet")
    p = (ROOT / wp).resolve()
    if p.exists():
        return p
    fb = cfg.get("weekly_parquet_fallback", "../original_data/weekly.parquet")
    return (ROOT / fb).resolve()


def get_target_df(cfg):
    """타겟(Y): growth_type. 260223 df_base_features 우선, 없으면 basic_data에서 growth_rate로 생성."""
    id_col = cfg.get("id_col", "public_id")
    # 1) 260223 Step 1 결과 우선 (growth_type 있음)
    base_path = OUT_DIR / "df_base_features.parquet"
    if base_path.exists():
        df = pd.read_parquet(base_path)
        if "growth_type" in df.columns:
            return df[[id_col, "growth_type"]].dropna()
        if "growth_rate" in df.columns:
            df = df.copy()
            df["growth_type"] = (df["growth_rate"] >= 1.0).astype(int)
            return df[[id_col, "growth_type"]]
    # 2) basic_data CSV (상대 경로는 260223 기준이므로 ROOT.parent)
    features_csv = cfg.get("features_csv", "../basic_data/store_features_for_analysis.csv")
    path = (ROOT / features_csv).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Target not found: {base_path} or {path}. Run Step 1 or provide basic_data.")
    cols_csv = list(pd.read_csv(path, nrows=0).columns)
    usecols = [id_col, "growth_rate"] if "growth_rate" in cols_csv else [id_col]
    df = pd.read_csv(path, usecols=usecols)
    if "growth_type" not in df.columns and "growth_rate" in df.columns:
        df["growth_type"] = (df["growth_rate"] >= 1.0).astype(int)
    if "growth_type" not in df.columns:
        raise ValueError("Target needs growth_type or growth_rate in features CSV.")
    return df[[id_col, "growth_type"]].dropna()


def calculate_early_features(weekly_df, weeks=30, time_col="day_after1", sales_col="sales_card", id_col="public_id"):
    """
    각 매장의 초기 N주 데이터만 사용하여 Feature 추출.
    시간 컬럼: day_after1(주차 인덱스) 사용 시 1~weeks 구간만 사용.
    """
    cols = set(weekly_df.columns)
    if time_col not in cols:
        time_col = "date_id" if "date_id" in cols else "week_id"
    if id_col not in cols:
        id_col = "public_id"
    if sales_col not in cols:
        sales_col = "sales_card" if "sales_card" in cols else "sales"

    weekly_df = weekly_df.sort_values([id_col, time_col])
    # 초기 N주만: day_after1이면 1~weeks, date_id면 그룹별 상위 weeks개
    if time_col == "day_after1":
        early_df = weekly_df[weekly_df[time_col].between(1, weeks)].copy()
    else:
        early_df = weekly_df.groupby(id_col).head(weeks)

    features = []
    for pid, group in tqdm(early_df.groupby(id_col), desc=f"[{weeks}주] 초기 피처"):
        sales = group[sales_col].values
        if len(sales) < 2:
            continue
        avg_sales = np.mean(sales)
        sum_sales = np.sum(sales)
        slope, _, _, _, _ = linregress(np.arange(len(sales)), sales)
        cv = np.std(sales) / (np.mean(sales) + 1e-8)
        features.append({
            id_col: pid,
            "early_avg": avg_sales,
            "early_sum": sum_sales,
            "early_slope": slope,
            "early_cv": cv,
        })
    return pd.DataFrame(features)


def get_early_sequence(weekly_df, store_ids, weeks=30, time_col="day_after1", sales_col="sales_card", id_col="public_id"):
    """
    업장별 초기 N주 매출을 시퀀스(길이 30 벡터)로 반환. 부족한 주는 0으로 패딩.
    store_ids 순서대로 (len(store_ids), weeks) 배열 반환 — df_final과 1:1 정렬.
    """
    cols = set(weekly_df.columns)
    tw = time_col if time_col in cols else ("day_after1" if "day_after1" in cols else "week_id")
    sid = id_col if id_col in cols else "public_id"
    sv = sales_col if sales_col in cols else ("sales_card" if "sales_card" in cols else "sales")
    weekly_df = weekly_df.sort_values([sid, tw])
    if tw == "day_after1":
        early = weekly_df[weekly_df[tw].between(1, weeks)][[sid, tw, sv]].copy()
    else:
        early = weekly_df.groupby(sid).head(weeks)[[sid, tw, sv]].copy()
    store_to_seq = {}
    for pid, group in early.groupby(sid):
        sales = group.sort_values(tw)[sv].values.astype(float)
        seq = np.zeros(weeks, dtype=float)
        n = min(len(sales), weeks)
        seq[:n] = sales[:n]
        store_to_seq[pid] = seq
    X_list = []
    for pid in store_ids:
        X_list.append(store_to_seq.get(pid, np.zeros(weeks, dtype=float)))
    return np.array(X_list, dtype=float)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "run_step5_real_prediction.log"

    def log(msg: str):
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    log("Step 5: Real Forecasting — 초기 30주 기반 미래 예측 (Model A vs B).")

    cfg = load_config()
    data_cfg = cfg.get("data", {})
    id_col = data_cfg.get("id_col", "public_id")
    time_col = data_cfg.get("time_col_week", "day_after1")
    sales_col = data_cfg.get("sales_col", "sales_card")
    seed = 42

    # 1) 타겟(Y): 전체 기간 기준 성장/쇠퇴
    df_target = get_target_df(data_cfg)
    log(f"Target: {len(df_target)} stores. growth_type 1={df_target['growth_type'].sum()}, 0={(df_target['growth_type']==0).sum()}")

    # 2) 주간 매출
    wp = get_weekly_path(data_cfg)
    if not wp.exists():
        log(f"ERROR: Weekly data not found: {wp}")
        return
    df_weekly = pd.read_parquet(wp)
    log(f"Weekly: {len(df_weekly)} rows, cols include time={time_col}, sales={sales_col}")

    # 3) 초기 30주 피처
    df_early = calculate_early_features(df_weekly, weeks=30, time_col=time_col, sales_col=sales_col, id_col=id_col)
    log(f"Early features: {len(df_early)} stores")

    # 4) 병합
    df_final = df_early.merge(df_target, on=id_col, how="inner").dropna()
    log(f"Final sample: {len(df_final)} stores")

    if not SKLEARN:
        log("ERROR: sklearn required. pip install scikit-learn")
        return

    X = df_final.drop([id_col, "growth_type"], axis=1)
    y = df_final["growth_type"].values

    # 동일한 train/test 분할 (Model A/B/C 공통)
    idx = np.arange(len(df_final))
    train_idx, test_idx = train_test_split(idx, test_size=0.2, random_state=seed, stratify=y)
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    # 초기 30주 시퀀스 (업장별 주별 매출 30개) — 시계열 학습용
    X_seq = get_early_sequence(df_weekly, df_final[id_col].values, weeks=30, time_col=time_col, sales_col=sales_col, id_col=id_col)
    X_seq_train, X_seq_test = X_seq[train_idx], X_seq[test_idx]

    # Model A: Baseline
    features_a = ["early_avg", "early_sum"]
    rf_a = RandomForestClassifier(n_estimators=100, random_state=seed)
    rf_a.fit(X_train[features_a], y_train)
    pred_a = rf_a.predict(X_test[features_a])
    acc_a = accuracy_score(y_test, pred_a)
    f1_a = f1_score(y_test, pred_a, zero_division=0)

    # Model B: Base + Pattern (slope, cv)
    features_b = ["early_avg", "early_sum", "early_slope", "early_cv"]
    rf_b = RandomForestClassifier(n_estimators=100, random_state=seed)
    rf_b.fit(X_train[features_b], y_train)
    pred_b = rf_b.predict(X_test[features_b])
    acc_b = accuracy_score(y_test, pred_b)
    f1_b = f1_score(y_test, pred_b, zero_division=0)

    # Model C: 시퀀스 학습 — 30주 원시 매출을 그대로 입력 (시계열)
    rf_c = RandomForestClassifier(n_estimators=100, random_state=seed)
    rf_c.fit(X_seq_train, y_train)
    pred_c = rf_c.predict(X_seq_test)
    acc_c = accuracy_score(y_test, pred_c)
    f1_c = f1_score(y_test, pred_c, zero_division=0)
    seq_feature_desc = "[week_1, week_2, ..., week_30] (30주 매출 시퀀스)"

    log("=" * 50)
    log(" [실험 결과] 초기 30주 기반 미래 예측 (F1 / Accuracy)")
    log("=" * 50)
    log(f" Model A (단순 평균·합계만): F1={f1_a:.4f}, Acc={acc_a:.4f}")
    log(f" Model B (평균·합계 + 기울기/변동성): F1={f1_b:.4f}, Acc={acc_b:.4f}")
    log(f" Model C (시퀀스 학습, 30주 원시값): F1={f1_c:.4f}, Acc={acc_c:.4f}")
    log(f" -> A→B F1: +{(f1_b - f1_a)*100:.2f}%p / A→C F1: +{(f1_c - f1_a)*100:.2f}%p")
    log("=" * 50)

    # 결과 CSV
    results = pd.DataFrame({
        "Model": ["Model A (Base)", "Model B (With Pattern)", "Model C (Sequence)"],
        "Features": [str(features_a), str(features_b), seq_feature_desc],
        "F1_Score": [f1_a, f1_b, f1_c],
        "Accuracy": [acc_a, acc_b, acc_c],
    })
    results.to_csv(OUT_DIR / "real_prediction_results.csv", index=False, encoding="utf-8-sig")
    log(f"Saved {OUT_DIR / 'real_prediction_results.csv'}")

    # Feature importance (Model B) — 한글 폰트 설정
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import platform
    system_name = platform.system()
    if system_name == "Darwin":
        plt.rcParams["font.family"] = "Apple SD Gothic Neo"
    elif system_name == "Windows":
        plt.rcParams["font.family"] = "Malgun Gothic"
    else:
        plt.rcParams["font.family"] = "NanumGothic"
    plt.rcParams["axes.unicode_minus"] = False

    importances = rf_b.feature_importances_
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(features_b, importances, color="teal", alpha=0.85)
    ax.set_xlabel("Feature importance")
    ax.set_title("Step 5: Early Prediction — Feature Importance (Model B)")
    fig.savefig(FIG_DIR / "early_prediction_importance.png", bbox_inches="tight", dpi=150)
    plt.close()
    log(f"Saved {FIG_DIR / 'early_prediction_importance.png'}")


if __name__ == "__main__":
    main()
