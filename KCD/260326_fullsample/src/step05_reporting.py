from __future__ import annotations

from pathlib import Path

import pandas as pd

from src import config as cfg


def _load_csv(path: Path) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def _frame_to_text(df: pd.DataFrame, n: int | None = None) -> str:
    if df.empty:
        return "No output."
    view = df.head(n) if n is not None else df
    return view.to_string(index=False)


def write_reports() -> None:
    panel_diag = _load_csv(cfg.TABLE_DIR / "observed_window_panel_diagnostics.csv")
    label_summary = _load_csv(cfg.TABLE_DIR / "observed_window_outcome3_summary.csv")
    age_diag = _load_csv(cfg.TABLE_DIR / "fullsample_age_diagnostics.csv")
    age_bucket = _load_csv(cfg.TABLE_DIR / "fullsample_age_bucket_outcome_summary.csv")
    fit_compare = _load_csv(cfg.TABLE_DIR / "fullsample_age_model_fit_comparison.csv")
    gap_summary = _load_csv(cfg.TABLE_DIR / "fullsample_age_observation_gap_summary.csv")
    bucket_feature_fit = _load_csv(cfg.TABLE_DIR / "fullsample_age_bucket_feature_model_fit.csv")
    bucket_feature_top = _load_csv(cfg.TABLE_DIR / "fullsample_age_bucket_feature_top5.csv")

    summary = f"""# 260326 전체 업장 observed-window 분석 요약

## 분석 목적

이 폴더는 `개업 초기 생애주기`가 아니라, `데이터에서 관측된 구간 기준 성장/안정/하락 패턴`을 전체 업장에 대해 새롭게 분석한 결과입니다.

즉,

- `260319_cur`, `260325`: 개업 후 초기 구간 중심 분석
- `260326_fullsample`: 전체 업장을 대상으로 한 관측 구간 중심 분석

입니다.

## 패널 구성 요약

{_frame_to_text(panel_diag)}

## observed-window 3분류 분포

{_frame_to_text(label_summary)}

## 전체 업력 진단

{_frame_to_text(age_diag)}

## 전체 업력 구간별 outcome 요약

{_frame_to_text(age_bucket, 18)}

## 관측 시작 시점과 실제 업력 차이

{_frame_to_text(gap_summary)}

## 모형 적합도

{_frame_to_text(fit_compare)}

## 업력 구간별 핵심 feature

이 결과는 `관측 길이(n_observed_weeks_used)`를 제외하고, 실제 해석 가능한 feature만 남겨 업력 구간별 다항 로짓으로 다시 본 것입니다.

### 버킷별 적합도

{_frame_to_text(bucket_feature_fit)}

### 버킷별 상위 feature

{_frame_to_text(bucket_feature_top, 30)}
"""
    with open(cfg.DOC_DIR / "summary.md", "w", encoding="utf-8") as handle:
        handle.write(summary)

    guide = """# 발표 메모: 260326 전체 업장 분석

## 이 분석이 필요한 이유

기존 분석은 2019년 이후 개업 업장만 남기고, 개업 후 초기 108주를 기준으로 생애주기를 정의했습니다.
따라서 전체 업장 일반 업력 효과를 말하기에는 표본이 제한적이었습니다.

이번 분석은 전체 업장을 대상으로 다시 보되, 레이블 정의를 바꿨습니다.

## 핵심 차이

1. 기존 분석:
   개업 후 초기 구간을 기준으로 Growth / Stable / Decline을 정의
2. 이번 분석:
   데이터에서 실제로 관측된 첫 구간을 기준으로 Growth / Stable / Decline을 정의

즉, 이번 결과는 `현재 관측 가능한 구간에서의 패턴`이지, `개점 초기 생애주기`와 동일한 개념은 아닙니다.

## 발표에서 반드시 말할 점

- 이 분석은 이전 결과를 대체하지 않습니다.
- 이전 결과는 `초기 생애주기`, 이번 결과는 `전체 업장 observed-window 패턴`입니다.
- 두 결과를 함께 보여주면, 업력 해석의 범위를 훨씬 정직하게 설명할 수 있습니다.

## 업력 구간별 비율

- `0~12개월`: Growth `35.6%`, Decline `36.2%`, Stable `28.3%`
- `12~24개월`: Growth `28.3%`, Decline `35.3%`, Stable `36.4%`
- `24~36개월`: Growth `32.7%`, Decline `30.0%`, Stable `37.3%`
- `36~60개월`: Growth `38.8%`, Decline `23.2%`, Stable `38.0%`
- `60~120개월`: Growth `44.5%`, Decline `16.4%`, Stable `39.2%`
- `120개월+`: Growth `50.4%`, Decline `9.4%`, Stable `40.2%`

## 업력 구간을 이렇게 나눈 이유

- `0~12개월`: 개업 직후 생존/정착 단계
- `12~24개월`: 1년차 이후 초기 안정화 단계
- `24~36개월`: 2~3년차 초기 정착 단계
- `36~60개월`: 3~5년차 중기 운영 단계
- `60~120개월`: 5~10년차 장기 운영 단계
- `120개월+`: 10년 이상 장수 업장

즉, 임의 구간이 아니라 `해석 가능한 경영 단계`와 `구간별 표본 안정성`을 같이 고려한 구간입니다.

## 왜 Growth가 가장 많아 보이는가

- 전체 `50,635개` 표본 재검산 결과는 Growth `40.04%`, Stable `38.24%`, Decline `21.72%`입니다.
- 이 값은 오류라기보다 `observed-window 라벨 + 생존자 편향`의 결합 결과로 보는 편이 맞습니다.
- 오래된 업장은 개업 직후부터 본 것이 아니라 이미 살아남은 뒤부터 관측된 경우가 많습니다.

## 업력 구간별 중요한 feature

이번에는 `관측 길이`는 빼고, 실제 해석 가능한 feature만 남겨 각 업력 구간에서 Growth/Stable/Decline을 가르는 요인을 따로 봤습니다.

- `0~12개월`: 사실상 `매출 추세`가 거의 전부였습니다. 개업 직후에는 다른 변수보다 초기 매출이 위로 붙는지가 가장 강했습니다.
- `12~24개월`: `매출 추세`가 가장 강했고, `최대 낙폭(MDD)`는 Decline 쪽, `신규 고객 비율`은 Growth 쪽 신호가 나타났습니다.
- `24~36개월`: `매출 추세`, `최대 낙폭`, `신규 고객 비율` 조합이 핵심이었고, `배달 비중`이 높을수록 Growth 쪽 신호는 약해졌습니다.
- `36~60개월`: `매출 추세`가 1순위였고, `최대 낙폭`과 `신규 고객 비율`이 보조적으로 중요했습니다.
- `60~120개월`: `매출 추세`, `신규 고객 비율`, `최대 낙폭`이 중요했고, `주말 비중`이 높을수록 Growth는 다소 약해지는 신호가 있었습니다.
- `120개월+`: `매출 추세`가 여전히 핵심이었고, `신규 고객 비율`은 Growth/Decline 같은 동적 상태와 연결됐습니다. `주말 비중`은 오히려 Stable 쪽과 연결됐습니다.
"""
    with open(cfg.DOC_DIR / "presentation_note.md", "w", encoding="utf-8") as handle:
        handle.write(guide)
