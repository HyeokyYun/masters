"""
중앙 설정 ─ 경로, 하이퍼파라미터
260321: 미팅 피드백 반영 추가 분석
"""
from pathlib import Path
import numpy as np

# ── 경로 ─────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent   # 260321_cur/
REPO_ROOT    = PROJECT_ROOT.parent                      # 26-1/
DATA_DIR     = REPO_ROOT / "original_data"

WEEKLY_PARQUET = DATA_DIR / "weekly.parquet"
WEEKLY_REDUCED = DATA_DIR / "weekly_reduced.parquet"
META_CSV       = DATA_DIR / "meta.csv"

PREV_DIR       = REPO_ROOT / "260319_cur"
PREV_TABLE_DIR = PREV_DIR / "outputs" / "tables"

OUTPUT_DIR  = PROJECT_ROOT / "outputs"
FIGURE_DIR  = OUTPUT_DIR / "figures"
TABLE_DIR   = OUTPUT_DIR / "tables"

for _d in (OUTPUT_DIR, FIGURE_DIR, TABLE_DIR):
    _d.mkdir(parents=True, exist_ok=True)


# ── 전처리 파라미터 (260319_cur 동일) ────────────────────
MIN_WEEKS     = 52
MAX_WEEKS     = 108
OPEN_DATE_MIN = "2019-01-01"
STL_PERIOD    = 13

SEED     = 42
CV_FOLDS = 5


# ── 레이블 ───────────────────────────────────────────────
LIFECYCLE_LABELS = [
    "DD_Z", "DD_Y", "DD_X",
    "DU_Z", "DU_Y", "DU_X",
    "UU_Z", "UU_Y", "UU_X",
    "UD_Z", "UD_Y", "UD_X",
]

LABEL_DESC = {
    "DD_Z": "전반↓ 후반↓ 전체↓ (쇠퇴)",
    "DD_Y": "전반↓ 후반↓ 전체유지 (저성과 안정)",
    "DD_X": "전반↓ 후반↓ 전체↑ (V자 회복 미달)",
    "DU_Z": "전반↓ 후반↑ 전체↓ (불완전 반등)",
    "DU_Y": "전반↓ 후반↑ 전체유지 (부분 반등)",
    "DU_X": "전반↓ 후반↑ 전체↑ (강한 반등)",
    "UU_Z": "전반↑ 후반↑ 전체↓ (정체)",
    "UU_Y": "전반↑ 후반↑ 전체유지 (완만 성장)",
    "UU_X": "전반↑ 후반↑ 전체↑ (지속 성장)",
    "UD_Z": "전반↑ 후반↓ 전체↓ (급락)",
    "UD_Y": "전반↑ 후반↓ 전체유지 (소폭 조정)",
    "UD_X": "전반↑ 후반↓ 전체↑ (성장 후 경미 조정)",
}

OUTCOME3_MAP = {
    "DD_Z": "Decline", "DD_Y": "Stable",  "DD_X": "Growth",
    "DU_Z": "Decline", "DU_Y": "Stable",  "DU_X": "Growth",
    "UU_Z": "Decline", "UU_Y": "Stable",  "UU_X": "Growth",
    "UD_Z": "Decline", "UD_Y": "Stable",  "UD_X": "Growth",
}

SLOPE_ALL_THRESHOLD_FACTOR = 0.5


# ── 업종 매핑 ────────────────────────────────────────────
def classify_industry(name: str) -> str:
    v = str(name)
    if any(k in v for k in ("카페", "커피")):        return "카페"
    if any(k in v for k in ("베이커리", "디저트")):  return "베이커리/디저트"
    if any(k in v for k in ("술집", "주점", "호프")): return "술집"
    for cat in ("한식", "일식", "양식", "중식", "분식", "패스트푸드"):
        if cat in v:
            return cat
    return "기타"


# ── Matplotlib 한글 폰트 ─────────────────────────────────
def setup_matplotlib():
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    from matplotlib import rcParams

    candidates = [f.name for f in fm.fontManager.ttflist
                  if any(k in f.name for k in ("Nanum", "Gothic", "Malgun", "나눔",
                                                 "Apple SD", "AppleGothic"))]
    rcParams["font.family"] = candidates[0] if candidates else "DejaVu Sans"
    rcParams["axes.unicode_minus"] = False
    return plt
