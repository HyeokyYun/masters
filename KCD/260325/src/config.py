from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parent
DATA_DIR = REPO_ROOT / "original_data"
PRIOR_RUN_DIR = REPO_ROOT / "260319_cur"

WEEKLY_PARQUET = DATA_DIR / "weekly.parquet"
WEEKLY_REDUCED = DATA_DIR / "weekly_reduced.parquet"
META_CSV = DATA_DIR / "meta.csv"
PRIOR_LABELED = PRIOR_RUN_DIR / "outputs" / "tables" / "store_features_labeled.csv"

OUTPUT_DIR = PROJECT_ROOT / "outputs"
TABLE_DIR = OUTPUT_DIR / "tables"
FIGURE_DIR = OUTPUT_DIR / "figures"
DOC_DIR = OUTPUT_DIR / "docs"

for _path in (OUTPUT_DIR, TABLE_DIR, FIGURE_DIR, DOC_DIR):
    _path.mkdir(parents=True, exist_ok=True)

MIN_WEEKS = 30
MAX_WEEKS = 108
OPEN_DATE_MIN = "2019-01-01"
STL_PERIOD = 13
EARLY_STORE_MONTHS = 12.0
SEED = 42

OUTCOME_MAP = {"X": "Growth", "Y": "Stable", "Z": "Decline"}
OUTCOME_ORDER = ["Stable", "Growth", "Decline"]

AGE_BUCKET_BINS = [0.0, 12.0, 18.0, 24.0, 10_000.0]
AGE_BUCKET_LABELS = ["0_12m", "12_18m", "18_24m", "24m_plus"]

CATEGORY_SLUGS = {
    "기타": "other",
    "베이커리/디저트": "bakery_dessert",
    "분식": "bunsik",
    "술집": "pub",
    "양식": "western",
    "일식": "japanese",
    "중식": "chinese",
    "카페": "cafe",
    "패스트푸드": "fastfood",
    "한식": "korean",
}


def get_weekly_path() -> Path:
    if WEEKLY_PARQUET.exists():
        return WEEKLY_PARQUET
    return WEEKLY_REDUCED


def classify_industry(name: str) -> str:
    value = str(name)
    if any(token in value for token in ("카페", "커피")):
        return "카페"
    if any(token in value for token in ("베이커리", "디저트")):
        return "베이커리/디저트"
    if any(token in value for token in ("술집", "주점", "호프")):
        return "술집"
    for category in ("한식", "일식", "양식", "중식", "분식", "패스트푸드"):
        if category in value:
            return category
    return "기타"


def category_to_slug(category: str) -> str:
    return CATEGORY_SLUGS.get(str(category), "other")


def configure_matplotlib() -> None:
    mpl_dir = PROJECT_ROOT / ".mplconfig"
    cache_dir = PROJECT_ROOT / ".cache"
    mpl_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLBACKEND", "Agg")
    os.environ.setdefault("MPLCONFIGDIR", str(mpl_dir))
    os.environ.setdefault("XDG_CACHE_HOME", str(cache_dir))


def set_korean_font() -> None:
    configure_matplotlib()
    import matplotlib.font_manager as fm
    from matplotlib import rcParams

    candidates = [
        font.name
        for font in fm.fontManager.ttflist
        if any(token in font.name for token in ("Nanum", "Malgun", "AppleGothic", "Apple SD Gothic"))
    ]
    if candidates:
        rcParams["font.family"] = candidates[0]
    rcParams["axes.unicode_minus"] = False
