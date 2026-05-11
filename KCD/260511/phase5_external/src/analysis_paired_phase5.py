"""Phase 5 종합 — 4 워크스트림(5A/5B/5C/5D)의 compare/paired CSV 를 결합.

Outputs:
  outputs/tables/phase5_master.csv      # 모델 × panel × F1 + Δ vs RF
  outputs/tables/phase5_summary.csv     # 모델별 평균 F1, mean Δ, n_panel, % wins
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common.paths import PHASE5_TABLE_DIR  # noqa: E402


def _read(name: str, workstream: str) -> pd.DataFrame:
    p = PHASE5_TABLE_DIR / name
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p)
    df["workstream"] = workstream
    return df


def main():
    cmp_dfs = []
    pair_dfs = []
    for ws, prefix in [
        ("5A_foundation", "foundation_zeroshot"),
        ("5B_neuralforecast", "neuralforecast"),
        ("5C_attention", "attention"),
        ("5D_weighting", "weighting"),
    ]:
        cmp_dfs.append(_read(f"{prefix}_compare.csv", ws))
        pair_dfs.append(_read(f"{prefix}_paired.csv", ws))

    cmp_all = pd.concat([df for df in cmp_dfs if not df.empty], ignore_index=True) if any(not df.empty for df in cmp_dfs) else pd.DataFrame()
    pair_all = pd.concat([df for df in pair_dfs if not df.empty], ignore_index=True) if any(not df.empty for df in pair_dfs) else pd.DataFrame()

    if cmp_all.empty:
        print("[phase5] no compare CSVs found")
        return

    cmp_all.to_csv(PHASE5_TABLE_DIR / "phase5_master.csv", index=False, encoding="utf-8-sig")
    pair_all.to_csv(PHASE5_TABLE_DIR / "phase5_paired_master.csv", index=False, encoding="utf-8-sig")

    # summary by model
    summary = []
    for (ws, model), g in cmp_all.groupby(["workstream", "model"]):
        n_panels = g["combo_id"].nunique()
        mean_f1 = float(g["macro_f1_mean"].mean())
        std_f1 = float(g["macro_f1_mean"].std() if n_panels > 1 else 0.0)
        row = {"workstream": ws, "model": model, "n_panels": int(n_panels),
                "mean_f1": mean_f1, "std_f1": std_f1}
        # paired stats if available
        ps = pair_all[(pair_all["workstream"] == ws) & (pair_all["model"] == model)]
        if not ps.empty:
            row["mean_delta_vs_rf"] = float(ps["delta_mean"].mean())
            row["n_sig_p05"] = int((ps["p_value"] < 0.05).sum())
            row["n_sig_p01"] = int((ps["p_value"] < 0.01).sum())
            row["wins_vs_rf"] = int((ps["delta_mean"] > 0).sum())
        else:
            row["mean_delta_vs_rf"] = float("nan")
            row["n_sig_p05"] = 0
            row["n_sig_p01"] = 0
            row["wins_vs_rf"] = 0
        summary.append(row)

    summary_df = pd.DataFrame(summary).sort_values("mean_f1", ascending=False)
    summary_df.to_csv(PHASE5_TABLE_DIR / "phase5_summary.csv", index=False, encoding="utf-8-sig")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
