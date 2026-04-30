"""
데이터 로딩 유틸리티
─ 260319_cur 산출물 또는 원시 데이터 로드
"""
import numpy as np
import pandas as pd
from src import config as cfg


def load_labeled_features() -> pd.DataFrame:
    """260319_cur에서 생성된 store_features_labeled.csv 로드."""
    path = cfg.PREV_TABLE_DIR / "store_features_labeled.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"260319_cur 산출물이 필요합니다: {path}\n"
            "먼저 260319_cur/main.py 를 실행하세요."
        )
    df = pd.read_csv(path)
    df["public_id"] = df["public_id"].astype(str)
    print(f"[DataLoader] store_features_labeled: {len(df):,} 매장, "
          f"{df['label'].nunique()} 레이블")
    return df


def load_meta() -> pd.DataFrame:
    """meta.csv 로드."""
    meta = pd.read_csv(cfg.META_CSV)
    meta["public_id"] = meta["public_id"].astype(str)
    print(f"[DataLoader] meta: {len(meta):,} 매장, "
          f"컬럼={list(meta.columns)}")
    return meta


def load_weekly_raw() -> pd.DataFrame:
    """weekly.parquet 원시 데이터 로드."""
    wp = cfg.WEEKLY_PARQUET if cfg.WEEKLY_PARQUET.exists() else cfg.WEEKLY_REDUCED
    print(f"[DataLoader] 로딩: {wp.name}")
    ts = pd.read_parquet(wp)
    ts["public_id"] = ts["public_id"].astype(str)
    ts["date_id"] = pd.to_datetime(ts["date_id"])
    ts.loc[ts["sales_card"] < 0, "sales_card"] = np.nan
    print(f"  행={len(ts):,}, 매장={ts['public_id'].nunique():,}")
    return ts


def prepare_ts_for_prediction(ts: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    """예측을 위한 최소 전처리: time-alignment + filter + interpolation + MinMax."""
    keep = [c for c in ("public_id", "open_month", "delivery_link",
                         "classification__kcd_v3__depth_2_name")
            if c in meta.columns]
    oinfo = meta[keep].copy()
    oinfo["open_date"] = pd.to_datetime(
        oinfo["open_month"].astype(str), format="%Y-%m", errors="coerce"
    )
    ts = ts.merge(oinfo, on="public_id", how="left")
    ts["weeks_since_open"] = (
        (ts["date_id"] - ts["open_date"]).dt.days // 7
    ).clip(lower=0)

    ts = ts[ts["open_date"] >= cfg.OPEN_DATE_MIN].copy()
    cnt = ts.groupby("public_id")["weeks_since_open"].count()
    ts = ts[ts["public_id"].isin(cnt[cnt >= cfg.MIN_WEEKS].index)].copy()

    ts["sales_card"] = ts.groupby("public_id")["sales_card"].transform(
        lambda x: x.interpolate("linear").ffill().bfill()
    )

    ts["sales_card_mm"] = ts.groupby("public_id")["sales_card"].transform(
        lambda x: (x - x.min()) / (x.max() - x.min() + 1e-9)
    )

    print(f"[DataLoader] 전처리 완료: {ts['public_id'].nunique():,} 매장")
    return ts


def add_outcome3(df: pd.DataFrame) -> pd.DataFrame:
    """12-class label → 3-class outcome (Growth/Stable/Decline) 추가."""
    df = df.copy()
    df["outcome3"] = df["label"].map(cfg.OUTCOME3_MAP)
    return df


# ── MNLogit 공용 러너 ────────────────────────────────────
def run_mnlogit(df, feature_cols, label_col="label", baseline="UU_X",
                save_prefix=None):
    """MNLogit 추정 공용 함수.
    Returns: (result, summary_text)
    """
    import statsmodels.api as sm
    from statsmodels.discrete.discrete_model import MNLogit
    from sklearn.preprocessing import LabelEncoder

    dm = df.dropna(subset=feature_cols).copy()
    vc = dm[label_col].value_counts()
    dm = dm[dm[label_col].isin(vc[vc >= 20].index)].copy()

    X = dm[feature_cols].fillna(0).astype(float)
    X = sm.add_constant(X)
    y = dm[label_col].values

    labels_sorted = sorted(dm[label_col].unique())
    if baseline in labels_sorted:
        labels_sorted.remove(baseline)
        labels_sorted = [baseline] + labels_sorted

    le = LabelEncoder()
    le.classes_ = np.array(labels_sorted)
    y_enc = le.transform(y)

    model = MNLogit(y_enc, X.astype(float))
    result = model.fit(method="lbfgs", maxiter=2000, disp=False)

    summary_text = str(result.summary2())
    print(f"  MNLogit (기준={baseline}, n={len(dm):,}): "
          f"Pseudo R²={result.prsquared:.4f}")

    if save_prefix:
        with open(cfg.TABLE_DIR / f"{save_prefix}_summary.txt", "w",
                  encoding="utf-8") as f:
            f.write(summary_text)

        params = result.params
        coef_df = pd.DataFrame(params, index=X.columns)
        coef_df.columns = [
            f"vs_{labels_sorted[0]}_{labels_sorted[j+1]}"
            for j in range(params.shape[1])
        ]
        coef_df.to_csv(
            cfg.TABLE_DIR / f"{save_prefix}_coefficients.csv",
            encoding="utf-8-sig"
        )

    return result, summary_text
