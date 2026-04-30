"""Build one integrated robustness master table for thesis reporting."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "260303" / "outputs" / "tables"
LOG_DIR = ROOT / "260303" / "outputs" / "logs"

INPUT_FILES = [
    OUT_DIR / "robustness_label_results.csv",
    OUT_DIR / "robustness_sample_results.csv",
    OUT_DIR / "robustness_model_results.csv",
]



def make_logger(path: Path):
    def _log(msg: str) -> None:
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    return _log



def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = make_logger(LOG_DIR / "run_robustness_master.log")

    frames = []
    for file in INPUT_FILES:
        if not file.exists():
            log(f"SKIP missing: {file}")
            continue
        try:
            frames.append(pd.read_csv(file))
        except Exception as exc:
            log(f"SKIP unreadable {file.name}: {exc}")

    if not frames:
        log("ERROR: no robustness result files found")
        return

    full = pd.concat(frames, ignore_index=True)

    cols = [
        "spec_type",
        "spec_name",
        "n_obs",
        "n_class",
        "macro_f1_cv",
        "weighted_f1_cv",
        "accuracy_cv",
        "pseudo_r2",
        "significant_ratio_p05",
        "direction_match_ratio",
        "notes",
    ]
    keep = [c for c in cols if c in full.columns]
    report = full[keep].copy()

    out_csv = OUT_DIR / "robustness_master_table.csv"
    report.to_csv(out_csv, index=False, encoding="utf-8-sig")
    log(f"Saved {out_csv}")


if __name__ == "__main__":
    main()
