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
CV_FOLDS = 3


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


def _feature_blocks(df: pd.DataFrame) -> dict[str, list[str]]:
    level_only = [
        "avg_sales_total",
        "avg_customer",
        "max_sales",
        "min_sales",
        "business_square_size",
    ]
    trend_volatility = level_only + [
        "std_sales_total",
        "cv_sales_total",
        "growth_rate",
        "trend_slope",
        "max_min_ratio",
    ]
    customer_behavior = trend_volatility + [
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
    local_market = customer_behavior + [
        "business_age_months",
        "age_numeric",
        "dong_store_count",
        "dong_avg_sales",
        "sigungu_store_count",
        "sigungu_avg_sales",
        "business_density",
        "delivery_link",
    ]
    plus_cluster = local_market + ["growth_type", "early_cluster"]

    blocks = {
        "level_only": level_only,
        "plus_trend_volatility": trend_volatility,
        "plus_customer_behavior": customer_behavior,
        "plus_local_market": local_market,
        "plus_cluster": plus_cluster,
    }
    return {name: [col for col in cols if col in df.columns] for name, cols in blocks.items()}


def _classification_ablation(df: pd.DataFrame, feature_sets: dict[str, list[str]]) -> pd.DataFrame:
    target = "life_cycle_category"
    work = df.dropna(subset=[target]).copy()
    class_counts = work[target].value_counts()
    n_splits = max(2, min(CV_FOLDS, int(class_counts.min())))
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=cfg.SEED)
    rows: list[dict[str, float | str | int]] = []

    for feature_set_name, features in feature_sets.items():
        if not features:
            continue
        subset = work[features + [target]].copy()
        model = RandomForestClassifier(
            n_estimators=60,
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
                "model": "RandomForest",
                "n_features": len(features),
                "n_obs": int(len(subset)),
                "accuracy": float(accuracy_score(subset[target], pred)),
                "macro_f1": float(f1_score(subset[target], pred, average="macro")),
                "weighted_f1": float(f1_score(subset[target], pred, average="weighted")),
            }
        )
    return pd.DataFrame(rows)


def _regression_ablation(df: pd.DataFrame, feature_sets: dict[str, list[str]]) -> pd.DataFrame:
    target = "future_avg_sales"
    work = df.dropna(subset=[target]).copy()
    cv = KFold(n_splits=CV_FOLDS, shuffle=True, random_state=cfg.SEED)
    rows: list[dict[str, float | str | int]] = []

    for feature_set_name, features in feature_sets.items():
        if not features:
            continue
        subset = work[features + [target]].copy()
        model = RandomForestRegressor(
            n_estimators=60,
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
                "model": "RandomForestRegressor",
                "n_features": len(features),
                "n_obs": int(len(subset)),
                "mae": float(mean_absolute_error(y, pred)),
                "rmse": float(np.sqrt(mean_squared_error(y, pred))),
                "r2": float(r2_score(y, pred)),
                "wape": float(np.abs(y - pred).sum() / np.abs(y).sum()),
            }
        )
    return pd.DataFrame(rows)


def _marginal_gain_table(metrics: pd.DataFrame, score_col: str, model_name: str) -> pd.DataFrame:
    order = [
        "level_only",
        "plus_trend_volatility",
        "plus_customer_behavior",
        "plus_local_market",
        "plus_cluster",
    ]
    work = metrics[metrics["model"] == model_name].copy()
    work["feature_set"] = pd.Categorical(work["feature_set"], categories=order, ordered=True)
    work = work.sort_values("feature_set").reset_index(drop=True)
    work["delta_from_prev"] = work[score_col].diff()
    work["delta_from_level_only"] = work[score_col] - work.loc[work["feature_set"] == "level_only", score_col].iloc[0]
    return work


def _write_doc(class_gain: pd.DataFrame, reg_gain: pd.DataFrame) -> None:
    lines: list[str] = []
    lines.append("# Forecast Feature Ablation")
    lines.append("")
    lines.append("## 1. 왜 이 실험을 했는가")
    lines.append("")
    lines.append("- 관측 주가 길어지면 성능이 올라가는 것은 자연스러운 현상이다.")
    lines.append("- 그래서 같은 `초기 30주` 조건에서 feature block을 하나씩 추가하며 성능이 얼마나 늘어나는지 확인했다.")
    lines.append("- 이 실험은 `시간이 길어져서 좋아진 것`과 `우리 feature가 실제로 도움이 된 것`을 구분하기 위한 것이다.")
    lines.append("")
    lines.append("## 2. 분류 예측에서 무엇이 도움이 되었는가")
    lines.append("")
    for row in class_gain.itertuples(index=False):
        delta_prev = "NA" if pd.isna(row.delta_from_prev) else f"{row.delta_from_prev:+.4f}"
        lines.append(
            f"- `{row.feature_set}`: accuracy `{row.accuracy:.4f}`, weighted F1 `{row.weighted_f1:.4f}`, 직전 대비 F1 변화 `{delta_prev}`"
        )
    lines.append("")
    lines.append("## 3. 미래 매출 회귀에서 무엇이 도움이 되었는가")
    lines.append("")
    for row in reg_gain.itertuples(index=False):
        delta_prev = "NA" if pd.isna(row.delta_from_prev) else f"{row.delta_from_prev:+.4f}"
        lines.append(
            f"- `{row.feature_set}`: R2 `{row.r2:.4f}`, RMSE `{row.rmse:,.0f}`, 직전 대비 R2 변화 `{delta_prev}`"
        )
    lines.append("")
    lines.append("## 4. 발표용 해석")
    lines.append("")
    lines.append("- `level_only`는 단순 현재 수준 정보만 쓴 경우다.")
    lines.append("- `plus_trend_volatility`에서 성능이 오르면, 단순 수준보다 추세/변동성이 추가로 의미 있다는 뜻이다.")
    lines.append("- `plus_customer_behavior`에서 더 오르면, 신규고객·주말 비중·결제/배달 구조가 추가 정보를 준다는 뜻이다.")
    lines.append("- `plus_local_market`와 `plus_cluster`의 추가 이득은 상권 구조 변수와 초기 패턴 요약 변수의 한계효과를 보여준다.")

    (cfg.DOC_DIR / "forecast_feature_ablation.md").write_text("\n".join(lines), encoding="utf-8")


def run_forecast_feature_ablation() -> None:
    df = pd.read_csv(PREDICTION_DATASET_PATH)
    if "public_id" in df.columns:
        df["public_id"] = df["public_id"].astype(str)

    feature_sets = _feature_blocks(df)
    class_metrics = _classification_ablation(df, feature_sets)
    reg_metrics = _regression_ablation(df, feature_sets)
    class_gain = _marginal_gain_table(class_metrics, "weighted_f1", "RandomForest")
    reg_gain = _marginal_gain_table(reg_metrics, "r2", "RandomForestRegressor")

    class_metrics.to_csv(cfg.TABLE_DIR / "forecast_feature_ablation_classification.csv", index=False, encoding="utf-8-sig")
    reg_metrics.to_csv(cfg.TABLE_DIR / "forecast_feature_ablation_regression.csv", index=False, encoding="utf-8-sig")
    class_gain.to_csv(cfg.TABLE_DIR / "forecast_feature_ablation_classification_gain.csv", index=False, encoding="utf-8-sig")
    reg_gain.to_csv(cfg.TABLE_DIR / "forecast_feature_ablation_regression_gain.csv", index=False, encoding="utf-8-sig")
    _write_doc(class_gain, reg_gain)
