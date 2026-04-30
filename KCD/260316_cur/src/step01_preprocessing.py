"""
Step 01 ─ 전처리 파이프라인
  1) 원시 데이터 로딩 (weekly.parquet + meta.csv)
  2) 거시변수 통제 (주별 총매출 대비 비율)
  3) Time-alignment (weeks_since_open)
  4) Sparsity 처리 (보간·결측 제거)
  5) STL 분해 → Trend 추출 (per-store, period=13)
  6) 업장별 MinMax 정규화
"""
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import STL
from src import config as cfg


# ─────────────────────────────────────────────────────────
def load_raw_data():
    """weekly.parquet + meta.csv 로드, 기본 타입 정리."""
    wp = cfg.WEEKLY_PARQUET if cfg.WEEKLY_PARQUET.exists() else cfg.WEEKLY_REDUCED
    print(f"[Step01] 로딩: {wp.name}")
    ts   = pd.read_parquet(wp)
    meta = pd.read_csv(cfg.META_CSV)

    ts["public_id"]   = ts["public_id"].astype(str)
    meta["public_id"] = meta["public_id"].astype(str)
    ts["date_id"]     = pd.to_datetime(ts["date_id"])
    ts.loc[ts["sales_card"] < 0, "sales_card"] = np.nan

    print(f"  TS  {ts.shape},  매장={ts['public_id'].nunique():,}")
    print(f"  기간 {ts['date_id'].min().date()} ~ {ts['date_id'].max().date()}")
    return ts, meta


# ─────────────────────────────────────────────────────────
def _macro_control(ts: pd.DataFrame) -> pd.DataFrame:
    """거시변수 통제: 주별 전체 매출 합 대비 개별 비율."""
    ts["sales_ratio"] = ts.groupby("date_id")["sales_card"].transform(
        lambda x: x / (x.sum() + 1e-9)
    )
    return ts


def _time_alignment(ts: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    """open_month → weeks_since_open 계산 및 메타 병합."""
    keep = [c for c in ("public_id", "open_month", "delivery_link",
                         "business_square_size",
                         "classification__kcd_v3__depth_2_name", "age")
            if c in meta.columns]
    oinfo = meta[keep].copy()
    oinfo["open_date"] = pd.to_datetime(
        oinfo["open_month"].astype(str), format="%Y-%m", errors="coerce"
    )
    ts = ts.merge(oinfo, on="public_id", how="left")
    ts["weeks_since_open"] = (
        (ts["date_id"] - ts["open_date"]).dt.days // 7
    ).clip(lower=0)
    return ts


def _filter_stores(ts: pd.DataFrame) -> pd.DataFrame:
    """2019-01 이후 개업 + 최소 관측 주 필터."""
    ts = ts[ts["open_date"] >= cfg.OPEN_DATE_MIN].copy()
    cnt = ts.groupby("public_id")["weeks_since_open"].count()
    ts  = ts[ts["public_id"].isin(cnt[cnt >= cfg.MIN_WEEKS].index)].copy()
    return ts


def _interpolate_sales(ts: pd.DataFrame) -> pd.DataFrame:
    """업장별 선형 보간 → forward/backward fill."""
    ts["sales_card"] = ts.groupby("public_id")["sales_card"].transform(
        lambda x: x.interpolate("linear").ffill().bfill()
    )
    return ts


def _stl_trend(group: pd.DataFrame) -> pd.DataFrame:
    """단일 업장에 대해 STL 분해 → trend 컬럼 추가.
    관측치가 2*period 미만이면 7주 rolling mean으로 대체."""
    y = group["sales_card"].values.astype(float)
    n = len(y)
    period = cfg.STL_PERIOD

    if n >= 2 * period and np.isfinite(y).all():
        try:
            res = STL(y, period=period, robust=True).fit()
            group = group.copy()
            group["trend"]    = res.trend
            group["seasonal"] = res.seasonal
            group["resid"]    = res.resid
            return group
        except Exception:
            pass

    group = group.copy()
    group["trend"]    = pd.Series(y).rolling(7, min_periods=1, center=True).mean().values
    group["seasonal"] = 0.0
    group["resid"]    = y - group["trend"].values
    return group


def _apply_stl(ts: pd.DataFrame) -> pd.DataFrame:
    """모든 업장에 STL 분해 적용."""
    print("[Step01] STL 분해 중...")
    ts = ts.sort_values(["public_id", "weeks_since_open"])
    parts = []
    for _, g in ts.groupby("public_id", sort=False):
        parts.append(_stl_trend(g))
    ts = pd.concat(parts, ignore_index=True)
    stl_count = (ts["seasonal"] != 0).groupby(ts["public_id"]).any().sum()
    print(f"  STL 적용 매장: {stl_count:,} / {ts['public_id'].nunique():,}")
    return ts


def _minmax_normalize(ts: pd.DataFrame) -> pd.DataFrame:
    """업장별 MinMax [0,1] 정규화 (sales_card, trend 모두)."""
    for col in ("sales_card", "trend"):
        ts[f"{col}_mm"] = ts.groupby("public_id")[col].transform(
            lambda x: (x - x.min()) / (x.max() - x.min() + 1e-9)
        )
    return ts


def _classify_industry(ts: pd.DataFrame) -> pd.DataFrame:
    col = "classification__kcd_v3__depth_2_name"
    if col in ts.columns:
        cat_map = ts.groupby("public_id")[col].first().apply(cfg.classify_industry)
        ts["category"] = ts["public_id"].map(cat_map)
    else:
        ts["category"] = "기타"
    return ts


# ─────────────────────────────────────────────────────────
def preprocess():
    """전체 전처리 파이프라인. (ts, meta) 반환."""
    ts, meta = load_raw_data()
    ts = _macro_control(ts)
    ts = _time_alignment(ts, meta)
    ts = _filter_stores(ts)
    ts = _interpolate_sales(ts)
    ts = _apply_stl(ts)
    ts = _minmax_normalize(ts)
    ts = _classify_industry(ts)

    n = ts["public_id"].nunique()
    print(f"[Step01] 전처리 완료: {n:,} 매장, {len(ts):,} 행")
    return ts, meta
