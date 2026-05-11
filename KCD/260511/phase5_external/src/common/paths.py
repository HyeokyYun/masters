"""Phase 5 공통 경로. 기존 260430_claude의 cfg를 재사용."""
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path("/home/hyeoky98/kcd")
_PHASE4_SRC = _REPO / "260430_claude" / "src"
sys.path.insert(0, str(_PHASE4_SRC))

import config as cfg  # noqa: E402  — 260430_claude/src/config.py
import utils_panel as up  # noqa: E402

PHASE5_DIR = _REPO / "260511" / "phase5_external"
PHASE5_TABLE_DIR = PHASE5_DIR / "outputs" / "tables"
PHASE5_FIGURE_DIR = PHASE5_DIR / "outputs" / "figures"
PHASE5_LOG_DIR = PHASE5_DIR / "outputs" / "logs"
PHASE5_DOC_DIR = PHASE5_DIR / "docs"
for _p in [PHASE5_TABLE_DIR, PHASE5_FIGURE_DIR, PHASE5_LOG_DIR, PHASE5_DOC_DIR]:
    _p.mkdir(parents=True, exist_ok=True)

PANELS = [
    ("sy2021_sm01_w3m_off1", "Jan-Mar 2021 → Jan-Mar 2022"),
    ("sy2021_sm05_w3m_off1", "May-Jul 2021 → May-Jul 2022"),
    ("sy2022_sm01_w3m_off1", "Jan-Mar 2022 → Jan-Mar 2023"),
    ("sy2022_sm05_w3m_off1", "May-Jul 2022 → May-Jul 2023"),
    ("sy2021_sm01_w7m_off1", "Jan-Jul 2021 → Jan-Jul 2022 (7m)"),
    ("sy2022_sm01_w7m_off1", "Jan-Jul 2022 → Jan-Jul 2023 (7m)"),
]

CHANNELS = [
    "sales_card", "customer", "customer_new",
    "before_noon_sales", "weekend_sales", "sales_delivery",
]

OUTCOME_CLASSES = cfg.OUTCOME_CLASSES
CLS_TO_IDX = {c: i for i, c in enumerate(OUTCOME_CLASSES)}
SEED = cfg.SEED
