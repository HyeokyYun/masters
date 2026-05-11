"""5A 로그에서 chronos/timesfm/moirai 결과 행을 파싱해 통합 compare/paired CSV로 저장.
RF baseline은 paired vs RF 비교를 위해 cv_harness를 직접 사용해 재계산."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.paths import PANELS, PHASE5_TABLE_DIR  # noqa: E402
from common.seq_loader import load_seq  # noqa: E402
from common.cv_harness import rf_baseline_folds  # noqa: E402

LOG_DIR = Path("/home/hyeoky98/kcd/260511/phase5_external/outputs/logs")
LOGS = {
    "chronos_bolt_small": LOG_DIR / "s5a_chronos_run.log",
    "timesfm_200m": LOG_DIR / "s5a_timesfm_run.log",
    "moirai_small": LOG_DIR / "s5a_moirai_run.log",
}

PANEL_MAP = dict(PANELS)
RE_ROW = re.compile(r"\[5A\] (\S+)\s+(\S+)\s+F1=([0-9.]+)\s+Δ=([+-][0-9.]+)\s+p=([0-9.]+)")
RE_RF = re.compile(r"\[5A\] (\S+) rf_tabular F1=([0-9.]+)")
RE_INFO = re.compile(r"\[5A\] (\S+) ([\d,]+) stores, H=(\d+)")


def main():
    rows = []
    paired = []
    rf_seen: set = set()
    for model, log in LOGS.items():
        if not log.exists():
            continue
        text = log.read_text(errors="ignore")
        # 정보 수집 (n_stores, horizon)
        info = {m.group(1): (int(m.group(2).replace(",", "")), int(m.group(3)))
                for m in RE_INFO.finditer(text)}
        # rf rows (combo_id, F1) — 가장 늦게 본 값 채택
        rf_map = {}
        for m in RE_RF.finditer(text):
            rf_map[m.group(1)] = float(m.group(2))
        for m in RE_ROW.finditer(text):
            combo = m.group(1); model_name = m.group(2)
            if model_name == "rf_tabular":
                continue
            f1 = float(m.group(3)); d = float(m.group(4)); p = float(m.group(5))
            n_st, H = info.get(combo, (0, 13))
            rows.append({
                "combo_id": combo,
                "description": PANEL_MAP.get(combo, combo),
                "model": model_name,
                "macro_f1_mean": f1, "macro_f1_std": 0.0,
                "n_stores": n_st, "horizon_weeks": H,
            })
            paired.append({"combo_id": combo, "model": model_name,
                            "delta_mean": d, "t_stat": float("nan"), "p_value": p})

    # RF baseline rerun (cv_harness 직접 호출) — paired vs RF용 reference
    panel_ids = set(r["combo_id"] for r in rows)
    for combo in panel_ids:
        ids, _, y = load_seq(combo)
        if ids is None:
            continue
        rf_f1 = rf_baseline_folds(combo, ids, y)
        n_st, H = info.get(combo, (len(ids), 13))
        rows.append({
            "combo_id": combo,
            "description": PANEL_MAP.get(combo, combo),
            "model": "rf_tabular",
            "macro_f1_mean": float(np.mean(rf_f1)),
            "macro_f1_std": float(np.std(rf_f1)),
            "n_stores": int(len(ids)), "horizon_weeks": H,
        })

    cmp_df = pd.DataFrame(rows).drop_duplicates(subset=["combo_id", "model"]).sort_values(["combo_id", "model"])
    pair_df = pd.DataFrame(paired).drop_duplicates(subset=["combo_id", "model"]).sort_values(["combo_id", "model"])
    cmp_df.to_csv(PHASE5_TABLE_DIR / "foundation_zeroshot_compare.csv", index=False, encoding="utf-8-sig")
    pair_df.to_csv(PHASE5_TABLE_DIR / "foundation_zeroshot_paired.csv", index=False, encoding="utf-8-sig")
    print(f"saved compare {len(cmp_df)} rows, paired {len(pair_df)} rows")
    print(cmp_df.groupby("model")["macro_f1_mean"].agg(["mean", "count"]).round(4))


if __name__ == "__main__":
    main()
