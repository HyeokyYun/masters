from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def get_work_dir() -> Path:
    return get_repo_root() / "260316"


def get_default_config_path() -> Path:
    return get_work_dir() / "configs" / "base.json"


def load_config(config_path: Path | None = None) -> Dict[str, Any]:
    path = config_path or get_default_config_path()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
