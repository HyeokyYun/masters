from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src import config as cfg


PREDICTION_DATASET_PATH = cfg.REPO_ROOT / "260316" / "outputs" / "tables" / "early_prediction_dataset.csv"
STORE_WEEK_PANEL_PATH = cfg.REPO_ROOT / "260316" / "outputs" / "tables" / "store_week_panel.parquet"
CV_FOLDS = 3
EARLY_WEEKS = 30
ROLLING_WINDOW = 13


def _build_one_hot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=True)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=True)


def _build_preprocessor(df: pd.DataFrame, features: list[str]) -> ColumnTransformer:
    numeric = [col for col in features if pd.api.types.is_numeric_dtype(df[col])]
    categorical = [col for col in features if col not in numeric]
    return ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric,
            ),
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("ohe", _build_one_hot_encoder()),
                    ]
                ),
                categorical,
            ),
        ],
        remainder="drop",
    )


def _relative_residual_scale(y: np.ndarray, trend: np.ndarray) -> float:
    residuals = y - trend
    denom = max(float(np.nanmean(np.abs(trend))), float(np.nanmean(np.abs(y))), 1.0)
    return float(np.nanstd(residuals) / (denom + 1e-9))


def _compute_new_volatility(public_ids: pd.Series) -> pd.DataFrame:
    panel = pd.read_parquet(STORE_WEEK_PANEL_PATH, columns=["public_id", "weeks_since_open", "sales_total"]).copy()
    panel["public_id"] = panel["public_id"].astype(str)
    panel = panel[panel["public_id"].isin(set(public_ids.astype(str)))].copy()
    panel = panel.replace([np.inf, -np.inf], np.nan).dropna(subset=["weeks_since_open", "sales_total"])
    panel["weeks_since_open"] = panel["weeks_since_open"].astype(int)
    panel = panel[(panel["weeks_since_open"] >= 0) & (panel["weeks_since_open"] < EARLY_WEEKS)].copy()
    panel = panel.sort_values(["public_id", "weeks_since_open"]).drop_duplicates(["public_id", "weeks_since_open"])

    records: list[dict[str, float | str]] = []
    for public_id, group in panel.groupby("public_id", sort=False):
        values = group["sales_total"].to_numpy(dtype=float)
        if len(values) < 10 or not np.isfinite(values).all():
            continue
        rolling_trend = pd.Series(values).rolling(ROLLING_WINDOW, min_periods=1, center=True).mean().to_numpy()
        records.append(
            {
                "public_id": public_id,
                "vol_resid_rolling13_30w": _relative_residual_scale(values, rolling_trend),
            }
        )
    return pd.DataFrame(records)


def _compute_competition_features(df: pd.DataFrame) -> pd.DataFrame:
    work = df[["public_id", "sido", "sigungu", "dong", "depth_2"]].copy()
    work["public_id"] = work["public_id"].astype(str)
    work["depth_2"] = work["depth_2"].fillna("missing")
    work["dong"] = work["dong"].fillna("missing")
    work["sigungu"] = work["sigungu"].fillna("missing")
    work["sido"] = work["sido"].fillna("missing")

    dong_keys = ["sido", "sigungu", "dong"]
    sigungu_keys = ["sido", "sigungu"]

    dong_total = work.groupby(dong_keys)["public_id"].transform("count")
    dong_same = work.groupby(dong_keys + ["depth_2"])["public_id"].transform("count")
    sigungu_total = work.groupby(sigungu_keys)["public_id"].transform("count")
    sigungu_same = work.groupby(sigungu_keys + ["depth_2"])["public_id"].transform("count")

    comp = work[["public_id"]].copy()
    comp["competition_share_dong"] = dong_same / dong_total.replace(0, np.nan)
    comp["competition_share_sigungu"] = sigungu_same / sigungu_total.replace(0, np.nan)
    comp["competition_count_dong"] = dong_same.astype(float)
    comp["competition_count_sigungu"] = sigungu_same.astype(float)
    comp["competition_total_dong"] = dong_total.astype(float)
    comp["competition_total_sigungu"] = sigungu_total.astype(float)
    return comp


