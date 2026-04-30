from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src import config as cfg
from src.model_utils import standardize_numeric_frame


FEATURES = [
    "trend_slope",
    "preferred_volatility",
    "mdd",
    "nc_rate",
    "del_ratio_log",
    "before_noon",
    "weekend",
    "seasonal_strength",
    "business_square_size",
    "delivery_link",
    "local_same_category_share",
    "business_age_months",
    "is_fastfood",
    "is_cafe",
    "is_pub",
]

FEATURE_LABELS = {
    "trend_slope": "매출 추세",
    "preferred_volatility": "추세조정 변동성",
    "mdd": "최대 낙폭(MDD)",
    "nc_rate": "신규 고객 비율",
    "del_ratio_log": "배달 비중(log)",
    "before_noon": "오전 매출 비중",
    "weekend": "주말 매출 비중",
    "seasonal_strength": "계절성 강도",
    "business_square_size": "점포 면적",
    "delivery_link": "배달앱 입점",
    "local_same_category_share": "동일업종 밀집도",
    "business_age_months": "표본 내부 업력(개월)",
    "is_fastfood": "패스트푸드 업종",
    "is_cafe": "카페 업종",
    "is_pub": "술집 업종",
}


def _interpret_signal(row: pd.Series) -> str:
    growth_sig = row["growth_pvalue"] < 0.05
    decline_sig = row["decline_pvalue"] < 0.05
    growth_coef = row["growth_coef"]
    decline_coef = row["decline_coef"]

    if growth_sig and decline_sig and growth_coef > 0 and decline_coef < 0:
        return "Growth 쪽으로 강하고 Decline은 억제"
    if growth_sig and decline_sig and growth_coef > 0 and decline_coef > 0:
        return "Stable보다 Growth/Decline 같은 동적 상태와 연결"
    if growth_sig and decline_sig and growth_coef < 0 and decline_coef < 0:
        return "Growth와 Decline 모두 낮아져 Stable 쪽과 연결"
    if growth_sig and growth_coef > 0:
        return "Growth 쪽과 연결"
    if growth_sig and growth_coef < 0:
        return "Growth를 억제"
    if decline_sig and decline_coef > 0:
        return "Decline 쪽과 연결"
    if decline_sig and decline_coef < 0:
        return "Stable 쪽과 연결"
    return "강한 신호는 아님"


def run_sample_feature_overview() -> tuple[pd.DataFrame, pd.DataFrame]:
    base = pd.read_csv(cfg.TABLE_DIR / "base_dataset.csv")
    vol_note = pd.read_csv(cfg.TABLE_DIR / "volatility_selection_note.csv")
    preferred_metric = vol_note.loc[vol_note["item"] == "preferred_metric", "value"].iloc[0]
    vol = pd.read_csv(cfg.TABLE_DIR / "volatility_candidates.csv")[["public_id", preferred_metric]]
    vol["public_id"] = vol["public_id"].astype(str)
    base["public_id"] = base["public_id"].astype(str)

    df = base.merge(vol, on="public_id", how="left")
    df = df.rename(columns={preferred_metric: "preferred_volatility"})
    work = df[["outcome_3"] + FEATURES].dropna(subset=["outcome_3"]).copy()
    work = standardize_numeric_frame(work, FEATURES)

    categories = list(cfg.OUTCOME_ORDER)
    y = pd.Categorical(work["outcome_3"], categories=categories, ordered=True)
    work = work[y.codes >= 0].copy()
    y = pd.Categorical(work["outcome_3"], categories=categories, ordered=True)
    X = sm.add_constant(work[FEATURES].astype(float), has_constant="add")

    result = sm.MNLogit(y.codes, X).fit(method="lbfgs", maxiter=500, disp=False)

    params = result.params.copy()
    pvalues = result.pvalues.copy()
    params.columns = ["growth_coef", "decline_coef"]
    pvalues.columns = ["growth_pvalue", "decline_pvalue"]

    ranked = pd.concat([params, pvalues], axis=1).loc[FEATURES].reset_index().rename(columns={"index": "feature"})
    ranked["feature_label"] = ranked["feature"].map(FEATURE_LABELS)
    ranked["importance_score"] = (
        ranked[["growth_coef", "decline_coef"]].abs().max(axis=1)
        * (-np.log10(ranked[["growth_pvalue", "decline_pvalue"]].min(axis=1) + 1e-12))
    )
    ranked["interpretation"] = ranked.apply(_interpret_signal, axis=1)
    ranked = ranked.sort_values("importance_score", ascending=False).reset_index(drop=True)
    ranked["rank"] = np.arange(1, len(ranked) + 1)

    fit_df = pd.DataFrame(
        [
            {
                "model_name": "sample_feature_overview",
                "nobs": float(result.nobs),
                "pseudo_r2": float(result.prsquared),
                "llf": float(result.llf),
                "aic": float(result.aic),
            }
        ]
    )

    ranked.to_csv(cfg.TABLE_DIR / "sample_feature_importance.csv", index=False, encoding="utf-8-sig")
    ranked.head(10).to_csv(cfg.TABLE_DIR / "sample_feature_top10.csv", index=False, encoding="utf-8-sig")
    fit_df.to_csv(cfg.TABLE_DIR / "sample_feature_model_fit.csv", index=False, encoding="utf-8-sig")

    note_lines = [
        "# 최근 개업 표본의 핵심 feature 메모",
        "",
        "아래 결과는 `21,365개` 최근 개업 표본에서 `Growth / Stable / Decline`을 전반적으로 가르는 요인을 한 번에 요약한 것입니다.",
        "",
        "- 방법: 다항 로짓(MNLogit)",
        "- 종속변수: `outcome_3`",
        "- 포함 변수: `매출 추세`, `추세조정 변동성`, `최대 낙폭`, `신규 고객 비율`, `배달 비중`, `오전/주말 비중`, `계절성`, `점포 면적`, `배달앱 입점`, `동일업종 밀집도`, `표본 내부 업력`, `주요 업종 더미`",
        "",
    ]
    for row in ranked.head(6).itertuples():
        note_lines.append(
            f"- `{row.feature_label}`: Growth coef `{row.growth_coef:.3f}`, "
            f"Decline coef `{row.decline_coef:.3f}`, 해석은 `{row.interpretation}`"
        )

    with open(cfg.DOC_DIR / "sample_feature_note.md", "w", encoding="utf-8") as handle:
        handle.write("\n".join(note_lines) + "\n")

    return ranked, fit_df
