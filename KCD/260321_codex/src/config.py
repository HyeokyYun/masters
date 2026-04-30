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

MIN_WEEKS = 52
MAX_WEEKS = 108
OPEN_DATE_MIN = "2019-01-01"
STL_PERIOD = 13
EARLY_STORE_MONTHS = 12
VERY_EARLY_STORE_MONTHS = 6
SEED = 42

OUTCOME_MAP = {"X": "growth", "Y": "stable", "Z": "decline"}
OUTCOME_ORDER = ["stable", "growth", "decline"]

AGE_BAND_TO_NUMERIC = {
    "20대 이하": 20.0,
    "20대": 25.0,
    "30대": 35.0,
    "40대": 45.0,
    "50대": 55.0,
    "60대": 65.0,
    "60대 이상": 65.0,
    "70대 이상": 75.0,
}

AGE_BUCKET_LABELS = ["0_6m", "6_12m", "12_24m", "24m_plus"]
AGE_BUCKET_BINS = [0.0, 6.0, 12.0, 24.0, 10_000.0]


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


def configure_matplotlib() -> None:
    mpl_dir = PROJECT_ROOT / ".mplconfig"
    cache_dir = PROJECT_ROOT / ".cache"
    mpl_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLBACKEND", "Agg")
    os.environ.setdefault("MPLCONFIGDIR", str(mpl_dir))
    os.environ.setdefault("XDG_CACHE_HOME", str(cache_dir))