def _core_features(df: pd.DataFrame) -> list[str]:
    cols = [
        "avg_sales_total",
        "avg_customer",
        "max_sales",
        "min_sales",
        "business_square_size",
        "std_sales_total",
        "cv_sales_total",
        "growth_rate",
        "trend_slope",
        "max_min_ratio",
        "new_customer_ratio",
        "cv_customer",
        "weekend_ratio",
        "card_ratio",
        "invoice_ratio",
        "delivery_ratio",
        "before_noon_ratio",
        "after_noon_ratio",
        "purchase_to_sales_ratio",
    ]
    return [col for col in cols if col in df.columns]


def _evaluate_classification(df: pd.DataFrame, feature_sets: dict[str, list[str]]) -> pd.DataFrame:
    target = "life_cycle_category"
    work = df.dropna(subset=[target]).copy()
    class_counts = work[target].value_counts()
    n_splits = max(2, min(CV_FOLDS, int(class_counts.min())))
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=cfg.SEED)
    rows: list[dict[str, float | str | int]] = []

    for feature_set_name, features in feature_sets.items():
        subset = work[features + [target]].copy()
        model = RandomForestClassifier(
            n_estimators=80,
            max_depth=12,
            class_weight="balanced",
            random_state=cfg.SEED,
            n_jobs=-1,
        )
        pipe = Pipeline([("pre", _build_preprocessor(subset, features)), ("model", model)])
        pred = cross_val_predict(pipe, subset[features], subset[target], cv=cv, method="predict")
        rows.append(
            {
                "feature_set": feature_set_name,
                "n_features": len(features),
                "n_obs": int(len(subset)),
                "accuracy": float(accuracy_score(subset[target], pred)),
                "macro_f1": float(f1_score(subset[target], pred, average="macro")),
                "weighted_f1": float(f1_score(subset[target], pred, average="weighted")),
            }
        )
    return pd.DataFrame(rows)


def _evaluate_regression(df: pd.DataFrame, feature_sets: dict[str, list[str]]) -> pd.DataFrame:
    target = "future_avg_sales"
    work = df.dropna(subset=[target]).copy()
    cv = KFold(n_splits=CV_FOLDS, shuffle=True, random_state=cfg.SEED)
    rows: list[dict[str, float | str | int]] = []

    for feature_set_name, features in feature_sets.items():
        subset = work[features + [target]].copy()
        model = RandomForestRegressor(
            n_estimators=80,
            max_depth=12,
            random_state=cfg.SEED,
            n_jobs=-1,
        )
        pipe = Pipeline([("pre", _build_preprocessor(subset, features)), ("model", model)])
        pred = cross_val_predict(pipe, subset[features], subset[target], cv=cv, method="predict")
        y = subset[target].to_numpy(dtype=float)
        rows.append(
            {
                "feature_set": feature_set_name,
                "n_features": len(features),
                "n_obs": int(len(subset)),
                "mae": float(mean_absolute_error(y, pred)),
                "rmse": float(np.sqrt(mean_squared_error(y, pred))),
                "r2": float(r2_score(y, pred)),
                "wape": float(np.abs(y - pred).sum() / np.abs(y).sum()),
            }
        )
    return pd.DataFrame(rows)


def _gain_table(metrics: pd.DataFrame, score_col: str) -> pd.DataFrame:
    order = [
        "core_existing",
        "core_plus_new_volatility",
        "core_plus_competition",
        "core_plus_new_volatility_and_competition",
    ]
    work = metrics.copy()
    work["feature_set"] = pd.Categorical(work["feature_set"], categories=order, ordered=True)
    work = work.sort_values("feature_set").reset_index(drop=True)
    base_value = work.loc[work["feature_set"] == "core_existing", score_col].iloc[0]
    work["delta_from_core"] = work[score_col] - base_value
    return work


