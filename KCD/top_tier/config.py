"""Top-tier 연구 공통 설정."""
from __future__ import annotations

from pathlib import Path

ROOT = Path("/home/hyeoky98/kcd")
TOP_TIER = ROOT / "top_tier"
SRC_DIR = TOP_TIER / "src"
OUT_DIR = TOP_TIER / "outputs"
TABLE_DIR = OUT_DIR / "tables"
FIGURE_DIR = OUT_DIR / "figures"
DOC_DIR = OUT_DIR / "docs"

for _p in [TABLE_DIR, FIGURE_DIR, DOC_DIR]:
    _p.mkdir(parents=True, exist_ok=True)

WEEKLY_PATH = ROOT / "original_data" / "weekly.parquet"
META_PATH = ROOT / "original_data" / "meta.csv"
PANEL_PATH = TABLE_DIR / "observed_window_panel.parquet"
FEATURES_PATH = TABLE_DIR / "observed_window_features_labeled.csv"
DATA_EXTERNAL_DIR = ROOT / "thesis" / "data_external"

SEED = 42

OBSERVATION_END = "2023-08-28"
CLOSURE_CUTOFF_WEEKS = 4

PREDICTION_WEEKS = 30
EVENT_WINDOW_BEFORE = 12
EVENT_WINDOW_AFTER = 12

OUTCOME_CLASSES = ["Growth", "Stable", "Decline"]
UDX_GROWTH = ["UUX", "UDX", "DUX"]
UDX_STABLE = ["UUY", "UDY", "DUY", "DDY"]
UDX_DECLINE = ["UUZ", "UDZ", "DUZ", "DDZ"]

K_RANGE = list(range(3, 16))
N_BOOTSTRAP = 1000
CV_FOLDS = 5

FIG_DPI = 300
FIG_STYLE = {
    "font.family": "NanumGothic",
    "axes.unicode_minus": False,
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "legend.fontsize": 10,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.dpi": 120,
    "savefig.dpi": FIG_DPI,
    "savefig.bbox": "tight",
}
