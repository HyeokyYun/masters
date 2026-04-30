"""
260320_codex — 경로 및 상수 (프로젝트 루트 기준)
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT = BASE_DIR.parent

# 입력 데이터
WEEKLY_PARQUET = ROOT / "original_data" / "weekly.parquet"
META_CSV = ROOT / "original_data" / "meta.csv"

# 260301 병합 테이블은 실제 산출물 위치를 우선 탐색
DF_MULTINOM_CANDIDATES = [
    ROOT / "260301" / "01_verify_data" / "outputs" / "tables" / "df_for_multinomial_logit.csv",
    ROOT / "260301" / "outputs" / "tables" / "df_for_multinomial_logit.csv",
    ROOT / "260225" / "outputs" / "tables" / "df_for_multinomial_logit.csv",
]

OUT_DIR = BASE_DIR / "outputs" / "tables"
FIG_DIR = BASE_DIR / "outputs" / "figures"
LOG_DIR = BASE_DIR / "outputs" / "logs"
DOCS_DIR = BASE_DIR / "docs"

# 추세 잔차 CV: 최소 주차
MIN_WEEKS_FOR_TREND = 20

# 업력 구간 (월) — 서브샘플
AGE_BUCKETS = [
    ("le6m", 0, 6),
    ("6m_12m", 6, 12),
    ("12m_24m", 12, 24),
    ("le24m", 0, 24),
    ("gt24m", 24, None),
]

# depth_2 상위 업종 (260301과 동일하게 한식 기준)
TOP_DEPTH2_FOR_DUMMY = ["한식", "카페", "술집", "패스트푸드", "일식"]

CATEGORIES = ["Stable", "Growth", "Decline"]


def resolve_multinom_path() -> Path:
    for path in DF_MULTINOM_CANDIDATES:
        if path.exists():
            return path
    return DF_MULTINOM_CANDIDATES[0]
