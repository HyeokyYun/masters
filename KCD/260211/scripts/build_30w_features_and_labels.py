"""
첫 30주 기반 피처 + 성장/하락 라벨 생성.
- 입력: 각 매장의 첫 30주 매출만 사용해 피처 계산.
- 라벨: 31주~끝 구간 매출 기울기 >= 0 → 성장(1), < 0 → 하락(0).
- 최소 전체 주수: min_total_weeks (기본 50) 이상인 매장만 포함.

Run from 260211: python scripts/build_30w_features_and_labels.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "configs" / "prediction_30w.yaml"
# 출력 경로는 main()에서 configs/prediction_30w.yaml 의 outputs.tables / outputs.logs 사용

STORE_CANDIDATES = ["public_id", "store_id"]
WEEK_CANDIDATES = ["week_id", "day_after1"]
SALES_CANDIDATES = ["sales_card", "sales"]

# 기본 설정 (YAML 없이 동작)
DEFAULT_CONFIG = {
    "data": {
        "weekly_parquet_primary": "../original_data/weekly_processed.parquet",
        "weekly_parquet_fallback": "../original_data/weekly.parquet",
        "meta_csv": "../original_data/meta_processed.csv",
        "meta_fallback": "../original_data/meta.csv",
        "id_col_store": "public_id",
        "time_col_week": "day_after1",
        "y_col_sales": "sales_card",
    },
    "prediction": {
        "first_n_weeks": 30,
        "min_total_weeks": 50,
        "growth_slope_threshold": 0.0,
    },
}


def load_config():
    try:
        import yaml
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return DEFAULT_CONFIG


def get_weekly_path(cfg):
    data = cfg.get("data", {})
    primary = ROOT / data.get("weekly_parquet_primary", "../original_data/weekly_processed.parquet")
    if primary.exists():
        return primary
    return ROOT / data.get("weekly_parquet_fallback", "../original_data/weekly.parquet")


def resolve_weekly_columns(df, data_cfg):
    df = df.copy()
    cols = set(df.columns)
    col_store = data_cfg.get("id_col_store") or "public_id"
    if col_store not in cols:
        for c in STORE_CANDIDATES:
            if c in cols:
                col_store = c
                break
        else:
            raise ValueError(f"Weekly: no store column. Columns: {sorted(cols)!r}")
    col_week = data_cfg.get("time_col_week")
    if not col_week or col_week not in cols:
        if "day_after1" in cols:
            col_week = "day_after1"
        elif "week_id" in cols:
            col_week = "week_id"
        elif "date_id" in cols:
            df["date_id"] = pd.to_datetime(df["date_id"])
            min_date = df["date_id"].min()
            df["_week_index"] = ((df["date_id"] - min_date).dt.days // 7) + 1
            df = df[df["_week_index"] != 0]
            col_week = "_week_index"
        else:
            raise ValueError(f"Weekly: no week column. Columns: {sorted(cols)!r}")
    col_sales = data_cfg.get("y_col_sales")
    if not col_sales or col_sales not in cols:
        for c in SALES_CANDIDATES:
            if c in cols:
                col_sales = c
                break
        else:
            raise ValueError(f"Weekly: no sales column. Columns: {sorted(cols)!r}")
    return df, col_store, col_week, col_sales


def features_from_first_n_weeks(sales: np.ndarray, n: int):
    """첫 n주 매출로 피처 계산. sales는 이미 주차순 정렬된 1d 배열."""
    if len(sales) < n:
        return None
    head = sales[:n].astype(float)
    avg = float(np.mean(head))
    std = float(np.std(head))
    if avg <= 0:
        cv = 0.0
    else:
        cv = std / avg
    mx = float(np.max(head))
    mn = float(np.min(head))
    max_min_ratio = mx / mn if mn > 0 else 0.0
    if n > 1:
        x = np.arange(n, dtype=float)
        slope = np.polyfit(x, head, 1)[0]
        trend_slope = slope / avg if avg > 0 else 0.0
    else:
        trend_slope = 0.0
    return {
        "avg_sales_card": avg,
        "std_sales_card": std,
        "cv_sales_card": cv,
        "max_sales": mx,
        "min_sales": mn,
        "max_min_ratio": max_min_ratio,
        "trend_slope": trend_slope,
        "total_weeks": n,
    }


def slope_after_weeks(sales: np.ndarray, after_week: int):
    """after_week 이후 구간 매출의 선형 기울기(연속값). 회귀 타깃용."""
    if len(sales) <= after_week:
        return None
    tail = sales[after_week:].astype(float)
    if len(tail) < 2:
        return None
    x = np.arange(len(tail), dtype=float)
    return float(np.polyfit(x, tail, 1)[0])


def label_after_weeks(sales: np.ndarray, after_week: int, threshold: float = 0.0):
    """after_week 이후 구간 매출의 선형 기울기. >= threshold → 1(성장), else 0(하락)."""
    s = slope_after_weeks(sales, after_week)
    return None if s is None else (1 if s >= threshold else 0)


def main():
    cfg = load_config()
    data_cfg = cfg.get("data", {})
    pred_cfg = cfg.get("prediction", {})
    out_cfg = cfg.get("outputs", {})
    tables_dir = ROOT / out_cfg.get("tables", "outputs/tables")
    logs_dir = ROOT / out_cfg.get("logs", "outputs/logs")
    OUT_PARQUET = tables_dir / "features_30w_and_labels.parquet"
    LOG_PATH = logs_dir / "build_30w_features_and_labels.log"

    ROOT.mkdir(parents=True, exist_ok=True)
    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    def log(msg: str):
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)
    first_n = int(pred_cfg.get("first_n_weeks", 30))
    min_total = int(pred_cfg.get("min_total_weeks", 50))
    threshold = float(pred_cfg.get("growth_slope_threshold", 0.0))

    path = get_weekly_path(cfg)
    if not path.exists():
        log(f"ERROR: Weekly parquet not found: {path}")
        return
    log(f"Loading {path}")
    df = pd.read_parquet(path)
    df, col_store, col_week, col_sales = resolve_weekly_columns(df, data_cfg)
    log(f"Columns: store={col_store}, week={col_week}, sales={col_sales}")

    # 속도 개선: 전체 (store, week) 1회 groupby 후 정렬, 매장별 순회(전체 df 재스캔 없음)
    log("데이터 그룹화 및 정렬 중...")
    agg_df = df.groupby([col_store, col_week], as_index=False)[col_sales].mean()
    agg_df = agg_df.sort_values([col_store, col_week])

    log("매장별 피처 및 라벨 생성 중...")
    rows = []
    for sid, group in agg_df.groupby(col_store):
        sales = group[col_sales].values  # 이미 주차순 정렬됨
        if len(sales) < min_total:
            continue
        feats = features_from_first_n_weeks(sales, first_n)
        if feats is None:
            continue
        lbl = label_after_weeks(sales, first_n, threshold)
        slope_val = slope_after_weeks(sales, first_n)
        # 31주~끝 구간 총 매출 (전체 매출 회귀 타깃용)
        total_sales_after = float(np.sum(sales[first_n:]))
        if lbl is None or slope_val is None:
            continue
        rows.append({
            col_store: sid,
            **feats,
            "growth": lbl,
            "slope_after_30w": slope_val,
            "total_sales_after_30w": total_sales_after,
        })

    out_df = pd.DataFrame(rows)
    # 메타(지역·업종) 병합 — 예측률 상승용, 시점 무관 정보만 (경로는 config 사용)
    meta_primary = ROOT / data_cfg.get("meta_csv", "../original_data/meta_processed.csv")
    meta_fallback = ROOT / data_cfg.get("meta_fallback", "../original_data/meta.csv")
    meta_path = meta_primary if meta_primary.exists() else meta_fallback
    if meta_path.exists():
        meta_df = pd.read_csv(meta_path)
        meta_cols = [c for c in ["public_id", "sigungu", "dong", "depth_1", "depth_2", "depth_3"] if c in meta_df.columns]
        if "public_id" in meta_cols and len(meta_cols) > 1:
            out_df = out_df.merge(meta_df[meta_cols], on=col_store, how="left")
            log(f"Merged meta: {[c for c in meta_cols if c != col_store]}")
    out_df.to_parquet(OUT_PARQUET, index=False)
    log(f"Saved {OUT_PARQUET} — {len(out_df)} stores")
    log(f"Label distribution: growth={out_df['growth'].sum()}, decline={(out_df['growth'] == 0).sum()}")
    if "slope_after_30w" in out_df.columns:
        log(f"slope_after_30w: mean={out_df['slope_after_30w'].mean():.4f}, std={out_df['slope_after_30w'].std():.4f} (regression target)")
    if "total_sales_after_30w" in out_df.columns:
        log(f"total_sales_after_30w: mean={out_df['total_sales_after_30w'].mean():.0f}, std={out_df['total_sales_after_30w'].std():.0f} (total sales regression target)")


if __name__ == "__main__":
    main()
