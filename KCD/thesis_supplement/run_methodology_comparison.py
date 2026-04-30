"""
논문 보강: 방법론 비교 (v4/v5 vs final_code)
────────────────────────────────────────────────────────────────────
v5 (데이터 드리븐 6클래스) vs final_code (K-Shape+변곡점) 레이블 비교
- 분포 비교
- 매장 단위 일치율 (v5 → final_code 매핑)
- 논문에서 방법론 선택 근거 제시용

실행: python thesis_supplement/run_methodology_comparison.py
출력: thesis_supplement/outputs/
────────────────────────────────────────────────────────────────────
"""
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "thesis_supplement" / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# v5 6클래스 → final_code 3자리 매핑 (해석적 대응)
V5_TO_FINAL_MAP = {
    "DD_Z": ["DDZ"],
    "DD_Y": ["DDY"],
    "DU":   ["DUX", "DUY", "DUZ"],
    "UU":   ["UUX", "UUY", "UUZ"],
    "UD_Z": ["UDZ"],
    "UD_Y": ["UDY"],
}


def load_v5_features():
    """v5 파이프라인 산출물 로드 (실행 후 생성됨)"""
    for p in [
        ROOT / "260309_claude" / "lifecycle_features_v5.csv",
    ]:
        if p.exists():
            df = pd.read_csv(p)
            df["public_id"] = df["public_id"].astype(str)
            return df[["public_id", "label"]]
    return None


def load_final_code():
    """final_code (260204_gem) 로드"""
    for p in [
        ROOT / "260204_gem" / "outputs" / "tables" / "final_code_by_store_260121_outlier_removal.csv",
        ROOT / "260224" / "03_inflection_udx" / "final_code_by_store_260121_outlier_removal.csv",
    ]:
        if p.exists():
            df = pd.read_csv(p)
            df["public_id"] = df["public_id"].astype(str)
            return df[["public_id", "final_code"]]
    return None


def load_outcome4():
    """outcome_4 (260301) 로드"""
    for p in [
        ROOT / "260301" / "outputs" / "tables" / "df_for_multinomial_logit.csv",
        ROOT / "260301" / "outputs" / "tables" / "df_base_features.csv",
    ]:
        if p.exists():
            df = pd.read_csv(p, nrows=50000)
            if "outcome_4" in df.columns:
                df = pd.read_csv(p)
                df["public_id"] = df["public_id"].astype(str)
                return df[["public_id", "outcome_4"]]
    return None


def main():
    print("=" * 60)
    print("논문 보강: 방법론 비교 (v5 vs final_code)")
    print("=" * 60)

    v5 = load_v5_features()
    final = load_final_code()

    if v5 is None:
        print("v5 산출물 없음. 먼저 실행: python 260309_claude/lifecycle_pipeline_v5.py")
        print("  (weekly_reduced.parquet 사용 시 빠름)")
        return

    if final is None:
        print("final_code 없음. 260204_gem 파이프라인 실행 필요.")
        return

    # 병합 (inner: 두 방법 모두 레이블 있는 매장)
    merged = v5.merge(final, on="public_id", how="inner", suffixes=("_v5", "_final"))
    print(f"\n비교 대상: {len(merged):,} 매장 (v5 ∩ final_code)")

    # 1) v5 분포
    print("\n[1] v5 레이블 분포:")
    v5_dist = merged["label"].value_counts().sort_index()
    for lbl, cnt in v5_dist.items():
        pct = cnt / len(merged) * 100
        print(f"  {lbl:6s}: {cnt:6,} ({pct:5.1f}%)")

    # 2) final_code 분포
    print("\n[2] final_code 레이블 분포:")
    fc_dist = merged["final_code"].value_counts().sort_index()
    for lbl, cnt in fc_dist.items():
        pct = cnt / len(merged) * 100
        print(f"  {lbl:6s}: {cnt:6,} ({pct:5.1f}%)")

    # 3) v5 × final_code 교차표
    cross = pd.crosstab(merged["label"], merged["final_code"], margins=True)
    cross.to_csv(OUT_DIR / "methodology_comparison_crosstab.csv", encoding="utf-8-sig")
    print("\n[3] 교차표 (v5 × final_code):")
    print(cross.to_string())
    print(f"\nSaved: {OUT_DIR / 'methodology_comparison_crosstab.csv'}")

    # 4) v5 → final_code 매핑 일치율
    print("\n[4] v5 클래스별 final_code 일치율 (매핑 기준):")
    rows = []
    for v5_lbl, fc_candidates in V5_TO_FINAL_MAP.items():
        sub = merged[merged["label"] == v5_lbl]
        if len(sub) == 0:
            continue
        match = sub["final_code"].isin(fc_candidates)
        rate = match.mean() * 100
        rows.append({"v5_label": v5_lbl, "match_pct": rate, "n": len(sub)})
        print(f"  {v5_lbl:6s}: {rate:5.1f}% 일치 (n={len(sub):,})")

    df_match = pd.DataFrame(rows)
    df_match.to_csv(OUT_DIR / "methodology_comparison_match_rates.csv", index=False, encoding="utf-8-sig")

    # 5) 요약
    overall_match = 0
    for v5_lbl, fc_candidates in V5_TO_FINAL_MAP.items():
        sub = merged[merged["label"] == v5_lbl]
        overall_match += (sub["final_code"].isin(fc_candidates)).sum()
    overall_pct = overall_match / len(merged) * 100
    print(f"\n[5] 전체 매핑 일치율: {overall_pct:.1f}%")
    print("=" * 60)


if __name__ == "__main__":
    main()
