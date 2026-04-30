from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable

import pandas as pd


def ensure_layout(work_dir: Path) -> None:
    for rel in [
        "outputs",
        "outputs/figures",
        "outputs/logs",
        "outputs/tables",
        "docs",
        "templates",
        "artifacts",
        "artifacts/models",
    ]:
        (work_dir / rel).mkdir(parents=True, exist_ok=True)


def build_logger(log_path: Path) -> Callable[[str], None]:
    log_path.parent.mkdir(parents=True, exist_ok=True)

    def _log(message: str) -> None:
        line = f"{datetime.now().isoformat()} {message}"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        print(message)

    return _log


def save_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def save_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def save_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