def _write_doc(class_gain: pd.DataFrame, reg_gain: pd.DataFrame) -> None:
    lines: list[str] = []
    lines.append("# New Volatility and Competition in Forecasting")
    lines.append("")
    lines.append("## 1. 질문")
    lines.append("")
    lines.append("- 최근에 새로 정의한 detrended volatility가 forecasting에도 실제로 도움이 되는가?")
    lines.append("- 상권 밀집도/경쟁강도는 forecasting에서 추가 설명력을 주는가?")
    lines.append("")
    lines.append("## 2. 실험 설계")
    lines.append("")
    lines.append("- 초기 30주 표본 고정")
    lines.append("- `core_existing`를 기준으로 삼고 새 변수만 추가")
    lines.append("- 새 volatility는 `vol_resid_rolling13` 개념을 초기 30주에 맞춰 다시 계산한 `vol_resid_rolling13_30w` 사용")
    lines.append("- competition은 동/구 수준 동일업종 점유율과 개수로 구성")
    lines.append("")
    lines.append("## 3. 분류 예측 결과")
    lines.append("")
    for row in class_gain.itertuples(index=False):
        lines.append(
            f"- `{row.feature_set}`: accuracy `{row.accuracy:.4f}`, weighted F1 `{row.weighted_f1:.4f}`, core 대비 F1 변화 `{row.delta_from_core:+.4f}`"
        )
    lines.append("")
    lines.append("## 4. 회귀 예측 결과")
    lines.append("")
    for row in reg_gain.itertuples(index=False):
        lines.append(
            f"- `{row.feature_set}`: R2 `{row.r2:.4f}`, RMSE `{row.rmse:,.0f}`, core 대비 R2 변화 `{row.delta_from_core:+.4f}`"
        )
    lines.append("")
    lines.append("## 5. 해석")
    lines.append("")
    lines.append("- 새 detrended volatility가 core 대비 꾸준히 성능을 올리면 forecasting에서도 의미가 있다고 본다.")
    lines.append("- competition block이 별 이득이 없으면, 경쟁강도는 cross-sectional 설명에는 유용해도 현재 forecasting에는 한계가 있다고 해석한다.")
    lines.append("- 둘 다 함께 넣었을 때만 오르면 단독효과보다 결합효과로 해석한다.")

    (cfg.DOC_DIR / "forecast_newvol_competition.md").write_text("\n".join(lines), encoding="utf-8")


def run_forecast_newvol_competition() -> None:
    df = pd.read_csv(PREDICTION_DATASET_PATH)
    df["public_id"] = df["public_id"].astype(str)

    new_vol = _compute_new_volatility(df["public_id"])
    competition = _compute_competition_features(df)
    merged = df.merge(new_vol, on="public_id", how="left").merge(competition, on="public_id", how="left")

    core = _core_features(merged)
    new_vol_cols = [col for col in ["vol_resid_rolling13_30w"] if col in merged.columns]
    competition_cols = [
        col
        for col in [
            "competition_share_dong",
            "competition_share_sigungu",
            "competition_count_dong",
            "competition_count_sigungu",
        ]
        if col in merged.columns
    ]

    feature_sets = {
        "core_existing": core,
        "core_plus_new_volatility": core + new_vol_cols,
        "core_plus_competition": core + competition_cols,
        "core_plus_new_volatility_and_competition": core + new_vol_cols + competition_cols,
    }

    class_metrics = _evaluate_classification(merged, feature_sets)
    reg_metrics = _evaluate_regression(merged, feature_sets)
    class_gain = _gain_table(class_metrics, "weighted_f1")
    reg_gain = _gain_table(reg_metrics, "r2")

    merged[["public_id"] + new_vol_cols + competition_cols].to_csv(
        cfg.TABLE_DIR / "forecast_newvol_competition_features.csv",
        index=False,
        encoding="utf-8-sig",
    )
    class_metrics.to_csv(cfg.TABLE_DIR / "forecast_newvol_competition_classification.csv", index=False, encoding="utf-8-sig")
    reg_metrics.to_csv(cfg.TABLE_DIR / "forecast_newvol_competition_regression.csv", index=False, encoding="utf-8-sig")
    class_gain.to_csv(cfg.TABLE_DIR / "forecast_newvol_competition_classification_gain.csv", index=False, encoding="utf-8-sig")
    reg_gain.to_csv(cfg.TABLE_DIR / "forecast_newvol_competition_regression_gain.csv", index=False, encoding="utf-8-sig")
    _write_doc(class_gain, reg_gain)

