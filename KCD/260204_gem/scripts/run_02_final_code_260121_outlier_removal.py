"""
260121 아웃라이어 제거 클러스터(Cluster 0~8) 시각 패턴 → X/Y/Z 매핑 후
P1_label + P2_label + Pattern_label 로 3자리 final_code 생성 및 분포 시각화.

참조: 260121/result_img/cluster_timeseries_with_outlier_removal.png

Run from 260204_gem: python scripts/run_02_final_code_260121_outlier_removal.py
"""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
TABLES_DIR = ROOT / "outputs" / "tables"
FIGURES_DIR = ROOT / "outputs" / "figures"
LOG_PATH = ROOT / "outputs" / "logs" / "run_02_final_code_260121_outlier_removal.log"

# 260121 cluster_timeseries_with_outlier_removal.png 기준 클러스터 시각 패턴 → X/Y/Z
# Cluster 0: 0.5~0.7 유지, 일부 하락 구간 있으나 전반 안정 → Y (Stable)
# Cluster 1: 0.6~0.7에서 0.1~0.2로 지속 하락 → Z (Decline)
# Cluster 2: 0.4→0.7 피크 후 0.3~0.4, 말기 회복 → Y (Stable/Fluctuating)
# Cluster 3: 0.4~0.5 수준 유지 → Y (Stable)
# Cluster 4: 0.1~0.2에서 0.5~0.6으로 지속 상승 → X (Growth)
# Cluster 5: 0.3~0.4에서 0.4 피크 후 0.2~0.3으로 하락 → Z (Decline)
# Cluster 6: 0.2~0.3 초기 피크 후 0.15~0.2 저점 유지 → Y (Stable)
# Cluster 7: 0.6~0.7에서 0.2~0.3으로 지속 하락 → Z (Decline)
# Cluster 8: 0.2~0.3에서 0.6~0.7으로 지속 상승 → X (Growth)
CLUSTER_TO_PATTERN = {
    0: "Y",  # Stable
    1: "Z",  # Decline
    2: "Y",  # Stable
    3: "Y",  # Stable
    4: "X",  # Growth
    5: "Z",  # Decline
    6: "Y",  # Stable
    7: "Z",  # Decline
    8: "X",  # Growth
}


def main():
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    def log(msg: str):
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    inflection_path = TABLES_DIR / "inflection_p1p2_labels.csv"
    cluster_path = ROOT / ".." / "260121" / "result_csv" / "cluster_labels_with_outlier_removal.csv"
    cluster_path = cluster_path.resolve()

    if not inflection_path.exists():
        log(f"ERROR: Not found {inflection_path}. Run run_01_inflection_p1p2.py first.")
        return
    if not cluster_path.exists():
        log(f"ERROR: Not found {cluster_path}. Run 260121 time_series_clustering_analysis_with_outlier_removal.py first.")
        return

    log("Loading inflection P1/P2 labels and 260121 cluster labels (outlier removed).")
    inflection = pd.read_csv(inflection_path)
    clusters = pd.read_csv(cluster_path)
    clusters["cluster"] = clusters["cluster"].astype(int)

    clusters["Pattern_label"] = clusters["cluster"].map(CLUSTER_TO_PATTERN)
    merged = inflection.merge(
        clusters[["public_id", "cluster", "Pattern_label"]],
        on="public_id",
        how="inner",
    )
    merged["final_code"] = (
        merged["P1_label"].astype(str)
        + merged["P2_label"].astype(str)
        + merged["Pattern_label"].astype(str)
    )

    out_table = TABLES_DIR / "final_code_by_store_260121_outlier_removal.csv"
    merged.to_csv(out_table, index=False, encoding="utf-8-sig")
    log(f"Saved {out_table} (rows={len(merged)})")

    counts = merged["final_code"].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(14, 5))
    x = range(len(counts))
    ax.bar(x, counts.values, color="steelblue", edgecolor="black", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(counts.index, rotation=45, ha="right")
    ax.set_ylabel("Store count")
    ax.set_xlabel("Final code (P1 + P2 + Pattern)")
    ax.set_title("Final code distribution — 260121 outlier-removed clusters (U/D + U/D + X/Y/Z)")
    plt.tight_layout()
    out_fig = FIGURES_DIR / "final_code_distribution_260121_outlier_removal.png"
    fig.savefig(out_fig, bbox_inches="tight", dpi=150)
    plt.close()
    log(f"Saved {out_fig}")

    log("Distribution summary:")
    for code, n in counts.items():
        log(f"  {code}: {n}")
    log("Done.")


if __name__ == "__main__":
    main()
